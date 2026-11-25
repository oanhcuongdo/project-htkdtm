"""
Data Warehouse ETL Pipeline (Staging -> Star Schema)
Dự án: Hệ thống quản lý đào tạo thông minh (HTKDTM - Nhóm 05)
Phụ trách: Nguyễn Quang Đức (Data Warehouse & BI)

Chức năng:
1. Khởi tạo lược đồ Star Schema (dw.*) từ dw_star_schema.sql
2. Nạp toàn bộ dữ liệu sạch từ data/processed/ vào các bảng staging (public.*)
   (khắc phục giới hạn 500 dòng của seed mẫu, nạp đầy đủ VietJobs, OULAD, Course Reviews, WEF)
3. Tổng hợp dữ liệu tương tác VLE (studentVle_cleaned.csv) theo activity_type vào dw.fact_vle_engagement
4. Thực thi dw_etl_from_staging.sql để đồng bộ Dimensions & Facts trong schema dw
5. Khởi tạo/cập nhật toàn bộ BI Views cho 3 Dashboards trên Apache Superset
"""

import os
import sys
import pandas as pd
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
SQL_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(BASE_DIR, "src", "backend", ".env")

load_dotenv(ENV_FILE)

DB_NAME = os.getenv("DB_NAME", "training_analytics")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgrespassword")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")


def get_connection():
    """Tạo kết nối PostgreSQL sử dụng psycopg (v3) hoặc psycopg2."""
    try:
        import psycopg
        return psycopg.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
    except ImportError:
        import psycopg2
        return psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )


def execute_sql_file(conn, filename: str):
    """Đọc và thực thi một tệp SQL trong thư mục src/database."""
    filepath = os.path.join(SQL_DIR, filename)
    if not os.path.exists(filepath):
        print(f"[!] Không tìm thấy tệp SQL: {filepath}")
        return
    with open(filepath, "r", encoding="utf-8") as f:
        sql_content = f.read()
    with conn.cursor() as cur:
        cur.execute(sql_content)
    conn.commit()
    print(f"[OK] Đã thực thi {filename}")


def load_full_staging_data(conn):
    """Nạp đầy đủ dữ liệu sạch từ CSV vào các bảng staging (public.*)."""
    cur = conn.cursor()

    # 1. OULAD Courses
    courses_csv = os.path.join(PROCESSED_DIR, "oulad", "courses_cleaned.csv")
    if os.path.exists(courses_csv):
        df = pd.read_csv(courses_csv)
        for _, r in df.iterrows():
            cur.execute(
                """
                INSERT INTO public.dim_course (code_module, code_presentation, module_presentation_length)
                VALUES (%s, %s, %s)
                ON CONFLICT (code_module, code_presentation) DO NOTHING
                """,
                (r["code_module"], r["code_presentation"], int(r["module_presentation_length"])),
            )
        print(f"[+] Staging dim_course: {len(df)} dòng")

    # 2. OULAD StudentInfo
    student_csv = os.path.join(PROCESSED_DIR, "oulad", "studentInfo_cleaned.csv")
    if os.path.exists(student_csv):
        df = pd.read_csv(student_csv)
        for _, r in df.iterrows():
            cur.execute(
                """
                INSERT INTO public.dim_student (
                    id_student, code_module, code_presentation, gender, region,
                    highest_education, imd_band, age_band, num_of_prev_attempts,
                    studied_credits, disability, final_result
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (code_module, code_presentation, id_student) DO NOTHING
                """,
                (
                    int(r["id_student"]), r["code_module"], r["code_presentation"],
                    r["gender"], r["region"], r["highest_education"],
                    None if pd.isna(r["imd_band"]) else str(r["imd_band"]),
                    r["age_band"], int(r["num_of_prev_attempts"]),
                    int(r["studied_credits"]), r["disability"], r["final_result"],
                ),
            )
        print(f"[+] Staging dim_student: {len(df)} dòng")

    # 3. OULAD Assessments
    ass_csv = os.path.join(PROCESSED_DIR, "oulad", "assessments_cleaned.csv")
    if os.path.exists(ass_csv):
        df = pd.read_csv(ass_csv)
        for _, r in df.iterrows():
            cur.execute(
                """
                INSERT INTO public.dim_assessment (
                    id_assessment, code_module, code_presentation, assessment_type, date, weight
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id_assessment) DO NOTHING
                """,
                (
                    int(r["id_assessment"]), r["code_module"], r["code_presentation"],
                    r["assessment_type"],
                    None if pd.isna(r["date"]) else int(r["date"]),
                    float(r["weight"]),
                ),
            )
        print(f"[+] Staging dim_assessment: {len(df)} dòng")

    # 4. OULAD StudentAssessment
    sa_csv = os.path.join(PROCESSED_DIR, "oulad", "studentAssessment_cleaned.csv")
    if os.path.exists(sa_csv):
        df = pd.read_csv(sa_csv)
        for _, r in df.iterrows():
            cur.execute(
                """
                INSERT INTO public.fact_student_assessment (
                    id_assessment, id_student, date_submitted, is_banked, score
                ) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id_assessment, id_student) DO NOTHING
                """,
                (
                    int(r["id_assessment"]), int(r["id_student"]),
                    int(r["date_submitted"]), int(r["is_banked"]),
                    None if pd.isna(r["score"]) else float(r["score"]),
                ),
            )
        print(f"[+] Staging fact_student_assessment: {len(df)} dòng")

    # 5. OULAD Student Features Analytics
    feat_csv = os.path.join(PROCESSED_DIR, "oulad", "student_features_analytics.csv")
    if os.path.exists(feat_csv):
        df = pd.read_csv(feat_csv)
        for _, r in df.iterrows():
            cur.execute(
                """
                INSERT INTO public.fact_student_learning_analytics (
                    id_student, code_module, code_presentation, gender, region,
                    highest_education, age_band, studied_credits, final_result,
                    total_clicks, active_days, avg_score, assessments_completed, risk_level
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (code_module, code_presentation, id_student) DO NOTHING
                """,
                (
                    int(r["id_student"]), r["code_module"], r["code_presentation"],
                    r["gender"], r["region"], r["highest_education"], r["age_band"],
                    int(r["studied_credits"]), r["final_result"],
                    int(r["total_clicks"]), int(r["active_days"]),
                    float(r["avg_score"]), int(r["assessments_completed"]), r["risk_level"],
                ),
            )
        print(f"[+] Staging fact_student_learning_analytics: {len(df)} dòng")

    # 6. Course Reviews
    rev_csv = os.path.join(PROCESSED_DIR, "course_reviews", "course_reviews_cleaned.csv")
    if os.path.exists(rev_csv):
        df = pd.read_csv(rev_csv)
        for _, r in df.iterrows():
            cur.execute(
                """
                INSERT INTO public.fact_course_reviews (
                    review_id, course_id, course_title, provider, category,
                    rating, sentiment, language, review_text, review_date,
                    learner_level, helpful_count
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (review_id) DO NOTHING
                """,
                (
                    r["review_id"], r["course_id"], r["course_title"],
                    r["provider"], r["category"], float(r["rating"]),
                    r["sentiment"], r["language"], r["review_text"],
                    r["review_date"], r["learner_level"], int(r["helpful_count"]),
                ),
            )
        print(f"[+] Staging fact_course_reviews: {len(df)} dòng")

    # 7. VietJobs
    vj_csv = os.path.join(PROCESSED_DIR, "vietjobs", "vietjobs_cleaned.csv")
    if os.path.exists(vj_csv):
        df = pd.read_csv(vj_csv)
        for _, r in df.iterrows():
            cur.execute(
                """
                INSERT INTO public.fact_job_postings (
                    job_id, job_title, company_name, location, industry,
                    required_skills, salary_min_mil, salary_max_mil,
                    is_salary_negotiable, experience_level, education_level,
                    posted_date, source, job_description
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (job_id) DO NOTHING
                """,
                (
                    r["job_id"], r["job_title"], r["company_name"], r["location"],
                    r["industry"], r["required_skills"],
                    None if pd.isna(r["salary_min_mil"]) else float(r["salary_min_mil"]),
                    None if pd.isna(r["salary_max_mil"]) else float(r["salary_max_mil"]),
                    bool(r["is_salary_negotiable"]), r["experience_level"],
                    r["education_level"], r["posted_date"], r["source"], r["job_description"],
                ),
            )
        print(f"[+] Staging fact_job_postings: {len(df)} dòng")

    # 8. WEF Trends
    wef_csv = os.path.join(PROCESSED_DIR, "wef", "wef_trends_cleaned.csv")
    if os.path.exists(wef_csv):
        df = pd.read_csv(wef_csv)
        for _, r in df.iterrows():
            cur.execute(
                """
                INSERT INTO public.wef_global_trends (
                    trend_id, report_source, category, item_name,
                    growth_rate_pct, global_demand_level, primary_sector,
                    reskilling_months, vietnam_relevance, trend_description
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (trend_id) DO NOTHING
                """,
                (
                    r["trend_id"], r["report_source"], r["category"], r["item_name"],
                    float(r["growth_rate_pct"]), r["global_demand_level"],
                    r["primary_sector"], int(r["reskilling_months"]),
                    r["vietnam_relevance"], r["trend_description"],
                ),
            )
        print(f"[+] Staging wef_global_trends: {len(df)} dòng")

    conn.commit()
    cur.close()


def load_vle_engagement_to_dw(conn):
    """Tổng hợp dữ liệu VLE (studentVle_cleaned.csv) theo activity_type vào dw.fact_vle_engagement."""
    vle_csv = os.path.join(PROCESSED_DIR, "oulad", "studentVle_cleaned.csv")
    if not os.path.exists(vle_csv):
        return

    df_vle = pd.read_csv(vle_csv)
    agg = (
        df_vle.groupby(["id_student", "code_module", "code_presentation", "activity_type"], as_index=False)
        .agg(total_clicks=("sum_click", "sum"), active_days_count=("date", "nunique"))
    )

    cur = conn.cursor()
    cur.execute("SELECT id_student, student_sk FROM dw.dim_student")
    student_map = dict(cur.fetchall())

    cur.execute("SELECT course_code, course_sk FROM dw.dim_course WHERE source_system = 'OULAD'")
    course_map = dict(cur.fetchall())

    inserted = 0
    for _, r in agg.iterrows():
        s_sk = student_map.get(int(r["id_student"]))
        c_sk = course_map.get(f"{r['code_module']}-{r['code_presentation']}")
        if s_sk and c_sk:
            cur.execute(
                """
                INSERT INTO dw.fact_vle_engagement (
                    student_sk, course_sk, activity_type, total_clicks, active_days_count
                ) VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (student_sk, course_sk, activity_type) DO UPDATE SET
                    total_clicks = EXCLUDED.total_clicks,
                    active_days_count = EXCLUDED.active_days_count
                """,
                (s_sk, c_sk, r["activity_type"], int(r["total_clicks"]), int(r["active_days_count"])),
            )
            inserted += 1

    conn.commit()
    cur.close()
    print(f"[+] DW fact_vle_engagement: {inserted} dòng tổng hợp từ {len(df_vle)} log VLE")


def run_warehouse_etl():
    print("=== BẮT ĐẦU QUY TRÌNH ETL DATA WAREHOUSE (NGUYỄN QUANG ĐỨC) ===")
    try:
        conn = get_connection()
    except Exception as exc:
        print(f"[!] Không thể kết nối PostgreSQL ({DB_HOST}:{DB_PORT}/{DB_NAME}): {exc}")
        sys.exit(1)

    try:
        execute_sql_file(conn, "schema_postgresql.sql")
        execute_sql_file(conn, "dw_star_schema.sql")
        load_full_staging_data(conn)
        execute_sql_file(conn, "dw_etl_from_staging.sql")
        load_vle_engagement_to_dw(conn)
        execute_sql_file(conn, "dw_views_academic.sql")
        execute_sql_file(conn, "dw_views_quality.sql")
        execute_sql_file(conn, "dw_views_careers.sql")
        print("=== HOÀN TẤT ETL DATA WAREHOUSE & BI VIEWS ===")
    finally:
        conn.close()


if __name__ == "__main__":
    run_warehouse_etl()
