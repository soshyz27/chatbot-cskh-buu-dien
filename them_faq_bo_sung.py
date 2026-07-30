"""
Gộp các FAQ mới trong faq_bo_sung.json vào database cskh.db,
KHÔNG xóa hoặc ghi đè FAQ gốc đã có.

Cách dùng:
    python them_faq_bo_sung.py
"""

import json
import db_utils

with open("faq_bo_sung.json", encoding="utf-8") as f:
    faq_moi = json.load(f)

da_them = 0
for item in faq_moi:
    id_moi = db_utils.them_faq_moi(item["chu_de"], item["cau_hoi_mau"], item["cau_tra_loi"])
    print(f"Đã thêm FAQ id={id_moi}: {item['cau_hoi_mau']}")
    da_them += 1

print(f"\n✅ Hoàn tất, đã thêm {da_them} FAQ mới.")
tong_so = len(db_utils.lay_toan_bo_faq())
print(f"Tổng số FAQ hiện có trong database: {tong_so}")