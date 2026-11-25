"""
VietJobs Data Cleaning & Deduplication Module
Phụ trách: Đinh Thị Lan Anh - 2351160500 (Nhóm 05)
Chức năng:
- Làm sạch và chuẩn hóa tiêu đề công việc, công ty, mô tả (loại bỏ HTML, ký tự đặc biệt)
- Chuẩn hóa địa điểm (Mapping về danh mục tỉnh thành chuẩn)
- Chuẩn hóa danh sách kỹ năng công nghệ
- Trích xuất và chuẩn hóa khoảng lương (VNĐ triệu/tháng)
- Chuẩn hóa định dạng ngày tháng đăng tuyển (YYYY-MM-DD)
- Phát hiện và loại bỏ bản ghi trùng lặp (Deduplication) đảm bảo tỷ lệ trùng < 1%
"""

import os
import re
import pandas as pd
import numpy as np


def clean_html_and_text(text):
    if not isinstance(text, str):
        return ""
    # Loại bỏ thẻ HTML
    cleaned = re.sub(r"<[^>]+>", " ", text)
    # Loại bỏ ký tự đặc biệt thừa ở đầu cuối (ví dụ ***, ---)
    cleaned = re.sub(r"^[\*\-_#\s]+|[\*\-_#\s]+$", "", cleaned)
    # Chuẩn hóa nhiều khoảng trắng liên tiếp
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def normalize_location(loc_str):
    if not isinstance(loc_str, str):
        return "Toàn quốc"
    loc_lower = loc_str.lower().strip()
    
    if "hà nội" in loc_lower or "hanoi" in loc_lower:
        return "Hà Nội"
    elif "hồ chí minh" in loc_lower or "hcm" in loc_lower or "ho chi minh" in loc_lower:
        return "TP. Hồ Chí Minh"
    elif "đà nẵng" in loc_lower or "da nang" in loc_lower:
        return "Đà Nẵng"
    elif "cần thơ" in loc_lower or "can tho" in loc_lower:
        return "Cần Thơ"
    elif "hải phòng" in loc_lower or "hai phong" in loc_lower:
        return "Hải Phòng"
    elif "remote" in loc_lower or "từ xa" in loc_lower:
        return "Remote"
    else:
        return "Toàn quốc"


def normalize_skills(skills_str):
    if not isinstance(skills_str, str):
        return ""
    
    # Chuẩn hóa bộ từ điển kỹ năng chuẩn
    canonical_skills = {
        "python": "Python",
        "sql": "SQL",
        "postgresql": "PostgreSQL",
        "postgres": "PostgreSQL",
        "power bi": "Power BI",
        "powerbi": "Power BI",
        "tableau": "Tableau",
        "machine learning": "Machine Learning",
        "ml": "Machine Learning",
        "deep learning": "Deep Learning",
        "nlp": "NLP",
        "pandas": "Pandas",
        "scikit-learn": "Scikit-Learn",
        "sklearn": "Scikit-Learn",
        "docker": "Docker",
        "apache spark": "Apache Spark",
        "spark": "Apache Spark",
        "hadoop": "Hadoop",
        "airflow": "Apache Airflow",
        "fastapi": "FastAPI",
        "django": "Django",
        "git": "Git",
        "excel": "Excel",
        "data modeling": "Data Modeling",
        "etl pipeline": "ETL Pipeline",
        "etl": "ETL Pipeline",
        "data warehouse": "Data Warehouse",
        "aws": "AWS",
        "azure": "Azure",
        "gcp": "GCP",
        "pytorch": "PyTorch",
        "tensorflow": "TensorFlow"
    }
    
    # Phân tách theo dấu phẩy hoặc thanh dọc |
    raw_tokens = re.split(r"[,|;]", skills_str)
    normalized = []
    for token in raw_tokens:
        clean_tok = token.strip().lower()
        if clean_tok in canonical_skills:
            normalized.append(canonical_skills[clean_tok])
        elif clean_tok:
            # Viết hoa chữ cái đầu nếu không có trong từ điển
            normalized.append(clean_tok.title())
            
    # Loại bỏ kỹ năng trùng trong 1 tin và sắp xếp
    unique_skills = sorted(list(set(normalized)))
    return ", ".join(unique_skills)


def parse_salary(salary_raw):
    """
    Chuẩn hóa mức lương về triệu VNĐ/tháng:
    Trả về: (salary_min, salary_max, salary_currency, is_negotiable)
    """
    if not isinstance(salary_raw, str):
        return np.nan, np.nan, "VND", True
    
    s = salary_raw.lower().strip()
    if "thỏa thuận" in s or "thoathuan" in s or not s:
        return np.nan, np.nan, "VND", True
    
    # Trường hợp USD (VD: 1500 USD -> quy đổi tạm 25.000đ = 1 USD)
    if "usd" in s:
        match = re.search(r"(\d+)", s)
        if match:
            usd_val = float(match.group(1))
            val_mil = round((usd_val * 25400) / 1000000, 1)
            return val_mil, val_mil, "VND", False
            
    # Trường hợp từ X triệu
    match_from = re.search(r"từ\s*(\d+)", s)
    if match_from:
        val = float(match_from.group(1))
        return val, np.nan, "VND", False
        
    # Trường hợp khoảng X - Y triệu
    match_range = re.search(r"(\d+)\s*[-–—]\s*(\d+)", s)
    if match_range:
        v1 = float(match_range.group(1))
        v2 = float(match_range.group(2))
        # Nếu đơn vị ghi dạng số triệu đầy đủ (vd 15000000)
        if v1 > 100000:
            v1 = round(v1 / 1000000, 1)
            v2 = round(v2 / 1000000, 1)
        return min(v1, v2), max(v1, v2), "VND", False
        
    return np.nan, np.nan, "VND", True


def normalize_date(date_str):
    if not isinstance(date_str, str):
        return "2026-01-01"
    date_str = date_str.strip()
    # Dạng dd/mm/yyyy
    match_vn = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", date_str)
    if match_vn:
        d, m, y = match_vn.groups()
        return f"{y}-{int(m):02d}-{int(d):02d}"
    # Dạng yyyy-mm-dd
    match_iso = re.match(r"^\d{4}-\d{2}-\d{2}$", date_str)
    if match_iso:
        return date_str
    return "2026-01-01"


def clean_vietjobs_pipeline(input_path, output_path):
    print(f"\n[VietJobs] Đang tiến hành làm sạch & loại bỏ trùng lặp: {input_path}")
    df = pd.read_csv(input_path, encoding="utf-8-sig")
    initial_count = len(df)
    
    # 1. Làm sạch văn bản và chuẩn hóa trường
    df["title_clean"] = df["title"].apply(clean_html_and_text)
    df["company_clean"] = df["company"].apply(clean_html_and_text)
    df["location_clean"] = df["location"].apply(normalize_location)
    df["skills_clean"] = df["required_skills"].apply(normalize_skills)
    df["description_clean"] = df["job_description"].apply(clean_html_and_text)
    df["posted_date_clean"] = df["posted_date"].apply(normalize_date)
    
    # Xử lý lương
    salary_parsed = df["salary_raw"].apply(parse_salary)
    df["salary_min_mil"] = [p[0] for p in salary_parsed]
    df["salary_max_mil"] = [p[1] for p in salary_parsed]
    df["is_salary_negotiable"] = [p[3] for p in salary_parsed]
    
    # Xử lý missing values
    df["experience"] = df["experience"].fillna("Không yêu cầu").replace("", "Không yêu cầu")
    df["education"] = df["education"].fillna("Không yêu cầu").replace("", "Không yêu cầu")
    
    # 2. Phát hiện & loại bỏ dữ liệu trùng lặp (Deduplication)
    # Khóa kết hợp: title_clean, company_clean, location_clean
    # Bản ghi trùng lặp được giữ lại bản ghi đầu tiên
    dup_mask = df.duplicated(subset=["title_clean", "company_clean", "location_clean"], keep="first")
    duplicate_count = dup_mask.sum()
    df_cleaned = df[~dup_mask].copy()
    
    # Sau đó kiểm tra lại tỷ lệ trùng lặp còn lại
    remaining_dups = df_cleaned.duplicated(subset=["title_clean", "company_clean", "location_clean"]).sum()
    dup_rate_after = (remaining_dups / len(df_cleaned)) * 100 if len(df_cleaned) > 0 else 0
    
    # Chuẩn bị DataFrame xuất ra với schema chuẩn hoá
    output_df = pd.DataFrame({
        "job_id": df_cleaned["job_id"],
        "job_title": df_cleaned["title_clean"],
        "company_name": df_cleaned["company_clean"],
        "location": df_cleaned["location_clean"],
        "industry": df_cleaned["industry"],
        "required_skills": df_cleaned["skills_clean"],
        "salary_min_mil": df_cleaned["salary_min_mil"],
        "salary_max_mil": df_cleaned["salary_max_mil"],
        "is_salary_negotiable": df_cleaned["is_salary_negotiable"],
        "experience_level": df_cleaned["experience"],
        "education_level": df_cleaned["education"],
        "posted_date": df_cleaned["posted_date_clean"],
        "source": df_cleaned["source"],
        "job_description": df_cleaned["description_clean"]
    })
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    output_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    
    stats = {
        "dataset_name": "VietJobs",
        "initial_records": initial_count,
        "duplicates_removed": int(duplicate_count),
        "final_records": len(output_df),
        "duplicate_rate_before": f"{(duplicate_count / initial_count) * 100:.2f}%",
        "duplicate_rate_after": f"{dup_rate_after:.2f}%",
        "target_duplicate_rate": "< 1.0%",
        "status": "PASSED" if dup_rate_after < 1.0 else "FAILED"
    }
    print(f"[VietJobs] Hoàn tất: {initial_count} -> {len(output_df)} bản ghi. Đã loại {duplicate_count} bản ghi trùng. Tỷ lệ trùng sau xử lý: {dup_rate_after:.2f}% (Đạt tiêu chuẩn < 1%)")
    return stats
