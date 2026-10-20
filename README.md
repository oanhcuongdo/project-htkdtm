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

## 2. Quy Chuẩn Tạo Và Quản Lý Nhánh Riêng Biệt Cho Từng Nhóm (Branching Strategy)

Để đảm bảo tính độc lập và tránh xung đột mã nguồn giữa các nhóm, quy định về phân nhánh (branching) được áp dụng bắt buộc như sau:

### 2.1. Quy tắc phân nhánh cốt lõi
- **Tuyệt đối cấm commit hoặc push trực tiếp vào nhánh `main`:** Nhánh `main` là nhánh tích hợp cuối cùng của học phần, chỉ được cập nhật thông qua Pull Request sau khi giảng viên kiểm duyệt và nghiệm thu.
- **Mỗi nhóm bắt buộc phải có một nhánh làm việc riêng:** Toàn bộ quá trình phát triển mã nguồn, tải tài liệu và cập nhật tiến độ của nhóm phải được thực hiện trên nhánh riêng của nhóm đó.

### 2.2. Cú pháp định danh nhánh nhóm
- **Cú pháp chuẩn:** `<ten-nhom>-<ten-lop>` (trùng khớp với tên thư mục của nhóm để đồng bộ quản lý).
- **Ví dụ chuẩn:**
  - Nhóm 01 lớp DHTI15A1HN: `nhom01-dhti15a1hn`
  - Nhóm 02 lớp DHTI15A2HN: `nhom02-dhti15a2hn`
  - Nhóm 05 lớp CNTT1: `nhom05-cntt1`

### 2.3. Lệnh tạo và xuất bản nhánh nhóm lên GitHub
Nhóm trưởng (hoặc đại diện nhóm) tạo nhánh từ nhánh `main` mới nhất và đẩy nhánh lên GitHub:
```bash
# 1. Chuyển về nhánh main và lấy mã nguồn mới nhất
git checkout main
git pull origin main

# 2. Tạo và chuyển sang nhánh riêng của nhóm
git checkout -b <ten-nhom>-<ten-lop>

# 3. Đẩy nhánh riêng của nhóm lên kho lưu trữ GitHub
git push -u origin <ten-nhom>-<ten-lop>
```
*Ví dụ cụ thể:*
```bash
git checkout main
git pull origin main
git checkout -b nhom01-dhti15a1hn
git push -u origin nhom01-dhti15a1hn
```

### 2.4. Quy trình đồng bộ giữa các thành viên trong cùng một nhóm
Các thành viên trong cùng một nhóm cộng tác trên nhánh của nhóm mình theo các bước:
1. Lấy danh sách nhánh mới nhất từ GitHub:
   ```bash
   git fetch origin
   ```
2. Chuyển sang làm việc trên nhánh của nhóm:
   ```bash
   git checkout --track origin/<ten-nhom>-<ten-lop>
   ```
   *(Trường hợp đã có nhánh cục bộ, chỉ cần chạy: `git checkout <ten-nhom>-<ten-lop>`)*
3. Trước khi bắt đầu viết mã hoặc thêm tệp, luôn kéo dữ liệu mới nhất của nhóm về:
   ```bash
   git pull origin <ten-nhom>-<ten-lop>
   ```
4. Đẩy kết quả công việc sau khi commit lên nhánh nhóm:
   ```bash
   git push origin <ten-nhom>-<ten-lop>
   ```

---

## 3. Quy Chuẩn Cấu Trúc Thư Mục Của Nhóm

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

## 4. Quy Định Về Quản Lý Mã Nguồn Và Tệp Tin

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

## 5. Hướng Dẫn Cấu Hình Và Tham Gia Dự Án Dành Cho Sinh Viên

Mọi sinh viên trước khi thực hiện thao tác mã nguồn cần hoàn tất các bước chuẩn bị sau:

### 5.1. Chuẩn bị tài khoản GitHub
- Mỗi sinh viên cần có một tài khoản GitHub cá nhân đang hoạt động.
- Gửi tài khoản GitHub (Username) cho giảng viên hoặc nhóm trưởng để được cấp quyền cộng tác (Collaborator) hoặc thực hiện theo luồng Fork.

### 5.2. Cấu hình định danh tác giả trên máy cục bộ
Để lịch sử commit ghi nhận chính xác danh tính sinh viên, mở Terminal / Git Bash và thiết lập:
```bash
git config --global user.name "Họ và Tên Sinh Viên"
git config --global user.email "email_sinh_vien@example.com"
```
*Lưu ý:* `email_sinh_vien@example.com` phải trùng khớp với email đã đăng ký trên tài khoản GitHub.

### 5.3. Lấy mã nguồn dự án về máy cục bộ
```bash
git clone https://github.com/oanhcuongdo/project-htkdtm.git
cd project-htkdtm
```

---

## 6. Quy Chuẩn Commit Và Push Mã Nguồn Vào Đúng Thư Mục Nhóm

Để đảm bảo không ảnh hưởng đến mã nguồn của nhóm khác và giữ cấu trúc kho lưu trữ chuẩn xác, sinh viên phải tuân thủ nghiêm ngặt quy trình dưới đây.

### 6.1. Quy tắc an toàn bắt buộc khi thao tác tệp
- **Chỉ làm việc bên trong thư mục nhóm:** Mọi tệp tin mới tạo hoặc sửa đổi bắt buộc phải nằm trong đường dẫn `<tennhom-tenlop>/`.
- **Không sử dụng lệnh `git add .` ở thư mục gốc:** Thao tác này dễ vô tình đưa cả các tệp ngoài ý muốn hoặc tệp của nhóm khác vào commit.
- **Luôn chỉ định cụ thể thư mục nhóm khi `git add`:**
  ```bash
  git add <tennhom-tenlop>/
  ```

### 6.2. Trình tự các bước thực hiện commit và push

#### Bước 1: Chuyển sang nhánh riêng của nhóm và đồng bộ mới nhất
```bash
git checkout <ten-nhom>-<ten-lop>
git pull origin <ten-nhom>-<ten-lop>
```

#### Bước 2: Tạo thư mục nhóm và sao chép biểu mẫu danh sách (nếu chưa có)
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

#### Bước 3: Thêm mã nguồn và tài liệu vào thư mục nhóm
Sao chép toàn bộ thư mục `src/`, `docs/` vào đúng vị trí:
```text
nhom01-dhti15a1hn/
├── danhsachnhom.md
├── docs/
└── src/
```

#### Bước 4: Kiểm tra trạng thái tệp tin bằng `git status`
Trước khi đưa tệp vào staging, chạy lệnh kiểm tra:
```bash
git status
```
*Yêu cầu kiểm tra:* Danh sách tệp hiển thị ở mục `Untracked files` hoặc `Changes not staged for commit` bắt buộc chỉ bắt đầu bằng `<tennhom-tenlop>/`. Nếu xuất hiện tệp ở ngoài thư mục nhóm, phải di chuyển tệp về đúng vị trí trước khi tiếp tục.

#### Bước 5: Đưa tệp vào khu vực theo dõi (Staging Area)
Chỉ định rõ ràng thư mục nhóm:
```bash
git add nhom01-dhti15a1hn/
```

Kiểm tra lại lần nữa để đảm bảo chỉ có tệp của nhóm được stage:
```bash
git status
```

#### Bước 6: Thực hiện commit
Commit với thông điệp rõ ràng, tuân thủ cấu trúc chuẩn:
```bash
git commit -m "feat(nhom01-dhti15a1hn): nop ma nguon backend va danh sach nhom"
```
Cú pháp thông điệp commit: `<loại-thay-đổi>(<tennhom-tenlop>): <mô-tả-ngắn-gọn>`
- `feat`: Thêm chức năng mới, mã nguồn mới.
- `fix`: Sửa lỗi mã nguồn.
- `docs`: Cập nhật tài liệu, tệp danhsachnhom.md.

#### Bước 7: Đẩy nhánh lên GitHub (Push)
Đẩy nhánh lên remote repository:
```bash
git push origin <ten-nhom>-<ten-lop>
```
*Ví dụ:* `git push origin nhom01-dhti15a1hn`

#### Bước 8: Mở Pull Request (PR) về nhánh `main` khi nộp bài
1. Truy cập vào kho lưu trữ: `https://github.com/oanhcuongdo/project-htkdtm`.
2. Chọn **Compare & pull request** cho nhánh nhóm `<ten-nhom>-<ten-lop>`.
3. Kiểm tra mục **Files changed** (Các tệp thay đổi): Đảm bảo 100% đường dẫn tệp đều có tiền tố `<tennhom-tenlop>/...`.
4. Đặt tiêu đề Pull Request:
   ```text
   [Nộp bài] <tennhom-tenlop> - <Tên đề tài>
   ```
5. Nhấn **Create pull request** để giảng viên đánh giá và phê duyệt.

---

## 7. Xử Lý Các Sự Cố Kỹ Thuật Thường Gặp

### 7.1. Xử lý khi lỡ thêm (add) tệp nhầm ngoài thư mục nhóm
Nếu chạy `git status` và thấy có tệp nằm ngoài thư mục nhóm đã bị đưa vào Staging:
```bash
# Hủy staging tệp bị nhầm
git reset HEAD <duong-dan-tep-bi-nham>

# Di chuyển tệp về đúng thư mục nhóm
mv <duong-dan-tep> <tennhom-tenlop>/
```

### 7.2. Xử lý khi bị từ chối push (rejected - non-fast-forward)
Khi có thành viên khác trong nhóm đã đẩy commit lên nhánh trước bạn:
```bash
git pull --rebase origin <ten-nhom>-<ten-lop>
git push origin <ten-nhom>-<ten-lop>
```

### 7.3. Giữ nhánh nhóm luôn cập nhật với nhánh `main` mới nhất
```bash
git checkout <ten-nhom>-<ten-lop>
git fetch origin
git merge origin/main
```

---

## 8. Danh Sách Kiểm Tra Trước Khi Nộp Bài (Checklist)

| STT | Tiêu chí kiểm tra | Yêu cầu kỹ thuật | Trạng thái |
| :-: | :--- | :--- | :-: |
| 1 | Nhánh làm việc riêng | Làm việc 100% trên nhánh riêng `<ten-nhom>-<ten-lop>`, không commit trực tiếp vào `main`. | Bắt buộc |
| 2 | Cú pháp tên thư mục | Đúng định dạng `<tennhom-tenlop>`, toàn bộ chữ thường, không dấu, không khoảng trắng. | Bắt buộc |
| 3 | Vị trí tệp tin | 100% tệp tin của nhóm nằm trọn vẹn trong thư mục `<tennhom-tenlop>/`. | Bắt buộc |
| 4 | Tệp `danhsachnhom.md` | Có mặt tại thư mục gốc của nhóm, điền đầy đủ thông tin thành viên và phân công. | Bắt buộc |
| 5 | Kiểm soát tệp tin rác | Không commit `node_modules/`, `venv/`, `.env`, tệp tạm IDE, tệp nhị phân nén lớn. | Bắt buộc |
| 6 | Lệnh `git add` | Luôn sử dụng `git add <tennhom-tenlop>/`, không `git add .` tại thư mục gốc. | Bắt buộc |
| 7 | Tính toàn vẹn nhánh chung | Không sửa đổi, không xóa thư mục hoặc mã nguồn của các nhóm khác. | Bắt buộc |
