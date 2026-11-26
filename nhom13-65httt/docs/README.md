# TÀI LIỆU HƯỚNG DẪN VÀ ĐẶC TẢ DỰ ÁN (DOCS INDEX)

Kho tài liệu này chứa toàn bộ các đặc tả kỹ thuật, kiến trúc hệ thống, thiết kế cơ sở dữ liệu và kế hoạch triển khai chi tiết cho đề tài:
**"Hệ thống Quản lý Tài chính Cá nhân Thông minh tích hợp Thu thập Dữ liệu Tự động, AI phân loại và dự báo, trực quan hóa bằng Apache Superset"** (Nhóm 13 - Lớp 65HTTT).

---

## Danh Mục Các File Tài Liệu

| Thứ tự | Tên tệp tin | Tóm tắt nội dung chính |
| :---: | :--- | :--- |
| **01** | [01_tong_quan_du_an.md](file:///d:/HTKDTM/project-htkdtm/nhom13-65httt/docs/01_tong_quan_du_an.md) | - Bối cảnh thực tế và vấn đề "Mù mờ dòng tiền vi mô".<br>- 5 câu hỏi nghiệp vụ cốt lõi.<br>- Đánh giá phê phán các giải pháp hiện nay.<br>- Mục tiêu tổng quát và bộ tiêu chí KPIs chi tiết. |
| **02** | [02_kien_truc_he_thong.md](file:///d:/HTKDTM/project-htkdtm/nhom13-65httt/docs/02_kien_truc_he_thong.md) | - Sơ đồ kiến trúc 5 tầng (Ingestion, ETL, DW, AI, BI).<br>- Tầng thu thập không xâm phạm (Email, CSV/PDF, Telegram Bot).<br>- Pipeline Staging $\rightarrow$ Clean $\rightarrow$ Deduplication $\rightarrow$ Star Schema.<br>- Tầng AI (NLP, Anomaly, Prophet) và Tầng BI Superset. |
| **03** | [03_cau_truc_thu_muc.md](file:///d:/HTKDTM/project-htkdtm/nhom13-65httt/docs/03_cau_truc_thu_muc.md) | - Quy định cấu trúc thư mục toàn dự án.<br>- **Quy định thư mục `src/` chứa trọn vẹn cả `backend/`, `frontend/`, `database/`**.<br>- Chi tiết từng file, quy chuẩn đặt tên và Git Commit Conventions. |
| **04** | [04_thiet_ke_co_so_du_lieu.md](file:///d:/HTKDTM/project-htkdtm/nhom13-65httt/docs/04_thiet_ke_co_so_du_lieu.md) | - Mô hình ERD Star Schema cho Data Warehouse PostgreSQL.<br>- Chi tiết bảng `fact_transactions` và các bảng `dim_*`.<br>- Bảng kiểm soát khử trùng `log_dedup` và bảng dự báo AI.<br>- Các SQL Views tầng ngữ nghĩa (Semantic Layer) cho Superset. |
| **05** | [05_ke_hoach_trien_khai.md](file:///d:/HTKDTM/project-htkdtm/nhom13-65httt/docs/05_ke_hoach_trien_khai.md) | - Lộ trình 8 tuần chia theo 5 giai đoạn chi tiết.<br>- Phân công nhiệm vụ chi tiết cho 5 thành viên trong nhóm.<br>- Ma trận phân trách nhiệm RACI.<br>- Kế hoạch quản lý rủi ro và phương án ứng phó. |
| **06** | [06_huong_dan_chuan_bi_va_van_hanh.md](file:///d:/HTKDTM/project-htkdtm/nhom13-65httt/docs/06_huong_dan_chuan_bi_va_van_hanh.md) | - Hướng dẫn thiết lập môi trường Docker Compose.<br>- Khởi tạo database và nạp dữ liệu mẫu mock data.<br>- Cấu hình Apache Superset và import 3 Dashboards.<br>- Kịch bản kiểm thử tích hợp (End-to-End). |
| **07** | [07_bao_cao_danh_gia_mo_hinh_ai.md](file:///d:/HTKDTM/project-htkdtm/nhom13-65httt/docs/07_bao_cao_danh_gia_mo_hinh_ai.md) | - Báo cáo đánh giá độ chính xác mô hình NLP phân loại tiếng Việt (F1, Confusion Matrix).<br>- Kết quả phát hiện giao dịch bất thường (Isolation Forest + Z-Score).<br>- Kiểm thử ngược dự báo dòng tiền 30 ngày (MAPE) & phân tích Burn-rate. |
| **08** | [08_ke_hoach_nang_cap_react_auth_gemini.md](file:///d:/HTKDTM/project-htkdtm/nhom13-65httt/docs/08_ke_hoach_nang_cap_react_auth_gemini.md) | - Kế hoạch nâng cấp React Portal (Docker `:3000`), Đăng ký/Đăng nhập JWT đa người dùng.<br>- Trung tâm tùy chọn nguồn lấy dữ liệu ngân hàng cá nhân (Upload, OCR, IMAP, Telegram).<br>- Kiến trúc Trợ lý Chat AI Gemini (Function Calling trên dữ liệu thật PostgreSQL). |
| **09** | [09_thiet_ke_giao_dien_landing_page_brand_estonia.md](file:///d:/HTKDTM/project-htkdtm/nhom13-65httt/docs/09_thiet_ke_giao_dien_landing_page_brand_estonia.md) | - Phân tích hệ thống thiết kế Brand Estonia (`brand.estonia.ee` / DDS 2.0): Estonian Blue, Boulders, Aino Typography, Rändrahnud & Broken Line.<br>- Đặc tả chi tiết 8 phân khu Landing Page, luồng chuyển tiếp sang Đăng nhập/Đăng ký & đồng bộ Design Tokens cho React/Tailwind. |

---

## Hướng Dẫn Dành Cho Thành Viên Nhóm

1. **Trước khi bắt tay vào code:** Đọc kỹ [03_cau_truc_thu_muc.md](file:///d:/HTKDTM/project-htkdtm/nhom13-65httt/docs/03_cau_truc_thu_muc.md) và [04_thiet_ke_co_so_du_lieu.md](file:///d:/HTKDTM/project-htkdtm/nhom13-65httt/docs/04_thiet_ke_co_so_du_lieu.md) để thống nhất tên các trường dữ liệu và vị trí đặt code trong `src/`.
2. **Theo dõi tiến độ:** Kiểm tra [05_ke_hoach_trien_khai.md](file:///d:/HTKDTM/project-htkdtm/nhom13-65httt/docs/05_ke_hoach_trien_khai.md) vào đầu mỗi tuần để bám sát sản phẩm bàn giao cam kết.
3. **Cài đặt chạy thử nghiệm:** Làm theo các bước tại [06_huong_dan_chuan_bi_va_van_hanh.md](file:///d:/HTKDTM/project-htkdtm/nhom13-65httt/docs/06_huong_dan_chuan_bi_va_van_hanh.md) để dựng môi trường làm việc trên máy cá nhân.
