# Đặc tả dashboard CafeFlow Market BI

Người phụ trách: Dương Quỳnh Trang  
Phạm vi theo đề cương: V1–V4, đầu ra R11  
Trạng thái: bản đặc tả dự kiến, chưa dựng dashboard hoặc xác nhận KPI bằng dữ liệu chạy thật.

## 1. Mục tiêu và người dùng

Dashboard giúp nhân viên thu mua/Analyst theo dõi thị trường, rà kế hoạch và phát hiện dữ liệu cũ/lỗi. Trang cấu hình Superset từ view Hiệp bàn giao; không chịu trách nhiệm tự xây kho dữ liệu hoặc huấn luyện AI.

Ba dashboard dự kiến gồm: thị trường, kế hoạch thu mua, chất lượng dữ liệu. Tối thiểu 10 biểu đồ/bảng tổng cộng là yêu cầu dự kiến theo đề cương, chưa phải kết quả hoàn thành.

## 2. Nguyên tắc hiển thị

- Luôn ghi đơn vị, nguồn, loại giá và thời điểm hiệu lực; tách với thời điểm collector kiểm tra.
- Chỉ dùng dữ liệu hợp lệ cho KPI chính; dữ liệu nghi lỗi đưa sang mục chất lượng.
- Tách giá chỉ báo ICO, giá kỳ hạn và giá nội địa. Không nối các hợp đồng kỳ hạn khác nhau thành một chuỗi.
- Không cộng giá hoặc lấy trung bình các loại giá/đơn vị khác nhau để tạo KPI tổng.
- Dữ liệu thiếu hiển thị “Chưa có dữ liệu”, không tự thay bằng 0. Số 0 thực phải được phân biệt với giá trị thiếu.
- Giá quy đổi chỉ là tham chiếu, chưa gồm các khoản chi phí giao hàng/chế biến khác.
- Tổng hợp mỗi fact đúng grain trước khi ghép dữ liệu để tránh nhân bản số liệu.
- Tên view/cột vật lý chờ Hiệp bàn giao; tên dữ liệu dưới đây là khái niệm nghiệp vụ.

## 3. Dashboard 1 — Thị trường

Câu hỏi: giá nào đang biến động, dựa trên quan sát nào và bối cảnh tin tức trong kỳ là gì?

| Mã | Biểu đồ/bảng dự kiến | Loại hiển thị | Dữ liệu cần có | Bộ lọc chính |
| --- | --- | --- | --- | --- |
| TT01 | Giá mới nhất hợp lệ của chuỗi đã chọn | KPI + bảng thông tin nguồn | Giá, nguồn, loại giá, thị trường/hợp đồng, tiền tệ, đơn vị, effective_at | Chuỗi, nguồn, ngày |
| TT02 | Biến động giá so với quan sát hợp lệ trước | KPI % kèm hai mốc so sánh | Hai quan sát liên tiếp cùng chuỗi, thời điểm và giá | Chuỗi, ngày |
| TT03 | Diễn biến giá theo thời gian | Đường | Giá hợp lệ theo effective_at, chuỗi và đơn vị | Khoảng ngày, nguồn, loại giá, hợp đồng |
| TT04 | Phân bố chủ đề tin trong kỳ | Cột | Tin sạch liên quan, chủ đề, ngày đăng, nguồn; tách kết quả chưa duyệt | Ngày đăng, nguồn, chủ đề |

TT01/TT02 chọn giá mới nhất trong khoảng lọc và ghi rõ mốc. Nếu TT02 cần quan sát trước ngoài khoảng lọc, phải ghi rõ mốc đối chiếu. Chưa có mốc trước thì không tính phần trăm. TT04 là số bài theo chủ đề, không phải nhu cầu tiêu thụ; một bài có thể có nhiều chủ đề nên tổng cột có thể lớn hơn số bài độc lập.

## 4. Dashboard 2 — Kế hoạch thu mua

Câu hỏi: kế hoạch nào cần rà soát vì chi phí tham chiếu vượt ngân sách, và cảnh báo đang được xử lý thế nào?

| Mã | Biểu đồ/bảng dự kiến | Loại hiển thị | Dữ liệu cần có | Bộ lọc chính |
| --- | --- | --- | --- | --- |
| KH01 | Chi phí tham chiếu và ngân sách theo kế hoạch | Cột nhóm | Kế hoạch, phiên bản kịch bản đang chọn, khối lượng, chi phí, ngân sách | Kế hoạch, ngày tạo, người phụ trách theo quyền |
| KH02 | Kế hoạch có chênh lệch ngân sách cần rà soát | Bảng | Mã kế hoạch, phiên bản, chi phí, ngân sách, chênh lệch, observation đầu vào | Kế hoạch, khoảng ngày, vượt/không vượt |
| KH03 | Số cảnh báo theo trạng thái | Cột | Cảnh báo duy nhất, loại, mức ưu tiên, trạng thái và thời điểm tạo | Ngày tạo, loại, trạng thái, người phụ trách theo quyền |

Mỗi kế hoạch chỉ lấy phiên bản kịch bản được chọn hoặc phiên bản hiện hành theo quy ước backend, tránh cộng nhiều phiên bản. Không gọi chênh lệch ngân sách là lợi nhuận hay khoản tiết kiệm đã đạt. Trạng thái cảnh báo chờ nhóm chốt thống nhất, không tự suy ra từ ghi chú.

## 5. Dashboard 3 — Chất lượng dữ liệu

Câu hỏi: nguồn nào đang cũ, dữ liệu có đáng dùng cho KPI và collector có chạy đúng không?

| Mã | Biểu đồ/bảng dự kiến | Loại hiển thị | Dữ liệu cần có | Bộ lọc chính |
| --- | --- | --- | --- | --- |
| CL01 | Tuổi dữ liệu và lần kiểm tra nguồn gần nhất | Bảng, màu theo ngưỡng cấu hình | Nguồn/chuỗi, effective_at mới nhất hợp lệ, collected_at, lần collector chạy gần nhất | Nguồn, chuỗi, ngưỡng quá hạn |
| CL02 | Số bản hợp lệ/cách ly và tỷ lệ hợp lệ theo batch | Cột chồng + tỷ lệ | batch_id, số bản đã kiểm tra, hợp lệ, cách ly, thời gian | Khoảng chạy, nguồn, batch |
| CL03 | Lịch sử chạy collector và lỗi | Bảng | Run ID, nguồn, bắt đầu/kết thúc, trạng thái, số mới/sửa, mã lỗi | Khoảng chạy, nguồn, thành công/lỗi |

HTTP 200 chỉ chứng minh tải được phản hồi, không thay cho dữ liệu hợp lệ. CL02 không trộn số bản ghi với số lần chạy; mẫu số bằng 0 hiển thị chưa tính được.

## 6. Định nghĩa ba KPI đối chiếu

### KPI 1 — Giá mới nhất hợp lệ

- Đơn vị quan sát: một chuỗi được xác định bởi nguồn, hàng hóa, loại giá, thị trường/hợp đồng, tiền tệ và đơn vị.
- Chọn bản hợp lệ có effective_at mới nhất theo bộ lọc.
- Nếu có sửa đổi cùng thời điểm, chọn bản sửa hiện hành theo quy ước của kho, không đếm thành hai giá.
- Hiển thị giá gốc và đơn vị. Giá quy đổi nếu có phải ghi tỷ giá/quan sát đã dùng.

### KPI 2 — Phần trăm biến động giá

Biến động (%) = (giá mới − giá trước) / giá trước × 100.

- Hai giá thuộc cùng chuỗi và đều hợp lệ, đã xử lý bản sửa.
- “Giá trước” là quan sát hợp lệ gần nhất trước giá mới; không tự gọi là hôm qua nếu ngày liền trước thiếu dữ liệu.
- Không đủ hai mốc hoặc mẫu số không hợp lệ thì trả thiếu dữ liệu, không mặc định 0%.
- Ví dụ minh họa, không phải giá thị trường thật: giá trước 4.000 USD/tấn, giá mới 4.080 USD/tấn → (4.080 − 4.000) / 4.000 × 100 = 2%.

### KPI 3 — Tuổi dữ liệu

Tuổi dữ liệu (giờ) = (thời điểm tham chiếu − effective_at mới nhất hợp lệ) / 1 giờ.

- Thống nhất múi giờ lưu trữ và quy đổi hiển thị; ghi rõ thời điểm tham chiếu/refresh dashboard.
- Ví dụ giả lập: dữ liệu hiệu lực 08:00, thời điểm tham chiếu 14:00 cùng ngày/cùng múi giờ → tuổi dữ liệu 6 giờ.
- collected_at là thời điểm lấy dữ liệu, không thay effective_at. Với tin dùng published_at nếu phù hợp với KPI tin.
- Khi lọc khoảng lịch sử, số tuổi được hiểu theo thời điểm tham chiếu đã ghi, tránh diễn giải như độ trễ collector hiện tại.

## 7. Bộ lọc và tương tác

- Thị trường: ngày hiệu lực, nguồn, hàng hóa, loại giá và hợp đồng nếu có.
- Tin: ngày đăng, nguồn và chủ đề; bộ lọc này có phạm vi riêng, không mặc định dùng ngày hiệu lực của giá.
- Kế hoạch: kế hoạch, ngày tạo và phiên bản kịch bản theo quy ước.
- Cảnh báo: ngày tạo, loại và trạng thái.
- Pipeline: thời gian chạy, nguồn và batch/run.
- Đặt phạm vi áp dụng của mỗi bộ lọc trong Superset, tránh một bộ lọc nguồn giá làm mất toàn bộ biểu đồ tin.
- Liên kết chi tiết tới trang ứng dụng/nguồn sẽ cấu hình sau khi nhóm bàn giao URL; chưa đặt đường dẫn giả như đã hoạt động.

## 8. Dữ liệu cần Hiệp bàn giao

| Nhóm dữ liệu | Yêu cầu tối thiểu |
| --- | --- |
| Giá | Chuỗi định danh, giá, đơn vị/tiền tệ, effective_at, quality_status, observation_id, source_url, bản sửa hiện hành |
| Tỷ giá | Cặp tiền, loại mua/bán, tỷ giá, effective_at và observation_id |
| Tin | ID, nguồn, published_at, chủ đề, trạng thái phân tích/duyệt và thông tin chống trùng |
| Kế hoạch | ID, phiên bản kịch bản, khối lượng kg, chi phí VND, ngân sách VND, tham chiếu quan sát đầu vào |
| Cảnh báo | ID duy nhất, loại, trạng thái, mức ưu tiên, created_at và người phụ trách theo quyền |
| Chất lượng/lần chạy | Run/batch ID, nguồn, thời gian, số bản kiểm tra/hợp lệ/lỗi/mới/sửa và lý do lỗi |

Nhóm chốt tên view/cột, grain và khóa nối trong từ điển dữ liệu trước khi cấu hình biểu đồ. Tài khoản Superset dùng quyền đọc phù hợp, không đưa dữ liệu cá nhân vào view công khai.

## 9. Kế hoạch đối chiếu SQL

Trang viết ba truy vấn SELECT sau khi tên view/cột đã được bàn giao. Tài liệu hiện chưa chứa SQL chạy thật.

| Ca | Cách kiểm tra | Kết quả cần đạt |
| --- | --- | --- |
| KPI-01 | Lọc một chuỗi, sắp thời điểm hiệu lực, chọn bản hiện hành mới nhất hợp lệ | Giá, nguồn, đơn vị và mốc thời gian khớp TT01 |
| KPI-02 | Lấy hai quan sát hợp lệ liên tiếp, tính phần trăm theo công thức | TT02 khớp kết quả SQL trước làm tròn |
| KPI-03 | Cố định cùng thời điểm tham chiếu, tính chênh lệch với effective_at | CL01 khớp kết quả SQL trong dung sai hiển thị đã thống nhất |

Lưu bộ lọc, thời điểm refresh, truy vấn và ảnh kết quả khi thực hiện. Chênh lệch do làm tròn phải giải thích; không đổi công thức để ép khớp.

## 10. Checklist thực hiện sau khi có dữ liệu

- [ ] Đã nhận view, quyền đọc và từ điển dữ liệu.
- [ ] Đã dựng ba dashboard và tối thiểu 10 biểu đồ/bảng tổng cộng.
- [ ] Đã kiểm tra bộ lọc đúng phạm vi, không trộn loại giá/hợp đồng.
- [ ] Đã kiểm tra đơn vị, ngày hiệu lực, bản sửa và dữ liệu thiếu.
- [ ] Đã đối chiếu ba KPI bằng SQL.
- [ ] Đã kiểm tra dữ liệu trùng, nhiều phiên bản kế hoạch và phép nối fact.
- [ ] Đã kiểm tra quyền truy cập theo thiết kế của nhóm.
- [ ] Đã xuất cấu hình dashboard, ghi cách dùng và ảnh demo.

Các ô chưa đánh dấu vì chưa có minh chứng triển khai. Tài liệu này hoàn thành bước thiết kế ban đầu, không thay báo cáo nghiệm thu R11.
