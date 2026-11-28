# Hướng Dẫn Commit & Tạo Pull Request Vào Nhánh `dev` (Nhóm 07 — 65HTTT)

> [!CAUTION]
> **LƯU Ý QUAN TRỌNG NHẤT — TRÁNH TẠO NHẦM PR LÊN REPO GỐC CỦA GIẢNG VIÊN!**
>
> Repo làm việc của nhóm là **repo fork**, nên khi bấm **Compare & pull request**, GitHub thường **mặc định trỏ sang repo gốc của giảng viên**. Thành viên bắt buộc phải kiểm tra kỹ trước khi bấm tạo PR:
> - **ĐÚNG (Repo nhóm — `origin`):** `codecuatai/project-htkdtm` → nhánh **`dev`**
> - **SAI (Repo gốc giảng viên — `upstream`):** `oanhcuongdo/project-htkdtm` → **KHÔNG** tạo PR vào đây khi làm việc hàng ngày!

---

## 1. Quy ước nhánh & phân biệt Repository

| Thành phần | Tên / Đường dẫn | Mục đích |
| :--- | :--- | :--- |
| **Repo làm việc của nhóm (`origin`)** | `https://github.com/codecuatai/project-htkdtm` | Toàn bộ thành viên clone, push nhánh và tạo PR vào đây. |
| **Repo gốc giảng viên (`upstream`)** | `https://github.com/oanhcuongdo/project-htkdtm` | Chỉ dùng để nhóm trưởng nộp bài cuối kỳ (từ nhánh `nhom07-65httt`), **không tạo PR phát triển vào đây**. |
| **Nhánh tích hợp chung** | `dev` | Mọi tính năng mới đều tách nhánh từ `dev` và tạo PR gộp lại vào `dev`. |
| **Nhánh làm việc cá nhân** | `feature/...`, `fix/...`, `docs/...`, `data/...` | Mỗi task hoặc module tạo một nhánh riêng, không code trực tiếp trên `main` hay `dev`. |

### Kiểm tra remote trên máy trước khi làm
Chạy lệnh sau tại thư mục gốc dự án:
```powershell
git remote -v
```
Đảm bảo `origin` trỏ đúng về repo của nhóm:
```text
origin  https://github.com/codecuatai/project-htkdtm.git (fetch)
origin  https://github.com/codecuatai/project-htkdtm.git (push)
```
*(Nếu lỡ clone từ `oanhcuongdo/project-htkdtm`, hãy đổi lại bằng lệnh: `git remote set-url origin https://github.com/codecuatai/project-htkdtm.git`.)*

---

## 2. Tạo nhánh mới từ `dev`

Trước khi bắt đầu làm task mới, luôn kéo code mới nhất của `dev` rồi mới tách nhánh:

```powershell
# 1. Chuyển sang nhánh dev và cập nhật code mới nhất
git checkout dev
git pull origin dev

# 2. Tạo nhánh mới theo quy ước đặt tên
git checkout -b feature/<ten-chuc-nang>
```

### Quy ước đặt tên nhánh (không dấu, chữ thường, nối bằng `-`)
- `feature/<mo-ta>` — Tính năng mới (VD: `feature/learning-profile-api`, `feature/recommender-m2`, `feature/skill-roadmap-ui`)
- `fix/<mo-ta>` — Sửa lỗi (VD: `fix/payment-idempotency`, `fix/filter-price-bug`)
- `data/<mo-ta>` — Thu thập, làm sạch, phát hành dữ liệu (VD: `data/crawl-detail-metadata`, `data/dq-report-v1`)
- `docs/<mo-ta>` — Tài liệu, báo cáo, khảo sát, test plan (VD: `docs/taxonomy-and-ground-truth`, `docs/update-api-spec`)

---

## 3. Kiểm tra file & Commit đúng chuẩn

### Checklist trước khi commit
- Chỉ chỉnh sửa file nằm trong thư mục `nhom07-65httt/` (không sửa file ở thư mục gốc repo trừ khi nhóm trưởng yêu cầu).
- **Tuyệt đối không commit:** file `.env`, API key/mật khẩu, dữ liệu cá nhân thật (PII), thư mục `node_modules/`, `__pycache__/`, `.venv/`.
- Chạy `git status` và `git diff` để kiểm tra kỹ các file sắp commit.

### Quy ước viết Commit Message (Conventional Commits)
Định dạng:
```text
<type>(<scope>): <mô tả ngắn gọn, dưới 70 ký tự>
```

| Type | Khi nào dùng | Ví dụ |
| :--- | :--- | :--- |
| `feat` | Thêm chức năng mới | `feat(backend): add learning profile and intake test APIs` |
| `fix` | Sửa lỗi | `fix(payment): enforce idempotency key on sandbox webhook` |
| `data` | Cập nhật crawler, ETL, dataset | `data(crawl): extract course duration and skill metadata` |
| `docs` | Cập nhật tài liệu, báo cáo, taxonomy | `docs(qa): add ground truth rubric and RBAC test cases` |
| `ref` | Tái cấu trúc code (không đổi hành vi) | `ref(ai): extract shared candidate filter for M0-M2` |
| `test` | Bổ sung hoặc sửa test | `test(e2e): add SmartEdu profile-to-purchase Playwright spec` |
| `chore` | Cấu hình, dependency, việc lặt vặt | `chore(docker): add Apache Superset service to compose` |

### Các lệnh commit và push nhánh lên `origin`
```powershell
# 1. Xem các file đã thay đổi
git status

# 2. Stage các file cần thiết (tránh dùng `git add .` bừa bãi nếu có file rác)
git add nhom07-65httt/<duong-dan-file>

# 3. Commit theo chuẩn
git commit -m "feat(frontend): add course recommendation card with S/G/L scores"

# 4. Cập nhật code mới nhất từ dev để xử lý xung đột (nếu có) ngay trên máy
git fetch origin
git merge origin/dev

# 5. Đẩy nhánh của bạn lên repo nhóm (origin)
git push -u origin <ten-nhanh-cua-ban>
```

---

## 4. Tạo Pull Request vào nhánh `dev` (Không bị nhầm sang repo gốc!)

### Cách 1 (KHUYẾN NGHỊ — An toàn 100%, không thể chọn nhầm repo gốc)
Sau khi `git push`, mở trực tiếp đường link theo mẫu sau trên trình duyệt (thay `<ten-nhanh-cua-ban>` bằng tên nhánh vừa push):

```text
https://github.com/codecuatai/project-htkdtm/compare/dev...<ten-nhanh-cua-ban>
```

*Ví dụ:* `https://github.com/codecuatai/project-htkdtm/compare/dev...feature/skill-roadmap-ui`

Link này sẽ khóa sẵn đích đến là **`codecuatai/project-htkdtm` nhánh `dev`**.

### Cách 2 (Tạo trực tiếp trên giao diện GitHub)
1. Vào trang repo của nhóm: `https://github.com/codecuatai/project-htkdtm`
2. Chuyển sang tab **Pull requests** → bấm **New pull request**.
3. **BẮT BUỘC KIỂM TRA 4 Ô CHỌN Ở PHÍA TRÊN CÙNG:**
   - Nếu thấy **`base repository: oanhcuongdo/project-htkdtm`** → bấm vào đó và **đổi ngay** sang **`codecuatai/project-htkdtm`**!
   - Ô **`base:`** chọn **`dev`** (không chọn `main`).
   - Ô **`head repository:`** chọn **`codecuatai/project-htkdtm`**.
   - Ô **`compare:`** chọn **nhánh của bạn**.

Hãy chắc chắn thanh so sánh trên GitHub hiển thị đúng như sơ đồ này:
```text
base repository: codecuatai/project-htkdtm  |  base: dev
                                    ⬅
head repository: codecuatai/project-htkdtm  |  compare: <ten-nhanh-cua-ban>
```

### Checklist 5 giây trước khi bấm "Create pull request"
- [ ] `base repository` là **`codecuatai/project-htkdtm`** (KHÔNG PHẢI `oanhcuongdo/project-htkdtm`)?
- [ ] `base` branch là **`dev`** (KHÔNG PHẢI `main`)?
- [ ] Tab **Files changed** chỉ chứa các file trong phạm vi task của bạn, không dính `.env` hay file tạm?
- [ ] Đã gán Reviewer là nhóm trưởng (**Trần Văn Tài**) hoặc thành viên liên quan?

---

## 5. Mẫu mô tả Pull Request (Copy & điền nhanh)

```markdown
## Mục tiêu
- Mô tả ngắn gọn PR này giải quyết task nào trong `danhsachnhom.md` (VD: Mục 2.5 — Task 4: Giao diện gợi ý AI Top-K).

## Thay đổi chính
- [ ] ...
- [ ] ...

## Cách kiểm thử / Minh chứng
- Đã chạy lệnh kiểm thử: `...` (hoặc đính kèm ảnh chụp giao diện / log kết quả).
- Trạng thái CI: Pass / Đang chờ chạy.
```

---

## 6. Xử lý nhanh nếu lỡ tạo nhầm PR lên repo gốc (`oanhcuongdo/project-htkdtm`)

Đừng lo lắng, xử lý ngay trong 30 giây:
1. Mở trang Pull Request vừa tạo nhầm trên `oanhcuongdo/project-htkdtm`.
2. Kéo xuống cuối trang và bấm nút **Close pull request**.
3. Quay lại **Mục 4 (Cách 1)** ở trên để mở PR mới đúng vào `codecuatai/project-htkdtm` nhánh `dev`.
