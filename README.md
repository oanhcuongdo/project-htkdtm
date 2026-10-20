# Hướng Dẫn Nộp Mã Nguồn Và Báo Cáo Đồ Án (Hệ Thống Kinh Doanh Thương Mại)

Kho lưu trữ này được thiết lập để quản lý và thu thập mã nguồn, báo cáo đồ án của các nhóm sinh viên học phần Hệ Thống Kinh Doanh Thương Mại (HTKDTM). Sinh viên thực hiện nộp bài thông qua hệ thống Git và GitHub theo đúng các quy chuẩn kỹ thuật được mô tả dưới đây.

---

## 1. Quy Chuẩn Đặt Tên Thư Mục Nhóm

Mỗi nhóm sinh viên bắt buộc phải tạo một thư mục riêng biệt tại thư mục gốc của kho lưu trữ này.

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

## 4. Quy Trình Nộp Bài Bằng Git Và GitHub

Quy trình nộp bài được thực hiện theo mô hình **Fork & Pull Request** chuẩn của GitHub nhằm đảm bảo tính toàn vẹn và minh bạch mã nguồn.

### Cách 1: Quy trình Fork và Pull Request (Khuyến nghị chuẩn)

#### Bước 1: Fork kho lưu trữ
- Truy cập vào trang chủ kho lưu trữ: `https://github.com/oanhcuongdo/project-htkdtm`.
- Nhấn nút **Fork** (nằm ở góc trên bên phải giao diện GitHub) để tạo bản sao kho lưu trữ về tài khoản GitHub của nhóm trưởng hoặc thành viên đại diện.

#### Bước 2: Clone kho lưu trữ đã fork về máy tính cục bộ
Mở Terminal / Command Prompt / Git Bash và thực hiện lệnh:
```bash
git clone https://github.com/<tai-khoan-github-cua-ban>/project-htkdtm.git
cd project-htkdtm
```

#### Bước 3: Tạo nhánh (Branch) làm việc mới
Tạo và chuyển sang nhánh riêng biệt mang tên nhóm:
```bash
git checkout -b feature/<tennhom-tenlop>
```
*Ví dụ:* `git checkout -b feature/nhom01-dhti15a1hn`

#### Bước 4: Tạo thư mục nhóm và thêm mã nguồn
1. Tạo thư mục nhóm theo đúng cú pháp: `mkdir nhom01-dhti15a1hn`
2. Sao chép tệp mẫu danh sách nhóm:
   - Trên Linux/macOS: `cp _template_nhom/danhsachnhom.md nhom01-dhti15a1hn/danhsachnhom.md`
   - Trên Windows PowerShell: `Copy-Item -Path _template_nhom\danhsachnhom.md -Destination nhom01-dhti15a1hn\danhsachnhom.md`
3. Mở tệp `nhom01-dhti15a1hn/danhsachnhom.md`, cập nhật chính xác toàn bộ thông tin thành viên và đề tài của nhóm.
4. Đặt mã nguồn, tài liệu vào đúng thư mục nhóm.

#### Bước 5: Kiểm tra trạng thái và commit
Kiểm tra các tệp tin đã thêm mới, đảm bảo không có tệp thừa:
```bash
git status
```
Thêm toàn bộ thư mục của nhóm vào khu vực theo dõi (Staging Area):
```bash
git add nhom01-dhti15a1hn/
```
Tạo commit với thông điệp rõ ràng theo chuẩn:
```bash
git commit -m "feat(nhom01-dhti15a1hn): nop ma nguon va danh sach thanh vien"
```

#### Bước 6: Đẩy nhánh lên GitHub cá nhân
```bash
git push -u origin feature/<tennhom-tenlop>
```

#### Bước 7: Mở Pull Request (PR) về kho lưu trữ gốc
1. Truy cập vào kho lưu trữ đã fork trên giao diện web GitHub.
2. Nhấn nút **Compare & pull request**.
3. Thiết lập thông số:
   - **Base repository:** `oanhcuongdo/project-htkdtm` - **Base branch:** `main`
   - **Head repository:** `<tai-khoan-cua-ban>/project-htkdtm` - **Compare branch:** `feature/<tennhom-tenlop>`
4. Đặt tiêu đề Pull Request theo cú pháp:
   ```text
   [Nộp bài] <tennhom-tenlop> - <Tên đề tài>
   ```
   *Ví dụ:* `[Nộp bài] nhom01-dhti15a1hn - He Thong Quan Ly Ban Hang Truc Tuyen`
5. Trong phần mô tả Pull Request, ghi rõ danh sách thành viên và các nội dung đã hoàn thành.
6. Nhấn **Create pull request** để hoàn tất nộp bài.

---

### Cách 2: Quy trình đẩy trực tiếp (Áp dụng khi sinh viên được cấp quyền Collaborator)

Trường hợp sinh viên được mời làm cộng tác viên trực tiếp (Collaborator) trên kho lưu trữ:

1. Clone trực tiếp kho lưu trữ gốc:
   ```bash
   git clone https://github.com/oanhcuongdo/project-htkdtm.git
   cd project-htkdtm
   ```
2. Tạo nhánh làm việc của nhóm:
   ```bash
   git checkout -b feature/<tennhom-tenlop>
   ```
3. Tạo thư mục nhóm, thêm mã nguồn và cập nhật `danhsachnhom.md`.
4. Commit và đẩy nhánh lên kho lưu trữ:
   ```bash
   git add nhom01-dhti15a1hn/
   git commit -m "feat(nhom01-dhti15a1hn): nop ma nguon do an"
   git push -u origin feature/<tennhom-tenlop>
   ```
5. Mở Pull Request từ nhánh `feature/<tennhom-tenlop>` vào nhánh `main` để giảng viên phê duyệt và hợp nhất (merge).

---

## 5. Danh Sách Kiểm Tra Trước Khi Nộp Bài (Checklist)

Trước khi gửi Pull Request hoặc hoàn tất nộp bài, đại diện nhóm phải kiểm tra lại các mục sau:

| STT | Hạng mục kiểm tra | Tiêu chuẩn đạt yêu cầu | Trạng thái |
| :-: | :--- | :--- | :-: |
| 1 | Tên thư mục nhóm | Đúng định dạng `<tennhom-tenlop>`, toàn bộ chữ thường, không dấu, không cách. | Bắt buộc |
| 2 | Tệp `danhsachnhom.md` | Nằm trực tiếp trong thư mục nhóm, điền đầy đủ họ tên, MSSV, vai trò, đóng góp. | Bắt buộc |
| 3 | Tệp `.gitignore` | Không commit thư mục rác (`node_modules/`, `venv/`, file `.env`, tệp build). | Bắt buộc |
| 4 | Mã nguồn dự án | Nằm gọn trong thư mục nhóm, có đầy đủ các tệp cần thiết để chạy chương trình. | Bắt buộc |
| 5 | Tệp hướng dẫn chạy | Đã hướng dẫn chi tiết cách cài đặt và chạy mã nguồn trong `danhsachnhom.md`. | Bắt buộc |
| 6 | Độc lập tệp tin | Không chỉnh sửa hoặc can thiệp vào thư mục của các nhóm khác. | Bắt buộc |
