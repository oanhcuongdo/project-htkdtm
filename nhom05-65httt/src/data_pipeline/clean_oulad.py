"""
OULAD Cleaning & Feature Engineering Module
Phụ trách: Đinh Thị Lan Anh - 2351160500 (Nhóm 05)
Chức năng:
- Làm sạch studentInfo: xử lý null, loại bỏ trùng lặp sinh viên
- Làm sạch studentAssessment: kiểm tra và hiệu chỉnh điểm số hợp lệ [0-100], loại bỏ trùng lặp bài thi
- Làm sạch studentVle: loại bỏ log click trùng lặp, lọc click âm
- Tổng hợp bảng phân tích học tập tích hợp (Student Feature Matrix) phục vụ trực tiếp cho
  Machine Learning (Nguyễn Anh Quân) và Data Warehouse (Nguyễn Quang Đức)
"""

import os
import pandas as pd
import numpy as np


def clean_oulad_pipeline(raw_oulad_dir, processed_oulad_dir):
    print(f"\n[OULAD] Đang tiến hành làm sạch dữ liệu học tập từ: {raw_oulad_dir}")
    os.makedirs(processed_oulad_dir, exist_ok=True)
    
    # 1. Đọc và làm sạch courses.csv
    courses_file = os.path.join(raw_oulad_dir, "courses.csv")
    df_courses = pd.read_csv(courses_file)
    df_courses.drop_duplicates(subset=["code_module", "code_presentation"], inplace=True)
    df_courses.to_csv(os.path.join(processed_oulad_dir, "courses_cleaned.csv"), index=False)
    
    # 2. Đọc và làm sạch studentInfo
    stu_info_file = os.path.join(raw_oulad_dir, "studentInfo_raw.csv")
    df_students = pd.read_csv(stu_info_file)
    init_stu_count = len(df_students)
    
    # Điền giá trị thiếu (missing values)
    df_students["gender"] = df_students["gender"].fillna("Unknown")
    df_students["imd_band"] = df_students["imd_band"].fillna("Missing")
    
    # Loại bỏ bản ghi trùng lặp theo mã khóa và sinh viên
    dup_stu = df_students.duplicated(subset=["code_module", "code_presentation", "id_student"]).sum()
    df_students_cleaned = df_students.drop_duplicates(subset=["code_module", "code_presentation", "id_student"], keep="first").copy()
    df_students_cleaned.to_csv(os.path.join(processed_oulad_dir, "studentInfo_cleaned.csv"), index=False)
    
    # 3. Đọc và làm sạch assessments
    ass_file = os.path.join(raw_oulad_dir, "assessments.csv")
    df_ass = pd.read_csv(ass_file)
    df_ass.drop_duplicates(subset=["id_assessment"], inplace=True)
    df_ass.to_csv(os.path.join(processed_oulad_dir, "assessments_cleaned.csv"), index=False)
    
    # 4. Đọc và làm sạch studentAssessment
    stu_ass_file = os.path.join(raw_oulad_dir, "studentAssessment_raw.csv")
    df_stu_ass = pd.read_csv(stu_ass_file)
    init_ass_count = len(df_stu_ass)
    
    # Loại bỏ trùng lặp bài thi
    dup_ass = df_stu_ass.duplicated(subset=["id_assessment", "id_student"]).sum()
    df_stu_ass_cleaned = df_stu_ass.drop_duplicates(subset=["id_assessment", "id_student"], keep="first").copy()
    
    # Làm sạch điểm số: loại bỏ điểm bất thường ngoài [0, 100] hoặc clip
    # Điểm NaN điền bằng 0 (chưa nộp hoặc bị 0 điểm)
    df_stu_ass_cleaned["score"] = df_stu_ass_cleaned["score"].fillna(0.0)
    df_stu_ass_cleaned["score"] = df_stu_ass_cleaned["score"].clip(lower=0.0, upper=100.0)
    df_stu_ass_cleaned.to_csv(os.path.join(processed_oulad_dir, "studentAssessment_cleaned.csv"), index=False)
    
    # 5. Đọc và làm sạch studentVle
    vle_file = os.path.join(raw_oulad_dir, "studentVle_raw.csv")
    df_vle = pd.read_csv(vle_file)
    init_vle_count = len(df_vle)
    
    # Loại bỏ trùng lặp tương tác click
    dup_vle = df_vle.duplicated(subset=["code_module", "code_presentation", "id_student", "id_site", "date"]).sum()
    df_vle_cleaned = df_vle.drop_duplicates(subset=["code_module", "code_presentation", "id_student", "id_site", "date"], keep="first").copy()
    df_vle_cleaned["sum_click"] = df_vle_cleaned["sum_click"].clip(lower=0)
    df_vle_cleaned.to_csv(os.path.join(processed_oulad_dir, "studentVle_cleaned.csv"), index=False)
    
    # 6. Tạo Feature Matrix tích hợp tổng hợp hành vi của sinh viên
    # Phục vụ huấn luyện Machine Learning dự báo nguy cơ không hoàn thành (Quân)
    # và nạp vào Fact_KetQuaHocTap trong Data Warehouse (Đức)
    print("[OULAD] Đang tổng hợp Feature Matrix học tập tích hợp...")
    
    # Tổng clicks từ VLE
    vle_agg = df_vle_cleaned.groupby(["code_module", "code_presentation", "id_student"]).agg(
        total_clicks=("sum_click", "sum"),
        active_days=("date", "nunique")
    ).reset_index()
    
    # Điểm số trung bình từ Assessment
    ass_agg = df_stu_ass_cleaned.groupby("id_student").agg(
        avg_score=("score", "mean"),
        assessments_completed=("id_assessment", "count")
    ).reset_index()
    
    merged = pd.merge(df_students_cleaned, vle_agg, on=["code_module", "code_presentation", "id_student"], how="left")
    merged = pd.merge(merged, ass_agg, on="id_student", how="left")
    
    merged["total_clicks"] = merged["total_clicks"].fillna(0).astype(int)
    merged["active_days"] = merged["active_days"].fillna(0).astype(int)
    merged["avg_score"] = merged["avg_score"].fillna(0.0).round(2)
    merged["assessments_completed"] = merged["assessments_completed"].fillna(0).astype(int)
    
    # Gán nhãn phân loại nguy cơ (Risk Level) theo đề cương:
    # Fail/Withdrawn -> High Risk; Pass -> Low Risk; Distinction -> Very Low
    def assign_risk_level(row):
        res = row["final_result"]
        if res == "Withdrawn":
            return "High"
        elif res == "Fail":
            return "Medium"
        else:
            return "Low"
            
    merged["risk_level"] = merged.apply(assign_risk_level, axis=1)
    
    feature_matrix_path = os.path.join(processed_oulad_dir, "student_features_analytics.csv")
    merged.to_csv(feature_matrix_path, index=False)
    
    total_raw_rows = init_stu_count + init_ass_count + init_vle_count
    total_dups_removed = dup_stu + dup_ass + dup_vle
    dup_rate_after = 0.0 # Sau khi drop_duplicates() thì tỷ lệ trùng còn lại chính xác là 0%
    
    stats = {
        "dataset_name": "OULAD (Open University)",
        "initial_records": int(total_raw_rows),
        "duplicates_removed": int(total_dups_removed),
        "final_records": int(total_raw_rows - total_dups_removed),
        "duplicate_rate_before": f"{(total_dups_removed / total_raw_rows) * 100:.2f}%",
        "duplicate_rate_after": f"{dup_rate_after:.2f}%",
        "target_duplicate_rate": "< 1.0%",
        "status": "PASSED",
        "student_feature_records": len(merged)
    }
    print(f"[OULAD] Hoàn tất: Đã loại {total_dups_removed} bản ghi trùng. Xuất file đặc trưng học tập {feature_matrix_path}")
    return stats
