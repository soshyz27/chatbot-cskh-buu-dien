"""
Chatbot CSKH bưu điện - Bản có nhớ ngữ cảnh hội thoại (Tuần 2, bổ sung)

Điểm mới so với bản trước:
- Mỗi hội thoại có 1 session_id, lịch sử được lưu tạm trong RAM (dict `sessions`)
- Lịch sử hội thoại được đưa vào cả bước phân loại ý định và bước trả lời,
  giúp chatbot "nhớ" được các câu hỏi/khiếu nại trước đó trong cùng phiên
- Thêm cờ "du_thong_tin": chỉ tạo ticket khi mô tả khiếu nại đã đủ rõ,
  nếu còn thiếu thì chatbot hỏi lại (không tạo ticket vội)

Lưu ý: lưu trong RAM nghĩa là lịch sử MẤT khi restart server - với quy mô
đồ án/demo là chấp nhận được. Nếu triển khai thật cần lưu vào database.
"""

import os
import re
import json
import time
import uuid
from fastapi import FastAPI
from fastapi.responses import FileResponse
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

# ---------- Lưu trữ lịch sử hội thoại theo session (tạm thời, trong RAM) ----------
# Dạng: { session_id: [ ("user", "..."), ("bot", "..."), ... ] }
sessions: dict[str, list[tuple[str, str]]] = {}

SO_LUOT_NHO_TOI_DA = 6  # chỉ nhớ 6 lượt gần nhất, tránh prompt quá dài


def lay_lich_su(session_id: str) -> str:
    lich_su = sessions.get(session_id, [])
    gan_day = lich_su[-SO_LUOT_NHO_TOI_DA:]
    if not gan_day:
        return "(Chưa có lịch sử - đây là tin nhắn đầu tiên trong phiên)"
    dong = []
    for vai_tro, noi_dung in gan_day:
        nhan = "Khách" if vai_tro == "user" else "Chatbot"
        dong.append(f"{nhan}: {noi_dung}")
    return "\n".join(dong)


def luu_vao_lich_su(session_id: str, vai_tro: str, noi_dung: str):
    sessions.setdefault(session_id, []).append((vai_tro, noi_dung))


def goi_gemini_co_retry(contents: str, so_lan_thu: int = 3) -> str:
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
    session_id: str | None = None  # nếu không gửi, server tự tạo mới


class ChatResponse(BaseModel):
    reply: str
    intent: str
    session_id: str  # trả về để frontend gửi lại ở lượt sau


# ---------- BƯỚC 1: Phân loại ý định (có xét lịch sử hội thoại) ----------

INTENT_PROMPT_TEMPLATE = """Phân loại tin nhắn MỚI NHẤT của khách hàng bưu điện, dựa trên cả lịch sử hội thoại bên dưới (nếu có).

LỊCH SỬ HỘI THOẠI GẦN ĐÂY:
{lich_su}

Phân vào đúng 1 trong 4 nhãn:
- "tra_cuu_don_hang": khách hỏi về trạng thái/tình trạng một đơn hàng cụ thể
- "hoi_faq": khách hỏi thông tin chung (giờ làm việc, cách đóng gói, phí, dịch vụ...)
- "khieu_nai": khách phàn nàn, báo lỗi, hoặc đang tiếp tục cung cấp thông tin cho một khiếu nại đã bắt đầu ở lượt trước
- "khac": không thuộc 3 loại trên (chào hỏi, hỏi ngoài phạm vi bưu điện, yêu cầu gặp nhân viên thật...)

Nếu là "tra_cuu_don_hang": cố gắng trích mã vận đơn (dạng chữ+số, VD: E88392011VN, R77402195VN, hoặc chỉ số+VN).

Nếu là "khieu_nai":
- Trích loại khiếu nại: "cham_giao" / "mat_hang" / "sai_cod" / "khac"
- Đánh giá "du_thong_tin": true nếu đã có mô tả CỤ THỂ về vấn đề (VD: nói rõ chậm bao lâu, mã đơn nào, thiếu bao nhiêu tiền...),
  false nếu khách mới nói chung chung kiểu "tôi muốn khiếu nại" mà chưa có chi tiết gì
- Nếu lượt trước bot đã hỏi thêm thông tin và khách vừa bổ sung ở tin nhắn mới nhất, hãy TỔNG HỢP cả nội dung khiếu nại
  từ lịch sử + tin nhắn mới vào trường "noi_dung_day_du"

CHỈ trả về JSON, không thêm chữ nào khác, đúng định dạng:
{{"intent": "...", "ma_van_don": "..." hoặc null, "loai_khieu_nai": "..." hoặc null, "du_thong_tin": true/false hoặc null, "noi_dung_day_du": "..." hoặc null}}

Tin nhắn MỚI NHẤT của khách: {message}"""


def phan_loai_y_dinh(message: str, session_id: str) -> dict:
    lich_su = lay_lich_su(session_id)
    prompt = INTENT_PROMPT_TEMPLATE.format(lich_su=lich_su, message=message)
    text = goi_gemini_co_retry(prompt).strip()
    text = re.sub(r"^```json|```$", "", text, flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "intent": "khac", "ma_van_don": None, "loai_khieu_nai": None,
            "du_thong_tin": None, "noi_dung_day_du": None,
        }


# ---------- BƯỚC 2 + 3: Xử lý theo ý định & soạn câu trả lời (có xét lịch sử) ----------

SYSTEM_PROMPT_TRA_LOI = """Bạn là trợ lý CSKH của Bưu điện Thành phố.
Giọng điệu: lịch sự, ngắn gọn, chuyên nghiệp, xưng "chúng tôi".
CHỈ sử dụng thông tin được cung cấp trong phần "DỮ LIỆU" để trả lời.
KHÔNG được tự bịa thêm thông tin ngoài dữ liệu đã cho.
Nếu khách hỏi ngoài phạm vi dịch vụ bưu điện, lịch sự từ chối và hướng khách quay lại chủ đề bưu chính.
Hãy tham khảo lịch sử hội thoại để trả lời liền mạch, không hỏi lại thông tin khách đã cung cấp rồi."""


def tao_cau_tra_loi(message: str, du_lieu: str, session_id: str) -> str:
    lich_su = lay_lich_su(session_id)
    prompt = (
        f"{SYSTEM_PROMPT_TRA_LOI}\n\n"
        f"LỊCH SỬ HỘI THOẠI GẦN ĐÂY:\n{lich_su}\n\n"
        f"DỮ LIỆU:\n{du_lieu}\n\n"
        f"Tin nhắn MỚI NHẤT của khách: {message}"
    )
    return goi_gemini_co_retry(prompt)


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())
    message = request.message

    phan_loai = phan_loai_y_dinh(message, session_id)
    intent = phan_loai.get("intent", "khac")

    if intent == "tra_cuu_don_hang":
        ma_van_don = phan_loai.get("ma_van_don")
        if not ma_van_don:
            reply = "Bạn vui lòng cung cấp mã vận đơn để chúng tôi tra cứu giúp bạn nhé."
        else:
            don_hang = db_utils.tra_cuu_don_hang(ma_van_don)
            du_lieu = (
                json.dumps(don_hang, ensure_ascii=False)
                if don_hang
                else f"Không tìm thấy đơn hàng với mã '{ma_van_don}' trong hệ thống."
            )
            reply = tao_cau_tra_loi(message, du_lieu, session_id)

    elif intent == "hoi_faq":
        faq_list = db_utils.lay_toan_bo_faq()
        du_lieu = json.dumps(faq_list, ensure_ascii=False)
        reply = tao_cau_tra_loi(message, du_lieu, session_id)

    elif intent == "khieu_nai":
        du_thong_tin = phan_loai.get("du_thong_tin")
        if du_thong_tin:
            loai = phan_loai.get("loai_khieu_nai") or "khac"
            ma_van_don = phan_loai.get("ma_van_don")
            noi_dung_day_du = phan_loai.get("noi_dung_day_du") or message
            ticket_id = db_utils.tao_ticket(ma_van_don, loai, noi_dung_day_du)
            du_lieu = f"Đã tạo ticket khiếu nại thành công, mã ticket: {ticket_id}, loại: {loai}."
        else:
            du_lieu = (
                "Khách đang khiếu nại nhưng CHƯA cung cấp đủ thông tin cụ thể. "
                "Hãy hỏi khách rõ hơn: mã vận đơn (nếu có), và mô tả cụ thể vấn đề gặp phải "
                "(VD: chậm bao nhiêu ngày, thiếu bao nhiêu tiền COD...). "
                "CHƯA tạo ticket ở bước này."
            )
        reply = tao_cau_tra_loi(message, du_lieu, session_id)

    else:
        reply = tao_cau_tra_loi(
            message,
            "Không có dữ liệu đặc biệt - tin nhắn ngoài phạm vi tra cứu/FAQ/khiếu nại.",
            session_id,
        )

    luu_vao_lich_su(session_id, "user", message)
    luu_vao_lich_su(session_id, "bot", reply)

    return ChatResponse(reply=reply, intent=intent, session_id=session_id)


@app.get("/")
def serve_frontend():
    return FileResponse("static/index.html")


@app.get("/health")
def health_check():
    return {"status": "Chatbot đang chạy OK"}