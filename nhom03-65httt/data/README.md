# Thư mục data/

Chứa dữ liệu của đồ án trên **máy từng thành viên**. Mọi thứ trong thư mục này (trừ file này) bị `.gitignore` chặn,
vì repo là công khai và dữ liệu gồm nội dung đánh giá/bình luận do người dùng viết.

```
data/
├── raw/      # dữ liệu thô đúng như thu thập được (đánh giá, bình luận YouTube, tin báo chí, UIT-VSFC)
└── clean/    # dữ liệu đã làm sạch, loại trùng, chuẩn hóa (đầu vào của ETL)
```

Tạo hai thư mục con ở máy mình: `mkdir -p data/raw data/clean`.

Chia sẻ dữ liệu trong nhóm qua kênh riêng (Drive của nhóm), không qua Git. Không đăng dữ liệu thô lên bất kỳ nơi công khai nào.
Xem ghi chú đạo đức và pháp lý: [../docs/dao_duc_phap_ly.md](../docs/dao_duc_phap_ly.md).
