"""
WEF (World Economic Forum) Data Cleaning & Normalization Module
Phụ trách: Đinh Thị Lan Anh - 2351160500 (Nhóm 05)
Chức năng:
- Báo cáo xu hướng nghề nghiệp quốc tế (The Future of Jobs Report - World Economic Forum)
- Chuẩn hóa thông tin: Nhóm nghề tăng trưởng (Emerging Jobs), Nghề suy giảm (Declining Jobs),
  Kỹ năng cốt lõi (Core Skills), và Xu hướng ứng dụng công nghệ (Technology Adoption).
- Phân tích mức độ liên đới và triển vọng phát triển tại thị trường lao động Việt Nam.
- Loại bỏ trùng lặp đảm bảo tỷ lệ trùng < 1%.
"""

import os
import re
import pandas as pd
import numpy as np


def clean_text(text):
    if not isinstance(text, str):
        return ""
    cleaned = re.sub(r"<[^>]+>", " ", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def clean_wef_pipeline(input_path, output_path):
    print(f"\n[WEF Trends] Đang tiến hành làm sạch & chuẩn hóa dữ liệu xu hướng quốc tế: {input_path}")
    df = pd.read_csv(input_path, encoding="utf-8-sig")
    initial_count = len(df)
    
    # 1. Làm sạch văn bản
    df["item_name_clean"] = df["item_name"].apply(clean_text)
    df["category_clean"] = df["category"].apply(clean_text)
    df["description_clean"] = df["description"].apply(clean_text)
    
    # 2. Chuẩn hóa tỷ lệ tăng trưởng và thời gian đào tạo
    df["growth_rate_pct"] = pd.to_numeric(df["growth_rate_pct"], errors="coerce").fillna(0.0).round(1)
    df["reskilling_months"] = pd.to_numeric(df["reskilling_duration_months"], errors="coerce").fillna(6).astype(int)
    
    # 3. Chuẩn hóa mức độ liên đới với thị trường Việt Nam
    def normalize_vn_relevance(val):
        if not isinstance(val, str):
            return "Medium"
        v = val.strip().title()
        return v if v in ["High", "Medium", "Emerging", "Low"] else "Medium"
        
    df["vn_relevance"] = df["relevance_to_vietnam"].apply(normalize_vn_relevance)
    
    # 4. Loại bỏ bản ghi trùng lặp (Deduplication)
    # Khóa kết hợp: category_clean, item_name_clean
    dup_mask = df.duplicated(subset=["category_clean", "item_name_clean"], keep="first")
    duplicate_count = dup_mask.sum()
    df_cleaned = df[~dup_mask].copy()
    
    remaining_dups = df_cleaned.duplicated(subset=["category_clean", "item_name_clean"]).sum()
    dup_rate_after = (remaining_dups / len(df_cleaned)) * 100 if len(df_cleaned) > 0 else 0
    
    output_df = pd.DataFrame({
        "trend_id": df_cleaned["trend_id"],
        "report_source": df_cleaned["report_source"],
        "category": df_cleaned["category_clean"],
        "item_name": df_cleaned["item_name_clean"],
        "growth_rate_pct": df_cleaned["growth_rate_pct"],
        "global_demand_level": df_cleaned["demand_level"].fillna("High"),
        "primary_sector": df_cleaned["impact_sector"].fillna("Information Technology"),
        "reskilling_months": df_cleaned["reskilling_months"],
        "vietnam_relevance": df_cleaned["vn_relevance"],
        "trend_description": df_cleaned["description_clean"]
    })
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    output_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    
    stats = {
        "dataset_name": "WEF International Trends",
        "initial_records": initial_count,
        "duplicates_removed": int(duplicate_count),
        "final_records": len(output_df),
        "duplicate_rate_before": f"{(duplicate_count / initial_count) * 100:.2f}%",
        "duplicate_rate_after": f"{dup_rate_after:.2f}%",
        "target_duplicate_rate": "< 1.0%",
        "status": "PASSED" if dup_rate_after < 1.0 else "FAILED"
    }
    print(f"[WEF Trends] Hoàn tất: {initial_count} -> {len(output_df)} bản ghi. Đã loại {duplicate_count} bản ghi trùng. Tỷ lệ trùng sau xử lý: {dup_rate_after:.2f}% (Đạt tiêu chuẩn < 1%)")
    return stats
