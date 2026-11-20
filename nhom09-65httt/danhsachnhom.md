# Danh Sách Nhóm Và Phân Công Nhiệm Vụ

## 1. Thông Tin Chung

- **Tên nhóm:** nhom09-65httt
- **Tên lớp học phần:** Hệ thống kinh doanh thông minh
- **Tên đề tài:** Hệ thống phân tích xu hướng lừa đảo trực tuyến và cảnh báo URL có dấu hiệu Phising
- **Giảng viên hướng dẫn:** ThS.Đỗ Oanh Cường

---

## 2. Danh Sách Thành Viên

| STT | Họ và Tên | Mã Sinh Viên | Lớp Sinh Hoạt | Vai Trò | Nhiệm Vụ Phân Công | Tỷ Lệ Đóng Góp (%) | Email |
| :-: | :--- | :-: | :-: | :--- | :--- | :-: | :--- |
| 1 | Nguyễn Thị Ngọc Ánh | 2351160506 | 65HTTT | Nhóm trưởng | Thiết kế kiến trúc, phát triển Backend API | 20% | nguyenngocanh2695@gmail.com |
| 2 | Đặng Thị Thu Hương | 2351160527 | 65HTTT | Thành viên | Thu thập dữ liệu (Scrapy/Requests), làm sạch và khử trùng lặp bài viết cảnh báo | 20% | b@student.edu.vn |
| 3 | Lê Duy Khánh | 2351160532 | 65HTTT | Thành viên |  Xây dựng mô hình NLP (PhoBERT) phân loại kịch bản lừa đảo từ bài viết | 20% | c@student.edu.vn |
| 4 | Nguyễn Minh Phú | 2351160540 | 65HTTT | Thành viên | Trích xuất đặc trưng chuỗi URL và huấn luyện mô hình ML (XGBoost/Random Forest) phát hiện Phishing. | 20% | c@student.edu.vn |
| 5 | Trần Quang Thịnh | 2351160555 | 65HTTT | Thành viên | Thiết kế Dashboard Power BI và phát triển giao diện Web Demo | 20% | c@student.edu.vn |

---

## 3. Cấu Trúc Mã Nguồn Trong Thư Mục Nhóm

Mã nguồn của nhóm phải được đặt trong thư mục này theo cấu trúc khuyến nghị:

```text
<tennhom-tenlop>/
├── danhsachnhom.md        # Tệp tin thông tin nhóm này
├── README.md              # (Tùy chọn) Hướng dẫn cài đặt và chạy mã nguồn của riêng nhóm
├── docs/                  # Tài liệu phân tích, thiết kế, báo cáo đồ án
│   └── baocao.pdf
└── src/                   # Mã nguồn của dự án
    ├── backend/
    └── frontend/
```

---

## 4. Hướng Dẫn Cài Đặt Và Thực Thi Mã Nguồn

### 4.1. Môi trường yêu cầu
- Hệ điều hành: [Ví dụ: Windows 10/11, Ubuntu 22.04]
- Nền tảng thực thi: [Ví dụ: Node.js >= 18.x, Python >= 3.10, JDK >= 17]
- Cơ sở dữ liệu: [Ví dụ: PostgreSQL 15, MySQL 8.0, MongoDB 6.0]

### 4.2. Các bước cài đặt và khởi chạy
1. Bước 1: Thiết lập cấu hình môi trường (sao chép tệp cấu hình mẫu và điền tham số).
2. Bước 2: Cài đặt các gói phụ thuộc.
3. Bước 3: Khởi chạy ứng dụng.
