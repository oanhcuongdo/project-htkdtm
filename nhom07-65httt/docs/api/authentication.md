# Multimodal AI Learning Hub — Tài Liệu Tham Chiếu API: Xác Thực & Định Danh

**Phiên bản đặc tả:** 1.0.0  
**Cập nhật lần cuối:** 14/09/2026  
**Module mục tiêu:** `/api/v1/auth`  
**Cơ chế bảo mật:** HTTP Bearer JWT + HttpOnly Cookies

---

## 1. Tổng Quan Các Endpoint

| Phương thức | Đường dẫn | Yêu cầu xác thực | Mô tả |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | Không | Đăng ký tài khoản mới kèm hạn mức lưu trữ khởi tạo tự động |
| `POST` | `/api/v1/auth/login` | Không | Xác thực thông tin đăng nhập, nhận access token và refresh cookie |
| `POST` | `/api/v1/auth/logout` | Bearer Token | Hủy phiên hiện tại và xóa cookie xác thực |
| `POST` | `/api/v1/auth/refresh` | Cookie hoặc Body | Đổi refresh token lấy access token mới và refresh token xoay vòng |
| `POST` | `/api/v1/auth/google` | Không | Đăng nhập hoặc đăng ký bằng Google OAuth2 ID token |
| `POST` | `/api/v1/auth/facebook` | Không | Đăng nhập hoặc đăng ký bằng Facebook access token |
| `GET` | `/api/v1/auth/me` | Bearer Token | Lấy thông tin hồ sơ người dùng hiện tại và mức sử dụng hạn mức |
| `PUT` | `/api/v1/auth/me` | Bearer Token | Cập nhật thông tin hồ sơ (họ tên, URL ảnh đại diện) |
| `POST` | `/api/v1/auth/change-password` | Bearer Token | Đổi mật khẩu và vô hiệu hóa các phiên cũ trên mọi thiết bị |
| `POST` | `/api/v1/auth/forgot-password` | Không | Gửi yêu cầu email đặt lại mật khẩu |
| `POST` | `/api/v1/auth/reset-password` | Không | Đặt lại mật khẩu tài khoản bằng token xác minh |

---

## 2. Luồng Token & Kiến Trúc Bảo Mật

Nền tảng triển khai cơ chế xác thực hai token đạt chuẩn bảo mật doanh nghiệp:

```text
┌────────────────┐                     ┌─────────────────────┐
│ Trình duyệt    │                     │ Learning Hub API    │
└───────┬────────┘                     └──────────┬──────────┘
        │                                         │
        │ 1. POST /auth/login (email, password)   │
        │────────────────────────────────────────>│
        │                                         │ Xác thực & sinh token
        │ 2. Phản hồi: Access Token (JSON)        │
        │    + Set-Cookie: refresh_token (HttpOnly)
        │<────────────────────────────────────────│
        │                                         │
        │ 3. Gọi API (Header: Bearer JWT)         │
        │────────────────────────────────────────>│
        │                                         │ Kiểm tra chữ ký & token_version
        │ 4. 401 Unauthorized (Token hết hạn)     │
        │<────────────────────────────────────────│
        │                                         │
        │ 5. POST /auth/refresh (Cookie / Body)   │
        │────────────────────────────────────────>│
        │                                         │ Kiểm tra JTI & version của refresh token
        │                                         │ Thu hồi refresh token cũ (Redis)
        │ 6. Access Token mới + Cookie mới        │
        │<────────────────────────────────────────│
```

- **Access Token:** JWT ngắn hạn (30 phút), mang thông tin `sub` (UUID người dùng), `role` và `ver` (`token_version`).
- **Refresh Token:** JWT dài hạn (7 ngày) với `jti` UUID duy nhất được lưu theo dõi trong Redis để kiểm tra thu hồi.
- **Thông số Refresh Cookie:**
  - `Path=/api/v1/auth`
  - `HttpOnly=true` (JavaScript không thể truy cập)
  - `Secure=true` trên môi trường production (bắt buộc HTTPS)
  - `SameSite=None` trên production (hỗ trợ frontend chạy khác tên miền) hoặc `Lax` trên môi trường dev cục bộ.

---

## 3. Đặc Tả Chi Tiết Các Endpoint

### 3.1 Đăng Ký Tài Khoản

Tạo tài khoản học viên hoặc giảng viên mới. Các hạn mức tài nguyên mặc định (dung lượng lưu trữ, AI token, lượt tải video) được cấp phát ngay lập tức.

- **Đường dẫn:** `POST /api/v1/auth/register`
- **Giới hạn tần suất:** 10 yêu cầu / phút

#### Request Body

```json
{
  "email": "student@example.com",
  "password": "SecurePassword123!",
  "full_name": "Jane Doe",
  "role": "student"
}
```

| Trường | Kiểu | Bắt buộc | Ràng buộc | Mô tả |
|---|---|---|---|---|
| `email` | string | Có | Định dạng email hợp lệ | Email chính của người dùng (duy nhất). |
| `password` | string | Có | Tối thiểu 8 ký tự | Mật khẩu tài khoản. |
| `full_name` | string | Không | Tối đa 255 ký tự | Tên hiển thị của người dùng. |
| `role` | string | Không | `student` hoặc `lecturer` | Vai trò tài khoản (mặc định: `student`). Lưu ý: tài khoản giảng viên có thể cần quản trị viên phê duyệt trên production. |

#### Phản Hồi (`201 Created`)

```json
{
  "user": {
    "id": "e674b889-f5ce-4927-b952-b88dcfce6331",
    "email": "student@example.com",
    "full_name": "Jane Doe",
    "avatar_url": null,
    "role": "student",
    "oauth_provider": null,
    "created_at": "2026-09-14T08:00:00Z",
    "quota": {
      "storage_limit_mb": 1024,
      "storage_used_mb": 0.0,
      "video_limit": 10,
      "video_used": 0,
      "token_limit": 100000,
      "token_used": 0
    }
  },
  "token": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "refresh_token": null
  }
}
```

*Lưu ý: `refresh_token` đồng thời được thiết lập qua header phản hồi `Set-Cookie`.*

#### Ví dụ cURL

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "password": "SecurePassword123!",
    "full_name": "Jane Doe",
    "role": "student"
  }'
```

---

### 3.2 Đăng Nhập (Email & Mật Khẩu)

Xác thực bằng email và mật khẩu đã đăng ký.

- **Đường dẫn:** `POST /api/v1/auth/login`
- **Giới hạn tần suất:** 10 yêu cầu / phút

#### Request Body

```json
{
  "email": "student@example.com",
  "password": "SecurePassword123!"
}
```

#### Phản Hồi (`200 OK`)

```json
{
  "user": {
    "id": "e674b889-f5ce-4927-b952-b88dcfce6331",
    "email": "student@example.com",
    "full_name": "Jane Doe",
    "avatar_url": "https://storage.learninghubs.tech/avatars/jane.png",
    "role": "student",
    "oauth_provider": null,
    "created_at": "2026-09-14T08:00:00Z",
    "quota": {
      "storage_limit_mb": 1024,
      "storage_used_mb": 12.5,
      "video_limit": 10,
      "video_used": 1,
      "token_limit": 100000,
      "token_used": 4200
    }
  },
  "token": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "refresh_token": null
  }
}
```

#### Ví dụ cURL

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{
    "email": "student@example.com",
    "password": "SecurePassword123!"
  }'
```

---

### 3.3 Xoay Vòng Refresh Token

Lấy access token mới và một refresh token mới được xoay vòng. Refresh token cũ bị đưa ngay vào danh sách thu hồi (blacklist) trong Redis.

- **Đường dẫn:** `POST /api/v1/auth/refresh`
- **Giới hạn tần suất:** 60 yêu cầu / phút
- **Bảo vệ CSRF:** Các yêu cầu khác nguồn (cross-origin) từ trình duyệt phải khớp với `CORS_ORIGINS` được phép.

#### Request Body (Tùy chọn nếu đã có Cookie)

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Phản Hồi (`200 OK`)

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "refresh_token": null
}
```

*Lưu ý: Refresh token mới được cấp thông qua header `Set-Cookie`.*

#### Ví dụ cURL

```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -c cookies.txt
```

---

### 3.4 Đăng Xuất

Hủy phiên đăng nhập hiện tại và xóa cookie refresh token.

- **Đường dẫn:** `POST /api/v1/auth/logout`
- **Xác thực:** Bearer Token

#### Request Body (Tùy chọn)

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Phản Hồi (`200 OK`)

```json
{
  "message": "Logged out successfully"
}
```

---

### 3.5 Đăng Nhập Mạng Xã Hội (OAuth2)

Đổi token truy cập của nền tảng mạng xã hội lấy cặp JWT của hệ thống.

- **Đường dẫn Google:** `POST /api/v1/auth/google`
- **Đường dẫn Facebook:** `POST /api/v1/auth/facebook`

#### Google Request Body

```json
{
  "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjFhMmIzYy..."
}
```

#### Facebook Request Body

```json
{
  "access_token": "EAABsbCS1...long_facebook_access_token..."
}
```

#### Phản Hồi (`200 OK`)

Trả về cấu trúc `AuthResponse` chuẩn gồm `user` và `token`.

---

### 3.6 Lấy Hồ Sơ Người Dùng Hiện Tại

Truy xuất thông tin hồ sơ và mức sử dụng hạn mức hiện tại (được cache trong Redis để truy cập nhanh).

- **Đường dẫn:** `GET /api/v1/auth/me`
- **Xác thực:** Bearer Token

#### Phản Hồi (`200 OK`)

```json
{
  "id": "e674b889-f5ce-4927-b952-b88dcfce6331",
  "email": "student@example.com",
  "full_name": "Jane Doe",
  "avatar_url": "https://storage.learninghubs.tech/avatars/jane.png",
  "role": "student",
  "oauth_provider": null,
  "created_at": "2026-09-14T08:00:00Z",
  "quota": {
    "storage_limit_mb": 1024,
    "storage_used_mb": 15.2,
    "video_limit": 10,
    "video_used": 1,
    "token_limit": 100000,
    "token_used": 4200
  }
}
```

---

### 3.7 Cập Nhật Hồ Sơ

Cập nhật tên hiển thị và đường dẫn ảnh đại diện của người dùng.

- **Đường dẫn:** `PUT /api/v1/auth/me`
- **Xác thực:** Bearer Token

#### Request Body

```json
{
  "full_name": "Jane Doe-Smith",
  "avatar_url": "https://storage.learninghubs.tech/avatars/new-jane.png"
}
```

| Trường | Kiểu | Bắt buộc | Ràng buộc | Mô tả |
|---|---|---|---|---|
| `full_name` | string | Không | Tối đa 255 ký tự | Tên hiển thị mới. |
| `avatar_url` | string | Không | Tối đa 500 ký tự | URL ảnh đại diện mới. |

#### Phản Hồi (`200 OK`)

Trả về đối tượng `AuthUserResponse` đã cập nhật.

---

### 3.8 Đổi Mật Khẩu

Kiểm tra mật khẩu cũ, cập nhật bản băm mật khẩu mới, tăng `token_version` (thu hồi token trên các thiết bị khác) và cấp phiên mới cho thiết bị hiện tại.

- **Đường dẫn:** `POST /api/v1/auth/change-password`
- **Xác thực:** Bearer Token
- **Giới hạn tần suất:** 5 yêu cầu / phút

#### Request Body

```json
{
  "current_password": "SecurePassword123!",
  "new_password": "NewUltraSecurePassword456!"
}
```

#### Phản Hồi (`200 OK`)

```json
{
  "message": "Đổi mật khẩu thành công"
}
```

---

## 4. Quy Tắc Kiểm Tra Dữ Liệu Đầu Vào

| Thực thể | Trường | Quy tắc | Mô tả lỗi |
|---|---|---|---|
| `RegisterRequest` | `email` | `EmailStr` chuẩn RFC 5322 | `422 Unprocessable Entity` nếu sai định dạng |
| `RegisterRequest` | `password` | `min_length=8` | `422 Unprocessable Entity` nếu độ dài < 8 |
| `RegisterRequest` | `role` | Regex `^(student\|lecturer)$` | `422 Unprocessable Entity` nếu giá trị không hợp lệ |
| `LoginRequest` | `email` | `EmailStr` | `422 Unprocessable Entity` |
| `ChangePasswordRequest` | `new_password` | `min_length=8, max_length=128` | Phải khác `current_password` |
| `UpdateProfileRequest` | `avatar_url` | `max_length=500` | Độ dài URL không vượt quá 500 ký tự |

---

## 5. Tham Chiếu Mã Lỗi Phản Hồi

| Mã trạng thái | Chi tiết lỗi (`detail`) | Nguyên nhân phổ biến |
|---|---|---|
| **400 Bad Request** | `Email already registered` | Đăng ký bằng email đã tồn tại trong hệ thống |
| **400 Bad Request** | `Mật khẩu hiện tại không đúng` | Mật khẩu hiện tại sai khi đổi mật khẩu |
| **400 Bad Request** | `Mật khẩu mới phải khác mật khẩu hiện tại` | Mật khẩu mới trùng với mật khẩu đang dùng |
| **401 Unauthorized** | `Invalid email or password` | Sai email hoặc mật khẩu khi đăng nhập |
| **401 Unauthorized** | `Refresh token required` | Thiếu refresh token trong cookie hoặc body khi gọi `/refresh` |
| **401 Unauthorized** | `Refresh token has been revoked` | Sử dụng lại refresh token đã được xoay vòng hoặc thu hồi |
| **401 Unauthorized** | `Token invalidated. Please login again.` | Sai lệch `token_version` do người dùng đổi mật khẩu trên thiết bị khác |
| **403 Forbidden** | `Cross-origin request rejected` | Header `Origin` không thuộc danh sách tên miền CORS cho phép |
| **404 Not Found** | `User not found` | Người dùng trong token không còn tồn tại |
| **422 Unprocessable Entity** | `[{ "loc": ["body", "..."], "msg": "..." }]` | Dữ liệu đầu vào không hợp lệ theo kiểm tra Pydantic |
| **429 Too Many Requests** | `Rate limit exceeded` | Vượt ngưỡng 10 req/phút cho đăng nhập hoặc đăng ký |
| **503 Service Unavailable** | `Authentication service temporarily unavailable` | Mất kết nối Redis khi kiểm tra danh sách thu hồi token |
