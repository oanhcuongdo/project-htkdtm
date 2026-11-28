# Tài Khoản Mẫu & Tham Chiếu Phân Quyền — Multimodal AI Learning Hub

> Phiên bản: 2.0 | Cập nhật lần cuối: 14/09/2026 | Phụ trách: Platform Team | Trạng thái: Chính thức (Active)
> **An toàn kho lưu trữ công khai:** Tuyệt đối không lưu mật khẩu hoặc thông tin xác thực thật của môi trường production trong hệ thống quản lý phiên bản (Git).

Tài liệu này mô tả các vai trò người dùng tiêu chuẩn, cấp độ phân quyền truy cập và tài khoản thử nghiệm dùng để đánh giá nền tảng ở môi trường phát triển cục bộ (local) hoặc thử nghiệm (staging).

- **Cổng Production:** https://learninghubs.tech
- **Cổng Phát Triển Cục Bộ (Local Dev):** http://localhost:3000

---

## 1. So Sánh Tài Khoản Môi Trường Local Dev Và Production

| Khía cạnh | Phát triển cục bộ (Seed & E2E) | Môi trường Production |
|---|---|---|
| **Cách khởi tạo** | Khởi tạo qua script `src/backend/app/core/init_db.py` | Cấp phát qua migration cơ sở dữ liệu hoặc bảng điều khiển Admin |
| **Email Quản trị viên** | `admin@learninghub.com` | Cấu hình bởi người vận hành (ví dụ: `admin@learninghubs.tech`) |
| **Mật khẩu Admin** | Thiết lập qua biến môi trường `ADMIN_PASSWORD` (xem [README.md](../../README.md)) | Quản lý trong Secret Manager / biến môi trường cloud |
| **Tài khoản kiểm thử** | Tài khoản phục vụ kiểm thử E2E (`e2e_student@test.com`, `e2e_lecturer@test.com`) | Người dùng tự đăng ký hoặc đăng nhập SSO |
| **Phạm vi dữ liệu** | PostgreSQL trên Docker cục bộ (`src/compose.yaml`) | Cơ sở dữ liệu cloud được quản lý (PostgreSQL Neon) |

---

## 2. Hệ Thống Phân Cấp Vai Trò & Quyền Hạn Chuẩn

### 2.1 Admin (Quản Trị Viên Hệ Thống)

| Trường | Mô tả / Giá trị |
|---|---|
| **Mã vai trò (`role`)** | `admin` |
| **Đường dẫn chính** | `/app/admin` |
| **Tài khoản Local Dev** | `admin@learninghub.com` / *(Cấu hình qua biến `ADMIN_PASSWORD` khi chạy `init_db`)* |
| **Quyền hạn** | Toàn quyền quản trị hệ thống: quản lý người dùng & phân quyền RBAC, kiểm duyệt khóa học, quản lý cây danh mục, quản lý kho khóa AI Key Vault và theo dõi tình trạng dịch vụ. |
| **Hạn mức mặc định (do `init_db.py` cấp)** | 10 GB (`10240 MB`) lưu trữ · 50 video · 2.000.000 AI token |

> **Lưu ý bảo mật:** Trên môi trường production, tài khoản quản trị viên phải dùng mật khẩu mạnh, duy nhất và độ ngẫu nhiên cao. Không bao giờ commit mật khẩu thật của production vào kho lưu trữ mã nguồn.

### 2.2 Lecturer (Giảng Viên)

| Trường | Mô tả / Giá trị |
|---|---|
| **Mã vai trò (`role`)** | `lecturer` |
| **Đường dẫn chính** | `/app/lecturer/dashboard` |
| **Tài khoản Local Dev / E2E** | `e2e_lecturer@test.com` / `TestPass123!` *(Chỉ dùng cho dev cục bộ & kiểm thử)* |
| **Quyền hạn** | Biên soạn khóa học, quản lý chương/bài học, tải lên video/PDF, trợ lý AI phác thảo nội dung giảng dạy, tạo bài trắc nghiệm, không gian chấm bài và phân tích tiến độ học viên. |
| **Hạn mức khuyến nghị** | 5 GB lưu trữ · 1.000.000 AI token/tháng |

### 2.3 Student (Học Viên)

| Trường | Mô tả / Giá trị |
|---|---|
| **Mã vai trò (`role`)** | `student` |
| **Đường dẫn chính** | `/app/student/dashboard` |
| **Tài khoản Local Dev / E2E** | `e2e_student@test.com` / `TestPass123!` *(Chỉ dùng cho dev cục bộ & kiểm thử)* |
| **Cách đăng ký** | Tự đăng ký tại `/register` hoặc qua OAuth (Google, Facebook) |
| **Quyền hạn** | Duyệt và ghi danh khóa học, học tập tập trung (`/learn`), hỏi đáp gia sư RAG đa phong cách, sinh quiz & flashcard bằng AI, chấm bài tự luận tự động, sơ đồ tư duy và podcast tóm tắt. |
| **Hạn mức mặc định** | 500 MB – 1 GB lưu trữ · 100.000 AI token/tháng |

---

## 3. Danh Mục Điều Hướng Theo Vai Trò

| Vai trò | Phân hệ chức năng | Đường dẫn URL |
|---|---|---|
| **Admin** | Tổng quan hệ thống & Giám sát sức khỏe | `/app/admin` |
| **Admin** | Danh sách người dùng & Phân quyền RBAC | `/app/admin/users` |
| **Admin** | Kiểm duyệt khóa học & Danh mục | `/app/admin/courses` |
| **Admin** | Kho khóa AI Key Vault & Cấu hình hệ thống | `/app/admin/settings` |
| **Lecturer** | Bảng điều khiển giảng dạy & Chỉ số | `/app/lecturer/dashboard` |
| **Lecturer** | Biên soạn khóa học & Giáo trình | `/app/lecturer/courses` |
| **Lecturer** | Phân tích doanh thu & Lượt ghi danh | `/app/lecturer/analytics` |
| **Student** | Bảng điều khiển học tập & Phân tích điểm yếu | `/app/student/dashboard` |
| **Student** | Khám phá & Duyệt khóa học | `/app/courses` (hoặc `/app/student/browse`) |
| **Student** | Khóa học đã ghi danh & Chế độ tập trung | `/app/courses/my` |
| **Student** | Kho tài liệu cá nhân | `/app/student/documents` |
| **Student** | Trình tạo trắc nghiệm AI | `/app/student/quiz` |
| **Student** | Thẻ ghi nhớ tương tác (Flashcards) | `/app/student/flashcards` |
| **Student** | Chấm bài tự luận tự động | `/app/student/essay` |
| **Student** | Trò chuyện Gia sư AI (RAG) | `/app/student/chat` |
| **Student** | Nhắn tin bạn học & Nhóm học tập | `/app/student/friends-chat` |

---

## 4. Đăng Ký / Tạo Tài Khoản Qua API (Kiểm Thử)

```bash
# Đăng ký tài khoản học viên mới (môi trường local dev hoặc staging)
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student_test@example.com",
    "password": "<MAT_KHAU_MANH_CUA_BAN>",
    "full_name": "Hoc Vien Thu Nghiem",
    "role": "student"
  }'

# Tạo tài khoản giảng viên (yêu cầu Bearer token của Admin)
curl -X POST http://localhost:8000/api/v1/admin/users \
  -H "Authorization: Bearer <ADMIN_ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "lecturer_test@example.com",
    "password": "<MAT_KHAU_MANH_CUA_BAN>",
    "full_name": "Giang Vien Thu Nghiem",
    "role": "lecturer"
  }'
```

---

## 5. Quản Trị Bảo Mật & Thông Tin Bí Mật

1. **Không chứa bí mật production trong Git:** Tuyệt đối không lưu mật khẩu thật, chuỗi kết nối cloud hoặc khóa API bên thứ ba (Google Gemini, Groq, VNPay, MoMo) trong tệp này hay bất kỳ tệp nào trong kho mã nguồn.
2. **Nạp biến môi trường khi triển khai:** Mọi bí mật ở môi trường production được truyền qua biến môi trường của hạ tầng triển khai hoặc trình quản lý bí mật (Secret Manager).
3. **Xoay vòng mật khẩu:** Nếu nghi ngờ mật khẩu quản trị hoặc mật khẩu thử nghiệm bị lộ, cần đổi ngay qua trang Quản trị (`/app/admin/users`) hoặc cập nhật lại bản băm mật khẩu trực tiếp trong cơ sở dữ liệu.

---

*Xem thêm: [README.md](../../README.md) · [Mục lục tài liệu](../README.md) · [API Xác thực](../api/authentication.md)*
