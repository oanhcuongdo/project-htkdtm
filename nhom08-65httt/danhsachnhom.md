# Danh Sách Nhóm Và Phân Công Nhiệm Vụ

## 1. Thông Tin Chung

- **Tên nhóm:** `nhom08-65httt`
- **Tên lớp học phần:** Hệ thống Kinh doanh thông minh
- **Tên đề tài:** CafeFlow Market BI – Hệ thống thu thập và phân tích thị trường cà phê đa nguồn hỗ trợ lập kế hoạch thu mua
- **Giảng viên hướng dẫn:** TS. Đỗ Oanh Cường

---

## 2. Danh Sách Thành Viên

| STT | Họ và Tên         | Mã Sinh Viên | Lớp Sinh Hoạt | Vai Trò     | Nhiệm Vụ Phân Công                                                                                                                                                                                                             | Tỷ Lệ Đóng Góp (%) | Email                   |
| :-: | :---------------- | :----------: | :-----------: | :---------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :----------------: | :---------------------- |
|  1  | Bùi Đăng Huy      |  2351160528  |    65HTTT     | Nhóm trưởng | Khởi tạo nền tảng dùng chung và luồng dữ liệu ICO đầu tiên. Xây dựng kịch bản chi phí, cảnh báo và AI phân tích tin, tạo bản tin có dẫn chứng; phát triển màn hình kế hoạch, chốt hợp đồng API, tích hợp và kiểm thử hệ thống. |        100%        | lphan7024@gmail.com     |
|  2  | Bùi Gia Hiếu      |  2351160518  |    65HTTT     | Thành viên  | Tiếp nhận khung Django/Wagtail và Docker Compose ban đầu; hoàn thiện model, tài khoản, phân quyền, API nghiệp vụ, môi trường triển khai và workflow n8n.                                                                       |        100%        | Hieukks2k5@gmail.com    |
|  3  | Vũ Tuấn Hiệp      |  2351160517  |    65HTTT     | Thành viên  | Tiếp nhận, hoàn thiện collector ICO và mở rộng collector đa nguồn; phát triển ETL, kho dữ liệu, view KPI, kiểm tra chất lượng, xử lý bản sửa, chống trùng và đối chiếu nguồn.                                                  |        100%        | 2351160517@e.tlu.edu.vn |
|  4  | Dương Quỳnh Trang |  2351160559  |    65HTTT     | Thành viên  | Cấu hình ba dashboard Superset từ view có sẵn, bộ lọc và truy vấn SQL đối chiếu KPI; xuất cấu hình và chuẩn bị demo.                                                                                                           |        100%        | 2351160559@e.tlu.edu.vn |
|  5  | Lưu Tuấn Minh     |  2251162072  |    64HTTT1    | Thành viên  | Phát triển trang tin và form cập nhật trạng thái cảnh báo bằng template/API có sẵn; hỗ trợ kiểm tra mẫu AI và kiểm thử giao diện.                                                                                              |        100%        | 2251162072@e.tlu.edu.vn |

---

## 3. Cấu Trúc Mã Nguồn Trong Thư Mục Nhóm

Cấu trúc dự kiến khi nhóm triển khai mã nguồn:

```text
nhom08-65httt/
├── danhsachnhom.md
├── README.md
├── docs/
│   └── De_cuong_CafeFlow_Market_BI_Nhom8.docx
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

### 4.2. Cài đặt và khởi chạy

Clone fork của nhóm, chuyển sang nhánh `nhom08-65httt` và làm theo phần [Chạy luồng ICO trên Windows](README.md#chạy-luồng-ico-trên-windows) để tạo cấu hình, chạy Django/PostgreSQL và kiểm tra giá thu thập từ ICO. Các mốc cho Superset và n8n nằm trong [kế hoạch triển khai](docs/ke-hoach-trien-khai.md).
