# Chatbot CSKH Bưu điện Thành phố

Chatbot hỗ trợ chăm sóc khách hàng cho bưu điện, xây dựng trong khuôn khổ thực tập
ngành Công nghệ Thông tin. Chatbot hỗ trợ 3 chức năng chính: tra cứu đơn hàng,
trả lời câu hỏi thường gặp (FAQ), và tiếp nhận khiếu nại của khách hàng.

## Tính năng chính

- **Tra cứu đơn hàng**: khách cung cấp mã vận đơn, chatbot trả về trạng thái thực tế
- **Hỏi đáp FAQ**: trả lời 18 câu hỏi thường gặp về dịch vụ bưu điện
- **Tiếp nhận khiếu nại**: tự động tạo ticket khiếu nại khi khách phàn nàn

## Kiến trúc hệ thống

Chatbot sử dụng kỹ thuật phân loại ý định 2 bước (two-call pattern) với Gemini API:

1. **Bước phân loại**: xác định ý định của khách (`tra_cuu_don_hang` / `hoi_faq` / `khieu_nai` / `khac`)
2. **Bước truy vấn**: lấy dữ liệu thật từ SQLite (đơn hàng / FAQ / tạo ticket)
3. **Bước trả lời**: Gemini soạn câu trả lời tự nhiên, chỉ dựa trên dữ liệu thật (kỹ thuật RAG),
   không tự bịa thông tin

## Công nghệ sử dụng

| Thành phần | Công nghệ |
|---|---|
| Backend | Python, FastAPI |
| AI Model | Google Gemini (`gemini-2.5-flash-lite`) |
| Database | SQLite |
| Frontend | HTML/CSS/JavaScript thuần |

## Cấu trúc thư mục

```
chatbot_project/
├── main.py              # FastAPI app, xử lý luồng chat
├── db_utils.py           # Các hàm truy vấn database
├── create_db.py           # Script khởi tạo database từ dữ liệu JSON
├── FAQ.json               # Dữ liệu 18 câu hỏi thường gặp
├── order.json              # Dữ liệu 30 đơn hàng mẫu
├── requirements.txt         # Danh sách thư viện Python cần cài
├── .env                       # API key (KHÔNG commit lên Git)
└── .gitignore
```

## Hướng dẫn cài đặt và chạy

1. Clone repository:
   ```bash
   git clone <đường dẫn repo của bạn>
   cd chatbot_project
   ```

2. Tạo virtual environment và cài thư viện:
   ```bash
   python -m venv venv
   venv\Scripts\activate       # Windows
   source venv/bin/activate    # macOS/Linux
   pip install -r requirements.txt
   ```

3. Tạo file `.env` chứa API key Gemini:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

4. Khởi tạo database:
   ```bash
   python create_db.py
   ```

5. Chạy server:
   ```bash
   uvicorn main:app --reload
   ```

6. Truy cập `http://127.0.0.1:8000/docs` để test API.

## Ghi chú

Dự án sử dụng dữ liệu mô phỏng (đơn hàng, FAQ mẫu), không kết nối trực tiếp
vào hệ thống nghiệp vụ thật của bưu điện, nhằm giữ phạm vi phù hợp với thời
gian thực tập.

## Tác giả

Sinh viên thực tập ngành Công nghệ Thông tin — Bưu điện Thành phố.