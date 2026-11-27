# Quy trình cộng tác & chuẩn nộp code nhóm `nhom02-65httt`

Tài liệu này bổ sung quy trình làm việc thực tế trên fork `minhnguyendev05/project-htkdtm` để tránh xung đột mã nguồn và giữ nhánh tích hợp của nhóm luôn chạy được. Quy định chung của giảng viên trong [README gốc](../README.md) luôn được ưu tiên cao nhất.

---

## 1. Mô hình nhánh (Branching Model)

- **`nhom02-65httt`**: Nhánh tích hợp chính của nhóm. **Không commit trực tiếp lên nhánh này.** Nhánh chỉ tiếp nhận mã nguồn qua Pull Request từ nhánh riêng của từng thành viên sau khi Nhóm trưởng review.
- **`nhom02-<ten>`**: Nhánh làm việc riêng của từng thành viên (ví dụ: `nhom02-minh`, `nhom02-leminhtu`, `nhom02-Yen`, `nhom02-Trung`, `nhom02-Truong` / `nhom2-Truong`). **Lưu ý:** Mọi nhánh thành viên bắt buộc tạo từ `origin/nhom02-65httt` (hoặc merge `origin/nhom02-65httt` vào), không tạo trực tiếp từ `main`.
- **`main` (upstream `oanhcuongdo/project-htkdtm`)**: Chỉ nhận Pull Request tổng hợp từ `nhom02-65httt` khi nộp bài cho giảng viên.

## 2. Đồng bộ và tạo Pull Request

Trước khi mở PR vào `nhom02-65httt`, thành viên đồng bộ nhánh cá nhân với nhánh nhóm mới nhất:

```bash
git fetch origin
git checkout nhom02-<ten>
git merge origin/nhom02-65httt
```

Sau khi xử lý xung đột (nếu có) và kiểm tra test pass:

```bash
git add nhom02-65httt/
git commit -m "<loai>(nhom02-65httt): <mo-ta-ngan-gon-khong-dau>"
git push origin nhom02-<ten>
```

Mở Pull Request trên GitHub fork (`minhnguyendev05/project-htkdtm`):
- **base:** `nhom02-65httt`
- **compare:** `nhom02-<ten>`

Quy ước tiền tố commit: Chỉ dùng đúng 3 loại `feat`, `fix`, `docs` theo README gốc của giảng viên (dù chuẩn Conventional Commits quốc tế có thêm `refactor`, `test`..., nhưng không dùng để tránh lệch quy chuẩn dự án; ví dụ: `feat(nhom02-65httt): them API quan ly san pham`).

## 3. Phân vùng sở hữu thư mục theo phân công

| Thành viên | Vai trò | Phạm vi thư mục phụ trách chính |
| :--- | :--- | :--- |
| **Nguyễn Anh Minh** | Nhóm trưởng / Backend Core & Integration Lead | `docker-compose.yml`, `.env.example`, `infra/`, `src/backend/app/{core,db,api/deps,integrations,worker,scripts}`, API `users`/`audit-logs`/`channels`/`executions`/`dashboard`, khung nền `src/backend/app/crawler/` |
| **Trần Đức Trung** | Database Seed, ERP Backend & OLAP Views Developer | Script seed 60–100 SKU + dữ liệu bán hàng trên schema 18 bảng sẵn có, `src/database/views_bi.sql` (Star Schema), các endpoint & schema CRUD ERP (`categories`, `suppliers`, `products`, `costs`, `inventory`, `channel-listings`) |
| **Lê Minh Tú** | AI / ML & Smart Pricing Backend Engineer | `src/backend/app/ml/` (gom `src/backend/ml/demand_baseline.py` vào `app/ml/` khi tích hợp), Rule Engine & công thức $P_{\min}$, API `pricing-rules`/`pricing/preview`/`pricing/run`/`recommendations` (Approve/Reject) |
| **Nghiêm Xuân Trường** | Data Crawler, Scheduler & BI (Superset) Engineer | Kế thừa & chuẩn hóa `src/backend/app/crawler/` thành 5 Adapter + Entity Resolution (`RapidFuzz`), API `competitors`/`competitor-prices`/`crawler`, lịch `celery_beat`, 3 Dashboard Apache Superset & đối chiếu BI/E2E |
| **Nguyễn Thị Yên** | Frontend Lead | Toàn bộ `src/frontend/` (mọi phân hệ ERP, Đối thủ, Đề xuất giá, Phê duyệt, Quy tắc, Thực thi, BI, Quản trị) và lớp HTTP Client nối FastAPI thật |

## 4. Checklist review trước khi merge vào `nhom02-65httt`

- [ ] 100% thay đổi nằm bên trong `nhom02-65httt/`, không sửa `README.md` gốc, `.gitignore` gốc hay thư mục nhóm khác.
- [ ] Không commit tệp nhạy cảm hoặc rác build: `.env`, `node_modules/`, `.venv/`, `__pycache__/`, `.pytest_cache/`, `dist/`, `build/`.
- [ ] **Cảnh báo tên thư mục theo `.gitignore` gốc:** Không đặt tên thư mục mã nguồn là `lib/`, `build/`, `dist/`, `env/`, `var/`, `parts/`, `downloads/`, `eggs/` vì `.gitignore` ở thư mục gốc bỏ qua các tên này trên toàn repo (ví dụ: frontend cần xử lý riêng cho `src/lib/` trong `src/frontend/.gitignore` hoặc đổi tên/force-add theo hướng dẫn).
- [ ] Mỗi thành viên tự viết unit/API test cho module mình phụ trách; Backend test & lint pass (`pytest -q`, `ruff check .`); Frontend pass (`npm run typecheck && npm run build`).
- [ ] Thay đổi database phải thêm file migration Alembic mới (`alembic/versions/...`), **không sửa** file migration đã merge vào `nhom02-65httt`.
- [ ] Nếu thay đổi API contract (field, enum, route), cập nhật đồng bộ giữa backend schema và frontend `src/types/domain.ts`.
