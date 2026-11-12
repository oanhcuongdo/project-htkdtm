# Danh Sách Nhóm Và Phân Công Nhiệm Vụ

## 1. Thông Tin Chung

- **Tên nhóm:** nhom02-65httt
- **Tên lớp học phần:** Hệ thống kinh doanh thông minh
- **Tên đề tài:** Hệ thống ERP Smart Pricing đa kênh tích hợp AI & BI
- **Giảng viên hướng dẫn:** TS. Đỗ Oanh Cường

---

## 2. Danh Sách Thành Viên

| STT | Họ và Tên | Mã Sinh Viên | Lớp Sinh Hoạt | Vai Trò | Nhiệm Vụ Phân Công | Tỷ Lệ Đóng Góp (%) | Email |
| :-: | :--- | :-: | :-: | :--- | :--- | :-: | :--- |
| 1 | Nguyễn Anh Minh | 2351160537 | 65HTTT | Nhóm trưởng | Backend/Lead (khó): thiết kế kiến trúc, FastAPI, xác thực và phân quyền, tích hợp adapter, review code | [Điền tỷ lệ] | 2351160537@e.tlu.edu.vn |
| 2 | Lê Minh Tú | 2351160562 | 65HTTT | Thành viên | AI/ML (khó): tiền xử lý dữ liệu, baseline, mô hình dự báo nhu cầu, price optimizer, đánh giá MAE/RMSE; kiêm Frontend nâng cao: màn hình đề xuất giá và phê duyệt | [Điền tỷ lệ] | 2351160562@e.tlu.edu.vn |
| 3 | Nghiêm Xuân Trường | 2351160561 | 65HTTT | Thành viên | Automation/BI/QA (trung bình): Celery worker, adapter/simulator, 3 dashboard Apache Superset, test case và tài liệu | [Điền tỷ lệ] | 2351160561@e.tlu.edu.vn |
| 4 | Trần Đức Trung | 2251162191 | 64HTTT1 | Thành viên | ERP/Data (trung bình): CRUD sản phẩm, nhà cung cấp, tồn kho, schema PostgreSQL, seed data | [Điền tỷ lệ] | 2351160501@e.tlu.edu.vn |
| 5 | Nguyễn Thị Yên | 2351160567 | 65HTTT | Thành viên | Frontend cơ bản (dễ hơn): màn hình CRUD, bảng dữ liệu, tìm kiếm/lọc/phân trang, biểu mẫu nhập liệu | [Điền tỷ lệ] | 2351160567@e.tlu.edu.vn |

---

## 3. Cấu Trúc Mã Nguồn Trong Thư Mục Nhóm

```text
nhom02-65httt/
├── danhsachnhom.md       # Tệp tin thông tin nhóm
├── README.md             # Hướng dẫn cài đặt và chạy mã nguồn của nhóm
├── docs/                 # Tài liệu phân tích, thiết kế, báo cáo đồ án
│   └── decuong_doan.docx # Đề cương bài tập lớn
└── src/                  # Mã nguồn của dự án
    ├── backend/
    ├── frontend/
    └── database/
```

---

## 4. Hướng Dẫn Cài Đặt Và Thực Thi Mã Nguồn

### 4.1. Môi trường yêu cầu

- Hệ điều hành: Windows 10/11, Ubuntu 22.04
- Nền tảng thực thi: Node.js >= 18.x, Python >= 3.10
- Cơ sở dữ liệu: PostgreSQL 15
- Dịch vụ phụ trợ: Redis, Celery, Apache Superset
- Triển khai: Docker Compose

### 4.2. Các bước cài đặt và khởi chạy

1. Bước 1: Sao chép tệp cấu hình mẫu `.env.example` thành `.env` và điền tham số kết nối cơ sở dữ liệu, Redis, secret key.
2. Bước 2: Cài đặt các gói phụ thuộc cho backend và frontend.
3. Bước 3: Khởi chạy dịch vụ bằng Docker Compose (`docker compose up -d`).

> Phần này sẽ được cập nhật đầy đủ khi mã nguồn của nhóm được đưa vào thư mục `src/`.
