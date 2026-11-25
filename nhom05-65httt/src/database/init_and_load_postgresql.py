"""
PostgreSQL Database Initializer and Data Loader
Dự án: Hệ thống quản lý đào tạo thông minh (HTKDTM - Nhóm 05)
Chức năng:
1. Đọc và thực thi DDL Schema từ schema_postgresql.sql trên PostgreSQL 16.x
2. Đọc toàn bộ dữ liệu sạch từ data/processed/ (VietJobs, OULAD, Course Reviews, WEF)
3. Nạp dữ liệu vào các bảng tương ứng trên PostgreSQL
4. Tạo tệp sao lưu dữ liệu toàn diện seed_data_postgresql.sql (hỗ trợ nhập nhanh bằng psql CLI)
"""

import os
import sys
import pandas as pd
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
SQL_DIR = os.path.join(BASE_DIR, "src", "database")
ENV_FILE = os.path.join(BASE_DIR, "src", "backend", ".env")

load_dotenv(ENV_FILE)

DB_NAME = os.getenv("DB_NAME", "training_analytics")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")


def generate_seed_sql_file():
    """Tạo tệp SQL hoàn chỉnh chứa cả cấu trúc bảng và toàn bộ dữ liệu sạch (INSERT statements)"""
    schema_path = os.path.join(SQL_DIR, "schema_postgresql.sql")
    seed_path = os.path.join(SQL_DIR, "seed_data_postgresql.sql")
    
    print(f"\n[*] Đang tạo tệp SQL nạp dữ liệu hoàn chỉnh: {seed_path}")
    
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()
        
    insert_statements = []
    
    # 1. Nạp WEF Trends
    wef_csv = os.path.join(PROCESSED_DIR, "wef", "wef_trends_cleaned.csv")
    if os.path.exists(wef_csv):
        df_wef = pd.read_csv(wef_csv)
        insert_statements.append("\n-- Data for wef_global_trends")
        for _, row in df_wef.iterrows():
            desc = str(row["trend_description"]).replace("'", "''")
            item = str(row["item_name"]).replace("'", "''")
            insert_statements.append(
                f"INSERT INTO wef_global_trends (trend_id, report_source, category, item_name, growth_rate_pct, global_demand_level, primary_sector, reskilling_months, vietnam_relevance, trend_description) "
                f"VALUES ('{row['trend_id']}', '{row['report_source']}', '{row['category']}', '{item}', {row['growth_rate_pct']}, '{row['global_demand_level']}', '{row['primary_sector']}', {row['reskilling_months']}, '{row['vietnam_relevance']}', '{desc}') "
                f"ON CONFLICT (trend_id) DO NOTHING;"
            )
            
    # 2. Nạp VietJobs (lấy tối đa 500 bản ghi mẫu để file SQL gọn nhẹ và thực thi nhanh)
    vj_csv = os.path.join(PROCESSED_DIR, "vietjobs", "vietjobs_cleaned.csv")
    if os.path.exists(vj_csv):
        df_vj = pd.read_csv(vj_csv)
        insert_statements.append(f"\n-- Data for fact_job_postings ({len(df_vj)} records)")
        for _, row in df_vj.head(500).iterrows():
            title = str(row["job_title"]).replace("'", "''")
            comp = str(row["company_name"]).replace("'", "''")
            skills = str(row["required_skills"]).replace("'", "''")
            desc = str(row["job_description"]).replace("'", "''")
            s_min = f"{row['salary_min_mil']}" if pd.notna(row['salary_min_mil']) else "NULL"
            s_max = f"{row['salary_max_mil']}" if pd.notna(row['salary_max_mil']) else "NULL"
            neg = "TRUE" if row["is_salary_negotiable"] else "FALSE"
            
            insert_statements.append(
                f"INSERT INTO fact_job_postings (job_id, job_title, company_name, location, industry, required_skills, salary_min_mil, salary_max_mil, is_salary_negotiable, experience_level, education_level, posted_date, source, job_description) "
                f"VALUES ('{row['job_id']}', '{title}', '{comp}', '{row['location']}', '{row['industry']}', '{skills}', {s_min}, {s_max}, {neg}, '{row['experience_level']}', '{row['education_level']}', '{row['posted_date']}', '{row['source']}', '{desc}') "
                f"ON CONFLICT (job_id) DO NOTHING;"
            )
            
    # 3. Nạp OULAD Courses & Features
    course_csv = os.path.join(PROCESSED_DIR, "oulad", "courses_cleaned.csv")
    if os.path.exists(course_csv):
        df_c = pd.read_csv(course_csv)
        insert_statements.append("\n-- Data for dim_course")
        for _, row in df_c.iterrows():
            insert_statements.append(
                f"INSERT INTO dim_course (code_module, code_presentation, module_presentation_length) "
                f"VALUES ('{row['code_module']}', '{row['code_presentation']}', {row['module_presentation_length']}) "
                f"ON CONFLICT (code_module, code_presentation) DO NOTHING;"
            )
            
    feat_csv = os.path.join(PROCESSED_DIR, "oulad", "student_features_analytics.csv")
    if os.path.exists(feat_csv):
        df_feat = pd.read_csv(feat_csv)
        insert_statements.append(f"\n-- Data for fact_student_learning_analytics ({len(df_feat)} records)")
        for _, row in df_feat.head(500).iterrows():
            insert_statements.append(
                f"INSERT INTO fact_student_learning_analytics (id_student, code_module, code_presentation, gender, region, highest_education, age_band, studied_credits, final_result, total_clicks, active_days, avg_score, assessments_completed, risk_level) "
                f"VALUES ({row['id_student']}, '{row['code_module']}', '{row['code_presentation']}', '{row['gender']}', '{row['region']}', '{row['highest_education']}', '{row['age_band']}', {row['studied_credits']}, '{row['final_result']}', {row['total_clicks']}, {row['active_days']}, {row['avg_score']}, {row['assessments_completed']}, '{row['risk_level']}') "
                f"ON CONFLICT (code_module, code_presentation, id_student) DO NOTHING;"
            )

    # 4. Nạp Course Reviews
    rev_csv = os.path.join(PROCESSED_DIR, "course_reviews", "course_reviews_cleaned.csv")
    if os.path.exists(rev_csv):
        df_rev = pd.read_csv(rev_csv)
        insert_statements.append(f"\n-- Data for fact_course_reviews ({len(df_rev)} records)")
        for _, row in df_rev.head(500).iterrows():
            title = str(row["course_title"]).replace("'", "''")
            rev_txt = str(row["review_text"]).replace("'", "''")
            insert_statements.append(
                f"INSERT INTO fact_course_reviews (review_id, course_id, course_title, provider, category, rating, sentiment, language, review_text, review_date, learner_level, helpful_count) "
                f"VALUES ('{row['review_id']}', '{row['course_id']}', '{title}', '{row['provider']}', '{row['category']}', {row['rating']}, '{row['sentiment']}', '{row['language']}', '{rev_txt}', '{row['review_date']}', '{row['learner_level']}', {row['helpful_count']}) "
                f"ON CONFLICT (review_id) DO NOTHING;"
            )

    full_sql_content = schema_sql + "\n\n-- =============================================================================\n-- SEED DATA\n-- =============================================================================\n" + "\n".join(insert_statements)
    
    with open(seed_path, "w", encoding="utf-8") as f:
        f.write(full_sql_content)
        
    print(f"[OK] Đã tạo thành công {seed_path} ({len(insert_statements)} câu lệnh INSERT)")
    return seed_path


def try_connect_and_load_postgresql():
    """Kiểm tra và nạp trực tiếp vào PostgreSQL nếu dịch vụ đang khả dụng"""
    print(f"\n[*] Đang kiểm tra kết nối tới PostgreSQL ({DB_HOST}:{DB_PORT}, database='{DB_NAME}', user='{DB_USER}')...")
    try:
        import psycopg
        conn = psycopg.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=3
        )
        print("[+] Kết nối PostgreSQL thành công! Đang thực thi DDL Schema và nạp dữ liệu...")
        schema_file = os.path.join(SQL_DIR, "schema_postgresql.sql")
        with open(schema_file, "r", encoding="utf-8") as f:
            ddl_sql = f.read()
            
        with conn.cursor() as cur:
            cur.execute(ddl_sql)
            conn.commit()
            print("[+] Đã khởi tạo bảng và các Views trong PostgreSQL thành công.")
            
        # Nạp dữ liệu
        seed_file = generate_seed_sql_file()
        with open(seed_file, "r", encoding="utf-8") as f:
            seed_sql = f.read()
            
        with conn.cursor() as cur:
            cur.execute(seed_sql)
            conn.commit()
            print("[+] Nạp dữ liệu vào PostgreSQL thành công!")
            
        conn.close()
        return True
    except Exception as e:
        print(f"[-] Thông báo: Chưa thể kết nối trực tiếp PostgreSQL tại {DB_HOST}:{DB_PORT} ({e}).")
        print("    -> Đã tạo sẵn toàn bộ Schema DDL [schema_postgresql.sql] và bản nạp dữ liệu [seed_data_postgresql.sql].")
        print("    -> Bạn có thể khởi động PostgreSQL (qua Docker compose hoặc cài đặt cục bộ) và nạp chỉ bằng 1 lệnh:")
        print(f"       psql -h {DB_HOST} -p {DB_PORT} -U {DB_USER} -d {DB_NAME} -f {os.path.join(SQL_DIR, 'seed_data_postgresql.sql')}")
        return False


if __name__ == "__main__":
    generate_seed_sql_file()
    try_connect_and_load_postgresql()
