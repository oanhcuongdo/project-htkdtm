"""
Script sinh dữ liệu giao dịch tài chính giả lập (800 - 1.000 giao dịch)
Đề tài: Hệ thống Quản lý Tài chính Cá nhân Thông minh (Nhóm 13 - 65HTTT)
Xuất ra 2 định dạng:
1. mock_transactions.sql: Để nạp trực tiếp vào PostgreSQL
2. mock_transactions.csv: Để xem hoặc nạp thử nghiệm vào Superset
"""

import os
import random
from datetime import datetime, timedelta

# Thiết lập seed để dữ liệu có tính nhất quán (reproducible)
random.seed(42)

ACCOUNTS = [
    (1, "VCB"),
    (2, "MBBank"),
    (3, "MoMo"),
    (4, "CASH")
]

# (category_id, name, parent, default_dir, merchant_id, min_amt, max_amt, [raw_templates], [clean_templates])
EXPENSE_PATTERNS = [
    # 1. Ăn uống & Cà phê
    (1, 4, 30000, 75000, 
     ["MBVCB.{ref}.Highlands Coffee", "VCB.Cafe sang voi ban {ref}", "HIGHLANDS COFFEE DIGIBANK", "Phuc Long tra sua {ref}"],
     "Cà phê sáng Highlands / Phúc Long"),
    (1, 5, 45000, 110000, 
     ["MOMO thanh toan Phuc Long {ref}", "Tra sua Phuc Long {ref}"],
     "Trà sữa Phúc Long"),
    (1, 6, 80000, 350000, 
     ["WINMART.{ref}.Sieu thi mua do an", "Momo thanh toan WinMart+ {ref}", "Di cho WinMart thuc pham"],
     "Đi chợ / Siêu thị WinMart"),
    (1, None, 35000, 65000, 
     ["MB.{ref}.Tien an trua com van phong", "An trua dong nghiep {ref}", "Bun cha trua {ref}"],
     "Cơm trưa văn phòng / Bún chả"),
    (1, None, 40000, 95000, 
     ["An toi pho bo {ref}", "Com rang buoi toi {ref}", "MOMO.Thanh toan an toi {ref}"],
     "Ăn tối"),

    # 4. Xăng xe & Đi lại
    (4, 3, 28000, 85000, 
     ["GRAB* VIETNAM {ref}", "GrabBike di lam sang {ref}", "GRABFOOD HOAC RIDE {ref}"],
     "GrabBike di chuyển"),
    (4, None, 50000, 120000, 
     ["Do xang Petrolimex {ref}", "Tien do xang xe may {ref}"],
     "Đổ xăng xe máy"),

    # 6. Mua sắm & Đồ dùng
    (6, 1, 120000, 850000, 
     ["SHOPEEPAY.{ref}.Don hang Shopee", "Shopee thanh toan do gia dung {ref}", "MOMO SHOPEE {ref}"],
     "Mua sắm online Shopee"),
    (6, 2, 200000, 950000, 
     ["LAZADA VIETNAM {ref}", "Lazada don hang gia dung {ref}"],
     "Mua sắm online Lazada"),

    # 7. Giải trí & Phim ảnh
    (7, 7, 110000, 260000, 
     ["CGV CINEMAS.{ref}.Ve xem phim", "MOMO CGV Cinema cuoi tuan {ref}"],
     "Vé xem phim CGV"),

    # 8. Gặp gỡ bạn bè & Tiệc tùng
    (8, None, 250000, 750000, 
     ["MBVCB.{ref}.Lien hoan an lau cuoi tuan", "Camp tien lau nuong cung nhom ban", "Uong bia giao luu {ref}"],
     "Ăn lẩu / Gặp gỡ bạn bè cuối tuần"),

    # 5. Chăm sóc sức khỏe
    (5, None, 50000, 250000, 
     ["Nha thuoc Long Chau mua thuoc {ref}", "Mua vitamin C thuoc cam {ref}"],
     "Mua thuốc tây / Nhà thuốc Long Châu")
]

def generate_reference_code(bank):
    return f"{bank}{random.randint(10000000, 99999999)}"

def main():
    transactions = []
    
    # Tạo giao dịch trải dài từ 01/01/2026 đến 22/11/2026 (~325 ngày)
    start_date = datetime(2026, 1, 1)
    end_date = datetime(2026, 11, 22)
    current_date = start_date

    trans_id = 1

    while current_date <= end_date:
        year = current_date.year
        month = current_date.month
        day = current_date.day
        weekday = current_date.weekday() # 0 = Monday, 6 = Sunday

        # ----------------------------------------------------
        # 1. Thu nhập cố định: Ngày 5 hàng tháng nhận lương MBBank
        # ----------------------------------------------------
        if day == 5:
            date_id = int(f"{year}{month:02d}{day:02d}09") # 9h sáng
            ref = generate_reference_code("MB")
            transactions.append({
                "transaction_id": trans_id,
                "date_id": date_id,
                "category_id": 12, # Lương
                "account_id": 2, # MBBank
                "merchant_id": 10, # Cty Alpha
                "amount": 22000000.0,
                "direction": "INCOME",
                "raw_description": f"CTY CP CONG NGHE ALPHA TRA LUONG THANG {month:02d}.{ref}",
                "clean_description": f"Nhận lương tháng {month:02d}/2026 từ Công ty Alpha",
                "is_internal_transfer": False,
                "is_anomaly": False,
                "anomaly_score": 0.0,
                "reference_code": ref,
                "source_type": "EMAIL",
                "created_at": f"{current_date.strftime('%Y-%m-%d')} 09:15:00+07"
            })
            trans_id += 1

            # Tự động trích tiền tiết kiệm ngày 6
            date_id_save = int(f"{year}{month:02d}{day+1:02d}10")
            ref_save = generate_reference_code("MB")
            transactions.append({
                "transaction_id": trans_id,
                "date_id": date_id_save,
                "category_id": 10, # Quỹ tiết kiệm
                "account_id": 2,
                "merchant_id": None,
                "amount": -2500000.0,
                "direction": "EXPENSE",
                "raw_description": f"MB.{ref_save}.Trich gui tiet kiem online ky han 6 thang",
                "clean_description": "Trích gửi tiết kiệm online định kỳ",
                "is_internal_transfer": False,
                "is_anomaly": False,
                "anomaly_score": 0.0,
                "reference_code": ref_save,
                "source_type": "EMAIL",
                "created_at": f"2026-{month:02d}-{day+1:02d} 10:00:00+07"
            })
            trans_id += 1

        # ----------------------------------------------------
        # 2. Thu nhập phụ / Freelance vào ngày 18 hoặc 20 hàng tháng
        # ----------------------------------------------------
        if day == 18 and month in [2, 3, 5, 7, 8, 10]:
            date_id = int(f"{year}{month:02d}{day:02d}15")
            ref = generate_reference_code("VCB")
            amt = random.choice([3500000.0, 5000000.0, 4200000.0])
            transactions.append({
                "transaction_id": trans_id,
                "date_id": date_id,
                "category_id": 13, # Thưởng & Freelance
                "account_id": 1, # VCB
                "merchant_id": None,
                "amount": amt,
                "direction": "INCOME",
                "raw_description": f"VCB.{ref}.Thanh toan du an freelance website",
                "clean_description": "Thu nhập làm thêm dự án Freelance",
                "is_internal_transfer": False,
                "is_anomaly": False,
                "anomaly_score": 0.0,
                "reference_code": ref,
                "source_type": "EMAIL",
                "created_at": f"{current_date.strftime('%Y-%m-%d')} 15:30:00+07"
            })
            trans_id += 1

        # ----------------------------------------------------
        # 3. Chi phí cố định hàng tháng:
        #    - Tiền nhà ngày 2
        #    - Điện nước ngày 12
        # ----------------------------------------------------
        if day == 2:
            date_id = int(f"{year}{month:02d}{day:02d}19")
            ref = generate_reference_code("VCB")
            transactions.append({
                "transaction_id": trans_id,
                "date_id": date_id,
                "category_id": 2, # Tiền nhà
                "account_id": 1,
                "merchant_id": 8, # Bác Hùng
                "amount": -3500000.0,
                "direction": "EXPENSE",
                "raw_description": f"MBVCB.{ref}.Nguyen Van A chuyen tien nha thang {month:02d}",
                "clean_description": f"Thanh toán tiền thuê nhà tháng {month:02d}/2026",
                "is_internal_transfer": False,
                "is_anomaly": False,
                "anomaly_score": 0.0,
                "reference_code": ref,
                "source_type": "CSV",
                "created_at": f"{current_date.strftime('%Y-%m-%d')} 19:20:00+07"
            })
            trans_id += 1

        if day == 12:
            date_id = int(f"{year}{month:02d}{day:02d}11")
            ref = generate_reference_code("MOMO")
            amt = random.choice([650000.0, 780000.0, 890000.0, 720000.0])
            transactions.append({
                "transaction_id": trans_id,
                "date_id": date_id,
                "category_id": 3, # Điện nước & Internet
                "account_id": 3, # MoMo
                "merchant_id": 9, # EVN
                "amount": -amt,
                "direction": "EXPENSE",
                "raw_description": f"MOMO-HOADON-EVN.{ref}.Tien dien thang {month:02d}",
                "clean_description": f"Hóa đơn tiền điện EVN tháng {month:02d}",
                "is_internal_transfer": False,
                "is_anomaly": False,
                "anomaly_score": 0.0,
                "reference_code": ref,
                "source_type": "EMAIL",
                "created_at": f"{current_date.strftime('%Y-%m-%d')} 11:10:00+07"
            })
            trans_id += 1

        # ----------------------------------------------------
        # 4. Chuyển tiền nội bộ giữa các ví (Internal Transfer)
        # ----------------------------------------------------
        if day in [7, 21]:
            date_id = int(f"{year}{month:02d}{day:02d}14")
            ref = generate_reference_code("VCB")
            amt = 500000.0
            transactions.append({
                "transaction_id": trans_id,
                "date_id": date_id,
                "category_id": 15, # Chuyển tiền nội bộ
                "account_id": 1, # VCB
                "merchant_id": None,
                "amount": -amt,
                "direction": "TRANSFER",
                "raw_description": f"VCB.{ref}.Nap tien vao Vi MoMo ca nhan",
                "clean_description": "Nạp tiền từ Vietcombank vào ví MoMo",
                "is_internal_transfer": True, # ĐÃ GẮN CỜ NỘI BỘ
                "is_anomaly": False,
                "anomaly_score": 0.0,
                "reference_code": ref,
                "source_type": "EMAIL",
                "created_at": f"{current_date.strftime('%Y-%m-%d')} 14:00:00+07"
            })
            trans_id += 1

        # ----------------------------------------------------
        # 5. Chi tiêu sinh hoạt hàng ngày (1-3 giao dịch/ngày)
        # ----------------------------------------------------
        num_daily = random.choices([1, 2, 3], weights=[0.3, 0.5, 0.2])[0]
        for _ in range(num_daily):
            pat = random.choice(EXPENSE_PATTERNS)
            cat_id, default_merchant, min_a, max_a, raw_tmpls, clean_name = pat

            # Giờ phát sinh: Sáng (7-9h), Trưa (11-13h), Chiều (15-17h), Tối (19-22h)
            hour = random.choice([7, 8, 9, 11, 12, 13, 15, 17, 19, 20, 21])
            date_id = int(f"{year}{month:02d}{day:02d}{hour:02d}")

            account = random.choice(ACCOUNTS)
            ref = generate_reference_code(account[1])

            # Giá trị giao dịch làm tròn theo nghìn đồng
            amt = round(random.randint(int(min_a), int(max_a)) / 1000) * 1000

            raw_tmpl = random.choice(raw_tmpls)
            raw_desc = raw_tmpl.format(ref=ref)

            source = random.choice(["EMAIL", "CSV", "TELEGRAM"])

            transactions.append({
                "transaction_id": trans_id,
                "date_id": date_id,
                "category_id": cat_id,
                "account_id": account[0],
                "merchant_id": default_merchant,
                "amount": -float(amt),
                "direction": "EXPENSE",
                "raw_description": raw_desc,
                "clean_description": clean_name,
                "is_internal_transfer": False,
                "is_anomaly": False,
                "anomaly_score": round(random.uniform(0.01, 0.15), 4),
                "reference_code": ref,
                "source_type": source,
                "created_at": f"{current_date.strftime('%Y-%m-%d')} {hour:02d}:{random.randint(10, 59):02d}:00+07"
            })
            trans_id += 1

        # Sang ngày tiếp theo
        current_date += timedelta(days=1)

    # ----------------------------------------------------
    # 6. Thêm một số giao dịch BẤT THƯỜNG (Anomalies)
    #    để kiểm thử tính năng AI phát hiện bất thường & Superset
    # ----------------------------------------------------
    anomalies = [
        (int("2026041514"), 6, 1, None, -14500000.0, "EXPENSE", 
         "MBVCB.99182312.Sua chua thay man hinh laptop MacBook Pro tai TTBH", 
         "Sửa chữa màn hình Laptop MacBook Pro", 0.9450, "EMAIL", "2026-04-15 14:30:00+07"),
        (int("2026082223"), 6, 3, 1, -6800000.0, "EXPENSE", 
         "SHOPEE-PAY*88312019 Mua may hut bui robot lau nha thong minh", 
         "Mua máy hút bụi Robot lau nhà", 0.8870, "TELEGRAM", "2026-08-22 23:15:00+07"),
        (int("2026101018"), 8, 2, None, -5200000.0, "EXPENSE", 
         "MB.91028301.Thanh toan bill tiec sinh nhat nha hang Sen Tay Ho", 
         "Tiệc sinh nhật nhà hàng Sen Tây Hồ", 0.9120, "CSV", "2026-10-10 18:45:00+07"),
        (int("2026063002"), 1, 1, None, -1250000.0, "EXPENSE", 
         "VCB.BATTHUONG.Phi quan ly dich vu ngoai le luc 2h sang", 
         "Phí dịch vụ bất thường lúc 2h sáng", 0.9850, "EMAIL", "2026-06-30 02:15:00+07")
    ]

    for date_id, cat_id, acc_id, merch_id, amt, dir_, raw_d, clean_d, score, src, created in anomalies:
        ref = f"ANOMALY{random.randint(1000, 9999)}"
        transactions.append({
            "transaction_id": trans_id,
            "date_id": date_id,
            "category_id": cat_id,
            "account_id": acc_id,
            "merchant_id": merch_id,
            "amount": amt,
            "direction": dir_,
            "raw_description": raw_d,
            "clean_description": clean_d,
            "is_internal_transfer": False,
            "is_anomaly": True,
            "anomaly_score": score,
            "reference_code": ref,
            "source_type": src,
            "created_at": created
        })
        trans_id += 1

    print(f"[*] Đã sinh tổng cộng: {len(transactions)} bản ghi giao dịch giả lập.")

    # ----------------------------------------------------
    # GHI RA FILE SQL (mock_transactions.sql)
    # ----------------------------------------------------
    output_dir = os.path.dirname(os.path.abspath(__file__))
    sql_path = os.path.join(output_dir, "mock_transactions.sql")
    csv_path = os.path.join(output_dir, "mock_transactions.csv")

    with open(sql_path, "w", encoding="utf-8") as f:
        f.write("-- File nạp dữ liệu giao dịch mẫu (mock data)\n")
        f.write("-- Tự động sinh bởi generate_mock_data.py\n\n")
        f.write("INSERT INTO fact_transactions (\n")
        f.write("    transaction_id, date_id, category_id, account_id, merchant_id, amount, direction,\n")
        f.write("    raw_description, clean_description, is_internal_transfer, is_anomaly, anomaly_score,\n")
        f.write("    reference_code, source_type, created_at\n")
        f.write(") VALUES\n")

        lines = []
        for t in transactions:
            merch_val = str(t['merchant_id']) if t['merchant_id'] else "NULL"
            raw_escaped = t['raw_description'].replace("'", "''")
            clean_escaped = t['clean_description'].replace("'", "''")
            line = (
                f"({t['transaction_id']}, {t['date_id']}, {t['category_id']}, {t['account_id']}, "
                f"{merch_val}, {t['amount']}, '{t['direction']}', '{raw_escaped}', '{clean_escaped}', "
                f"{t['is_internal_transfer']}, {t['is_anomaly']}, {t['anomaly_score']}, '{t['reference_code']}', "
                f"'{t['source_type']}', '{t['created_at']}')"
            )
            lines.append(line)

        f.write(",\n".join(lines))
        f.write(";\n\n")
        f.write("-- Cập nhật lại giá trị sequence sau khi chèn với ID cụ thể\n")
        f.write("SELECT setval('fact_transactions_transaction_id_seq', (SELECT MAX(transaction_id) FROM fact_transactions));\n")

    print(f"[✓] Đã tạo file SQL: {sql_path}")

    # ----------------------------------------------------
    # GHI RA FILE CSV (mock_transactions.csv)
    # ----------------------------------------------------
    import csv
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=transactions[0].keys())
        writer.writeheader()
        writer.writerows(transactions)

    print(f"[✓] Đã tạo file CSV: {csv_path}")

if __name__ == "__main__":
    main()
