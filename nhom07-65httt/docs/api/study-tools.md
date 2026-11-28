# Multimodal AI Learning Hub — Tài Liệu Tham Chiếu API: Công Cụ Học Tập & Đánh Giá AI

**Phiên bản đặc tả:** 1.0.0  
**Cập nhật lần cuối:** 14/09/2026  
**Module mục tiêu:** `/api/v1/study`  
**Cơ chế bảo mật:** HTTP Bearer JWT  
**Mô hình xử lý:** Hàng đợi tác vụ bất đồng bộ (Celery + Redis)

---

## 1. Tổng Quan Các Endpoint

| Phương thức | Đường dẫn | Yêu cầu xác thực | Mô tả |
|---|---|---|---|
| `POST` | `/api/v1/study/quiz/generate` | Bearer Token | Kích hoạt tác vụ sinh trắc nghiệm bất đồng bộ từ tài liệu cá nhân (`202 Accepted`) |
| `POST` | `/api/v1/study/quiz/by-course` | Bearer Token | Kích hoạt tác vụ sinh trắc nghiệm bất đồng bộ từ học liệu khóa học đã ghi danh (`202 Accepted`) |
| `GET` | `/api/v1/study/quiz/job/{job_id}` | Bearer Token | Kiểm tra tiến độ sinh quiz và lấy danh sách câu hỏi khi sẵn sàng |
| `GET` | `/api/v1/study/quiz/history` | Bearer Token | Liệt kê tất cả các bộ quiz đã lưu do người dùng hiện tại tạo |
| `GET` | `/api/v1/study/quiz/sets/{quiz_set_id}` | Bearer Token | Lấy câu hỏi, các phương án và metadata của một bộ quiz đã lưu |
| `DELETE` | `/api/v1/study/quiz/sets/{quiz_set_id}` | Bearer Token | Xóa vĩnh viễn một bộ quiz đã lưu (`204 No Content`) |
| `POST` | `/api/v1/study/quiz/{quiz_id}/submit` | Bearer Token | Nộp đáp án của học viên để chấm điểm và nhận phân tích kết quả |
| `POST` | `/api/v1/study/flashcards/generate` | Bearer Token | Sinh bộ thẻ ghi nhớ (flashcards) từ tài liệu (`201 Created`) |
| `GET` | `/api/v1/study/flashcards` | Bearer Token | Liệt kê lịch sử các bộ flashcard đã lưu kèm số lượng thẻ |
| `GET` | `/api/v1/study/flashcards/sets/{flashcard_id}` | Bearer Token | Lấy bộ flashcard và toàn bộ nội dung mặt trước/mặt sau |
| `DELETE` | `/api/v1/study/flashcards/{flashcard_id}` | Bearer Token | Xóa một bộ flashcard (`204 No Content`) |
| `POST` | `/api/v1/study/essay/submit` | Bearer Token | Nộp bài tự luận để AI chấm điểm đối chiếu với tài liệu gốc (`202 Accepted`) |
| `GET` | `/api/v1/study/essay/job/{job_id}` | Bearer Token | Kiểm tra trạng thái tác vụ chấm bài tự luận và nhận báo cáo đánh giá |

---

## 2. API Trình Tạo & Nộp Bài Trắc Nghiệm (Quiz)

### 2.1 Sinh Bộ Câu Hỏi Trắc Nghiệm Từ Tài Liệu

Khởi tạo tác vụ nền trên Celery để trích xuất các khái niệm trọng tâm từ tài liệu và sinh câu hỏi trắc nghiệm nhiều lựa chọn.

- **Đường dẫn:** `POST /api/v1/study/quiz/generate`
- **Giới hạn tần suất:** 30 yêu cầu / phút
- **Mã trạng thái:** `202 Accepted`

#### Request Body

```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "quiz_type": "quick",
  "question_count": 10
}
```

| Trường | Kiểu | Bắt buộc | Ràng buộc | Mô tả |
|---|---|---|---|---|
| `document_id` | UUID | Có | UUID hợp lệ | Tài liệu nguồn thuộc quyền sở hữu của người dùng. |
| `quiz_type` | string | Không | `quick` hoặc `detailed` | `quick` (kiểm tra nhanh) hoặc `detailed` (chuyên sâu khái niệm). Mặc định: `quick`. |
| `question_count`| integer| Không | Tối thiểu: 5, Tối đa: 20 | Số lượng câu hỏi cần sinh (mặc định: 10). |

#### Phản Hồi (`202 Accepted`)

```json
{
  "job_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "status": "processing"
}
```

---

### 2.2 Sinh Bộ Câu Hỏi Trắc Nghiệm Theo Khóa Học

Sinh đề trắc nghiệm tổng hợp từ học liệu của một khóa học hoặc các bài học được chọn.

- **Đường dẫn:** `POST /api/v1/study/quiz/by-course`
- **Mã trạng thái:** `202 Accepted`

#### Request Body

```json
{
  "course_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "lesson_ids": ["f47ac10b-58cc-4372-a567-0e02b2c3d479"],
  "quiz_type": "quick",
  "question_count": 10
}
```

---

### 2.3 Kiểm Tra Tiến Độ Sinh Quiz & Lấy Câu Hỏi

Truy vấn trạng thái của tác vụ nền. Khi trạng thái chuyển sang `"ready"`, các câu hỏi được tự động lưu bền vững vào PostgreSQL (`quiz_sets` và `quiz_questions`) để không bị mất sau khi khóa Redis hết hạn.

- **Đường dẫn:** `GET /api/v1/study/quiz/job/{job_id}`
- **Mã trạng thái:** `200 OK`

#### Phản Hồi: Đang Xử Lý (`status: "processing"`)

```json
{
  "job_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "status": "processing"
}
```

#### Phản Hồi: Hoàn Tất (`status: "ready"`)

```json
{
  "job_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "status": "ready",
  "quiz_set_id": "110e8400-e29b-41d4-a716-446655440099",
  "questions": [
    {
      "id": "220e8400-e29b-41d4-a716-446655440001",
      "question": "What is the primary function of the softmax activation function in neural networks?",
      "options": [
        "Normalizes outputs into a probability distribution over predicted classes",
        "Prevents the vanishing gradient problem in recurrent networks",
        "Applies non-linear thresholding by clamping values below zero",
        "Calculates the Euclidean distance between feature embeddings"
      ],
      "correct_answer": "A"
    }
  ]
}
```

---

### 2.4 Nộp Bài Trắc Nghiệm & Chấm Điểm

Chấm điểm các câu trả lời đã nộp dựa trên dữ liệu `quiz_questions` lưu trong PostgreSQL.

- **Đường dẫn:** `POST /api/v1/study/quiz/{quiz_id}/submit`
- **Mã trạng thái:** `200 OK`

#### Request Body

```json
{
  "answers": [
    {
      "question_id": "220e8400-e29b-41d4-a716-446655440001",
      "answer": "A"
    },
    {
      "question_id": "220e8400-e29b-41d4-a716-446655440002",
      "answer": "C"
    }
  ]
}
```

#### Phản Hồi (`200 OK`)

```json
{
  "score": 1,
  "total": 2,
  "percentage": 50.0,
  "results": [
    {
      "question_id": "220e8400-e29b-41d4-a716-446655440001",
      "correct": true,
      "correct_answer": "A",
      "your_answer": "A"
    },
    {
      "question_id": "220e8400-e29b-41d4-a716-446655440002",
      "correct": false,
      "correct_answer": "B",
      "your_answer": "C"
    }
  ]
}
```

---

## 3. Lưu Ý Quan Trọng Cho Lập Trình Viên: Định Dạng Đáp Án & Lỗi So Khớp

### 3.1 Vấn Đề Lệch Định Dạng Thường Gặp (Phân Tích Nguyên Nhân)

Trong kiến trúc AI Learning Hub, pipeline sinh đề AI trả về đáp án đúng dưới dạng **một chữ cái in hoa duy nhất**: `"A"`, `"B"`, `"C"`, hoặc `"D"`.

Một cách cài đặt ngây thơ ở frontend thường cố gắng tìm chỉ số phương án đúng bằng cách:

```javascript
// CÀI ĐẶT LỖI - TUYỆT ĐỐI KHÔNG DÙNG
const correctIndex = question.options.findIndex(opt => opt === question.correct_answer);
```

**Vì sao cách này bị sai:**  
`question.options` là mảng các chuỗi nội dung đầy đủ, ví dụ:  
`["Normalizes outputs into a probability distribution", "Prevents vanishing gradient", ...]`  
Phép so sánh `'Normalizes outputs...' === 'A'` luôn trả về `-1` (không tìm thấy). Khi UI mặc định `-1` thành `0`, phương án A sẽ bị đánh dấu đúng sai lệch cho mọi câu hỏi bất kể đáp án thực tế là gì.

### 3.2 Hợp Đồng Kiểm Tra Khi Nộp Bài

Trình kiểm tra phía backend bắt buộc đáp án nộp lên phải khớp biểu thức chính quy một ký tự:

```python
class QuizAnswerItem(BaseModel):
    question_id: UUID
    answer: str = Field(pattern="^[A-D]$")
```

Nếu client gửi chỉ số dạng số (`0`, `1`, `2`, `3`) hoặc toàn bộ chuỗi đáp án (`"Normalizes outputs..."`), API sẽ từ chối ngay lập tức với lỗi:  
`HTTP 422 Unprocessable Entity - Value should match pattern '^[A-D]$'`

### 3.3 Cách Triển Khai Khuyến Nghị Phía Client (TypeScript)

Để loại bỏ triệt để lỗi lệch định dạng, sử dụng bộ hàm chuyển đổi chuẩn hóa sau:

```typescript
// 1. Chuyển chữ cái từ Backend ("A"-"D") sang chỉ số mảng Options (0-3)
export function letterToIndex(letter: string): number {
  const clean = String(letter || "").trim().toUpperCase();
  const match = clean.match(/^([A-D])/);
  if (match) {
    return match[1].charCodeAt(0) - 65; // 'A' -> 0, 'B' -> 1, 'C' -> 2, 'D' -> 3
  }
  return -1;
}

// 2. Chuyển chỉ số phương án đã chọn (0-3) sang chữ cái nộp bài ("A"-"D")
export function indexToLetter(index: number): "A" | "B" | "C" | "D" {
  if (index < 0 || index > 3) {
    throw new Error(`Invalid option index: ${index}. Must be between 0 and 3.`);
  }
  return String.fromCharCode(65 + index) as "A" | "B" | "C" | "D";
}

// 3. Định dạng payload nộp bài
export function prepareQuizSubmission(
  answersMap: Record<string, number> // question_id -> selectedIndex (0..3)
) {
  return {
    answers: Object.entries(answersMap).map(([questionId, selectedIndex]) => ({
      question_id: questionId,
      answer: indexToLetter(selectedIndex),
    })),
  };
}
```

---

## 4. API Thẻ Ghi Nhớ (Flashcards)

### 4.1 Sinh Bộ Flashcards

Sinh các thẻ học tập (khái niệm mặt trước, giải thích mặt sau) từ tài liệu mục tiêu.

- **Đường dẫn:** `POST /api/v1/study/flashcards/generate`
- **Mã trạng thái:** `201 Created`

#### Request Body

```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "set_name": "Gradient Descent Key Terms",
  "count": 20
}
```

| Trường | Kiểu | Bắt buộc | Ràng buộc | Mô tả |
|---|---|---|---|---|
| `document_id` | UUID | Có | UUID hợp lệ | ID tài liệu nguồn. |
| `set_name` | string | Có | Tối đa 255 ký tự | Tiêu đề bộ flashcard. |
| `count` | integer | Không | Tối thiểu: 10, Tối đa: 50 | Tổng số thẻ cần sinh (mặc định: 20). |

#### Phản Hồi (`201 Created`)

```json
{
  "id": "330e8400-e29b-41d4-a716-446655440000",
  "set_name": "Gradient Descent Key Terms",
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "items": [],
  "created_at": "2026-09-14T08:30:00Z"
}
```

---

### 4.2 Lấy Bộ Flashcard & Danh Sách Thẻ

Truy xuất bộ flashcard đã lưu cùng toàn bộ các thẻ mặt trước/mặt sau.

- **Đường dẫn:** `GET /api/v1/study/flashcards/sets/{flashcard_id}` (hoặc `/api/v1/study/flashcards/{flashcard_id}`)
- **Mã trạng thái:** `200 OK`

#### Phản Hồi (`200 OK`)

```json
{
  "id": "330e8400-e29b-41d4-a716-446655440000",
  "set_name": "Gradient Descent Key Terms",
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "items": [
    {
      "id": "440e8400-e29b-41d4-a716-446655440001",
      "front": "Learning Rate (alpha)",
      "back": "A hyperparameter determining the step size at each iteration while moving toward a minimum of a loss function.",
      "last_reviewed": null
    }
  ],
  "created_at": "2026-09-14T08:30:00Z"
}
```

---

## 5. API Chấm Điểm & Đánh Giá Bài Tự Luận (Essay Grading)

### 5.1 Nộp Bài Tự Luận Để AI Chấm Điểm

Gửi nội dung bài viết tự luận của học viên để phân tích ngữ nghĩa bất đồng bộ đối chiếu với tài liệu tham chiếu.

- **Đường dẫn:** `POST /api/v1/study/essay/submit`
- **Giới hạn tần suất:** 30 yêu cầu / phút
- **Mã trạng thái:** `202 Accepted`

#### Request Body

```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "essay_text": "Gradient descent is an optimization algorithm used to minimize the loss function by iteratively moving in the direction of steepest descent..."
}
```

| Trường | Kiểu | Bắt buộc | Ràng buộc | Mô tả |
|---|---|---|---|---|
| `document_id` | UUID | Có | UUID hợp lệ | Tài liệu nguồn tham chiếu để đánh giá bài viết. |
| `essay_text` | string | Có | 1 – 50.000 ký tự | Toàn bộ nội dung bài tự luận của học viên. |

#### Phản Hồi (`202 Accepted`)

```json
{
  "job_id": "770e8400-e29b-41d4-a716-446655440999",
  "status": "processing"
}
```

---

### 5.2 Kiểm Tra Kết Quả Chấm Bài Tự Luận

Truy vấn trạng thái tác vụ chấm bài tự luận.

- **Đường dẫn:** `GET /api/v1/study/essay/job/{job_id}`
- **Mã trạng thái:** `200 OK`

#### Phản Hồi: Chấm Điểm Hoàn Tất (`status: "completed"`)

```json
{
  "job_id": "770e8400-e29b-41d4-a716-446655440999",
  "status": "completed",
  "submission_id": "880e8400-e29b-41d4-a716-446655440123",
  "score": 8.5,
  "max_score": 10.0,
  "feedback": "Comprehensive explanation of gradient descent mechanics and convergence criteria. To achieve full marks, detail the trade-offs between batch gradient descent and stochastic gradient descent (SGD).",
  "comparisons": [
    {
      "student_point": "Gradient descent updates parameters iteratively in the negative gradient direction.",
      "source_match": "Parameter weights are updated using W = W - alpha * dL/dW.",
      "similarity": 0.92,
      "assessment": "High semantic alignment. Demonstrates clear conceptual understanding."
    }
  ],
  "graded_at": "2026-09-14T08:35:00Z"
}
```

---

## 6. Tham Chiếu Mã Lỗi Phản Hồi

| Mã trạng thái | Chi tiết lỗi (`detail`) | Nguyên nhân phổ biến |
|---|---|---|
| **400 Bad Request** | `Invalid question count: must be between 5 and 20` | Số lượng câu hỏi vượt ngoài khoảng cho phép |
| **403 Forbidden** | `Access denied for document` | Người dùng không sở hữu tài liệu tham chiếu mục tiêu |
| **403 Forbidden** | `You must be enrolled to generate quiz from this course` | Người dùng chưa ghi danh khóa học được yêu cầu |
| **404 Not Found** | `Quiz job not found` | ID tác vụ không hợp lệ, đã hết hạn hoặc thuộc người dùng khác |
| **404 Not Found** | `Quiz not found` | Không tìm thấy `quiz_id` trong cơ sở dữ liệu hoặc cache |
| **404 Not Found** | `Flashcard set not found` | ID bộ flashcard không hợp lệ hoặc thuộc người dùng khác |
| **422 Unprocessable Entity** | `Value should match pattern '^[A-D]$'` | Đáp án nộp lên không phải một chữ cái in hoa `"A"`, `"B"`, `"C"` hoặc `"D"` |
| **422 Unprocessable Entity** | `[{ "loc": ["body", "essay_text"], ... }]` | Bài tự luận trống hoặc vượt quá 50.000 ký tự |
| **429 Too Many Requests** | `Rate limit exceeded` | Vượt quá giới hạn 30 yêu cầu tạo nội dung mỗi phút |
