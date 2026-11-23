# Thư mục lưu trữ cấu hình Trực quan hóa và Giao diện người dùng

## Phân công phụ trách
- **Người phụ trách chính:** Nguyễn Thị Khanh

## Cấu trúc thư mục:
- `superset/`:
  - `dashboards_export/`: Các file JSON xuất 3 Dashboard (Cashflow, Spending Behavior, AI Forecast)
  - `datasources/`: Cấu hình kết nối DB và Virtual Datasets
  - `superset_config.py`: File cấu hình bảo mật, CSP cho Superset
- `portal/`: Giao diện Web hỗ trợ người dùng tải file sao kê và xem trạng thái
