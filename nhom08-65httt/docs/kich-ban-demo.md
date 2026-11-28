# Kịch bản demo CafeFlow Market BI

Chuẩn bị cho TH5 ngày 30/11/2026. Kết quả dưới đây lấy từ các lần chạy ngày 28/11/2026. Mốc Git và trạng thái từng phần nằm trong [nhật ký tiến độ](tien-do-trien-khai.md).

## Chọn môi trường demo

| Môi trường | Điều kiện | URL |
| --- | --- | --- |
| Compose thông thường | Chạy từ `nhom08-65httt/src` theo [README nhóm](../README.md#chạy-luồng-ico-trên-windows), dùng `.env` riêng. Cổng mặc định là 8000. | `http://127.0.0.1:8000` hoặc cổng trong `DJANGO_PORT`. |
| Preview CF-002B.1 | Project Docker riêng `cafeflow-cf002a-preview` trên máy đã thử. Image được build trước commit [19c7b39](https://github.com/DangHuy1302/project-htkdtm/commit/19c7b399dd8eaa657a376664b0da993e8a0e749b) từ mã CF-002B.1 đã kiểm thử. Preview có 110 quan sát ICO tháng 10/2026. | [Preview cục bộ](http://127.0.0.1:18082/) khi các container preview còn chạy trên máy đó. Dùng cho phần xem giao diện và API. |

| Phiên bản mã đang chạy | Trang chủ | Bảng giá ICO | Phần dùng chung |
| --- | --- | --- | --- |
| CF-002A tại `d6d4601` (mốc cũ) | `/` mở bảng giá | `/` | `/api/v1/prices/`, `/cms/` và CSS dùng chung |
| CF-002B.1 tại `19c7b39` hoặc preview cùng mốc mã | `/` mở Tổng quan | `/market/` | `/api/v1/prices/`, `/cms/` và CSS dùng chung |

Trước buổi demo, ghi phiên bản được chọn bằng `git rev-parse --short HEAD` và `git status -sb`. Nếu dùng Compose thông thường, chạy build từ đúng cây mã rồi dùng cổng đã cấu hình. Các lệnh bên dưới dành cho Compose thông thường trên PowerShell, ngoại trừ phần xem preview được ghi riêng. Bản preview và CSDL PostgreSQL cục bộ trong [hồ sơ ICO](kiem-chung-ico.md) là hai môi trường kiểm thử khác nhau.

## 1. Khởi động web và PostgreSQL

- **Mục tiêu** Django chạy, PostgreSQL sẵn sàng và migration đã áp dụng.
- **Điều kiện** Docker Desktop dùng Linux containers. Tạo `.env` từ `.env.example` theo README nếu chưa có. Dùng lại thông tin trong `.env` của volume hiện có. Mở PowerShell từ gốc repo.
- **URL** `$baseUrl/`. Dùng bảng phiên bản ở trên để nhận biết trang hiển thị.

```powershell
Set-Location .\nhom08-65httt\src
$baseUrl = 'http://127.0.0.1:8000'
# Đổi cổng trong $baseUrl nếu DJANGO_PORT khác 8000.
docker compose config --quiet
docker compose up -d --build
docker compose ps
docker compose logs --tail 30 web
docker compose exec -T web python manage.py check
```

- **Mong đợi** `db` healthy, `web` đang chạy, log ghi migration thành công hoặc đã áp dụng và Django lắng nghe cổng 8000 bên trong container.
- **Đã kiểm thử** Compose web/db, migration, Django system check, HTTP trên CSDL trống và giữ dữ liệu qua stop/start.
- **Giới hạn** Compose dự án có hai dịch vụ web/db. Một lần dừng web đã ghi mã `137`, `OOMKilled=false`. PostgreSQL dừng với mã `0`. Nếu cần dừng sau demo, dùng `docker compose stop` để giữ volume.

## 2. Thu thập PDF ICO tháng lưu trữ

- **Mục tiêu** Minh họa từ PDF công khai đến run, tài liệu raw và giá chuẩn hóa.
- **Điều kiện** Đã xong kịch bản 1, container web truy cập được HTTPS tới ICO. Chạy trên CSDL demo.
- **Nguồn** [PDF ICO tháng 10/2026](https://ico.org/documents/prices/I-CIP_10.2026.pdf).

```powershell
docker compose exec -T web python manage.py collect_ico --month 2026-10
```

- **Mong đợi** Log có `run`, `http`, `raw`, `rows`, `rejected_rows`, `created_prices`, `revised_prices` và `unchanged_prices`. Nếu tháng này đã nạp, các giá giống nhau có thể được giữ nguyên ngay ở lần demo đầu.
- **Đã kiểm thử** Bản PDF dùng trong lần chạy Compose có 22 ngày và 110 giá thuộc 5 chuỗi chỉ báo. Trên CSDL trống tạo 110 quan sát, không có dòng bị loại. CSDL kiểm thử cục bộ riêng đã thu 205 quan sát từ hai tháng 10 và 11.
- **Giới hạn** Kết quả phụ thuộc phiên bản PDF nguồn và tình trạng CSDL. Các số trên là kết quả đã đo, nên so với log thực tế của buổi demo. Lệnh không có `--month` tải PDF hiện tại, có thể thay đổi theo lịch công bố.

## 3. Đối chiếu dữ liệu bằng SQL

- **Mục tiêu** Truy vết giá về nguồn và kiểm tra cùng mẫu qua PostgreSQL và API.
- **Điều kiện** Chạy từ `src`. CSDL demo đã có ít nhất một run ICO.
- **URL đối chiếu** `$baseUrl/api/v1/prices/?source=ico&series=robustas&price_type=indicator`.

```powershell
Get-Content -LiteralPath .\database\kiem-tra-ico.sql |
    docker compose exec -T db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
$prices = Invoke-RestMethod "$baseUrl/api/v1/prices/?source=ico&series=robustas&price_type=indicator"
$prices.results[0] | Select-Object effective_date, value, unit, source_url, run_id, collected_at, content_hash
```

- **Mong đợi** Truy vấn đầu ghi các run ICO, trạng thái HTTP, số đếm, hash và kích thước raw. Truy vấn sau lấy 5 bản Robustas hiện hành gần nhất. So giá, ngày, đơn vị và run của cùng quan sát với API.
- **Đã kiểm thử** Bản chỉ có ICO tháng 10 khớp ngày 30/10/2026, `156.8400` US cents/lb. CSDL có thêm tháng 11 khớp ngày 26/11/2026, `140.2700` US cents/lb.
- **Giới hạn** Ngày hiệu lực gần nhất thay đổi khi nạp thêm tháng. Kiểm tra này dùng [hai truy vấn đọc](../src/database/kiem-tra-ico.sql).

## 4. Kiểm tra nạp lại cùng raw

- **Mục tiêu** Chứng minh một lần chạy mới có nhật ký và cùng nội dung không tạo giá trùng.
- **Điều kiện** Đã chạy kịch bản 2 ít nhất một lần. Hai lần tải có cùng hash và không có tiến trình khác đang nạp vào CSDL demo.
- **URL đo số quan sát** `$baseUrl/api/v1/prices/?source=ico`.

```powershell
$before = (Invoke-RestMethod "$baseUrl/api/v1/prices/?source=ico").count
docker compose exec -T web python manage.py collect_ico --month 2026-10
if ($LASTEXITCODE -ne 0) { throw 'Collector ICO thất bại' }
$after = (Invoke-RestMethod "$baseUrl/api/v1/prices/?source=ico").count
if ($before -ne $after) { throw "Số quan sát thay đổi từ $before thành $after" }
Write-Output "Số quan sát ICO giữ nguyên: $after"
```

- **Mong đợi** `created_prices=0` và `revised_prices=0` khi nguồn không đổi. Chạy lại SQL ở kịch bản 3 để xác nhận có run mới với cùng SHA-256.
- **Đã kiểm thử** Compose nạp lặp tháng 10 giữ nguyên 110 quan sát và dùng lại cùng raw. CSDL cục bộ nạp lặp tháng 11 giữ nguyên 95 giá của tháng đó. Ca mất kết nối đã lưu log và giữ nguyên 205 quan sát trong CSDL cục bộ.
- **Giới hạn** Nếu hash thay đổi, đối chiếu bản nguồn trước khi kết luận ca nạp lặp. Chưa kiểm chứng một lần sửa giá thực giữa hai lần tải.

## 5. Mở CafeFlow, API và Wagtail

- **Mục tiêu** Trình bày luồng đọc từ PostgreSQL tới API và giao diện, cùng trạng thái các vùng Tổng quan nếu chạy CF-002B.1.
- **Điều kiện** Web đã chạy và có dữ liệu. Đối với preview, đặt `$baseUrl = 'http://127.0.0.1:18082'` và dùng các thao tác đọc bên dưới.

| Thao tác và URL | Mong đợi |
| --- | --- |
| Mở `$baseUrl/` | Tại `d6d4601`, thấy bố cục CafeFlow và bảng giá. Tại CF-002B.1, thấy Tổng quan với các vùng đang chờ triển khai và nút mở bảng giá ICO. |
| Trên CF-002B.1, bấm **Thị trường** hoặc **Mở bảng giá ICO** tới `$baseUrl/market/`, sau đó bấm **Tổng quan** | Bảng giá hiện tối đa 25 quan sát ở phiên bản hiện hành, có ngày, đơn vị và liên kết nguồn. Mục active đổi đúng khi chuyển trang. |
| Bấm **Xem dữ liệu JSON** hoặc mở `$baseUrl/api/v1/prices/?series=robustas` | API trả kết quả JSON gồm `count`, `next`, `previous`, `results`. Có thể so một giá cùng ngày với SQL. |
| Mở **Quản trị** tại `$baseUrl/cms/` khi chưa đăng nhập | Chuyển tới trang đăng nhập Wagtail. |

- **Đã kiểm thử** CF-002A đã thử layout và empty state. CF-002B.1 đã thử HTTP, CSS, điều hướng ở 1440/390/320 px và đối chiếu bốn phản hồi API trước/sau khớp từng byte. Trong CF-DOC-001, preview vẫn trả HTTP 200 cho Tổng quan, Thị trường và CSS. API lọc Robustas trả tổng 22 quan sát.
- **Giới hạn** KPI, biến động, biểu đồ, theo dõi nguồn trên Tổng quan, phân hệ nghiệp vụ và quyền Admin/Analyst còn chờ triển khai hoặc kiểm thử. Kiểm tra Wagtail mới tới màn hình đăng nhập.

Trước TH5, nhóm trưởng ghi phiên bản chọn demo, môi trường, người trình bày và kết quả diễn tập. Lưu minh chứng có thể chia sẻ tại [bảng nghiệm thu](theo-doi-nghiem-thu.md), gồm run/hash hoặc ảnh đã loại thông tin nhạy cảm.
