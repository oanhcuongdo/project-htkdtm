
# Thiết kế Data Warehouse & Business Intelligence

## 1. Mục tiêu
Thiết kế kho dữ liệu phục vụ phân tích kết quả học tập,
theo dõi chất lượng đào tạo và hỗ trợ ra quyết định.

## 2. Mô hình dữ liệu đề xuất
Sử dụng Star Schema (lược đồ hình sao).

### Bảng Fact
Fact_KetQuaHocTap

Mức chi tiết: Một sinh viên - một học phần - một học kỳ.

Các chỉ số dự kiến:
- Điểm tổng kết
- Số tín chỉ
- Số lần đạt / không đạt

### Bảng Dimension
- Dim_SinhVien
- Dim_HocPhan
- Dim_HocKy
- Dim_GiangVien

## 3. KPI đề xuất
- Điểm trung bình theo học kỳ
- Tỷ lệ sinh viên đạt học phần
- Tỷ lệ sinh viên không đạt
- Xu hướng kết quả học tập theo thời gian

## 4. Công cụ dự kiến
- SQL để xử lý và tổng hợp dữ liệu
- Power BI để trực quan hóa
- Quy trình ETL để đưa dữ liệu vào kho

## 5. Công việc tiếp theo
- Xác định dữ liệu nguồn
- Thiết kế chi tiết Star Schema
- Xây dựng ETL
- Tạo dashboard BI
- Kiểm tra kết quả phân tích

Lưu ý: Đây là thiết kế sơ bộ, cần thống nhất với nhóm
và điều chỉnh theo dữ liệu thực tế.
