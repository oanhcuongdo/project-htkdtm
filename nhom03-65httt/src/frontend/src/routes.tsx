import React, { lazy, Suspense } from "react"
import { createBrowserRouter, Navigate } from "react-router-dom"

import { ProtectedRoute } from "@/auth/ProtectedRoute"
import { RoleGuard } from "@/auth/RoleGuard"
import { AppLayout } from "@/components/layout/AppLayout"
import { Skeleton } from "@/components/ui/skeleton"

// Fallback component khi đang lazy load trang
const PageLoadingFallback = () => (
  <div className="space-y-4 p-4">
    <div className="space-y-2">
      <Skeleton className="h-8 w-64" />
      <Skeleton className="h-4 w-96" />
    </div>
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4">
      <Skeleton className="h-32 w-full" />
      <Skeleton className="h-32 w-full" />
      <Skeleton className="h-32 w-full" />
    </div>
    <Skeleton className="h-64 w-full" />
  </div>
)

// Helper bọc component bằng Suspense
const withSuspense = (Component: React.LazyExoticComponent<React.ComponentType<any>>) => (
  <Suspense fallback={<PageLoadingFallback />}>
    <Component />
  </Suspense>
)

// Các trang đã hoàn thiện
const LoginPage = lazy(() => import("@/pages/login"))
const KhongCoQuyenPage = lazy(() => import("@/pages/khong-co-quyen"))
const NotFoundPage = lazy(() => import("@/pages/not-found"))
const DashboardPage = lazy(() => import("@/pages/dashboard"))
const TongQuanPage = lazy(() => import("@/pages/tong-quan"))
const SoSanhPage = lazy(() => import("@/pages/so-sanh"))
const KhiaCanhPage = lazy(() => import("@/pages/khia-canh"))
const XuHuongPage = lazy(() => import("@/pages/xu-huong"))
const TroLyPage = lazy(() => import("@/pages/tro-ly"))
const ReviewExplorerPage = lazy(() => import("@/pages/review-explorer"))
const CanhBaoPage = lazy(() => import("@/pages/canh-bao"))
const QuanTriPage = lazy(() => import("@/pages/quan-tri"))

export const router = createBrowserRouter([
  // Route đăng nhập công khai
  {
    path: "/login",
    element: withSuspense(LoginPage),
  },

  // Route thông báo không có quyền
  {
    path: "/khong-co-quyen",
    element: withSuspense(KhongCoQuyenPage),
  },

  // Nhánh route bảo vệ (yêu cầu đăng nhập)
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          // Mặc định chuyển hướng từ "/" sang "/tong-quan"
          {
            path: "/",
            element: <Navigate to="/tong-quan" replace />,
          },
          {
            path: "/tong-quan",
            element: withSuspense(TongQuanPage),
          },
          {
            path: "/so-sanh",
            element: withSuspense(SoSanhPage),
          },
          {
            path: "/khia-canh",
            element: withSuspense(KhiaCanhPage),
          },
          {
            path: "/xu-huong",
            element: withSuspense(XuHuongPage),
          },
          {
            path: "/dashboard",
            element: withSuspense(DashboardPage),
          },
          {
            path: "/tro-ly",
            element: withSuspense(TroLyPage),
          },
          {
            path: "/review-explorer",
            element: withSuspense(ReviewExplorerPage),
          },
          {
            path: "/canh-bao",
            element: withSuspense(CanhBaoPage),
          },

          // Route Quản trị: chỉ Quản trị viên (Admin) được phép vào
          {
            element: <RoleGuard allowedRoles={["admin"]} />,
            children: [
              {
                path: "/quan-tri",
                element: withSuspense(QuanTriPage),
              },
            ],
          },
        ],
      },
    ],
  },

  // Bắt tất cả các đường dẫn lạ -> trang 404 tiếng Việt
  {
    path: "*",
    element: withSuspense(NotFoundPage),
  },
])
