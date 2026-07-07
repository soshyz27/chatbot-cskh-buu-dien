"""
Chatbot CSKH bưu điện - Bản đầy đủ Tuần 2
Luồng xử lý mỗi tin nhắn:
  1. Phân loại ý định (tra_cuu_don_hang / hoi_faq / khieu_nai / khac)
  2. Lấy dữ liệu thật từ database tương ứng
  3. Gemini soạn câu trả lời tự nhiên dựa trên dữ liệu thật đó
"""

import os
import re
import json
import time
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors

import db_utils

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("Không tìm thấy GEMINI_API_KEY. Kiểm tra lại file .env")

client = genai.Client(api_key=API_KEY)
MODEL_NAME = "gemini-2.5-flash-lite"

app = FastAPI(title="Chatbot CSKH Bưu điện")


def goi_gemini_co_retry(contents: str, so_lan_thu: int = 3) -> str:
    """
    Gọi Gemini API, tự động thử lại nếu gặp lỗi 503 (server quá tải).
    Chờ tăng dần giữa các lần thử (1s, 2s, 4s).
    Nếu gặp lỗi 429 (hết quota), báo lỗi rõ ràng ngay, không thử lại.
    """
    for lan_thu in range(so_lan_thu):
        try:
            response = client.models.generate_content(model=MODEL_NAME, contents=contents)
            return response.text
        except genai_errors.ServerError:
            if lan_thu == so_lan_thu - 1:
                raise
            time.sleep(2 ** lan_thu)
        except genai_errors.ClientError as e:
            if "RESOURCE_EXHAUSTED" in str(e):
                raise RuntimeError(
                    "Đã hết quota API Gemini hôm nay. Vui lòng thử lại sau hoặc kiểm tra gói cước."
                ) from e
            raise
    raise RuntimeError("Không thể kết nối Gemini sau nhiều lần thử.")


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    intent: str  # trả kèm intent để debug/demo dễ hơn


# ---------- BƯỚC 1: Phân loại ý định ----------

INTENT_PROMPT = """Phân loại tin nhắn của khách hàng bưu điện vào đúng 1 trong 4 nhãn sau:
- "tra_cuu_don_hang": khách hỏi về trạng thái/tình trạng một đơn hàng cụ thể
- "hoi_faq": khách hỏi thông tin chung (giờ làm việc, cách đóng gói, phí, dịch vụ...)
- "khieu_nai": khách phàn nàn, báo lỗi, muốn khiếu nại (chậm giao, mất hàng, sai tiền COD...)
- "khac": không thuộc 3 loại trên (chào hỏi, hỏi ngoài phạm vi bưu điện...)

Nếu là "tra_cuu_don_hang", hãy cố gắng trích xuất mã vận đơn trong tin nhắn (thường có dạng chữ+số, VD: E88392011VN, R77402195VN, hoặc chỉ số+VN).
Nếu là "khieu_nai", hãy phân loại thêm loại khiếu nại: "cham_giao" / "mat_hang" / "sai_cod" / "khac".

CHỈ trả về JSON, không thêm chữ nào khác, đúng định dạng:
{"intent": "...", "ma_van_don": "..." hoặc null, "loai_khieu_nai": "..." hoặc null}

Tin nhắn của khách: """


def phan_loai_y_dinh(message: str) -> dict:
    text = goi_gemini_co_retry(INTENT_PROMPT + message).strip()
    # Gemini đôi khi bọc JSON trong ```json ... ``` - loại bỏ nếu có
    text = re.sub(r"^```json|```$", "", text, flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Nếu Gemini trả sai định dạng, coi như "khac" để không làm sập app
        return {"intent": "khac", "ma_van_don": None, "loai_khieu_nai": None}


# ---------- BƯỚC 2 + 3: Xử lý theo ý định & soạn câu trả lời ----------

SYSTEM_PROMPT_TRA_LOI = """Bạn là trợ lý CSKH của Bưu điện Thành phố.
Giọng điệu: lịch sự, ngắn gọn, chuyên nghiệp, xưng "chúng tôi".
CHỈ sử dụng thông tin được cung cấp trong phần "DỮ LIỆU" bên dưới để trả lời.
KHÔNG được tự bịa thêm thông tin (số tiền, ngày tháng, trạng thái...) ngoài dữ liệu đã cho.
Nếu dữ liệu không có thông tin khách cần, hãy xin lỗi và đề nghị khách cung cấp thêm hoặc liên hệ tổng đài."""


def tao_cau_tra_loi(message: str, du_lieu: str) -> str:
    prompt = f"{SYSTEM_PROMPT_TRA_LOI}\n\nDỮ LIỆU:\n{du_lieu}\n\nCâu hỏi của khách: {message}"
    return goi_gemini_co_retry(prompt)


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    message = request.message
    phan_loai = phan_loai_y_dinh(message)
    intent = phan_loai.get("intent", "khac")

    if intent == "tra_cuu_don_hang":
        ma_van_don = phan_loai.get("ma_van_don")
        if not ma_van_don:
            reply = "Bạn vui lòng cung cấp mã vận đơn để chúng tôi tra cứu giúp bạn nhé."
        else:
            don_hang = db_utils.tra_cuu_don_hang(ma_van_don)
            if don_hang:
                du_lieu = json.dumps(don_hang, ensure_ascii=False)
            else:
                du_lieu = f"Không tìm thấy đơn hàng với mã '{ma_van_don}' trong hệ thống."
            reply = tao_cau_tra_loi(message, du_lieu)

    elif intent == "hoi_faq":
        # Lấy toàn bộ FAQ cho Gemini tự chọn câu phù hợp nhất (18 câu là số lượng nhỏ, ổn để đưa hết)
        faq_list = db_utils.lay_toan_bo_faq()
        du_lieu = json.dumps(faq_list, ensure_ascii=False)
        reply = tao_cau_tra_loi(message, du_lieu)

    elif intent == "khieu_nai":
        loai = phan_loai.get("loai_khieu_nai") or "khac"
        ma_van_don = phan_loai.get("ma_van_don")
        ticket_id = db_utils.tao_ticket(ma_van_don, loai, message)
        du_lieu = f"Đã tạo ticket khiếu nại thành công, mã ticket: {ticket_id}, loại: {loai}."
        reply = tao_cau_tra_loi(message, du_lieu)

    else:
        reply = tao_cau_tra_loi(message, "Không có dữ liệu đặc biệt - đây là tin nhắn ngoài phạm vi tra cứu/FAQ/khiếu nại.")

    return ChatResponse(reply=reply, intent=intent)


@app.get("/")
def health_check():
    return {"status": "Chatbot đang chạy OK"}