# Multimodal AI Learning Hub — Tài Liệu Tham Chiếu API: Tổng Quan

**Phiên bản đặc tả:** 1.0.0  
**Cập nhật lần cuối:** 14/09/2026  
**Môi trường mục tiêu:** Phát triển cục bộ (Local Development) & Production  
**Đặc tả OpenAPI:** Có sẵn qua Swagger UI (`/docs`) và ReDoc (`/redoc`)

---

## 1. Tóm Tắt Tổng Quan

API của **Multimodal AI Learning Hub** cung cấp bộ endpoint RESTful và streaming toàn diện phục vụ xác thực người dùng, quản lý khóa học, xử lý tài liệu đa phương tiện, hội thoại **Retrieval-Augmented Generation (RAG)**, công cụ tự học thích ứng (trắc nghiệm, thẻ ghi nhớ, chấm bài tự luận) và quản trị hệ thống.

Mọi endpoint đều tuân thủ các nguyên tắc thiết kế API chuẩn doanh nghiệp:
- **Định phiên bản URL thống nhất:** Có tiền tố `/api/v1`.
- **Xác thực phi trạng thái (Stateless Authentication):** Dùng JSON Web Tokens (JWT) truyền qua HTTP header `Authorization: Bearer <token>` hoặc cookie `HttpOnly` bảo mật.
- **Kiểm tra dữ liệu đầu vào chặt chẽ:** Sử dụng mô hình Pydantic để sinh schema tự động và báo lỗi kiểm tra hợp lệ chi tiết.
- **Xử lý bất đồng bộ:** Các tác vụ tốn thời gian (vector hóa tài liệu, sinh nội dung AI, chấm bài tự luận) được chạy bất đồng bộ qua hàng đợi Celery trên nền tảng Redis.
- **Truyền phát thời gian thực:** Hỗ trợ Server-Sent Events (SSE) để đẩy từng token câu trả lời AI và trích dẫn theo thời gian thực.

---

## 2. Môi Trường & URL Cơ Sở

| Môi trường | URL cơ sở | Swagger UI | ReDoc |
|---|---|---|---|
| **Local Docker / Development** | `http://localhost:8000/api/v1` | `http://localhost:8000/docs` | `http://localhost:8000/redoc` |
| **OpenAPI Schema** | `/openapi.json` | - | - |

---

## 3. Tổng Quan Các Nhóm Endpoint

API được phân tách thành các phân hệ chức năng rõ ràng, ánh xạ tới các tài liệu đặc tả chi tiết dưới đây:

| Phân hệ | Đường dẫn gốc | Yêu cầu xác thực | Tài liệu đặc tả |
|---|---|---|---|
| **Xác thực & Hồ sơ** | `/api/v1/auth` | Công khai / Bearer JWT | [API Xác thực](./authentication.md) |
| **Chat & Multimodal RAG** | `/api/v1/chat` | Bearer JWT | [API Chat & RAG](./chat-and-rag.md) |
| **Công cụ học tập & Đánh giá AI** | `/api/v1/study` | Bearer JWT | [API Công cụ học tập](./study-tools.md) |
| **Tài liệu, Khóa học & Giảng dạy** | `/api/v1/documents`, `/api/v1/courses` | Công khai / Bearer JWT | [API Tài liệu & Khóa học](./documents-and-courses.md) |
| **Quản trị & Điều hành** | `/api/v1/admin`, `/api/v1/categories` | Admin Bearer JWT | [API Quản trị](./admin.md) |

---

## 4. Xác Thực & Phân Quyền

Toàn bộ các endpoint được bảo vệ đều yêu cầu header `Authorization` chứa Bearer JWT hợp lệ:

```http
Authorization: Bearer <access_token>
```

### Vòng Đời Token

- **Access Token:** Ký bằng HMAC-SHA256, thời hạn **30 phút**, truyền qua header.
- **Refresh Token:** Gắn mật mã với `token_version`, thời hạn **7 ngày**. Truyền qua cookie `HttpOnly`, `SameSite`, `Secure` (`refresh_token`) hoặc trong request body đối với client không phải trình duyệt.
- **Phiên bản hóa Token (`token_version`):** Mỗi lần đổi mật khẩu hoặc thu hồi phiên thủ công, `token_version` sẽ tăng lên để vô hiệu hóa ngay toàn bộ token cũ trên mọi thiết bị.

---

## 5. Định Dạng Phản Hồi Chuẩn

### 5.1 Phản Hồi Thành Công

Các truy vấn tài nguyên chuẩn trả về trực tiếp đối tượng thực thể hoặc tập hợp có kiểu dữ liệu rõ ràng:

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "title": "Introduction to Neural Networks",
  "status": "ready",
  "created_at": "2026-09-14T08:30:00Z"
}
```

Các endpoint thực thi hành động (như đổi trạng thái hoặc xác nhận xóa) trả về đối tượng thông báo mô tả:

```json
{
  "status": "ok",
  "message": "Operation completed successfully."
}
```

### 5.2 Phản Hồi Lỗi

Các lỗi tuân theo định dạng chuẩn của FastAPI:

```json
{
  "detail": "Descriptive error message explaining the cause of failure."
}
```

Đối với lỗi kiểm tra hợp lệ dữ liệu (`HTTP 422`), hệ thống trả về mảng chi tiết có cấu trúc:

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address: The email address is not valid.",
      "type": "value_error"
    }
  ]
}
```

---

## 6. Mã Trạng Thái HTTP Chuẩn

| Mã | Trạng thái | Mô tả |
|---|---|---|
| **200** | `OK` | Yêu cầu thành công và dữ liệu tài nguyên được trả về trong body. |
| **201** | `Created` | Tài nguyên đã được tạo mới thành công. |
| **202** | `Accepted` | Yêu cầu đã được tiếp nhận để xử lý bất đồng bộ (ví dụ: phân tích tài liệu, sinh quiz). |
| **204** | `No Content` | Yêu cầu thành công và không trả về nội dung body (ví dụ: thao tác `DELETE`). |
| **400** | `Bad Request` | Yêu cầu sai định dạng, vi phạm quy tắc nghiệp vụ hoặc chữ ký tệp không hợp lệ. |
| **401** | `Unauthorized` | Thiếu token, token không hợp lệ, đã hết hạn hoặc bị thu hồi. |
| **403** | `Forbidden` | Người dùng đã xác thực nhưng thiếu quyền hoặc chưa ghi danh khóa học được yêu cầu. |
| **404** | `Not Found` | Thực thể được yêu cầu không tồn tại hoặc không thuộc phạm vi người dùng hiện tại. |
| **409** | `Conflict` | Xung đột tài nguyên (ví dụ: trùng email, trùng slug duy nhất). |
| **413** | `Payload Too Large` | Tệp tải lên vượt quá ngưỡng tối đa cho phép (100 MB). |
| **422** | `Unprocessable Entity` | Dữ liệu đầu vào không vượt qua bước kiểm tra lược đồ Pydantic. |
| **429** | `Too Many Requests` | Vượt quá giới hạn tần suất yêu cầu cho endpoint hoặc địa chỉ IP. |
| **500** | `Internal Server Error` | Lỗi ngoài ý muốn từ phía máy chủ hoặc cơ sở dữ liệu. |
| **503** | `Service Unavailable` | Dịch vụ phụ thuộc phía sau (Redis, AI Service, Qdrant) tạm thời không khả dụng. |

---

## 7. Chuẩn Phân Trang

Mọi endpoint có phân trang đều hỗ trợ các tham số truy vấn chuẩn sau:

| Tham số | Kiểu | Mặc định | Ràng buộc | Mô tả |
|---|---|---|---|---|
| `page` | integer | `1` | `ge=1` | Số trang hiện tại (đánh số từ 1). |
| `page_size` | integer | `20` | `ge=1, le=100` | Số lượng phần tử trên mỗi trang. |

### Cấu Trúc Phản Hồi Phân Trang

```json
{
  "items": [
    {
      "id": "e674b889-f5ce-4927-b952-b88dcfce6331",
      "title": "Machine Learning Foundations"
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 20
}
```

---

## 8. Chính Sách Giới Hạn Tần Suất (Rate Limiting)

Giới hạn tần suất được áp dụng tại tầng API Gateway thông qua Redis và `slowapi`:

| Nhóm / Endpoint | Giới hạn | Phạm vi áp dụng |
|---|---|---|
| `/auth/login` | 10 yêu cầu / phút | IP người dùng |
| `/auth/register` | 10 yêu cầu / phút | IP người dùng |
| `/auth/*` (Các endpoint xác thực chung) | 60 yêu cầu / phút | IP người dùng |
| `/chat/ask`, `/chat/ask/stream` | 30 yêu cầu / phút | User ID / IP người dùng |
| `/documents/upload` | 5 yêu cầu / phút | User ID |
| `/study/*` (Sinh Quiz/Flashcard/Chấm bài luận) | 30 yêu cầu / phút | User ID |
| `/admin/*` | 60 yêu cầu / phút | Admin User ID |

Khi vượt ngưỡng cho phép, máy chủ trả về mã HTTP `429 Too Many Requests` kèm header `Retry-After`.

---

## 9. Hướng Dẫn Tích Hợp Nhanh Cho Client

### 9.1 cURL

```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer <access_token>" \
  -H "Accept: application/json"
```

### 9.2 TypeScript / Axios

```typescript
import axios from "axios";

const apiClient = axios.create({
  baseURL: "http://localhost:8000/api/v1",
  withCredentials: true, // bắt buộc để gửi nhận cookie HttpOnly refresh_token
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

---

## 10. Danh Mục Tài Liệu Đặc Tả Chi Tiết

Định nghĩa schema chi tiết, tham số và hợp đồng phản hồi được lưu trong các tệp sau:

1. [API Xác thực (Authentication)](./authentication.md) — Đăng ký, đăng nhập mật khẩu, OAuth mạng xã hội, xoay vòng refresh token, cập nhật hồ sơ.
2. [API Chat & RAG](./chat-and-rag.md) — Vòng đời phiên chat, hỏi đáp đồng bộ, luồng SSE, trích dẫn đa nguồn, chọn ngữ cảnh.
3. [API Công cụ học tập (Study Tools)](./study-tools.md) — Sinh quiz AI, nộp bài & chấm điểm, quản lý flashcard, chấm bài tự luận, quy tắc định dạng đáp án.
4. [API Tài liệu & Khóa học](./documents-and-courses.md) — Nạp tệp, lưu trữ MinIO, soạn khóa học, theo dõi tiến độ, thông báo, diễn đàn hỏi đáp bài học.
5. [API Quản trị (Admin)](./admin.md) — Quản lý vai trò người dùng, quản lý khóa học, cây danh mục, kho khóa API AI mã hóa, chẩn đoán hệ thống.
