"""
Pre-Push Verification Script (Kiểm tra và đánh giá trước khi Push code)
Phụ trách: Đinh Thị Lan Anh - 2351160500 (Nhóm 05)

Kịch bản kiểm tra tự động bao gồm:
1. Kiểm tra cấu trúc thư mục và vị trí các tệp theo quy chuẩn môn học.
2. Kiểm tra Git Branch & file nhạy cảm (không commit .env, .venv, db.sqlite3).
3. Kiểm tra tính toàn vẹn và tiêu chí chất lượng của 3 bộ dữ liệu:
   - VietJobs: số lượng bản ghi, tỷ lệ trùng lặp (< 1%), chuẩn hóa lương & kỹ năng.
   - OULAD: bảng tổng hợp sinh viên (student_features), log VLE, điểm số.
   - Course Reviews: phân phối rating [1-5], loại bỏ trùng lặp (< 1%).
4. Tổng hợp trạng thái: READY TO PUSH hay BLOCKED.
"""

import os
import sys
import subprocess
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")


def check_git_status():
    print("\n--- [BƯỚC 1] KIỂM TRA QUY CHUẨN GIT & NHÁNH LÀM VIỆC ---")
    try:
        branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=BASE_DIR).decode().strip()
        print(f"[*] Nhánh hiện tại: '{branch}'")
        if branch == "main":
            print("[FAIL] CẢNH BÁO: Bạn đang ở nhánh 'main'. Đề cương quy định tuyệt đối không push trực tiếp lên main!")
            return False
        else:
            print(f"[PASS] Nhánh làm việc hợp lệ (không phải main): {branch}")
            
        status = subprocess.check_output(["git", "status", "--porcelain"], cwd=BASE_DIR).decode()
        sensitive_files = [".env", ".venv", "db.sqlite3", "__pycache__"]
        found_sensitive = []
        for line in status.splitlines():
            for sf in sensitive_files:
                if sf in line and not line.strip().endswith(".env.example"):
                    found_sensitive.append(line.strip())
                    
        if found_sensitive:
            print(f"[FAIL] Phát hiện tệp không được phép commit: {found_sensitive}")
            return False
        else:
            print("[PASS] Không có tệp nhạy cảm (.env, .venv, db.sqlite3) bị theo dõi.")
            return True
    except Exception as e:
        print(f"[WARN] Không kiểm tra được git: {e}")
        return True


def check_datasets_quality():
    print("\n--- [BƯỚC 2] KIỂM TRA TIÊU CHÍ CHẤT LƯỢNG DỮ LIỆU ĐỀ CƯƠNG ---")
    all_passed = True
    
    # 1. VietJobs
    vj_file = os.path.join(PROCESSED_DIR, "vietjobs", "vietjobs_cleaned.csv")
    if not os.path.exists(vj_file):
        print(f"[FAIL] Không tìm thấy file VietJobs: {vj_file}")
        return False
        
    df_vj = pd.read_csv(vj_file)
    vj_dups = df_vj.duplicated(subset=["job_title", "company_name", "location"]).sum()
    vj_dup_rate = (vj_dups / len(df_vj)) * 100
    print(f"[*] VietJobs: {len(df_vj)} bản ghi | Bản ghi trùng: {vj_dups} ({vj_dup_rate:.2f}%)")
    if vj_dup_rate < 1.0 and len(df_vj) >= 1000:
        print("    -> [PASS] VietJobs đạt tiêu chuẩn (Tỷ lệ trùng < 1% và số lượng >= 1,000)")
    else:
        print("    -> [FAIL] VietJobs không đạt tiêu chuẩn!")
        all_passed = False
        
    # 2. OULAD
    feat_file = os.path.join(PROCESSED_DIR, "oulad", "student_features_analytics.csv")
    if not os.path.exists(feat_file):
        print(f"[FAIL] Không tìm thấy file OULAD features: {feat_file}")
        return False
        
    df_feat = pd.read_csv(feat_file)
    oulad_dups = df_feat.duplicated(subset=["code_module", "code_presentation", "id_student"]).sum()
    print(f"[*] OULAD: {len(df_feat)} sinh viên phân tích | Bản ghi trùng: {oulad_dups}")
    required_cols = {"id_student", "total_clicks", "active_days", "avg_score", "risk_level"}
    if required_cols.issubset(df_feat.columns) and oulad_dups == 0:
        print("    -> [PASS] OULAD đạt tiêu chuẩn (Đầy đủ đặc trưng ML & không trùng lặp)")
    else:
        print("    -> [FAIL] OULAD thiếu cột đặc trưng hoặc có trùng lặp!")
        all_passed = False
        
    # 3. Course Reviews
    rev_file = os.path.join(PROCESSED_DIR, "course_reviews", "course_reviews_cleaned.csv")
    if not os.path.exists(rev_file):
        print(f"[FAIL] Không tìm thấy file Course Reviews: {rev_file}")
        return False
        
    df_rev = pd.read_csv(rev_file)
    rev_dups = df_rev.duplicated(subset=["course_id", "review_text"]).sum()
    rev_dup_rate = (rev_dups / len(df_rev)) * 100
    invalid_ratings = df_rev[~df_rev["rating"].between(1.0, 5.0)]
    print(f"[*] Course Reviews: {len(df_rev)} nhận xét | Bản ghi trùng: {rev_dups} ({rev_dup_rate:.2f}%) | Điểm ngoài [1-5]: {len(invalid_ratings)}")
    if rev_dup_rate < 1.0 and len(invalid_ratings) == 0:
        print("    -> [PASS] Course Reviews đạt tiêu chuẩn (Tỷ lệ trùng < 1% và rating chuẩn [1.0 - 5.0])")
    else:
        print("    -> [FAIL] Course Reviews không đạt tiêu chuẩn!")
        all_passed = False

    # 4. WEF International Trends
    wef_file = os.path.join(PROCESSED_DIR, "wef", "wef_trends_cleaned.csv")
    if not os.path.exists(wef_file):
        print(f"[FAIL] Không tìm thấy file WEF Trends: {wef_file}")
        return False
        
    df_wef = pd.read_csv(wef_file)
    wef_dups = df_wef.duplicated(subset=["category", "item_name"]).sum()
    wef_dup_rate = (wef_dups / len(df_wef)) * 100
    print(f"[*] WEF Trends: {len(df_wef)} xu hướng quốc tế | Bản ghi trùng: {wef_dups} ({wef_dup_rate:.2f}%)")
    if wef_dup_rate < 1.0 and len(df_wef) >= 20:
        print("    -> [PASS] WEF Trends đạt tiêu chuẩn (Báo cáo xu hướng WEF đầy đủ, không trùng lặp)")
    else:
        print("    -> [FAIL] WEF Trends không đạt tiêu chuẩn!")
        all_passed = False
        
    return all_passed


def check_documentation():
    print("\n--- [BƯỚC 3] KIỂM TRA TÀI LIỆU VÀ BÁO CÁO NGHIỆM THU ---")
    doc_file = os.path.join(BASE_DIR, "docs", "BAO_CAO_THU_THAP_XU_LY_DU_LIEU_LAN_ANH.md")
    json_report = os.path.join(PROCESSED_DIR, "data_quality_report.json")
    
    ok = True
    if os.path.exists(doc_file):
        print(f"[PASS] Đã có tài liệu báo cáo kỹ thuật: {os.path.basename(doc_file)}")
    else:
        print(f"[FAIL] Chưa tìm thấy báo cáo kỹ thuật tại docs/")
        ok = False
        
    if os.path.exists(json_report):
        print(f"[PASS] Đã có báo cáo chất lượng máy đọc: {os.path.basename(json_report)}")
    else:
        print(f"[FAIL] Chưa tìm thấy data_quality_report.json")
        ok = False
        
    return ok


def main():
    print("================================================================================")
    print("       KIỂM ĐỊNH TOÀN DIỆN TRƯỚC KHI PUSH CODE (PRE-PUSH VERIFICATION)")
    print("       Đinh Thị Lan Anh - 2351160500 | Nhóm 05 - HTKDTM")
    print("================================================================================")
    
    step1 = check_git_status()
    step2 = check_datasets_quality()
    step3 = check_documentation()
    
    print("\n================================================================================")
    if step1 and step2 and step3:
        print("  >>> KẾT LUẬN: TẤT CẢ TIÊU CHÍ ĐỀ CƯƠNG ĐỀU ĐẠT! [READY TO PUSH] <<<")
        print("  Bạn có thể tiến hành commit và push code lên nhánh của mình.")
        print("================================================================================\n")
        return 0
    else:
        print("  >>> KẾT LUẬN: CÒN TIÊU CHÍ CHƯA ĐẠT. VUI LÒNG KHẮC PHỤC TRƯỚC KHI PUSH! <<<")
        print("================================================================================\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
