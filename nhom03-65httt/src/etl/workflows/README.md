# Workflow n8n (T8: tự động hóa)

Đề cương yêu cầu workflow n8n **chạy thật** cho ba việc: lập lịch ETL hằng ngày, nút "Cập nhật dữ liệu" trên website, và gửi email cảnh báo
khi vượt ngưỡng. Thư mục này chứa ba workflow (JSON, không chứa bí mật), script cài đặt và kiểm thử.

| Tệp | Làm gì | Kích hoạt khi |
|---|---|---|
| `01_etl_hang_ngay.json` | 02:00 mỗi ngày gọi bộ chạy ETL, chờ xong, **gửi email nếu vòng lỗi** hoặc bị từ chối | `--activate daily` |
| `02_webhook_cap_nhat_du_lieu.json` | Webhook `POST /webhook/eduvision-refresh` cho nút "Cập nhật dữ liệu": có khóa, trả 202 và mã công việc | `--activate webhook` |
| `03_email_canh_bao.json` | Mỗi 15 phút lấy cảnh báo mới trong `dw.fact_alert`, **gộp thành một email**, rồi đánh dấu đã gửi | `--activate alert` |

Cả ba có nút **Chạy thử bằng tay** (trừ webhook): mở workflow trong n8n rồi bấm *Execute workflow* để thử bất cứ lúc nào.

## Cách hoạt động

```
n8n (Docker) ──HTTP, khóa X-Runner-Token──▶ etl-runner (Docker) ──▶ run_pipeline.py ──▶ PostgreSQL
     │                                           (src/etl/runner)       (collector + ETL, nhật ký data/logs)
     └──SMTP──▶ Mailpit (hộp thư thử)  hoặc SMTP thật
```

- **`etl-runner`** (`src/etl/runner/`) bọc `run_pipeline.py` (T8a) sau một HTTP nhỏ, **chỉ nghe trong mạng Compose** (không mở cổng ra máy).
  Lý do: n8n chạy trong Docker nên không gọi được Python trên máy; nút Execute Command của n8n 2.x lại tắt sẵn vì an toàn.
  Chống chạy chồng bằng cùng khóa `pipeline.lock` với Task Scheduler và lần chạy tay; chờ tối thiểu `ETL_RUNNER_MIN_INTERVAL` giây giữa hai lần bấm
  (409 khi đang chạy, 429 khi bấm quá nhanh). Chỉ nhận `only`, `count` (1 đến 500), `dry_run`, `skip_collect`; lệnh ghép từ giá trị đã kiểm tra, không qua shell.
- **Đánh dấu cảnh báo đã gửi** dùng cột `dw.fact_alert.notified_at` (migration 0005), **không đổi `status`**: website vẫn thấy cảnh báo "mới" sau khi email đã gửi.
  Đánh dấu chạy SAU khi gửi: gửi lỗi thì không mất cảnh báo (lần sau gửi lại); gửi được mà đánh dấu lỗi thì lần sau có thể gửi lặp một email.
- **Mailpit** là hộp thư thử (http://localhost:8025): email chỉ nằm ở đó, không tới người thật. Muốn gửi thật: điền `SMTP_*` trong `.env` (xem `.env.example`) rồi chạy lại `setup_n8n.py`
  và đổi địa chỉ nhận trong nút *Gửi email* (mặc định `canh-bao@eduvision.local`).

## Cài đặt (làm một lần)

1. Điền trong `.env` (xem `.env.example`; tạo khóa bằng `python -c "import secrets; print(secrets.token_urlsafe(32))"`):
   `ETL_RUNNER_TOKEN`, `N8N_WEBHOOK_KEY` (hai khóa **khác nhau**, mỗi khóa ít nhất 16 ký tự), `N8N_ENCRYPTION_KEY` (đặt một lần rồi giữ nguyên, đổi là mất credentials đã lưu).
2. Dựng dịch vụ:
   ```powershell
   docker compose --profile automation up -d --build
   ```
   Có ba dịch vụ mới: `etl-runner`, `n8n` (http://localhost:5678), `mailpit` (http://localhost:8025). Chờ `docker ps` thấy cả ba `healthy`.
3. Mở http://localhost:5678, tạo **tài khoản chủ** (email và mật khẩu của bạn, chỉ lưu trên máy).
4. Nạp credentials và workflow:
   ```powershell
   python src/etl/workflows/setup_n8n.py
   ```
   Script lấy mật khẩu từ `.env` đưa thẳng vào n8n (không ghi ra tệp, không in ra màn hình), tạo 4 credentials
   (`EduVision PostgreSQL`, `EduVision SMTP`, `EduVision ETL Runner`, `EduVision Webhook Key`) và nhập 3 workflow ở trạng thái **tắt**.
5. Kích hoạt:
   ```powershell
   python src/etl/workflows/setup_n8n.py --activate alert webhook      # email cảnh báo và webhook
   python src/etl/workflows/setup_n8n.py --status                      # xem workflow nào đang bật
   ```
   Chạy lại script bất cứ lúc nào (ví dụ sau khi sửa workflow): workflow đang bật được giữ nguyên trạng thái.

## Chọn MỘT bộ lập lịch ETL cho mỗi giai đoạn

Có hai cách chạy ETL hằng ngày: **Windows Task Scheduler** (`src/etl/schedule/`) và workflow `01_etl_hang_ngay` của n8n. Đừng bật cả hai cùng lúc:
khóa `pipeline.lock` chặn chạy chồng nhưng vẫn là **hai lần thu thập mỗi ngày**, trái với `docs/dao_duc_phap_ly.md` (không tăng tần suất).

Cách chuyển sang n8n (đúng đề cương) sau khi đã thử xong:
```powershell
# 1. thử một vòng nhỏ qua webhook (dry-run, không ghi vào kho), xem kết quả
$key = (Select-String -Path .env -Pattern '^N8N_WEBHOOK_KEY=').Line.Split('=',2)[1]
Invoke-RestMethod -Method Post -Uri http://localhost:5678/webhook/eduvision-refresh -Headers @{ 'X-Webhook-Key' = $key } `
  -ContentType 'application/json' -Body '{"only":["ELSA Speak"],"count":5,"dry_run":true}'
# 2. gỡ lịch Windows rồi bật lịch n8n
.\src\etl\schedule\register_daily_task.ps1 -Remove
python src/etl/workflows/setup_n8n.py --activate daily
```
Bằng chứng "tự chạy N ngày liên tiếp" (`python src/etl/run_pipeline.py --report`) đọc cùng một nhật ký `data/logs/pipeline_runs.jsonl`
nên liền mạch khi đổi bộ lập lịch. Báo cáo cần ghi trung thực: từ ngày nào chạy bằng Task Scheduler, từ ngày nào bằng n8n.

## Webhook "Cập nhật dữ liệu" (cho API và website)

```
POST http://localhost:5678/webhook/eduvision-refresh
Header: X-Webhook-Key: <N8N_WEBHOOK_KEY>
Body (tùy chọn): {"only": ["ELSA Speak"], "count": 100, "dry_run": false, "skip_collect": false}
```
| Mã | Ý nghĩa |
|---|---|
| 202 | Đã bắt đầu chạy nền; trả `job_id` |
| 403 | Thiếu hoặc sai khóa |
| 409 | Đang có một vòng chạy (không sinh công việc thứ hai) |
| 429 | Vừa chạy xong, chờ `retry_after` giây |
| 422 | Tham số không hợp lệ (nền tảng không có trong cấu hình, `count` ngoài 1 đến 500, trường lạ) |

Khóa này chỉ để **máy chủ** (API của nhóm, mục HA4) gọi; **không đưa khóa xuống trình duyệt**. Quyền Admin kiểm tra ở API, trước khi API gọi webhook.

## Kiểm thử đã làm (n8n 2.49.7, Docker thật)

- Bộ chạy: 28 test (xác thực, kiểm tra đầu vào, chống chèn lệnh, 409/429, trạng thái `failed` và `skipped`); workflow và script: 19 test.
- Email cảnh báo: một email gộp, **chạy lại không gửi lặp**, cảnh báo mới thêm sau vẫn được gửi, nội dung HTML được vô hiệu hóa.
- Lập lịch: ba tình huống (thành công không gửi email; tham số sai gửi email "không bắt đầu được"; vòng ETL thất bại thật gửi email "BỊ LỖI").
- Webhook: không khóa và sai khóa 403; tham số sai và chèn lệnh 422; hợp lệ 202; bấm lại ngay 409.
- Chạy thu thập thật trong container (Google Play qua Internet) thành công.

## Giới hạn đã biết

- Trạng thái công việc chỉ giữ trong bộ nhớ của `etl-runner` (khởi động lại thì mất); nhật ký bền vững là `data/logs/pipeline_runs.jsonl`.
- Webhook chưa có giao diện hiển thị tiến độ: website có thể gọi `GET /status` của bộ chạy thông qua API của nhóm khi HA4 làm xong.
- Email chưa có "đề xuất hành động và bộ phận phụ trách" (đề cương mục khuyến nghị): cần cột tương ứng do T7 sinh vào `fact_alert`; bổ sung vào nút *Gộp thành một email* khi có.
