# Đặc tả giao diện tin và xử lý cảnh báo

Người phụ trách: Lưu Tuấn Minh  
Phạm vi theo đề cương: U1–U4, đầu ra chính R13; hỗ trợ rà mẫu AI và kiểm thử  
Trạng thái: bản đặc tả dự kiến; chưa có giao diện, API hoặc kết quả lưu dữ liệu được kiểm chứng.

## 1. Mục tiêu

Cung cấp giao diện Django template để Analyst tìm/xem tin ngành, mở nguồn gốc, xem cảnh báo và ghi nhận hành động xử lý. Minh tích hợp API Hiếu bàn giao; không phụ trách collector, kho dữ liệu hay hạ tầng.

Trạng thái, tên trường, mã lỗi và URL API dưới đây cần được thống nhất với Hiếu/Huy trước khi lập trình. Không coi tài liệu này là hợp đồng API đã được phê duyệt.

## 2. Màn hình danh sách tin

### 2.1. Thành phần dự kiến

| Thành phần | Nội dung và hành vi |
| --- | --- |
| Tiêu đề trang | Tin thị trường cà phê |
| Bộ lọc | Từ khóa tiêu đề, khoảng ngày đăng, nguồn và chủ đề |
| Danh sách/bảng | Tiêu đề, nguồn, ngày đăng, chủ đề nếu có, trạng thái phân tích và nút xem chi tiết |
| Nguồn gốc | Nút mở bài nguồn nếu có URL hợp lệ |
| Phân trang | Dùng thông tin phân trang API cung cấp; không tải toàn bộ tin khi dữ liệu lớn |
| Thông tin trạng thái | Đang tải, không có kết quả, không thể tải hoặc chưa phân tích |

### 2.2. Luồng thao tác

1. Người dùng mở trang tin và nhận dữ liệu theo quyền.
2. Chọn bộ lọc và bấm tìm kiếm/áp dụng.
3. Giao diện kiểm tra ngày bắt đầu không sau ngày kết thúc; áp dụng điều kiện lọc qua API.
4. Hiển thị kết quả và phân trang; thay bộ lọc thì quay về trang đầu.
5. Chọn tiêu đề để mở chi tiết hoặc mở URL nguồn.
6. Nút xóa bộ lọc đưa về trạng thái mặc định được nhóm thống nhất.

Không có kết quả phải hiện “Không có tin phù hợp”, không dùng cùng thông báo với API lỗi.

## 3. Màn hình chi tiết tin

| Khu vực | Nội dung |
| --- | --- |
| Thông tin gốc | Tiêu đề, nguồn, ngày đăng, thời điểm thu thập nếu API có, URL nguồn |
| Nội dung được phép hiển thị | Trích đoạn/tóm tắt hoặc phần văn bản có quyền sử dụng; không mặc định tái đăng toàn văn |
| Phân tích AI | Chủ đề, loại sự kiện, hàng hóa/khu vực, ngày sự kiện nếu có và phần chưa chắc chắn |
| Bằng chứng | Trích dẫn/ngữ cảnh được backend kiểm tra, URL và thông tin tham chiếu |
| Điều hướng | Quay lại danh sách, ưu tiên giữ bộ lọc trước đó |

- Chỉ hiển thị phần AI theo dữ liệu hợp lệ và trạng thái cho phép của backend; chưa phân tích thì ghi rõ.
- Không tự tạo nhận định, giá hoặc dẫn chứng trên frontend.
- Không biến ngày thiếu thành ngày hiện tại; hiển thị “Chưa xác định”.
- Dữ liệu lấy từ nguồn phải được escape phù hợp, không chèn HTML/script thô vào template.
- Liên kết nguồn chỉ chấp nhận URL web hợp lệ theo kiểm tra backend; mở tab mới dùng thuộc tính bảo vệ phù hợp khi triển khai.

## 4. Màn hình chi tiết và xử lý cảnh báo

### 4.1. Nội dung hiển thị

- Mã cảnh báo, loại, mức ưu tiên và thời điểm tạo.
- Lý do kích hoạt, ngưỡng/quy tắc và số liệu đầu vào do backend trả.
- Quan sát giá/tỷ giá, thời điểm hiệu lực và nguồn liên quan nếu có.
- Kế hoạch/kịch bản liên quan nếu có.
- Người phụ trách, trạng thái hiện tại và lịch sử thao tác.

### 4.2. Biểu mẫu cập nhật

| Trường | Quy tắc dự kiến |
| --- | --- |
| Trạng thái mới | Chọn trong danh sách backend cho phép; không nhập tùy ý |
| Ghi chú/hành động | Mô tả nội dung rà soát hoặc xử lý; đề xuất bắt buộc khi chuyển sang đã xử lý, chờ nhóm chốt |
| Mã cảnh báo | Lấy từ bản ghi đang xem, không dùng để thay kiểm tra quyền ở backend |
| Phiên bản/thời điểm cập nhật | Dùng nếu API hỗ trợ phát hiện hai người sửa đồng thời |

Tên trạng thái đề xuất ban đầu: “Chưa xử lý”, “Đang xử lý”, “Đã xử lý”. Mã máy và các bước chuyển chờ Hiếu/Huy chốt, không dùng như enum đã triển khai.

### 4.3. Luồng cập nhật

1. Mở một cảnh báo và xem bằng chứng.
2. Chọn trạng thái mới, nhập ghi chú theo quy tắc.
3. Kiểm tra biểu mẫu và gửi API đúng phương thức được bàn giao; với session Django cần CSRF theo thiết kế.
4. Trong lúc gửi, khóa nút lưu để hạn chế thao tác lặp.
5. Chỉ báo thành công khi API xác nhận lưu; hiển thị trạng thái và lịch sử từ phản hồi hoặc tải lại.
6. Khi lỗi, giữ nội dung người dùng đã nhập, hiển thị lý do có thể xử lý và cho thử lại.
7. Tải lại trang để xác minh trạng thái/ghi chú đã được lưu thật.

Ẩn nút trên UI không thay cho kiểm tra quyền trên backend. Cập nhật cảnh báo không đồng nghĩa hệ thống đã thực hiện giao dịch thu mua.

## 5. Dữ liệu giao diện cần nhận — đề xuất

Tên dưới đây mang tính đề xuất. Hiếu/Huy xác nhận tên, kiểu, null, cấu trúc JSON và quyền trước khi tích hợp.

### 5.1. Dữ liệu tin

| Trường đề xuất | Ý nghĩa | Yêu cầu dự kiến |
| --- | --- | --- |
| id | Định danh tin | Bắt buộc |
| title | Tiêu đề | Bắt buộc |
| source_name | Tên nguồn | Bắt buộc |
| source_url | URL nguồn gốc | Cần có để truy vết; thiếu thì không tạo liên kết giả |
| published_at | Thời điểm đăng | Có thể thiếu; không thay bằng collected_at |
| collected_at | Thời điểm thu thập | Hiển thị riêng nếu có |
| excerpt | Trích đoạn có quyền sử dụng | Có thể thiếu |
| topics | Chủ đề được phân tích | Có thể rỗng |
| analysis_status | Trạng thái phân tích/duyệt | Cần để quyết định cách hiển thị |
| analysis | Sự kiện, bằng chứng và uncertainty | Chỉ hiển thị khi backend cho phép |

### 5.2. Dữ liệu cảnh báo và lịch sử

| Trường đề xuất | Ý nghĩa | Yêu cầu dự kiến |
| --- | --- | --- |
| id | Mã cảnh báo | Bắt buộc |
| alert_type | Loại cảnh báo | Bắt buộc |
| priority | Mức ưu tiên | Theo quy tắc backend |
| reason | Lý do kích hoạt | Bắt buộc để người dùng hiểu |
| evidence | Quan sát, ngưỡng, nguồn hoặc kế hoạch liên quan | Cần truy vết; cách biểu diễn chờ chốt |
| status | Trạng thái hiện tại | Bắt buộc |
| allowed_transitions | Trạng thái người dùng được chuyển tới | Đề xuất; backend quyết định quyền |
| assignee | Người phụ trách | Theo quyền, có thể chưa gán |
| created_at / updated_at | Thời điểm tạo/cập nhật | Cần hiển thị đúng múi giờ |
| action_logs | Các lần đổi trạng thái và ghi chú | Có thể rỗng; cần tải lại được |

Lịch sử cần định danh hành động, trạng thái trước/sau, ghi chú, người thực hiện và thời điểm. Không cho frontend tự khai người thực hiện thay phiên đăng nhập.

### 5.3. Những điểm phải bàn giao trước khi tích hợp

- URL và phương thức danh sách/chi tiết tin, chi tiết/cập nhật cảnh báo, đọc lịch sử.
- Cách xác thực, CSRF, quyền Admin/Analyst và quyền trên đối tượng.
- Tham số bộ lọc/phân trang; múi giờ và định dạng ngày.
- JSON mẫu thành công, rỗng, lỗi trường nhập, chưa đăng nhập, thiếu quyền, không tìm thấy và sửa đồng thời nếu có.
- Trạng thái cảnh báo, chuyển trạng thái hợp lệ và quy định ghi chú.
- Giới hạn trường nhập, cách trả lỗi và dữ liệu mẫu đã gắn nhãn giả lập.

## 6. Checklist kiểm thử dự kiến

| Mã | Tình huống | Thao tác | Kết quả mong đợi |
| --- | --- | --- | --- |
| UI01 | Danh sách có dữ liệu | Mở trang với tài khoản đúng quyền | Hiện đúng tin, nguồn và ngày; phân trang hoạt động |
| UI02 | Bộ lọc | Chọn nguồn/chủ đề/ngày | Kết quả đúng điều kiện, thay bộ lọc về trang đầu |
| UI03 | Lọc rỗng | Chọn điều kiện không có bản ghi | Hiện thông báo không có tin phù hợp |
| UI04 | Khoảng ngày sai | Chọn bắt đầu sau kết thúc | Báo lỗi rõ, không gửi truy vấn sai |
| UI05 | Tin chưa có AI | Mở tin chưa phân tích | Hiện thông tin gốc và nhãn chưa phân tích, không có nhận định giả |
| UI06 | Mở nguồn | Bấm URL hợp lệ | Mở đúng nguồn; URL thiếu/không hợp lệ không tạo liên kết nguy hiểm |
| UI07 | Thiếu trường bắt buộc | Gửi trạng thái/ghi chú thiếu theo hợp đồng đã chốt | UI và backend báo lỗi; dữ liệu chưa bị cập nhật |
| UI08 | Lưu hợp lệ | Đổi trạng thái, ghi chú và bấm lưu | API xác nhận; trạng thái/lịch sử hiển thị đúng |
| UI09 | Lưu và đọc lại | Tải lại sau UI08 | Dữ liệu đọc lại trùng kết quả đã lưu |
| UI10 | Không đủ quyền | Thử xem/sửa đối tượng ngoài quyền | Backend từ chối, UI thông báo; không lộ dữ liệu |
| UI11 | API/mạng lỗi | Giả lập timeout hoặc lỗi máy chủ | Không báo thành công giả, giữ nội dung nhập và cho thử lại |
| UI12 | Bấm lưu nhiều lần | Bấm liên tiếp khi đang gửi | UI khóa nút; kiểm tra thêm phía backend, không chỉ dựa vào UI |
| UI13 | Cảnh báo không tồn tại | Mở ID không có | Hiện không tìm thấy, không lỗi trang trắng |
| UI14 | Nội dung có ký tự HTML | Dùng dữ liệu thử chứa thẻ/script | Nội dung được xử lý an toàn, script không chạy |

Tất cả ca hiện ở trạng thái chưa chạy. Khi thực hiện, bổ sung ngày chạy, môi trường/commit, dữ liệu đầu vào, kết quả thực tế, đạt/chưa đạt và minh chứng. Kết quả mong đợi không phải kết quả đã đo.

## 7. Phụ thuộc và bàn giao

- Hiếu: API, tài khoản thử, quyền, JSON mẫu, trạng thái và lịch sử lưu.
- Hiệp: tin/nguồn và dữ liệu đã chuẩn hóa; giải thích ngày đăng/thu thập.
- Huy: nội dung bằng chứng, quy tắc cảnh báo và cách hiển thị AI chưa chắc chắn.
- Minh: template, thao tác lọc, biểu mẫu, xử lý lỗi UI, checklist và mô tả lỗi tái hiện.

Minh chỉ rà/chấm mẫu AI theo rubric nhóm thống nhất; chưa tự ghi tỷ lệ chính xác khi chưa có bộ kiểm thử và kết quả.

## 8. Điều kiện hoàn thành phần triển khai sau này

- [ ] Danh sách/chi tiết tin hiển thị và lọc được trên ứng dụng chạy thật.
- [ ] Mở đúng nguồn; phân biệt dữ liệu thiếu, chưa phân tích và API lỗi.
- [ ] Form cập nhật trạng thái/ghi chú gọi API và lưu được.
- [ ] Lịch sử đọc lại đúng sau tải lại trang.
- [ ] Kiểm thử các ca hợp lệ, lỗi và thiếu quyền; lưu kết quả thực tế.
- [ ] Có mã nguồn, commit, hướng dẫn demo và minh chứng.

Chưa đánh dấu hoàn thành R13 từ tài liệu đặc tả này.
