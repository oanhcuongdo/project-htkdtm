# Frontend - Hệ Thống Tìm Kiếm Nhà Thuê Thông Minh
1.Các chức năng giao diện: Trang chủ, tìm kiếm, bộ lọc, bản đồ, chi tiết phòng trọ, trợ lý AI và Dashboard.
2.Cấu hình môi trường: File .env và địa chỉ API Backend.
3.Cài đặt và khởi chạy: Hướng dẫn npm install, npm run dev, npm run build.
4.Quy ước phát triển: Cách tổ chức components, hooks, services và pages.
5.Tích hợp API: Mô tả cách Frontend giao tiếp với FastAPI.
6.Giao diện Responsive: Hỗ trợ Desktop, Tablet và Mobile.
## Công Nghệ Đề Xuất (Theo Đề Cương)
- **Framework:** React 18 / 19 (Vite)
- **Styling:** Tailwind CSS + Lucide Icons / Shadcn UI
- **Bản Đồ (Map):** Leaflet / React-Leaflet hoặc Mapbox GL JS (Hiển thị bản đồ nhiệt, vị trí phòng trọ, bán kính di chuyển tới trường đại học)
- **Quản lý State:** TanStack Query (React Query) + Zustand
- **Giao tiếp Backend:** Gọi REST API từ `src/backend/api/main.py` (`/api/listings`, `/api/recommendations`)

## Cấu Trúc Khuyến Nghị
```text
src/frontend/
├── public/
├── src/
│   ├── assets/
│   ├── components/
│   │   ├── Map/              # Bản đồ phòng trọ & tiện ích Leaflet
│   │   ├── Filters/          # Bộ lọc theo khoảng giá, bán kính, quận/huyện
│   │   ├── ListingCard/      # Thẻ hiển thị phòng trọ kèm Matching Score
│   │   └── ChatAssistant/    # Cửa sổ trợ lý AI tư vấn nhà trọ
│   ├── hooks/
│   ├── services/             # API client giao tiếp FastAPI backend
│   ├── pages/
│   │   ├── HomePage.jsx      # Tìm kiếm thông minh
│   │   ├── AnalyticsPage.jsx # Nhúng Dashboard Superset
│   │   └── DetailPage.jsx    # Chi tiết phòng trọ
│   ├── App.jsx
│   └── main.jsx
├── package.json
└── vite.config.js
```
