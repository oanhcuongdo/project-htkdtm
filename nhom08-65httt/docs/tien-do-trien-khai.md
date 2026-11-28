# Tiến độ triển khai CafeFlow Market BI

- **Dự án** CafeFlow Market BI, Nhóm 8, lớp 65HTTT, học phần Hệ thống Kinh doanh thông minh.
- **Nhóm trưởng** Bùi Đăng Huy.
- **Cập nhật** 28/11/2026, giờ Việt Nam, để chuẩn bị TH5 ngày 30/11/2026.
- **Mốc mã demo** Nhánh `nhom08-65httt`, CF-002B.1 tại `19c7b399dd8eaa657a376664b0da993e8a0e749b`. Trước khi tách commit, mốc CF-002A `d6d4601` khớp `origin/nhom08-65httt` sau fetch (0 trước, 0 sau).

## Nhiệm vụ và minh chứng

Mã R trong bảng cho biết phạm vi mà nhiệm vụ đóng góp. Trạng thái của một nhiệm vụ CF được dùng để theo dõi công việc. Xem [bảng nghiệm thu](theo-doi-nghiem-thu.md) để biết từng mã R đã đáp ứng tới đâu.

| Nhiệm vụ | Phụ trách | Mã R liên quan | Nội dung | Trạng thái | Kiểm thử hoặc minh chứng | Commit/PR |
| --- | --- | --- | --- | --- | --- | --- |
| Nền tảng ICO | Bùi Đăng Huy khởi tạo, Vũ Tuấn Hiệp và Bùi Gia Hiếu tiếp nhận theo phân công | R01–R07, R15–R17 | PDF ICO → raw/ETL → PostgreSQL → API và trang giá. Khung Django/Wagtail/DRF và Compose web/db. | Đã push, đã kiểm thử trong phạm vi nền tảng | 205 quan sát trong CSDL kiểm thử PostgreSQL từ hai PDF tháng 10 và 11. Đã thử nạp lặp, lỗi kết nối, khóa chạy chồng, đối chiếu giá SQL/API/trang và giữ dữ liệu qua stop/start. [Hồ sơ ICO](kiem-chung-ico.md) | [f63ee2e](https://github.com/DangHuy1302/project-htkdtm/commit/f63ee2ea605ed86e9193c904015ef4fb6cc28a91), [bàn giao c33dae6](https://github.com/DangHuy1302/project-htkdtm/commit/c33dae67da361cadecc539476ed480a3142c5633) |
| CF-001 | Bùi Đăng Huy | R01–R17 | Kiểm tra Git, phạm vi tệp, tình trạng mã và hồ sơ thử trước khi tiếp tục. | Hoàn thành rà soát | Nhánh khớp remote tại thời điểm kiểm tra, working tree sạch, không phát hiện tệp nhạy cảm theo mẫu quét, cú pháp 14 tệp Python qua. Kết quả runtime được đọc từ hồ sơ có sẵn. | Căn cứ [7b62b50](https://github.com/DangHuy1302/project-htkdtm/commit/7b62b50712e82708308b56a378b282fdafcfd8aa). CF-001 không tạo commit hoặc PR. |
| CF-002A | Bùi Đăng Huy | R16, R17 | Layout Django chung, menu tám mục, CSS và tích hợp trang giá. | Đã review, commit và push | Django check và static qua trên Windows/Docker. Kiểm tra CSDL rỗng và dữ liệu ICO, API, CMS tới trang đăng nhập và Chrome ở 1440/390/320 px. | [d6d4601](https://github.com/DangHuy1302/project-htkdtm/commit/d6d4601a0e5b886639fec5b584d8914d7c3dbbc7) |
| CF-002B.1 | Bùi Đăng Huy | R16, R17 | Tổng quan tại `/`, chuyển bảng giá sang `/market/`, điều hướng bằng named URL. Có vùng dành cho KPI, diễn biến giá, tình trạng nguồn và phân hệ. | Đã kiểm thử, duyệt và commit | Hai trang trả 200, menu active đúng, CSS và tuyến CMS qua, Chrome ở 1440/390/320 px. Bốn phản hồi API trước/sau khớp từng byte. Xác nhận lại các URL bằng HTTP chỉ đọc trong CF-DOC-001. | [19c7b39](https://github.com/DangHuy1302/project-htkdtm/commit/19c7b399dd8eaa657a376664b0da993e8a0e749b) |
| CF-002B.2–CF-002B.6 | Bùi Đăng Huy | R16, R17 | KPI ICO, biến động giá, tình trạng nguồn, biểu đồ và bộ kiểm thử tự động tổng quan. | Chưa triển khai trong phiên này | Thực hiện theo từng mốc sau khi nhóm trưởng xác nhận bắt đầu. | Chưa có |
| CF-002C | Bùi Đăng Huy điều phối | R16, R17 | Khung bàn giao route/template cho các phân hệ. | Chưa triển khai trong phiên này | Chờ chốt điểm tích hợp với người phụ trách theo [phân công](../danhsachnhom.md). | Chưa có |
| CF-DOC-001 | Bùi Đăng Huy review | R16, R17 | Nhật ký tiến độ, bảng nghiệm thu và kịch bản demo TH5. | Đã duyệt nội dung | Đối chiếu đề cương, Git, mã và hồ sơ kiểm thử. [Kịch bản demo](kich-ban-demo.md) phân biệt bản chạy thông thường với preview. | Xem các commit tài liệu CF-DOC-001 trong lịch sử nhánh. |

## Nhật ký kỹ thuật

| Ngày | Quyết định hoặc kết quả | Giới hạn và bước kế tiếp |
| --- | --- | --- |
| 28/11/2026 | Một backend Django, template render phía máy chủ và PostgreSQL. ICO lưu raw và log theo lần chạy, chỉ công bố giá hợp lệ qua API. | Hai tháng đã kiểm chứng, dưới mốc tối thiểu ba tháng. Ca nguồn sửa giá và PDF chứa dòng lỗi thực còn thiếu. Giacaphe, FX và tin mới ở mức khảo sát hoặc đặc tả. |
| 28/11/2026 | Layout dùng chung và named URL cho điều hướng. Giữ hợp đồng API giá khi chuyển route trang HTML. | Trang tổng quan chỉ có khung. Wagtail mới thử đến màn hình đăng nhập. Chưa xác nhận dừng web bình thường sau lần thoát mã `137` với `OOMKilled=false`. |
| 28/11/2026 | Demo TH5 có thể dùng bản build từ mốc CF-002B.1 hoặc preview đã kiểm tra. | Nhóm trưởng chốt bản demo, người trình bày và minh chứng phát sinh. Dữ liệu lịch sử kiểm thử và dữ liệu trong preview được ghi riêng. |

## Tiến độ và phụ thuộc theo thành viên

| Thành viên | Minh chứng hiện có | Phần tiếp theo hoặc phụ thuộc |
| --- | --- | --- |
| Bùi Đăng Huy | Commit nền tảng và layout, kiểm thử tích hợp luồng ICO. CF-002B.1 đã kiểm thử, duyệt và commit. | Kịch bản thu mua, rule cảnh báo, AI và tích hợp R17 cần dữ liệu chuẩn từ Hiệp và hợp đồng lưu/đọc từ Hiếu. |
| Bùi Gia Hiếu | Được bàn giao nền tảng backend/Compose theo [c33dae6](https://github.com/DangHuy1302/project-htkdtm/commit/c33dae67da361cadecc539476ed480a3142c5633). | Chốt API và quyền với Huy. Bàn giao tài khoản và API mẫu cho Minh. Workflow n8n cần lệnh tác vụ và hợp đồng log từ phần dữ liệu. |
| Vũ Tuấn Hiệp | Có [README giới thiệu](https://github.com/DangHuy1302/project-htkdtm/commit/a31f5c640449774851eed3823f7d829d4542501b), tiếp nhận pipeline nền tảng theo c33dae6. | Chốt quyền nguồn, mở rộng collector/ETL và bàn giao schema, view BI, mẫu đối chiếu cho Trang/Huy. |
| Dương Quỳnh Trang | Có [đặc tả dashboard](dac-ta-dashboard.md), [11614a2](https://github.com/DangHuy1302/project-htkdtm/commit/11614a29a8ccc81efed1c4f361bff9f0fb77509b). | Chờ view và mẫu sạch từ Hiệp, tài khoản chỉ đọc và môi trường Superset từ Hiếu để dựng và đối chiếu dashboard. |
| Lưu Tuấn Minh | Có [đặc tả giao diện tin và cảnh báo](dac-ta-tin-va-canh-bao.md), [8ad4843](https://github.com/DangHuy1302/project-htkdtm/commit/8ad484303d5aa001e12ecc21f3dae85ff62d7ab5). | Chờ API/tài khoản từ Hiếu, hợp đồng cảnh báo từ Huy và dữ liệu tin sạch từ Hiệp. |

Khi cập nhật, ghi ngày, người phụ trách, môi trường kiểm thử, kết quả và liên kết commit/PR. Nhóm trưởng xác nhận lịch và người trình bày TH5, sau đó bổ sung kết quả diễn tập và liên kết minh chứng nếu có. Phân công chính thức nằm trong [danh sách nhóm](../danhsachnhom.md) và [đề cương](De_cuong_CafeFlow_Market_BI_Nhom8.docx).
