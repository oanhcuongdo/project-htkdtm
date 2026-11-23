# Quy tắc làm việc nhóm (Nhóm 03, 65HTTT, EduVision BI)

Áp dụng cho **mọi thành viên**. Nguồn gốc: `README.md` gốc của giảng viên (mục nhánh và mục commit) cộng với quy định riêng của nhóm.
Tài liệu liên quan: [docs/quy_uoc_ma_nguon.md](docs/quy_uoc_ma_nguon.md) (quy ước viết mã, API, migration, dữ liệu) và [docs/review_pull_request.md](docs/review_pull_request.md) (mẫu mô tả PR và danh sách kiểm tra khi duyệt).

## 1. Quy tắc cứng (vi phạm là sai)

1. **Không co-author, không dấu vết công cụ** trong thông điệp commit và mô tả PR: không `Co-Authored-By:`, không dòng "Generated with ...". Công cụ có nhắc thêm thì vẫn không thêm.
2. **Không push thẳng** vào nhánh `nhom03-65httt` và **tuyệt đối không đụng `main`**. Mỗi việc làm trên nhánh riêng rồi mở Pull Request.
3. **Chỉ làm trong thư mục `nhom03-65httt/`.** Không sửa `README.md` gốc, `.gitignore` gốc, `_template_nhom/`, thư mục nhóm khác; không để tệp nào ở gốc kho.
4. **Cấm `git add .`, `git add -A`, `git commit -a`.** Luôn `git add` từng đường dẫn cụ thể.
5. **Không đưa lên Git:** dữ liệu thật (CSV, Excel, tệp gán nhãn), `.env`, khóa API và token, trọng số mô hình (`*.pt`, `*.safetensors`, `*.bin`, `*.ckpt`, `*.pkl`), `node_modules/`, `dist/`, `venv/`, `__pycache__/`, `.vscode/`, `.idea/`, tệp nén, `~$*`. Chỉ được đưa `.env.example` với giá trị rỗng. Repo công khai, lộ khóa là phải thu hồi khóa ngay.
6. **Một việc = một nhánh = một PR.** Không gộp việc của người khác vào nhánh của mình.
7. Email trong `git config user.email` phải trùng email tài khoản GitHub của bạn, để lịch sử ghi đúng người.
8. Không tự bấm **Merge**. Nhóm trưởng duyệt và merge.

## 2. Đặt tên nhánh

Mẫu: `nhom03-65httt-<ten>-<viec>`, chữ thường, không dấu, nối bằng dấu gạch ngang.
Ví dụ: `nhom03-65httt-thaianh-appstore`, `nhom03-65httt-hung-kpi-api`.

Mỗi việc mới tạo nhánh mới từ bản `nhom03-65httt` mới nhất. Không dùng lại nhánh đã merge.

```bash
git fetch origin
git checkout nhom03-65httt
git pull origin nhom03-65httt
git checkout -b <TEN-NHANH>
git branch --show-current        # phải ra đúng tên nhánh của bạn
```

## 3. Thông điệp commit

Mẫu bắt buộc: `<loại>(nhom03-65httt): <mô tả>`

- Loại: `feat` (chức năng, mã nguồn), `fix` (sửa lỗi), `docs` (tài liệu).
- Mô tả tiếng Việt **không dấu**, chữ thường, **một dòng**, nói đúng việc đã làm.
- Dùng đúng **một** tùy chọn `-m`, không thân thư, không `--trailer`.

```bash
git commit -m "feat(nhom03-65httt): api du bao m3 theo nen tang"
```

Mỗi commit một chủ đề. Việc lớn có thể tách nhiều commit trên cùng nhánh.

## 4. Quy trình mỗi lần commit

1. `git branch --show-current` không được là `main` hay `nhom03-65httt`.
2. `git status`: mọi đường dẫn định commit phải bắt đầu bằng `nhom03-65httt/`. Tệp lạ (csv, xlsx, `.env`, `node_modules`) thì **không add**.
3. `git add nhom03-65httt/<duong-dan-cu-the>`, rồi `git status` lần nữa: chỉ thấy đúng tệp dự định.
4. `git commit -m "..."`.
5. Kiểm tra sau commit:
   ```bash
   git log -1 --format=%B             # không có Co-Authored-By hay dòng ghi công
   git show --stat --format= HEAD     # mọi đường dẫn bắt đầu bằng nhom03-65httt/
   ```
6. Lỡ có dòng co-author mà **chưa push**: `git commit --amend -m "<thong-diep-dung>"`. Đã push thì báo nhóm trưởng, không tự sửa lịch sử.

## 5. Push và Pull Request

```bash
git push -u origin <TEN-NHANH>
```

Trên GitHub, **kiểm tra đúng đích** trước khi bấm tạo:

- **base repository:** `thanhtung111205/project-htkdtm` (kho Fork của nhóm trưởng), **không phải** `oanhcuongdo/project-htkdtm`.
- **base:** `nhom03-65httt`; **compare:** nhánh của bạn.
- **Tiêu đề PR:** giống thông điệp commit.
- **Mô tả PR:** theo mẫu trong [docs/review_pull_request.md](docs/review_pull_request.md).
- Tab **Files changed**: 100% đường dẫn bắt đầu bằng `nhom03-65httt/`.

Sau khi nhóm trưởng merge, cập nhật máy và xóa nhánh cũ:

```bash
git checkout nhom03-65httt && git pull origin nhom03-65httt
git branch -d <TEN-NHANH>
```

## 6. Nhịp làm việc

- **Pull trước khi làm** mỗi buổi: `git pull origin nhom03-65httt`.
- **PR nhỏ, merge sớm.** Một PR nên đọc xong trong khoảng 15 phút. PR lớn hơn thì tách.
- **Vướng quá nửa buổi thì báo ngay** trong nhóm chat, không đợi đến hạn.
- **Nhóm trưởng phản hồi PR** trong vòng 24 giờ; người viết sửa theo góp ý trên cùng nhánh, không mở PR mới.
- **Sửa lỗi sau khi merge:** nhánh `fix` mới, PR mới.

## 7. Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
|---|---|---|
| `protected branch` khi push `nhom03-65httt` | Nhánh nhóm cấm push thẳng | Đúng quy định: push nhánh riêng rồi mở PR |
| `Permission denied` hoặc 403 | Chưa là Collaborator, hoặc đang push `upstream` | Nhận lời mời Collaborator; chỉ push `origin` |
| `non-fast-forward` trên nhánh riêng | Nhánh có thay đổi mới | `git pull --rebase origin <TEN-NHANH>` rồi push lại |
| PR có tệp ngoài `nhom03-65httt/` | Lỡ `git add` nhầm | Gỡ tệp khỏi commit, tạo lại nhánh sạch |
| PR mở nhầm vào kho của giảng viên | Sai base repository | Đóng PR, mở lại với base là Fork của nhóm trưởng |
| Thấy `.csv`, `.xlsx`, `.env`, `node_modules` trong `git status` | Dữ liệu, khóa không được commit | Không add; kiểm tra `.gitignore` |
| Commit có `Co-Authored-By` | Công cụ tự thêm | `git commit --amend -m "..."` khi chưa push |
| Xung đột khi merge | Hai người sửa cùng tệp | Pull bản mới, giải quyết xung đột trên nhánh của bạn, báo nhóm trưởng nếu không chắc |
