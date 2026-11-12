# Vị Việt

Website đặt món trực tuyến tích hợp trí tuệ nhân tạo gợi ý ẩm thực Việt Nam.

**Nhóm:** 14, lớp 65HTTT. **Học phần:** Hệ thống kinh doanh thông minh. **Nhánh làm việc:** `nhom14-65httt`.

## Trạng thái hiện tại

Repository đang ở giai đoạn đề cương. Đã có tài liệu đề xuất; các hướng dẫn và thư mục nguồn được chuẩn bị để phát triển tiếp. Chưa có website chạy được, cơ sở dữ liệu triển khai, mô hình đã huấn luyện hoặc dashboard đã nghiệm thu.

Thông tin thành viên được ghi tại [danhsachnhom.md](danhsachnhom.md). Cần hoàn thiện các trường đang đánh dấu trước khi xác nhận hồ sơ nộp đầy đủ.

## Vấn đề và mục tiêu

Hỗ trợ khách lựa chọn món Việt phù hợp khẩu vị và điều kiện phục vụ, thực hiện đặt món trong cùng website; kết nối dữ liệu tương tác với đơn hàng để chủ quán hiểu nhu cầu và chất lượng phục vụ. Các giả thuyết về khó khăn lựa chọn sẽ được kiểm chứng bằng khảo sát.

Hệ thống dự kiến phục vụ ba vai trò:

| Vai trò | Chức năng chính dự kiến |
| :--- | :--- |
| Khách hàng | Khai báo khẩu vị, chọn vị trí, tìm món và quán, nhận gợi ý có lý do, đặt món, theo dõi đơn và phản hồi |
| Chủ quán | Quản lý hồ sơ, giờ mở cửa, thực đơn, nguyên liệu, phạm vi phục vụ, trạng thái món và đơn hàng |
| Quản trị viên | Duyệt quán, quản lý danh mục, tài khoản, chất lượng dữ liệu và dashboard toàn hệ thống |

## Phạm vi bản mẫu

- Thử nghiệm tại một khu vực quanh trường ở Hà Nội; bán kính tìm kiếm mặc định 5 km, đồng thời phải thỏa phạm vi phục vụ của quán.
- Mỗi đơn thuộc một quán; quán tự giao, khách thanh toán khi nhận món.
- Chỉ quán tham gia hệ thống được nhận đơn qua website. Bản đồ hỗ trợ vị trí và chỉ đường; dữ liệu địa điểm không thay thế thực đơn.
- Gợi ý theo nội dung kết hợp khẩu vị, vị trí, khả dụng và phản hồi đã có; có phương án đối chứng để đánh giá.
- BI tập trung hành vi chọn món, phễu hiển thị–nhấp–đặt và trạng thái đơn.
- Công thức tự nấu, chatbot, lọc cộng tác, thanh toán trực tuyến và điều phối tài xế là hướng mở rộng.

## Dữ liệu và công nghệ dự kiến

ViFoodRec là nguồn chính cho đặc trưng món ăn. Dữ liệu quán, thực đơn kinh doanh, tình trạng món và giao dịch được quản lý riêng. Dataset PTIT chỉ xem xét bổ sung khi cần. Chi tiết nguồn và kế hoạch làm sạch tại [NGUON_DU_LIEU.md](docs/NGUON_DU_LIEU.md).

| Thành phần | Công nghệ dự kiến | Tình trạng |
| :--- | :--- | :--- |
| Giao diện web | React | Chưa triển khai |
| API nghiệp vụ và dịch vụ gợi ý | FastAPI/Python | Chưa triển khai |
| Cơ sở dữ liệu | PostgreSQL | Chưa triển khai |
| Xử lý đặc trưng và gợi ý | scikit-learn | Chưa triển khai |
| Báo cáo phân tích | Power BI | Chưa triển khai |

Phiên bản môi trường và thư viện sẽ được ghi lại khi nhóm bắt đầu lập trình.

## Các tài liệu và thư mục

| Đường dẫn | Mục đích |
| :--- | :--- |
| [danhsachnhom.md](danhsachnhom.md) | Thông tin thành viên, phân công dự kiến, môi trường và hướng dẫn lấy tài liệu |
| [docs/De_cuong_Vi_Viet.docx](docs/De_cuong_Vi_Viet.docx) | Đề cương project |
| [docs/NGUON_DU_LIEU.md](docs/NGUON_DU_LIEU.md) | Nguồn dữ liệu và quy tắc chuẩn bị |
| [docs/KE_HOACH_THUC_HIEN.md](docs/KE_HOACH_THUC_HIEN.md) | Lộ trình và tiêu chí đánh giá |
| [docs/CHECKLIST_NOP_BAI.md](docs/CHECKLIST_NOP_BAI.md) | Các mục cần kiểm tra trước nộp |
| [src/backend/README.md](src/backend/README.md) | Phạm vi backend dự kiến |
| [src/frontend/README.md](src/frontend/README.md) | Phạm vi frontend dự kiến |
| [src/database/README.md](src/database/README.md) | Phạm vi dữ liệu giao dịch và BI dự kiến |

## Lấy tài liệu và chạy dự án

Tại thư mục repository đã clone, sau khi xử lý các thay đổi đang làm dở:

```bash
git checkout nhom14-65httt
git pull --ff-only origin nhom14-65httt
```

Mở tài liệu trong `nhom14-65httt/docs/`. Hiện chưa có lệnh chạy ứng dụng. Hướng dẫn cài phụ thuộc, cấu hình, tạo cơ sở dữ liệu và chạy từng thành phần sẽ được bổ sung sau khi có mã nguồn và được kiểm tra thực tế.

## Cập nhật và nộp bài

Chỉ thêm hoặc sửa tệp bên trong `nhom14-65httt/`, làm việc trên nhánh cùng tên. Kiểm tra thay đổi trước khi commit:

```bash
git status
git add nhom14-65httt/
git diff --cached --stat
git commit -m "docs(nhom14-65httt): cap nhat tai lieu Vi Viet"
git push origin nhom14-65httt
```

Khi nộp PR, đích là `oanhcuongdo/project-htkdtm:main`, nguồn là `DucEvil/project-htkdtm:nhom14-65httt`. Nhóm không tự gộp vào nhánh chung; giảng viên kiểm duyệt theo quy định repository. Không đưa `.env`, khóa API, gói phụ thuộc hoặc tệp nén lớn lên Git.

