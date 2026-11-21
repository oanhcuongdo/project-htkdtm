# Thư mục models/

Chứa trọng số mô hình đã huấn luyện (PhoBERT M1, ABSA M2, LightGBM M3...). Trọng số thường vài trăm MB nên
**không đưa vào Git**; `.gitignore` đã chặn cả thư mục này (trừ file README) và các đuôi `.safetensors`, `.ckpt`, `.pt`, `.pth`, `.onnx`, `.joblib`.

## Cách lấy trọng số

1. Tải từ thư mục Drive của nhóm: **[điền liên kết sau khi nhóm tạo]**.
2. Giải nén vào `models/`, giữ cấu trúc:

```
models/
├── m1_phobert_sentiment/   # M1 - cảm xúc 3 lớp
├── m2_absa/                # M2 - cảm xúc theo khía cạnh
└── m3_forecast/            # M3 - dự báo
```

3. Đặt đường dẫn trong `.env` (xem `.env.example`).

Người huấn luyện xong mô hình nào thì tải lên Drive, ghi lại phiên bản và ngày huấn luyện (khớp bảng `dim_model`), rồi báo nhóm.
Nếu sau này cần quản lý phiên bản trọng số bằng Git thì dùng Git LFS, và nhớ kiểm tra hạn mức dung lượng của GitHub trước.
