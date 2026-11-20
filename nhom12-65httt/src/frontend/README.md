# Frontend - Hệ Thống Tìm Kiếm Nhà Thuê Thông Minh

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
