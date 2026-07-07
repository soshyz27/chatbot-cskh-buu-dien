"""
Các hàm truy vấn database cskh.db.
Tách riêng khỏi main.py để dễ đọc, dễ test độc lập.
"""

import sqlite3
import uuid
from datetime import datetime

DB_PATH = "cskh.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # cho phép truy cập cột theo tên
    return conn


def tra_cuu_don_hang(ma_van_don: str) -> dict | None:
    """Tìm 1 đơn hàng theo mã vận đơn. Trả None nếu không tồn tại."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM orders WHERE ma_van_don = ?", (ma_van_don.strip().upper(),)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def tim_faq_lien_quan(tu_khoa: str, gioi_han: int = 3) -> list[dict]:
    """
    Tìm các câu FAQ có liên quan bằng cách so khớp từ khóa đơn giản (LIKE).
    Đây là cách tìm kiếm cơ bản - đủ dùng cho demo với 18 câu FAQ.
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM faq WHERE cau_hoi_mau LIKE ? OR cau_tra_loi LIKE ? OR chu_de LIKE ? LIMIT ?",
            (f"%{tu_khoa}%", f"%{tu_khoa}%", f"%{tu_khoa}%", gioi_han),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def lay_toan_bo_faq() -> list[dict]:
    """Lấy toàn bộ 18 câu FAQ - dùng khi cần đưa hết cho Gemini tham khảo."""
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM faq").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def tao_ticket(ma_van_don: str | None, loai_khieu_nai: str, noi_dung: str) -> str:
    """Tạo 1 ticket khiếu nại mới, trả về mã ticket vừa tạo."""
    ticket_id = "TK-" + uuid.uuid4().hex[:8].upper()
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO tickets (ticket_id, ma_van_don, loai_khieu_nai, noi_dung, trang_thai, thoi_gian_tao)
               VALUES (?, ?, ?, ?, 'Mới tạo', ?)""",
            (ticket_id, ma_van_don, loai_khieu_nai, noi_dung, datetime.now().isoformat(timespec="seconds")),
        )
        conn.commit()
        return ticket_id
    finally:
        conn.close()