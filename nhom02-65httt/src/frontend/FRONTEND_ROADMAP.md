# FRONTEND ROADMAP & KHUYẾN NGHỊ CHUYÊN NGHIỆP

**Dự án:** ERP Smart Pricing đa kênh (ESP-ERP-001)
**Phạm vi:** `frontend/` (React 18 + Vite 6 + Tailwind v4 + TypeScript) — **chỉ frontend, chưa có backend**.
**Căn cứ:** `ERP_Smart_Pricing_SPEC/UI_SPEC.md`, `SPEC.md`, `API_SPEC.md`, `BUSINESS_RULES.md`, `AI_PRICING.md`, `BI_SPEC.md`
**Trạng thái:** typecheck + build pass; mock API chạy được toàn bộ luồng chính; **chưa có test tự động**. Toàn bộ dữ liệu đi qua `src/mocks/`, nên các mục đánh dấu **(cần backend)** là để dành, không phải việc phải làm bây giờ.

Tài liệu này chia làm 4 nhóm: (A) việc cần làm để "ra nghề", (B) tính năng nên bổ sung, (C) việc làm đẹp, (D) kiến trúc khi nối backend thật. Cuối tài liệu có lộ trình và checklist nghiệm thu.

> Nguyên tắc bất di bất dịch: **không đổi tên field/enum/route** đã chốt trong đặc tả; **không trình bày dữ liệu mock như live**; **không thêm tính năng vượt quá quyền hạn backend**.

---

## 0. Phạm vi hiện tại: chỉ frontend

Một đồ án frontend-only **không** bị trừ điểm vì thiếu backend, nhưng bị trừ nếu: dữ liệu đổi mỗi lần reload, nút bấm không phản hồi, hoặc tuyên bố những thứ chưa tồn tại. Cách trình bày đúng:

1. **Nói rõ ranh giới ngay trong README/demo:** “Frontend hoàn chỉnh theo `UI_SPEC`; toàn bộ API được mô phỏng trong `src/mocks/api.ts` với cùng envelope như `API_SPEC`; chưa có backend.”
2. **Mock phải hành xử như backend thật:** delay, lỗi, phân trang, validate, idempotent-ish, dữ liệu **deterministic** (đã đúng — không dùng `Math.random`).
3. **Không hứa tính năng live:** mọi thao tác giá là `SIMULATED`, đã có nhãn.
4. **Bù lại bằng chiều sâu UI:** các màn hình “khó” (rule builder, import wizard, approval, execution log) làm được hoàn toàn ở client.

### Việc chỉ frontend làm được ngay (không cần một dòng backend)

| # | Việc | Vì sao đáng làm | Công sức |
|---|---|---|---|
| F1 | **Lưu state mock vào `localStorage`** + nút “Khôi phục dữ liệu demo” | Sửa đúng điểm yếu lớn nhất hiện tại: F5 là mất đề xuất vừa chạy. Rất rẻ, tác động rất lớn khi demo | S |
| F2 | **Rule builder + preview tại client** (dùng lại đúng công thức floor trong `mocks/api.ts`) | Lấp UI-10 — phần đặc sản của đề tài; preview tính tại chỗ nên không cần máy chủ | M |
| F3 | **Import CSV bằng `FileReader`**: chọn file → map cột → preview → validate → merge vào store | Lấp UI-03/UI-07 và UAT số 2. Toàn bộ xử lý file là client-side | M |
| F4 | **Điều chỉnh tồn kho + lý do + lịch sử biến động** (ghi vào store, sinh audit entry tại client) | Lấp UI-05; chứng minh hiểu `available = on_hand − reserved` và ràng buộc lý do | S |
| F5 | **Trang chi tiết nhà cung cấp** (SKU theo NCC, lịch sử báo giá dựng từ seed data) | Lấp UI-04; giải thích được nguồn gốc landed cost | M |
| F6 | **Competitor price trend + dải min/median/max** từ các observation sẵn có | Lấp UI-07 phần chart; không cần dữ liệu mới | S |
| F7 | **Command palette Ctrl/Cmd+K** + lưu bộ lọc vào URL | Cảm giác “tool thật”, chia sẻ được link trạng thái | S |
| F8 | **Test với mock** (Vitest + RTL + MSW dùng chính handler mock) | Chứng minh chất lượng mà không cần server | M |

> F1 + F8 là hai thứ “ăn điểm” cao nhất trên mỗi giờ bỏ ra khi chỉ có frontend.

### Không nên làm khi chưa có backend

- Không gọi `fetch` tới endpoint chưa tồn tại rồi hiện lỗi mạng — trông như app hỏng.
- Không tự nhận “đã tích hợp Shopee/TikTok” khi chỉ có adapter giả lập.
- Không đưa JWT/refresh flow nửa vời; giữ session demo và ghi rõ trong README.
- Không thêm thư viện state manager/caching lớn cho một app chỉ đọc mock.
- Không nhồi thêm màn hình trang trí; ưu tiên làm sâu 5 luồng UAT trong `IMPLEMENTATION_PLAN.md` §6.

---

## 0.1 Hiện trạng (baseline để không làm lại)

| Hạng mục | Trạng thái |
|---|---|
| Design tokens, app shell 248/72px, header 64px | Đạt UI_SPEC §1–2 |
| Format VND / % / `Asia/Ho_Chi_Minh` / null = `—` | Đạt §7, tập trung ở `lib/format.ts` |
| Bảng: sort, `aria-sort`, caption, pagination | Đạt §6 |
| Trạng thái loading / empty / error / forbidden | Đạt §11 (đã tách refresh loading) |
| RBAC theo ma trận §3.2 | Đạt (UI gate; backend vẫn phải kiểm tra) |
| Chạy định giá end-to-end (floor, clamp, NO_SAFE_PRICE) | Có, chạy bằng rule-based deterministic |
| Trang chi tiết sản phẩm 5 tab, giá vốn, mapping listing, cấu hình phí, lịch sử chạy | Có |
| Biểu đồ có legend + bảng sr-only | Có |
| Test tự động | **Chưa có (0 file)** |

**Còn thiếu so với đặc tả:** rule builder (UI-10), wizard import CSV (UI-03/07), điều chỉnh tồn kho có lý do (UI-05), trang chi tiết nhà cung cấp (UI-04), competitor price trend + min/median/max (UI-07), supplier cost trend + landed cost chart (BI_SPEC §5), approval latency + rule impact (BI_SPEC §6).

---

## A. Việc cần làm để bài "chuyên nghiệp"

Đây là những thứ giảng viên/hội đồng và team backend đánh giá cao hơn mọi animation đẹp.

### A1. Test tự động (ưu tiên số 1) — S/M
Đặc tả yêu cầu UI test (`SPEC.md` §11) và DoD yêu cầu test (`IMPLEMENTATION_PLAN.md` §5). Hiện tại chưa có gì.

Tối thiểu nên có:
- **Unit**: `lib/format.ts` (null vs 0, làm tròn VND, timezone), `lib/rbac.ts` (ma trận quyền), công thức floor trong mock (biên `1-f-m <= 0`).
- **Component**: `DataTable` (sort + `aria-sort`), `Modal` (Escape, focus trap), form validation login.
- **Integration (MSW)**: chạy định giá → xuất hiện đề xuất; approve bị chặn khi hết hạn; retry bị chặn ở lần thứ 3.

Công cụ gợi ý: Vitest + React Testing Library + MSW (đều chạy trong Vite, không cần thêm bundler). Viết 12–15 test là đủ chứng minh văn hoá test, không cần coverage 80%.

**Tiêu chí xong:** `npm test` chạy trong CI, fail nếu test fail.

### A2. Xử lý lỗi theo API contract — S
Hiện lỗi đang là `Error.message` thô. Khi nối `API_SPEC` §3 cần map `code` → thông điệp tiếng Việt và hành động:

| `code` | UI nên làm |
|---|---|
| `VALIDATION_ERROR` | Gắn lỗi vào từng field qua `details[]` |
| `FORBIDDEN` | Hiện `Forbidden`, không phải "lỗi hệ thống" |
| `CONFLICT` | Giải thích trạng thái đã đổi, cho tải lại |
| `RATE_LIMITED` | Đếm ngược + disable nút submit |
| `PROVIDER_UNAVAILABLE` | Phân biệt với lỗi nội bộ, gợi ý chế độ SIMULATION |

Thêm **ErrorBoundary** ở cấp route để một component lỗi không trắng cả app (hiện chưa có).

### A3. Tách lớp API thật khỏi mock — S/M **(cần backend, có thể chuẩn bị trước)**
`mocks/api.ts` đang là "backend giả" rất tốt cho demo. Để chuyển sang FastAPI chỉ nên sửa **một file**:
1. Tạo `lib/http.ts` (base URL từ `import.meta.env.VITE_API_BASE_URL`, gắn Bearer, parse envelope `{data, meta}` / `{error}`).
2. Khai báo interface `PricingApi` với đúng các hàm đang dùng.
3. `mocks/api.ts` và `api/http.ts` cùng implement interface đó; chọn bằng biến môi trường.

Điều này chứng minh được "API contract là ranh giới" (`AI_AGENT_GUIDE` §2) thay vì nói suông.

**Lưu ý contract:** tiền trong `API_SPEC` là **decimal string**, UI đang dùng `number`. Khi nối thật phải parse sang string/Decimal ở lớp adapter, không `Number()` trực tiếp để tránh sai số.

### A4. Chất lượng code & CI — S
- ESLint (flat config) + Prettier + `tsc --noEmit` trong CI.
- `npm run build` phải chạy trong CI, không chỉ trên máy cá nhân.
- Cấm `console.log` sót lại, cấm `any` ngầm định (đã bật `strict` — giữ nguyên).
- Đặt tên file/route theo đúng sitemap; route mới phải cập nhật `UI_SPEC.md` cùng PR (quy tắc quản lý thay đổi trong README).

### A5. Accessibility như một tiêu chí, không phải phụ lục — S
Đã có skip-link, focus-visible, `aria-sort`, bảng sr-only cho chart. Nên thêm:
- `axe-core` chạy trong test (hoặc `@axe-core/playwright` cho 3 route chính).
- Bàn phím: kiểm tra toàn bộ luồng duyệt đề xuất chỉ bằng Tab/Enter/Escape.
- Không dùng màu làm tín hiệu duy nhất (đã đúng ở freshness/outlier).
- Đảm bảo contrast ≥ 4.5:1 cho text 12px — `text-muted #667085` trên `#F9FAFB` đang sát ngưỡng, nên đo bằng công cụ.

### A6. Hiệu năng có số đo — S/M
- Bundle hiện tại: `charts` 406 kB (gzip 111 kB), `index` 473 kB (gzip 103 kB). Recharts chiếm phần lớn.
- Việc nên làm: `React.lazy` theo route (3 trang BI + pricing tách chunk), để màn Tổng quan không tải cả Recharts.
- Bảng > 200 dòng: virtualization (`@tanstack/react-virtual`) thay vì render hết.
- Đo bằng Lighthouse trên build tĩnh, ghi lại số trước/sau vào PR (đừng nói "nhanh hơn" mà không có số).

### A7. Quan sát lỗi & phân tích — S **(cần backend/triển khai)**
Với đồ án, có thể bỏ qua. Nếu demo public, nên có một lớp error tracking + một lớp analytics sự kiện tối thiểu (`pricing_run_submitted`, `recommendation_approved`, `simulation_executed`) để chứng minh "sản phẩm có đo lường". Chọn dịch vụ theo tiêu chí: free tier, không gửi dữ liệu giá/PII lên ngoài, hỗ trợ sourcemap. **Không đưa API key vào bundle** — chỉ dùng qua server hoặc DSN công khai đúng thiết kế.

### A8. Auth đúng chuẩn khi rời demo — M **(cần backend)**
`localStorage` hiện chỉ để demo (`AuthContext` đã ghi chú). Khi có backend:
- Access token ngắn hạn + refresh cookie `httpOnly; Secure; SameSite`.
- Không render dữ liệu trước khi `GET /auth/me` trả về (tránh nháy giao diện sai quyền).
- Xử lý 401 toàn cục: logout + redirect kèm `state.from`.
- Ma trận quyền phải có **test đối chiếu với backend**, đừng tin UI gate.

---

## B. Tính năng nên bổ sung (theo giá trị nghiệp vụ)

Xếp theo "đáng làm nhất cho một bài ERP định giá".

### B1. Rule builder có preview & conflict — L
`UI-10` yêu cầu form đầy đủ: name, type, scope, priority, conditions, action, start/end, max change %, min margin, approval policy, enabled + **preview SKU bị ảnh hưởng** + **rule thắng khi xung đột**.
Hiện có bảng rule, phát hiện xung đột và bật/tắt; chưa có form.
Giá trị: đây là phần "đặc sản" của đề tài (Flash Sale / Skimming / Clearance / Competitor Match / Margin Guard). Không có nó, demo chỉ dừng ở "xem rule".
Gợi ý: form dạng drawer 2 cột, cột phải là preview realtime (gọi `POST /automation/preview`).

### B2. Import CSV có wizard 4 bước — M
`FR-006`, `UI-07`: upload → map cột → preview/validate → confirm. Cần: bảng preview lỗi theo dòng, tải file lỗi, chặn file > giới hạn, chống CSV injection khi export.
Giá trị: đây là luồng UAT số 2 mà nhóm phải demo được.

### B3. Điều chỉnh tồn kho có lý do — S/M
`UI-05`: `POST /inventory/adjustments` bắt buộc `reason`, hiển thị lịch sử biến động. Hiện chỉ xem tồn.
Thêm modal 3 field (SKU, delta, lý do) + bảng movement là đủ.

### B4. Chi tiết nhà cung cấp + lịch sử báo giá — M
`UI-04`, `FR-004`: danh sách SKU theo NCC, lịch sử giá mua theo `valid_from/valid_to`, cảnh báo giá vốn hết hiệu lực (BR-003).
Đây là dữ liệu đầu vào trực tiếp của price floor — thiếu nó, "giá sàn" khó giải thích trước hội đồng.

### B5. Competitor intelligence sâu hơn — M
`UI-07`: trend nhiều đường theo ngày, dải min/median/max, price gap dạng diverging bar. Hiện có bảng quan sát + histogram gap ở BI.
Nên thêm: badge "stale" ngay trên chart, tooltip hiển thị nguồn + confidence.

### B6. BI: landed cost vs floor, supplier cost trend — M
`BI_SPEC` §5 yêu cầu; hiện thiếu. Đây là chart kể câu chuyện "vì sao không thể giảm giá thêm" — rất mạnh khi bảo vệ đồ án.

### B7. Approval latency & rule impact — M
`BI_SPEC` §6. Cần backend trả `submitted_at/approved_at` và `rule_id` trên execution. Frontend chỉ hiển thị — nhưng nên đặt trước "khung" để backend biết cần trả gì.

### B8. Bulk actions & saved views — S/M
Analyst thật làm việc theo lô: chọn nhiều dòng → "Chạy định giá", "Gửi duyệt", "Xuất CSV". Kèm lưu bộ lọc vào URL để chia sẻ link (`?status=PENDING&channel=shopee`).
Đây là chi tiết khiến UI "giống tool thật" hơn "trang bài tập".

### B9. Command palette (Ctrl/Cmd+K) — S
Nhảy nhanh tới SKU/đề xuất/route. Rất rẻ để làm (dữ liệu đã có), tạo ấn tượng mạnh khi demo, và thay cho ô search hiện chỉ tìm sản phẩm.

### B10. Demo reset & dữ liệu có "mạch" — S
Hiện state mock nằm trong RAM, reload là mất đề xuất vừa tạo. Nên: nút "Khôi phục dữ liệu demo" + ghi rõ "thay đổi chỉ tồn tại trong phiên". Tránh cảnh hội đồng bấm F5 và mất kết quả vừa chạy.

---

## C. Làm đẹp có kỷ luật (enterprise fintech, không màu mè)

`UI_SPEC` §1 cấm gradient lòe loẹt, glassmorphism, emoji, chart trang trí. Vì vậy "đẹp" ở đây là **nhịp điệu và độ chính xác**, không phải hiệu ứng.

1. **Sticky table header + sticky filter bar** — bảng 10–12 cột cuộn sẽ dễ đọc hơn hẳn. Ưu tiên cao, chi phí thấp.
2. **Skeleton theo đúng layout bảng** thay spinner giữa trang: giảm nhảy layout (CLS) và trông "prod-ready".
3. **Sparkline 7 điểm trong KPI card**: dashboard có xu hướng mà không cần thêm chart lớn.
4. **Density toggle (Compact / Comfortable)**: lưu localStorage; analyst soát 30+ SKU sẽ dùng ngay.
5. **Số liệu có ngữ cảnh**: mỗi KPI thêm dòng "kỳ đo · nguồn · cập nhật lúc" (đã có một phần). Đây là thứ khiến dashboard đáng tin.
6. **Typography & spacing scale**: chốt thang chữ (12/13/14/16/20/24) và nhịp 4px; hiện đang dùng khá nhất quán, nên đưa vào token thay vì rải class.
7. **Chart style thống nhất**: cùng stroke grid `#E4E7EC`, cùng font tick 11px, cùng tooltip. Đã gần đúng — nên gom vào `chartTheme.ts`.
8. **Print/PDF cho báo cáo**: BI có nhu cầu in. Một `@media print` gọn (ẩn sidebar, nền trắng, bảng không cắt dòng) là điểm cộng lớn, chi phí rất thấp.
9. **Micro-interaction duyệt giá**: highlight dòng vừa duyệt + toast "Đã duyệt · undo trong 5s" (chỉ demo) — tạo cảm giác an toàn.
10. **Dark mode**: cân nhắc kỹ. Với dashboard tài chính, dark mode dễ làm số liệu khó đọc và tốn công QA. Nếu làm, phải test contrast toàn bộ bảng + chart. Không khuyến nghị cho MVP.

Điều **không nên** làm: animation chuyển trang dài, gradient KPI, icon 3D, bo góc lớn hơn 12px, chart donut nhiều màu cho dữ liệu so sánh.

---

## D. Kiến trúc & thư viện (chỉ thêm khi có lý do)

| Nhu cầu | Hiện tại | Đề xuất |
|---|---|---|
| Data fetching | `useAsync` tự viết (đủ dùng) | Khi có cache/invalidate/lỗi retry: TanStack Query |
| Form phức tạp (rule builder, import) | state thủ công | React Hook Form + Zod, schema map 1-1 với Pydantic |
| Bảng lớn | render toàn bộ | TanStack Table + virtual rows |
| Test API contract | mock thuần | MSW dùng chung mock handler với Storybook |
| Tài liệu component | không có | Storybook (chỉ 6–8 component lõi: Button, StatusPill, DataTable, Modal, KpiCard, Field) |
| Analytics/monitoring | không có | Thêm khi deploy thật, không đưa key vào bundle |

Không đổi framework/router/state manager giữa chừng (`AI_AGENT_GUIDE` §1).

---

## E. Lộ trình gợi ý

### E1. Nếu chỉ có 2 tuần và chỉ làm frontend

| Ngày | Việc | Kết quả nhìn thấy được |
|---|---|---|
| 1–2 | F1 (localStorage + reset demo) + F8 (5 test lõi: format, rbac, floor) | F5 không mất dữ liệu; `npm test` pass |
| 3–4 | F4 (điều chỉnh tồn kho + lý do + movement) | UAT 1 chạy được đầu-cuối |
| 5–7 | F3 (import CSV: đọc file → map → preview → merge) | UAT 2 chạy được, có báo dòng lỗi |
| 8–10 | F2 (rule builder + preview + conflict) | UAT 4 thuyết phục: tạo rule → thấy SKU bị ảnh hưởng |
| 11–12 | F5 + F6 (chi tiết NCC, competitor trend) | Đủ chiều sâu dữ liệu để trả lời hội đồng |
| 13 | F7 (command palette) + C1–C3 (sticky/skeleton/sparkline) | Demo mượt, không nhảy layout |
| 14 | Đóng gói: README mô tả ranh giới mock, ảnh 3 breakpoint, kịch bản demo 8 phút | Bộ nộp hoàn chỉnh |

### E2. Nếu có 4 tuần (frontend + sẵn sàng nối backend)

| Tuần | Việc | Kết quả kiểm chứng được |
|---|---|---|
| 1 | A1 + A2 + A4: test lõi, ErrorBoundary, map lỗi API, ESLint/CI | `npm test`, `npm run build` trong CI; demo lỗi 403/422 đúng thông điệp |
| 2 | B2 + B3 + B4: import wizard, điều chỉnh tồn, chi tiết NCC | UAT 1 & 2 chạy được đầu-cuối |
| 3 | B1 + B10: rule builder có preview, nút reset demo | UAT 4 (duyệt + simulation) thuyết phục |
| 4 | B6 + B7 + C1–C4 + A5–A6: BI bổ sung, sticky/skeleton/sparkline, axe + lazy route | Báo cáo Lighthouse + ảnh chụp 3 breakpoint |

Nếu chỉ có 3–4 ngày trước bảo vệ: làm **A2 + A1 (5 test) + B10 + C1**, đó là 4 thứ tạo khác biệt rõ nhất trên mỗi phút bỏ ra.

---

## F. Checklist nghiệm thu UI (rút từ `UI_SPEC` §12)

- [ ] Mọi route có title, breadcrumb, quyền phù hợp.
- [ ] Bảng có sort/filter/pagination ở nơi cần; trạng thái rỗng có hướng dẫn.
- [ ] VND/%, ngày giờ `Asia/Ho_Chi_Minh`, null ≠ 0.
- [ ] DEMO / SIMULATED / LIVE luôn phân biệt, không có metric "live" giả.
- [ ] Responsive 360 / 768 / 1440 px; modal không vượt viewport.
- [ ] Bàn phím đi hết luồng chính; focus không bị cướp khi mở modal.
- [ ] Hành động phá huỷ hoặc cập nhật giá thật đều có confirm + hiển thị SKU/kênh/giá.
- [ ] Chart có legend + bảng thay thế; không dùng màu làm tín hiệu duy nhất.
- [ ] Không có nút bấm mà không phản hồi (phải disabled kèm lý do).
- [ ] `npm run typecheck` và `npm run build` pass; test liên quan pass.

### Checklist riêng cho bài frontend-only

- [ ] README ghi rõ: “backend chưa có; API được mô phỏng trong `src/mocks/api.ts` theo `API_SPEC`”.
- [ ] Dữ liệu deterministic: reload cho cùng kết quả, không có `Math.random` trong seed.
- [ ] Thao tác người dùng (chạy định giá, duyệt, retry, điều chỉnh tồn) **không mất khi F5** — hoặc có nút reset nói rõ.
- [ ] Không có nút bấm không phản hồi; nút chưa hỗ trợ phải `disabled` + lý do.
- [ ] Mọi trạng thái mô phỏng đều có nhãn `DEMO` / `SIMULATED` / `SNAPSHOT`.
- [ ] Có ít nhất 5 test chạy được bằng một lệnh.
- [ ] Có kịch bản demo 8 phút đi hết 5 UAT trong `IMPLEMENTATION_PLAN.md` §6.

---

## G. Rủi ro cần nói trước với hội đồng

1. **Mock ≠ live**: toàn bộ giá/đối thủ/BI là fixture hoặc snapshot. UI đã ghi nhãn; đừng bỏ nhãn khi thuyết trình.
2. **Chưa có backend**: mọi con số là deterministic từ công thức, không phải kết quả model. Đây là lựa chọn đúng cho MVP (`AI_PRICING` §2) và nên nói rõ.
3. **Retry/idempotency** mới mô phỏng ở UI+mock; khi nối thật, idempotency key phải do backend sinh và lưu.
4. **Quyền**: UI ẩn nút chỉ để trải nghiệm; mọi endpoint vẫn phải kiểm tra (SPEC §3.2).
5. **Dữ liệu thật đã thu thập** (TikTok Shop) là snapshot công khai, không phải connector realtime — giữ nhãn `SNAPSHOT`.
