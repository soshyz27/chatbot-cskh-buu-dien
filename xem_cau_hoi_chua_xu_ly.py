"""
Công cụ admin: xem lại các câu hỏi chatbot chưa xử lý tốt (intent = 'khac'),
và bổ sung FAQ mới sau khi bạn xác nhận câu trả lời đúng.

Đây chính là cơ chế "học có giám sát" (human-in-the-loop):
chatbot tự ghi log -> con người xem xét -> con người quyết định bổ sung.

Cách dùng:
    python xem_cau_hoi_chua_xu_ly.py            # xem danh sách câu hỏi chưa xử lý
    python xem_cau_hoi_chua_xu_ly.py --tat-ca   # xem cả câu đã xử lý
"""

import sys
import db_utils


def hien_thi_danh_sach(chi_lay_chua_xu_ly: bool = True):
    danh_sach = db_utils.lay_danh_sach_cau_hoi_chua_xu_ly(chi_lay_chua_xu_ly)

    if not danh_sach:
        print("✅ Không có câu hỏi nào đang chờ xử lý.")
        return

    print(f"\n{'=' * 60}")
    print(f"CÓ {len(danh_sach)} CÂU HỎI CẦN XEM XÉT")
    print(f"{'=' * 60}\n")

    for item in danh_sach:
        trang_thai = "Đã xử lý" if item["da_xu_ly"] else "Chưa xử lý"
        print(f"[ID {item['id']}] ({trang_thai}) - {item['thoi_gian']}")
        print(f"   Nội dung: {item['noi_dung']}")
        print()


def them_faq_tuong_tac():
    """Quy trình hỏi-đáp trên terminal để thêm 1 FAQ mới, có xác nhận trước khi lưu."""
    print("\n--- Thêm FAQ mới ---")
    chu_de = input("Chủ đề (VD: gio_le_tet): ").strip()
    cau_hoi_mau = input("Câu hỏi mẫu: ").strip()
    cau_tra_loi = input("Câu trả lời: ").strip()

    print(f"\nBạn sắp thêm FAQ:\n  Chủ đề: {chu_de}\n  Câu hỏi: {cau_hoi_mau}\n  Trả lời: {cau_tra_loi}")
    xac_nhan = input("Xác nhận lưu? (y/n): ").strip().lower()

    if xac_nhan == "y":
        id_moi = db_utils.them_faq_moi(chu_de, cau_hoi_mau, cau_tra_loi)
        print(f"✅ Đã thêm FAQ mới với id = {id_moi}")
    else:
        print("❌ Đã hủy, không lưu.")


def danh_dau_xong(id_cau_hoi: int):
    db_utils.danh_dau_da_xu_ly(id_cau_hoi)
    print(f"✅ Đã đánh dấu câu hỏi ID {id_cau_hoi} là đã xem xét xong.")


def main():
    if "--tat-ca" in sys.argv:
        hien_thi_danh_sach(chi_lay_chua_xu_ly=False)
        return

    hien_thi_danh_sach(chi_lay_chua_xu_ly=True)

    print("--- Tùy chọn ---")
    print("1. Thêm FAQ mới từ 1 trong các câu hỏi trên")
    print("2. Đánh dấu 1 câu hỏi là đã xem xét (không cần thêm FAQ)")
    print("3. Thoát")
    lua_chon = input("Chọn (1/2/3): ").strip()

    if lua_chon == "1":
        them_faq_tuong_tac()
        id_lien_quan = input("Nhập ID câu hỏi vừa xử lý để đánh dấu xong (Enter để bỏ qua): ").strip()
        if id_lien_quan:
            danh_dau_xong(int(id_lien_quan))
    elif lua_chon == "2":
        id_cau_hoi = input("Nhập ID câu hỏi cần đánh dấu: ").strip()
        if id_cau_hoi:
            danh_dau_xong(int(id_cau_hoi))
    else:
        print("Thoát chương trình.")


if __name__ == "__main__":
    main()