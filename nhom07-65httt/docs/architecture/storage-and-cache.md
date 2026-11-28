# Kiến Trúc Lưu Trữ, Bộ Nhớ Đệm & Bền Vững Dữ Liệu

> Phiên bản: 2.0 | Cập nhật lần cuối: 14/09/2026 | Phụ trách: Platform Team | Trạng thái: Chính thức (Active)

---

## 1. Tổng Quan Các Tầng Lưu Trữ

**Multimodal AI Learning Hub** áp dụng kiến trúc lưu trữ phân tầng nhằm đáp ứng đặc thù của từng loại tải công việc: dữ liệu tệp nhị phân lớn (blob), trạng thái giao dịch quan hệ, chỉ mục vector ngữ nghĩa và bộ nhớ đệm / hàng đợi tạm thời.

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│                       Sơ Đồ Lưu Trữ & Bộ Nhớ Đệm Hệ Thống                       │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   [ Tệp / Video / Audio ]      [ Dữ Liệu Quan Hệ ]        [ Vector Ngữ Nghĩa ]   │
│            │                            │                           │            │
│            ▼                            ▼                           ▼            │
│    ┌───────────────┐           ┌──────────────────┐        ┌────────────────┐    │
│    │  MinIO S3     │           │ PostgreSQL 14    │        │  Qdrant 6333   │    │
│    │  (Cổng 9000)  │           │ (Docker / Neon)  │        │  (v1.12.5)     │    │
│    └───────────────┘           └──────────────────┘        └────────────────┘    │
│     Blob / Media                  ACID / Metadata              Embeddings        │
│                                                                                  │
│   ────────────────────────────────────────────────────────────────────────────   │
│   Tầng Bộ Nhớ Đệm & Hàng Đợi Bất Đồng Bộ:                                        │
│   ┌──────────────────────────────────────────────────────────────────────────┐   │
│   │ Redis 7 (Cổng 6379)                                                      │   │
│   │ ├── DB 0: Bộ nhớ đệm ứng dụng (TTL: 60s – 3600s) & Kết quả Celery        │   │
│   │ └── DB 1: Celery Message Broker (xử lý tài liệu, media, tác vụ AI)       │   │
│   └──────────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

| Công nghệ | Vai trò | Giao thức / Cổng | Thời gian lưu trữ | Đảm bảo bền vững |
|---|---|---|---|---|
| **MinIO** | Lưu trữ đối tượng (PDF, DOCX, video, audio, ảnh) | S3 API (`9000`) / Console (`9001`) | Vĩnh viễn tới khi xóa | Volume đĩa cục bộ (`minio_data`) hoặc lưu trữ S3 |
| **PostgreSQL 14** | Dữ liệu quan hệ, người dùng, khóa học, nhật ký | AsyncPG / Cổng `5432` | Bền vững giao dịch | Volume `pgdata` (WAL + sao lưu) |
| **Qdrant v1.12.5** | Vector ngữ nghĩa của các đoạn văn bản tài liệu | HTTP/gRPC / Cổng `6333` | Theo vòng đời tài liệu | Volume `qdrant_storage` + chỉ mục HNSW |
| **Redis 7 (DB 0)** | Đọc nhanh qua cache & giới hạn tần suất (rate limit) | RESP / Cổng `6379` | Tạm thời (theo TTL) | Trên RAM (hỗ trợ AOF/RDB) |
| **Redis 7 (DB 1)** | Hàng đợi tác vụ bất đồng bộ cho Celery | RESP / Cổng `6379` | Trong lúc xử lý tác vụ | Trên RAM với `--appendonly yes` (`redis_data`) |

---

## 2. Lưu Trữ Đối Tượng: MinIO (Tương Thích Chuẩn S3)

MinIO đảm nhiệm lưu trữ phi cấu trúc cho tệp người dùng tải lên, video bài giảng và các tài nguyên sinh ra.

### 2.1. Tổ Chức Các Bucket

| Tên Bucket | Chính sách truy cập | Nội dung lưu trữ | Ghi chú |
|---|---|---|---|
| `documents-bucket` | Riêng tư (Private) | Tài liệu tải lên (PDF, DOCX, TXT, ảnh) | Bucket mặc định (`MINIO_BUCKET_NAME`) |
| `media-bucket` | Riêng tư (Private) | Tệp âm thanh và video bài giảng (MP3, MP4, WebM) | Truyền phát qua presigned URL / range stream |
| `avatars-bucket` | Công khai đọc | Ảnh đại diện tài khoản người dùng | — |
| `thumbnails-bucket` | Công khai đọc | Ảnh thu nhỏ xem trước của khóa học / tài liệu | — |

### 2.2. Cấu Trúc Đường Dẫn & Vòng Đời Đối Tượng

Các đối tượng tuân theo quy ước đường dẫn phân tách theo người dùng / khóa học:

```text
documents-bucket/
└── users/{user_id}/documents/{document_id}/{filename}

media-bucket/
└── courses/{course_id}/lessons/{lesson_id}/{filename}

thumbnails-bucket/
└── documents/{document_id}/cover.jpg
```

**Luồng nạp và truy cập tệp:**
1. **Tải lên:** Backend API kiểm tra hạn mức dung lượng còn lại của người dùng (`quotas.storage_limit_mb`) rồi đẩy tệp lên MinIO qua `minio` / S3 client.
2. **Worker đọc tệp:** Celery Worker tải trực tiếp dữ liệu nhị phân từ MinIO qua mạng nội bộ để trích xuất văn bản / OCR / tách âm thanh.
3. **Xem trước / Tải về:** Backend API cấp phát **presigned URL ngắn hạn** hoặc stream có kiểm tra quyền (hỗ trợ HTTP Range `206` cho PDF/video), bảo vệ các bucket riêng tư khỏi truy cập trái phép.

### 2.3. Cấu Hình Bảo Mật Môi Trường Production

```env
MINIO_ENDPOINT=minio.internal:9000
MINIO_ACCESS_KEY=<khóa-truy-cập-mạnh>
MINIO_SECRET_KEY=<khóa-bí-mật-mạnh>
MINIO_BUCKET_NAME=documents-bucket
MINIO_SECURE=true
```
*Lưu ý: Ở môi trường production (`DEBUG=false`), `src/backend/app/core/config.py` bắt buộc `MINIO_SECURE=true` và chặn khởi động nếu còn dùng thông tin mặc định (`minioadmin` / `minioadmin123`).*

---

## 3. Bộ Nhớ Đệm & Hàng Đợi: Redis 7

Redis 7 phục vụ hai vai trò tách biệt theo số thứ tự database để tránh xung đột khóa.

### 3.1. Bộ Nhớ Đệm Ứng Dụng (Redis DB 0)

Database 0 giúp tăng tốc các endpoint đọc dữ liệu thường xuyên (`src/backend/app/core/config.py`):

| Nhóm dữ liệu cache | Mẫu khóa Redis | Thời gian sống (TTL) | Sự kiện xóa cache (Invalidation) |
|---|---|---|---|
| **Metadata tài liệu** | `cache:doc:{document_id}` | `60s` (`REDIS_CACHE_TTL_DOCS`) | Khi cập nhật trạng thái hoặc xóa tài liệu |
| **Ghi danh khóa học** | `cache:enrollment:{user_id}:{course_id}` | `60s` (`REDIS_CACHE_TTL_ENROLLMENTS`) | Khi mua / xác nhận ghi danh khóa học |
| **Danh mục khóa học** | `cache:courses:list:{page}:{filter}` | `120s` (`REDIS_CACHE_TTL_COURSES`) | Khi giảng viên xuất bản hoặc sửa khóa học |
| **Nội dung bài học** | `cache:lesson:{lesson_id}` | `120s` (`REDIS_CACHE_TTL_LESSONS`) | Khi giảng viên cập nhật nội dung bài học |
| **Thông báo khóa học** | `cache:announcements:{course_id}` | `120s` (`REDIS_CACHE_TTL_ANNOUNCEMENTS`) | Khi giảng viên đăng / sửa thông báo mới |
| **Hồ sơ người dùng** | `cache:user:profile:{user_id}` | `300s` (`REDIS_CACHE_TTL_PROFILE`) | Khi người dùng cập nhật hồ sơ / ảnh đại diện |
| **Danh sách danh mục** | `cache:categories:all` | `600s` (`REDIS_CACHE_TTL_CATEGORIES`) | Khi Admin thêm / sửa / xóa danh mục |
| **Bộ đề trắc nghiệm** | `cache:quiz:{quiz_id}` | `3600s` (`REDIS_CACHE_TTL_QUIZ`) | Khi sinh lại hoặc xóa bộ quiz |

### 3.2. Hàng Đợi Tác Vụ Celery (Redis DB 1)

Database 1 vận hành các hàng đợi xử lý nền với mức song song được kiểm soát chặt chẽ:

```env
CELERY_BROKER_URL=redis://redis:6379/1
REDIS_URL=redis://redis:6379/0
```

| Nhóm tác vụ | Thời gian chạy điển hình | Giới hạn tiến trình song song |
|---|---|---|
| **Xử lý tài liệu** (`document_processing`, `lesson_content`, `course_file`) | 10s – 60s | `CELERY_CONCURRENCY=2` |
| **Xử lý đa phương tiện** (Video FFmpeg, Whisper, OCR Tesseract) | 30s – 300s | `CELERY_CONCURRENCY=2` |
| **Tác vụ AI nền** (`quiz`, `course_quiz`, `essay`, `flashcards`) | 15s – 90s | `CELERY_CONCURRENCY=2` |

**Lý do đặt mặc định `CELERY_CONCURRENCY=2`:**
- Việc trích xuất PDF (PyMuPDF, `pdfplumber`), chuyển mã âm thanh/video (FFmpeg) và chạy mô hình nhúng tiêu tốn nhiều CPU và RAM.
- Giới hạn 2 tiến trình worker song song giúp phòng tránh lỗi tràn bộ nhớ (OOM) trong container và không làm cạn kiệt pool kết nối PostgreSQL. Thêm vào đó, `worker_max_tasks_per_child=20` tự tái chế tiến trình con để giải phóng bộ nhớ PyTorch.

```python
# src/worker/celery_app.py
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,          # Giới hạn cứng: ngắt tác vụ sau 10 phút
    task_soft_time_limit=540,     # Giới hạn mềm: báo ngoại lệ sau 9 phút
    worker_prefetch_multiplier=1, # Mỗi tiến trình con chỉ nhận 1 tác vụ mỗi lần
    worker_max_tasks_per_child=20,
    task_acks_late=True,
    worker_concurrency=int(os.getenv("CELERY_CONCURRENCY", "2")),
)
```

---

## 4. Cơ Sở Dữ Liệu Vector: Qdrant

Qdrant lưu trữ các vector ngữ nghĩa (embeddings) phục vụ truy xuất RAG trên toàn bộ tài liệu cá nhân và học liệu khóa học.

### 4.1. Đặc Tả Collection

- **Tên Collection:** `document_chunks`
- **Số chiều vector:** `384` (tạo bởi mô hình `sentence-transformers/all-MiniLM-L6-v2`)
- **Hàm đo khoảng cách:** `Cosine`
- **Chỉ mục tìm kiếm:** HNSW

### 4.2. Tối Ưu Lưu Trữ & Tìm Kiếm

1. **Lưu Payload trên đĩa (`on_disk`):** Văn bản đoạn trích và metadata được đọc qua memory-mapped files (mmap) để tiết kiệm RAM.
2. **Payload Indexing:** Đánh chỉ mục trực tiếp trên các trường hay lọc (`document_id`, `user_id`, `course_id`, `lesson_id`, `page_number`) nhằm đảm bảo tốc độ lọc ở mức mili-giây:

```python
# Khởi tạo chỉ mục payload trong Qdrant
qdrant_client.create_payload_index(
    collection_name="document_chunks",
    field_name="document_id",
    field_schema="keyword"
)
```

---

## 5. Cơ Sở Dữ Liệu Quan Hệ: PostgreSQL (Neon và Docker)

Hệ thống hỗ trợ linh hoạt hai cấu hình vận hành: **Docker PostgreSQL (`postgres:14-alpine`)** khi chạy phát triển cục bộ (đã cấu hình sẵn trong `src/compose.yaml`) và **Neon Serverless PostgreSQL** trên cloud.

```text
┌──────────────────────────────────────┐  ┌──────────────────────────────────────┐
│    Môi Trường Phát Triển Cục Bộ      │  │     Môi Trường Cloud Production      │
├──────────────────────────────────────┤  ├──────────────────────────────────────┤
│  • Container postgres:14-alpine      │  │  • Neon Serverless PostgreSQL        │
│  • Cổng 127.0.0.1:5432               │  │  • Bộ gộp kết nối PgBouncer          │
│  • Kết nối trực tiếp không SSL       │  │  • DB_SSL_MODE=require               │
│  • Dữ liệu lưu trong volume pgdata   │  │  • Tự động co giãn & sao lưu cloud   │
└──────────────────────────────────────┘  └──────────────────────────────────────┘
```

### 5.1. Xử Lý Tương Thích Chuỗi Kết Nối & Pool Kết Nối

Trong `src/backend/app/core/config.py`, bộ validator `assemble_db_url` tự động chuẩn hóa giao thức `postgres://` hoặc `postgresql://` sang `postgresql+asyncpg://` và **tự động loại bỏ tham số truy vấn `pgbouncer`** trong `DATABASE_URL` (do driver `asyncpg` không hỗ trợ tham số này).

```python
# src/backend/app/core/database.py
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=settings.DB_POOL_SIZE,          # Mặc định: 5
    max_overflow=settings.DB_MAX_OVERFLOW,    # Mặc định: 10
    pool_recycle=settings.DB_POOL_RECYCLE,    # Mặc định: 1800 giây
    pool_pre_ping=settings.DB_POOL_PRE_PING,  # Mặc định: True (kiểm tra kết nối trước khi dùng)
    pool_timeout=30,
    connect_args={"command_timeout": 60, "ssl": settings.DB_SSL_MODE},
)
```

### 5.2. Ma Trận Tham Số Connection Pool

| Tham số | Local Docker | Production (Cloud/Neon) | Mục đích |
|---|---|---|---|
| `DB_POOL_SIZE` | `5` | `5` | Số kết nối nền tảng giữ ổn định |
| `DB_MAX_OVERFLOW` | `10` | `10` | Khoảng đệm mở thêm khi tải tăng đột biến |
| `DB_POOL_RECYCLE` | `1800` | `1800` | Làm mới kết nối nhàn rỗi trước khi bị ngắt |
| `DB_POOL_PRE_PING` | `true` | `true` | Tự động phát hiện và tạo lại socket bị đứt |
| `DB_SSL_MODE` | `disable` | `require` | Mã hóa đường truyền khi kết nối qua mạng công cộng |

### 5.3. Thực Thi Migration Cho Môi Trường Khác

```bash
# Ví dụ chạy Alembic trỏ tạm vào cơ sở dữ liệu cloud từ PowerShell
$env:DATABASE_URL="postgresql+asyncpg://<user>:<password>@<cloud-host>/<db>?sslmode=require"
$env:MIGRATION_MODE="True"
cd nhom07-65httt/src/backend
alembic upgrade head
```

---

## Xem Thêm

- [Thiết kế tổng thể hệ thống](./system-design.md)
- [Giao tiếp liên dịch vụ & Hợp đồng API](./service-communication.md)
- [Lược đồ cơ sở dữ liệu](./database-schema.md)
- [Quy trình AI Agent & RAG](./ai-agent-workflow.md)
- [Hướng dẫn tổng quan (README)](../../README.md)
