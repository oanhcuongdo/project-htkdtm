# Thiết kế cấu trúc mã nguồn – Vị Việt (Nhóm 14 – 65HTTT)

> [!NOTE]
> Tài liệu này là **bản thiết kế**, chưa tạo file nào. Mục đích: chốt bố cục để chia việc và bắt đầu lập trình.

---

## A. Kiến trúc tổng quan

```
┌─────────────┐    ┌────────────────────────────────────┐    ┌────────────┐
│  React SPA  │───▶│  FastAPI (một process, nhiều module)│───▶│ PostgreSQL │
│  (Vite+TS)  │    │  ┌────────┬─────┬──────┬─────────┐ │    │            │
│             │    │  │  Auth  │ Biz │  AI  │ Tracking│ │    │ OLTP tables│
│  Tracking   │    │  └────────┴─────┴──────┴─────────┘ │    │ BI views   │
│  client     │    │  Alembic migrations (cùng process)  │    └─────┬──────┘
└─────────────┘    │  ETL scripts (chạy theo lịch/CLI)   │          │
                   └────────────────────────────────────┘    ┌──────▼──────┐
                                                             │  Power BI   │
                                                             │  (kết nối   │
                                                             │  trực tiếp) │
                                                             └─────────────┘
```

**Lý do chọn monolith chia module:**
- Nhóm 5 người, 8 tuần – không đủ nhân lực vận hành nhiều service.
- AI (scikit-learn) và ETL (Python scripts) nằm trong cùng codebase backend, chia thành `app/ai/` và `app/etl/`. Chúng dùng chung kết nối DB và models.
- Power BI kết nối trực tiếp tới PostgreSQL qua views/materialized views đã chuẩn bị sẵn trong migration; không cần data warehouse riêng.
- Migration là **nguồn schema duy nhất** – quản lý bởi Alembic trong `src/backend/`. Thư mục `src/database/` chứa tài liệu thiết kế (ERD, từ điển dữ liệu), seed data, truy vấn BI, và tài liệu Power BI – không chứa migration hay schema cạnh tranh.

**Quy ước route chủ quán:**
- Thư mục frontend: `pages/vendor/` và `pages/admin/`
- API prefix: `/api/v1/vendor/...` và `/api/v1/admin/...`
- Thuật ngữ thống nhất trong code và tài liệu: **vendor** (chủ quán), **customer** (khách hàng), **admin** (quản trị viên).

---

## B. Cây thư mục đầy đủ

Ký hiệu:
- ✅ = file/thư mục **đã có** trên nhánh `nhom14-65httt`
- 🆕 = **cần tạo** (bắt buộc cho MVP)
- 📌 = **đề xuất** (mở rộng hoặc tương lai, chưa kiểm chứng)
- 🔧 = **sản phẩm phát sinh** khi chạy (không commit)

```
nhom14-65httt/                                    ✅
├── danhsachnhom.md                                ✅
├── README.md                                      ✅ (sẽ cập nhật khi có mã nguồn)
├── .env.example                                   🆕
├── docker-compose.yml                             🆕
├── Makefile                                       🆕
│
├── docs/                                          ✅
│   ├── De_cuong_Vi_Viet.docx                      ✅
│   ├── NGUON_DU_LIEU.md                           🆕
│   ├── KE_HOACH_THUC_HIEN.md                      🆕
│   ├── CHECKLIST_NOP_BAI.md                       🆕
│   ├── KIEN_TRUC.md                               🆕
│   ├── ERD.md                                     🆕
│   ├── TU_DIEN_DU_LIEU.md                         🆕
│   ├── API_CONTRACT.md                            🆕
│   ├── EVENT_CATALOG.md                           🆕
│   ├── HUONG_DAN_CAI_DAT.md                       🆕
│   └── HUONG_DAN_DEMO.md                          🆕
│
├── src/
│   ├── backend/                                   ✅ (thư mục, hiện chỉ có README)
│   │   ├── README.md                              ✅ (sẽ cập nhật)
│   │   ├── pyproject.toml                         🆕
│   │   ├── requirements.txt                       🆕
│   │   ├── requirements-dev.txt                   🆕
│   │   ├── Dockerfile                             🆕
│   │   ├── alembic.ini                            🆕
│   │   ├── conftest.py                            🆕
│   │   │
│   │   ├── alembic/                               🆕
│   │   │   ├── env.py                             🆕
│   │   │   ├── script.py.mako                     🆕
│   │   │   └── versions/                          🆕
│   │   │       └── 001_initial_schema.py          🆕
│   │   │
│   │   ├── app/                                   🆕
│   │   │   ├── __init__.py                        🆕
│   │   │   ├── main.py                            🆕
│   │   │   ├── config.py                          🆕
│   │   │   ├── database.py                        🆕
│   │   │   ├── exceptions.py                      🆕
│   │   │   ├── dependencies.py                    🆕
│   │   │   ├── middleware.py                       🆕
│   │   │   │
│   │   │   ├── auth/                              🆕
│   │   │   │   ├── __init__.py                    🆕
│   │   │   │   ├── router.py                      🆕
│   │   │   │   ├── schemas.py                     🆕
│   │   │   │   ├── service.py                     🆕
│   │   │   │   ├── dependencies.py                🆕
│   │   │   │   └── utils.py                       🆕
│   │   │   │
│   │   │   ├── users/                             🆕
│   │   │   │   ├── __init__.py                    🆕
│   │   │   │   ├── router.py                      🆕
│   │   │   │   ├── schemas.py                     🆕
│   │   │   │   ├── service.py                     🆕
│   │   │   │   └── models.py                      🆕
│   │   │   │
│   │   │   ├── preferences/                       🆕
│   │   │   │   ├── __init__.py                    🆕
│   │   │   │   ├── router.py                      🆕
│   │   │   │   ├── schemas.py                     🆕
│   │   │   │   ├── service.py                     🆕
│   │   │   │   └── models.py                      🆕
│   │   │   │
│   │   │   ├── restaurants/                       🆕
│   │   │   │   ├── __init__.py                    🆕
│   │   │   │   ├── router.py                      🆕
│   │   │   │   ├── schemas.py                     🆕
│   │   │   │   ├── service.py                     🆕
│   │   │   │   └── models.py                      🆕
│   │   │   │
│   │   │   ├── menu/                              🆕
│   │   │   │   ├── __init__.py                    🆕
│   │   │   │   ├── router.py                      🆕
│   │   │   │   ├── schemas.py                     🆕
│   │   │   │   ├── service.py                     🆕
│   │   │   │   └── models.py                      🆕
│   │   │   │
│   │   │   ├── orders/                            🆕
│   │   │   │   ├── __init__.py                    🆕
│   │   │   │   ├── router.py                      🆕
│   │   │   │   ├── schemas.py                     🆕
│   │   │   │   ├── service.py                     🆕
│   │   │   │   ├── models.py                      🆕
│   │   │   │   └── state_machine.py               🆕
│   │   │   │
│   │   │   ├── reviews/                           🆕
│   │   │   │   ├── __init__.py                    🆕
│   │   │   │   ├── router.py                      🆕
│   │   │   │   ├── schemas.py                     🆕
│   │   │   │   ├── service.py                     🆕
│   │   │   │   └── models.py                      🆕
│   │   │   │
│   │   │   ├── search/                            🆕
│   │   │   │   ├── __init__.py                    🆕
│   │   │   │   ├── router.py                      🆕
│   │   │   │   ├── schemas.py                     🆕
│   │   │   │   └── service.py                     🆕
│   │   │   │
│   │   │   ├── tracking/                          🆕
│   │   │   │   ├── __init__.py                    🆕
│   │   │   │   ├── router.py                      🆕
│   │   │   │   ├── schemas.py                     🆕
│   │   │   │   ├── service.py                     🆕
│   │   │   │   └── models.py                      🆕
│   │   │   │
│   │   │   ├── vendor/                            🆕
│   │   │   │   ├── __init__.py                    🆕
│   │   │   │   ├── router.py                      🆕
│   │   │   │   ├── schemas.py                     🆕
│   │   │   │   └── service.py                     🆕
│   │   │   │
│   │   │   ├── admin/                             🆕
│   │   │   │   ├── __init__.py                    🆕
│   │   │   │   ├── router.py                      🆕
│   │   │   │   ├── schemas.py                     🆕
│   │   │   │   └── service.py                     🆕
│   │   │   │
│   │   │   ├── ai/                                🆕
│   │   │   │   ├── __init__.py                    🆕
│   │   │   │   ├── router.py                      🆕
│   │   │   │   ├── schemas.py                     🆕
│   │   │   │   ├── service.py                     🆕
│   │   │   │   ├── feature_encoder.py             🆕
│   │   │   │   ├── candidate_filter.py            🆕
│   │   │   │   ├── scorer.py                      🆕
│   │   │   │   ├── diversifier.py                 🆕
│   │   │   │   ├── explainer.py                   🆕
│   │   │   │   ├── baseline.py                    🆕
│   │   │   │   └── config.py                      🆕
│   │   │   │
│   │   │   └── etl/                               🆕
│   │   │       ├── __init__.py                    🆕
│   │   │       ├── run_etl.py                     🆕
│   │   │       ├── attribution.py                 🆕
│   │   │       ├── fact_builders.py               🆕
│   │   │       └── validation.py                  🆕
│   │   │
│   │   ├── scripts/                               🆕
│   │   │   ├── seed.py                            🆕
│   │   │   ├── load_vifoodrec.py                  🆕
│   │   │   └── benchmark_recommendation.py        🆕
│   │   │
│   │   └── tests/                                 🆕
│   │       ├── __init__.py                        🆕
│   │       ├── conftest.py                        🆕
│   │       ├── test_auth.py                       🆕
│   │       ├── test_orders.py                     🆕
│   │       ├── test_order_state_machine.py        🆕
│   │       ├── test_recommendations.py            🆕
│   │       ├── test_tracking.py                   🆕
│   │       ├── test_vendor_access.py              🆕
│   │       ├── test_search.py                     🆕
│   │       ├── test_idempotency.py                🆕
│   │       ├── test_constraints.py                🆕
│   │       └── test_etl.py                        🆕
│   │
│   ├── frontend/                                  ✅ (thư mục, hiện chỉ có README)
│   │   ├── README.md                              ✅ (sẽ cập nhật)
│   │   ├── package.json                           🆕
│   │   ├── package-lock.json                      🆕 (tự sinh bởi npm)
│   │   ├── tsconfig.json                          🆕
│   │   ├── tsconfig.node.json                     🆕
│   │   ├── vite.config.ts                         🆕
│   │   ├── index.html                             🆕
│   │   ├── Dockerfile                             🆕
│   │   ├── .env.example                           🆕
│   │   ├── eslint.config.js                       🆕
│   │   │
│   │   ├── public/                                🆕
│   │   │   └── favicon.svg                        🆕
│   │   │
│   │   └── src/                                   🆕
│   │       ├── main.tsx                           🆕
│   │       ├── App.tsx                            🆕
│   │       ├── router.tsx                         🆕
│   │       ├── vite-env.d.ts                      🆕
│   │       │
│   │       ├── api/                               🆕
│   │       │   ├── client.ts                      🆕
│   │       │   ├── auth.ts                        🆕
│   │       │   ├── restaurants.ts                 🆕
│   │       │   ├── menu.ts                        🆕
│   │       │   ├── orders.ts                      🆕
│   │       │   ├── recommendations.ts             🆕
│   │       │   ├── tracking.ts                    🆕
│   │       │   ├── preferences.ts                 🆕
│   │       │   ├── reviews.ts                     🆕
│   │       │   ├── search.ts                      🆕
│   │       │   ├── vendor.ts                      🆕
│   │       │   └── admin.ts                       🆕
│   │       │
│   │       ├── types/                             🆕
│   │       │   ├── auth.ts                        🆕
│   │       │   ├── restaurant.ts                  🆕
│   │       │   ├── menu.ts                        🆕
│   │       │   ├── order.ts                       🆕
│   │       │   ├── recommendation.ts              🆕
│   │       │   ├── tracking.ts                    🆕
│   │       │   ├── preference.ts                  🆕
│   │       │   ├── review.ts                      🆕
│   │       │   └── common.ts                      🆕
│   │       │
│   │       ├── hooks/                             🆕
│   │       │   ├── useAuth.ts                     🆕
│   │       │   ├── useLocation.ts                 🆕
│   │       │   ├── useCart.ts                     🆕
│   │       │   ├── useTracking.ts                 🆕
│   │       │   └── useIdempotency.ts              🆕
│   │       │
│   │       ├── contexts/                          🆕
│   │       │   ├── AuthContext.tsx                 🆕
│   │       │   ├── CartContext.tsx                 🆕
│   │       │   └── LocationContext.tsx             🆕
│   │       │
│   │       ├── components/                        🆕
│   │       │   ├── layout/                        🆕
│   │       │   │   ├── AppShell.tsx                🆕
│   │       │   │   ├── Navbar.tsx                  🆕
│   │       │   │   ├── Footer.tsx                  🆕
│   │       │   │   └── RoleGuard.tsx               🆕
│   │       │   │
│   │       │   ├── common/                        🆕
│   │       │   │   ├── LoadingSpinner.tsx          🆕
│   │       │   │   ├── EmptyState.tsx              🆕
│   │       │   │   ├── ErrorBoundary.tsx           🆕
│   │       │   │   ├── ErrorDisplay.tsx            🆕
│   │       │   │   └── ConfirmDialog.tsx           🆕
│   │       │   │
│   │       │   ├── map/                           🆕
│   │       │   │   ├── MapView.tsx                 🆕
│   │       │   │   ├── LocationPicker.tsx          🆕
│   │       │   │   └── AddressFallback.tsx         🆕
│   │       │   │
│   │       │   ├── menu/                          🆕
│   │       │   │   ├── DishCard.tsx                🆕
│   │       │   │   ├── MenuList.tsx                🆕
│   │       │   │   └── DishDetail.tsx              🆕
│   │       │   │
│   │       │   ├── recommendation/                🆕
│   │       │   │   ├── RecommendationList.tsx      🆕
│   │       │   │   ├── RecommendationCard.tsx      🆕
│   │       │   │   ├── ReasonBadge.tsx             🆕
│   │       │   │   ├── FeedbackButtons.tsx         🆕
│   │       │   │   └── NotPersonalized.tsx         🆕
│   │       │   │
│   │       │   ├── cart/                          🆕
│   │       │   │   ├── CartDrawer.tsx              🆕
│   │       │   │   ├── CartItem.tsx                🆕
│   │       │   │   └── CheckoutForm.tsx            🆕
│   │       │   │
│   │       │   ├── order/                         🆕
│   │       │   │   ├── OrderCard.tsx               🆕
│   │       │   │   ├── OrderTimeline.tsx           🆕
│   │       │   │   └── ReviewForm.tsx              🆕
│   │       │   │
│   │       │   └── evaluation/                    🆕
│   │       │       └── BlindEvalForm.tsx           🆕
│   │       │
│   │       └── pages/                             🆕
│   │           ├── auth/                          🆕
│   │           │   ├── LoginPage.tsx               🆕
│   │           │   └── RegisterPage.tsx            🆕
│   │           │
│   │           ├── customer/                      🆕
│   │           │   ├── HomePage.tsx                🆕
│   │           │   ├── PreferencePage.tsx          🆕
│   │           │   ├── SearchPage.tsx              🆕
│   │           │   ├── RestaurantPage.tsx          🆕
│   │           │   ├── DishDetailPage.tsx          🆕
│   │           │   ├── CartPage.tsx                🆕
│   │           │   ├── CheckoutPage.tsx            🆕
│   │           │   ├── OrderListPage.tsx           🆕
│   │           │   ├── OrderDetailPage.tsx         🆕
│   │           │   └── EvaluationPage.tsx          🆕
│   │           │
│   │           ├── vendor/                        🆕
│   │           │   ├── DashboardPage.tsx           🆕
│   │           │   ├── ProfilePage.tsx             🆕
│   │           │   ├── MenuManagePage.tsx          🆕
│   │           │   ├── IngredientPage.tsx          🆕
│   │           │   ├── OrderManagePage.tsx         🆕
│   │           │   └── StatsPage.tsx               🆕
│   │           │
│   │           ├── admin/                         🆕
│   │           │   ├── DashboardPage.tsx           🆕
│   │           │   ├── RestaurantApprovalPage.tsx  🆕
│   │           │   ├── DishCatalogPage.tsx         🆕
│   │           │   ├── UserManagePage.tsx          🆕
│   │           │   └── DataQualityPage.tsx         🆕
│   │           │
│   │           └── NotFoundPage.tsx               🆕
│   │
│   └── database/                                  ✅ (thư mục, hiện chỉ có README)
│       ├── README.md                              ✅ (sẽ cập nhật)
│       │
│       ├── seed/                                  🆕
│       │   ├── README.md                          🆕
│       │   ├── canonical_dishes.json              🆕
│       │   ├── ingredients.json                   🆕
│       │   ├── regions_and_labels.json             🆕
│       │   ├── sample_restaurants.json             🆕
│       │   ├── sample_menu_items.json              🆕
│       │   ├── sample_users.json                   🆕
│       │   └── sample_orders.json                  🆕
│       │
│       ├── vifoodrec/                             🆕
│       │   ├── README.md                          🆕
│       │   └── mapping.json                       🆕
│       │
│       ├── bi/                                    🆕
│       │   ├── README.md                          🆕
│       │   ├── views_fact_order_item.sql           🆕
│       │   ├── views_fact_rec_impression.sql       🆕
│       │   ├── views_fact_session.sql              🆕
│       │   ├── views_dimensions.sql               🆕
│       │   ├── kpi_queries.sql                    🆕
│       │   ├── reconciliation.sql                 🆕
│       │   └── data_quality_checks.sql            🆕
│       │
│       └── powerbi/                               🆕
│           ├── README.md                          🆕
│           ├── Vi_Viet_Dashboard.pbix             🆕 (sản phẩm Power BI, file nhị phân)
│           ├── dax_measures.md                    🆕
│           └── dashboard_guide.md                 🆕
│
│   (Các sản phẩm phát sinh – KHÔNG commit)
│   🔧 src/backend/.venv/
│   🔧 src/frontend/node_modules/
│   🔧 src/frontend/dist/
│   🔧 src/backend/__pycache__/
│   🔧 *.pyc
│   🔧 .env
```

> [!IMPORTANT]
> **Nguồn schema duy nhất** là `src/backend/alembic/versions/`. Thư mục `src/database/` chỉ chứa tài liệu thiết kế, seed data, truy vấn BI và tài liệu Power BI. Các BI views cũng được thực thi thông qua migration hoặc script riêng, nhưng file SQL gốc nằm ở `src/database/bi/` để Power BI developer đọc độc lập.

---

## C. Bảng trách nhiệm từng nhóm file

### C.1 Gốc dự án và vận hành

| Đường dẫn | Trách nhiệm | Phụ thuộc chính | Người phụ trách |
|:---|:---|:---|:---|
| `README.md` | Tổng quan, link tới docs, lệnh chạy | — | Đinh Văn Mạnh |
| `danhsachnhom.md` | Thông tin nhóm theo mẫu giảng viên | — | Đinh Văn Mạnh |
| `.env.example` | Biến môi trường mẫu (DB, JWT secret placeholder, Maps API key placeholder) – không chứa giá trị thật | — | Đinh Văn Mạnh |
| `docker-compose.yml` | Khởi PostgreSQL, backend, frontend trong container | Dockerfile BE + FE | Đinh Văn Mạnh |
| `Makefile` | Tập hợp lệnh: `make dev`, `make migrate`, `make seed`, `make test`, `make etl` | docker-compose | Đinh Văn Mạnh |

### C.2 Tài liệu (`docs/`)

| Đường dẫn | Trách nhiệm | Phụ thuộc chính | Người phụ trách |
|:---|:---|:---|:---|
| `NGUON_DU_LIEU.md` | Mô tả nguồn ViFoodRec, quy tắc làm sạch, ánh xạ, cờ mô phỏng | ViFoodRec repo | Nguyễn Mạnh Đức |
| `KE_HOACH_THUC_HIEN.md` | Lộ trình 8 tuần, milestone, tiêu chí | — | Đinh Văn Mạnh |
| `CHECKLIST_NOP_BAI.md` | Danh sách kiểm tra trước PR nộp bài | — | Đinh Văn Mạnh |
| `KIEN_TRUC.md` | Sơ đồ kiến trúc, luồng dữ liệu, quyết định thiết kế | — | Đinh Văn Mạnh |
| `ERD.md` | Sơ đồ quan hệ thực thể (Mermaid hoặc hình) | Models backend | Phạm Trọng Sang |
| `TU_DIEN_DU_LIEU.md` | Mô tả từng bảng, cột, kiểu, ràng buộc, quan hệ | ERD | Phạm Trọng Sang |
| `API_CONTRACT.md` | Danh sách endpoint, method, request/response schema, mã lỗi | Schemas backend | Phạm Hồng Thái |
| `EVENT_CATALOG.md` | Danh sách event_type, payload, quy tắc ghi, session/request ID | Tracking module | Đỗ Đình Đức |
| `HUONG_DAN_CAI_DAT.md` | Bước cài đặt đã kiểm chứng: clone, env, docker, migrate, seed, chạy | docker-compose | Đinh Văn Mạnh |
| `HUONG_DAN_DEMO.md` | Kịch bản demo 3 vai trò, dữ liệu mẫu, ảnh chụp hoặc video | Ứng dụng hoạt động | Đinh Văn Mạnh |

### C.3 Backend – Lõi (`src/backend/app/`)

| Đường dẫn | Trách nhiệm | Phụ thuộc chính | Người phụ trách |
|:---|:---|:---|:---|
| `main.py` | Entry point FastAPI, mount router, middleware, startup/shutdown | config, database | Đinh Văn Mạnh |
| `config.py` | Đọc biến môi trường (pydantic-settings), các hằng số | .env | Đinh Văn Mạnh |
| `database.py` | SQLAlchemy engine, SessionLocal, Base declarative | config | Đinh Văn Mạnh |
| `exceptions.py` | Exception classes nghiệp vụ + handler trả JSON chuẩn | — | Đinh Văn Mạnh |
| `dependencies.py` | Dependency injection: get_db, get_current_user, require_role | auth, database | Đinh Văn Mạnh |
| `middleware.py` | CORS, request logging, request-id header | config | Đinh Văn Mạnh |

### C.4 Backend – Auth & Users

| Đường dẫn | Trách nhiệm | Phụ thuộc chính | Người phụ trách |
|:---|:---|:---|:---|
| `auth/router.py` | POST `/auth/register`, `/auth/login`, `/auth/me` | auth/service | Đinh Văn Mạnh |
| `auth/service.py` | Hash mật khẩu, tạo/xác thực JWT, refresh token | models User | Đinh Văn Mạnh |
| `auth/schemas.py` | RegisterRequest, LoginRequest, TokenResponse, UserOut | — | Đinh Văn Mạnh |
| `auth/dependencies.py` | `get_current_user`, `require_role(role)`, `require_vendor_owner(restaurant_id)` | JWT, DB | Đinh Văn Mạnh |
| `users/models.py` | SQLAlchemy model: User (id, email, hashed_password, role, created_at) | Base | Đinh Văn Mạnh |
| `users/router.py` | GET/PATCH profile | users/service | Đinh Văn Mạnh |

### C.5 Backend – Nghiệp vụ theo module

Mỗi module có cấu trúc: `models.py` (SQLAlchemy), `schemas.py` (Pydantic), `router.py` (endpoint), `service.py` (logic nghiệp vụ).

| Module | Trách nhiệm chính | Models đáng chú ý | Người phụ trách |
|:---|:---|:---|:---|
| `preferences/` | CRUD khẩu vị 5 câu hỏi; mã hóa profile vector | Preference | Nguyễn Mạnh Đức |
| `restaurants/` | CRUD quán, giờ mở, phạm vi giao, trạng thái duyệt | Restaurant, RestaurantMembership | Phạm Hồng Thái |
| `menu/` | CanonicalDish, MenuItem, Ingredient, MenuItemIngredient, khả dụng | CanonicalDish, MenuItem, Ingredient, MenuItemIngredient | Phạm Hồng Thái |
| `orders/` | Tạo đơn (snapshot giá, idempotency), chuyển trạng thái, lịch sử | Order, OrderItem, OrderStatusHistory | Đinh Văn Mạnh |
| `orders/state_machine.py` | Quy tắc chuyển trạng thái hợp lệ, kiểm tra quyền theo vai trò | Enum OrderStatus | Đinh Văn Mạnh |
| `reviews/` | Đánh giá món sau đơn hoàn tất, phân biệt với feedback gợi ý | Review | Phạm Hồng Thái |
| `search/` | Tìm món/quán theo text, lọc khoảng cách (Haversine), phạm vi phục vụ | Restaurant, MenuItem | Phạm Hồng Thái |
| `tracking/` | Ghi sự kiện: impression, click, add_to_cart, feedback, session; chống trùng event_id | RecommendationRequest, RecommendationImpression, InteractionEvent | Đỗ Đình Đức |
| `vendor/` | Endpoint riêng chủ quán: quản lý thực đơn, nhận/từ chối đơn, thống kê quán mình | — (dùng models từ restaurants, menu, orders) | Phạm Hồng Thái |
| `admin/` | Duyệt quán, quản lý tài khoản, danh mục món chuẩn, nhãn, chất lượng dữ liệu | — (dùng models từ các module khác) | Phạm Trọng Sang |

### C.6 Backend – AI (`src/backend/app/ai/`)

| Đường dẫn | Trách nhiệm | Phụ thuộc chính | Người phụ trách |
|:---|:---|:---|:---|
| `router.py` | POST `/recommendations/` → trả Top 5 + lý do | ai/service | Nguyễn Mạnh Đức |
| `schemas.py` | RecommendationRequest/Response, ReasonDetail, CandidateInfo | — | Nguyễn Mạnh Đức |
| `service.py` | Pipeline chính: gọi filter → scorer → diversifier → explainer | Tất cả sub-module AI | Nguyễn Mạnh Đức |
| `feature_encoder.py` | Mã hóa vector đặc trưng món (vùng miền, cay, nguyên liệu, chế biến) từ CanonicalDish và Preference | scikit-learn, models menu + preferences | Nguyễn Mạnh Đức |
| `candidate_filter.py` | Lọc cứng: món còn bán, quán nhận đơn, trong phạm vi, loại nguyên liệu cần tránh | models menu, restaurant | Nguyễn Mạnh Đức |
| `scorer.py` | Tính điểm: 0.70 × cosine_similarity + 0.20 × distance_score + 0.10 × feedback_score; chuẩn hóa 0–1; bỏ thành phần thiếu và chuẩn hóa lại | feature_encoder, Haversine | Nguyễn Mạnh Đức |
| `diversifier.py` | Đa dạng hóa: không trùng CanonicalDish, trải đều quán khi đủ ứng viên | — | Nguyễn Mạnh Đức |
| `explainer.py` | Sinh lý do dựa trên đặc trưng thật (vùng miền, cay, nguyên liệu, khoảng cách) | feature_encoder | Nguyễn Mạnh Đức |
| `baseline.py` | Baseline phổ biến: xếp hạng theo số đơn hoàn tất trên cùng tập ứng viên; thứ tự cố định khi thiếu lịch sử | models orders | Nguyễn Mạnh Đức |
| `config.py` | Trọng số cố định, phiên bản thuật toán, số ứng viên tối đa | — | Nguyễn Mạnh Đức |

### C.7 Backend – ETL (`src/backend/app/etl/`)

| Đường dẫn | Trách nhiệm | Phụ thuộc chính | Người phụ trách |
|:---|:---|:---|:---|
| `run_etl.py` | Entry point CLI: `python -m app.etl.run_etl`; chạy lặp an toàn (idempotent) | fact_builders, attribution | Phạm Trọng Sang |
| `attribution.py` | Quy thuộc click→order: cùng MenuItem, ≤30 phút, cùng session; loại đơn hủy/từ chối; đợi cửa sổ quan sát | InteractionEvent, Order | Phạm Trọng Sang |
| `fact_builders.py` | Xây dựng/cập nhật Fact_OrderItem, Fact_RecImpression, Fact_Session và dimensions | Tracking models, Order | Phạm Trọng Sang |
| `validation.py` | Đối soát: so khớp số đơn, số sự kiện giữa OLTP và bảng fact; báo lỗi chênh lệch | Fact tables, OLTP tables | Phạm Trọng Sang |

### C.8 Backend – Scripts & Tests

| Đường dẫn | Trách nhiệm | Phụ thuộc chính | Người phụ trách |
|:---|:---|:---|:---|
| `scripts/seed.py` | Nạp seed data từ `src/database/seed/` vào DB; gắn cờ `is_simulated=True` | Seed JSON files, models | Nguyễn Mạnh Đức |
| `scripts/load_vifoodrec.py` | Nhập ViFoodRec → CanonicalDish; loại trùng, bổ sung nhãn, giữ source_id | vifoodrec mapping | Nguyễn Mạnh Đức |
| `scripts/benchmark_recommendation.py` | Đo Precision@5, so sánh AI vs baseline, khoảng tin cậy, p95 latency | ai module, seed data | Nguyễn Mạnh Đức |
| `tests/test_auth.py` | Đăng ký, đăng nhập, token, phân quyền | auth module | Đinh Văn Mạnh |
| `tests/test_orders.py` | 30 ca giao dịch: tạo đơn, snapshot, gửi lặp, luồng trạng thái | orders module | Đinh Văn Mạnh |
| `tests/test_order_state_machine.py` | Chuyển trạng thái hợp lệ/không hợp lệ cho từng vai trò | state_machine | Đinh Văn Mạnh |
| `tests/test_recommendations.py` | Lọc cứng, loại nguyên liệu tránh, danh sách ngắn, thiếu ứng viên | ai module | Nguyễn Mạnh Đức |
| `tests/test_tracking.py` | Ghi sự kiện, chống trùng event_id, đúng loại | tracking module | Đỗ Đình Đức |
| `tests/test_vendor_access.py` | Chủ quán chỉ truy cập quán mình, không xem/sửa quán khác | vendor, auth | Phạm Hồng Thái |
| `tests/test_search.py` | Tìm kiếm, lọc khoảng cách, phạm vi phục vụ | search module | Phạm Hồng Thái |
| `tests/test_idempotency.py` | Gửi lặp tạo đơn không sinh đơn trùng | orders module | Đinh Văn Mạnh |
| `tests/test_constraints.py` | 100 ca ràng buộc: giá thay đổi, món hết, quán đóng, ngoài phạm vi | orders, menu, restaurants | Đinh Văn Mạnh |
| `tests/test_etl.py` | ETL idempotent, quy thuộc đúng, đối soát khớp | etl module | Phạm Trọng Sang |

### C.9 Frontend – Lõi (`src/frontend/src/`)

| Đường dẫn | Trách nhiệm | Phụ thuộc chính | Người phụ trách |
|:---|:---|:---|:---|
| `main.tsx` | Mount React app | App | Đỗ Đình Đức |
| `App.tsx` | Provider tree: Auth, Cart, Location | Contexts | Đỗ Đình Đức |
| `router.tsx` | Định tuyến theo vai trò, public/private routes | react-router-dom | Đỗ Đình Đức |
| `api/client.ts` | Axios instance, base URL, interceptor gắn token, xử lý lỗi chuẩn | — | Đỗ Đình Đức |
| `api/*.ts` | Hàm gọi API theo module, trả kiểu TypeScript | client.ts, types | Đỗ Đình Đức |
| `types/*.ts` | Interface/type cho request, response, entity | API_CONTRACT.md | Đỗ Đình Đức |
| `hooks/useAuth.ts` | Đăng nhập, đăng xuất, lưu token, lấy user hiện tại | AuthContext | Đỗ Đình Đức |
| `hooks/useLocation.ts` | Geolocation API, fallback nhập địa chỉ, xử lý lỗi Maps | LocationContext | Đỗ Đình Đức |
| `hooks/useCart.ts` | Giỏ hàng một quán: thêm/sửa/xóa, đổi quán thì cảnh báo | CartContext | Đỗ Đình Đức |
| `hooks/useTracking.ts` | Gửi sự kiện, queue offline, event_id duy nhất, chống trùng | api/tracking.ts | Đỗ Đình Đức |
| `hooks/useIdempotency.ts` | Sinh và lưu idempotency key, khóa nút gửi lặp | — | Đỗ Đình Đức |
| `contexts/AuthContext.tsx` | State user, token, role; persist localStorage | — | Đỗ Đình Đức |
| `contexts/CartContext.tsx` | State giỏ hàng, restaurant_id hiện tại | — | Đỗ Đình Đức |
| `contexts/LocationContext.tsx` | Tọa độ/địa chỉ hiện tại, trạng thái cấp quyền | — | Đỗ Đình Đức |

### C.10 Frontend – Components

| Nhóm | File chính | Trách nhiệm | Người phụ trách |
|:---|:---|:---|:---|
| `layout/` | AppShell, Navbar, Footer, RoleGuard | Khung chung, điều hướng, bảo vệ route theo role | Đỗ Đình Đức |
| `common/` | LoadingSpinner, EmptyState, ErrorBoundary, ErrorDisplay, ConfirmDialog | UI trạng thái tải, rỗng, lỗi; hộp thoại xác nhận | Đỗ Đình Đức |
| `map/` | MapView, LocationPicker, AddressFallback | Hiển thị bản đồ, chọn vị trí, nhập địa chỉ khi Maps lỗi | Đỗ Đình Đức |
| `menu/` | DishCard, MenuList, DishDetail | Hiển thị món, danh sách thực đơn, chi tiết món | Đỗ Đình Đức |
| `recommendation/` | RecommendationList, RecommendationCard, ReasonBadge, FeedbackButtons, NotPersonalized | Top 5 gợi ý, lý do, nút phản hồi, thông báo chưa cá nhân hóa | Đỗ Đình Đức |
| `cart/` | CartDrawer, CartItem, CheckoutForm | Giỏ hàng, thanh toán COD | Đỗ Đình Đức |
| `order/` | OrderCard, OrderTimeline, ReviewForm | Trạng thái đơn, timeline, đánh giá sau hoàn tất | Đỗ Đình Đức |
| `evaluation/` | BlindEvalForm | Đánh giá mù: hiện 2 danh sách xáo trộn, ẩn thuật toán, chấm điểm | Đỗ Đình Đức |

### C.11 Frontend – Pages

| Nhóm trang | File | Trách nhiệm | Người phụ trách |
|:---|:---|:---|:---|
| `auth/` | LoginPage, RegisterPage | Đăng nhập, đăng ký | Đỗ Đình Đức |
| `customer/` | HomePage, PreferencePage, SearchPage, RestaurantPage, DishDetailPage, CartPage, CheckoutPage, OrderListPage, OrderDetailPage, EvaluationPage | Toàn bộ luồng khách hàng | Đỗ Đình Đức |
| `vendor/` | DashboardPage, ProfilePage, MenuManagePage, IngredientPage, OrderManagePage, StatsPage | Toàn bộ luồng chủ quán | Phạm Trọng Sang |
| `admin/` | DashboardPage, RestaurantApprovalPage, DishCatalogPage, UserManagePage, DataQualityPage | Toàn bộ luồng admin | Phạm Trọng Sang |
| — | NotFoundPage | Trang 404 | Đỗ Đình Đức |

### C.12 Database (`src/database/`)

| Đường dẫn | Trách nhiệm | Phụ thuộc chính | Người phụ trách |
|:---|:---|:---|:---|
| `seed/README.md` | Giải thích cấu trúc seed, cờ `is_simulated`, nguồn gốc | — | Nguyễn Mạnh Đức |
| `seed/*.json` | Dữ liệu mẫu: 100 món chuẩn, 20 quán, 200 menu items, 30 users, 100 đơn | ViFoodRec | Nguyễn Mạnh Đức |
| `vifoodrec/README.md` | Quy trình nhập, loại trùng, bổ sung nhãn | ViFoodRec repo | Nguyễn Mạnh Đức |
| `vifoodrec/mapping.json` | Ánh xạ ID gốc ViFoodRec → CanonicalDish ID, nhãn bổ sung | — | Nguyễn Mạnh Đức |
| `bi/views_fact_*.sql` | Định nghĩa views/materialized views cho 3 bảng fact | OLTP schema | Phạm Trọng Sang |
| `bi/views_dimensions.sql` | Dim_Date, Dim_User (ẩn danh), Dim_Restaurant, Dim_Dish | OLTP schema | Phạm Trọng Sang |
| `bi/kpi_queries.sql` | Truy vấn CTR, tỷ lệ phiên đặt từ gợi ý, tỷ lệ hoàn tất | Fact views | Phạm Trọng Sang |
| `bi/reconciliation.sql` | Đối soát: đếm đơn, đếm sự kiện OLTP vs fact | Fact + OLTP | Phạm Trọng Sang |
| `bi/data_quality_checks.sql` | Kiểm tra null, orphan, trùng, khoảng thời gian bất thường | All tables | Phạm Trọng Sang |
| `powerbi/README.md` | Hướng dẫn kết nối PostgreSQL, cập nhật data source | — | Phạm Trọng Sang |
| `powerbi/Vi_Viet_Dashboard.pbix` | File Power BI (nhị phân, tạo bằng công cụ) | BI views | Phạm Trọng Sang |
| `powerbi/dax_measures.md` | Công thức DAX cho các KPI | — | Phạm Trọng Sang |
| `powerbi/dashboard_guide.md` | Mô tả từng trang dashboard, ý nghĩa, cách đọc | — | Phạm Trọng Sang |

---

## D. Bảng đối chiếu yêu cầu đề cương

| # | Yêu cầu đề cương | Frontend | Backend | Bảng dữ liệu | Kiểm thử |
|:-:|:---|:---|:---|:---|:---|
| 1 | Đăng ký, đăng nhập, phiên | LoginPage, RegisterPage, AuthContext, useAuth | auth/router, auth/service | User | test_auth |
| 2 | Phân quyền 3 vai trò | RoleGuard, router.tsx | auth/dependencies (require_role) | User.role | test_auth, test_vendor_access |
| 3 | Khai báo khẩu vị 5 câu | PreferencePage | preferences/router, preferences/service | Preference | test_recommendations |
| 4 | Chọn vị trí / nhập địa chỉ | LocationPicker, AddressFallback, useLocation | search/service (Haversine) | — (client-side) | Manual + test_search |
| 5 | Tìm món/quán | SearchPage | search/router, search/service | Restaurant, MenuItem | test_search |
| 6 | Top 5 gợi ý + lý do | RecommendationList, ReasonBadge | ai/router, ai/service | RecommendationRequest, RecommendationImpression | test_recommendations |
| 7 | Phản hồi gợi ý | FeedbackButtons | tracking/router | InteractionEvent (type=feedback) | test_tracking |
| 8 | Danh sách chưa cá nhân hóa | NotPersonalized, RecommendationList | ai/baseline | Cùng pipeline, không dùng Preference | test_recommendations |
| 9 | Giỏ hàng 1 quán | CartDrawer, CartItem, useCart | — (client state) | — | Manual |
| 10 | Đặt đơn COD, snapshot giá | CheckoutPage, useIdempotency | orders/router, orders/service | Order, OrderItem (snapshot_price, snapshot_name) | test_orders, test_idempotency |
| 11 | Idempotency gửi lặp | useIdempotency (khóa nút + key) | orders/service (idempotency_key unique) | Order.idempotency_key | test_idempotency |
| 12 | Luồng trạng thái đơn | OrderTimeline | orders/state_machine | OrderStatusHistory | test_order_state_machine |
| 13 | Hủy đơn (khách) / Từ chối (quán) | OrderDetailPage, OrderManagePage | orders/state_machine (CANCELLED, REJECTED) | OrderStatusHistory | test_order_state_machine |
| 14 | Đánh giá món sau hoàn tất | ReviewForm | reviews/router | Review | test_orders |
| 15 | Quản lý quán, giờ mở, phạm vi | vendor/ProfilePage | restaurants/router, vendor/router | Restaurant, RestaurantMembership | test_vendor_access |
| 16 | Quản lý thực đơn, nguyên liệu | vendor/MenuManagePage, IngredientPage | menu/router, vendor/router | MenuItem, Ingredient, MenuItemIngredient | test_vendor_access |
| 17 | Quán chỉ xem dữ liệu mình | vendor/* pages | auth/dependencies (require_vendor_owner) | RestaurantMembership | test_vendor_access |
| 18 | Admin duyệt quán | admin/RestaurantApprovalPage | admin/router | Restaurant.status | test_auth |
| 19 | Admin quản lý món chuẩn, nhãn | admin/DishCatalogPage | admin/router | CanonicalDish | — |
| 20 | Tracking impression/click/cart | useTracking | tracking/router, tracking/service | InteractionEvent, RecommendationImpression | test_tracking |
| 21 | Session tracking | useTracking (session_id) | tracking/service | InteractionEvent.session_id | test_tracking |
| 22 | Lọc cứng: món bán, quán nhận, phạm vi, nguyên liệu tránh | — (backend) | ai/candidate_filter | MenuItem.is_available, Restaurant.accepting_orders | test_recommendations, test_constraints |
| 23 | Điểm = 0.70×sim + 0.20×dist + 0.10×fb | — (backend) | ai/scorer | — | test_recommendations |
| 24 | Đa dạng hóa Top 5 | — (backend) | ai/diversifier | — | test_recommendations |
| 25 | Baseline phổ biến | — (backend) | ai/baseline | Order (count) | test_recommendations |
| 26 | Đánh giá mù AI vs baseline | EvaluationPage, BlindEvalForm | ai/router (cả 2 danh sách xáo trộn) | — | benchmark_recommendation |
| 27 | Precision@5, khoảng tin cậy | — | scripts/benchmark_recommendation | — | Script output |
| 28 | p95 < 2s, 10 người đồng thời | — | scripts/benchmark_recommendation (locust/ab) | — | Script output |
| 29 | ETL idempotent | — | etl/run_etl, fact_builders | Fact_OrderItem, Fact_RecImpression, Fact_Session | test_etl |
| 30 | Quy thuộc click→order 30 phút | — | etl/attribution | Fact_OrderItem.attributed_impression_id | test_etl |
| 31 | Đối soát BI 100% | — | etl/validation | OLTP vs Fact | test_etl |
| 32 | Dashboard phễu hiển thị–nhấp–đặt | — (Power BI) | — | Fact_RecImpression, Fact_OrderItem | Reconciliation |
| 33 | CanonicalDish vs MenuItem | — | menu/models | CanonicalDish, MenuItem | test_constraints |
| 34 | Dữ liệu mô phỏng có cờ | — | scripts/seed | *.is_simulated | Seed README |
| 35 | 100 ca ràng buộc | — | — | — | test_constraints |
| 36 | 30 ca giao dịch 100% | — | — | — | test_orders |

---

## E. Hợp đồng cần chốt trước khi lập trình song song

### E.1 Endpoint và schema dùng chung

```
Prefix: /api/v1/

Auth:
  POST /auth/register        → { email, password, full_name, role }
  POST /auth/login            → { email, password } → { access_token, token_type, user }
  GET  /auth/me               → UserOut

Customer:
  GET/PUT  /preferences/      → Preference (5 câu hỏi)
  GET      /search/dishes?q=&lat=&lng=&radius=   → PaginatedResult<DishSearchResult>
  GET      /search/restaurants?q=&lat=&lng=       → PaginatedResult<RestaurantSearchResult>
  POST     /recommendations/  → { lat, lng } → RecommendationResponse
  GET      /restaurants/{id}  → RestaurantDetail
  GET      /restaurants/{id}/menu  → MenuItem[]
  GET      /menu-items/{id}   → MenuItemDetail
  POST     /orders/           → { items, restaurant_id, delivery_address, idempotency_key }
  GET      /orders/           → Order[] (của user hiện tại)
  GET      /orders/{id}       → OrderDetail
  PATCH    /orders/{id}/cancel
  POST     /orders/{id}/review  → { menu_item_id, rating, comment }
  POST     /tracking/events   → { events: InteractionEvent[] }

Vendor (prefix /vendor):
  GET      /vendor/restaurant              → RestaurantDetail (quán của mình)
  PUT      /vendor/restaurant              → cập nhật hồ sơ
  GET/POST /vendor/menu-items              → CRUD thực đơn
  PUT      /vendor/menu-items/{id}
  DELETE   /vendor/menu-items/{id}
  GET      /vendor/orders                  → đơn hàng quán mình
  PATCH    /vendor/orders/{id}/confirm
  PATCH    /vendor/orders/{id}/reject      → { reason }
  PATCH    /vendor/orders/{id}/preparing
  PATCH    /vendor/orders/{id}/delivering
  PATCH    /vendor/orders/{id}/complete
  GET      /vendor/stats                   → thống kê cơ bản

Admin (prefix /admin):
  GET      /admin/restaurants              → tất cả quán
  PATCH    /admin/restaurants/{id}/approve
  PATCH    /admin/restaurants/{id}/suspend
  GET/POST /admin/canonical-dishes         → CRUD món chuẩn
  GET      /admin/users                    → danh sách tài khoản
  PATCH    /admin/users/{id}/role
  GET      /admin/data-quality             → báo cáo chất lượng
```

### E.2 Vai trò và trạng thái đơn

```python
class UserRole(str, Enum):
    CUSTOMER = "customer"
    VENDOR   = "vendor"
    ADMIN    = "admin"

class OrderStatus(str, Enum):
    PENDING    = "pending"
    CONFIRMED  = "confirmed"
    PREPARING  = "preparing"
    DELIVERING = "delivering"
    COMPLETED  = "completed"
    CANCELLED  = "cancelled"   # Khách hủy từ PENDING
    REJECTED   = "rejected"    # Chủ quán từ chối từ PENDING

# Chuyển trạng thái hợp lệ:
TRANSITIONS = {
    "pending":    {"confirmed": "vendor", "rejected": "vendor", "cancelled": "customer"},
    "confirmed":  {"preparing": "vendor"},
    "preparing":  {"delivering": "vendor"},
    "delivering": {"completed": "vendor"},
}
```

### E.3 Định dạng lỗi chuẩn

```json
{
  "error": {
    "code": "ORDER_ITEM_UNAVAILABLE",
    "message": "Món 'Phở bò tái' hiện không còn bán tại quán này.",
    "details": { "menu_item_id": 42, "field": "is_available" }
  }
}
```
HTTP status: 400 (validation), 401 (chưa đăng nhập), 403 (không đủ quyền), 404 (không tìm thấy), 409 (trùng idempotency_key / trạng thái không hợp lệ), 422 (Pydantic validation).

### E.4 Idempotency key

- Client sinh UUID v4, lưu vào `localStorage` theo session, gửi trong body `POST /orders/`.
- Backend: cột `Order.idempotency_key` UNIQUE; nếu đã tồn tại → trả lại đơn cũ, HTTP 200.
- Hết hạn: idempotency key hợp lệ trong 24 giờ kể từ tạo.

### E.5 Event ID, Session ID, Recommendation Request ID

```typescript
// Frontend sinh:
event_id:    crypto.randomUUID()   // duy nhất mỗi sự kiện
session_id:  crypto.randomUUID()   // sinh khi mở app/tab, lưu sessionStorage

// Backend sinh:
request_id:  uuid4()               // mỗi lần gọi /recommendations/
```

| Trường | Nguồn | Mục đích |
|:---|:---|:---|
| `event_id` | Frontend | Chống gửi trùng sự kiện |
| `session_id` | Frontend | Nhóm sự kiện theo phiên |
| `request_id` | Backend | Liên kết impression với request gợi ý |
| `algorithm_version` | Backend (ai/config) | Gắn vào impression, dùng cho BI và đánh giá |

### E.6 Đầu vào/đầu ra gợi ý

**Request:**
```json
{
  "latitude": 21.0285,
  "longitude": 105.8542,
  "session_id": "uuid"
}
```

**Response (đủ ứng viên):**
```json
{
  "request_id": "uuid",
  "algorithm_version": "content_v1",
  "is_personalized": true,
  "items": [
    {
      "rank": 1,
      "menu_item_id": 42,
      "canonical_dish_id": 7,
      "dish_name": "Phở bò tái",
      "restaurant_name": "Phở Thìn",
      "price": 55000,
      "distance_km": 1.2,
      "score": 0.87,
      "reasons": [
        "Phù hợp sở thích miền Bắc của bạn",
        "Cách bạn 1.2 km"
      ]
    }
  ],
  "total_candidates_after_filter": 23,
  "note": null
}
```

**Response (thiếu ứng viên):**
```json
{
  "request_id": "uuid",
  "algorithm_version": "content_v1",
  "is_personalized": true,
  "items": [ /* < 5 items */ ],
  "total_candidates_after_filter": 2,
  "note": "Chỉ có 2 món phù hợp điều kiện lọc. Hãy thử mở rộng bán kính tìm kiếm."
}
```

**Response (bỏ qua khẩu vị):**
```json
{
  "request_id": "uuid",
  "algorithm_version": "explore_v1",
  "is_personalized": false,
  "items": [ /* danh sách khám phá */ ],
  "total_candidates_after_filter": 15,
  "note": "Danh sách khám phá – chưa được cá nhân hóa. Khai báo khẩu vị để nhận gợi ý phù hợp hơn."
}
```

### E.7 Quy tắc quy thuộc và định nghĩa KPI

| KPI | Định nghĩa | Lưu ý |
|:---|:---|:---|
| **CTR gợi ý** | Số lượt hiển thị có ≥1 click ÷ tổng lượt hiển thị hợp lệ | Chỉ đếm impression thật sự hiển thị |
| **Tỷ lệ phiên đặt từ gợi ý** | Phiên có đơn hợp lệ được quy thuộc gợi ý ÷ phiên có hiển thị gợi ý | Loại đơn CANCELLED/REJECTED |
| **Quy thuộc** | Click cùng `menu_item_id`, gần nhất trước đặt, ≤30 phút, cùng `session_id` | Đợi cửa sổ quan sát hết trước khi chốt |
| **Precision@5** | Số món "phù hợp" trong Top 5 ÷ min(5, số ứng viên trả về) | Đánh giá bởi người dùng (mù) |
| **Tỷ lệ hoàn tất** | Đơn COMPLETED ÷ tổng đơn (trừ CANCELLED trước CONFIRMED) | — |

---

## F. Thứ tự tạo file theo phụ thuộc

### Phase 0 – Nền tảng (Tuần 1–2) ⬅ **Bắt buộc MVP**

```
1. docs/NGUON_DU_LIEU.md, KE_HOACH_THUC_HIEN.md, CHECKLIST_NOP_BAI.md
   (tài liệu thiếu, không phụ thuộc kỹ thuật)

2. .env.example, docker-compose.yml, Makefile
   (hạ tầng chạy local)

3. src/backend/pyproject.toml, requirements.txt, Dockerfile, alembic.ini
   src/backend/app/__init__, main, config, database, exceptions, dependencies, middleware
   (backend skeleton – chạy được `uvicorn app.main:app`)

4. src/frontend/package.json, tsconfig, vite.config, index.html, Dockerfile, .env.example
   src/frontend/src/main.tsx, App.tsx, router.tsx, vite-env.d.ts
   (frontend skeleton – chạy được `npm run dev`)
```

### Phase 1 – Auth & Models (Tuần 2–3) ⬅ **Bắt buộc MVP**

```
5. src/backend/app/users/models.py          → User model
   src/backend/app/preferences/models.py    → Preference
   src/backend/app/restaurants/models.py    → Restaurant, RestaurantMembership
   src/backend/app/menu/models.py           → CanonicalDish, MenuItem, Ingredient, MenuItemIngredient
   src/backend/app/orders/models.py         → Order, OrderItem, OrderStatusHistory
   src/backend/app/reviews/models.py        → Review
   src/backend/app/tracking/models.py       → RecommendationRequest, RecommendationImpression, InteractionEvent

6. src/backend/alembic/ + versions/001_initial_schema.py
   (migration tạo toàn bộ bảng)

7. docs/ERD.md, TU_DIEN_DU_LIEU.md
   (vẽ từ models vừa tạo)

8. src/backend/app/auth/*                   → đăng ký, đăng nhập, JWT
   src/frontend/src/contexts/AuthContext.tsx
   src/frontend/src/hooks/useAuth.ts
   src/frontend/src/api/client.ts, auth.ts
   src/frontend/src/pages/auth/*
   src/frontend/src/components/layout/*

9. tests/test_auth.py
```

### Phase 2 – Nghiệp vụ giao dịch (Tuần 3–5) ⬅ **Bắt buộc MVP**

```
10. src/backend/app/restaurants/*, menu/*, search/*
    src/backend/app/vendor/*, admin/*
    src/backend/app/orders/* (bao gồm state_machine.py)
    src/backend/app/reviews/*

11. docs/API_CONTRACT.md
    src/frontend/src/types/*, api/*

12. src/frontend/src/pages/customer/* (trừ EvaluationPage)
    src/frontend/src/pages/vendor/*
    src/frontend/src/pages/admin/*
    src/frontend/src/components/menu/*, cart/*, order/*, map/*, common/*
    src/frontend/src/hooks/useCart, useLocation, useIdempotency
    src/frontend/src/contexts/CartContext, LocationContext

13. tests/test_orders, test_order_state_machine, test_vendor_access,
    test_search, test_idempotency, test_constraints
```

### Phase 3 – AI & Tracking (Tuần 4–6) ⬅ **Bắt buộc MVP**

```
14. src/database/vifoodrec/*, seed/*
    src/backend/scripts/load_vifoodrec.py, seed.py

15. src/backend/app/ai/*
    src/backend/app/tracking/*
    docs/EVENT_CATALOG.md

16. src/frontend/src/hooks/useTracking.ts
    src/frontend/src/components/recommendation/*
    src/frontend/src/pages/customer/EvaluationPage.tsx
    src/frontend/src/components/evaluation/BlindEvalForm.tsx

17. tests/test_recommendations, test_tracking
```

### Phase 4 – BI & Đánh giá (Tuần 6–7) ⬅ **Bắt buộc MVP**

```
18. src/backend/app/etl/*
19. src/database/bi/*
20. src/database/powerbi/* (README, dax_measures, dashboard_guide; .pbix tạo bằng Power BI)
21. src/backend/scripts/benchmark_recommendation.py
22. tests/test_etl
```

### Phase 5 – Hoàn thiện (Tuần 7–8) ⬅ **Bắt buộc MVP**

```
23. docs/KIEN_TRUC.md (cập nhật theo thực tế)
    docs/HUONG_DAN_CAI_DAT.md (kiểm chứng từ Docker)
    docs/HUONG_DAN_DEMO.md
    docs/CHECKLIST_NOP_BAI.md (cập nhật)
24. README.md, danhsachnhom.md (cập nhật tỷ lệ đóng góp)
25. Toàn bộ test chạy xanh, reconciliation BI pass
```

### Phần mở rộng (có thể hoãn)

| Tính năng | File liên quan | Lý do hoãn |
|:---|:---|:---|
| Chatbot gợi ý | — | Ngoài phạm vi đề cương |
| Lọc cộng tác (collaborative filtering) | ai/collaborative.py 📌 | Cần đủ dữ liệu tương tác |
| Thanh toán trực tuyến | orders/payment.py 📌 | Yêu cầu tích hợp cổng thanh toán |
| Điều phối tài xế | — | Ngoài phạm vi |
| Công thức tự nấu | — | Ngoài phạm vi |
| CI/CD pipeline | .github/workflows/ 📌 | Tiện nhưng không bắt buộc cho MVP |
| Thông báo realtime (WebSocket) | — 📌 | Có thể dùng polling trong MVP |

---

## Tổng kết phân công theo người

| Thành viên | Module chính | Số file ước tính |
|:---|:---|:---|
| **Đinh Văn Mạnh** | Backend lõi, auth, orders, state_machine, DevOps, docs tổng hợp | ~35 |
| **Đỗ Đình Đức** | Frontend toàn bộ (customer pages, components, hooks, tracking client) | ~55 |
| **Phạm Hồng Thái** | Backend restaurants, menu, search, reviews, vendor endpoints, API docs | ~25 |
| **Nguyễn Mạnh Đức** | AI module, ViFoodRec xử lý, seed data, preferences, benchmark | ~25 |
| **Phạm Trọng Sang** | Frontend vendor/admin pages, ETL, BI views, Power BI, DB docs | ~25 |

> [!TIP]
> Đỗ Đình Đức có nhiều file frontend nhất nhưng nhiều component có cấu trúc lặp (CRUD pages). Phạm Trọng Sang phụ trách cả frontend vendor/admin lẫn BI để hiểu end-to-end luồng dữ liệu từ giao diện → ETL → dashboard.
