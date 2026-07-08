# Bộ kiểm thử 12 kịch bản hội thoại — Chatbot CSKH Bưu điện

> Hướng dẫn: gõ nguyên văn cột "Câu gõ vào chatbot", so sánh với "Tiêu chí đạt",
> tick ✅/❌ vào cột cuối. Với kịch bản có nhiều lượt (10, 12), gõ từng dòng theo thứ tự.

---

### Kịch bản 1 — Hỏi giờ làm việc bưu cục
**Câu gõ vào chatbot:**
```
Bưu cục làm việc giờ nào?
```
**Tiêu chí đạt:** `intent: hoi_faq`, trả lời đúng "8h00–17h00 T2–T6" (theo FAQ #1 của bạn)

---

### Kịch bản 2 — Hỏi phí gửi hàng COD
**Câu gõ vào chatbot:**
```
Phí thu hộ COD tính thế nào?
```
**Tiêu chí đạt:** `intent: hoi_faq`, nội dung khớp FAQ #2 (tùy giá trị đơn hàng + hợp đồng)

---

### Kịch bản 3 — Tra cứu đơn hàng bằng mã hợp lệ
**Câu gõ vào chatbot:**
```
Cho tôi hỏi đơn R77402195VN đang ở đâu rồi?
```
**Tiêu chí đạt:** `intent: tra_cuu_don_hang`, trả lời đúng trạng thái **"Đang giao"** (theo order.json)

---

### Kịch bản 4 — Tra cứu đơn hàng bằng mã KHÔNG tồn tại
**Câu gõ vào chatbot:**
```
Đơn E00000000VN của tôi sao rồi?
```
**Tiêu chí đạt:** `intent: tra_cuu_don_hang`, chatbot báo **không tìm thấy**, KHÔNG được bịa trạng thái

---

### Kịch bản 5 — Hỏi cách đóng gói hàng dễ vỡ
**Câu gõ vào chatbot:**
```
Tôi muốn gửi ly thủy tinh, đóng gói thế nào cho an toàn?
```
**Tiêu chí đạt:** `intent: hoi_faq`, nội dung khớp FAQ #5 (bubble wrap, mút xốp, carton cứng)

---

### Kịch bản 6 — Khiếu nại đơn hàng giao chậm
**Câu gõ vào chatbot:**
```
Đơn E11940291VN của tôi giao chậm 4 ngày rồi, chưa thấy shipper liên hệ
```
**Tiêu chí đạt:** `intent: khieu_nai`, `loai_khieu_nai: cham_giao`, tạo ticket ngay (đã đủ thông tin), trả về mã ticket

---

### Kịch bản 7 — Khiếu nại chưa nhận được tiền COD
**Câu gõ vào chatbot:**
```
Tôi là người gửi đơn BK55201938VN, đã 10 ngày rồi mà chưa thấy chuyển khoản tiền COD 1.950.000đ
```
**Tiêu chí đạt:** `intent: khieu_nai`, `loai_khieu_nai: sai_cod`, tạo ticket, trả lời có nhắc thời gian đối soát chuẩn (3-7 ngày theo FAQ #3) để khách hiểu vì sao chậm hơn dự kiến

---

### Kịch bản 8 — Hỏi thời gian bồi thường bảo hiểm PTI
**Câu gõ vào chatbot:**
```
Bồi thường bảo hiểm PTI mất bao lâu vậy?
```
**Tiêu chí đạt:** `intent: hoi_faq`, trả lời đúng "15 ngày làm việc" (FAQ #13)

---

### Kịch bản 9 — Hỏi ngoài phạm vi (kiểm tra từ chối lịch sự)
**Câu gõ vào chatbot:**
```
Hôm nay thời tiết Hà Nội thế nào bạn?
```
**Tiêu chí đạt:** `intent: khac`, chatbot **từ chối lịch sự** và hướng khách quay lại chủ đề bưu chính — KHÔNG trả lời về thời tiết

---

### Kịch bản 10 — Hỏi liên tiếp nhiều câu (kiểm tra ngữ cảnh) — **3 lượt**
**Lượt 1:**
```
Đơn EMS20491823VN của tôi tới đâu rồi?
```
**Lượt 2 (không nhắc lại mã đơn):**
```
Vậy có tiền COD không?
```
**Lượt 3 (tiếp tục không nhắc lại mã):**
```
Bao giờ người gửi nhận được tiền đó?
```
**Tiêu chí đạt:** Cả 3 lượt bot đều hiểu đang nói về đơn `EMS20491823VN` (450.000đ COD, đã giao thành công) mà **không cần khách nhắc lại mã đơn** ở lượt 2, 3

---

### Kịch bản 11 — Yêu cầu gặp nhân viên thật
**Câu gõ vào chatbot:**
```
Tôi không muốn nói chuyện với bot nữa, cho tôi gặp nhân viên
```
**Tiêu chí đạt:** Chatbot xác nhận yêu cầu, hướng dẫn cách kết nối nhân viên hỗ trợ (theo FAQ #18), giọng điệu lịch sự không "cố giữ chân" khách ở lại với bot

---

### Kịch bản 12 — Khiếu nại thiếu thông tin → chatbot hỏi lại — **2 lượt**
**Lượt 1:**
```
Tôi muốn khiếu nại
```
**Lượt 2 (bổ sung sau khi bot hỏi lại):**
```
Đơn giao chậm, mã vận đơn là E11940291VN
```
**Tiêu chí đạt:** Lượt 1 bot **hỏi lại** thông tin (KHÔNG tạo ticket vội), lượt 2 mới tạo ticket sau khi đủ thông tin

✅ *(Đã test thành công kịch bản này trước đó)*

---

## Bảng tổng hợp kết quả (điền sau khi test)

| # | Kịch bản | Kết quả (✅/❌) | Ghi chú lỗi (nếu có) |
|---|---|---|---|
| 1 | Giờ làm việc | | |
| 2 | Phí COD | | |
| 3 | Tra cứu mã hợp lệ | | |
| 4 | Tra cứu mã không tồn tại | | |
| 5 | Đóng gói dễ vỡ | | |
| 6 | Khiếu nại giao chậm | | |
| 7 | Khiếu nại sai COD | | |
| 8 | Bồi thường PTI | | |
| 9 | Ngoài phạm vi | | |
| 10 | Ngữ cảnh đa lượt | | |
| 11 | Gặp nhân viên thật | | |
| 12 | Khiếu nại thiếu tin | ✅ | Đã test đạt |

**Mục tiêu theo đặc tả:** đạt ≥ 80% (tức tối thiểu 10/12 kịch bản đạt) mới coi là đạt yêu cầu demo.