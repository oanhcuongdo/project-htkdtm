# Hướng Dẫn Nộp Mã Nguồn Và Báo Cáo Đồ Án (Hệ Thống Kinh Doanh Thương Mại)

Kho lưu trữ này được thiết lập để quản lý và thu thập mã nguồn, báo cáo đồ án của các nhóm sinh viên học phần Hệ Thống Kinh Doanh Thương Mại (HTKDTM). Sinh viên thực hiện tham gia, phát triển và nộp bài thông qua hệ thống Git và GitHub theo đúng các quy chuẩn kỹ thuật được mô tả dưới đây.

---

## 1. Quy Chuẩn Đặt Tên Thư Mục Nhóm

Mỗi nhóm sinh viên bắt buộc phải tạo duy nhất một thư mục riêng biệt tại cấp cao nhất (root) của kho lưu trữ.

### 1.1. Cấu trúc định danh thư mục
- **Cú pháp quy định:** `<ten-nhom>-<ten-lop>`
- **Ví dụ chuẩn:**
  - Nhóm 01 lớp DHTI15A1HN: `nhom01-dhti15a1hn`
  - Nhóm 02 lớp DHTI15A2HN: `nhom02-dhti15a2hn`
  - Nhóm 05 lớp CNTT1: `nhom05-cntt1`

### 1.2. Ràng buộc kỹ thuật về tên thư mục
- Toàn bộ ký tự viết thường (lowercase).
- Không sử dụng ký tự tiếng Việt có dấu.
- Không sử dụng dấu khoảng trắng (space).
- Các thành phần được phân tách duy nhất bằng dấu gạch ngang (`-`).
- Không sử dụng các ký tự đặc biệt khác (`@`, `#`, `$`, `%`, `&`, `_`, `/`, `\`).

---

## 2. Quy Chuẩn Cấu Trúc Thư Mục Của Nhóm

Toàn bộ tài liệu, thông tin thành viên và mã nguồn của nhóm phải nằm trọn vẹn bên trong thư mục của nhóm mình. Cấu trúc tổ chức tệp tin yêu cầu như sau:

```text
project-htkdtm/
├── .gitignore
├── README.md
├── _template_nhom/
│   └── danhsachnhom.md
└── <tennhom-tenlop>/
    ├── danhsachnhom.md        # Tệp bắt buộc: Thông tin thành viên và phân công
    ├── README.md              # (Tùy chọn) Hướng dẫn cài đặt, chạy hệ thống của nhóm
    ├── docs/                  # Thư mục chứa tài liệu đặc tả, báo cáo đồ án (PDF/DOCX)
    │   └── baocao_doan.pdf
    └── src/                   # Thư mục chứa toàn bộ mã nguồn của dự án
        ├── backend/
        ├── frontend/
        └── database/
```

### Yêu cầu bắt buộc đối với tệp tin `danhsachnhom.md`:
- Tệp tin phải được đặt trực tiếp tại cấp cao nhất của thư mục nhóm: `<tennhom-tenlop>/danhsachnhom.md`.
- Sử dụng mẫu có sẵn tại thư mục `_template_nhom/danhsachnhom.md`.
- Nội dung tệp tin phải bao gồm đầy đủ:
  - Thông tin tên đề tài, lớp học phần.
  - Bảng danh sách thành viên: Số thứ tự, Họ và tên, Mã sinh viên, Lớp sinh hoạt, Vai trò (Nhóm trưởng / Thành viên), Nhiệm vụ phân công, Tỷ lệ đóng góp (%), Email.
  - Hướng dẫn thiết lập môi trường và các bước khởi chạy mã nguồn của nhóm.

---

## 3. Quy Định Về Quản Lý Mã Nguồn Và Tệp Tin

1. **Phạm vi thao tác:**
   - Mỗi nhóm chỉ được phép thêm mới, chỉnh sửa các tệp tin nằm trong thư mục của nhóm mình (`<tennhom-tenlop>/`).
   - Nghiêm cấm chỉnh sửa, đổi tên hoặc xóa các tệp tin, thư mục của các nhóm khác.
   - Không chỉnh sửa tệp tin gốc của kho lưu trữ (`README.md`, `.gitignore`, `_template_nhom/`), trừ trường hợp có thông báo từ giảng viên.

2. **Các tệp tin tuyệt đối không đưa lên kho lưu trữ (đã được cấu hình trong `.gitignore`):**
   - Thư mục thư viện, gói phụ thuộc: `node_modules/`, `venv/`, `env/`, `vendor/`, `packages/`.
   - Tệp tin cấu hình bảo mật cục bộ: `.env`, `.env.local`, file chứa mật khẩu, API key cá nhân.
   - Thư mục biên dịch và tệp nhị phân: `dist/`, `build/`, `bin/`, `obj/`, `target/`, `out/`, `*.exe`, `*.dll`.
   - Tệp bộ nhớ tạm của IDE/OS: `.vscode/`, `.idea/`, `__pycache__/`, `*.pyc`, `.DS_Store`, `Thumbs.db`.
   - Tệp nén dung lượng lớn: `*.zip`, `*.rar`, `*.tar.gz`, `*.7z` (nếu cần chia sẻ tài nguyên lớn, hãy sử dụng Google Drive/OneDrive và đính kèm liên kết trong tài liệu).

---

## 4. Hướng Dẫn Cấu Hình Và Tham Gia Dự Án Dành Cho Sinh Viên

Mọi sinh viên trước khi thực hiện thao tác mã nguồn cần hoàn tất các bước chuẩn bị sau:

### 4.1. Chuẩn bị tài khoản GitHub
- Mỗi sinh viên cần có một tài khoản GitHub cá nhân đang hoạt động.
- Gửi tài khoản GitHub (Username) cho giảng viên hoặc nhóm trưởng để được cấp quyền cộng tác (Collaborator) hoặc thực hiện theo luồng Fork.

### 4.2. Cấu hình định danh tác giả trên máy cục bộ
Để lịch sử commit ghi nhận chính xác danh tính sinh viên, mở Terminal / Git Bash và thiết lập:
```bash
git config --global user.name "Họ và Tên Sinh Viên"
git config --global user.email "email_sinh_vien@example.com"
```
*Lưu ý:* `email_sinh_vien@example.com` phải trùng khớp với email đã đăng ký trên tài khoản GitHub.

### 4.3. Lấy mã nguồn dự án về máy cục bộ
```bash
git clone https://github.com/oanhcuongdo/project-htkdtm.git
cd project-htkdtm
```

---

## 5. Quy Chuẩn Commit Và Push Mã Nguồn Vào Đúng Thư Mục Nhóm

Để đảm bảo không ảnh hưởng đến mã nguồn của nhóm khác và giữ cấu trúc kho lưu trữ chuẩn xác, sinh viên phải tuân thủ nghiêm ngặt quy trình dưới đây.

### 5.1. Quy tắc an toàn bắt buộc khi thao tác tệp
- **Chỉ làm việc bên trong thư mục nhóm:** Mọi tệp tin mới tạo hoặc sửa đổi bắt buộc phải nằm trong đường dẫn `<tennhom-tenlop>/`.
- **Không sử dụng lệnh `git add .` ở thư mục gốc:** Thao tác này dễ vô tình đưa cả các tệp ngoài ý muốn hoặc tệp của nhóm khác vào commit.
- **Luôn chỉ định cụ thể thư mục nhóm khi `git add`:**
  ```bash
  git add <tennhom-tenlop>/
  ```

### 5.2. Trình tự các bước thực hiện commit và push

#### Bước 1: Cập nhật mã nguồn mới nhất từ remote trước khi sửa
Tránh xung đột mã nguồn bằng cách kéo dữ liệu mới nhất về nhánh làm việc:
```bash
git checkout main
git pull origin main
```

#### Bước 2: Tạo hoặc chuyển sang nhánh làm việc của nhóm
Mỗi nhóm làm việc trên một nhánh riêng biệt:
```bash
git checkout -b feature/<tennhom-tenlop>
```
*Ví dụ:* `git checkout -b feature/nhom01-dhti15a1hn`

#### Bước 3: Tạo thư mục nhóm và sao chép biểu mẫu danh sách (nếu chưa có)
Nếu nhóm chưa có thư mục trên kho lưu trữ:
1. Tạo thư mục:
   ```bash
   mkdir nhom01-dhti15a1hn
   ```
2. Sao chép tệp `danhsachnhom.md` từ thư mục mẫu:
   - Trên Linux/macOS:
     ```bash
     cp _template_nhom/danhsachnhom.md nhom01-dhti15a1hn/danhsachnhom.md
     ```
   - Trên Windows PowerShell:
     ```powershell
     Copy-Item -Path _template_nhom\danhsachnhom.md -Destination nhom01-dhti15a1hn\danhsachnhom.md
     ```
3. Mở tệp `nhom01-dhti15a1hn/danhsachnhom.md`, điền đầy đủ và chính xác thông tin các thành viên.

#### Bước 4: Thêm mã nguồn và tài liệu vào thư mục nhóm
Sao chép toàn bộ thư mục `src/`, `docs/` vào đúng vị trí:
```text
nhom01-dhti15a1hn/
├── danhsachnhom.md
├── docs/
└── src/
```

#### Bước 5: Kiểm tra trạng thái tệp tin bằng `git status`
Trước khi đưa tệp vào staging, chạy lệnh kiểm tra:
```bash
git status
```
*Yêu cầu kiểm tra:* Danh sách tệp hiển thị ở mục `Untracked files` hoặc `Changes not staged for commit` bắt buộc chỉ bắt đầu bằng `<tennhom-tenlop>/`. Nếu xuất hiện tệp ở ngoài thư mục nhóm, phải di chuyển tệp về đúng vị trí trước khi tiếp tục.

#### Bước 6: Đưa tệp vào khu vực theo dõi (Staging Area)
Chỉ định rõ ràng thư mục nhóm:
```bash
git add nhom01-dhti15a1hn/
```

Kiểm tra lại lần nữa để đảm bảo chỉ có tệp của nhóm được stage:
```bash
git status
```

#### Bước 7: Thực hiện commit
Commit với thông điệp rõ ràng, tuân thủ cấu trúc chuẩn:
```bash
git commit -m "feat(nhom01-dhti15a1hn): nop ma nguon backend va danh sach nhom"
```
Cú pháp thông điệp commit: `<loại-thay-đổi>(<tennhom-tenlop>): <mô-tả-ngắn-gọn>`
- `feat`: Thêm chức năng mới, mã nguồn mới.
- `fix`: Sửa lỗi mã nguồn.
- `docs`: Cập nhật tài liệu, tệp danhsachnhom.md.

#### Bước 8: Đẩy nhánh lên GitHub (Push)
Đẩy nhánh lên remote repository:
```bash
git push -u origin feature/<tennhom-tenlop>
```
*Ví dụ:* `git push -u origin feature/nhom01-dhti15a1hn`

#### Bước 9: Mở Pull Request (PR) và kiểm tra lại vị trí tệp
1. Truy cập vào kho lưu trữ: `https://github.com/oanhcuongdo/project-htkdtm`.
2. Chọn **Compare & pull request** cho nhánh vừa đẩy.
3. Kiểm tra mục **Files changed** (Các tệp thay đổi): Đảm bảo 100% đường dẫn tệp đều có tiền tố `<tennhom-tenlop>/...`.
4. Đặt tiêu đề Pull Request:
   ```text
   [Nộp bài] <tennhom-tenlop> - <Tên đề tài>
   ```
5. Nhấn **Create pull request**.

---

## 6. Xử Lý Các Sự Cố Thường Gặp

### 6.1. Xử lý khi lỡ thêm (add) tệp nhầm ngoài thư mục nhóm
Nếu chạy `git status` và thấy có tệp nằm ngoài thư mục nhóm đã bị đưa vào Staging:
```bash
# Hủy staging tệp bị nhầm
git reset HEAD <duong-dan-tep-bi-nham>

# Di chuyển tệp về đúng thư mục nhóm
mv <duong-dan-tep> <tennhom-tenlop>/
```

### 6.2. Xử lý khi bị từ chối push (rejected - non-fast-forward)
Khi có thành viên khác trong nhóm hoặc nhóm khác đã đẩy commit lên nhánh trước bạn:
```bash
git pull --rebase origin feature/<tennhom-tenlop>
git push origin feature/<tennhom-tenlop>
```

### 6.3. Giữ nhánh cá nhân luôn cập nhật với nhánh `main` mới nhất
```bash
git checkout feature/<tennhom-tenlop>
git fetch origin
git merge origin/main
```

---

## 7. Danh Sách Kiểm Tra Trước Khi Nộp Bài (Checklist)

| STT | Tiêu chí kiểm tra | Yêu cầu kỹ thuật | Trạng thái |
| :-: | :--- | :--- | :-: |
| 1 | Cú pháp tên thư mục | Đúng định dạng `<tennhom-tenlop>`, toàn bộ chữ thường, không dấu, không khoảng trắng. | Bắt buộc |
| 2 | Vị trí tệp tin | 100% tệp tin của nhóm nằm trọn vẹn trong thư mục `<tennhom-tenlop>/`. | Bắt buộc |
| 3 | Tệp `danhsachnhom.md` | Có mặt tại thư mục gốc của nhóm, điền đầy đủ thông tin thành viên và phân công. | Bắt buộc |
| 4 | Kiểm soát tệp tin rác | Không commit `node_modules/`, `venv/`, `.env`, tệp tạm IDE, tệp nhị phân nén lớn. | Bắt buộc |
| 5 | Lệnh `git add` | Luôn sử dụng `git add <tennhom-tenlop>/`, không `git add .` tại thư mục gốc. | Bắt buộc |
| 6 | Tính toàn vẹn nhánh chung | Không sửa đổi, không xóa thư mục hoặc mã nguồn của các nhóm khác. | Bắt buộc |
