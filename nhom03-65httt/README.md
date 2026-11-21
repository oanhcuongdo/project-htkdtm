# EduVision BI - Nhóm 03 (65HTTT)

Hệ thống phân tích trải nghiệm người học và cạnh tranh giữa các nền tảng E-learning.

## Cấu trúc mã nguồn

- `src/database/`: star schema, dữ liệu mẫu, migration (PostgreSQL)
- `src/etl/`: collector, transform, load, nhật ký chất lượng, workflow n8n
- `src/ml/`: gán nhãn, mô hình cảm xúc (M1), ABSA (M2), dự báo (M3), phát hiện bất thường
- `src/backend/`: API FastAPI
- `src/frontend/`: website React + TypeScript
- `src/bi/superset/`: dashboard Superset
- `config/platforms.yml`: danh sách nền tảng (thêm nền tảng = thêm một khối cấu hình)
- `data/` (`raw/`, `clean/`): dữ liệu trên máy từng thành viên, **không commit** (repo công khai)
- `models/`: trọng số mô hình, **không commit**; cách tải ở `models/README.md`
- `docs/`: tài liệu, gồm [dao_duc_phap_ly.md](docs/dao_duc_phap_ly.md) (điều khoản Google Play, App Store, YouTube)
- `docker-compose.yml`, `.env.example`: chạy hệ thống (chưa cấu hình)

## Quy tắc với repo công khai

- Không commit CSV thô/đã làm sạch, trọng số mô hình, khóa API hay file `.env` (đã có `.gitignore` của nhóm).
- Dữ liệu và trọng số chia sẻ qua kênh riêng của nhóm; xem `data/README.md` và `models/README.md`.

## Cài đặt và chạy

(Cập nhật khi có mã nguồn.)
