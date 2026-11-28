# Kiểm chứng luồng giá ICO

Kiểm tra ngày 28/11/2026 theo giờ Việt Nam trên Windows với Python 3.13.9, Django 5.2.19, Wagtail 7.4.4, DRF 3.18.3 và PostgreSQL 17.11 chạy cục bộ. Dùng nguồn HTTPS thật và một CSDL PostgreSQL kiểm thử riêng.

## Nguồn và ý nghĩa dữ liệu

| Nguồn | Kiểm tra và cách sử dụng |
| --- | --- |
| ICO | Trang công bố dẫn đến PDF hiện tại và kho tháng trước. Collector đã tải trực tiếp hai PDF, đọc năm chuỗi chỉ báo theo ngày, đơn vị US cents/lb. Hai ngày trống trong mẫu tháng 11 được bỏ qua. [Trang công bố ICO](https://ico.org/resources/public-market-information/) · [PDF hiện tại](https://ico.org/documents/I-CIP.pdf) · [PDF tháng 10](https://ico.org/documents/prices/I-CIP_10.2026.pdf) |
| Giacaphe | Trang bảng giá hiển thị giá nội địa VND/kg theo ngày 27/11 trong lần khảo sát. Khi tích hợp, lưu nội địa và kỳ hạn do Giacaphe công bố lại ở hai loại giá riêng; đối chiếu mã kỳ hạn, thị trường và giá/đơn vị ở từng dòng. [Bảng giá Giacaphe](https://giacaphe.com/gia-ca-phe-noi-dia/) |
| ICE | Đặc tả hợp đồng Robusta (RC) niêm yết USD/tấn. Tình trạng truy cập feed trực tiếp vẫn cần xác nhận. [Đặc tả ICE](https://www.ice.com/products/37089079/Robusta-Coffee-Futures) |
| Vietcombank | Tải và đọc XML trực tiếp, xác nhận trường `DateTime` và USD `Buy` / `Transfer` / `Sell`. Mẫu lúc 00:58:28 ngày 28/11 có lần lượt 25.620, 25.650 và 26.030 VND/USD. Chưa nạp FX vào CSDL. [Trang tỷ giá](https://www.vietcombank.com.vn/vi-VN/KHCN/Cong-cu-Tien-ich/Ty-gia) · [XML nguồn](https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx) |

Đợt này kiểm chứng khả năng tải và phân tích kỹ thuật. Nhóm còn phải chốt quyền lưu, hiển thị và tái phân phối theo từng nguồn, cũng như yêu cầu nguồn trực tiếp từ sàn với giảng viên. ICO công bố PDF và có kênh yêu cầu dữ liệu dạng bảng qua `stats@ico.org`. [Thông tin cung cấp dữ liệu ICO](https://ico.org/resources/public-market-information/)

## Kết quả theo lần chạy

| Run | Thời điểm thu thập UTC+07 | HTTP | Ngày có giá | Giá mới / sửa / giữ nguyên | Raw |
| --- | --- | --- | --- | --- | --- |
| 1, ICO tháng 11 | 28/11 01:11:06 | 200 | 19 | 95 / 0 / 0 | 1 |
| 2, nạp lặp tháng 11 | 28/11 01:11:10 | 200 | 19 | 0 / 0 / 95 | 1 |
| 3, ICO tháng 10 | 28/11 01:11:17 | 200 | 22 | 110 / 0 / 0 | 2 |
| 4, lỗi kết nối trong môi trường chặn HTTPS | chưa tải được | chưa nhận phản hồi | 0 | 0 / 0 / 0 | — |

- Raw 1 có 110.806 byte, SHA-256 `d275d4761c35ac7053ed8d695b52debfdc1a452df8ba83fd74c2546f4c4234a8`. Raw 2 có 115.523 byte, SHA-256 `90e03c0390d58cdccd4bac215f26f854cee75f8cf299c64bdf2298ae32cae56c`.
- PostgreSQL có 205 quan sát hiện hành, 2 PDF raw, 3 run thành công. Run 4 lưu lỗi kết nối và thời điểm kết thúc, giữ nguyên 205 quan sát. Hai PDF nguồn có 0 dòng bị loại. Khóa PostgreSQL chặn lần chạy chồng khi một session khác đang giữ khóa.
- API `/api/v1/prices/?series=robustas` trả HTTP 200, 41 quan sát và 25 quan sát trên trang đầu. Bản gần nhất có ID 95, ngày hiệu lực 26/11/2026, giá `140.2700`, loại `indicator`, run 1. Trang `/` qua HTTP cục bộ trả 200 và hiển thị cùng giá 140,27 cùng liên kết PDF. SQL trả cùng ngày, nguồn, giá và đơn vị. Kiểm tra thêm truy vấn rỗng và trang đăng nhập Wagtail qua Django test client.
- `pip check`, `manage.py check`, migration PostgreSQL, `makemigrations --check --dry-run` và [truy vấn đối chiếu](../src/database/kiem-tra-ico.sql) đều chạy thành công.

## Kiểm tra lại bằng Docker Compose

Ngày 28/11/2026, Docker Desktop chạy hai dịch vụ `web` và `db` với CSDL kiểm thử riêng. `docker compose config --quiet`, build image và migration đều qua. Trang và API trả HTTP 200 từ CSDL trống. Hai lần chạy `collect_ico --month 2026-10` cùng nhận HTTP 200. Lần đầu ghi 110 giá trong 22 ngày và lần sau giữ nguyên cả 110 giá với cùng tài liệu raw.

SQL, API và trang web khớp giá chỉ báo Robustas ngày 30/10/2026 là 156,84 US cents/lb. Sau `docker compose stop` và `docker compose start`, API vẫn trả 22 quan sát Robustas với cùng giá gần nhất và SHA-256. PostgreSQL gắn volume tại `/var/lib/postgresql/data` và dừng với mã 0. Container web kết thúc với mã 137, Docker ghi `OOMKilled=false`. Cần kiểm tra dừng web bằng tín hiệu kết thúc thông thường. Các container kiểm thử đã dừng và volume được giữ lại.

Còn chờ kiểm chứng bản sửa giá thực giữa hai lần tải, cách ly dòng lỗi có sẵn trong PDF ICO, quyền Admin/Analyst và lịch n8n. Hai mẫu tháng chưa đáp ứng chỉ tiêu lịch sử của đề cương. Các mã R01–R17 vẫn chờ nghiệm thu theo tiêu chí tương ứng.
