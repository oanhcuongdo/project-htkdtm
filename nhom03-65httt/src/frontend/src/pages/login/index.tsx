import React, { useState } from "react"
import { useNavigate } from "react-router-dom"
import { GraduationCap, ShieldCheck, UserCheck, AlertCircle, Sparkles, ArrowRight } from "lucide-react"

import { useAuth } from "@/auth/AuthContext"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ThemeToggle } from "@/components/theme-toggle"

export default function LoginPage() {
  const { login, loginAsAdmin, loginAsViewer, isAuthenticated } = useAuth()
  const navigate = useNavigate()

  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")

  React.useEffect(() => {
    if (isAuthenticated) {
      navigate("/tong-quan", { replace: true })
    }
  }, [isAuthenticated, navigate])

  const handleCustomLogin = (e: React.FormEvent) => {
    e.preventDefault()
    login(email || "demo@eduvision.vn")
    navigate("/tong-quan")
  }

  const handleAdminQuick = () => {
    loginAsAdmin()
    navigate("/tong-quan")
  }

  const handleViewerQuick = () => {
    loginAsViewer()
    navigate("/tong-quan")
  }

  return (
    <div className="relative flex min-h-[100dvh] w-full flex-col items-center justify-center p-3 sm:p-6 bg-muted/30">
      {/* Nút đổi giao diện góc trên */}
      <div className="absolute top-3 right-3 sm:top-5 sm:right-5 z-20">
        <ThemeToggle />
      </div>

      <div className="w-full max-w-[440px] space-y-3.5 my-auto py-6">
        {/* Banner thông báo demo */}
        <div className="flex items-start gap-2.5 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-xs sm:text-sm text-amber-800 dark:text-amber-300 shadow-sm">
          <AlertCircle className="h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400 mt-0.5" />
          <div className="leading-snug">
            <span className="font-semibold block">Đăng nhập demo, chưa kết nối máy chủ</span>
            <span className="text-xs text-amber-700/80 dark:text-amber-300/80">
              Chọn một trong hai vai trò bên dưới để kiểm thử phân quyền giao diện.
            </span>
          </div>
        </div>

        <Card className="border-border/80 shadow-lg">
          <CardHeader className="text-center pb-3 pt-5 px-4 sm:px-6">
            <div className="mx-auto mb-2.5 flex h-12 w-12 sm:h-14 sm:w-14 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-md">
              <GraduationCap className="h-7 w-7 sm:h-8 sm:w-8" />
            </div>
            <CardTitle className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
              EduVision BI
            </CardTitle>
            <CardDescription className="text-xs sm:text-sm mt-1 leading-relaxed text-muted-foreground">
              Hệ thống phân tích trải nghiệm người học & cạnh tranh giữa 9 nền tảng E-learning
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4 px-4 sm:px-6">
            {/* Hai nút đăng nhập nhanh dạng Option Card responsive */}
            <div className="space-y-2">
              <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider text-center">
                Vào nhanh theo vai trò (1 chạm)
              </p>

              <div className="flex flex-col gap-2">
                {/* Nút Admin */}
                <button
                  type="button"
                  onClick={handleAdminQuick}
                  className="group relative flex w-full items-center justify-between rounded-lg border border-primary/30 bg-primary/5 p-3 text-left transition-all hover:bg-primary/10 hover:border-primary/50 focus:outline-none focus:ring-2 focus:ring-primary/40 cursor-pointer"
                >
                  <div className="flex items-center gap-2.5 min-w-0 pr-2">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-primary text-primary-foreground">
                      <ShieldCheck className="h-5 w-5" />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="text-xs sm:text-sm font-semibold text-foreground">
                          Vào với tư cách Quản trị viên (Admin)
                        </span>
                        <Badge variant="default" className="text-[9px] py-0 px-1 h-3.5 leading-none">
                          Admin
                        </Badge>
                      </div>
                      <p className="text-[11px] text-muted-foreground truncate mt-0.5">
                        Xem tất cả 9 phân hệ và toàn quyền Quản trị
                      </p>
                    </div>
                  </div>
                  <ArrowRight className="h-4 w-4 shrink-0 text-muted-foreground group-hover:text-primary group-hover:translate-x-0.5 transition-all" />
                </button>

                {/* Nút Viewer */}
                <button
                  type="button"
                  onClick={handleViewerQuick}
                  className="group relative flex w-full items-center justify-between rounded-lg border border-border bg-card p-3 text-left transition-all hover:bg-accent/60 hover:border-border/80 focus:outline-none focus:ring-2 focus:ring-primary/40 cursor-pointer"
                >
                  <div className="flex items-center gap-2.5 min-w-0 pr-2">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-secondary text-secondary-foreground border border-border/50">
                      <UserCheck className="h-5 w-5" />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="text-xs sm:text-sm font-semibold text-foreground">
                          Vào với tư cách Người xem (Viewer)
                        </span>
                        <Badge variant="secondary" className="text-[9px] py-0 px-1 h-3.5 leading-none">
                          Viewer
                        </Badge>
                      </div>
                      <p className="text-[11px] text-muted-foreground truncate mt-0.5">
                        Xem 8 phân hệ; bị chặn ở trang Quản trị
                      </p>
                    </div>
                  </div>
                  <ArrowRight className="h-4 w-4 shrink-0 text-muted-foreground group-hover:text-foreground group-hover:translate-x-0.5 transition-all" />
                </button>
              </div>
            </div>

            <div className="relative my-2">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t border-border/70" />
              </div>
              <div className="relative flex justify-center text-[11px] uppercase">
                <span className="bg-card px-2 text-muted-foreground font-medium">hoặc tự nhập email</span>
              </div>
            </div>

            {/* Form đăng nhập giả */}
            <form onSubmit={handleCustomLogin} className="space-y-3">
              <div className="space-y-1">
                <Label htmlFor="email" className="text-xs font-medium">
                  Email (chứa từ "admin" sẽ nhận quyền Admin)
                </Label>
                <Input
                  id="email"
                  type="text"
                  placeholder="admin@eduvision.vn hoặc user@eduvision.vn"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="h-9 text-xs sm:text-sm"
                />
              </div>

              <div className="space-y-1">
                <Label htmlFor="password" className="text-xs font-medium">
                  Mật khẩu giả (nhận bất kỳ giá trị nào)
                </Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="h-9 text-xs sm:text-sm"
                />
              </div>

              <Button
                type="submit"
                variant="outline"
                className="w-full cursor-pointer h-9 text-xs sm:text-sm font-medium mt-1"
              >
                Đăng nhập vào hệ thống
              </Button>
            </form>
          </CardContent>

          <CardFooter className="flex flex-col border-t border-border/50 py-3.5 px-4 sm:px-6 text-center text-xs text-muted-foreground gap-1">
            <div className="flex items-center justify-center gap-1.5 font-medium text-foreground text-xs">
              <Sparkles className="h-3.5 w-3.5 text-primary shrink-0" />
              <span>Đồ án HTKDTM - Nhóm 03 (65HTTT)</span>
            </div>
            <p className="text-[11px] text-muted-foreground">
              Phiên làm việc được lưu trên trình duyệt qua khóa <code>eduvision.session</code>
            </p>
          </CardFooter>
        </Card>
      </div>
    </div>
  )
}
