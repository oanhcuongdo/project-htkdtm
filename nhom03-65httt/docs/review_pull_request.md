# Mẫu mô tả Pull Request và danh sách kiểm tra khi duyệt (Nhóm 03)

Bổ sung cho [CONTRIBUTING.md](../CONTRIBUTING.md) và [quy_uoc_ma_nguon.md](quy_uoc_ma_nguon.md).

## 1. Mẫu mô tả PR (người làm điền)

Sao chép khối dưới đây vào phần mô tả khi mở PR. Không thêm dòng ghi công công cụ.

```markdown
## Đã làm gì
- (1 đến 3 gạch đầu dòng, đúng phạm vi của nhánh)

## Cách kiểm tra
Lệnh chạy và kết quả mong đợi, ví dụ:
- `cd nhom03-65httt/src/backend && pytest` → tất cả qua
- `curl -X POST http://127.0.0.1:8000/api/v1/predict/aspects -d '{"text":"..."}'` → trả 200 với 4 khía cạnh

## Kết quả chạy thử
(Dán kết quả, đã bỏ dữ liệu nhạy cảm, khóa và đường dẫn máy cá nhân.)

## Ảnh hưởng đến người khác
- Có sửa tệp dùng chung (`main.py`, `routes.tsx`, migration...) không? Nếu có, nêu rõ dòng nào.
- Có cần người khác làm gì sau khi merge không (chạy migration, cài gói mới...)?

## Danh sách tự kiểm tra
- [ ] Mọi đường dẫn trong tab Files changed bắt đầu bằng `nhom03-65httt/`
- [ ] Không có dữ liệu thật, `.env`, khóa, trọng số mô hình
- [ ] Thông điệp commit đúng mẫu, không co-author
- [ ] Kiểm thử liên quan đã chạy và qua
```

## 2. Danh sách kiểm tra của người duyệt (nhóm trưởng)

**Hình thức**
- [ ] Đích PR đúng: Fork của nhóm trưởng, base `nhom03-65httt`.
- [ ] Tab Files changed chỉ chứa `nhom03-65httt/...`; không có tệp lạ (csv, xlsx, `.env`, `node_modules`, `dist`, trọng số).
- [ ] Thông điệp commit đúng `<loại>(nhom03-65httt): <mô tả không dấu>`, không `Co-Authored-By`.
- [ ] PR đúng một việc, đúng phạm vi nhánh; nhỏ đủ để đọc hết.

**Nội dung**
- [ ] Chạy được theo đúng "Cách kiểm tra" trong mô tả (nhóm trưởng tự chạy lại ít nhất một lần).
- [ ] Không thay đổi hợp đồng API đã chốt khi chưa báo.
- [ ] Không sửa tệp của người khác ngoài những dòng cần thiết (`main.py`, `routes.tsx`).
- [ ] Công thức BHI, KPI trùng `docs/kpi_bhi.md`; SQL và Python cho kết quả giống nhau trên dữ liệu mẫu.
- [ ] Migration chạy lại hai lần không lỗi, có `downgrade`, số phiên bản không trùng.
- [ ] Mô hình có baseline và chỉ số đánh giá đi kèm; có đặt hạt ngẫu nhiên.
- [ ] Không có khóa, mật khẩu, thông tin cá nhân trong mã, nhật ký hay ảnh chụp.

**Quyết định**
- Đạt: bấm Merge (người duyệt tự bấm), nhắc người làm cập nhật máy và xóa nhánh cũ.
- Cần sửa: ghi góp ý cụ thể, nêu rõ mức độ "bắt buộc" hay "nên làm"; người làm sửa trên cùng nhánh.
- Không đạt phạm vi: yêu cầu tách PR.
