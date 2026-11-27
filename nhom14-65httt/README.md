# Vị Việt

Website đặt món trực tuyến tích hợp trí tuệ nhân tạo gợi ý ẩm thực Việt Nam.

**Nhóm:** 14, lớp 65HTTT. **Học phần:** Hệ thống kinh doanh thông minh. **Nhánh làm việc:** `nhom14-65httt`.

## Trạng thái hiện tại

Đang triển khai theo từng phần của [thiết kế cấu trúc](docs/THIET_KE_CAU_TRUC.md) để nhóm commit riêng từng nội dung. Đã có nền tảng FastAPI, React/Vite/TypeScript, cấu hình môi trường, Docker, models F.5, migration `001`, ERD/từ điển dữ liệu, auth backend/frontend và API hồ sơ/duyệt quán, thực đơn/món chuẩn/nguyên liệu, tìm kiếm F.10.1–F.10.3. API đơn COD đã được bổ sung ở F.10.5; AI, ETL và dashboard triển khai sau; chưa có giao diện tìm kiếm hoặc quản lý thực đơn. Xem [tiến độ](docs/TIEN_DO_TRIEN_KHAI.md).

Thông tin thành viên được ghi tại [danhsachnhom.md](danhsachnhom.md). Cần hoàn thiện các trường đang đánh dấu trước khi xác nhận hồ sơ nộp đầy đủ.

Phần đơn hàng đã có API COD, snapshot giá, chống gửi lặp và chuyển trạng thái/lịch sử cùng transaction (F.10.4–F.10.5). Customer có thể gửi đánh giá món trong đơn completed qua API F.10.6; chưa có giao diện đơn hàng/đánh giá. Xem [README backend](src/backend/README.md#api-đơn-cod-và-idempotency).

Customer có thể lưu năm câu trả lời khẩu vị qua API F.10.7; bỏ qua không tạo hồ sơ. API F.10.8 tiếp nhận batch sự kiện tương tác và ghi nhận hiển thị thực tế; luồng sinh gợi ý và giao diện khai báo khẩu vị/tracking sẽ tích hợp sau.

Frontend F.11.1 đã có types và tám hàm gọi API đọc quán, món, danh mục, tìm kiếm, chuẩn bị cho các trang khách hàng F.12. Xem [README frontend](src/frontend/README.md#api-công-khai-đã-chuẩn-bị--f111); chưa có giao diện tìm kiếm/thực đơn.

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
| Giao diện web | React/Vite/TypeScript | Có đăng ký/đăng nhập, quản lý phiên, refresh, thông tin tài khoản và guard vai trò; chưa có trang giao dịch |
| API nghiệp vụ và dịch vụ gợi ý | FastAPI/Python | Có auth, hồ sơ/duyệt quán, thực đơn vendor, catalog admin, tìm món/quán theo chữ và khoảng cách, đơn COD, khẩu vị và nhận sự kiện tracking; chưa có API sinh gợi ý |
| Cơ sở dữ liệu | PostgreSQL | Có migration 001 tạo 15 bảng OLTP; đã thử SQLite và sinh SQL PostgreSQL, chưa chạy PostgreSQL thực tế |
| Xử lý đặc trưng và gợi ý | scikit-learn | Chưa triển khai |
| Báo cáo phân tích | Power BI | Chưa triển khai |

Yêu cầu Python >=3.11; Node.js 20.19+, 22.12+ hoặc 24+ theo `engines` frontend. Frontend có `package-lock.json`; phụ thuộc backend nằm trong `src/backend/requirements*.txt`.

## Các tài liệu và thư mục

| Đường dẫn | Mục đích |
| :--- | :--- |
| [danhsachnhom.md](danhsachnhom.md) | Thông tin thành viên, phân công dự kiến, môi trường và hướng dẫn lấy tài liệu |
| [docs/De_cuong_Vi_Viet.docx](docs/De_cuong_Vi_Viet.docx) | Đề cương project |
| [docs/NGUON_DU_LIEU.md](docs/NGUON_DU_LIEU.md) | Nguồn dữ liệu và quy tắc chuẩn bị |
| [docs/KE_HOACH_THUC_HIEN.md](docs/KE_HOACH_THUC_HIEN.md) | Lộ trình và tiêu chí đánh giá |
| [docs/CHECKLIST_NOP_BAI.md](docs/CHECKLIST_NOP_BAI.md) | Các mục cần kiểm tra trước nộp |
| [docs/ERD.md](docs/ERD.md) | Sơ đồ 15 bảng OLTP, quan hệ và quy tắc xóa |
| [docs/TU_DIEN_DU_LIEU.md](docs/TU_DIEN_DU_LIEU.md) | Từng cột, kiểu, mặc định, ràng buộc và giới hạn kiểm tra |
| [docs/API_CONTRACT.md](docs/API_CONTRACT.md) | Hợp đồng API auth và nghiệp vụ, gồm tracking; JWT, mã lỗi và giới hạn refresh |
| [src/backend/README.md](src/backend/README.md) | Phạm vi backend dự kiến |
| [src/frontend/README.md](src/frontend/README.md) | Phạm vi frontend dự kiến |
| [src/database/README.md](src/database/README.md) | Phạm vi dữ liệu giao dịch và BI dự kiến |

## Lấy tài liệu và chạy dự án

Tại thư mục repository đã clone, sau khi xử lý các thay đổi đang làm dở:

```bash
git checkout nhom14-65httt
git pull --ff-only origin nhom14-65httt
```

Xem [hướng dẫn cài đặt](docs/HUONG_DAN_CAI_DAT.md) để chạy local hoặc Docker. Frontend dùng cổng 5173, backend dùng cổng 8000. PostgreSQL/Docker và các chức năng ở phần sau chưa được nghiệm thu.

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

