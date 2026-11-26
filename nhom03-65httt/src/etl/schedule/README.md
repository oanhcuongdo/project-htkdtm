# Lịch chạy pipeline tự động (T8a)

Chỉ tiêu của đề cương: pipeline **tự chạy liên tục** tối thiểu 3 ngày (mục tiêu 7, mở rộng 14). Bằng chứng là nhật ký các vòng chạy.

## Một vòng gồm
1. Gọi collector Google Play và App Store cho từng nền tảng trong `config/platforms.yml` (giãn cách tối thiểu 2 giây).
2. Nạp các CSV mới qua `raw`, `clean`, `dw` (loại trùng theo `(source, review_id)`, chạy lại không sinh trùng).
3. Ghi một dòng vào `data/logs/pipeline_runs.jsonl` (ngoài Git).

```bash
python src/etl/run_pipeline.py                       # một vòng đầy đủ
python src/etl/run_pipeline.py --only "ELSA Speak" --count 20
python src/etl/run_pipeline.py --dry-run             # thử, hoàn tác ETL
python src/etl/run_pipeline.py --report              # bằng chứng: số ngày liên tiếp (thoát mã 3 nếu chưa đủ 3 ngày)
```

Trạng thái mỗi vòng: `success` (mọi collector ổn), `partial` (một vài collector lỗi, ETL vẫn chạy), `failed` (ETL lỗi hoặc mọi collector lỗi).

## Bật lịch hằng ngày trên Windows
```powershell
.\nhom03-65httt\src\etl\schedule\register_daily_task.ps1 -WhatIf   # xem trước
.\nhom03-65httt\src\etl\schedule\register_daily_task.ps1            # đăng ký, 02:00 mỗi ngày
Start-ScheduledTask -TaskName EduVisionBI-Pipeline                  # chạy thử ngay
.\nhom03-65httt\src\etl\schedule\register_daily_task.ps1 -Remove    # gỡ
```
Linux hoặc macOS dùng cron, ví dụ `0 2 * * * cd /duong/dan/nhom03-65httt && python src/etl/run_pipeline.py`.

## Điều kiện để đủ 3 ngày
- Máy chạy phải bật (hoặc để tác vụ chạy bù khi bật lại), Docker Desktop chạy (`restart: unless-stopped` đã đặt cho PostgreSQL và API).
- Cài thư viện collector một lần: `pip install -r src/etl/collectors/requirements.txt`.
- Bật lịch chậm nhất tối 27/11 để đến 30/11 có đủ 3 ngày liên tiếp. Chưa đủ thì ghi **số ngày thật** vào báo cáo.
