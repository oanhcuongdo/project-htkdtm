'use client'

import Link from 'next/link'
import { ShieldAlert, ArrowLeft, Home } from 'lucide-react'
import { useAppStore } from '@/stores/appStore'

export default function UnauthorizedRoutePage() {
  const user = useAppStore((s) => s.auth.user)
  const dashboardHref =
    user?.role === 'admin'
      ? '/app/admin'
      : user?.role === 'lecturer'
        ? '/app/lecturer/dashboard'
        : '/app/student/dashboard'

  return (
    <main className="min-h-screen bg-background text-foreground flex items-center justify-center px-4 py-12">
      <div className="max-w-md w-full rounded-2xl border border-border bg-surface-elevated p-8 text-center shadow-soft space-y-5">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-destructive/10 text-destructive">
          <ShieldAlert className="h-7 w-7" />
        </div>
        <div className="space-y-2">
          <p className="text-xs font-bold uppercase tracking-widest text-destructive">403 · Không có quyền truy cập</p>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Bạn không có quyền xem trang này
          </h1>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Tài khoản hiện tại không thuộc vai trò được phép truy cập khu vực này. Vui lòng quay lại không gian làm việc của bạn.
          </p>
        </div>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
          <Link
            href={user ? dashboardHref : '/login'}
            className="inline-flex w-full sm:w-auto items-center justify-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground shadow-sm hover:opacity-95 transition"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>{user ? 'Về không gian của tôi' : 'Đăng nhập'}</span>
          </Link>
          <Link
            href="/"
            className="inline-flex w-full sm:w-auto items-center justify-center gap-2 rounded-xl border border-border bg-background px-4 py-2.5 text-sm font-semibold text-foreground hover:bg-muted transition"
          >
            <Home className="h-4 w-4" />
            <span>Trang chủ</span>
          </Link>
        </div>
      </div>
    </main>
  )
}
