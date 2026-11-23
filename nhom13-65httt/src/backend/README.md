# Thư mục lưu trữ mã nguồn Backend, ETL Pipeline và Dịch vụ AI

## Phân công phụ trách
- **Thu thập Email & Sao kê:** Trần Minh Giang
- **Telegram Bot OCR & Khử trùng lặp:** Nguyễn Thu Giang
- **Mô hình AI (NLP, Anomaly, Prophet) & API:** Trương Quốc Thái

## Cấu trúc thư mục:
- `ingestion/`: Các module thu thập dữ liệu (Email, CSV/PDF, Telegram Bot)
- `etl_pipeline/`: Làm sạch, chuẩn hóa, khử trùng lặp và nạp kho dữ liệu
- `ai_service/`: Mô hình phân loại tiếng Việt, phát hiện bất thường, dự báo chuỗi thời gian
- `api/`: RESTful API phát triển bằng FastAPI
- `scheduler/`: Kịch bản lập lịch chạy batch tự động
- `notification/`: Gửi cảnh báo Telegram và báo cáo định kỳ
