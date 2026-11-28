# Multimodal AI Learning Hub — Tài Liệu Tham Chiếu API: Chat & Multimodal RAG

**Phiên bản đặc tả:** 1.0.0  
**Cập nhật lần cuối:** 14/09/2026  
**Module mục tiêu:** `/api/v1/chat`  
**Cơ chế bảo mật:** HTTP Bearer JWT  
**Giao thức hỗ trợ:** RESTful JSON + Server-Sent Events (SSE)

---

## 1. Tổng Quan Các Endpoint

| Phương thức | Đường dẫn | Yêu cầu xác thực | Mô tả |
|---|---|---|---|
| `POST` | `/api/v1/chat/sessions` | Bearer Token | Tạo phiên hội thoại mới theo ngữ cảnh tổng quát, khóa học hoặc bài học |
| `GET` | `/api/v1/chat/sessions` | Bearer Token | Liệt kê các phiên chat có phân trang của người dùng hiện tại |
| `DELETE` | `/api/v1/chat/sessions/{session_id}` | Bearer Token | Xóa một phiên chat và toàn bộ lịch sử hội thoại đã lưu |
| `GET` | `/api/v1/chat/sessions/{session_id}/messages` | Bearer Token | Lấy lịch sử tin nhắn và trích dẫn có phân trang của một phiên chat |
| `POST` | `/api/v1/chat/ask` | Bearer Token | Gửi câu hỏi đồng bộ và nhận câu trả lời AI kèm trích dẫn RAG |
| `POST` | `/api/v1/chat/ask/stream` | Bearer Token | Gửi câu hỏi và nhận luồng token sinh ra theo thời gian thực qua Server-Sent Events (SSE) |

---

## 2. Kiến Trúc Multimodal RAG

API Chat của Learning Hub tích hợp truy xuất vector và chuỗi xử lý AI đa phương thức:

```text
┌──────────────────────────────────────────────────────────────────────────┐
│                            Ứng Dụng Client                               │
└────────────┬────────────────────────────────────────────▲────────────────┘
             │ 1. POST /chat/ask/stream                   │ 7. Sự kiện SSE
             ▼                                            │ (tokens, citations)
┌─────────────────────────┐                               │
│   API Gateway (FastAPI) │                               │
├─────────────────────────┤                               │
│ • Kiểm tra hạn mức      │                               │
│ • Kiểm tra ghi danh     │                               │
│ • Bộ nhớ hội thoại      │                               │
└────────────┬────────────┘                               │
             │ 2. Chuyển tiếp kèm ngữ cảnh                │
             ▼                                            │
┌─────────────────────────┐                               │
│    AI Service Engine    │                               │
├─────────────────────────┤                               │
│ • Viết lại truy vấn     │                               │
│ • Tìm kiếm kết hợp:     │                               │
│   - Text Chunks (Qdrant)├──────────┐                    │
│   - Video Frames / Audio│          │ 4. Xếp hạng & Gộp  │
│   - Học liệu khóa học   │          ▼                    │
│ • Tổng hợp ngữ cảnh     │     ┌────────────┐            │
│ • Sinh câu trả lời LLM  │────>│ Trích dẫn  │────────────┘
└─────────────────────────┘     └────────────┘
```

---

## 3. Các Endpoint Quản Lý Phiên Chat

### 3.1 Tạo Phiên Chat

Khởi tạo một phiên hội thoại. Phiên chat có thể dùng chung hoặc giới hạn trực tiếp vào một khóa học/bài học (có kiểm tra trạng thái ghi danh).

- **Đường dẫn:** `POST /api/v1/chat/sessions`
- **Mã trạng thái:** `201 Created`

#### Request Body

```json
{
  "title": "Machine Learning Concept Clarification",
  "course_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "lesson_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "context_type": "course"
}
```

| Trường | Kiểu | Bắt buộc | Ràng buộc | Mô tả |
|---|---|---|---|---|
| `title` | string | Không | Tối đa 255 ký tự | Tiêu đề tùy chỉnh cho phiên chat. Tự động sinh nếu bỏ trống. |
| `course_id` | UUID | Không | UUID hợp lệ | Giới hạn ngữ cảnh hội thoại trong khóa học này. Yêu cầu đã ghi danh. |
| `lesson_id` | UUID | Không | UUID hợp lệ | Thu hẹp thêm ngữ cảnh về tài liệu của bài học này. |
| `context_type` | string | Không | Mặc định: `"general"` | Chế độ ngữ cảnh: `"general"`, `"course"`, hoặc `"lesson"`. |

#### Phản Hồi (`201 Created`)

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "course_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "lesson_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "title": "Machine Learning Concept Clarification",
  "context_type": "course",
  "created_at": "2026-09-14T08:15:00Z",
  "updated_at": "2026-09-14T08:15:00Z"
}
```

---

### 3.2 Liệt Kê Các Phiên Chat

Liệt kê danh sách phiên chat có phân trang thuộc về người dùng hiện tại, sắp xếp theo hoạt động gần nhất.

- **Đường dẫn:** `GET /api/v1/chat/sessions`
- **Mã trạng thái:** `200 OK`

#### Tham Số Truy Vấn

| Tham số | Kiểu | Mặc định | Mô tả |
|---|---|---|---|
| `page` | integer | `1` | Số trang (tối thiểu: 1). |
| `page_size` | integer | `20` | Số mục mỗi trang (tối thiểu: 1, tối đa: 100). |

#### Phản Hồi (`200 OK`)

```json
{
  "items": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "course_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
      "lesson_id": null,
      "title": "Deep Learning Architectures",
      "context_type": "course",
      "updated_at": "2026-09-14T08:20:00Z",
      "last_message": "What is the difference between CNN and Transformer backbones?"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

### 3.3 Xóa Phiên Chat

Xóa vĩnh viễn một phiên chat, toàn bộ lượt hỏi đáp và các mục cache liên quan.

- **Đường dẫn:** `DELETE /api/v1/chat/sessions/{session_id}`
- **Mã trạng thái:** `204 No Content`

---

### 3.4 Lấy Danh Sách Tin Nhắn Trong Phiên Chat

Truy xuất lịch sử tin nhắn và trích dẫn nguồn của một phiên chat (có phân trang).

- **Đường dẫn:** `GET /api/v1/chat/sessions/{session_id}/messages`
- **Mã trạng thái:** `200 OK`

#### Phản Hồi (`200 OK`)

```json
{
  "items": [
    {
      "id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "role": "user",
      "content": "Can you explain backpropagation mathematically?",
      "context_type": "course",
      "citations": null,
      "created_at": "2026-09-14T08:16:00Z"
    },
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "role": "assistant",
      "content": "Backpropagation computes the gradient of the loss function with respect to weights using the chain rule...",
      "context_type": "course",
      "citations": [
        {
          "document_id": "550e8400-e29b-41d4-a716-446655440000",
          "chunk_id": "chunk-102",
          "page_number": 42,
          "timestamp": null,
          "text": "The gradient of the loss with respect to weight W_ij is calculated via the chain rule of calculus...",
          "source_type": "pdf"
        }
      ],
      "created_at": "2026-09-14T08:16:05Z"
    }
  ],
  "total": 2,
  "page": 1,
  "page_size": 50
}
```

---

## 4. Các Endpoint Truy Vấn & Hỏi Đáp AI

### 4.1 Hỏi Đáp AI Đồng Bộ (`POST /chat/ask`)

Gửi câu hỏi tới hệ thống Multimodal RAG và nhận về toàn bộ câu trả lời tổng hợp kèm trích dẫn nguồn.

- **Đường dẫn:** `POST /api/v1/chat/ask`
- **Giới hạn tần suất:** 30 yêu cầu / phút
- **Mã trạng thái:** `200 OK`

#### Request Body

```json
{
  "session_id": "770e8400-e29b-41d4-a716-446655440002",
  "query": "How does multi-head attention work in Transformers?",
  "course_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "lesson_id": null,
  "document_ids": ["550e8400-e29b-41d4-a716-446655440000"],
  "tutor_mode": "standard",
  "strict_course": false
}
```

| Trường | Kiểu | Bắt buộc | Ràng buộc | Mô tả |
|---|---|---|---|---|
| `session_id` | UUID | Có | UUID hợp lệ | Mã định danh phiên chat. |
| `query` | string | Có | 1 – 5000 ký tự | Câu hỏi hoặc yêu cầu của người dùng. |
| `course_id` | UUID | Không | UUID hợp lệ | Mã khóa học tùy chọn để giới hạn kho tri thức. |
| `lesson_id` | UUID | Không | UUID hợp lệ | Mã bài học tùy chọn. |
| `document_ids` | UUID[] | Không | Mảng UUID | Danh sách tài liệu chỉ định cụ thể cho truy xuất vector. |
| `tutor_mode` | string | Không | Mặc định: `"standard"` | Phong cách gia sư: `"standard"`, `"socratic"`, `"exam_prep"`, `"concise"`. |
| `course_title` | string | Không | Tối đa 255 ký tự | Ghi đè tên khóa học khi tạo system prompt. |
| `strict_course`| boolean | Không | Mặc định: `false` | Nếu `true`, từ chối thông tin nằm ngoài học liệu khóa học đã ghi danh. |

#### Phản Hồi (`200 OK`)

```json
{
  "answer": "Multi-Head Attention allows the model to jointly attend to information from different representation subspaces at different positions...",
  "citations": [
    {
      "document_id": "550e8400-e29b-41d4-a716-446655440000",
      "chunk_id": "c98b671a-2849-410a-b68e-4a810eb0cfc2",
      "page_number": 5,
      "timestamp": null,
      "text": "Multi-head attention projects the queries, keys, and values h times with different, learned linear projections...",
      "source_type": "pdf"
    },
    {
      "document_id": "990e8400-e29b-41d4-a716-446655440001",
      "chunk_id": "video-transcription-seg-12",
      "page_number": null,
      "timestamp": 312.5,
      "text": "Notice how each head specializes in tracking different syntactic relationships.",
      "source_type": "video"
    }
  ],
  "token_usage": {
    "prompt_tokens": 1420,
    "completion_tokens": 280,
    "total_tokens": 1700
  }
}
```

#### Ví dụ cURL

```bash
curl -X POST "http://localhost:8000/api/v1/chat/ask" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "770e8400-e29b-41d4-a716-446655440002",
    "query": "How does multi-head attention work in Transformers?"
  }'
```

---

### 4.2 Hỏi Đáp AI Truyền Phát Trực Tiếp (`POST /chat/ask/stream`)

Truyền phát từng token câu trả lời và metadata theo thời gian thực qua Server-Sent Events (SSE), giúp giao diện chat phản hồi tức thì.

- **Đường dẫn:** `POST /api/v1/chat/ask/stream`
- **Giới hạn tần suất:** 30 yêu cầu / phút
- **Header yêu cầu:** `Accept: text/event-stream`

#### Request Body

Payload sử dụng cấu trúc `ChatAskRequest` giống hệt `/chat/ask`.

#### Giao Thức Server-Sent Events

Máy chủ đẩy các sự kiện theo định dạng `data: {JSON}\n\n`. Có ba loại thông điệp:

1. **Sự kiện `token`:** Phát cho từng đoạn token vừa được sinh ra.
2. **Sự kiện `meta`:** Phát sau khi truy xuất xong, chứa danh sách trích dẫn (`citations`).
3. **Sự kiện `done`:** Phát khi hoàn tất luồng kèm toàn văn câu trả lời tổng hợp.

#### Ví Dụ Chuỗi Sự Kiện Stream

```http
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

data: {"type": "meta", "citations": [{"document_id": "550e8400-e29b-41d4-a716-446655440000", "chunk_id": "chunk-1", "page_number": 5, "timestamp": null, "text": "Multi-head attention allows...", "source_type": "pdf"}]}

data: {"type": "token", "text": "Multi-Head "}

data: {"type": "token", "text": "Attention "}

data: {"type": "token", "text": "operates "}

data: {"type": "token", "text": "by running "}

data: {"type": "token", "text": "scaled dot-product attention in parallel."}

data: {"type": "done", "answer": "Multi-Head Attention operates by running scaled dot-product attention in parallel."}

```

#### Ví Dụ Tích Hợp Phía Client (TypeScript / Fetch)

```typescript
const response = await fetch("http://localhost:8000/api/v1/chat/ask/stream", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${token}`,
    "Accept": "text/event-stream",
  },
  body: JSON.stringify({
    session_id: sessionId,
    query: "Explain Multi-Head Attention",
  }),
});

const reader = response.body?.getReader();
const decoder = new TextDecoder();

while (reader) {
  const { done, value } = await reader.read();
  if (done) break;
  const chunk = decoder.decode(value);
  const lines = chunk.split("\n");
  for (const line of lines) {
    if (line.startsWith("data: ")) {
      const payload = JSON.parse(line.slice(6));
      if (payload.type === "token") {
        process.stdout.write(payload.text);
      } else if (payload.type === "meta") {
        console.log("\nCitations received:", payload.citations);
      } else if (payload.type === "done") {
        console.log("\nStream finished.");
      }
    }
  }
}
```

---

## 5. Đặc Tả Định Dạng Trích Dẫn (Citations)

Mỗi đối tượng trích dẫn trả về từ endpoint đồng bộ hoặc streaming đều tuân theo cấu trúc sau:

| Trường | Kiểu | Cho phép Null | Mô tả |
|---|---|---|---|
| `document_id` | UUID | Không | Mã định danh duy nhất của tài liệu nguồn lưu trên MinIO/PostgreSQL. |
| `chunk_id` | string / UUID | Không | Mã định danh đoạn văn bản cụ thể trong cơ sở dữ liệu vector Qdrant. |
| `page_number` | integer | Có | Số trang trong tài liệu PDF/DOCX (đánh số từ 1). `null` đối với audio/video. |
| `timestamp` | float | Có | Mốc thời gian tính bằng giây cho đoạn phiên âm video/audio. `null` đối với tài liệu văn bản. |
| `text` | string | Không | Trích đoạn nguyên văn từ tài liệu nguồn khớp với truy vấn. |
| `source_type` | string | Không | Loại nguồn: `"pdf"`, `"docx"`, `"video"`, `"audio"`, `"web"`. |

---

## 6. Bộ Chọn Ngữ Cảnh & Lọc Truy Vấn

Client có thể kiểm soát phạm vi truy xuất tài liệu qua nhiều cơ chế:

### 6.1 Chỉ Định Trực Tiếp Danh Sách Tài Liệu
Truyền mảng UUID tài liệu trong request body:
```json
{
  "document_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "660e8400-e29b-41d4-a716-446655440001"
  ]
}
```

### 6.2 Đính Thẻ Tài Liệu Trong Câu Hỏi (`@Document`)
Người dùng có thể nhắc trực tiếp tên tệp ngay trong câu hỏi:
```text
@Neural_Networks.pdf Công thức của hàm mất mát Cross-Entropy là gì?
```
Bộ tiền xử lý truy vấn ở backend sẽ nhận diện thẻ `@`, đối chiếu tên tệp với kho tài liệu của người dùng và tự động lọc truy xuất vào đúng tài liệu đó.

### 6.3 Cô Lập Tri Thức Khóa Học
Khi truyền `course_id` kèm `strict_course: true`, hệ thống RAG chỉ truy xuất trong phạm vi học liệu, bản ghi bài giảng và tệp đính kèm thuộc khóa học đó.

---

## 7. Tham Chiếu Mã Lỗi Phản Hồi

| Mã trạng thái | Chi tiết lỗi (`detail`) | Nguyên nhân phổ biến |
|---|---|---|
| **400 Bad Request** | `Course not available` | Khóa học đang ở trạng thái nháp và người gọi không phải giảng viên phụ trách |
| **400 Bad Request** | `Session course cannot be changed` | Cố tình truy vấn mã khóa học khác với khóa học đã gắn lúc tạo phiên chat |
| **400 Bad Request** | `Session lesson cannot be changed` | Cố tình ghi đè mã bài học đã khởi tạo của phiên |
| **403 Forbidden** | `Not enrolled in this course` | Người dùng truy vấn ngữ cảnh khóa học khi chưa ghi danh |
| **403 Forbidden** | `AI token quota exceeded` | Người dùng đã dùng hết hạn mức AI token được cấp |
| **404 Not Found** | `Session not found` | Mã phiên chat không tồn tại hoặc thuộc về người dùng khác |
| **404 Not Found** | `Course not found` | `course_id` truyền vào không tồn tại |
| **422 Unprocessable Entity** | `[{ "loc": ["body", "query"], ... }]` | Thiếu câu hỏi hoặc vượt quá 5000 ký tự |
| **429 Too Many Requests** | `Rate limit exceeded` | Vượt quá giới hạn 30 truy vấn mỗi phút |
| **503 Service Unavailable** | `AI service temporarily unavailable` | Dịch vụ AI bị timeout hoặc mất kết nối tới mô hình LLM |
