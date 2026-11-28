# Theo dõi nghiệm thu CafeFlow Market BI

Các cột **Đầu ra**, **Điều kiện hoàn thành và minh chứng** và **Chủ trì** trích từ mục 16.2 của [đề cương hiện hành](De_cuong_CafeFlow_Market_BI_Nhom8.docx). Cột trạng thái dùng ký hiệu của đề cương và phản ánh bằng chứng đã rà ngày 28/11/2026. Ngày trong bảng là ngày kiểm tra minh chứng.

| Ký hiệu | Ý nghĩa |
| --- | --- |
| CXN | Chưa xác nhận triển khai |
| ĐL | Đang làm, có commit |
| CKT | Chờ kiểm thử |
| ĐNT | Đã nghiệm thu, có minh chứng |

Một mốc CF hoàn thành có thể cung cấp minh chứng cho một phần đầu ra. Các dòng ĐL dưới đây có commit hoặc tài liệu kiểm chứng đầu ra đang thực hiện. Bản đặc tả chưa đi kèm triển khai giữ CXN. Chỉ chuyển ĐNT khi đáp ứng đủ tiêu chí và nhóm trưởng xác nhận minh chứng. **Hiện có 0/17 đầu ra ĐNT.**

## Bảng R01–R17

| Mã | Đầu ra | Điều kiện hoàn thành và minh chứng | Chủ trì | Trạng thái | Minh chứng, kết quả đã kiểm tra và phần còn thiếu | Ngày kiểm tra |
| --- | --- | --- | --- | --- | --- | --- |
| R01 | Nguồn và quyền | Danh mục URL, loại giá, lịch chạy, trường dữ liệu và điều khoản; ghi rõ nguồn kỳ hạn trực tiếp/công bố lại. Có biên bản chốt nguồn. | Hiệp, Huy phối hợp | ĐL | [Hồ sơ ICO](kiem-chung-ico.md) trong [f63ee2e][ico] ghi nguồn, loại giá và mẫu kỹ thuật. Còn thiếu biên bản chốt quyền, lịch từng nguồn và xác nhận điều kiện feed sàn. | 28/11/2026 |
| R02 | Collector nguồn | Thu tự động PDF, HTML, XML và tin theo nguồn đã chốt; raw, status, hash, timestamp và lỗi được lưu. Có mẫu đối chiếu từng parser. | Hiệp | ĐL | Collector PDF ở [f63ee2e][ico] đã tải hai tháng, giữ raw/hash và log lỗi. Còn thiếu collector HTML, FX XML, tin và mẫu từng parser. | 28/11/2026 |
| R03 | ETL tăng dần | Chạy lại cùng đầu vào không tạo trùng; giữ bản sửa; không tự điền giá thiếu; có test và log. | Hiệp | ĐL | [f63ee2e][ico] có nạp tăng dần và giữ bản sửa. Đã thử nạp lặp cùng raw và bỏ qua ngày trống. Còn thiếu ca kiểm chứng nguồn đổi giá và bộ test lưu trong repo. | 28/11/2026 |
| R04 | Chất lượng dữ liệu | Cách ly giá sai đơn vị/ngày/high-low; báo tuổi dữ liệu và tỷ lệ lỗi. Có 20 mẫu đối chiếu và ca lỗi tái hiện. | Hiệp | ĐL | [f63ee2e][ico] có kiểm tra PDF ICO, `QualityIssue` và số dòng bị loại. Hai mẫu thật có 0 dòng bị loại. Còn thiếu mẫu lỗi tái hiện, high-low, tuổi dữ liệu, tỷ lệ lỗi và bộ 20 mẫu. | 28/11/2026 |
| R05 | Kho dữ liệu | Migration/DDL, fact/dimension và grain đúng mục 8; raw_id/observation_id truy ngược được. Có từ điển và sơ đồ. | Hiệp, Hiếu hỗ trợ | ĐL | Migration trong [f63ee2e][ico] đã chạy trên PostgreSQL, giá ICO truy vết tới run và raw. Còn thiếu mô hình đa nguồn, từ điển và sơ đồ đủ phạm vi. | 28/11/2026 |
| R06 | View và KPI | View giá, FX, chủ đề, kế hoạch, cảnh báo và pipeline; SQL đối chiếu ít nhất 3 KPI, không nhân bản khi nối fact. | Hiệp | ĐL | [SQL ICO](../src/database/kiem-tra-ico.sql) trong [f63ee2e][ico] đã đối chiếu giá gần nhất. Còn thiếu các view BI và đối chiếu đủ ba KPI, kể cả kiểm tra nối fact. | 28/11/2026 |
| R07 | Tài khoản và API | Hai vai trò; CRUD đúng quyền/đối tượng; hợp đồng JSON và mã lỗi; demo hợp lệ, thiếu trường và bị từ chối. | Hiếu | ĐL | [f63ee2e][ico] có API giá chỉ đọc và route Wagtail. Đã thử API và mở trang đăng nhập. Còn thiếu Admin/Analyst, CRUD và demo quyền theo đối tượng. | 28/11/2026 |
| R08 | Kế hoạch và kịch bản | Nhập Q/ngân sách, chọn observation, tính đúng quy đổi/chi phí, lưu và đọc lại đầy đủ. Đối chiếu phép tính bằng một ca tay. | Huy, Hiếu hỗ trợ | CXN | Có [đề xuất hợp đồng](ke-hoach-trien-khai.md). Chưa có commit triển khai, ca tính tay hoặc kiểm thử lưu/đọc lại. | 28/11/2026 |
| R09 | Cảnh báo | Ngưỡng giá/ngân sách/độ mới; có chứng cứ và khóa chống lặp; không tạo lặp cùng sự kiện; có ca test vượt/không vượt. | Huy | CXN | Có [đặc tả cảnh báo](dac-ta-tin-va-canh-bao.md). Chưa có commit triển khai rule, chống lặp hoặc ca kiểm thử. | 28/11/2026 |
| R10 | AI trích sự kiện | JSON hợp lệ, chủ đề và dẫn chứng; lưu model/prompt/hash; đủ 40 tin kiểm thử, điểm thực đo và phân tích lỗi. | Huy, Cả nhóm rà mẫu | CXN | Đề cương có yêu cầu đánh giá. Chưa có commit triển khai AI, tập 40 tin kiểm thử hoặc điểm thực đo. | 28/11/2026 |
| R11 | Ba dashboard | Đủ 3 dashboard và 10 biểu đồ/bảng tổng; lọc nguồn/ngày/loại giá; 3 KPI khớp SQL; có tệp xuất và demo. | Trang, Hiệp cấp view | CXN | [11614a2](https://github.com/DangHuy1302/project-htkdtm/commit/11614a29a8ccc81efed1c4f361bff9f0fb77509b) có đặc tả. Chưa có dashboard chạy, tệp xuất hoặc xác nhận KPI. | 28/11/2026 |
| R12 | Bản tin AI | Số liệu lấy từ mã tính, mỗi nhận định có evidence/URL; kỳ dữ liệu và bản thiếu nguồn rõ. Kiểm tra 20 bản tin/tình huống. | Huy, Minh hỗ trợ QA | CXN | Có [đề xuất API bản tin](ke-hoach-trien-khai.md). Chưa có commit triển khai hoặc bộ 20 ca kiểm thử. | 28/11/2026 |
| R13 | Tin và xử lý việc | Danh sách/chi tiết tin lọc được; link nguồn; form trạng thái/ghi chú lưu qua API; lịch sử đọc lại đúng. Có ca UI và ảnh demo. | Minh, Hiếu cấp API | CXN | [8ad4843](https://github.com/DangHuy1302/project-htkdtm/commit/8ad484303d5aa001e12ecc21f3dae85ff62d7ab5) có đặc tả. Chưa có giao diện chạy, ca lưu/đọc lại hoặc ảnh demo. | 28/11/2026 |
| R14 | Lịch n8n | Workflow gọi collector → ETL → cảnh báo theo lịch; có xác thực, khóa chạy chồng, retry giới hạn và ít nhất 7 ngày log. | Hiếu, Hiệp phối hợp | CXN | Collector ICO có khóa chạy chồng và retry trong [f63ee2e][ico]. Chưa có commit triển khai workflow n8n, endpoint điều phối xác thực hoặc bảy ngày log. | 28/11/2026 |
| R15 | Môi trường Docker | Web, PostgreSQL, Superset, n8n khởi động theo README; volume giữ dữ liệu khi khởi động lại; .env.example không có khóa thật. | Hiếu | ĐL | Compose web/db và mẫu env nằm trong [f63ee2e][ico]. CSDL đã giữ dữ liệu qua stop/start. Còn thiếu Superset, n8n trong Compose dự án và xác nhận dừng web bình thường. | 28/11/2026 |
| R16 | Mã nguồn và tài liệu | Thư mục nhóm, commit/PR; README, API, từ điển, workflow/dashboard xuất, báo cáo nguồn/test và danh mục lỗi còn mở. | Hiếu, Cả nhóm bổ sung | ĐL | Có [f63ee2e][ico], [d6d4601][layout], [19c7b39][overview], README, hợp đồng API giá và hồ sơ ICO. Bộ tài liệu CF-DOC-001 đã được duyệt. Còn thiếu bộ từ điển, workflow/dashboard xuất và hồ sơ kiểm thử đầy đủ. | 28/11/2026 |
| R17 | Demo và nghiệm thu | 3 luồng đầu cuối có kết quả; ít nhất một luồng dùng giá thu thật; ca giả lập có nhãn; kiểm thử sai quyền, nguồn lỗi và nạp lặp. | Huy, Cả nhóm demo | ĐL | [Hồ sơ ICO](kiem-chung-ico.md) và [f63ee2e][ico] chứng minh một luồng dùng giá thật, nguồn lỗi và nạp lặp. [d6d4601][layout] bổ sung layout. CF-002B.1 tại [19c7b39][overview] đã kiểm tra tuyến UI ở preview. Còn thiếu hai luồng và ca sai quyền. | 28/11/2026 |

Đối chiếu thêm [nhật ký tiến độ CF](tien-do-trien-khai.md) và [kịch bản demo](kich-ban-demo.md). Khi xác nhận một mã R, ghi ngày, người kiểm tra, môi trường/SHA và liên kết bằng chứng hoặc Issue/PR.

[ico]: https://github.com/DangHuy1302/project-htkdtm/commit/f63ee2ea605ed86e9193c904015ef4fb6cc28a91
[layout]: https://github.com/DangHuy1302/project-htkdtm/commit/d6d4601a0e5b886639fec5b584d8914d7c3dbbc7
[overview]: https://github.com/DangHuy1302/project-htkdtm/commit/19c7b399dd8eaa657a376664b0da993e8a0e749b
