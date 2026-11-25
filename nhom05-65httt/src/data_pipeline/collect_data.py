"""
Data Collection Module
Nhiệm vụ: Thu thập và khởi tạo các tập dữ liệu gốc (Raw Data)
Phụ trách: Đinh Thị Lan Anh - 2351160500 (Nhóm 05)
Các nguồn dữ liệu:
1. VietJobs (Tuyển dụng CNTT & Phân tích dữ liệu tại Việt Nam)
2. OULAD (Open University Learning Analytics Dataset - Hành vi học tập)
3. Course Reviews (Đánh giá và chất lượng khóa học MOOC / Coursera / Udemy)
"""

import os
import random
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Định nghĩa các thư mục lưu trữ dữ liệu
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, "data", "processed")

os.makedirs(os.path.join(RAW_DATA_DIR, "vietjobs"), exist_ok=True)
os.makedirs(os.path.join(RAW_DATA_DIR, "oulad"), exist_ok=True)
os.makedirs(os.path.join(RAW_DATA_DIR, "course_reviews"), exist_ok=True)
os.makedirs(os.path.join(RAW_DATA_DIR, "wef"), exist_ok=True)
os.makedirs(os.path.join(PROCESSED_DATA_DIR, "vietjobs"), exist_ok=True)
os.makedirs(os.path.join(PROCESSED_DATA_DIR, "oulad"), exist_ok=True)
os.makedirs(os.path.join(PROCESSED_DATA_DIR, "course_reviews"), exist_ok=True)
os.makedirs(os.path.join(PROCESSED_DATA_DIR, "wef"), exist_ok=True)

np.random.seed(42)
random.seed(42)


def generate_raw_vietjobs_data(n_samples=2500):
    """
    Thu thập/tạo dữ liệu tuyển dụng VietJobs thô, mô phỏng từ các nguồn tuyển dụng thực tế
    tại Việt Nam (TopCV, VietnamWorks, ITviec).
    Bao gồm các bản ghi bị trùng lặp, nhiễu văn bản HTML, lỗi định dạng lương, khoảng trắng thừa.
    """
    titles = [
        "Data Analyst", "Senior Data Analyst", "Junior Data Analyst", "Data Engineer",
        "Senior Data Engineer", "Machine Learning Engineer", "AI Engineer", "BI Analyst",
        "Business Intelligence Developer", "Python Developer", "Backend Developer (Python/Django)",
        "Data Scientist", "Big Data Engineer", "AI/ML Researcher", "Database Administrator (DBA)",
        "DevOps Engineer", "Data Warehouse Specialist", "Chuyên viên Phân tích Dữ liệu",
        "Kỹ sư Trí tuệ Nhân tạo", "Lập trình viên Python"
    ]
    
    companies = [
        "FPT Software", "Viettel Telecom", "VNG Corporation", "VNPT IT", "MISA JSC",
        "One Mount Group", "Techcombank", "MB Bank", "VPBank", "Shopee Vietnam",
        "Tiki Corporation", "MoMo", "ZaloPay", "KMS Technology", "NashTech Vietnam",
        "CMC Global", "LG CNS Vietnam", "Samsung R&D Vietnam", "VietinBank IT", "Agribank"
    ]
    
    locations = [
        "Hà Nội", "Hanoi", "ha noi", "TP. Hồ Chí Minh", "TP HCM", "Ho Chi Minh",
        "hcm", "Đà Nẵng", "Da Nang", "Cần Thơ", "Hải Phòng", "Toàn quốc", "Remote (Làm việc từ xa)"
    ]
    
    skills_pool = [
        "Python", "SQL", "PostgreSQL", "Power BI", "Tableau", "Machine Learning",
        "Deep Learning", "NLP", "Pandas", "Scikit-Learn", "Docker", "Apache Spark",
        "Hadoop", "Airflow", "FastAPI", "Django", "Git", "Excel", "Data Modeling",
        "ETL Pipeline", "Data Warehouse", "AWS", "Azure", "GCP", "PyTorch", "TensorFlow"
    ]
    
    industries = [
        "Công nghệ thông tin / Phần mềm", "Tài chính / Ngân hàng / Fintech",
        "Thương mại điện tử / Bán lẻ", "Viễn thông", "Dịch vụ Dữ liệu & AI"
    ]
    
    records = []
    base_date = datetime(2026, 1, 1)
    
    for i in range(n_samples):
        title = random.choice(titles)
        # Giả lập lỗi khoảng trắng, chữ hoa chữ thường
        if random.random() < 0.15:
            title = f"  {title.lower()}  " if random.random() < 0.5 else f"***{title.upper()}***"
            
        company = random.choice(companies)
        loc = random.choice(locations)
        ind = random.choice(industries)
        
        # Chọn ngẫu nhiên 3 - 6 kỹ năng
        selected_skills = random.sample(skills_pool, random.randint(3, 6))
        # Giả lập kỹ năng viết hoa thường hỗn hợp
        if random.random() < 0.2:
            selected_skills = [s.lower() if random.random() < 0.5 else s.upper() for s in selected_skills]
        skills_str = ", ".join(selected_skills)
        if random.random() < 0.08:
            skills_str = " | ".join(selected_skills)  # Khác biệt phân cách
            
        # Giả lập mức lương (triệu VND)
        sal_type = random.random()
        if sal_type < 0.15:
            salary_raw = "Thỏa thuận"
        elif sal_type < 0.35:
            min_s = random.choice([10, 15, 20, 25])
            salary_raw = f"Từ {min_s} triệu"
        elif sal_type < 0.8:
            min_s = random.choice([12, 15, 20, 25, 30])
            max_s = min_s + random.choice([5, 10, 15, 20])
            salary_raw = f"{min_s} - {max_s} triệu VNĐ" if random.random() < 0.7 else f"{min_s*1000000} - {max_s*1000000} VND"
        else:
            salary_raw = f"{random.randint(1000, 2500)} USD"
            
        exp_years = random.choice(["Không yêu cầu", "Dưới 1 năm", "1 - 2 năm", "2 - 3 năm", "3 - 5 năm", "Trên 5 năm", None])
        edu = random.choice(["Đại học", "Cao đẳng", "Không yêu cầu", None])
        
        # Giả lập ngày đăng
        post_days = random.randint(0, 150)
        p_date = (base_date + timedelta(days=post_days)).strftime("%Y-%m-%d")
        if random.random() < 0.05:
            p_date = (base_date + timedelta(days=post_days)).strftime("%d/%m/%Y") # Lỗi định dạng ngày
            
        # Mô tả công việc có thể dính HTML tag hoặc khoảng trắng thừa
        desc = f"<p>Tuyển dụng vị trí <b>{title.strip()}</b> tại {company}. Yêu cầu thành thạo các kỹ năng: {skills_str}. Phúc lợi: Bảo hiểm đầy đủ, thưởng dự án, môi trường làm việc trẻ trung chuyên nghiệp.</p>"
        if random.random() < 0.2:
            desc += "<br/><div>Liên hệ ngay để nhận JD chi tiết!</div>"
            
        records.append({
            "job_id": f"VJ_{i+1:05d}",
            "title": title,
            "company": company,
            "location": loc,
            "industry": ind,
            "required_skills": skills_str,
            "salary_raw": salary_raw,
            "experience": exp_years,
            "education": edu,
            "job_description": desc,
            "posted_date": p_date,
            "source": random.choice(["TopCV", "VietnamWorks", "ITviec", "VietJobs"])
        })
        
    df = pd.DataFrame(records)
    
    # Tạo chủ động khoảng 150-200 bản ghi bị trùng lặp (duplicate records)
    # để kiểm thử khả năng phát hiện và loại bỏ trùng lặp đạt chuẩn < 1%
    dup_sample = df.sample(n=180, random_state=42).copy()
    # Một số bản ghi trùng lặp y hệt
    # Một số bản ghi trùng nhau về title, company, location nhưng job_id khác (cross-post)
    dup_sample["job_id"] = [f"VJ_DUP_{j:04d}" for j in range(len(dup_sample))]
    df_raw = pd.concat([df, dup_sample], ignore_index=True)
    
    # Xáo trộn thứ tự
    df_raw = df_raw.sample(frac=1, random_state=42).reset_index(drop=True)
    
    out_path = os.path.join(RAW_DATA_DIR, "vietjobs", "vietjobs_raw.csv")
    df_raw.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[VietJobs] Đã tạo raw dataset: {out_path} ({len(df_raw)} bản ghi, có ~{len(dup_sample)} bản ghi trùng lặp)")
    return df_raw


def generate_raw_oulad_data():
    """
    Thu thập/tạo dữ liệu hành vi học tập OULAD (Open University Learning Analytics Dataset)
    gồm các bảng cốt lõi:
    - studentInfo.csv
    - courses.csv
    - assessments.csv
    - studentAssessment.csv
    - studentVle.csv
    Bao gồm các bản ghi trùng lặp, giá trị thiếu (missing), điểm số ngoài miền hợp lệ.
    """
    oulad_dir = os.path.join(RAW_DATA_DIR, "oulad")
    
    # 1. Courses
    courses = [
        {"code_module": "AAA", "code_presentation": "2026J", "module_presentation_length": 268},
        {"code_module": "AAA", "code_presentation": "2026B", "module_presentation_length": 240},
        {"code_module": "BBB", "code_presentation": "2026J", "module_presentation_length": 268},
        {"code_module": "BBB", "code_presentation": "2026B", "module_presentation_length": 240},
        {"code_module": "CCC", "code_presentation": "2026J", "module_presentation_length": 269},
        {"code_module": "DDD", "code_presentation": "2026B", "module_presentation_length": 241},
        {"code_module": "EEE", "code_presentation": "2026J", "module_presentation_length": 268},
        {"code_module": "FFF", "code_presentation": "2026B", "module_presentation_length": 241},
    ]
    df_courses = pd.DataFrame(courses)
    df_courses.to_csv(os.path.join(oulad_dir, "courses.csv"), index=False)
    
    # 2. Student Info (3000 sinh viên)
    n_students = 3000
    regions = ["East Anglian", "Scotland", "North Western", "South East", "West Midlands", "Wales", "London"]
    edus = ["HE Qualification", "A Level or Equivalent", "Lower Than A Level", "Post Graduate Qualification", "No Formal quals"]
    results = ["Pass", "Distinction", "Fail", "Withdrawn"]
    
    student_records = []
    student_ids = [100000 + i for i in range(n_students)]
    
    for sid in student_ids:
        c = random.choice(courses)
        gender = random.choice(["M", "F", None if random.random() < 0.02 else "M"])
        res = random.choices(results, weights=[0.45, 0.15, 0.22, 0.18])[0]
        
        student_records.append({
            "code_module": c["code_module"],
            "code_presentation": c["code_presentation"],
            "id_student": sid,
            "gender": gender,
            "region": random.choice(regions),
            "highest_education": random.choice(edus),
            "imd_band": random.choice(["0-10%", "10-20", "20-30%", "30-40%", "40-50%", "50-60%", "60-70%", "70-80%", "80-90%", "90-100%"]),
            "age_band": random.choice(["0-35", "35-55", "55<="]),
            "num_of_prev_attempts": random.choice([0, 0, 0, 0, 1, 2]),
            "studied_credits": random.choice([60, 90, 120, 150, 180, 240]),
            "disability": random.choice(["N", "N", "N", "N", "Y"]),
            "final_result": res
        })
        
    df_students = pd.DataFrame(student_records)
    # Thêm 120 dòng trùng lặp vào studentInfo
    dup_students = df_students.sample(n=120, random_state=42).copy()
    df_students_raw = pd.concat([df_students, dup_students], ignore_index=True)
    df_students_raw.to_csv(os.path.join(oulad_dir, "studentInfo_raw.csv"), index=False)
    
    # 3. Assessments (40 bài đánh giá)
    assessments = []
    ass_id = 1750
    for c in courses:
        for a_idx in range(5):
            ass_id += 1
            assessments.append({
                "code_module": c["code_module"],
                "code_presentation": c["code_presentation"],
                "id_assessment": ass_id,
                "assessment_type": "TMA" if a_idx < 4 else "Exam",
                "date": 30 + a_idx * 40,
                "weight": 20.0 if a_idx < 4 else 100.0
            })
    df_ass = pd.DataFrame(assessments)
    df_ass.to_csv(os.path.join(oulad_dir, "assessments.csv"), index=False)
    
    # 4. Student Assessment (Kết quả thi của sinh viên)
    student_ass_records = []
    ass_dict = df_ass.set_index(["code_module", "code_presentation"])
    
    for s in student_records[:1500]: # lấy tập con để dữ liệu gọn nhẹ nhưng thực tế
        m = s["code_module"]
        p = s["code_presentation"]
        sid = s["id_student"]
        course_assessments = df_ass[(df_ass["code_module"] == m) & (df_ass["code_presentation"] == p)]
        
        for _, ass in course_assessments.iterrows():
            if s["final_result"] == "Withdrawn" and random.random() < 0.6:
                continue # sinh viên bỏ học không làm bài
            
            # Điểm số giả lập theo kết quả
            if s["final_result"] in ["Pass", "Distinction"]:
                score = min(100.0, max(40.0, np.random.normal(78, 12)))
            else:
                score = min(75.0, max(0.0, np.random.normal(38, 15)))
                
            # Tạo nhiễu điểm số lỗi (VD: điểm âm hoặc >100)
            if random.random() < 0.01:
                score = 150.0 if random.random() < 0.5 else -10.0
            elif random.random() < 0.03:
                score = np.nan # Missing score
                
            student_ass_records.append({
                "id_assessment": ass["id_assessment"],
                "id_student": sid,
                "date_submitted": int(ass["date"] + random.randint(-5, 10)),
                "is_banked": 0,
                "score": score
            })
            
    df_stu_ass = pd.DataFrame(student_ass_records)
    # Thêm trùng lặp trong studentAssessment
    dup_ass = df_stu_ass.sample(n=150, random_state=42).copy()
    df_stu_ass_raw = pd.concat([df_stu_ass, dup_ass], ignore_index=True)
    df_stu_ass_raw.to_csv(os.path.join(oulad_dir, "studentAssessment_raw.csv"), index=False)
    
    # 5. Student VLE Activity (Log tương tác hệ thống học tập)
    # Mỗi sinh viên có tổng hợp số lần click vào các hoạt động VLE
    vle_records = []
    activity_types = ["forumng", "oucontent", "quiz", "resource", "url", "subpage"]
    
    for s in student_records[:1200]:
        sid = s["id_student"]
        m = s["code_module"]
        p = s["code_presentation"]
        n_acts = random.randint(5, 15)
        for act_idx in range(n_acts):
            site_id = random.randint(5000, 5200)
            clicks = random.randint(1, 45) if s["final_result"] != "Withdrawn" else random.randint(0, 8)
            date_click = random.randint(-15, 240)
            vle_records.append({
                "code_module": m,
                "code_presentation": p,
                "id_student": sid,
                "id_site": site_id,
                "activity_type": random.choice(activity_types),
                "date": date_click,
                "sum_click": clicks
            })
            
    df_vle = pd.DataFrame(vle_records)
    # Thêm trùng lặp log
    dup_vle = df_vle.sample(n=350, random_state=42).copy()
    df_vle_raw = pd.concat([df_vle, dup_vle], ignore_index=True)
    df_vle_raw.to_csv(os.path.join(oulad_dir, "studentVle_raw.csv"), index=False)
    
    print(f"[OULAD] Đã tạo các tệp dữ liệu OULAD thô tại: {oulad_dir}")


def generate_raw_course_reviews(n_reviews=3000):
    """
    Thu thập/tạo dữ liệu đánh giá khóa học trực tuyến (Coursera / Udemy) phong phú
    Gồm: thông tin khóa học, đơn vị cung cấp, điểm rating, nhận xét phản hồi học viên (tiếng Việt & tiếng Anh).
    Bao gồm các bản ghi trùng lặp, spam review, định dạng rating sai lệch.
    """
    reviews_dir = os.path.join(RAW_DATA_DIR, "course_reviews")
    
    courses_info = [
        {"course_id": "CRS_001", "course_title": "Python for Everybody Specialization", "provider": "University of Michigan", "category": "Programming"},
        {"course_id": "CRS_002", "course_title": "Machine Learning Specialization", "provider": "DeepLearning.AI / Stanford", "category": "Data & AI"},
        {"course_id": "CRS_003", "course_title": "Google Data Analytics Professional Certificate", "provider": "Google", "category": "Data & AI"},
        {"course_id": "CRS_004", "course_title": "IBM Data Science Professional Certificate", "provider": "IBM", "category": "Data & AI"},
        {"course_id": "CRS_005", "course_title": "Deep Learning Specialization", "provider": "DeepLearning.AI", "category": "Data & AI"},
        {"course_id": "CRS_006", "course_title": "Business Intelligence & Data Analysis", "provider": "Wharton Online", "category": "Business Analytics"},
        {"course_id": "CRS_007", "course_title": "Natural Language Processing (NLP) in Practice", "provider": "DeepLearning.AI", "category": "Data & AI"},
        {"course_id": "CRS_008", "course_title": "Full-Stack Web Development with Django and React", "provider": "HKUST", "category": "Programming"},
        {"course_id": "CRS_009", "course_title": "Data Engineering Essentials", "provider": "IBM", "category": "Data Engineering"},
        {"course_id": "CRS_010", "course_title": "Power BI Desktop for Business Intelligence", "provider": "Microsoft Learn", "category": "Business Analytics"},
        {"course_id": "CRS_011", "course_title": "Cloud Computing on AWS & GCP", "provider": "AWS Training", "category": "Cloud Computing"},
        {"course_id": "CRS_012", "course_title": "Generative AI Fundamentals & Prompt Engineering", "provider": "DeepLearning.AI", "category": "Data & AI"}
    ]
    
    aspects_pos = [
        "Bài giảng rất chi tiết và dễ hiểu", "Giảng viên truyền cảm hứng tốt", 
        "Hệ thống bài tập thực hành rất sát với thực tế", "Project cuối khóa rất thực chiến",
        "Tài liệu slide và mã nguồn mẫu được chuẩn bị chu đáo", "Giải thích trực quan các thuật toán phức tạp",
        "Rất phù hợp để nâng cao kỹ năng nghề nghiệp", "Phần giải đáp thắc mắc hỗ trợ rất nhiệt tình"
    ]
    aspects_neu = [
        "Nội dung ở mức cơ bản, phù hợp với người bắt đầu", "Khóa học ổn, tốc độ giảng hơi nhanh ở tuần cuối",
        "Cần bổ sung thêm ví dụ tình huống thực tế tại doanh nghiệp", "Bài tập kiểm tra trắc nghiệm hơi ngắn",
        "Tài liệu tốt nhưng thời gian chờ chấm bài tự động hơi lâu", "Slide bài giảng tóm tắt chưa được đầy đủ"
    ]
    aspects_neg = [
        "Bài tập tự động chấm liên tục báo lỗi kết nối", "Nhiều thư viện trong code mẫu đã cũ không tương thích",
        "Nội dung quá nặng lý thuyết hàn lâm, thiếu ứng dụng", "Giảng viên giải thích lướt qua các công thức toán khó",
        "Diễn đàn hỗ trợ học viên phản hồi rất chậm trễ", "Chất lượng âm thanh trong một số video bài giảng bị rè",
        "Không đáng với học phí bỏ ra, thiếu bài tập lab thực hành"
    ]
    
    records = []
    base_date = datetime(2026, 1, 1)
    
    for i in range(n_reviews):
        c = random.choice(courses_info)
        prob = random.random()
        
        if prob < 0.65:
            rating = round(random.uniform(4.0, 5.0), 1)
            p1, p2 = random.sample(aspects_pos, 2)
            comment = f"{p1}. {p2}. Tôi rất khuyến khích các bạn tham gia khóa học {c['course_title']} này!"
        elif prob < 0.85:
            rating = round(random.uniform(2.8, 3.8), 1)
            n1 = random.choice(aspects_neu)
            comment = f"Đánh giá về {c['course_title']}: {n1}. Nhìn chung có thể cải thiện tốt hơn."
        else:
            rating = round(random.uniform(1.0, 2.5), 1)
            neg1, neg2 = random.sample(aspects_neg, 2)
            comment = f"Trải nghiệm chưa tốt với khóa học {c['course_title']}: {neg1}. {neg2}."
            
        # Thêm nhiễu ngẫu nhiên
        if random.random() < 0.12:
            comment = f"  <div><p>{comment}</p></div>  "
            
        if random.random() < 0.015:
            rating = 9.9 if random.random() < 0.5 else -2.0
        elif random.random() < 0.02:
            rating = np.nan
            
        r_date = (base_date + timedelta(days=random.randint(0, 150))).strftime("%Y-%m-%d")
        
        records.append({
            "review_id": f"REV_{i+1:06d}",
            "course_id": c["course_id"],
            "course_title": c["course_title"],
            "provider": c["provider"],
            "category": c["category"],
            "rating": rating,
            "review_text": comment,
            "review_date": r_date,
            "learner_level": random.choice(["Beginner", "Intermediate", "Advanced", None]),
            "helpful_count": random.randint(0, 60)
        })
        
    df_reviews = pd.DataFrame(records)
    # Thêm bản ghi trùng lặp có chủ đích
    dup_rev = df_reviews.sample(n=220, random_state=42).copy()
    dup_rev["review_id"] = [f"REV_DUP_{k:04d}" for k in range(len(dup_rev))]
    df_reviews_raw = pd.concat([df_reviews, dup_rev], ignore_index=True)
    df_reviews_raw = df_reviews_raw.sample(frac=1, random_state=42).reset_index(drop=True)
    
    out_file = os.path.join(reviews_dir, "course_reviews_raw.csv")
    df_reviews_raw.to_csv(out_file, index=False, encoding="utf-8-sig")
    print(f"[Course Reviews] Đã tạo raw dataset: {out_file} ({len(df_reviews_raw)} bản ghi, có ~{len(dup_rev)} bản ghi trùng lặp)")
    return df_reviews_raw


def generate_raw_wef_data():
    """
    Thu thập và mô phỏng dữ liệu Báo cáo xu hướng nghề nghiệp quốc tế (World Economic Forum - WEF)
    Nguồn: WEF The Future of Jobs Report.
    Bao gồm các nhóm:
    - Emerging Jobs (Nghề tăng trưởng nhanh)
    - Declining Jobs (Nghề có xu hướng suy giảm)
    - Core Skills (Kỹ năng cốt lõi toàn cầu)
    - Technology Adoption (Xu hướng áp dụng công nghệ)
    """
    wef_dir = os.path.join(RAW_DATA_DIR, "wef")
    
    items = [
        # Emerging Jobs
        {"cat": "Emerging Jobs", "name": "AI and Machine Learning Specialist", "growth": 38.5, "demand": "Very High", "sec": "Information Technology", "reskill": 9, "vn": "High", "desc": "Thiết kế, xây dựng và triển khai các thuật toán học máy, mô hình học sâu và ứng dụng AI thông minh."},
        {"cat": "Emerging Jobs", "name": "Data Analyst and Scientist", "growth": 34.2, "demand": "Very High", "sec": "Data & AI", "reskill": 6, "vn": "High", "desc": "Khai phá, phân tích dữ liệu lớn và trích xuất thông tin chiến lược hỗ trợ ra quyết định kinh doanh."},
        {"cat": "Emerging Jobs", "name": "Big Data Specialist", "growth": 30.1, "demand": "High", "sec": "Data Engineering", "reskill": 6, "vn": "High", "desc": "Xây dựng hạ tầng dữ liệu phân tán, đường ống ETL và Data Lake / Data Warehouse."},
        {"cat": "Emerging Jobs", "name": "Information Security Analyst (Cybersecurity)", "growth": 31.0, "demand": "Very High", "sec": "Security & Defense", "reskill": 8, "vn": "High", "desc": "Bảo vệ hệ thống hạ tầng thông tin, an ninh mạng và an toàn dữ liệu doanh nghiệp."},
        {"cat": "Emerging Jobs", "name": "Fintech Engineer", "growth": 28.5, "demand": "High", "sec": "Financial Services", "reskill": 6, "vn": "High", "desc": "Phát triển các giải pháp công nghệ tài chính, thanh toán số và ngân hàng điện tử."},
        {"cat": "Emerging Jobs", "name": "DevOps & Cloud Architect", "growth": 27.4, "demand": "High", "sec": "Cloud & Infrastructure", "reskill": 6, "vn": "High", "desc": "Tự động hóa triển khai phần mềm, tích hợp liên tục CI/CD và quản trị đám mây AWS/GCP/Azure."},
        {"cat": "Emerging Jobs", "name": "Business Intelligence Specialist", "growth": 25.8, "demand": "High", "sec": "Enterprise Analytics", "reskill": 5, "vn": "High", "desc": "Thiết kế dashboard trực quan hóa chỉ số KPI kinh doanh và xây dựng mô hình Star Schema."},
        {"cat": "Emerging Jobs", "name": "Robotics Engineer", "growth": 22.0, "demand": "Moderate", "sec": "Manufacturing & Automation", "reskill": 12, "vn": "Medium", "desc": "Nghiên cứu chế tạo robot tự động hóa dây chuyền sản xuất công nghiệp."},
        {"cat": "Emerging Jobs", "name": "Digital Transformation Specialist", "growth": 26.3, "demand": "High", "sec": "Management Consulting", "reskill": 6, "vn": "High", "desc": "Tư vấn và thúc đẩy quá trình chuyển đổi số quy trình kinh doanh trong doanh nghiệp."},
        {"cat": "Emerging Jobs", "name": "Renewable Energy Engineer", "growth": 29.5, "demand": "High", "sec": "Energy & Sustainability", "reskill": 10, "vn": "Emerging", "desc": "Nghiên cứu và phát triển nguồn năng lượng tái tạo, điện gió và điện mặt trời."},
        
        # Declining Jobs
        {"cat": "Declining Jobs", "name": "Data Entry Clerk", "growth": -32.0, "demand": "Declining", "sec": "Administrative Support", "reskill": 3, "vn": "High", "desc": "Nhập liệu thủ công bị thay thế bởi các hệ thống OCR, RPA và AI tự động trích xuất thông tin."},
        {"cat": "Declining Jobs", "name": "Administrative and Executive Secretary", "growth": -26.5, "demand": "Declining", "sec": "Office Operations", "reskill": 4, "vn": "High", "desc": "Công việc thư ký hành chính truyền thống chuyển dần sang trợ lý ảo AI và phần mềm tự động."},
        {"cat": "Declining Jobs", "name": "Accounting and Bookkeeping Clerk", "growth": -28.0, "demand": "Declining", "sec": "Financial Operations", "reskill": 5, "vn": "High", "desc": "Kế toán ghi sổ sơ cấp được tự động hóa bằng phần mềm kế toán số và hóa đơn điện tử."},
        {"cat": "Declining Jobs", "name": "Bank Teller and Related Clerks", "growth": -29.0, "demand": "Declining", "sec": "Retail Banking", "reskill": 4, "vn": "High", "desc": "Giao dịch viên ngân hàng giảm mạnh do sự phổ biến của Mobile Banking và Digital Onboarding."},
        {"cat": "Declining Jobs", "name": "Postal Service Clerk", "growth": -30.5, "demand": "Declining", "sec": "Logistics & Post", "reskill": 3, "vn": "Medium", "desc": "Thủ tục bưu chính truyền thống giảm do thư tín điện tử và hệ thống kho vận thông minh."},

        # Core Skills
        {"cat": "Core Skills", "name": "Analytical Thinking & Problem Solving", "growth": 45.0, "demand": "Very High", "sec": "Cross-Industry", "reskill": 4, "vn": "High", "desc": "Khả năng tư duy logic, phân tích dữ kiện và giải quyết vấn đề phức tạp dựa trên bằng chứng số liệu."},
        {"cat": "Core Skills", "name": "AI, Machine Learning & Big Data Literacy", "growth": 52.0, "demand": "Very High", "sec": "Technology", "reskill": 6, "vn": "High", "desc": "Hiểu biết và kỹ năng ứng dụng AI, mô hình ngôn ngữ lớn và khai thác dữ liệu trong công việc."},
        {"cat": "Core Skills", "name": "Creative Thinking & Innovation", "growth": 40.5, "demand": "Very High", "sec": "Cross-Industry", "reskill": 5, "vn": "High", "desc": "Tư duy sáng tạo, khả năng đề xuất ý tưởng đột phá và giải pháp mới cho doanh nghiệp."},
        {"cat": "Core Skills", "name": "Cybersecurity and Systems Thinking", "growth": 36.0, "demand": "High", "sec": "Technology & Governance", "reskill": 6, "vn": "High", "desc": "Tư duy hệ thống kiến trúc và nhận thức bảo đảm an toàn dữ liệu số."},
        {"cat": "Core Skills", "name": "Resilience, Flexibility and Agility", "growth": 35.0, "demand": "High", "sec": "Personal Competency", "reskill": 3, "vn": "High", "desc": "Khả năng thích ứng linh hoạt với sự thay đổi của công nghệ và môi trường làm việc mới."},
        
        # Technology Adoption
        {"cat": "Technology Adoption", "name": "Cloud Computing Platforms", "growth": 86.0, "demand": "Very High", "sec": "IT Infrastructure", "reskill": 6, "vn": "High", "desc": "86% doanh nghiệp dự kiến mở rộng hạ tầng đám mây trong giai đoạn 2024-2027."},
        {"cat": "Technology Adoption", "name": "Big Data Analytics & BI Platforms", "growth": 82.0, "demand": "Very High", "sec": "Enterprise Analytics", "reskill": 5, "vn": "High", "desc": "82% doanh nghiệp đầu tư nền tảng phân tích dữ liệu lớn và báo cáo thông minh."},
        {"cat": "Technology Adoption", "name": "Generative AI & LLMs", "growth": 75.0, "demand": "Very High", "sec": "Artificial Intelligence", "reskill": 4, "vn": "High", "desc": "75% doanh nghiệp tích cực nghiên cứu và ứng dụng Generative AI để tăng năng suất lao động."},
        {"cat": "Technology Adoption", "name": "Internet of Things (IoT) & Connected Devices", "growth": 68.0, "demand": "High", "sec": "Smart Devices & Hardware", "reskill": 6, "vn": "High", "desc": "Ứng dụng cảm biến thông minh và mạng kết nối vạn vật trong theo dõi vận hành."},
        {"cat": "Technology Adoption", "name": "Robotics & Autonomous Automation", "growth": 55.0, "demand": "Moderate", "sec": "Automation", "reskill": 8, "vn": "Medium", "desc": "Tự động hóa dây chuyền sản xuất và kho bãi thông minh."}
    ]
    
    records = []
    for i, it in enumerate(items):
        name = it["name"]
        # Thêm nhiễu khoảng trắng hoặc ký tự
        if random.random() < 0.2:
            name = f"  {name}  "
            
        desc = it["desc"]
        if random.random() < 0.15:
            desc = f"<p><b>{it['name']}</b>: {desc}</p>"
            
        records.append({
            "trend_id": f"WEF_{i+1:03d}",
            "report_source": "World Economic Forum - Future of Jobs Report",
            "category": it["cat"],
            "item_name": name,
            "growth_rate_pct": it["growth"],
            "demand_level": it["demand"],
            "impact_sector": it["sec"],
            "reskilling_duration_months": it["reskill"],
            "relevance_to_vietnam": it["vn"],
            "description": desc
        })
        
    df = pd.DataFrame(records)
    # Thêm bản ghi trùng lặp
    dup = df.sample(n=6, random_state=42).copy()
    dup["trend_id"] = [f"WEF_DUP_{j:02d}" for j in range(len(dup))]
    df_raw = pd.concat([df, dup], ignore_index=True)
    df_raw = df_raw.sample(frac=1, random_state=42).reset_index(drop=True)
    
    out_path = os.path.join(wef_dir, "wef_trends_raw.csv")
    df_raw.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[WEF Trends] Đã tạo raw dataset: {out_path} ({len(df_raw)} bản ghi, có ~{len(dup)} bản ghi trùng lặp)")
    return df_raw


if __name__ == "__main__":
    print("=== BẮT ĐẦU THU THẬP & KHỞI TẠO TẬP DỮ LIỆU GỐC (RAW DATA) ===")
    generate_raw_vietjobs_data(n_samples=2500)
    generate_raw_oulad_data()
    generate_raw_course_reviews(n_reviews=3000)
    generate_raw_wef_data()
    print("=== THU THẬP HOÀN TẤT VÀ LƯU VÀO data/raw/ ===")
