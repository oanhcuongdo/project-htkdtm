# Kế hoạch triển khai CafeFlow Market BI

Đặc tả này là đề xuất để năm thành viên ghép phần việc trên nhánh tích hợp `nhom08-65httt`. Route và schema của luồng ICO ở mục “Đang triển khai” có mã đi kèm. Những hợp đồng nghiệp vụ bên dưới cần Hiếu, Huy và Hiệp chốt trước khi Minh và Trang tích hợp.

## Cấu trúc và hợp đồng bàn giao

- `src/backend/cafeflow/` giữ cấu hình một tiến trình Django, Wagtail và DRF. App `market` giữ giá, nguồn, collector và màn hình giá. Django template ở `templates/` của app sở hữu màn hình.
- Các app dự kiến là `procurement` cho kế hoạch, kịch bản và quy tắc cảnh báo, `news` cho tin, phân tích và bản tin. API và template gọi cùng dịch vụ nghiệp vụ. Dùng Django session và CSRF cho thao tác ghi từ giao diện.
- `src/database/` giữ SQL kiểm tra và tài liệu view. Migration Django là nguồn triển khai DDL. `src/compose.yaml` hiện có web và PostgreSQL. Superset dùng vai trò PostgreSQL chỉ đọc trên view BI. n8n điều phối tác vụ Python qua endpoint nội bộ đã xác thực, với lịch, khóa chạy chồng và số lần thử lại giới hạn.

## Mô hình dữ liệu

| Lớp | Grain và khóa dự kiến |
| --- | --- |
| Nguồn và raw | `market_source` theo mã. `raw_collection_run` theo một lần chạy, lưu nguồn, URL, mốc thu, HTTP, trạng thái và số đếm. `raw_document` duy nhất theo nguồn, URL và SHA-256. `raw_quality_issue` theo dòng bị loại trong một lần chạy. |
| Giá | `dw_price_series` theo nguồn và mã chuỗi, mang hàng hóa, loại giá, thị trường, hợp đồng, tiền tệ và đơn vị. `dw_price_observation` theo chuỗi, ngày hiệu lực và phiên bản. Tối đa một bản hiện hành cho mỗi ngày/chuỗi. Quan sát truy ngược run và raw. Giá công bố chính xác tới ngày dùng `effective_date`. Nguồn có giờ công bố cần trường thời điểm riêng và khóa theo độ phân giải gốc khi mở rộng. |
| FX | Nguồn, cặp tiền, loại tỷ giá, thời điểm hiệu lực và bản sửa. Lưu riêng mua tiền mặt, mua chuyển khoản, bán và tham chiếu raw. |
| Tin | Một URL chuẩn theo nguồn, một phiên bản theo hash nội dung; giữ ngày đăng có thể rỗng và trích đoạn được phép lưu. Phân tích duy nhất theo phiên bản nội dung, model và prompt. Nhóm các bài trùng sự kiện khi chia tập đánh giá. |
| Thu mua | Kế hoạch theo chủ sở hữu, hàng hóa, kỳ dự kiến, khối lượng kg, ngân sách VND. Kịch bản bất biến theo kế hoạch và phiên bản, lưu ID bản giá/FX đã chọn, snapshot đầu vào, chi phí, chênh lệch và quy tắc làm tròn. |
| Cảnh báo | Rule theo loại và phiên bản. Cảnh báo có khóa duy nhất theo rule, đối tượng và sự kiện kích hoạt. Hành động là bản ghi nối thêm, chứa trạng thái trước/sau, người thao tác, ghi chú và thời điểm; khóa duy nhất theo alert và mã yêu cầu ghi. |
| Bản tin | Kỳ quan sát, snapshot KPI do backend tính, phiên bản model/prompt, trạng thái duyệt; mỗi nhận định tham chiếu chứng cứ có URL và observation/article ID. |
| BI | Ngày, nguồn, thị trường, đơn vị, chủ đề và chuỗi dùng chung. Đề xuất view `bi_prices`, `bi_fx`, `bi_news_topics`, `bi_plan_scenarios`, `bi_alerts`, `bi_collection_runs`. Chọn bản hiện hành, ghép sau khi tổng hợp đúng grain. So giá gần nhất với mốc hợp lệ liền trước trong cùng chuỗi. Tuổi dữ liệu dùng ngày hoặc giờ theo độ phân giải nguồn. |

Nhánh hiện tại dùng tiền tố bảng `raw_` và `dw_` cho luồng ICO. Hiệp và Hiếu chốt thời điểm tách schema vật lý và quyền đọc cùng migration BI.

## API v1

**Đang triển khai.** `GET /api/v1/prices/` đọc bản giá hiện hành, lọc `source`, `series`, `price_type`, phân trang `page` với 25 dòng. Phản hồi DRF gồm `count`, `next`, `previous`, `results`. Mỗi dòng có `id`, `source`, `source_name`, `source_url`, `run_id`, `content_hash`, `series`, `series_name`, `commodity`, `price_type`, `market`, `contract_code`, `currency`, `unit`, `effective_date`, `collected_at`, `value`, `revision`. Ngày dùng ISO 8601, `value` là chuỗi thập phân. Hợp đồng rỗng biểu thị chuỗi không có kỳ hạn. Trang `/` và API giá chỉ đọc trên môi trường demo cục bộ.

| Đề xuất route dưới `/api/v1/` | Hợp đồng |
| --- | --- |
| `GET/POST plans/`, `GET/PATCH plans/{id}/` | Tên, hàng hóa, ngày kế hoạch, `quantity_kg`, `budget_vnd`. Backend lấy chủ sở hữu từ session. Analyst cập nhật kế hoạch theo quyền đối tượng. |
| `GET/POST plans/{id}/scenarios/` | POST `price_observation_id`, `fx_observation_id` khi cần; trả `id`, `revision`, snapshot và `reference_cost_vnd`, `budget_delta_vnd`, `over_budget`. Chọn FX có hiệu lực tương ứng và lưu loại tỷ giá. |
| `GET news/`, `GET news/{id}/`, `GET briefs/`, `GET briefs/{id}/` | Lọc tin theo `q`, `source`, `topic`, `published_from`, `published_to`. Tin trả nguồn, ngày đăng, excerpt, chủ đề, trạng thái phân tích và chứng cứ được phép xem. Bản tin trả kỳ, KPI đầu vào, nhận định và `evidence_ids`, kèm tập bằng chứng. |
| `GET alerts/`, `GET alerts/{id}/`, `GET/POST alerts/{id}/actions/` | Chi tiết gồm `priority`, `reason`, `evidence`, `status`, `allowed_transitions`, `assignee`, `version`. POST gồm `status`, `note`, `expected_version`, `request_id`; cập nhật và ghi lịch sử trong một giao dịch. Đề xuất `open → in_progress → resolved`, ghi chú bắt buộc khi xử lý xong. |
| `GET collection-runs/`, `GET collection-runs/{id}/` | Run, HTTP, thời điểm và số đếm; raw và dòng lỗi giới hạn Admin. Endpoint điều phối riêng cho n8n dùng token từ biến môi trường; khóa URL nguồn theo cấu hình. |

API nghiệp vụ đề xuất dùng tiền/khối lượng dưới dạng chuỗi thập phân và thời điểm ISO 8601 có offset. Thành công đọc/sửa trả 200, tạo trả 201. Lỗi đề xuất gồm `code`, `detail`, `fields` khi có lỗi nhập (400), từ chối session/CSRF/quyền (403), đối tượng không thấy (404) và phiên bản đã đổi (409). Kiểm tra CSRF và quyền theo đối tượng ở backend. Mẫu hợp đồng JSON bằng schema và giá trị thật sẽ đi cùng API sau khi các trường được chốt.

## Thứ tự chạy thử và tiêu chí nghiệm thu

| Bước | Chủ trì và mã R | Minh chứng cần có |
| --- | --- | --- |
| 1. Kiểm tra nguồn và luồng ICO | Hiệp R01–R05, Hiếu hỗ trợ R15 | Đối chiếu hồ sơ nguồn, PDF, đơn vị và ngày thật. Chạy collector, kiểm tra raw, log, giá hiện hành, nạp lặp, API và template. Chốt điều khoản và yêu cầu feed sàn với giảng viên. |
| 2. Mở rộng ETL và BI, song song thiết lập quyền | Hiệp R02–R06; Hiếu R07/R14–R16 | Giacaphe tách nội địa/kỳ hạn công bố lại, FX XML, tin có quyền lưu. Cách ly lỗi, 20 mẫu đối chiếu, truy vết, view và tài khoản chỉ đọc. Hai vai trò Admin/Analyst, ca sai quyền, n8n có ít nhất 7 ngày log, Compose đủ 4 dịch vụ và kiểm tra giữ volume. |
| 3. Kịch bản thu mua và cảnh báo | Huy R08–R09; Hiếu API; Minh chuẩn bị R13 | Đối chiếu Q × VND/kg, chi phí trừ ngân sách và snapshot. Chốt loại FX, độ mới, ngưỡng và cách làm tròn. Chạy các ca vượt/không vượt, cùng sự kiện chạy lại, lưu hành động và phát hiện cập nhật đồng thời. |
| 4. Web tin, AI và dashboard | Huy R10/R12; Trang R11; Minh R13 | Minh lọc tin, mở nguồn và lưu hành động qua API. Huy chốt LLM/model, quyền gửi dữ liệu, taxonomy và rubric; kiểm tra JSON, trích dẫn trong văn bản, nguồn, ngày có thể rỗng. Bản tin dùng KPI tính sẵn và evidence ID. Chia 20 tin phát triển và 40 tin kiểm thử, đo kết quả thật, kiểm tra 20 tình huống bản tin. Trang dựng 3 dashboard, tối thiểu 10 bảng/biểu đồ, đối chiếu 3 KPI và xuất cấu hình. |
| 5. Tích hợp | Huy R17; Hiếu R16; cả nhóm | Ba luồng đầu cuối, ít nhất một dùng giá thật. Chạy ca nguồn lỗi, sai quyền, nạp lặp, cảnh báo chống trùng, lưu kế hoạch/hành động và đọc lại. Lưu log, truy vấn, README, workflow/dashboard xuất và danh mục lỗi mở. |

Chatbot, dự báo, MCP và thông báo ra ngoài được xếp sau các mốc trên. Bảng này giữ các mã R ở trạng thái chưa nghiệm thu.
