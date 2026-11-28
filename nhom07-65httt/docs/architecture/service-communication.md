# Giao Tiếp Liên Dịch Vụ & Hợp Đồng API

> Phiên bản: 2.0 | Cập nhật lần cuối: 14/09/2026 | Phụ trách: Platform Team | Trạng thái: Chính thức (Active)

---

## 1. Tổng Quan Kiến Trúc Giao Tiếp

Hệ thống được phân tách thành ba tầng giao tiếp rõ ràng:
1. **Tầng Client công khai (Frontend → Backend API Gateway):** REST API qua HTTP/HTTPS và Server-Sent Events (SSE) được bảo vệ bằng Bearer JWT (qua proxy `/api/:path*` của Next.js sang `INTERNAL_API_URL`).
2. **Tầng đồng bộ nội bộ (Backend API Gateway / Worker → AI Service):** Giao tiếp HTTP nội bộ giữa các service, xác thực bằng header bí mật dùng chung `X-Internal-API-Key`.
3. **Tầng bất đồng bộ nội bộ (Backend API Gateway → Celery Worker):** Phân phối tác vụ nền qua Redis message broker.

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                        Các Tầng Giao Tiếp Trong Hệ Thống                      │
├──────────────────────────────────────────────────────────────────────────────┤
│  [ web: src/frontend/ ] (Next.js 16 — Cổng 3000)                             │
│         │                                                                    │
│         ▼ HTTP REST + SSE (Authorization: Bearer <JWT>)                      │
│  [ api: src/backend/ ]  (FastAPI API Gateway — Cổng 8000)                    │
│         │                                                                    │
│         ├── HTTP REST / SSE (X-Internal-API-Key: <SECRET>)                   │
│         │   Timeout mặc định: 150s                                           │
│         ▼                                                                    │
│  [ ai: src/ai/ ]        (FastAPI AI Service — Cổng 8001)                     │
│                                                                              │
│  [ api: src/backend/ ] ─── Redis Broker (DB 1: CELERY_BROKER_URL)            │
│         │                  Tác vụ nền: document/media/quiz/essay/flashcards  │
│         ▼                                                                    │
│  [ worker: src/worker/ ] (Celery Worker — concurrency mặc định = 2)          │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Frontend → API Gateway (Tầng Công Khai)

Toàn bộ lưu lượng từ người dùng đều đi qua **API Gateway (`src/backend/`)**. Trình duyệt không kết nối trực tiếp tới AI Service, Celery Worker hay cơ sở dữ liệu; Server Next.js (`src/frontend/`) chuyển tiếp các lời gọi `/api/:path*` sang biến `INTERNAL_API_URL` (`http://api:8000` trong Docker hoặc `http://localhost:8000` ở máy local).

### 2.1. Hợp Đồng Xác Thực (Authentication Contract)

Xác thực người dùng sử dụng **JSON Web Tokens (JWT)** ký bằng thuật toán HMAC-SHA256 (`HS256`):
- **Access Token:** Thời hạn ngắn (30 phút), gửi trong header `Authorization: Bearer <access_token>`.
- **Refresh Token:** Thời hạn dài (7 ngày), lưu trong cookie `HttpOnly` bảo mật hoặc truyền qua body tới `/api/v1/auth/refresh`.

#### Đăng Ký Tài Khoản
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "student@example.com",
  "password": "<secure_password>",
  "full_name": "Minh Tran",
  "role": "student"
}
```
**Phản hồi (`201 Created`):**
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "student@example.com",
    "full_name": "Minh Tran",
    "role": "student"
  },
  "token": {
    "access_token": "<jwt_access_token>",
    "token_type": "bearer"
  }
}
```

#### Đăng Nhập & Nhận Token
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "student@example.com",
  "password": "<secure_password>"
}
```
**Phản hồi (`200 OK`):**
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "student@example.com",
    "role": "student"
  },
  "token": {
    "access_token": "<jwt_access_token>",
    "refresh_token": null,
    "token_type": "bearer"
  }
}
```

### 2.2. Hợp Đồng Tải Lên Tài Liệu

Quá trình nạp tài liệu diễn ra bất đồng bộ: API tiếp nhận dữ liệu nhị phân, lưu lên MinIO, ghi bản ghi vào PostgreSQL, đẩy tác vụ vào hàng đợi Celery và trả về ngay mã theo dõi (`202 Accepted`).

```http
POST /api/v1/documents/upload
Authorization: Bearer <jwt_access_token>
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="lecture-notes.pdf"
Content-Type: application/pdf

<binary data>
------WebKitFormBoundary--
```
**Phản hồi (`202 Accepted`):**
```json
{
  "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "file_name": "lecture-notes.pdf",
  "file_type": "pdf",
  "file_size": 2481024,
  "status": "processing",
  "created_at": "2026-09-14T10:00:00Z"
}
```

### 2.3. Hợp Đồng Chat Truyền Phát Trực Tiếp (SSE)

Chế độ chat streaming truyền dần từng token câu trả lời qua **Server-Sent Events (SSE)** nhằm giảm tối đa thời gian phản hồi token đầu tiên (TTFT).

```http
POST /api/v1/chat/ask/stream
Authorization: Bearer <jwt_access_token>
Accept: text/event-stream
Content-Type: application/json

{
  "session_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "query": "What are the core differences between supervised and unsupervised learning?",
  "document_ids": ["6ba7b810-9dad-11d1-80b4-00c04fd430c8"]
}
```

**Định dạng luồng SSE (`data: {JSON}\n\n`):**
```text
data: {"type": "meta", "intent": "qa", "citations": [{"document_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8", "page_number": 4, "text": "Supervised algorithms map inputs to known outputs..."}]}

data: {"type": "token", "text": "Supervised"}

data: {"type": "token", "text": " learning"}

data: {"type": "token", "text": " uses labeled datasets..."}

data: {"type": "done", "answer": "Supervised learning uses labeled datasets..."}
```

---

## 3. API Gateway / Worker → AI Service (Tầng Đồng Bộ Nội Bộ)

API Gateway (`src/backend/app/clients/ai_client.py`) và Worker chuyển tiếp các yêu cầu xử lý AI tới **AI Service (`src/ai/main.py`)**. Mọi endpoint bảo vệ trên AI Service đều kiểm tra header khóa nội bộ.

### 3.1. Cấu Hình & Xác Thực Nội Bộ

Trong `compose.yaml` (Docker) hoặc `.env` cục bộ:
```env
AI_SERVICE_URL=http://ai:8001          # hoặc http://localhost:8001 khi chạy native
AI_SERVICE_TIMEOUT=150.0
INTERNAL_API_KEY=<chuỗi-bí-mật-tối-thiểu-16-ký-tự>
```

Mỗi request gửi sang AI Service bắt buộc phải kèm header:
```http
X-Internal-API-Key: <INTERNAL_API_KEY>
```
Mọi request thiếu header hoặc sai khóa đều bị từ chối ngay với mã `403 Forbidden`.

### 3.2. Danh Mục Endpoint Nội Bộ Trên AI Service (`src/ai/main.py`)

| Endpoint | Phương thức | Mục đích | Đầu vào chính | Phản hồi |
|---|---|---|---|---|
| `/chat/ask` | POST | Truy vấn RAG đồng bộ (qua `asyncio` workflow) | `QueryRequest` (`query`, `document_ids` / `course_id`, `lesson_id`, `tutor_mode`) | `ChatResponse` (`answer`, `citations`, `token_usage`) |
| `/chat/ask/stream` | POST | Truy vấn RAG truyền phát SSE từng token | `QueryRequest` | Luồng `text/event-stream` (`meta`, `token`, `done`, `error`) |
| `/study/quiz/generate` | POST | Sinh câu hỏi trắc nghiệm từ ngữ cảnh | `QuizGenerateRequest` (`context`, `quiz_type`, `question_count`) | `QuizGenerateResponse` |
| `/study/quiz/generate-from-lesson` | POST | Truy xuất Qdrant theo bài học & sinh quiz | `QuizGenerateFromLessonRequest` (`lesson_id`, `course_id`) | `QuizGenerateResponse` |
| `/study/quiz/remedial` | POST | Sinh mini-quiz ôn tập cho câu hỏi làm sai | `RemedialQuizRequest` (`missed_questions`, `lesson_id`) | `QuizGenerateResponse` |
| `/study/flashcards/generate` | POST | Sinh bộ thẻ ghi nhớ mặt trước / mặt sau | `FlashcardGenerateRequest` (`context`, `set_name`, `count`) | `FlashcardGenerateResponse` |
| `/study/essay/grade` | POST | Chấm bài tự luận đối chiếu tài liệu nguồn | `EssayGradeRequest` (`essay_text`, `document_id`, `context`) | `EssayGradeResponse` (`score`, `feedback`, `comparisons`) |
| `/study/mindmap/generate` | POST | Sinh cây Markdown cho sơ đồ tư duy (Markmap) | `MindmapGenerateRequest` (`content`, `title`) | `MindmapGenerateResponse` (`markdown_tree`) |
| `/internal/config/sync` | POST | Đồng bộ Gemini API keys đang bật và model từ Admin database | `{"keys": [...], "model_id": "gemini-3.5-flash-lite"}` | `{"synced": true, "count": int, "model_id": str}` |
| `/internal/transcribe` | POST | Phiên âm một audio chunk bằng key/model Gemini do Admin quản lý | `{"mime_type": "audio/wav", "audio_base64": "..."}` | `{"text": str}` |
| `/internal/keys/status` | GET | Lấy trạng thái xoay vòng khóa & số lượt dùng | — | Danh sách khóa đã che (`masked`) & bộ đếm |

### 3.3. Hợp Đồng Truy Vấn RAG Nội Bộ

```http
POST /chat/ask
X-Internal-API-Key: <INTERNAL_API_KEY>
Content-Type: application/json

{
  "query": "Explain backpropagation in deep neural networks.",
  "document_ids": ["6ba7b810-9dad-11d1-80b4-00c04fd430c8"],
  "session_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Phản hồi (`200 OK`):**
```json
{
  "answer": "Backpropagation calculates the gradient of the loss function with respect to each weight using the chain rule...",
  "citations": [
    {
      "document_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
      "chunk_id": "a98c091d-28e4-4d89-8dcf-4e76cba98a12",
      "page_number": 18,
      "text": "The gradient of the error is propagated backward through the network layers...",
      "material_id": "",
      "course_id": "",
      "lesson_id": ""
    }
  ],
  "token_usage": {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0
  }
}
```

### 3.4. Hợp Đồng Sinh Trắc Nghiệm Nội Bộ

```http
POST /study/quiz/generate
X-Internal-API-Key: <INTERNAL_API_KEY>
Content-Type: application/json

{
  "context": "Extracted document chunks...",
  "quiz_type": "detailed",
  "question_count": 5
}
```

**Phản hồi (`200 OK`):**
```json
{
  "questions": [
    {
      "id": "q1",
      "question": "Which algorithm computes gradients in neural networks?",
      "options": [
        "Backpropagation",
        "Bubble Sort",
        "Dijkstra's Algorithm",
        "K-Means"
      ],
      "correct_answer": "A",
      "explanation": "Backpropagation computes the gradient of the loss function via the chain rule."
    }
  ]
}
```

---

## 4. API Gateway → Celery Worker (Tầng Bất Đồng Bộ Nội Bộ)

Xử lý tệp nặng, trích xuất văn bản, nhận dạng giọng nói/OCR và sinh bài tập chạy nền được đẩy sang Celery Worker qua Redis.

### 4.1. Cấu Hình Hàng Đợi Thông Điệp (Message Broker)

```env
REDIS_URL=redis://redis:6379/0          # Cache ứng dụng & lưu kết quả Celery
CELERY_BROKER_URL=redis://redis:6379/1  # Broker hàng đợi Celery chuyên biệt
```

### 4.2. Các Module Tác Vụ Trong Worker (`src/worker/celery_app.py`)

| Module tác vụ (`include`) | Chức năng chính | Giới hạn mềm / cứng | Nơi cập nhật kết quả |
|---|---|---|---|
| `src.tasks.document_processing` | Nạp & vector hóa PDF, DOCX, TXT, ảnh, audio/video | 540s / 600s | PostgreSQL (`documents.status`) & Qdrant |
| `src.tasks.lesson_content` | Nạp nội dung học liệu gắn bài học vào Qdrant | 540s / 600s | Qdrant (`lesson_id`, `course_id`) |
| `src.tasks.course_file` | Xử lý tệp đính kèm của khóa học | 540s / 600s | PostgreSQL & Qdrant |
| `src.tasks.quiz` | Sinh bộ câu hỏi trắc nghiệm từ tài liệu qua AI Service | 540s / 600s | Redis / PostgreSQL (`quiz_sets`) |
| `src.tasks.course_quiz` | Sinh câu hỏi trắc nghiệm từ khóa học / bài học | 540s / 600s | PostgreSQL (`course_quizzes`) |
| `src.tasks.essay` | Chấm điểm bài tự luận qua AI Service | 540s / 600s | PostgreSQL (`essay_submissions`) |
| `src.tasks.flashcards` | Sinh bộ thẻ ghi nhớ qua AI Service | 540s / 600s | PostgreSQL (`flashcard_items`) |

### 4.3. Thiết Lập Thực Thi Celery

```python
# src/worker/celery_app.py
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,          # Giới hạn cứng: 10 phút
    task_soft_time_limit=540,     # Giới hạn mềm: 9 phút
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=20,# Tái khởi tạo worker con để tránh rò rỉ RAM PyTorch
    task_acks_late=True,
    worker_concurrency=int(os.getenv("CELERY_CONCURRENCY", "2")),
)
```

---

## 5. Bảo Mật & Phân Quyền Liên Dịch Vụ

```text
                    Lưu lượng công khai               Mạng Docker / Nội bộ
  Trình duyệt Web ──────────────────────► API Gateway ───────────────────────► AI Service
                    Authorization:                      X-Internal-API-Key:
                 Bearer <JWT Token>                     <INTERNAL_API_KEY>
```

1. **Phòng vệ nhiều lớp (Defense in Depth):**
   - Trong Docker Compose (`src/compose.yaml`), chỉ có **Next.js (`3000`)** và **Backend API (`8000`, bind về `127.0.0.1`)** được mở cổng trực tiếp; **AI Service (`8001`)** chỉ lắng nghe trong mạng nội bộ Compose (`http://ai:8001`).
2. **So sánh khóa an toàn thời gian hằng (Timing-Safe Comparison):**
   - AI Service kiểm tra khóa bằng `secrets.compare_digest` để chống tấn công dò thời gian (timing side-channel attack):
   ```python
   # src/ai/main.py
   async def verify_internal_key(x_internal_api_key: str = Header(..., alias="X-Internal-API-Key")):
       if not secrets.compare_digest(x_internal_api_key, settings.INTERNAL_API_KEY):
           raise HTTPException(status_code=403, detail="Forbidden: Invalid Internal API Key")
       return x_internal_api_key
   ```
3. **Kiểm soát khóa nội bộ lúc khởi động:**
   - `INTERNAL_API_KEY` bắt buộc tối thiểu 16 ký tự và không được trùng với các giá trị mặc định yếu (`changeme`, `secret`, `your_internal_key`...) — bị kiểm tra ngay bởi Pydantic validator trong `src/backend/app/core/config.py`.

---

## 6. Cơ Chế Chịu Lỗi, Timeout & Thử Lại

### 6.1. Định Dạng Phản Hồi Lỗi Chuẩn (`src/backend/app/main.py`)

Mọi lỗi `HTTPException`, lỗi kiểm tra hợp lệ hay lỗi máy chủ tại Backend API đều trả về JSON thống nhất:

```json
{
  "error": "http_error",
  "message": "Mô tả chi tiết nguyên nhân lỗi",
  "details": null
}
```

### 6.2. Phân Loại Mã Lỗi HTTP Phổ Biến

| Mã HTTP | Giá trị `error` / Ngữ cảnh | Mô tả | Hành động phía Client |
|---|---|---|---|
| **400** | `http_error` | Dữ liệu nghiệp vụ không hợp lệ hoặc vượt hạn mức | Kiểm tra tham số hoặc hạn mức tài khoản |
| **401** | `http_error` | JWT Bearer token thiếu, hết hạn hoặc đã bị thu hồi | Gọi `/api/v1/auth/refresh` hoặc đăng nhập lại |
| **403** | `http_error` | Không đủ vai trò (`admin`/`lecturer`) hoặc sai `X-Internal-API-Key` | Kiểm tra quyền truy cập của tài khoản |
| **404** | `http_error` | Tài liệu, phiên chat, khóa học hoặc bộ đề không tồn tại | Kiểm tra lại UUID tài nguyên |
| **422** | `validation_error` | Lỗi kiểm tra schema Pydantic (`details` chứa chi tiết từng trường) | Sửa đúng định dạng payload theo đặc tả |
| **429** | `Rate limit exceeded` | Vượt quá ngưỡng giới hạn tần suất (Redis + `slowapi`) | Chờ và thử lại theo cơ chế backoff |
| **500** | `internal_server_error` | Lỗi ngoài ý muốn trên máy chủ (ẩn chi tiết nhạy cảm) | Ghi nhận lỗi và liên hệ quản trị viên |
| **503** | `http_error` / `degraded` | Dịch vụ phụ thuộc (Redis/PostgreSQL/AI Service) tạm thời gián đoạn | Kiểm tra endpoint `/health/ready` |

### 6.3. Ma Trận Timeout & Thử Lại (`tenacity`)

| Luồng kết nối | Timeout cơ sở | Số lần thử lại | Chiến lược backoff | Cơ chế dự phòng |
|---|---|---|---|---|
| **API (`AiClient.ask`) → AI Service** | 150.0s | Tối đa 2 lần | Exponential backoff (2s–10s) | Frontend có thể chuyển sang luồng SSE hoặc báo lỗi thân thiện |
| **API (`AiClient`) → Công cụ học tập AI** | 150.0s | Tối đa 3 lần | Exponential backoff (2s–10s) | Worker báo lỗi tác vụ nếu hết lượt |
| **AI Service → Phân loại / Chấm chunk (Groq)** | 10s – 15s | Xoay vòng khóa / dự phòng | Bỏ qua bước chấm hoặc dùng chunk thô | Chuyển sang khóa dự phòng / giữ ngữ cảnh an toàn |
| **AI Service → Sinh câu trả lời (Gemini)** | 60.0s | Xoay vòng API Key trong `GeminiKeyRotator` | Tự động đổi sang key kế tiếp khi gặp quota limit | Thông báo timeout rõ ràng nếu toàn bộ key bận |

---

## 7. Endpoint Kiểm Tra Sức Khỏe (Health & Readiness Probes)

Backend API (`8000`) và AI Service (`8001`) cung cấp các endpoint kiểm tra trạng thái để Docker Compose (`src/compose.yaml`) và hệ thống giám sát theo dõi:

### Backend API (`http://localhost:8000`)
```http
GET /health
```
**Phản hồi (`200 OK`):**
```json
{
  "status": "healthy"
}
```

```http
GET /health/ready
```
**Phản hồi (`200 OK` hoặc `503 Service Unavailable`):**
```json
{
  "status": "ready",
  "dependencies": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```

### AI Service (`http://127.0.0.1:8001` nội bộ)
- `GET /health` → Kiểm tra kết nối Qdrant (không ép tải sớm mô hình embedding ~500MB trong lúc probe).
- `GET /ready` → Trả về `{"ready": true}`.

---

## Xem Thêm

- [Thiết kế tổng thể hệ thống](./system-design.md)
- [Lược đồ cơ sở dữ liệu](./database-schema.md)
- [Quy trình AI Agent & RAG](./ai-agent-workflow.md)
- [Lưu trữ, bộ nhớ đệm & bền vững dữ liệu](./storage-and-cache.md)
