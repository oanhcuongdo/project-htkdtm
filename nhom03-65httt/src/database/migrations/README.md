# Migration cơ sở dữ liệu (Alembic)

Kho dữ liệu của nhóm viết bằng **SQL thuần** trong `../schema/` (nguồn chuẩn do người phụ trách kho quản lý).
Mỗi migration Alembic chỉ **chạy một tệp SQL tương ứng**, nhờ đó mọi máy có cùng trạng thái CSDL và biết đang ở phiên bản nào.

| Phiên bản | Tệp SQL | Nội dung |
|---|---|---|
| `0001` | `schema/01_schema_core.sql` | schema `raw`, `clean`, `dw`; dim_time, dim_platform, dim_source, fact_review |
| `0002` | `schema/02_schema_dims_facts.sql` | các dim và fact còn lại (đủ 6 fact, 7 dim) |
| `0003` | `schema/03_schema_news.sql` | `clean.news_article`: bài báo gốc (tiêu đề, tên báo, đường dẫn, ngày đăng; không toàn văn). Migration kế tiếp dùng `0004` |

## Chạy

Cách chính là Docker: dịch vụ `migrate` trong `docker-compose.yml` tự chạy `alembic upgrade head` trước khi API khởi động.

```bash
docker compose run --rm migrate alembic current            # phiên bản hiện tại
docker compose run --rm migrate alembic history            # danh sách phiên bản
docker compose run --rm migrate alembic upgrade head       # lên phiên bản mới nhất
docker compose run --rm migrate alembic downgrade 0001     # lùi một bước (CHỈ máy phát triển, có thể xóa dữ liệu)
```

Chạy không qua Docker (cần Python 3.10 trở lên và một PostgreSQL đang chạy):

```bash
cd src/database
pip install -r requirements.txt
export DATABASE_URL=postgresql://eduvision:<mat-khau>@localhost:5432/eduvision   # Windows PowerShell: $env:DATABASE_URL="..."
alembic upgrade head
```

## Thêm một thay đổi schema

1. **Không sửa** tệp SQL hay migration đã merge. Thêm tệp SQL mới có số kế tiếp, ví dụ `schema/03_alter_fact_review.sql` (dùng `ADD COLUMN IF NOT EXISTS`, `IF NOT EXISTS`... để chạy lại an toàn).
2. Thêm `migrations/versions/0003_<ten>.py` theo mẫu `0002_dims_facts.py`: `down_revision = "0002"`, `upgrade()` gọi `run_sql_file("03_alter_fact_review.sql")`, `downgrade()` ghi câu lệnh hoàn tác.
3. Chạy thử hai lần: lần hai không được tạo gì mới và không lỗi; thử cả `downgrade` rồi `upgrade head`.
4. Báo người phụ trách kho dữ liệu duyệt trong Pull Request.

## Lưu ý
- Biến `DATABASE_URL` được đọc từ môi trường (không ghi vào mã). Không commit `.env`.
- `downgrade` xóa bảng/schema: không chạy trên dữ liệu thật.
- Chế độ `--sql` (xuất ra tệp) không được hỗ trợ vì migration chạy tệp SQL trực tiếp.
