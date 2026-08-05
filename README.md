# Chatbot CSKH Bưu điện Thành phố

Chatbot hỗ trợ chăm sóc khách hàng cho bưu điện, xây dựng trong khuôn khổ thực tập
ngành Công nghệ Thông tin. Hệ thống hỗ trợ 4 chức năng chính: tra cứu đơn hàng, trực
quan hóa vị trí đơn hàng trên bản đồ, trả lời câu hỏi thường gặp (FAQ), và tiếp nhận
khiếu nại của khách hàng.

## Tính năng chính

- **Tra cứu đơn hàng**: khách cung cấp mã vận đơn, chatbot trả về trạng thái thực tế
- **Trực quan hóa vị trí đơn hàng trên bản đồ**: giao diện 2 cột (bản đồ 3/4 - chatbot 1/4), tra cứu mã
  vận đơn để xem vị trí hiện tại trên bản đồ thật (Leaflet + OpenStreetMap), phân biệt 5 trạng thái bằng
  icon riêng: đang vận chuyển/giao (🚚), đang chờ tại bưu cục (🏤), đã giao thành công (✅), chuyển hoàn (↩️)
- **Hỏi đáp FAQ**: trả lời 28 câu hỏi thường gặp về dịch vụ bưu điện (18 câu gốc + 10 câu bổ sung từ phân
  tích rủi ro vận hành thực tế)
- **Tiếp nhận khiếu nại**: tự động tạo ticket khiếu nại khi khách phàn nàn, chỉ tạo khi đã đủ thông tin
- **Ghi nhớ ngữ cảnh hội thoại**: chatbot nhớ 6 lượt trao đổi gần nhất trong cùng phiên
- **Cơ chế học có giám sát**: tự động ghi log câu hỏi chưa xử lý tốt, có công cụ CLI để admin xem lại và
  bổ sung FAQ mới sau kiểm duyệt

## Kiến trúc hệ thống

Chatbot sử dụng kỹ thuật phân loại ý định 2 bước (two-call pattern) với Gemini API:

1. **Bước phân loại**: xác định ý định của khách (`tra_cuu_don_hang` / `hoi_faq` / `khieu_nai` / `khac`)
2. **Bước truy vấn**: lấy dữ liệu thật từ SQLite (đơn hàng / FAQ / tạo ticket)
3. **Bước trả lời**: Gemini soạn câu trả lời tự nhiên, chỉ dựa trên dữ liệu thật (kỹ thuật RAG),
   không tự bịa thông tin

Phần bản đồ hoạt động độc lập với luồng chat, qua endpoint riêng `/tra-cuu-ban-do`:

1. Nhận mã vận đơn → tra cứu SQLite lấy trạng thái + địa chỉ liên quan
2. Geocode địa chỉ sang tọa độ (lat/lng) qua Nominatim (OpenStreetMap), có cache để tránh gọi API lặp lại
3. Trả về tọa độ + loại icon phù hợp cho frontend vẽ lên bản đồ Leaflet.js

## Công nghệ sử dụng

| Thành phần | Công nghệ |
|---|---|
| Backend | Python, FastAPI |
| AI Model | Google Gemini (`gemini-2.5-flash-lite`) |
| Database | SQLite |
| Bản đồ | Leaflet.js + OpenStreetMap (miễn phí, không cần API key) |
| Geocode | Nominatim (OpenStreetMap), có cache trong SQLite |
| Frontend | HTML/CSS/JavaScript thuần |

## Cấu trúc thư mục

```
chatbot_project/
├── main.py                    # FastAPI app, xử lý luồng chat + endpoint tra cứu bản đồ
├── db_utils.py                 # Các hàm truy vấn database
├── geocode_utils.py              # Geocode địa chỉ sang tọa độ (Nominatim), có cache
├── create_db.py                   # Script khởi tạo database từ dữ liệu JSON
├── FAQ.json                        # 28 câu FAQ (18 gốc + 10 bổ sung từ phân tích rủi ro vận hành)
├── order.json                          # 30 đơn hàng mẫu (đủ 5 trạng thái, có vị trí hiện tại)
├── xem_cau_hoi_chua_xu_ly.py             # CLI admin: xem log câu hỏi chưa xử lý + thêm FAQ
├── static/index.html                      # Giao diện 2 cột: bản đồ (3/4) + chatbot (1/4)
├── test_scenarios.md                       # Bộ 12 kịch bản kiểm thử
├── requirements.txt                         # Danh sách thư viện Python cần cài
├── .env                                       # API key (KHÔNG commit lên Git)
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

6. Truy cập `http://127.0.0.1:8000` để dùng giao diện chính (bản đồ + chatbot).
   Truy cập `http://127.0.0.1:8000/docs` nếu muốn test trực tiếp từng API endpoint.

## Ghi chú

Dự án sử dụng dữ liệu mô phỏng (đơn hàng, FAQ mẫu), không kết nối trực tiếp
vào hệ thống nghiệp vụ thật của bưu điện, nhằm giữ phạm vi phù hợp với thời
gian thực tập.

## Tác giả

Sinh viên thực tập ngành Công nghệ Thông tin — Bưu điện Thành phố.