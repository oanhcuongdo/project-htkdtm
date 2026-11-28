# Multimodal AI Learning Hub — Tài Liệu Tham Chiếu API: Tài Liệu, Khóa Học & Giảng Dạy

**Phiên bản đặc tả:** 1.0.0  
**Cập nhật lần cuối:** 14/09/2026  
**Module mục tiêu:** `/api/v1/documents`, `/api/v1/courses`, `/api/v1/lessons`, `/api/v1/enrollments`, `/api/v1/progress`  
**Cơ chế bảo mật:** HTTP Bearer JWT (Student, Lecturer, Administrator)

---

## 1. Tổng Quan Các Endpoint

| Phương thức | Đường dẫn | Yêu cầu xác thực | Mô tả |
|---|---|---|---|
| **Tài liệu (Documents)** | | | |
| `POST` | `/api/v1/documents/upload` | Bearer Token | Tải tài liệu lên để trích xuất và vector hóa bất đồng bộ (`202 Accepted`) |
| `GET` | `/api/v1/documents` | Bearer Token | Liệt kê tài liệu của người dùng có phân trang và lọc trạng thái |
| `GET` | `/api/v1/documents/{doc_id}` | Bearer Token | Lấy metadata, trạng thái xử lý và số lượng chunk của tài liệu |
| `GET` | `/api/v1/documents/{doc_id}/content` | Bearer / Cookie | Truyền phát nội dung tệp trực tiếp (PDF, video, audio) hỗ trợ range request |
| `POST` | `/api/v1/documents/{doc_id}/retry` | Bearer Token | Đưa tài liệu xử lý lỗi vào hàng đợi chạy lại |
| `DELETE` | `/api/v1/documents/{doc_id}` | Bearer Token | Xóa tài liệu, đối tượng trên MinIO và vector chunk trong Qdrant (`204 No Content`) |
| **Khóa học & Giáo trình** | | | |
| `GET` | `/api/v1/courses` | Token tùy chọn | Duyệt và lọc các khóa học đã xuất bản (tìm kiếm, danh mục, trình độ, giá) |
| `POST` | `/api/v1/courses` | Lecturer / Admin | Tạo bản nháp khóa học mới (`201 Created`) |
| `GET` | `/api/v1/courses/{course_id}` | Token tùy chọn | Lấy chi tiết khóa học, đề cương và hồ sơ giảng viên |
| `PUT` | `/api/v1/courses/{course_id}` | Lecturer / Admin | Cập nhật metadata, học phí và thiết lập khóa học |
| `POST` | `/api/v1/courses/{course_id}/publish`| Lecturer / Admin | Xuất bản khóa học lên danh mục công khai |
| `POST` | `/api/v1/courses/{course_id}/archive`| Lecturer / Admin | Lưu trữ khóa học để ẩn khỏi lượt ghi danh mới |
| `DELETE` | `/api/v1/courses/{course_id}` | Lecturer / Admin | Xóa vĩnh viễn khóa học nháp (`204 No Content`) |
| `GET` | `/api/v1/courses/{course_id}/sections`| Bearer Token | Lấy danh sách chương kèm cấu trúc bài học lồng bên trong |
| `POST` | `/api/v1/courses/{course_id}/sections`| Lecturer / Admin | Thêm chương mới vào đề cương khóa học |
| `POST` | `/api/v1/sections/{section_id}/lessons`| Lecturer / Admin | Thêm bài học mới vào một chương (video, văn bản, tài liệu) |
| `GET` | `/api/v1/sections/{section_id}/lessons/{lesson_id}` | Bearer Token | Lấy nội dung bài học, tài liệu đính kèm và luồng video |
| **Ghi danh & Tiến độ** | | | |
| `POST` | `/api/v1/courses/{course_id}/enroll/payment-intent` | Bearer Token | Khởi tạo giao dịch thanh toán ghi danh khóa học |
| `POST` | `/api/v1/courses/{course_id}/enroll/confirm` | Bearer Token | Xác nhận thanh toán và kích hoạt quyền học khóa học |
| `GET` | `/api/v1/my-enrollments` | Bearer Token | Liệt kê toàn bộ khóa học mà học viên hiện tại đã ghi danh |
| `GET` | `/api/v1/enrollments/{enrollment_id}/progress` | Bearer Token | Xem chỉ số hoàn thành bài học và học liệu của học viên |
| `POST` | `/api/v1/enrollments/{enrollment_id}/lessons/{lesson_id}/progress` | Bearer Token | Đánh dấu bài học đã hoàn thành hoặc chưa hoàn thành |
| `POST` | `/api/v1/enrollments/{enrollment_id}/materials/{material_id}/progress` | Bearer Token | Cập nhật vị trí đang xem và phần trăm hoàn thành học liệu |
| **Vận hành giảng dạy (Teaching Ops)** | | | |
| `GET` | `/api/v1/courses/{course_id}/students/{student_id}/progress-summary` | Lecturer / Admin | Chi tiết tiến độ của từng học viên (bài học, điểm trắc nghiệm) |
| `POST` | `/api/v1/courses/{course_id}/students/{student_id}/remind` | Lecturer / Admin | Gửi thông báo nhắc nhở học tập tới học viên tiến độ chậm |
| `GET` | `/api/v1/courses/{course_id}/announcements` | Bearer Token | Liệt kê các thông báo đã đăng trong khóa học |
| `POST` | `/api/v1/courses/{course_id}/announcements` | Lecturer / Admin | Đăng thông báo mới kèm tự động gửi notification cho học viên |
| `PUT` | `/api/v1/courses/{course_id}/announcements/{announcement_id}` | Lecturer / Admin | Chỉnh sửa thông báo hiện có |
| `DELETE`| `/api/v1/courses/{course_id}/announcements/{announcement_id}` | Lecturer / Admin | Xóa thông báo |
| `GET` | `/api/v1/lessons/{lesson_id}/discussions` | Bearer Token | Liệt kê các chủ đề hỏi đáp (Q&A) và phản hồi trong bài học |
| `POST` | `/api/v1/lessons/{lesson_id}/discussions` | Bearer Token | Đặt câu hỏi Q&A mới hoặc trả lời một chủ đề |
| `PUT` | `/api/v1/lessons/{lesson_id}/discussions/pin/{post_id}` | Lecturer / Admin | Bật/tắt ghim một bài thảo luận lên đầu |
| `POST` | `/api/v1/lessons/{lesson_id}/discussions/posts/{post_id}/mark-answer` | Lecturer / Admin | Đánh dấu câu trả lời chính thức từ giảng viên |
| `POST` | `/api/v1/lessons/{lesson_id}/discussions/posts/{post_id}/upvote` | Bearer Token | Bình chọn hữu ích (upvote) cho câu hỏi hoặc câu trả lời |
| `POST` | `/api/v1/courses/{course_id}/ai-assist` | Lecturer / Admin | Trợ lý giảng dạy AI: sinh dàn ý bài giảng, tóm tắt hoặc lời thoại |
| `GET` | `/api/v1/courses/{course_id}/quiz-analytics` | Lecturer / Admin | Tổng hợp tỷ lệ trả lời sai và độ khó từng câu hỏi |

---

## 2. Xử Lý & Nạp Tài Liệu (Ingestion)

### 2.1 Vòng Đời Trạng Thái Tài Liệu

Mỗi tài liệu được tải lên hoặc thu thập từ web đều trải qua vòng đời xử lý bất đồng bộ:

```text
[ Upload / Scrape ]
        │
        ▼
   ┌─────────┐
   │ pending │ ──▶ Đưa vào hàng đợi Redis / Celery broker
   └────┬────┘
        │ Worker nhận tác vụ
        ▼
 ┌──────────────┐
 │  processing  │ ──▶ Trích xuất văn bản, OCR, bóc băng Whisper,
 └──────┬───────┘     Cắt đoạn (Chunking) & nhúng vector vào Qdrant
        │
        ├──────────────────────────────┐
        │ Thành công                   │ Lỗi không thể phục hồi
        ▼                              ▼
   ┌─────────┐                    ┌────────┐
   │  ready  │                    │ failed │
   └─────────┘                    └───┬────┘
   Sẵn sàng cho RAG & Study Tools     │ POST /documents/{id}/retry
                                      └───────┘
```

### 2.2 Các Định Dạng Hỗ Trợ & Kiểm Tra Hợp Lệ

API kiểm tra chữ ký nhị phân thực tế của tệp (magic bytes) bên cạnh việc kiểm tra phần mở rộng tên tệp.

| Định dạng | Phần mở rộng | MIME Type | Pipeline xử lý |
|---|---|---|---|
| **PDF** | `.pdf` | `application/pdf` | Trích xuất văn bản bằng PyMuPDF, phân tích bố cục, cắt chunk theo đoạn |
| **Word Document** | `.docx`, `.doc` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | Trích xuất văn bản, giữ phân cấp cấu trúc, cắt chunk |
| **Video** | `.mp4`, `.webm` | `video/mp4`, `video/webm` | Tách luồng âm thanh (FFmpeg), phiên âm Whisper, cắt chunk gắn timestamp |
| **Audio** | `.mp3`, `.wav` | `audio/mpeg`, `audio/wav` | Phiên âm giọng nói Whisper đồng bộ mốc thời gian |
| **Văn bản thuần** | `.txt` | `text/plain` | Cắt chunk ngữ nghĩa với cửa sổ trượt chồng lấp (sliding window overlap) |
| **Hình ảnh** | `.png`, `.jpg`, `.jpeg` | `image/png`, `image/jpeg` | Nhận dạng chữ OCR (Tesseract) và tạo vector ngữ nghĩa |

**Giới hạn tải lên:** Dung lượng tối đa: **100 MB**. Giới hạn tần suất: **5 lượt tải lên / phút**.

---

### 2.3 Hợp Đồng Tải Lên Tài Liệu

- **Đường dẫn:** `POST /api/v1/documents/upload`
- **Content-Type:** `multipart/form-data`
- **Mã trạng thái:** `202 Accepted`

#### Ví dụ cURL

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@/path/to/Deep_Learning_Overview.pdf"
```

#### Phản Hồi (`202 Accepted`)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "file_name": "Deep_Learning_Overview.pdf",
  "file_type": "pdf",
  "file_size": 3425120,
  "status": "processing",
  "created_at": "2026-09-14T08:00:00Z"
}
```

---

## 3. Quản Lý Khóa Học & Giáo Trình

### 3.1 Lược Đồ Thực Thể Khóa Học

```json
{
  "id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "lecturer_id": "e674b889-f5ce-4927-b952-b88dcfce6331",
  "category_id": "c1d2e3f4-a5b6-7c8d-9e0f-1a2b3c4d5e6f",
  "title": "Mastering Transformer Architectures",
  "description": "Comprehensive hands-on course covering Attention mechanisms, BERT, GPT, and ViT.",
  "thumbnail_url": "https://storage.learninghubs.tech/courses/thumbnails/transformer.png",
  "price_vnd": 499000,
  "status": "published",
  "level": "intermediate",
  "language": "vi",
  "requirements": ["Basic Python", "Linear Algebra fundamentals"],
  "learning_outcomes": ["Implement Multi-Head Attention from scratch", "Fine-tune LLMs"],
  "tags": ["AI", "Transformers", "PyTorch"],
  "view_count": 1420,
  "rating_avg": 4.85,
  "rating_count": 128,
  "created_at": "2026-08-01T00:00:00Z",
  "updated_at": "2026-09-10T12:00:00Z"
}
```

---

### 3.2 Tạo Bản Nháp Khóa Học

- **Đường dẫn:** `POST /api/v1/courses`
- **Xác thực:** Lecturer hoặc Admin
- **Mã trạng thái:** `201 Created`

#### Request Body

```json
{
  "title": "Mastering Transformer Architectures",
  "category_id": "c1d2e3f4-a5b6-7c8d-9e0f-1a2b3c4d5e6f",
  "description": "Comprehensive hands-on course covering Attention mechanisms.",
  "price_vnd": 499000,
  "level": "intermediate",
  "language": "vi",
  "requirements": ["Basic Python"],
  "learning_outcomes": ["Implement Attention from scratch"]
}
```

---

## 4. Ghi Danh & Theo Dõi Tiến Độ

### 4.1 Cấu Trúc Tiến Độ Ghi Danh

Truy xuất trạng thái hoàn thành tính trên tất cả bài học và học liệu bắt buộc.

- **Đường dẫn:** `GET /api/v1/enrollments/{enrollment_id}/progress`
- **Mã trạng thái:** `200 OK`

#### Phản Hồi (`200 OK`)

```json
{
  "enrollment_id": "880e8400-e29b-41d4-a716-446655440001",
  "course_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "total_materials": 12,
  "completed_materials": 9,
  "total_lessons": 10,
  "completed_lessons": 8,
  "completed_lesson_ids": [
    "f47ac10b-58cc-4372-a567-0e02b2c3d401",
    "f47ac10b-58cc-4372-a567-0e02b2c3d402"
  ],
  "completion_percent": 80,
  "materials": [
    {
      "id": "mat-prog-uuid-1",
      "enrollment_id": "880e8400-e29b-41d4-a716-446655440001",
      "material_id": "mat-uuid-1",
      "completion_percent": 100,
      "completed": true,
      "last_position": 620,
      "completed_at": "2026-09-12T10:00:00Z"
    }
  ]
}
```

### 4.2 Cập Nhật Tiến Độ Bài Học

Đánh dấu hoàn thành một bài học cụ thể cho học viên đang ghi danh.

- **Đường dẫn:** `POST /api/v1/enrollments/{enrollment_id}/lessons/{lesson_id}/progress`
- **Request Body:**
  ```json
  {
    "completed": true
  }
  ```

---

## 5. Hợp Đồng Vận Hành Giảng Dạy (Teaching Ops)

Các hợp đồng API phục vụ quy trình giảng dạy được định nghĩa tại [`lecturer-teaching-experience-tasks.md`](../../src/frontend/docs/lecturer-teaching-experience-tasks.md):

### 5.1 Chi Tiết Tiến Độ & Chẩn Đoán Học Tập Của Học Viên

Cho phép giảng viên xem tiến độ chi tiết của từng học viên qua các bài học và lượt làm bài kiểm tra.

- **Đường dẫn:** `GET /api/v1/courses/{course_id}/students/{student_id}/progress-summary` (hoặc `/progress-detail`)
- **Xác thực:** Giảng viên phụ trách khóa học hoặc Admin

#### Phản Hồi (`200 OK`)

```json
{
  "progress_percent": 35,
  "lessons": [
    {
      "id": "f47ac10b-58cc-4372-a567-0e02b2c3d401",
      "title": "1. Introduction to Attention",
      "completed": true
    },
    {
      "id": "f47ac10b-58cc-4372-a567-0e02b2c3d402",
      "title": "2. Multi-Head Implementation",
      "completed": false
    }
  ],
  "attempts": [
    {
      "id": "att-uuid-1",
      "quiz_id": "quiz-uuid-1",
      "title": "Module 1 Quiz",
      "score": 40,
      "max_score": 100,
      "passed": false,
      "duration": "15m",
      "date": "2026-09-10T14:30:00Z"
    }
  ]
}
```

---

### 5.2 Gửi Nhắc Nhở Học Tập

Gửi thông báo nhắc nhở tự động trong ứng dụng và qua email tới học viên có tiến độ thấp (ví dụ dưới 15%).

- **Đường dẫn:** `POST /api/v1/courses/{course_id}/students/{student_id}/remind` (hoặc `/reminders`)
- **Xác thực:** Giảng viên phụ trách khóa học hoặc Admin

#### Phản Hồi (`200 OK`)

```json
{
  "status": "ok",
  "message": "Reminder message sent."
}
```

---

### 5.3 Quản Lý Thông Báo Khóa Học (CRUD)

Đăng và quản lý các thông báo toàn khóa học, đồng thời tự động phát thông báo tới các học viên đã ghi danh.

- **Liệt kê thông báo:** `GET /api/v1/courses/{course_id}/announcements`
- **Đăng thông báo:** `POST /api/v1/courses/{course_id}/announcements`

#### Request Body Khi Đăng Thông Báo

```json
{
  "title": "Live Q&A Session Scheduled for Friday",
  "content": "We will be reviewing Transformer attention implementations live this Friday at 19:00 ICT.",
  "is_pinned": true
}
```

#### Phản Hồi (`201 Created`)

```json
{
  "id": "ann-uuid-101",
  "course_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "title": "Live Q&A Session Scheduled for Friday",
  "content": "We will be reviewing Transformer attention implementations...",
  "is_pinned": true,
  "created_at": "2026-09-14T09:00:00Z",
  "author_name": "Dr. Alex Nguyen"
}
```

---

### 5.4 Diễn Đàn Hỏi Đáp Bài Học (Q&A)

Thảo luận tương tác theo từng bài học, hỗ trợ giảng viên ghim bài viết, đánh dấu câu trả lời chính thức và bình chọn hữu ích.

- **Danh sách chủ đề Q&A:** `GET /api/v1/lessons/{lesson_id}/discussions`
- **Ghim chủ đề:** `PUT /api/v1/lessons/{lesson_id}/discussions/pin/{post_id}`
- **Đánh dấu đáp án chính thức:** `POST /api/v1/lessons/{lesson_id}/discussions/posts/{post_id}/mark-answer`
- **Bình chọn thảo luận:** `POST /api/v1/lessons/{lesson_id}/discussions/posts/{post_id}/upvote`

#### Cấu Trúc Chủ Đề Thảo Luận Q&A

```json
{
  "id": "disc-uuid-001",
  "lesson_id": "f47ac10b-58cc-4372-a567-0e02b2c3d402",
  "user_id": "student-uuid-456",
  "user_name": "Jane Doe",
  "user_avatar": "https://storage.learninghubs.tech/avatars/jane.png",
  "parent_id": null,
  "content": "Why do we scale the dot product by sqrt(d_k) in scaled dot-product attention?",
  "is_pinned": true,
  "is_answer": false,
  "upvotes": 14,
  "created_at": "2026-09-12T11:00:00Z",
  "replies": [
    {
      "id": "reply-uuid-002",
      "user_name": "Dr. Alex Nguyen (Lecturer)",
      "content": "For large values of d_k, dot products grow large in magnitude, pushing the softmax function into regions with extremely small gradients. Scaling by 1/sqrt(d_k) counteracts this effect.",
      "is_answer": true,
      "upvotes": 25,
      "created_at": "2026-09-12T11:30:00Z"
    }
  ]
}
```

---

### 5.5 Trợ Lý Giảng Dạy AI (AI Teaching Assistant)

Hỗ trợ giảng viên phác thảo dàn ý bài giảng, tạo bản tóm tắt và biên tập lời thoại bài học.

- **Đường dẫn:** `POST /api/v1/courses/{course_id}/ai-assist`
- **Xác thực:** Giảng viên phụ trách khóa học hoặc Admin

#### Request Body

```json
{
  "topic": "Multi-Head Attention PyTorch Implementation",
  "mode": "outline"
}
```

| Trường | Kiểu | Bắt buộc | Giá trị hợp lệ | Mô tả |
|---|---|---|---|---|
| `topic` | string | Có | Chuỗi văn bản | Chủ đề hoặc tiêu đề bài học. |
| `mode` | string | Có | `"outline"`, `"summary"`, `"transcript"` | Định dạng đầu ra mong muốn. |

#### Phản Hồi (`200 OK`)

```json
{
  "course_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "mode": "outline",
  "content": "### Lesson Plan: Multi-Head Attention\n\n1. Review of Scaled Dot-Product Formula\n2. Tensor Dimensions: (Batch, Seq_Len, Heads, D_k)\n3. Implementing Linear Projections with nn.Linear\n4. Splitting & Transposing Tensors\n5. Applying Causal Masking\n6. Concatenation and Output Projection"
}
```

---

### 5.6 Phân Tích Hiệu Quả Bài Kiểm Tra (Quiz Analytics)

Tổng hợp tỷ lệ trả lời sai và số lượt làm bài để phát hiện các chủ đề kiến thức học viên hay mắc lỗi trong khóa học.

- **Đường dẫn:** `GET /api/v1/courses/{course_id}/quiz-analytics`
- **Xác thực:** Giảng viên phụ trách khóa học hoặc Admin

#### Phản Hồi (`200 OK`)

```json
[
  {
    "question": "Which dimension represents the attention head count in PyTorch MultiheadAttention?",
    "wrongRate": 64.5,
    "attempts": 42
  },
  {
    "question": "Why is layer normalization applied before attention in Pre-LN Transformers?",
    "wrongRate": 48.0,
    "attempts": 42
  }
]
```

---

## 6. Tham Chiếu Mã Lỗi Phản Hồi

| Mã trạng thái | Chi tiết lỗi (`detail`) | Nguyên nhân phổ biến |
|---|---|---|
| **400 Bad Request** | `Unsupported file format: .xyz` | Phần mở rộng tệp không nằm trong danh sách cho phép |
| **400 Bad Request** | `Uploaded file content does not match expected signature` | Nội dung nhị phân giả mạo phần mở rộng tệp (lệch magic bytes) |
| **400 Bad Request** | `Storage quota exceeded` | Dung lượng tải lên vượt quá hạn mức còn lại của người dùng |
| **403 Forbidden** | `Active enrollment required to access course announcements` | Học viên chưa ghi danh nhưng cố truy cập thông báo khóa học |
| **403 Forbidden** | `Only course instructor or admin can pin a discussion` | Người không phải giảng viên phụ trách cố ghim bài thảo luận Q&A |
| **404 Not Found** | `Document not found` | ID tài liệu mục tiêu không tồn tại |
| **404 Not Found** | `Course not found` | ID khóa học mục tiêu không tồn tại |
| **413 Payload Too Large** | `File too large` | Tệp tải lên vượt quá 100 MB |
| **422 Unprocessable Entity** | `[{ "loc": ["body", "..."], ... }]` | Lỗi kiểm tra hợp lệ dữ liệu |
| **429 Too Many Requests** | `Rate limit exceeded` | Vượt quá giới hạn 5 lần tải lên/phút hoặc 60 truy vấn khóa học/phút |
