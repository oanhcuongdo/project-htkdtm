# CafeFlow Market BI — Nhóm 8

Học phần: Hệ thống Kinh doanh thông minh  
Giảng viên hướng dẫn: TS. Đỗ Oanh Cường  
Nhóm: `nhom08-65httt`

## 1. Trạng thái dự án

Dự án có luồng giá chỉ báo ICO từ PDF qua PostgreSQL đến API và trang giá. Layout chung CF-002A nằm ở `d6d4601`. Trang Tổng quan và route Thị trường của CF-002B.1 đã được duyệt và commit tại `19c7b39` ngày 28/11/2026. [Nhật ký tiến độ](docs/tien-do-trien-khai.md) ghi SHA và minh chứng của từng mốc.

## Chạy luồng ICO trên Windows

Mở Docker Desktop ở chế độ Linux containers. Từ thư mục gốc repository, chạy trong PowerShell. Tạo `.env` một lần trước khi khởi động, rồi dùng lại tệp đó để giữ thông tin đăng nhập của volume.

```powershell
Set-Location .\nhom08-65httt\src
if (-not (Test-Path -LiteralPath .env)) {
    $cafeSecret = [Guid]::NewGuid().ToString('N') + [Guid]::NewGuid().ToString('N')
    $cafeDbPassword = [Guid]::NewGuid().ToString('N')
    (Get-Content -LiteralPath .env.example) |
        ForEach-Object { $_ -replace '^DJANGO_SECRET_KEY=$', "DJANGO_SECRET_KEY=$cafeSecret" -replace '^POSTGRES_PASSWORD=$', "POSTGRES_PASSWORD=$cafeDbPassword" } |
        Set-Content -LiteralPath .env -Encoding Ascii
}
docker compose config --quiet
docker compose up -d --build
docker compose logs web
```

Khi log web báo đang lắng nghe cổng 8000, chạy collector. Lệnh tháng lịch sử dùng định dạng `YYYY-MM` và chỉ chạy được với PDF lưu trữ có định dạng parser hỗ trợ.

```powershell
docker compose exec web python manage.py check
docker compose exec web python manage.py collect_ico
docker compose exec web python manage.py collect_ico
docker compose exec web python manage.py collect_ico --month 2026-10
docker compose exec web python manage.py collect_vcb
docker compose exec web python manage.py collect_vcb
Get-Content -LiteralPath .\database\kiem-tra-ico.sql |
    docker compose exec -T db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
Get-Content -LiteralPath .\database\kiem-tra-vcb.sql |
    docker compose exec -T db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
Invoke-RestMethod 'http://localhost:8000/api/v1/prices/?series=robustas'
Invoke-RestMethod 'http://localhost:8000/api/v1/exchange-rates/?currency=USD'
```

- Từ CF-002B.1 (`19c7b39`), mở [Tổng quan](http://localhost:8000/), [Thị trường](http://localhost:8000/market/) hoặc [API JSON](http://localhost:8000/api/v1/prices/?format=json). Ở mốc CF-002A (`d6d4601`), trang `/` mở bảng giá. Dùng `DJANGO_PORT` nếu cổng 8000 đã được dùng.
- Trên hai lần tải cùng nội dung, lần sau vẫn có run mới và số giá không đổi. Dòng chưa có giá trong PDF được bỏ qua. Dòng có giá nhưng không hợp lệ được ghi lý do; raw có thể tra theo run.
- Collector Vietcombank đọc XML qua `collect_vcb`, lưu bản gốc và từng loại tỷ giá vào `dw_fx_observation`; chạy lặp để kiểm tra `unchanged_rates`. Trang tỷ giá ở `/market/exchange-rates/`; API hỗ trợ lọc `currency` và `rate_type`. Truy vấn chống trùng nằm trong `src/database/kiem-tra-vcb.sql`.
- Có thể tạo tài khoản quản trị thử bằng `docker compose exec web python manage.py createsuperuser` và mở [Wagtail](http://localhost:8000/cms/).
- `docker compose stop` dừng dịch vụ và giữ volume; `docker compose start` chạy lại. Cấu hình này dành cho chạy thử trên máy cá nhân.

## 2. Giới thiệu

CafeFlow Market BI là hệ thống thu thập và phân tích thị trường cà phê đa nguồn, hỗ trợ người phụ trách thu mua của một cơ sở rang xay theo dõi giá, tỷ giá, tin ngành, lập kịch bản chi phí và xử lý cảnh báo.

Bối cảnh cơ sở rang xay được dùng để thiết kế bài tập; nhóm chưa xác nhận có dữ liệu giao dịch nội bộ hoặc đã khảo sát doanh nghiệp. Hệ thống hỗ trợ người dùng rà soát thông tin, không tự quyết định mua hay đặt lệnh giao dịch.

## 3. Luồng nghiệp vụ dự kiến

1. Thu thập giá, tỷ giá và tin ngành theo nguồn đã xác minh.
2. Lưu dữ liệu gốc, thời điểm hiệu lực, thời điểm thu thập và thông tin nguồn.
3. Chuẩn hóa, chống trùng, kiểm tra chất lượng và cách ly bản ghi nghi lỗi.
4. Nạp dữ liệu hợp lệ vào kho chung và cung cấp view phục vụ BI.
5. Theo dõi thị trường, kế hoạch thu mua và chất lượng dữ liệu trên dashboard.
6. Nhập khối lượng, ngân sách, chọn quan sát giá/tỷ giá để tính chi phí tham chiếu.
7. Tạo cảnh báo theo quy tắc; người dùng xác nhận, cập nhật trạng thái và ghi hành động.
8. AI hỗ trợ phân tích tin và diễn giải bản tin có dẫn nguồn; số liệu và điều kiện cảnh báo do mã xác định tính toán.

## 4. Phạm vi dự kiến

| Hạng mục | Nội dung |
| --- | --- |
| Thu thập và ETL | Collector Python cho nguồn PDF, HTML, XML và RSS/chuyên mục tin; raw, chuẩn hóa, chống trùng, kiểm tra lỗi và truy vết |
| Kho dữ liệu | PostgreSQL, fact/dimension và view KPI thống nhất |
| BI | Ba dashboard: thị trường, kế hoạch thu mua, chất lượng dữ liệu; tối thiểu 10 biểu đồ/bảng tổng cộng theo đề cương |
| Nghiệp vụ | Kế hoạch, kịch bản chi phí, cảnh báo, trạng thái và lịch sử xử lý |
| Giao diện | Trang tin, chi tiết tin, kế hoạch và xử lý cảnh báo bằng Django template |
| AI | Trích sự kiện/chủ đề và tạo bản tin có bằng chứng, có kiểm tra đầu ra |
| Môi trường | Django/Wagtail, Superset, n8n, PostgreSQL và Docker Compose |

Không thuộc MVP: POS, giỏ hàng, luật gợi ý combo, tự động đặt lệnh mua hoặc hệ thống ERP/CRM đầy đủ. Dự báo, chatbot và MCP chỉ là mở rộng có điều kiện; chưa ghi nhận đã triển khai.

## 5. Nguồn dữ liệu dự kiến và giới hạn

| Nguồn | Dữ liệu dự kiến | Điểm cần xác minh |
| --- | --- | --- |
| ICO | Báo cáo PDF giá chỉ báo cà phê | Quyền sử dụng, parser nhiều tháng; giá chỉ báo không phải giá kỳ hạn |
| Giacaphe | Bảng giá và giá kỳ hạn theo từng hợp đồng | Đơn vị, thời điểm, tính đầy đủ; ghi rõ nguồn công bố lại |
| Vietcombank | XML tỷ giá USD/VND | Tách loại mua/bán và thời điểm hiệu lực; lịch sử có thể chưa đủ |
| Nguồn tin ngành | Giacaphe, VietnamBiz và nguồn bổ sung phù hợp | Điều khoản, quyền lưu nội dung, độ liên quan, trùng tin và tần suất |

Khảo sát tải mẫu trong đề cương không đồng nghĩa collector đã vận hành ổn định. Nguồn, quyền và khả năng truy cập phải được xác minh khi triển khai. Nếu nguồn lỗi, chỉ dùng dữ liệu gần nhất với nhãn thời điểm rõ ràng, không giả dữ liệu mới.

## 6. Công nghệ dự kiến

| Thành phần | Công nghệ | Vai trò |
| --- | --- | --- |
| Backend và quản trị | Python, Django, Wagtail | API, nghiệp vụ, tài khoản/quyền và quản trị |
| Giao diện ứng dụng | Django template, HTML/CSS/JavaScript khi cần | Trang tin, kế hoạch và xử lý cảnh báo |
| Dữ liệu | PostgreSQL, SQL | Raw, kho dữ liệu, bảng nghiệp vụ và view BI |
| Dashboard | Apache Superset | Phân tích, bộ lọc và trực quan hóa |
| Điều phối | n8n | Gọi collector, ETL và tác vụ theo lịch |
| AI | LLM qua API, nhà cung cấp/model chờ chốt | Trích sự kiện và bản tin có căn cứ |
| Đóng gói | Docker Compose | Môi trường các dịch vụ |
| Cộng tác | Git/GitHub | Phiên bản, phân công và kiểm tra thay đổi |

## 7. Tổ chức thư mục

Các đường dẫn dưới đây đều tính từ thư mục nhóm `nhom08-65httt/`.

| Đường dẫn | Mục đích |
| --- | --- |
| `danhsachnhom.md` | Thông tin thành viên, nhiệm vụ và đóng góp |
| `README.md` | Giới thiệu, trạng thái và hướng dẫn chạy |
| `docs/` | Đề cương, đặc tả, tài liệu kiểm thử và báo cáo |
| `src/backend/` | Django/Wagtail, API, migration, collector và template trong từng app |
| `src/frontend/` | Thư mục giữ cấu trúc học phần |
| `src/database/` | SQL đối chiếu và tài liệu BI |

## 8. Tài liệu liên quan

- [Danh sách và phân công nhóm](danhsachnhom.md)
- [Đề cương CafeFlow Market BI](docs/De_cuong_CafeFlow_Market_BI_Nhom8.docx)
- [Kế hoạch triển khai, schema và hợp đồng API](docs/ke-hoach-trien-khai.md)
- [Nhật ký tiến độ triển khai](docs/tien-do-trien-khai.md)
- [Theo dõi nghiệm thu R01–R17](docs/theo-doi-nghiem-thu.md)
- [Kịch bản demo CafeFlow](docs/kich-ban-demo.md)
- [Kết quả kiểm tra luồng ICO](docs/kiem-chung-ico.md)
- [Đặc tả dashboard dự kiến](docs/dac-ta-dashboard.md)
- [Đặc tả giao diện tin và cảnh báo dự kiến](docs/dac-ta-tin-va-canh-bao.md)

## 9. Quy tắc làm việc

- Làm việc trên nhánh `nhom08-65httt` và chỉ thêm/sửa tệp bên trong thư mục `nhom08-65httt/`.
- Giữ nguyên `README.md`, `.gitignore` và `_template_nhom/` ở gốc kho theo hướng dẫn học phần.
- Pull bản mới trước khi sửa; chỉ stage đúng tệp phụ trách và kiểm tra trước khi commit.
- Mỗi thành viên tự kiểm tra nội dung và commit bằng danh tính của mình. Không dùng số commit thay cho đánh giá chất lượng công việc.
- Không đưa `.env`, mật khẩu, API key, thư viện cài sẵn hoặc tệp nén lớn vào kho.
- Khi bàn giao, ghi rõ phần đã làm, chưa làm, phụ thuộc và đường dẫn minh chứng.

## 10. Công việc tiếp theo

1. Chốt quyền và điều kiện sử dụng nguồn, schema, KPI, API nghiệp vụ và trạng thái cảnh báo.
2. Mở rộng ETL cho giá nội địa, kỳ hạn công bố lại, FX và tin. Bàn giao view BI cho Trang và API/tài khoản cho Minh.
3. Triển khai kịch bản chi phí, cảnh báo và hành động xử lý, AI có dẫn chứng, rồi kiểm tra đầu cuối theo R17.
