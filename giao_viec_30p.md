# Giao việc 30 phút cho từng thành viên (Nhóm 03, EduVision BI)

Mỗi người làm **một việc nhỏ** trong thư mục riêng, dùng agent (Claude Code hoặc tương đương) để làm nhanh, rồi commit và push **nhánh riêng**, mở Pull Request vào `nhom03-65httt` của Fork.
Nhánh `nhom03-65httt` được bảo vệ: **không push thẳng**, chỉ merge bằng Pull Request.

---

## PHẦN A. QUY TRÌNH GIT CHUNG (ai cũng làm theo)

### A1. Chuẩn bị một lần (nếu chưa có)
1. Nhận lời mời Collaborator của kho Fork `thanhtung111205/project-htkdtm` (email GitHub hoặc mục Notifications), bấm Accept.
2. Cấu hình tác giả, **email phải trùng email tài khoản GitHub**:
```bash
git config --global user.name "Họ và Tên"
git config --global user.email "email_cua_ban@example.com"
```
3. Clone kho Fork:
```bash
git clone https://github.com/thanhtung111205/project-htkdtm.git
cd project-htkdtm
```

### A2. Mỗi lần bắt đầu làm (phút 0–3)
```bash
git fetch origin
git checkout nhom03-65httt
git pull origin nhom03-65httt
git checkout -b <TEN-NHANH-CUA-BAN>        # tên ở phần B, ví dụ nhom03-65httt-thaianh-collector
git branch --show-current                    # phải ra đúng tên nhánh của bạn, KHÔNG phải main hay nhom03-65httt
```

### A3. Khi xong việc: commit (phút 23–27)
```bash
git status
# Mọi đường dẫn phải bắt đầu bằng nhom03-65httt/ . Có tệp lạ (csv, xlsx, .env, node_modules...) thì KHÔNG add.

git add nhom03-65httt/<DUONG-DAN-CU-THE-1> nhom03-65httt/<DUONG-DAN-CU-THE-2>
git status                                   # kiểm tra lại: chỉ thấy đúng tệp của bạn ở trạng thái staged

git commit -m "<THONG-DIEP-COMMIT-CUA-BAN>"  # đúng một dòng, KHÔNG co-author
git log -1 --format=%B                       # phải KHÔNG có dòng Co-Authored-By hay Generated with
```
Quy tắc:
- **Không** dùng `git add .`, `git add -A`, `git commit -a`.
- Thông điệp theo mẫu của thầy: `<loại>(nhom03-65httt): <mô tả không dấu>`; loại là `feat` (mã nguồn), `fix` (sửa lỗi), `docs` (tài liệu).
- **Không có `Co-Authored-By`.** Nếu công cụ tự thêm dòng này, sửa ngay trước khi push (chưa push thì an toàn):
```bash
git commit --amend -m "<THONG-DIEP-COMMIT-CUA-BAN>"
git log -1 --format=%B
```

### A4. Push nhánh riêng và mở Pull Request (phút 27–30)
```bash
git push -u origin <TEN-NHANH-CUA-BAN>
```
Sau đó vào `https://github.com/thanhtung111205/project-htkdtm`, bấm **Compare & pull request** và **kiểm tra đúng đích**:
- **base repository:** `thanhtung111205/project-htkdtm` (Fork của nhóm trưởng, KHÔNG phải `oanhcuongdo/project-htkdtm`)
- **base:** `nhom03-65httt`
- **compare:** nhánh của bạn
- Tiêu đề PR: giống thông điệp commit. Mô tả PR một hai dòng, không có dòng ghi công công cụ.
- Mục **Files changed**: 100% đường dẫn bắt đầu bằng `nhom03-65httt/`.
Không tự bấm Merge nếu chưa được nhóm trưởng đồng ý.

### A5. Lỗi thường gặp
| Lỗi | Nguyên nhân | Cách xử lý |
|---|---|---|
| `push rejected` / `protected branch` khi push `nhom03-65httt` | Nhánh nhóm cấm push thẳng | Đúng quy định. Push nhánh riêng của bạn rồi mở PR |
| `Permission denied` / 403 | Chưa là Collaborator | Nhận lời mời Collaborator (A1) |
| `non-fast-forward` trên nhánh riêng | Ai đó đã đẩy vào nhánh đó | `git pull --rebase origin <TEN-NHANH>` rồi push lại |
| Thấy tệp `.csv`, `.xlsx`, `.env`, `node_modules` trong `git status` | Dữ liệu và khóa không được commit | Không add chúng; kiểm tra `.gitignore` của nhóm |
| PR mở nhầm vào kho của thầy | Chọn sai base repository | Đóng PR, mở lại với base repository là Fork của nhóm trưởng |

---

## PHẦN B. PROMPT RIÊNG TỪNG NGƯỜI

> Cách dùng: mở agent ở thư mục `project-htkdtm`, **dán nguyên khối prompt** của mình.
> Khối nào cũng có phần "Quy tắc bắt buộc" để agent không thêm co-author và không sửa tệp ngoài việc của bạn.

### B0. Phần "Quy tắc bắt buộc" (đã nhúng sẵn trong mọi prompt bên dưới)
```text
Quy tắc bắt buộc:
- Chỉ tạo hoặc sửa các tệp đã nêu trong "Tệp cần tạo". Không sửa tệp nào khác, không đụng tới README.md gốc, .gitignore gốc, _template_nhom/.
- Không đưa dữ liệu thật, khóa API, token, .env, CSV/Excel vào tệp hay vào commit.
- Mọi đường dẫn nằm trong thư mục nhom03-65httt/.
- Không thêm Co-Authored-By, Signed-off-by hay bất kỳ dòng ghi công công cụ nào vào commit.
- Chưa push. Cuối cùng chỉ đưa tôi các lệnh git add (đường dẫn cụ thể), git commit (một dòng, đúng mẫu), và lệnh kiểm tra git log -1 --format=%B.
```

---

### B1. NGUYỄN THÁI ANH: Collector Google Play (nhánh `nhom03-65httt-thaianh-collector`)

**Tệp cần tạo:** `nhom03-65httt/src/etl/collectors/google_play_collector.py`, `nhom03-65httt/src/etl/collectors/requirements.txt`, `nhom03-65httt/src/etl/collectors/README.md`

**Thông điệp commit:** `feat(nhom03-65httt): collector google play doc platforms yml`

**Chuẩn bị:** nhóm trưởng gửi script thu thập mẫu qua kênh riêng (không bắt buộc). Cài trước: `pip install google-play-scraper pyyaml`.

```text
Bối cảnh: đồ án EduVision BI (phân tích đánh giá các nền tảng E-learning), kho project-htkdtm, thư mục nhom03-65httt. Đề tài chỉ phục vụ học tập, chỉ thu dữ liệu công khai.

Việc (30 phút): viết collector đánh giá Google Play cho MỘT nền tảng mỗi lần chạy.

Yêu cầu:
1. Đọc danh sách nền tảng từ nhom03-65httt/config/platforms.yml (khóa "platforms", mỗi khối có id, play_id, platform_group). Tham số dòng lệnh: --only "<id nền tảng>", --count <số đánh giá, mặc định 200>, --out <thư mục, mặc định nhom03-65httt/data/raw>, --sleep <giây, mặc định 2>. Từ chối chạy nếu --sleep < 2.
2. Dùng thư viện google-play-scraper, lang="vi", country="vn", sắp xếp mới nhất, lấy từng trang bằng continuation token cho tới khi đủ --count.
3. Gặp lỗi 429 hoặc 5xx: thử lại với độ trễ tăng dần (exponential backoff), tối đa 5 lần rồi dừng và báo lỗi, KHÔNG vượt cơ chế chặn, KHÔNG đổi IP/proxy.
4. Ghi CSV (UTF-8, có BOM) đúng các cột theo thứ tự: source, product, review_id, author_hash, rating, text, lang_guess, created_at, app_version, thumbs_up, reply_text, crawled_at.
   - source = "google_play"; product = id nền tảng trong platforms.yml.
   - author_hash = 12 ký tự đầu của SHA-256 tên hiển thị. TUYỆT ĐỐI không lưu tên người dùng, ảnh đại diện hay đường dẫn trang cá nhân.
   - lang_guess = "vi" nếu có từ 2 ký tự tiếng Việt có dấu trở lên, ngược lại "other".
   - created_at theo ISO 8601; crawled_at là thời điểm chạy.
5. Chạy lại không sinh dòng trùng: nếu file đã có, đọc review_id cũ và chỉ ghi phần mới.
6. Tệp requirements.txt gồm đúng: google-play-scraper, pyyaml. README.md (tiếng Việt) ghi: mục đích, cách cài, ví dụ lệnh chạy, các cột CSV, lưu ý không commit dữ liệu.

Tệp cần tạo: nhom03-65httt/src/etl/collectors/google_play_collector.py, nhom03-65httt/src/etl/collectors/requirements.txt, nhom03-65httt/src/etl/collectors/README.md

Tiêu chí xong: chạy `python nhom03-65httt/src/etl/collectors/google_play_collector.py --only "ELSA Speak" --count 20` tạo được file CSV 20 dòng trong nhom03-65httt/data/raw/; chạy lần hai không thêm dòng trùng; `git status` KHÔNG thấy file CSV (đã bị .gitignore chặn).

[dán nguyên khối "Quy tắc bắt buộc" ở B0]
```

**Lệnh git** (sau khi A2 với tên nhánh `nhom03-65httt-thaianh-collector`):
```bash
git add nhom03-65httt/src/etl/collectors/google_play_collector.py nhom03-65httt/src/etl/collectors/requirements.txt nhom03-65httt/src/etl/collectors/README.md
git status
git commit -m "feat(nhom03-65httt): collector google play doc platforms yml"
git log -1 --format=%B
git push -u origin nhom03-65httt-thaianh-collector
```

---

### B2. TẠ THỊ NGỌC ANH: Schema lõi PostgreSQL (nhánh `nhom03-65httt-ngocanh-schema`)

**Tệp cần tạo:** `nhom03-65httt/src/database/schema/01_schema_core.sql`

**Thông điệp commit:** `feat(nhom03-65httt): schema loi raw clean dw va fact_review`

**Chuẩn bị:** có PostgreSQL cục bộ (hoặc chạy bằng Docker). Không cần dữ liệu thật.

```text
Bối cảnh: đồ án EduVision BI, kho dữ liệu galaxy schema trong PostgreSQL, schema dw. Mô hình: nhiều bảng fact dùng chung dimension; bảng fact chỉ chứa khóa ngoại và số đo; văn bản đánh giá lưu ở bảng clean.review_text, không lưu trong fact.

Việc (30 phút): viết MỘT tệp SQL tạo phần lõi của kho dữ liệu.

Yêu cầu:
1. Tạo 3 schema: raw (dữ liệu thô nguyên trạng), clean (đã làm sạch), dw (kho dữ liệu). Dùng CREATE SCHEMA IF NOT EXISTS.
2. raw.review_raw: các cột theo CSV thu thập: source, product, review_id, author_hash, rating, text, lang_guess, created_at, app_version, thumbs_up, reply_text, crawled_at (kiểu phù hợp, cho phép text rỗng).
3. clean.review_text: review_key (khóa), review_id, source, text, lang_guess, text_hash (để loại trùng nội dung). UNIQUE theo (source, review_id).
4. dw.dim_time (time_key kiểu int dạng yyyymmdd, date, week, month, quarter, year).
5. dw.dim_platform (platform_key, platform_name, platform_group nhận 'trong_nuoc' hoặc 'quoc_te', play_id, ios_id).
6. dw.dim_source (source_key, source_name, source_type nhận 'kho_ung_dung', 'youtube', 'bao_chi', 'khac').
7. dw.fact_review: review_key (khóa chính), time_key, platform_key, source_key (khóa ngoại), rating, thumbs_up. Grain: một đánh giá. Chỉ khóa ngoại và số đo.
8. Có chú thích COMMENT ON TABLE cho từng bảng bằng tiếng Việt. Tệp chạy lại nhiều lần không lỗi (IF NOT EXISTS).
9. Không tạo bảng nào khác (các fact và dim còn lại làm ở commit sau).

Tệp cần tạo: nhom03-65httt/src/database/schema/01_schema_core.sql

Tiêu chí xong: chạy `psql -f nhom03-65httt/src/database/schema/01_schema_core.sql` hai lần liên tiếp đều không lỗi; `\dt dw.*` thấy 4 bảng (dim_time, dim_platform, dim_source, fact_review).

[dán nguyên khối "Quy tắc bắt buộc" ở B0]
```

**Lệnh git** (nhánh `nhom03-65httt-ngocanh-schema`):
```bash
git add nhom03-65httt/src/database/schema/01_schema_core.sql
git status
git commit -m "feat(nhom03-65httt): schema loi raw clean dw va fact_review"
git log -1 --format=%B
git push -u origin nhom03-65httt-ngocanh-schema
```

---

### B3. NGUYỄN HOÀNG ANH: README frontend và backend (nhánh `nhom03-65httt-hoanganh-readme`)

**Tệp cần tạo:** `nhom03-65httt/src/frontend/README.md`, `nhom03-65httt/src/backend/README.md`

**Thông điệp commit:** `docs(nhom03-65httt): readme thiet ke frontend va backend`

```text
Bối cảnh: đồ án EduVision BI, thư mục nhom03-65httt. Đọc nhom03-65httt/docs/De_Cuong_Nhom03.docx, chủ yếu mục 5 (kiến trúc) và mục 11 (website, phân quyền, tự động hóa) để lấy thông tin.

Việc (30 phút): viết hai README tiếng Việt mô tả THIẾT KẾ DỰ KIẾN. Mã nguồn chưa được viết, nên đầu mỗi README ghi đúng dòng: "Trạng thái: mã nguồn chưa được viết, nội dung dưới đây là thiết kế dự kiến theo đề cương."

src/frontend/README.md gồm:
- Công nghệ: React + TypeScript. Cấu trúc thư mục hiện có: src/auth, src/components, src/pages, src/services (mô tả mỗi thư mục để làm gì).
- Các trang dự kiến: đăng nhập và đăng ký; dashboard (Superset nhúng bằng iframe, quyền xem theo vai trò); Review Explorer (tìm kiếm, lọc, xem nhãn AI); cảnh báo và khuyến nghị; quản lý nguồn dữ liệu và bảng sự kiện (Admin); chatbot hỏi đáp trên số liệu.
- Hai vai trò: Admin (thấy thêm quản lý nguồn, lịch ETL, người dùng) và Viewer (chỉ xem).
- Nút "Cập nhật dữ liệu" của Admin: kích hoạt thu thập phần mới qua webhook n8n hoặc FastAPI, chạy nền, hiển thị trạng thái.
- Mục "Cách chạy": ghi "Cập nhật khi có mã nguồn", không viết lệnh chưa chạy thử.

src/backend/README.md gồm:
- Công nghệ: FastAPI. Cấu trúc hiện có: app/api, app/core, app/llm, app/ml, app/models, app/schemas, app/services, tests (mô tả mỗi thư mục).
- Các nhóm API dự kiến (ghi rõ "dự kiến, có thể đổi tên"): dự đoán cảm xúc, dự đoán khía cạnh, dự báo, chatbot, kích hoạt cập nhật dữ liệu, cảnh báo và khuyến nghị. Nêu website và n8n gọi API này.
- Mục "Cách chạy": ghi "Cập nhật khi có mã nguồn", không viết lệnh chưa chạy thử.

Không viết thông tin không có trong đề cương. Không đưa khóa API, .env, dữ liệu thật.

Tệp cần tạo: nhom03-65httt/src/frontend/README.md, nhom03-65httt/src/backend/README.md

Tiêu chí xong: hai README đọc được, có dòng "Trạng thái" ở đầu, mọi trang và API khớp với đề cương, không có lệnh chưa chạy thử.

[dán nguyên khối "Quy tắc bắt buộc" ở B0]
```

**Lệnh git** (nhánh `nhom03-65httt-hoanganh-readme`):
```bash
git add nhom03-65httt/src/frontend/README.md nhom03-65httt/src/backend/README.md
git status
git commit -m "docs(nhom03-65httt): readme thiet ke frontend va backend"
git log -1 --format=%B
git push -u origin nhom03-65httt-hoanganh-readme
```

---

### B4. HOÀNG HỮU HƯNG: README dashboard Superset và kho dữ liệu (nhánh `nhom03-65httt-hung-readme`)

**Tệp cần tạo:** `nhom03-65httt/src/bi/superset/README.md`, `nhom03-65httt/src/database/README.md`

**Thông điệp commit:** `docs(nhom03-65httt): readme thiet ke dashboard superset va kho du lieu`

```text
Bối cảnh: đồ án EduVision BI, thư mục nhom03-65httt. Đọc nhom03-65httt/docs/De_Cuong_Nhom03.docx, chủ yếu mục 7 (thiết kế kho dữ liệu) và mục 9 (hệ thống BI: KPI và dashboard) để lấy thông tin.

Việc (30 phút): viết hai README tiếng Việt mô tả THIẾT KẾ DỰ KIẾN. Mã chưa được viết, nên đầu mỗi README ghi đúng dòng: "Trạng thái: mã nguồn chưa được viết, nội dung dưới đây là thiết kế dự kiến theo đề cương."

src/bi/superset/README.md gồm:
- Mục đích: Apache Superset trực quan hóa và so sánh các nền tảng, nhúng vào website.
- Danh sách 6 dashboard (tên, câu hỏi mà dashboard trả lời, KPI chính). Chỉ lấy đúng từ mục 9 đề cương.
- Bảng KPI: tên, ý nghĩa, đơn vị, kỳ tính (chỉ ghi những gì đề cương đã định nghĩa; chỗ chưa có công thức ghi "chưa định nghĩa", không tự bịa).
- Chỉ số sức khỏe thương hiệu (BHI) là KPI tổng hợp trên dashboard.
- Cách nhúng: iframe (embedded dashboard), phân quyền xem theo vai trò.
- Mục "Cách chạy": ghi "Cập nhật khi có mã nguồn".

src/database/README.md gồm:
- Mô hình galaxy schema, PostgreSQL, schema raw / clean / dw và vai trò mỗi schema.
- Danh sách 6 bảng fact và 7 bảng dimension (tên bảng và grain, lấy từ mục 7 đề cương).
- Các thư mục: schema (DDL), migrations, seed. Ghi rõ seed chỉ chứa dữ liệu mẫu nhỏ tự tạo, KHÔNG chứa đánh giá thật.
- OLAP: roll-up, drill-down, slice, dice, pivot (một câu mỗi loại, đúng như đề cương).
- Mục "Cách chạy": ghi "Cập nhật khi có mã nguồn".

Không viết thông tin không có trong đề cương. Không đưa khóa API, .env, dữ liệu thật.

Tệp cần tạo: nhom03-65httt/src/bi/superset/README.md, nhom03-65httt/src/database/README.md

Tiêu chí xong: đủ 6 dashboard và 6 fact + 7 dim khớp đề cương; có dòng "Trạng thái" ở đầu; không công thức nào tự bịa.

[dán nguyên khối "Quy tắc bắt buộc" ở B0]
```

**Lệnh git** (nhánh `nhom03-65httt-hung-readme`):
```bash
git add nhom03-65httt/src/bi/superset/README.md nhom03-65httt/src/database/README.md
git status
git commit -m "docs(nhom03-65httt): readme thiet ke dashboard superset va kho du lieu"
git log -1 --format=%B
git push -u origin nhom03-65httt-hung-readme
```

---

### B5. GIANG THANH TÙNG (nhóm trưởng): Script gán nhãn (nhánh `nhom03-65httt-tung-labeling`)

**Tệp cần tạo:** `nhom03-65httt/src/ml/labeling/make_label_set.py`, `nhom03-65httt/src/ml/labeling/label_tools.py`, `nhom03-65httt/src/ml/labeling/README.md`

**Thông điệp commit:** `feat(nhom03-65httt): script tao va gop nhan tap vang`

**Chuẩn bị:** hai file nguồn là `make_label_set_v2.py` và `label_tools.py` trong thư mục `eduvision_scripts` (ngoài repo). Copy sang `src/ml/labeling/` (đổi tên `make_label_set_v2.py` thành `make_label_set.py`). **Không** copy file Excel gán nhãn và không copy dữ liệu: gửi hai file Excel cho 4 bạn qua kênh riêng.

```text
Bối cảnh: đồ án EduVision BI, tập vàng gán nhãn khoảng 600 mẫu (lô 500 mẫu 5 nền tảng và lô 100 mẫu Quizlet), cả 5 thành viên cùng gán, mỗi người khoảng 140 dòng, 100 mẫu hai người cùng gán để tính Cohen's kappa.

Việc (30 phút): đưa hai script gán nhãn vào nhom03-65httt/src/ml/labeling/ và viết README tiếng Việt cho thư mục đó.

README gồm: mục đích; cách tạo bộ gán nhãn (`python make_label_set.py <csv-dữ-liệu-đã-làm-sạch> <thư-mục-ra>`, input nằm ở nhom03-65httt/data/clean/, không commit); hai file ra (lô 1 và lô Quizlet); cách gộp nhãn và tính kappa (`python label_tools.py <các file xlsx đã gán> --out labeled`); quy ước nhãn (Tích cực, Trung tính, Tiêu cực, Bỏ qua và bốn khía cạnh Kỹ thuật, Học thuật, CSKH, Giá); nhắc rõ không đưa file Excel và CSV có nội dung đánh giá thật lên Git.

Kiểm tra: grep trong hai script đảm bảo không có khóa API hay đường dẫn tuyệt đối tới máy cá nhân.

Tệp cần tạo: nhom03-65httt/src/ml/labeling/make_label_set.py, nhom03-65httt/src/ml/labeling/label_tools.py, nhom03-65httt/src/ml/labeling/README.md

Tiêu chí xong: git status không thấy file .xlsx hoặc .csv; README khớp với cách chạy hai script.

[dán nguyên khối "Quy tắc bắt buộc" ở B0]
```

**Lệnh git** (nhánh `nhom03-65httt-tung-labeling`):
```bash
git add nhom03-65httt/src/ml/labeling/make_label_set.py nhom03-65httt/src/ml/labeling/label_tools.py nhom03-65httt/src/ml/labeling/README.md
git status
git commit -m "feat(nhom03-65httt): script tao va gop nhan tap vang"
git log -1 --format=%B
git push -u origin nhom03-65httt-tung-labeling
```

---

## PHẦN C. NHÓM TRƯỞNG DUYỆT PR

1. Mỗi PR: kiểm tra **Files changed** chỉ có tệp thuộc việc của người đó, đường dẫn bắt đầu bằng `nhom03-65httt/`.
2. Kiểm tra commit không có `Co-Authored-By`: trong PR, mở tab Commits.
3. Không có CSV, Excel, `.env`, `node_modules`, tệp nén.
4. Bấm **Merge pull request** (kiểu Merge), sau đó mọi người: `git checkout nhom03-65httt && git pull origin nhom03-65httt`.
5. Xong mỗi người có thể xóa nhánh riêng: `git branch -d <TEN-NHANH>`.
