# Learning Hub — Nhóm 07 (65HTTT)

> **Đề tài:** Multimodal AI Learning Hub — Nền tảng phát triển năng lực và đào tạo thông minh dành cho sinh viên  
> **Học phần:** Hệ Thống Kinh Doanh Thông Minh · **Lớp:** 65HTTT · **Giảng viên hướng dẫn:** Đỗ Oanh Cường  
> **Thông tin thành viên:** [danhsachnhom.md](./danhsachnhom.md) · **Kho tài liệu đầy đủ:** [docs/README.md](./docs/README.md)

Mã nguồn trong [`src/`](./src/) được tổ chức theo mô hình monorepo 4 service độc lập (`frontend/`, `backend/`, `ai/`, `worker/`), dùng chung một file điều phối Docker [`src/compose.yaml`](./src/compose.yaml) và một file biến môi trường `src/.env` duy nhất.

---

## 1. Tổng Quan Chức Năng Theo Vai Trò

| Vai trò | Chức năng trọng tâm |
|---|---|
| **Học viên (`student`)** | Tải lên & xử lý tài liệu đa định dạng (PDF, DOCX, TXT, ảnh, audio/video, URL); hỏi đáp Gia sư AI (Multimodal RAG truyền phát SSE kèm trích dẫn trang / mốc thời gian); sinh bộ trắc nghiệm & thẻ ghi nhớ (flashcards); chấm bài tự luận đối chiếu nguồn; sơ đồ tư duy; mua / ghi danh khóa học và theo dõi tiến độ. |
| **Giảng viên (`lecturer`)** | Tạo và xuất bản khóa học theo chương/bài học; tải video/tài liệu giảng dạy; trợ lý AI phác thảo bài giảng & tóm tắt; đăng thông báo khóa học; quản lý hỏi đáp (Q&A) theo bài học; theo dõi tiến độ học viên, phân tích câu hỏi hay sai và xuất báo cáo CSV/XLSX. |
| **Quản trị viên (`admin`)** | Quản lý tài khoản & phân quyền RBAC; kiểm duyệt khóa học và cây danh mục; quản lý Kho khóa AI Key Vault mã hóa Fernet (hỗ trợ xoay vòng khóa Gemini); theo dõi thống kê & kiểm tra sức khỏe toàn hệ thống. |

---

## 2. Kiến Trúc & Công Nghệ

```text
Trình duyệt ──HTTP / SSE──> Next.js Web (3000) ──HTTP──> Backend API (8000)
                                                            ├──HTTP + X-Internal-API-Key──> AI Service (8001)
                                                            ├──Hàng đợi Redis─────────────> Celery Worker
                                                            ├──PostgreSQL 14
                                                            └──MinIO
AI Service ──> Qdrant và Redis
Worker ──────> PostgreSQL 14, MinIO, Qdrant và AI Service
```

| Thành phần | Thư mục / Tệp | Công nghệ chính | Cổng mặc định |
|---|---|---|---|
| **Frontend** | `src/frontend/` | Next.js 16 (App Router, standalone), React 19, TypeScript, Tailwind CSS, Zustand, Markmap | `3000` |
| **Backend API** | `src/backend/` | FastAPI, SQLAlchemy (Async), Alembic, Pydantic v2, Redis Cache, `slowapi` | `8000` |
| **AI Service** | `src/ai/` | FastAPI, luồng RAG đa bước bằng `asyncio` (`GraphState`), Gemini LLM, `all-MiniLM-L6-v2`, Qdrant | `8001` *(nội bộ Compose)* |
| **Worker** | `src/worker/` | Celery, Redis Broker, PyMuPDF (`fitz`), `pdfplumber`, FFmpeg, Whisper, Tesseract OCR | — |
| **Hạ tầng** | `src/compose.yaml` | PostgreSQL 14 (`postgres:14-alpine`), Redis 7 (`redis:7-alpine`), Qdrant (`v1.12.5`), MinIO | `5432`, `6379`, `6333`, `9000` / `9001` |

> **Lưu ý kiến trúc:** Trình duyệt chỉ gọi các đường dẫn `/api/:path*`; Next.js proxy các lời gọi này tới `http://api:8000` trong mạng Docker. Toàn bộ giao tiếp đồng bộ giữa `backend`/`worker` với `ai` được bảo vệ bằng header `X-Internal-API-Key`.

---

## 3. Cấu Trúc Thư Mục Nhóm

```text
nhom07-65httt/
├── README.md                  # Tài liệu tổng quan và vận hành bằng Docker
├── danhsachnhom.md            # Thông tin nhóm 07, danh sách thành viên & phân công nhiệm vụ
├── docs/                      # Tài liệu hệ thống chi tiết (Tiếng Việt)
│   ├── README.md              # Chỉ mục toàn bộ tài liệu kiến trúc, API & hướng dẫn
│   ├── architecture/          # Thiết kế hệ thống, giao tiếp dịch vụ, DB schema, lưu trữ & RAG
│   ├── api/                   # Đặc tả API REST & SSE streaming theo phân hệ
│   └── guides/                # Tài khoản mẫu, thuật ngữ & cẩm nang Student/Lecturer/Admin
└── src/                       # Mã nguồn monorepo & cấu hình Docker dùng chung
    ├── .env.example           # Mẫu biến môi trường dùng chung cho toàn bộ service
    ├── .dockerignore          # Quy tắc loại trừ ngữ cảnh build Docker
    ├── .python-version        # Phiên bản Python mục tiêu (3.11)
    ├── compose.yaml           # Định nghĩa toàn bộ cụm container (hạ tầng + 4 service)
    ├── python.Dockerfile      # Dockerfile đa mục tiêu cho api, ai và worker
    ├── ruff.toml              # Cấu hình lint Python dùng chung
    ├── frontend/              # Ứng dụng Next.js 16 + Dockerfile + đặc tả UI giảng dạy
    ├── backend/               # Dịch vụ API Gateway FastAPI + Alembic migrations
    ├── ai/                    # Dịch vụ AI RAG (FastAPI + asyncio workflow + Qdrant/LLM)
    └── worker/                # Tiến trình Celery xử lý tệp nền & tác vụ AI
```

---

## 4. Yêu Cầu Môi Trường

- Docker Desktop với Docker Compose v2 trở lên.
- Máy 8 GB RAM có thể chạy demo nhẹ; nên dùng 16 GB RAM nếu thường xuyên xử lý AI, OCR hoặc nhiều tài liệu.
- Không cần cài Python, Node.js, PostgreSQL, Redis, Qdrant, MinIO hay FFmpeg trực tiếp trên máy.

---

## 5. Cấu Hình Docker (Một File `.env`)

Toàn bộ hệ thống đọc cấu hình từ `nhom07-65httt/src/.env`:

```powershell
cd nhom07-65httt/src
Copy-Item .env.example .env
```

Mở tệp `src/.env` và cập nhật **bắt buộc** toàn bộ các giá trị `CHANGE_ME_*` sau:

| Biến môi trường | Yêu cầu | Ghi chú đồng bộ |
|---|---|---|
| `DB_PASSWORD` | Mật khẩu PostgreSQL | Phải khớp với mật khẩu trong `DATABASE_URL` |
| `MINIO_ROOT_USER` | Tên người dùng gốc MinIO | Khớp với `MINIO_ACCESS_KEY` trong cấu hình Docker |
| `MINIO_ROOT_PASSWORD` | Mật khẩu gốc MinIO | Khớp với `MINIO_SECRET_KEY` trong cấu hình Docker |
| `SECRET_KEY` | Chuỗi bí mật JWT (tối thiểu **32 ký tự**) | Không dùng các chuỗi mặc định yếu (`changeme`, `secret`...) |
| `AI_KEY_ENCRYPTION_KEY` | Khóa mã hóa khóa AI (tối thiểu 32 byte hex hoặc Fernet key) | Dùng mã hóa API key lưu trong bảng AI Key Vault |
| `INTERNAL_API_KEY` | Khóa xác thực nội bộ (tối thiểu **16 ký tự**) | Dùng cho header `X-Internal-API-Key` tới `ai/` |

**Các biến tùy chọn (điền khi cần dùng tính năng tương ứng):**
- **AI LLM:** Thêm Gemini API key và chọn model trong Admin → Khóa API & AI. Không cần đặt `GEMINI_API_KEY` hoặc `GEMINI_MODEL` trong môi trường chạy.
- **Đăng nhập OAuth:** `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `NEXT_PUBLIC_GOOGLE_CLIENT_ID`, `FACEBOOK_APP_ID`, `FACEBOOK_APP_SECRET`, `NEXT_PUBLIC_FACEBOOK_APP_ID`.
- **Thanh toán & Email:** `VNPAY_*`, `MOMO_*`, `SMTP_*`.
- **Khởi tạo tài khoản Admin:** `ADMIN_PASSWORD` (sử dụng khi chạy script `app.core.init_db`).

Có thể tạo nhanh các khóa bí mật bằng Docker:
```powershell
docker run --rm python:3.11-alpine python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32)); print('INTERNAL_API_KEY=' + secrets.token_hex(16)); print('AI_KEY_ENCRYPTION_KEY=' + secrets.token_hex(32))"
```

---

## 6. Khởi Chạy Bằng Docker Compose

Từ thư mục `nhom07-65httt/src/`:

```bash
# Build image và khởi chạy toàn bộ cụm
docker compose up -d --build

# Khởi tạo hoặc cập nhật các bảng PostgreSQL
docker compose --profile tools run --rm migrate

# Kiểm tra trạng thái các container
docker compose ps
```

Nếu các cổng mặc định đang được ứng dụng khác sử dụng, đặt `DB_HOST_PORT`, `REDIS_HOST_PORT`, `API_HOST_PORT` và `WEB_HOST_PORT` trong `src/.env` trước khi chạy. Cổng giao tiếp nội bộ giữa các container không đổi.

### Khởi Tạo Dữ Liệu Ban Đầu (Tùy Chọn)

```bash
# Nạp danh mục khóa học mặc định
docker compose exec api python -m app.scripts.seed_categories

# Tạo tài khoản quản trị viên
docker compose exec -e ADMIN_PASSWORD="<MatKhauAdminManh>" api python -m app.core.init_db
```

### Địa Chỉ Truy Cập Mặc Định

- **Giao diện Web (Next.js):** `http://localhost:3000`
- **Tài liệu Backend API (Swagger UI):** `http://localhost:8000/docs`
- **Tài liệu Backend API (ReDoc):** `http://localhost:8000/redoc`
- **Kiểm tra sức khỏe API Gateway:** `http://localhost:8000/health/ready`
- **MinIO Console:** `http://localhost:9001` *(đăng nhập bằng `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD`)*

Nếu đã đổi `WEB_HOST_PORT` hoặc `API_HOST_PORT`, thay cổng trong các địa chỉ trên bằng giá trị tương ứng trong `src/.env`.

### Các Lệnh Vận Hành Hữu Ích

```bash
# Theo dõi log của các dịch vụ ứng dụng
docker compose logs -f api ai worker web

# Dừng toàn bộ container (giữ lại dữ liệu trong volumes)
docker compose down

# Dừng và xóa sạch toàn bộ volumes dữ liệu (cân nhắc trước khi dùng)
docker compose down -v
```

---

## 7. Hệ Thống Tài Liệu Chi Tiết (`docs/`)

Xem mục lục đầy đủ tại [`docs/README.md`](./docs/README.md):

| Nhóm tài liệu | Nội dung chính | Liên kết |
|---|---|---|
| **Kiến trúc (`docs/architecture/`)** | Thiết kế tổng thể hệ thống | [system-design.md](./docs/architecture/system-design.md) |
| | Giao tiếp liên dịch vụ & hợp đồng nội bộ | [service-communication.md](./docs/architecture/service-communication.md) |
| | Lược đồ cơ sở dữ liệu PostgreSQL & Qdrant | [database-schema.md](./docs/architecture/database-schema.md) |
| | Kiến trúc lưu trữ MinIO, Redis & bền vững dữ liệu | [storage-and-cache.md](./docs/architecture/storage-and-cache.md) |
| | Quy trình xử lý AI Workflow & RAG (`asyncio`) | [ai-agent-workflow.md](./docs/architecture/ai-agent-workflow.md) |
| **Đặc tả API (`docs/api/`)** | Tổng quan API, phân trang, mã lỗi & rate limit | [overview.md](./docs/api/overview.md) |
| | Xác thực JWT, OAuth2 & xoay vòng refresh token | [authentication.md](./docs/api/authentication.md) |
| | Tài liệu, khóa học & vận hành giảng dạy | [documents-and-courses.md](./docs/api/documents-and-courses.md) |
| | Hội thoại Chat & Multimodal RAG (REST / SSE) | [chat-and-rag.md](./docs/api/chat-and-rag.md) |
| | Công cụ học tập AI (Quiz, Flashcards, Essay) | [study-tools.md](./docs/api/study-tools.md) |
| | Quản trị hệ thống, AI Key Vault & kiểm tra sức khỏe | [admin.md](./docs/api/admin.md) |
| **Hướng dẫn (`docs/guides/`)** | Tài khoản mẫu & ma trận đường dẫn theo vai trò | [demo-accounts.md](./docs/guides/demo-accounts.md) |
| | Bảng thuật ngữ kỹ thuật | [glossary.md](./docs/guides/glossary.md) |
| | Cẩm nang sử dụng dành cho Học viên | [student-guide.md](./docs/guides/student-guide.md) |
| | Cẩm nang vận hành dành cho Giảng viên | [lecturer-guide.md](./docs/guides/lecturer-guide.md) |
| | Cẩm nang vận hành dành cho Quản trị viên | [admin-guide.md](./docs/guides/admin-guide.md) |
| | Các luồng nghiệp vụ đầu-cuối (End-to-End) | [end-to-end-workflows.md](./docs/guides/end-to-end-workflows.md) |
| | Giải thích công nghệ & phương pháp cho người non-tech | [tech-and-methods-explained.md](./docs/guides/tech-and-methods-explained.md) |
| **Đặc tả UI Frontend** | Danh sách tác vụ trải nghiệm giảng dạy | [lecturer-teaching-experience-tasks.md](./src/frontend/docs/lecturer-teaching-experience-tasks.md) |
