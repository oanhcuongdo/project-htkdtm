# Thư mục lưu trữ mã nguồn cơ sở dữ liệu và kho dữ liệu (PostgreSQL)

## Phân công phụ trách
- **Người phụ trách chính:** Thiệu Quang Gia Bảo (Nhóm trưởng)

## Cấu trúc thư mục:
- `schemas/`: Chứa các script SQL định nghĩa Staging, Fact, Dimension, Views
- `migrations/`: Quản lý nâng cấp phiên bản schema
- `seeds/`: Dữ liệu ban đầu (danh mục chuẩn, đơn vị thụ hưởng)
- `mock_data/`: Script sinh dữ liệu giả lập 500 - 1000 giao dịch để kiểm thử
