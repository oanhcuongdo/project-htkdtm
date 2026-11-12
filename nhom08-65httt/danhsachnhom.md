# Danh Sách Nhóm Và Phân Công Nhiệm Vụ

## 1. Thông Tin Chung

- **Tên nhóm:** `nhom08-65httt`
- **Tên lớp học phần:** Hệ thống Kinh doanh thông minh
- **Tên đề tài:** CafeFlow BI và AI – Hệ thống kinh doanh thông minh hỗ trợ bán hàng cho quán cà phê và bánh
- **Giảng viên hướng dẫn:** TS. Đỗ Oanh Cường

---

## 2. Danh Sách Thành Viên

| STT | Họ và Tên | Mã Sinh Viên | Lớp Sinh Hoạt | Vai Trò | Nhiệm Vụ Phân Công | Tỷ Lệ Đóng Góp (%) | Email |
| :-: | :--- | :-: | :-: | :--- | :--- | :-: | :--- |
| 1 | Bùi Đăng Huy | 2351160528 | 65HTTT | Nhóm trưởng | Phát triển màn hình ghi đơn và tích hợp API lưu đơn. Xây dựng logic và API gợi ý combo theo luật kết hợp. Chốt hợp đồng API, tích hợp các nhánh và kiểm thử luồng ghi đơn có gợi ý | [ %] | lphan7024@gmail.com |
| 2 | Bùi Gia Hiếu | 2351160518 | 65HTTT | Thành viên | Phát triển model Wagtail/Django, quản lý danh mục và quyền, làm API lưu đơn và Docker Compose, kiểm tra kết nối MCP | [ %] | 2351160518@e.tlu.edu.vn |
| 3 | Vũ Tuấn Hiệp | 2351160517 | 65HTTT | Thành viên | Xây dựng ETL từ CSV và Open-Meteo, thiết kế Star Schema, đối soát dữ liệu và kiểm thử gợi ý có đối chứng | [ %] | 2351160517@e.tlu.edu.vn |
| 4 | Dương Quỳnh Trang | 2351160559 | 65HTTT | Thành viên | Cấu hình biểu đồ và bộ lọc trên Apache Superset, viết truy vấn SQL đối chiếu KPI | [ %] | 2351160559@e.tlu.edu.vn |
| 5 | Lưu Tuấn Minh | 2251162072 | 64HTTT1 | Thành viên | Làm biểu mẫu phản hồi bằng Django template, chuẩn bị mã đơn để kiểm thử và kiểm tra luồng giao diện | [ %] | 2251162072@e.tlu.edu.vn |

---

## 3. Cấu Trúc Mã Nguồn Trong Thư Mục Nhóm

Cấu trúc dự kiến khi nhóm triển khai mã nguồn:

```text
nhom08-65httt/
├── danhsachnhom.md
├── README.md
├── docs/
│   └── De_cuong_TH4_CafeFlow_Nhom8.docx
└── src/
    ├── backend/
    ├── frontend/
    └── database/
```

---

## 4. Hướng Dẫn Cài Đặt Và Thực Thi Mã Nguồn

### 4.1. Môi trường yêu cầu dự kiến

- Hệ điều hành phát triển: Windows 10/11 hoặc Ubuntu.
- Công cụ: Git và Docker Compose.
- Ứng dụng web: Python, Django và Wagtail.
- Cơ sở dữ liệu và báo cáo: PostgreSQL và Apache Superset.

### 4.2. Các bước cài đặt và khởi chạy dự kiến

1. Clone fork của nhóm và chuyển sang nhánh `nhom08-65httt`.
2. Tạo cấu hình môi trường từ tệp mẫu do nhóm cung cấp.
3. Khởi động các dịch vụ ứng dụng web, PostgreSQL và Superset bằng Docker Compose.
4. Chạy migration, nạp dữ liệu giao dịch và thời tiết, rồi kiểm tra ứng dụng và dashboard.

Nhóm sẽ bổ sung tên tệp cấu hình, câu lệnh và địa chỉ truy cập cụ thể sau khi cấu hình triển khai chạy thử thành công.