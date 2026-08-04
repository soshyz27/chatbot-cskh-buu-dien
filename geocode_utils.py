"""
Module geocode: chuyển địa chỉ dạng text sang tọa độ (lat, lng) bằng dịch vụ
miễn phí Nominatim (OpenStreetMap).

QUAN TRỌNG - Nominatim có 2 điều khoản bắt buộc phải tuân thủ:
  1. Giới hạn tốc độ: tối đa 1 request/giây (https://operations.osmfoundation.org/policies/nominatim/)
  2. Bắt buộc gửi kèm header "User-Agent" nhận diện ứng dụng của bạn

Để tránh gọi API lặp lại cho cùng 1 địa chỉ (chậm + có thể bị chặn nếu gọi quá nhiều),
kết quả geocode được lưu cache vào bảng `geocode_cache` trong cskh.db - lần sau tra
cùng địa chỉ sẽ đọc từ cache, không gọi mạng nữa.
"""

import time
import sqlite3
import requests

DB_PATH = "cskh.db"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
# Nominatim yêu cầu User-Agent định danh rõ ứng dụng - KHÔNG để trống hoặc dùng giá trị mặc định
HEADERS = {"User-Agent": "ChatbotCSKHBuuDien-DoAnThucTap/1.0"}

# Các tiền tố nhãn hiển thị TỰ ĐẶT (không phải địa danh thật) - phải bỏ trước khi geocode,
# vì Nominatim chỉ tra được địa danh/địa chỉ có thật, không tra được tên bưu cục tự đặt
TIEN_TO_KHONG_GEOCODE_DUOC = ["Bưu cục trung tâm ", "Bưu cục khu vực "]

_lan_goi_cuoi = 0.0  # thời điểm gọi API gần nhất, dùng để tự giới hạn tốc độ


def _lam_sach_de_geocode(dia_chi: str) -> str:
    """Bỏ tiền tố nhãn tự đặt, chỉ giữ lại phần địa danh thật để gửi cho Nominatim."""
    for tien_to in TIEN_TO_KHONG_GEOCODE_DUOC:
        if dia_chi.startswith(tien_to):
            return dia_chi[len(tien_to):]
    return dia_chi


def _dam_bao_bang_cache_ton_tai(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS geocode_cache (
            dia_chi TEXT PRIMARY KEY,
            lat REAL,
            lng REAL
        )
    """)
    conn.commit()


def _doc_cache(dia_chi: str) -> tuple[float, float] | None:
    conn = sqlite3.connect(DB_PATH)
    try:
        _dam_bao_bang_cache_ton_tai(conn)
        row = conn.execute(
            "SELECT lat, lng FROM geocode_cache WHERE dia_chi = ?", (dia_chi,)
        ).fetchone()
        return (row[0], row[1]) if row else None
    finally:
        conn.close()


def _luu_cache(dia_chi: str, lat: float, lng: float):
    conn = sqlite3.connect(DB_PATH)
    try:
        _dam_bao_bang_cache_ton_tai(conn)
        conn.execute(
            "INSERT OR REPLACE INTO geocode_cache (dia_chi, lat, lng) VALUES (?, ?, ?)",
            (dia_chi, lat, lng),
        )
        conn.commit()
    finally:
        conn.close()


def geocode(dia_chi: str) -> dict | None:
    """
    Chuyển 1 địa chỉ text sang {"lat": ..., "lng": ...}.
    Trả None nếu không tìm được (địa chỉ quá mơ hồ, lỗi mạng, v.v.)
    """
    global _lan_goi_cuoi

    if not dia_chi:
        return None

    # 1. Kiểm tra cache trước
    cached = _doc_cache(dia_chi)
    if cached:
        return {"lat": cached[0], "lng": cached[1]}

    # 2. Tự giới hạn tốc độ gọi API (Nominatim yêu cầu tối đa 1 req/giây)
    khoang_cach = time.time() - _lan_goi_cuoi
    if khoang_cach < 1.1:
        time.sleep(1.1 - khoang_cach)

    # 3. Gọi API thật - dùng địa danh đã làm sạch (bỏ nhãn tự đặt không geocode được)
    dia_danh_that = _lam_sach_de_geocode(dia_chi)
    try:
        # Thêm ", Việt Nam" để tăng độ chính xác geocode (tránh nhầm sang địa danh trùng tên ở nước khác)
        params = {
            "q": f"{dia_danh_that}, Việt Nam",
            "format": "json",
            "limit": 1,
        }
        response = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=10)
        _lan_goi_cuoi = time.time()
        response.raise_for_status()
        ket_qua = response.json()

        if not ket_qua:
            return None

        lat = float(ket_qua[0]["lat"])
        lng = float(ket_qua[0]["lon"])
        _luu_cache(dia_chi, lat, lng)
        return {"lat": lat, "lng": lng}

    except (requests.RequestException, KeyError, ValueError, IndexError) as e:
        print(f"[Geocode] Lỗi khi geocode '{dia_chi}': {e}")
        return None


if __name__ == "__main__":
    # Chạy trực tiếp file này để tự test geocode vài địa chỉ mẫu
    dia_chi_test = [
        "123 Lê Lợi, Quận 1, TP.HCM",
        "Bưu cục trung tâm Hà Nội",
        "Bưu cục khu vực Đà Nẵng",
    ]
    for dc in dia_chi_test:
        ket_qua = geocode(dc)
        print(f"{dc} -> {ket_qua}")