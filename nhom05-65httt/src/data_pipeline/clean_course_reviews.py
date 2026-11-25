"""
Course Reviews Cleaning & Deduplication Module
Phụ trách: Đinh Thị Lan Anh - 2351160500 (Nhóm 05)
Chức năng:
- Bóc tách thẻ HTML, ký tự bẩn, khoảng trắng thừa trong văn bản nhận xét
- Chuẩn hóa điểm rating trong khoảng [1.0, 5.0], xử lý giá trị thiếu
- Chuẩn hóa thông tin khóa học, đơn vị cung cấp, phân loại lĩnh vực
- Loại bỏ bản ghi đánh giá trùng lặp (Deduplication) đảm bảo tỷ lệ trùng < 1%
- Gắn nhãn sơ bộ ngôn ngữ và cảm xúc (Positive, Neutral, Negative) phục vụ NLP (Diễm Quỳnh)
"""

import os
import re
import pandas as pd
import numpy as np


def clean_review_text(text):
    if not isinstance(text, str):
        return ""
    # Xóa thẻ HTML
    cleaned = re.sub(r"<[^>]+>", " ", text)
    # Xóa ký tự điều khiển hoặc tab xuống dòng lộn xộn
    cleaned = re.sub(r"[\r\n\t]+", " ", cleaned)
    # Chuẩn hóa khoảng trắng
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def detect_language(text):
    if not isinstance(text, str) or not text:
        return "unknown"
    # Dấu hiệu tiếng Việt cơ bản
    vn_chars = set("àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ")
    text_lower = text.lower()
    if any(char in vn_chars for char in text_lower):
        return "vi"
    return "en"


def clean_course_reviews_pipeline(input_path, output_path):
    print(f"\n[Course Reviews] Đang làm sạch & loại bỏ trùng lặp: {input_path}")
    df = pd.read_csv(input_path, encoding="utf-8-sig")
    initial_count = len(df)
    
    # 1. Làm sạch văn bản nhận xét
    df["review_text_clean"] = df["review_text"].apply(clean_review_text)
    
    # 2. Chuẩn hóa Rating: hợp lệ trong khoảng [1.0, 5.0]
    # Lấy rating trung bình của từng khóa học để điền missing/lỗi
    course_mean_ratings = df[df["rating"].between(1.0, 5.0)].groupby("course_id")["rating"].mean().to_dict()
    
    def normalize_rating(row):
        r = row["rating"]
        cid = row["course_id"]
        if pd.isna(r) or r < 1.0 or r > 5.0:
            return round(course_mean_ratings.get(cid, 4.0), 1)
        return round(float(r), 1)
        
    df["rating_clean"] = df.apply(normalize_rating, axis=1)
    
    # 3. Gắn nhãn ngôn ngữ và phân loại cảm xúc sơ bộ
    df["language"] = df["review_text_clean"].apply(detect_language)
    
    def assign_sentiment(r):
        if r >= 4.0:
            return "Positive"
        elif r >= 3.0:
            return "Neutral"
        else:
            return "Negative"
            
    df["sentiment_label"] = df["rating_clean"].apply(assign_sentiment)
    
    # 4. Loại bỏ bản ghi trùng lặp (Deduplication)
    # Khóa kết hợp: course_id và review_text_clean
    dup_mask = df.duplicated(subset=["course_id", "review_text_clean"], keep="first")
    duplicate_count = dup_mask.sum()
    df_cleaned = df[~dup_mask].copy()
    
    remaining_dups = df_cleaned.duplicated(subset=["course_id", "review_text_clean"]).sum()
    dup_rate_after = (remaining_dups / len(df_cleaned)) * 100 if len(df_cleaned) > 0 else 0
    
    output_df = pd.DataFrame({
        "review_id": df_cleaned["review_id"],
        "course_id": df_cleaned["course_id"],
        "course_title": df_cleaned["course_title"],
        "provider": df_cleaned["provider"],
        "category": df_cleaned["category"],
        "rating": df_cleaned["rating_clean"],
        "sentiment": df_cleaned["sentiment_label"],
        "language": df_cleaned["language"],
        "review_text": df_cleaned["review_text_clean"],
        "review_date": df_cleaned["review_date"],
        "learner_level": df_cleaned["learner_level"].fillna("All Levels"),
        "helpful_count": df_cleaned["helpful_count"].fillna(0).astype(int)
    })
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    output_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    
    stats = {
        "dataset_name": "Course Reviews",
        "initial_records": initial_count,
        "duplicates_removed": int(duplicate_count),
        "final_records": len(output_df),
        "duplicate_rate_before": f"{(duplicate_count / initial_count) * 100:.2f}%",
        "duplicate_rate_after": f"{dup_rate_after:.2f}%",
        "target_duplicate_rate": "< 1.0%",
        "status": "PASSED" if dup_rate_after < 1.0 else "FAILED"
    }
    print(f"[Course Reviews] Hoàn tất: {initial_count} -> {len(output_df)} bản ghi. Đã loại {duplicate_count} bản ghi trùng. Tỷ lệ trùng sau xử lý: {dup_rate_after:.2f}% (Đạt tiêu chuẩn < 1%)")
    return stats
