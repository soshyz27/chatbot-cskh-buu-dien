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
    dam_bao_bang_log_ton_tai(conn)
    return conn


def dam_bao_bang_log_ton_tai(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cau_hoi_chua_xu_ly (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            noi_dung TEXT NOT NULL,
            intent_du_doan TEXT,
            thoi_gian TEXT NOT NULL,
            da_xu_ly INTEGER NOT NULL DEFAULT 0
        )
    """)

    # MỚI: bảng lưu lịch sử hội thoại theo session
    conn.execute("""
        CREATE TABLE IF NOT EXISTS lich_su_hoi_thoai (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            vai_tro TEXT NOT NULL,
            noi_dung TEXT NOT NULL,
            thoi_gian TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_lich_su_session
        ON lich_su_hoi_thoai (session_id, id)
    """)
    conn.commit()


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


# ---------- Cơ chế "học có giám sát": ghi log câu hỏi chatbot xử lý kém ----------

def ghi_log_cau_hoi_chua_xu_ly(noi_dung: str, intent_du_doan: str) -> None:
    """
    Lưu lại các tin nhắn mà chatbot không xử lý tốt (intent = 'khac'),
    để admin xem lại định kỳ và cân nhắc bổ sung FAQ mới.
    Đây KHÔNG phải tự động học - chỉ là log để con người quyết định.
    """
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO cau_hoi_chua_xu_ly (noi_dung, intent_du_doan, thoi_gian, da_xu_ly)
               VALUES (?, ?, ?, 0)""",
            (noi_dung, intent_du_doan, datetime.now().isoformat(timespec="seconds")),
        )
        conn.commit()
    finally:
        conn.close()


def lay_danh_sach_cau_hoi_chua_xu_ly(chi_lay_chua_xu_ly: bool = True) -> list[dict]:
    """Lấy danh sách câu hỏi đã ghi log, mới nhất trước."""
    conn = get_connection()
    try:
        if chi_lay_chua_xu_ly:
            rows = conn.execute(
                "SELECT * FROM cau_hoi_chua_xu_ly WHERE da_xu_ly = 0 ORDER BY id DESC"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM cau_hoi_chua_xu_ly ORDER BY id DESC"
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def danh_dau_da_xu_ly(id_cau_hoi: int) -> None:
    """Đánh dấu 1 câu hỏi trong log là đã xem xét xong (dù có thêm FAQ hay không)."""
    conn = get_connection()
    try:
        conn.execute("UPDATE cau_hoi_chua_xu_ly SET da_xu_ly = 1 WHERE id = ?", (id_cau_hoi,))
        conn.commit()
    finally:
        conn.close()


def them_faq_moi(chu_de: str, cau_hoi_mau: str, cau_tra_loi: str) -> int:
    """
    Thêm 1 câu FAQ mới - dùng khi admin đã xác nhận (kiểm duyệt) câu trả lời đúng
    từ log câu hỏi chưa xử lý. id tự tăng dựa trên id lớn nhất hiện có.
    """
    conn = get_connection()
    try:
        max_id_row = conn.execute("SELECT MAX(id) as max_id FROM faq").fetchone()
        id_moi = (max_id_row["max_id"] or 0) + 1
        conn.execute(
            "INSERT INTO faq (id, chu_de, cau_hoi_mau, cau_tra_loi) VALUES (?, ?, ?, ?)",
            (id_moi, chu_de, cau_hoi_mau, cau_tra_loi),
        )
        conn.commit()
        return id_moi
    finally:
        conn.close()

# ---------- Lịch sử hội thoại (lưu SQLite thay vì RAM) ----------

def luu_tin_nhan(session_id: str, vai_tro: str, noi_dung: str) -> None:
    """Lưu 1 lượt tin nhắn (user hoặc bot) vào bảng lich_su_hoi_thoai."""
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO lich_su_hoi_thoai (session_id, vai_tro, noi_dung, thoi_gian)
               VALUES (?, ?, ?, ?)""",
            (session_id, vai_tro, noi_dung, datetime.now().isoformat(timespec="seconds")),
        )
        conn.commit()
    finally:
        conn.close()


def lay_lich_su_gan_day(session_id: str, so_luot: int = 6) -> list[dict]:
    """Lấy N lượt gần nhất của 1 session, trả về theo thứ tự thời gian tăng dần."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT vai_tro, noi_dung FROM lich_su_hoi_thoai
               WHERE session_id = ? ORDER BY id DESC LIMIT ?""",
            (session_id, so_luot),
        ).fetchall()
        return [dict(r) for r in reversed(rows)]
    finally:
        conn.close()