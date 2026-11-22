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

// Component giữ chỗ chung cho các trang Tùng sẽ phát triển sau
const PlaceholderPage = ({ title }: { title: string }) => (
  <div className="space-y-4">
    <div>
      <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
      <p className="text-sm text-muted-foreground mt-0.5">
        Trang đang xây dựng (Tùng sẽ thêm nội dung theo thiết kế v0).
      </p>
    </div>
    <div className="rounded-xl border border-dashed border-border/80 p-8 text-center bg-card/50">
      <p className="text-sm text-muted-foreground">
        Nội dung trang này sẽ được Tùng hoàn thiện trong nhánh phát triển giao diện <code>nhom03-65httt-tung-ui</code>.
      </p>
    </div>
  </div>
)

// Các trang đã hoàn thiện
const LoginPage = lazy(() => import("@/pages/login"))
const KhongCoQuyenPage = lazy(() => import("@/pages/khong-co-quyen"))
const NotFoundPage = lazy(() => import("@/pages/not-found"))
const DashboardPage = lazy(() => import("@/pages/dashboard"))

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
            element: <PlaceholderPage title="Tổng quan nền tảng" />,
          },
          {
            path: "/so-sanh",
            element: <PlaceholderPage title="So sánh nền tảng" />,
          },
          {
            path: "/khia-canh",
            element: <PlaceholderPage title="Phân tích khía cạnh (ABSA)" />,
          },
          {
            path: "/xu-huong",
            element: <PlaceholderPage title="Xu hướng & dự báo" />,
          },
          {
            path: "/dashboard",
            element: withSuspense(DashboardPage),
          },
          {
            path: "/tro-ly",
            element: <PlaceholderPage title="Trợ lý AI" />,
          },
          {
            path: "/review-explorer",
            element: <PlaceholderPage title="Review Explorer" />,
          },
          {
            path: "/canh-bao",
            element: <PlaceholderPage title="Cảnh báo & khuyến nghị" />,
          },

          // Route Quản trị: chỉ Quản trị viên (Admin) được phép vào
          {
            element: <RoleGuard allowedRoles={["admin"]} />,
            children: [
              {
                path: "/quan-tri",
                element: <PlaceholderPage title="Quản trị hệ thống" />,
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
