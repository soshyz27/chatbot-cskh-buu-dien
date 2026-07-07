"""
Script tạo database SQLite cho chatbot CSKH bưu điện.
Đọc dữ liệu từ FAQ.json và order.json, tạo 3 bảng: faq, orders, tickets.

Cách chạy:
    python create_db.py

Kết quả: file cskh.db được tạo trong cùng thư mục.
"""

import json
import sqlite3
import os

# ---- Cấu hình đường dẫn (sửa lại nếu file JSON của bạn ở nơi khác) ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FAQ_JSON_PATH = os.path.join(BASE_DIR, "FAQ.json")
ORDER_JSON_PATH = os.path.join(BASE_DIR, "order.json")
DB_PATH = os.path.join(BASE_DIR, "cskh.db")


def create_tables(conn: sqlite3.Connection) -> None:
    """Tạo cấu trúc 3 bảng: faq, orders, tickets."""
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS faq")
    cursor.execute("""
        CREATE TABLE faq (
            id INTEGER PRIMARY KEY,
            chu_de TEXT NOT NULL,
            cau_hoi_mau TEXT NOT NULL,
            cau_tra_loi TEXT NOT NULL
        )
    """)

    cursor.execute("DROP TABLE IF EXISTS orders")
    cursor.execute("""
        CREATE TABLE orders (
            ma_van_don TEXT PRIMARY KEY,
            ten_nguoi_gui TEXT,
            ten_nguoi_nhan TEXT,
            dia_chi_nhan TEXT,
            trang_thai TEXT NOT NULL,
            ngay_gui TEXT,
            ngay_du_kien_giao TEXT,
            so_tien_cod INTEGER DEFAULT 0,
            loai_dich_vu TEXT
        )
    """)

    # Bảng tickets không có dữ liệu mẫu — sẽ được điền khi chatbot chạy thật
    cursor.execute("DROP TABLE IF EXISTS tickets")
    cursor.execute("""
        CREATE TABLE tickets (
            ticket_id TEXT PRIMARY KEY,
            ma_van_don TEXT,
            loai_khieu_nai TEXT NOT NULL,
            noi_dung TEXT NOT NULL,
            trang_thai TEXT NOT NULL DEFAULT 'Mới tạo',
            thoi_gian_tao TEXT NOT NULL
        )
    """)

    conn.commit()


def load_faq(conn: sqlite3.Connection) -> int:
    with open(FAQ_JSON_PATH, encoding="utf-8") as f:
        faq_data = json.load(f)

    cursor = conn.cursor()
    for item in faq_data:
        cursor.execute(
            "INSERT INTO faq (id, chu_de, cau_hoi_mau, cau_tra_loi) VALUES (?, ?, ?, ?)",
            (item["id"], item["chu_de"], item["cau_hoi_mau"], item["cau_tra_loi"]),
        )
    conn.commit()
    return len(faq_data)


def load_orders(conn: sqlite3.Connection) -> int:
    with open(ORDER_JSON_PATH, encoding="utf-8") as f:
        order_data = json.load(f)

    cursor = conn.cursor()
    for item in order_data:
        cursor.execute(
            """INSERT INTO orders
               (ma_van_don, ten_nguoi_gui, ten_nguoi_nhan, dia_chi_nhan,
                trang_thai, ngay_gui, ngay_du_kien_giao, so_tien_cod, loai_dich_vu)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                item["ma_van_don"],
                item["ten_nguoi_gui"],
                item["ten_nguoi_nhan"],
                item["dia_chi_nhan"],
                item["trang_thai"],
                item["ngay_gui"],
                item["ngay_du_kien_giao"],
                item["so_tien_cod"],
                item["loai_dich_vu"],
            ),
        )
    conn.commit()
    return len(order_data)


def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)  # tạo lại từ đầu mỗi lần chạy, tránh dữ liệu trùng

    conn = sqlite3.connect(DB_PATH)
    try:
        create_tables(conn)
        n_faq = load_faq(conn)
        n_orders = load_orders(conn)
        print(f"✅ Đã tạo database tại: {DB_PATH}")
        print(f"   - Bảng faq: {n_faq} dòng")
        print(f"   - Bảng orders: {n_orders} dòng")
        print(f"   - Bảng tickets: 0 dòng (sẽ tạo khi chatbot chạy)")
    finally:
        conn.close()


if __name__ == "__main__":
    main()