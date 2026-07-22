# Hướng dẫn chi tiết dự án: Chatbot AI hỗ trợ CSKH Bưu điện
### (Dùng cho báo cáo thực tập Công nghệ thông tin — thời gian thực hiện: 4 tuần)

## Mục lục

1. [Tổng quan dự án](#1-tổng-quan-dự-án)
2. [Phạm vi & mục tiêu cụ thể](#2-phạm-vi--mục-tiêu-cụ-thể)
3. [Kiến trúc hệ thống](#3-kiến-trúc-hệ-thống)
4. [Công nghệ sử dụng](#4-công-nghệ-sử-dụng)
5. [Thiết kế dữ liệu mô phỏng](#5-thiết-kế-dữ-liệu-mô-phỏng)
6. [Thiết kế kịch bản hội thoại & System Prompt](#6-thiết-kế-kịch-bản-hội-thoại--system-prompt)
7. [Kế hoạch chi tiết theo tuần](#7-kế-hoạch-chi-tiết-theo-tuần)
8. [Hướng dẫn kỹ thuật từng bước](#8-hướng-dẫn-kỹ-thuật-từng-bước)
9. [Kế hoạch kiểm thử & đánh giá](#9-kế-hoạch-kiểm-thử--đánh-giá)
10. [Cấu trúc báo cáo thực tập](#10-cấu-trúc-báo-cáo-thực-tập)
11. [Câu hỏi demo chuẩn bị cho buổi bảo vệ](#11-câu-hỏi-demo-chuẩn-bị-cho-buổi-bảo-vệ)
12. [Rủi ro thường gặp & cách xử lý](#12-rủi-ro-thường-gặp--cách-xử-lý)
13. [Hướng phát triển mở rộng (nếu còn thời gian)](#13-hướng-phát-triển-mở-rộng)

---

## 1. Tổng quan dự án

**Tên dự án:** Chatbot AI hỗ trợ chăm sóc khách hàng (CSKH) tại Bưu điện Thành phố

**Bối cảnh:** Trong quy trình vận hành thực tế tại bưu điện, bộ phận CSKH tiếp nhận lượng lớn câu hỏi lặp lại từ khách hàng (tra cứu đơn hàng, hỏi phí dịch vụ, khiếu nại chậm giao...) thông qua hệ thống CRM và phần mềm Case. Việc xử lý thủ công gây quá tải nhân sự và chậm phản hồi khách hàng.

**Đề xuất giải pháp:** Xây dựng một chatbot ứng dụng AI (Large Language Model) có khả năng:
- Trả lời tự động các câu hỏi thường gặp (FAQ) về nghiệp vụ bưu chính
- Tra cứu trạng thái đơn hàng theo mã vận đơn
- Tiếp nhận và phân loại khiếu nại, tự động tạo "ticket" chuyển cho nhân viên CSKH xử lý tiếp

**Lưu ý quan trọng khi viết báo cáo:** Vì sinh viên thực tập không có quyền truy cập hệ thống thật (MPITS, CRM nội bộ), dự án sử dụng **dữ liệu mô phỏng** được xây dựng dựa trên quy trình nghiệp vụ quan sát thực tế tại đơn vị thực tập. Đây là cách làm được chấp nhận rộng rãi cho đồ án/báo cáo thực tập — cần nêu rõ điều này trong phần "Giới hạn của đề tài".

---

## 2. Phạm vi & mục tiêu cụ thể

### Trong phạm vi (làm)
- [ ] Chatbot trả lời FAQ về: giờ làm việc, cách đóng gói, phí COD, thời gian đối soát COD (3-7 ngày), quy trình gửi hàng, dịch vụ EMS/bưu phẩm bảo đảm
- [ ] Tra cứu trạng thái đơn hàng theo mã vận đơn (dữ liệu mô phỏng dạng bảng)
- [ ] Tiếp nhận mô tả khiếu nại, phân loại theo 3-4 nhóm (chậm giao / mất hàng / sai COD / khác), tạo ticket có mã số
- [ ] Giao diện chat web đơn giản
- [ ] Ghi log hội thoại để phục vụ đánh giá

### Ngoài phạm vi (không làm — nêu rõ trong báo cáo là "hướng phát triển")
- Kết nối trực tiếp hệ thống thật của bưu điện (MPITS, CRM, PNS)
- Xử lý giọng nói (voice)
- Đa ngôn ngữ
- Thanh toán/giao dịch tài chính thật

### Mục tiêu đo lường được
- Chatbot trả lời đúng ≥ 80% trên bộ 20-30 câu hỏi test
- Thời gian phản hồi trung bình < 3 giây
- Phân loại đúng loại khiếu nại ≥ 75%

---

## 3. Kiến trúc hệ thống

```
┌─────────────┐
│  Khách hàng │  (nhập câu hỏi qua giao diện web chat)
└──────┬──────┘
       │
       ▼
┌─────────────────────────────┐
│   Chatbot Engine             │
│   (NLU/Intent qua LLM API)   │
└──────┬──────┬──────┬─────────┘
       │      │      │
       ▼      ▼      ▼
  ┌────────┐ ┌──────┐ ┌───────────┐
  │Tra cứu │ │ FAQ  │ │ Khiếu nại │
  │đơn hàng│ │      │ │(tạo ticket)│
  └───┬────┘ └──┬───┘ └─────┬─────┘
      │         │           │
      ▼         ▼           ▼
┌───────────────────────────────────┐
│  Dữ liệu mô phỏng (SQLite/JSON)    │
│  - Bảng đơn hàng                   │
│  - Bảng FAQ                        │
│  - Bảng ticket khiếu nại           │
│  → ticket khiếu nại chuyển CSKH    │
└───────────────────────────────────┘
```

**Luồng xử lý một câu hỏi:**
1. Khách hàng nhập câu hỏi trên giao diện web
2. Backend nhận request, gửi câu hỏi + system prompt tới LLM API
3. LLM phân loại ý định (intent): `tra_cuu_don_hang` / `faq` / `khieu_nai` / `khong_xac_dinh`
4. Backend gọi hàm xử lý tương ứng (query database, tìm FAQ, hoặc tạo ticket)
5. Kết quả được đưa trở lại LLM để tạo câu trả lời tự nhiên, hoặc trả trực tiếp nếu là FAQ
6. Trả kết quả về giao diện chat

---

## 4. Công nghệ sử dụng

| Thành phần | Công nghệ đề xuất | Lý do chọn |
| --- | --- | --- |
| LLM/AI | Anthropic Claude API hoặc OpenAI API | Không cần tự train model, tiết kiệm thời gian, chất lượng cao |
| Backend | Python + FastAPI | Nhẹ, dễ viết, tài liệu phong phú, sinh viên dễ tiếp cận |
| Database | SQLite (file `.db`) | Không cần cài server riêng, đủ dùng cho demo |
| Frontend | HTML/CSS/JavaScript thuần (hoặc Streamlit nếu muốn nhanh) | Đơn giản, dễ demo, không cần framework phức tạp |
| Quản lý mã nguồn | Git + GitHub | Chuẩn công nghiệp, dễ trình bày trong báo cáo |

**Yêu cầu môi trường:**
- Python 3.10+
- Tài khoản API key (Anthropic hoặc OpenAI — sinh viên có thể đăng ký gói miễn phí/dùng thử)
- Trình soạn thảo code: VS Code (khuyến nghị)

---

## 5. Thiết kế dữ liệu mô phỏng

### Bảng `orders` (đơn hàng)
| Cột | Kiểu dữ liệu | Mô tả |
| --- | --- | --- |
| ma_van_don | TEXT (PK) | Mã vận đơn, VD: `EV123456789VN` |
| ten_nguoi_gui | TEXT | Tên người gửi |
| ten_nguoi_nhan | TEXT | Tên người nhận |
| dia_chi_nhan | TEXT | Địa chỉ giao hàng |
| trang_thai | TEXT | Một trong: `Đã tiếp nhận`, `Đang vận chuyển`, `Đang giao`, `Đã giao thành công`, `Chuyển hoàn` |
| ngay_gui | DATE | Ngày tiếp nhận |
| ngay_du_kien_giao | DATE | Ngày dự kiến giao |
| so_tien_cod | INTEGER | Số tiền thu hộ (0 nếu không COD) |
| loai_dich_vu | TEXT | `EMS`, `Bưu phẩm bảo đảm`, `Bưu kiện thường` |

**Dữ liệu mẫu cần tạo:** 20-30 dòng, đa dạng trạng thái để test đầy đủ tình huống.

### Bảng `faq` (câu hỏi thường gặp)
| Cột | Kiểu dữ liệu | Mô tả |
| --- | --- | --- |
| id | INTEGER (PK) | |
| chu_de | TEXT | VD: `gio_lam_viec`, `phi_cod`, `dong_goi`, `thoi_gian_giao` |
| cau_hoi_mau | TEXT | Câu hỏi mẫu để đối chiếu |
| cau_tra_loi | TEXT | Nội dung trả lời chuẩn (dựa theo quy trình thực tế) |

**Gợi ý 15-20 chủ đề FAQ dựa trên tài liệu quy trình bưu điện:**
- Giờ làm việc bưu cục (7h30-17h30 T2-T6, có thể đến 19h-20h ở trung tâm)
- Thời gian toàn trình EMS (1-2 ngày nội vùng)
- Thời gian đối soát/chi trả COD (3-7 ngày làm việc)
- Quy cách đóng gói theo từng loại hàng (điện tử, hàng lỏng, tài liệu, tranh cuộn)
- Cách tra cứu đơn hàng
- Quy trình khiếu nại và thời gian xử lý
- Dịch vụ tiết kiệm bưu điện, PostPay
- Chính sách bồi thường bảo hiểm PTI (15 ngày làm việc)

### Bảng `tickets` (khiếu nại)
| Cột | Kiểu dữ liệu | Mô tả |
| --- | --- | --- |
| ticket_id | TEXT (PK) | Mã tự sinh, VD: `TK-20260702-001` |
| ma_van_don | TEXT | Liên kết đơn hàng liên quan (nếu có) |
| loai_khieu_nai | TEXT | `cham_giao`, `mat_hang`, `sai_cod`, `khac` |
| noi_dung | TEXT | Mô tả khách hàng nhập |
| trang_thai | TEXT | `Mới tạo`, `Đang xử lý`, `Đã giải quyết` |
| thoi_gian_tao | DATETIME | |

---

## 6. Thiết kế kịch bản hội thoại & System Prompt

### System prompt gợi ý (điều chỉnh theo nhu cầu)

```
Bạn là trợ lý ảo chăm sóc khách hàng của Bưu điện Thành phố.

NHIỆM VỤ:
1. Trả lời câu hỏi về dịch vụ bưu chính dựa trên thông tin FAQ được cung cấp
2. Tra cứu trạng thái đơn hàng khi khách cung cấp mã vận đơn
3. Tiếp nhận khiếu nại: hỏi thông tin cần thiết (mã đơn nếu có, mô tả vấn đề),
   sau đó phân loại vào một trong: cham_giao / mat_hang / sai_cod / khac

QUY TẮC BẮT BUỘC:
- CHỈ trả lời các câu hỏi liên quan đến dịch vụ bưu điện. Nếu khách hỏi chuyện
  ngoài phạm vi, lịch sự từ chối và hướng họ quay lại chủ đề bưu chính.
- KHÔNG bịa đặt thông tin về đơn hàng hoặc chính sách không có trong dữ liệu
  được cung cấp. Nếu không tìm thấy thông tin, trả lời trung thực là chưa có
  dữ liệu và đề nghị chuyển nhân viên hỗ trợ.
- Giọng điệu: lịch sự, ngắn gọn, chuyên nghiệp, xưng "bưu điện" hoặc "chúng tôi".
- Khi khách cung cấp mã vận đơn, luôn xác nhận lại mã trước khi trả lời.
```

### 12 kịch bản hội thoại mẫu (dùng để test và làm phụ lục báo cáo)

1. Khách hỏi giờ làm việc bưu cục
2. Khách hỏi phí gửi hàng COD
3. Khách tra cứu đơn hàng bằng mã vận đơn hợp lệ
4. Khách tra cứu đơn hàng bằng mã vận đơn không tồn tại
5. Khách hỏi cách đóng gói hàng dễ vỡ
6. Khách khiếu nại đơn hàng giao chậm
7. Khách khiếu nại chưa nhận được tiền COD
8. Khách hỏi thời gian bồi thường bảo hiểm PTI
9. Khách hỏi ngoài phạm vi (VD: hỏi về thời tiết) → chatbot từ chối lịch sự
10. Khách hỏi liên tiếp nhiều câu trong một hội thoại (kiểm tra ngữ cảnh)
11. Khách yêu cầu nói chuyện với nhân viên thật
12. Khách cung cấp thông tin khiếu nại không đầy đủ → chatbot hỏi lại

---

## 7. Kế hoạch chi tiết theo tuần

### Tuần 1 — Nghiên cứu & thiết kế
| Ngày | Công việc | Kết quả cần đạt |
| --- | --- | --- |
| 1-2 | Thu thập câu hỏi CSKH thực tế, hoàn thiện danh sách FAQ | File danh sách 15-20 FAQ |
| 3-4 | Thiết kế schema database (mục 5), tạo dữ liệu mẫu | File SQL/JSON dữ liệu mẫu |
| 5-6 | Viết 12 kịch bản hội thoại, soạn system prompt | Tài liệu kịch bản hoàn chỉnh |
| 7 | Review lại toàn bộ thiết kế | Sẵn sàng bước sang code |

### Tuần 2 — Xây dựng lõi chatbot
| Ngày | Công việc | Kết quả cần đạt |
| --- | --- | --- |
| 1-2 | Setup môi trường Python, FastAPI, kết nối LLM API | API endpoint `/chat` gọi được LLM |
| 3-4 | Tạo database SQLite, viết hàm truy vấn đơn hàng/FAQ | Hàm `query_order()`, `search_faq()` hoạt động |
| 5-6 | Tích hợp logic phân loại ý định (intent classification) | Chatbot phân biệt được 3 loại câu hỏi |
| 7 | Test thủ công 12 kịch bản | Ghi log kết quả |

### Tuần 3 — Tích hợp chức năng & giao diện
| Ngày | Công việc | Kết quả cần đạt |
| --- | --- | --- |
| 1-2 | Hoàn thiện chức năng tạo ticket khiếu nại | Ticket được lưu vào DB đúng định dạng |
| 3-4 | Xây giao diện web chat (HTML/CSS/JS) | Giao diện chat cơ bản chạy được |
| 5-6 | Kết nối frontend-backend, test end-to-end | Demo chạy trọn luồng |
| 7 | Sửa lỗi phát sinh | Hệ thống ổn định |

### Tuần 4 — Hoàn thiện, kiểm thử, viết báo cáo
| Ngày | Công việc | Kết quả cần đạt |
| --- | --- | --- |
| 1-2 | Kiểm thử toàn diện 20-30 câu hỏi, tính tỷ lệ đúng | Bảng kết quả đánh giá |
| 3 | Tối ưu prompt dựa trên lỗi phát hiện | Cải thiện độ chính xác |
| 4-5 | Viết báo cáo thực tập (theo mục 10) | Bản nháp báo cáo |
| 6 | Chuẩn bị slide + kịch bản demo | Slide thuyết trình |
| 7 | Rà soát tổng thể, in ấn/nộp | Hoàn tất |

---

## 8. Hướng dẫn kỹ thuật từng bước

> Phần này viết dưới dạng "công thức" để bạn đưa cho AI khác nhờ code cụ thể theo từng bước.

### Bước 1: Setup backend cơ bản
**Yêu cầu gửi cho AI:** *"Viết cho tôi một FastAPI app cơ bản với 1 endpoint POST /chat nhận {message: string} và trả về {reply: string}, dùng Anthropic Claude API để sinh câu trả lời."*

### Bước 2: Tạo database và dữ liệu mẫu
**Yêu cầu gửi cho AI:** *"Viết script Python tạo database SQLite với 3 bảng: orders, faq, tickets theo schema sau [dán mục 5 vào], sau đó chèn dữ liệu mẫu: 25 đơn hàng, 18 câu FAQ."*

### Bước 3: Xây dựng logic phân loại ý định
**Yêu cầu gửi cho AI:** *"Viết hàm Python nhận câu hỏi của khách, gọi Claude API với system prompt sau [dán system prompt ở mục 6], yêu cầu Claude trả về JSON dạng {intent: 'tra_cuu_don_hang'|'faq'|'khieu_nai'|'khac', ma_van_don: string hoặc null}."*

### Bước 4: Xử lý từng loại ý định
**Yêu cầu gửi cho AI:** *"Viết 3 hàm Python: (1) tra_cuu_don_hang(ma_van_don) query bảng orders và trả kết quả dạng câu trả lời tự nhiên, (2) tra_cuu_faq(cau_hoi) tìm FAQ phù hợp nhất, (3) tao_ticket(loai, noi_dung, ma_van_don) tạo dòng mới trong bảng tickets với mã tự sinh dạng TK-YYYYMMDD-XXX."*

### Bước 5: Giao diện chat
**Yêu cầu gửi cho AI:** *"Viết giao diện chat web đơn giản bằng HTML/CSS/JS thuần: có ô nhập tin nhắn, nút gửi, khung hiển thị hội thoại dạng bong bóng chat, gọi API POST /chat ở localhost:8000."*

### Bước 6: Kết nối và test toàn bộ
**Yêu cầu gửi cho AI:** *"Giúp tôi kiểm tra và sửa lỗi khi kết nối frontend HTML với backend FastAPI, xử lý CORS nếu cần."*

---

## 9. Kế hoạch kiểm thử & đánh giá

### Bộ câu hỏi test (chuẩn bị 25-30 câu, chia đều 4 nhóm)
- 8 câu FAQ (các chủ đề khác nhau)
- 8 câu tra cứu đơn hàng (bao gồm cả mã không tồn tại)
- 8 câu khiếu nại (đủ 4 loại)
- 5 câu ngoài phạm vi hoặc mơ hồ (test khả năng từ chối lịch sự / hỏi lại)

### Bảng đánh giá kết quả (mẫu để điền vào báo cáo)
| STT | Câu hỏi | Kết quả mong đợi | Kết quả thực tế | Đúng/Sai |
| --- | --- | --- | --- | --- |
| 1 | ... | ... | ... | ... |

### Chỉ số cần tính
- Tỷ lệ trả lời đúng tổng thể (%)
- Tỷ lệ phân loại đúng ý định (%)
- Thời gian phản hồi trung bình (giây)
- Số lỗi "AI bịa thông tin" (quan trọng — hội đồng hay hỏi về vấn đề này)

---

## 10. Cấu trúc báo cáo thực tập

1. **Mở đầu:** Lý do chọn đề tài, mục tiêu, phạm vi
2. **Chương 1 — Tổng quan đơn vị thực tập:** Giới thiệu Bưu điện Thành phố, quy trình vận hành (dùng tài liệu bạn đã có)
3. **Chương 2 — Cơ sở lý thuyết:** Giới thiệu về LLM/Chatbot AI, kiến trúc hệ thống chatbot nói chung
4. **Chương 3 — Phân tích & thiết kế hệ thống:** Sơ đồ kiến trúc, thiết kế database, thiết kế kịch bản hội thoại
5. **Chương 4 — Triển khai:** Công nghệ sử dụng, các bước xây dựng, ảnh chụp màn hình code/giao diện quan trọng
6. **Chương 5 — Kiểm thử & đánh giá kết quả:** Bảng test, chỉ số đo lường, phân tích ưu/nhược điểm
7. **Kết luận & hướng phát triển:** Kết quả đạt được, hạn chế (dữ liệu mô phỏng, chưa kết nối hệ thống thật), đề xuất mở rộng
8. **Phụ lục:** Toàn bộ code quan trọng, danh sách FAQ, kịch bản hội thoại

---

## 11. Câu hỏi demo chuẩn bị cho buổi bảo vệ

Chuẩn bị sẵn để chủ động demo, tránh hội đồng hỏi ngoài phạm vi dữ liệu:
1. "Bưu cục làm việc giờ nào?"
2. "Phí COD được đối soát trong bao lâu?"
3. "Đơn hàng mã EV123456789VN đang ở đâu?" *(dùng mã có thật trong dữ liệu mẫu)*
4. "Tôi muốn khiếu nại đơn hàng giao chậm 3 ngày"
5. Một câu hỏi ngoài phạm vi để cho thấy chatbot từ chối đúng cách (VD: "Bạn có thể đặt vé máy bay giúp tôi không?")

---

## 12. Rủi ro thường gặp & cách xử lý

| Rủi ro | Cách phòng tránh |
| --- | --- |
| Chatbot "bịa" thông tin không có trong dữ liệu | Ràng buộc chặt system prompt, luôn yêu cầu chatbot chỉ dùng dữ liệu được cung cấp (kỹ thuật gọi là RAG cơ bản) |
| Hết thời gian vì cố làm giao diện đẹp | Ưu tiên chức năng chạy đúng trước, giao diện đơn giản là đủ điểm |
| API key hết hạn mức miễn phí | Đăng ký sớm, theo dõi usage, có phương án backup (dùng model khác) |
| Không có dữ liệu thật để đối chiếu | Nêu rõ trong báo cáo là dữ liệu mô phỏng dựa trên quan sát thực tế, không cố "giả vờ" là dữ liệu thật |
| Hội đồng hỏi về bảo mật dữ liệu khách hàng | Chuẩn bị sẵn câu trả lời: dự án dùng dữ liệu mô phỏng, không xử lý dữ liệu cá nhân thật, nêu hướng bảo mật nếu triển khai thật (mã hoá, phân quyền truy cập) |

---

## 13. Hướng phát triển mở rộng

*(Chỉ làm nếu còn dư thời gian sau tuần 3, hoặc nêu trong phần "Kết luận" như định hướng tương lai)*

- Kết nối RAG (Retrieval-Augmented Generation) với tài liệu quy trình đầy đủ thay vì chỉ FAQ tĩnh
- Thêm phân tích cảm xúc khách hàng (phát hiện khách đang bức xúc để ưu tiên xử lý)
- Dashboard thống kê cho CSKH xem số lượng ticket theo loại/thời gian
- Tích hợp thật với API tra cứu vận đơn công khai (nếu bưu điện có cung cấp)
- Hỗ trợ đa kênh (tích hợp Zalo OA, Facebook Messenger)

---

*Tài liệu này được soạn để hỗ trợ sinh viên thực tập ngành Công nghệ thông tin triển khai dự án chatbot AI CSKH dựa trên quy trình vận hành thực tế quan sát tại đơn vị thực tập bưu điện.*
