# Multimodal AI Learning Hub — Tài Liệu Tham Chiếu API: Quản Trị & Điều Hành Hệ Thống

**Phiên bản đặc tả:** 1.0.0  
**Cập nhật lần cuối:** 14/09/2026  
**Module mục tiêu:** `/api/v1/admin`, `/api/v1/categories`, `/health`  
**Cơ chế bảo mật:** HTTP Bearer JWT (`role: admin`)  
**Lớp bảo vệ phân quyền:** Dependency `require_admin` kèm cơ chế bảo vệ quản trị viên cuối cùng

---

## 1. Tổng Quan Các Endpoint

| Phương thức | Đường dẫn | Yêu cầu xác thực | Mô tả |
|---|---|---|---|
| **Quản trị người dùng** | | | |
| `GET` | `/api/v1/admin/users` | Admin JWT | Liệt kê tất cả người dùng đã đăng ký kèm phân trang, vai trò và trạng thái hoạt động |
| `POST` | `/api/v1/admin/users` | Admin JWT | Quản trị viên tạo trực tiếp tài khoản với vai trò tùy chọn và hạn mức lớn |
| `PUT` | `/api/v1/admin/users/{user_id}` | Admin JWT | Cập nhật vai trò, trạng thái hoạt động hoặc họ tên (có bảo vệ admin cuối cùng) |
| `DELETE` | `/api/v1/admin/users/{user_id}` | Admin JWT | Xóa vĩnh viễn tài khoản người dùng và dữ liệu liên quan |
| **Quản lý khóa học** | | | |
| `GET` | `/api/v1/admin/courses` | Admin JWT | Danh sách khóa học toàn hệ thống ở mọi trạng thái (nháp, đã xuất bản, lưu trữ) |
| `DELETE` | `/api/v1/admin/courses/{course_id}` | Admin JWT | Quản trị viên xóa cứng khóa học và toàn bộ đề cương bài giảng |
| **Phân loại danh mục** | | | |
| `GET` | `/api/v1/categories` | Bearer Token | Lấy danh sách danh mục dạng phẳng |
| `GET` | `/api/v1/categories/tree` | Bearer Token | Lấy cây phân cấp danh mục (có cache trong Redis) |
| `GET` | `/api/v1/categories/{category_id}` | Bearer Token | Xem chi tiết một danh mục cụ thể |
| `POST` | `/api/v1/categories` | Admin JWT | Tạo danh mục cấp cao nhất hoặc danh mục con mới |
| `PUT` | `/api/v1/categories/{category_id}` | Admin JWT | Cập nhật tên, slug, mô tả hoặc danh mục cha |
| `DELETE`| `/api/v1/categories/{category_id}` | Admin JWT | Xóa danh mục (`204 No Content`) |
| **Kho khóa AI & Xoay vòng** | | | |
| `GET` | `/api/v1/admin/ai-keys` | Admin JWT | Liệt kê tất cả khóa API AI đã cấu hình kèm chuỗi che dấu và bộ đếm sử dụng |
| `POST` | `/api/v1/admin/ai-keys` | Admin JWT | Lưu khóa API AI được mã hóa (Gemini, OpenAI, Groq, Anthropic) |
| `PATCH`| `/api/v1/admin/ai-keys/{key_id}/toggle`| Admin JWT | Bật/tắt trạng thái khóa và đồng bộ lại pool sang dịch vụ AI |
| `DELETE`| `/api/v1/admin/ai-keys/{key_id}` | Admin JWT | Xóa khóa API AI khỏi pool xoay vòng |
| **Chẩn đoán & Sức khỏe hệ thống** | | | |
| `GET` | `/api/v1/admin/analytics` | Admin JWT | Chỉ số tổng hợp toàn hệ thống (tổng người dùng, số tài liệu xử lý) |
| `GET` | `/api/v1/admin/health` | Admin JWT | Kiểm tra sức khỏe chuyên sâu (DB, Redis, AI service) |
| `GET` | `/health` | Công khai | Kiểm tra sống (liveness ping) mức nhẹ |
| `GET` | `/health/ready` | Công khai | Kiểm tra sẵn sàng (readiness probe) xác minh kết nối DB và Redis |

---

## 2. Kiểm Soát Truy Cập Theo Vai Trò Quản Trị (RBAC)

Mọi endpoint dưới `/api/v1/admin` đều bắt buộc kiểm tra vai trò nghiêm ngặt:

```python
async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin" or not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user
```

### Hàng Rào An Toàn (Bảo Vệ Quản Trị Viên Cuối Cùng)
Để tránh tình trạng vô tình khóa mất quyền quản trị toàn nền tảng, API tự động áp dụng:
1. **Chặn tự xóa tài khoản:** Quản trị viên không thể tự xóa chính tài khoản đang đăng nhập (`400 Bad Request: Cannot delete yourself`).
2. **Bảo vệ Admin cuối cùng:** API ngăn chặn thao tác vô hiệu hóa, hạ quyền hoặc xóa quản trị viên nếu chỉ còn duy nhất **1 quản trị viên đang hoạt động** trong cơ sở dữ liệu (`400 Bad Request: Cannot demote or deactivate the last active administrator`).

---

## 3. Các Endpoint Quản Lý Người Dùng

### 3.1 Liệt Kê Người Dùng

Lấy danh sách phân trang toàn bộ người dùng trên nền tảng.

- **Đường dẫn:** `GET /api/v1/admin/users`
- **Giới hạn tần suất:** 60 yêu cầu / phút
- **Tham số truy vấn:** `page` (mặc định 1), `page_size` (mặc định 20, tối đa 100)

#### Phản Hồi (`200 OK`)

```json
{
  "items": [
    {
      "id": "e674b889-f5ce-4927-b952-b88dcfce6331",
      "email": "student@example.com",
      "full_name": "Jane Doe",
      "role": "student",
      "is_active": true,
      "created_at": "2026-09-14T08:00:00Z"
    },
    {
      "id": "110e8400-e29b-41d4-a716-446655440000",
      "email": "admin@example.com",
      "full_name": "System Administrator",
      "role": "admin",
      "is_active": true,
      "created_at": "2026-01-01T00:00:00Z"
    }
  ],
  "total": 2,
  "page": 1,
  "page_size": 20
}
```

---

### 3.2 Tạo Tài Khoản Người Dùng

Quản trị viên tạo người dùng với bất kỳ vai trò nào (`student`, `lecturer`, `admin`) và tự động cấp hạn mức cấp cao (10 GB lưu trữ, 50 video, 2.000.000 AI token).

- **Đường dẫn:** `POST /api/v1/admin/users`
- **Mã trạng thái:** `201 Created`

#### Request Body

```json
{
  "email": "dr.nguyen@university.edu",
  "password": "TemporarySecurePassword123!",
  "full_name": "Dr. Alex Nguyen",
  "role": "lecturer"
}
```

#### Phản Hồi (`201 Created`)

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440011",
  "email": "dr.nguyen@university.edu",
  "full_name": "Dr. Alex Nguyen",
  "role": "lecturer",
  "is_active": true,
  "created_at": "2026-09-14T09:00:00Z"
}
```

---

### 3.3 Cập Nhật Trạng Thái & Vai Trò Người Dùng

Cập nhật vai trò, trạng thái kích hoạt hoặc họ tên. Kiểm tra điều kiện bảo vệ admin cuối cùng trước khi ghi thay đổi.

- **Đường dẫn:** `PUT /api/v1/admin/users/{user_id}`
- **Mã trạng thái:** `200 OK`

#### Request Body

```json
{
  "role": "lecturer",
  "is_active": true,
  "full_name": "Dr. Alex Nguyen, PhD"
}
```

---

### 3.4 Xóa Người Dùng

- **Đường dẫn:** `DELETE /api/v1/admin/users/{user_id}`
- **Mã trạng thái:** `204 No Content`

---

## 4. Quản Lý Cây Danh Mục Khóa Học

Danh mục quy định cách phân nhóm khóa học, lập chỉ mục tìm kiếm và lọc điều hướng.

### 4.1 Lấy Cây Danh Mục

Truy xuất cấu trúc danh mục phân cấp lồng nhau (được lưu đệm trong Redis).

- **Đường dẫn:** `GET /api/v1/categories/tree`
- **Mã trạng thái:** `200 OK`

#### Phản Hồi (`200 OK`)

```json
[
  {
    "id": "c1d2e3f4-a5b6-7c8d-9e0f-1a2b3c4d5e6f",
    "name": "Artificial Intelligence",
    "slug": "artificial-intelligence",
    "description": "Machine learning, deep learning, computer vision, and NLP courses.",
    "parent_id": null,
    "image_url": "https://storage.learninghubs.tech/categories/ai.png",
    "children": [
      {
        "id": "d2e3f4a5-b67c-8d9e-0f1a-2b3c4d5e6f7a",
        "name": "Natural Language Processing",
        "slug": "nlp",
        "description": "Transformers, LLMs, and language embeddings.",
        "parent_id": "c1d2e3f4-a5b6-7c8d-9e0f-1a2b3c4d5e6f",
        "image_url": null,
        "children": []
      }
    ]
  }
]
```

---

### 4.2 Tạo Danh Mục

- **Đường dẫn:** `POST /api/v1/categories`
- **Xác thực:** Admin JWT
- **Mã trạng thái:** `201 Created`

#### Request Body

```json
{
  "name": "Machine Learning",
  "slug": "machine-learning",
  "description": "Supervised, unsupervised, and reinforcement learning.",
  "parent_id": "c1d2e3f4-a5b6-7c8d-9e0f-1a2b3c4d5e6f",
  "image_url": "https://storage.learninghubs.tech/categories/ml.png"
}
```

---

## 5. Kho Khóa AI & Xoay Vòng Đa Nhà Cung Cấp

Nhằm đảm bảo độ sẵn sàng cao và tránh giới hạn tốc độ (rate limit) trên một khóa đơn lẻ, nền tảng duy trì pool khóa mã hóa hỗ trợ **Google Gemini**, **OpenAI**, **Groq** và **Anthropic**.

### Mô Hình Bảo Mật & Mã Hóa
- **Khi lưu trữ (At Rest):** Khóa bí mật được mã hóa đối xứng bằng Fernet thông qua `secret_store.py` trước khi lưu vào PostgreSQL.
- **Khi truyền tải (In Transit):** Toàn bộ API đọc chỉ trả về chuỗi khóa đã che (`AIza...1234` hoặc `sk-...a1b2`).
- **Đồng bộ hóa (Synchronization):** Mỗi khi tạo, bật/tắt hoặc xóa khóa, danh sách khóa đang hoạt động được đồng bộ ngay vào bộ nhớ của AI Service thông qua xác thực nội bộ (`X-Internal-API-Key`).
- **Đồng bộ lượt dùng:** Một tác vụ nền bất đồng bộ tổng hợp số lượt gọi và thời điểm dùng gần nhất từ AI Service về PostgreSQL mỗi 60 giây.

---

### 5.1 Liệt Kê Khóa AI

- **Đường dẫn:** `GET /api/v1/admin/ai-keys`
- **Tham số truy vấn:** `provider` (lọc tùy chọn: `gemini`, `openai`, `groq`, `anthropic`)
- **Mã trạng thái:** `200 OK`

#### Phản Hồi (`200 OK`)

```json
{
  "items": [
    {
      "id": "a5b6c7d8-e9f0-1a2b-3c4d-5e6f7a8b9c0d",
      "provider": "gemini",
      "key_name": "Configured Gemini model - Primary",
      "masked_key": "AIza...k91P",
      "is_active": true,
      "usage_count": 48210,
      "last_used_at": "2026-09-14T08:45:12Z",
      "created_at": "2026-08-01T00:00:00Z"
    },
    {
      "id": "b6c7d8e9-f01a-2b3c-4d5e-6f7a8b9c0d1e",
      "provider": "groq",
      "key_name": "Llama 3 70B Fast Inference",
      "masked_key": "gsk_...x72Q",
      "is_active": true,
      "usage_count": 19430,
      "last_used_at": "2026-09-14T08:40:02Z",
      "created_at": "2026-08-15T00:00:00Z"
    }
  ],
  "total": 2
}
```

---

### 5.2 Thêm Khóa Vào Pool Xoay Vòng

- **Đường dẫn:** `POST /api/v1/admin/ai-keys`
- **Mã trạng thái:** `201 Created`

#### Request Body

```json
{
  "provider": "openai",
  "key_name": "GPT-4o Mini RAG Rotation Key 1",
  "api_key": "sk-proj-example-placeholder-key-for-documentation"
}
```

| Trường | Kiểu | Bắt buộc | Ràng buộc | Mô tả |
|---|---|---|---|---|
| `provider` | string | Có | `gemini`, `openai`, `groq`, `anthropic` | Nhà cung cấp mô hình AI. |
| `key_name` | string | Có | Tối đa 100 ký tự | Nhãn mô tả mục đích sử dụng. |
| `api_key` | string | Có | Chuỗi khóa gốc | Khóa bí mật; được mã hóa ngay trước khi lưu. |

#### Phản Hồi (`201 Created`)

```json
{
  "id": "c7d8e9f0-1a2b-3c4d-5e6f-7a8b9c0d1e2f",
  "provider": "openai",
  "key_name": "GPT-4o Mini RAG Rotation Key 1",
  "masked_key": "sk-p...tion",
  "is_active": true,
  "usage_count": 0,
  "last_used_at": null,
  "created_at": "2026-09-14T09:10:00Z"
}
```

---

### 5.3 Bật / Tắt Trạng Thái Khóa AI

Kích hoạt hoặc tạm ngừng một khóa trong pool xoay vòng mà không xóa khỏi cơ sở dữ liệu.

- **Đường dẫn:** `PATCH /api/v1/admin/ai-keys/{key_id}/toggle`
- **Mã trạng thái:** `200 OK`

---

### 5.4 Xóa Khóa AI

Xóa vĩnh viễn khóa khỏi kho lưu trữ.

- **Đường dẫn:** `DELETE /api/v1/admin/ai-keys/{key_id}`
- **Mã trạng thái:** `204 No Content`

---

## 6. Kiểm Tra Sức Khỏe, Chẩn Đoán & Thống Kê Hệ Thống

### 6.1 Kiểm Tra Sức Khỏe Dành Cho Quản Trị Viên

Kiểm tra kết nối tới các thành phần hạ tầng trọng yếu gồm PostgreSQL, Redis và AI Service.

- **Đường dẫn:** `GET /api/v1/admin/health`
- **Xác thực:** Admin JWT
- **Mã trạng thái:** `200 OK`

#### Phản Hồi (`200 OK`)

```json
{
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "ai_service": "healthy"
  }
}
```

---

### 6.2 Các Probe Kiểm Tra Sống & Sẵn Sàng Công Khai

Phục vụ kiểm tra tình trạng container và bộ cân bằng tải (load balancer).

#### Liveness Probe
- **Đường dẫn:** `GET /health`
- **Xác thực:** Không
- **Phản hồi (`200 OK`):**
  ```json
  {
    "status": "healthy"
  }
  ```

#### Readiness Probe
- **Đường dẫn:** `GET /health/ready`
- **Xác thực:** Không
- **Phản hồi (`200 OK`):**
  ```json
  {
    "status": "ready",
    "dependencies": {
      "database": "healthy",
      "redis": "healthy"
    }
  }
  ```

---

### 6.3 Tổng Quan Thống Kê Hệ Thống

Trả về các chỉ số tổng hợp toàn nền tảng (được cache trong Redis trong 60 giây).

- **Đường dẫn:** `GET /api/v1/admin/analytics`
- **Xác thực:** Admin JWT
- **Mã trạng thái:** `200 OK`

#### Phản Hồi (`200 OK`)

```json
{
  "total_users": 154,
  "total_documents": 482,
  "documents_ready": 468,
  "documents_processing": 14
}
```

---

## 7. Tham Chiếu Mã Lỗi Phản Hồi

| Mã trạng thái | Chi tiết lỗi (`detail`) | Nguyên nhân phổ biến |
|---|---|---|
| **400 Bad Request** | `Cannot delete yourself` | Quản trị viên cố xóa tài khoản đang đăng nhập |
| **400 Bad Request** | `Cannot demote or deactivate the last active administrator` | Thao tác sẽ làm hệ thống còn 0 quản trị viên hoạt động |
| **400 Bad Request** | `Cannot delete the last active administrator` | Xóa mất quản trị viên hoạt động duy nhất |
| **403 Forbidden** | `Admin privileges required` | Người dùng có vai trò `student` hoặc `lecturer` |
| **404 Not Found** | `User not found` | ID người dùng mục tiêu không tồn tại |
| **404 Not Found** | `Course not found` | ID khóa học mục tiêu không tồn tại |
| **404 Not Found** | `API Key not found` | ID khóa AI mục tiêu không tồn tại |
| **409 Conflict** | `Email already registered` | Tạo người dùng với email đã tồn tại |
| **409 Conflict** | `Category slug already exists` | Trùng slug danh mục |
| **409 Conflict** | `API Key already exists` | Khóa giải mã bị trùng với bản ghi đã có trong CSDL |
| **422 Unprocessable Entity** | `[{ "loc": ["body", "..."], ... }]` | Lỗi kiểm tra dữ liệu đầu vào |
| **429 Too Many Requests** | `Rate limit exceeded` | Vượt quá giới hạn 60 yêu cầu / phút |
