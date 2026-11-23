# EduVision BI - Giao diện người dùng (Frontend)

Ứng dụng web trực quan hóa dữ liệu Business Intelligence cho đề tài: **“Hệ thống phân tích trải nghiệm người học và cạnh tranh giữa các nền tảng E-learning, ứng dụng AI phân tích cảm xúc và dự báo xu hướng”** (Sản phẩm: **EduVision BI**, Đồ án môn Hệ thống kinh doanh thông minh, Nhóm 03 - 65HTTT).

---

## 1. Mục đích

Ứng dụng Frontend cung cấp giao diện tương tác cho người dùng, phân tích đa chiều dữ liệu phản hồi người học của 9 nền tảng E-learning (ELSA Speak, Vuihoc, Monkey Junior, HOCMAI, Duolingo, Busuu, Khan Academy, Memrise, Quizlet). Hệ thống bao gồm:
- Trực quan hóa chỉ số Brand Health Index (BHI) và so sánh cạnh tranh.
- Phân tích cảm xúc theo 4 khía cạnh trọng yếu (ABSA) qua mô hình PhoBERT.
- Theo dõi dự báo xu hướng cảm xúc theo tháng (mô hình M3).
- Nhúng 6 dashboard trực quan hóa từ Apache Superset.
- Tương tác với Trợ lý AI (Chatbot LLM hỏi đáp trên số liệu kho dw).
- Xem và tìm kiếm chi tiết đánh giá (Review Explorer).
- Quản trị nguồn dữ liệu, kích hoạt ETL và nhận cảnh báo bất thường.

> **LƯU Ý:** Hệ thống đăng nhập hiện tại là **GIẢ (Demo)** phục vụ kiểm thử phân quyền giao diện phía client, **chưa kết nối máy chủ xác thực thật**.

---

## 2. Công nghệ sử dụng

- **Khung ứng dụng:** [React 19](https://react.dev/) + [Vite 8](https://vite.dev/) + [TypeScript](https://www.typescriptlang.org/)
- **Định tuyến:** [React Router v7](https://reactrouter.com/) (BrowserRouter, React.lazy, Suspense)
- **Giao diện & CSS:** [Tailwind CSS v4](https://tailwindcss.com/) + `@tailwindcss/vite`
- **Bộ thư viện thành phần UI:** [shadcn/ui](https://ui.shadcn.com/) (Style `new-york`, Base color `slate`, hỗ trợ Dark/Light mode qua `ThemeProvider`)
- **Biểu tượng (Icons):** [Lucide React](https://lucide.dev/)
- **Biểu đồ (Charts):** [Recharts](https://recharts.org/)
- **Thông báo:** [Sonner](https://sonner.emilkowal.ski/)
- **Tiện ích:** `clsx`, `tailwind-merge`, `date-fns`, `class-variance-authority`
- **Font chữ:** Inter

---

## 3. Cấu trúc thư mục

```text
nhom03-65httt/src/frontend/
├── .env.example              # Mẫu biến môi trường (không chứa giá trị nhạy cảm)
├── .gitignore                # Bỏ qua node_modules, dist, .env...
├── components.json           # Cấu hình shadcn/ui (style new-york, slate)
├── index.html                # Tệp HTML gốc với font Inter
├── package.json              # Khai báo phụ thuộc và scripts
├── tsconfig.json             # Cấu hình TypeScript gốc
├── tsconfig.app.json         # Cấu hình TypeScript ứng dụng & alias @ -> src
├── tsconfig.node.json        # Cấu hình TypeScript cho Vite config
├── vite.config.ts            # Cấu hình Vite, Tailwind CSS plugin và alias @
├── README.md                 # Tài liệu hướng dẫn (tệp này)
└── src/
    ├── auth/                 # Quản lý xác thực và phân quyền
    │   ├── AuthContext.tsx   # Context lưu phiên đăng nhập (khóa "eduvision.session")
    │   ├── ProtectedRoute.tsx# Chặn người dùng chưa đăng nhập chuyển về /login
    │   └── RoleGuard.tsx     # Chặn vai trò không phù hợp chuyển về /khong-co-quyen
    ├── components/
    │   ├── layout/           # Khung layout dùng chung
    │   │   ├── AppLayout.tsx # Bọc SidebarProvider, AppSidebar, Topbar và Outlet
    │   │   ├── AppSidebar.tsx# Sidebar thu gọn với 9 phân hệ theo thứ tự đề cương
    │   │   └── Topbar.tsx    # Header gồm breadcrumb, nút đổi theme, menu người dùng
    │   ├── theme-provider.tsx# Provider quản lý chế độ Sáng / Tối (lưu localStorage)
    │   ├── theme-toggle.tsx  # Nút chuyển giao diện Sáng / Tối
    │   └── ui/               # 20 component shadcn/ui dựng sẵn
    │       ├── avatar.tsx, badge.tsx, button.tsx, calendar.tsx, card.tsx,
    │       ├── dialog.tsx, dropdown-menu.tsx, input.tsx, label.tsx, popover.tsx,
    │       ├── scroll-area.tsx, select.tsx, separator.tsx, sheet.tsx, sidebar.tsx,
    │       └── skeleton.tsx, sonner.tsx, table.tsx, tabs.tsx, tooltip.tsx
    ├── hooks/
    │   └── use-mobile.tsx    # Hook kiểm tra kích thước màn hình di động
    ├── lib/
    │   └── utils.ts          # Hàm tiện ích cn (clsx + tailwind-merge)
    ├── pages/                # Các trang theo từng phân hệ (mỗi trang là 1 thư mục)
    │   ├── login/            # Trang đăng nhập demo
    │   ├── khong-co-quyen/   # Trang thông báo khi truy cập trái quyền
    │   ├── not-found/        # Trang lỗi 404 tiếng Việt
    │   ├── tong-quan/        # Phân hệ Tổng quan
    │   ├── so-sanh/          # Phân hệ So sánh nền tảng
    │   ├── khia-canh/        # Phân hệ Phân tích khía cạnh (ABSA)
    │   ├── xu-huong/         # Phân hệ Xu hướng & dự báo
    │   ├── dashboard/        # Phân hệ Dashboard Superset (khung iframe hoàn chỉnh)
    │   ├── tro-ly/           # Phân hệ Trợ lý AI (Chatbot)
    │   ├── review-explorer/  # Phân hệ Review Explorer
    │   ├── canh-bao/         # Phân hệ Cảnh báo & khuyến nghị
    │   └── quan-tri/         # Phân hệ Quản trị hệ thống (chỉ Admin)
    ├── services/
    │   └── api.ts            # Dịch vụ API giả lập có độ trễ 300-600ms (sẽ thay bằng FastAPI)
    ├── routes.tsx            # Bảng định tuyến tập trung hỗ trợ React.lazy
    ├── App.tsx               # Component ứng dụng cấp cao nhất
    ├── index.css             # CSS biến giao diện Slate & Tailwind directives
    └── main.tsx              # Điểm khởi động ứng dụng React
```

---

## 4. Danh sách Route và Phân quyền vai trò

| Đường dẫn (URL) | Tên phân hệ | Quyền truy cập | Mô tả |
|---|---|---|---|
| `/login` | Đăng nhập demo | Công khai | Đăng nhập nhanh Admin/Viewer hoặc nhập email giả |
| `/tong-quan` | Tổng quan nền tảng | Admin, Viewer | Trang mặc định khi đăng nhập thành công |
| `/so-sanh` | So sánh nền tảng | Admin, Viewer | So sánh đối đầu đa chiều giữa các nền tảng |
| `/khia-canh` | Phân tích khía cạnh | Admin, Viewer | Phân tích 4 khía cạnh ABSA qua PhoBERT |
| `/xu-huong` | Xu hướng & dự báo | Admin, Viewer | Dự báo cảm xúc theo tháng (mô hình M3) |
| `/dashboard` | Dashboard Superset | Admin, Viewer | Nhúng 6 dashboard Superset (iframe responsive) |
| `/tro-ly` | Trợ lý AI | Admin, Viewer | Chatbot hỏi đáp số liệu kho dw bằng tiếng Việt |
| `/review-explorer`| Review Explorer | Admin, Viewer | Tìm kiếm, lọc hơn 16.000 đánh giá |
| `/canh-bao` | Cảnh báo & khuyến nghị| Admin, Viewer | Cảnh báo bất thường và đề xuất hành động |
| `/quan-tri` | Quản trị hệ thống | **Chỉ Admin** | Quản lý nguồn, kích hoạt ETL, sự kiện dim_event |
| `/khong-co-quyen` | Không có quyền | Đã đăng nhập | Hiển thị khi Viewer gõ tay vào `/quan-tri` |
| `*` | 404 Not Found | Công khai | Thông báo khi nhập sai đường dẫn |

### Cơ chế đăng nhập giả (Demo)
- Nhấn nút **"Vào với tư cách Quản trị viên (Admin)"**: Cấp quyền `admin`, hiển thị toàn bộ 9 mục menu.
- Nhấn nút **"Vào với tư cách Người xem (Viewer)"**: Cấp quyền `viewer`, ẩn mục "Quản trị" trên Sidebar. Nếu người xem tự gõ `/quan-tri` trên thanh URL, `RoleGuard` sẽ tự động chuyển hướng sang `/khong-co-quyen`.
- Nhập email tùy ý: Nếu email chứa chuỗi `"admin"` (không phân biệt hoa thường) sẽ nhận vai trò Admin, ngược lại nhận vai trò Viewer.
- Phiên đăng nhập được lưu tại `localStorage` với khóa `"eduvision.session"`. Khi Đăng xuất, khóa này sẽ bị xóa.

---

## 5. Biến môi trường

Sao chép tệp mẫu `.env.example` thành `.env`:

```bash
cp .env.example .env
```

Cấu hình các biến trong tệp `.env`:
- `VITE_API_BASE_URL`: Địa chỉ backend FastAPI (ví dụ: `http://localhost:8000/api/v1`).
- `VITE_SUPERSET_DASHBOARD_URL`: Đường dẫn nhúng Superset Dashboard (ví dụ: `http://localhost:8088/superset/dashboard/.../?standalone=true`).
  - *Nếu để trống, trang `/dashboard` sẽ hiển thị thẻ hướng dẫn thiết lập thân thiện.*

---

## 6. Hướng dẫn chạy và kiểm thử

Di chuyển vào thư mục frontend:
```bash
cd nhom03-65httt/src/frontend
```

1. **Cài đặt các gói phụ thuộc:**
```bash
npm install
```

2. **Chạy máy chủ phát triển (Development):**
```bash
npm run dev
```
Ứng dụng sẽ chạy tại địa chỉ: `http://localhost:3000` (hoặc cổng hiển thị trên terminal).

3. **Kiểm tra kiểu dữ liệu TypeScript (Typecheck):**
```bash
npm run typecheck
```

4. **Đóng gói sản phẩm (Production Build):**
```bash
npm run build
```

5. **Xem trước bản đóng gói (Preview):**
```bash
npm run preview
```

---

## 7. Quy ước cho thành viên phát triển trang tiếp theo

> **Quy ước:**
> 1. Khi thêm trang nội dung mới, hãy tạo tệp `index.tsx` trong thư mục `src/pages/<tên-trang>/` và khai báo route tương ứng tại `src/routes.tsx`.
> 2. **KHÔNG** sửa đổi các tệp cấu hình nền tảng (`vite.config.ts`, `tsconfig*.json`, `components.json`), thư mục `src/components/ui/`, thư mục `src/auth/` hoặc `src/components/layout/` nếu không thật sự cần thiết.
> 3. Tùng sẽ bổ sung tệp `src/services/mock-data.ts` khi ghép dữ liệu mẫu cho các trang.
