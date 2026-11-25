import React, { useState } from "react"
import { useNavigate } from "react-router-dom"
import { GraduationCap, ShieldCheck, UserCheck, AlertCircle, Sparkles, Loader2, KeyRound } from "lucide-react"

import { useAuth } from "@/auth/AuthContext"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ThemeToggle } from "@/components/theme-toggle"

export default function LoginPage() {
  const { login, isAuthenticated } = useAuth()
  const navigate = useNavigate()

  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  React.useEffect(() => {
    if (isAuthenticated) {
      navigate("/tong-quan", { replace: true })
    }
  }, [isAuthenticated, navigate])

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMessage(null)

    if (!username.trim() || !password) {
      setErrorMessage("Vui lòng điền đầy đủ tên đăng nhập và mật khẩu.")
      return
    }

    try {
      setIsLoading(true)
      await login(username, password)
      navigate("/tong-quan", { replace: true })
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Đăng nhập thất bại. Vui lòng kiểm tra lại.")
    } finally {
      setIsLoading(false)
    }
  }

  const fillAdminAccount = () => {
    setUsername("admin")
    setPassword("")
    setErrorMessage(null)
  }

  const fillViewerAccount = () => {
    setUsername("viewer")
    setPassword("")
    setErrorMessage(null)
  }

  return (
    <div className="relative flex min-h-[100dvh] w-full flex-col items-center justify-center p-3 sm:p-6 bg-muted/30">
      {/* Nút đổi giao diện góc trên */}
      <div className="absolute top-3 right-3 sm:top-5 sm:right-5 z-20">
        <ThemeToggle />
      </div>

      <div className="w-full max-w-[440px] space-y-3.5 my-auto py-6">
        {/* Banner thông báo xác thực JWT thật */}
        <div className="flex items-start gap-2.5 rounded-lg border border-primary/30 bg-primary/10 p-3 text-xs sm:text-sm text-foreground shadow-sm">
          <KeyRound className="h-4 w-4 shrink-0 text-primary mt-0.5" />
          <div className="leading-snug">
            <span className="font-semibold block">Hệ thống xác thực JWT & Phân quyền</span>
            <span className="text-xs text-muted-foreground">
              Đăng nhập bằng tài khoản cấu hình trong tệp <code>.env</code> (AUTH_ADMIN_USER / AUTH_VIEWER_USER).
            </span>
          </div>
        </div>

        {errorMessage && (
          <div className="flex items-start gap-2.5 rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-xs sm:text-sm text-destructive shadow-sm animate-in fade-in-50">
            <AlertCircle className="h-4 w-4 shrink-0 text-destructive mt-0.5" />
            <div className="leading-snug">{errorMessage}</div>
          </div>
        )}

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
            {/* Hai nút điền nhanh tài khoản mẫu */}
            <div className="space-y-2">
              <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider text-center">
                Chọn vai trò đăng nhập
              </p>

              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={fillAdminAccount}
                  className="flex items-center gap-2 rounded-lg border border-primary/30 bg-primary/5 p-2.5 text-left transition-all hover:bg-primary/10 hover:border-primary/50 cursor-pointer"
                >
                  <ShieldCheck className="h-4 w-4 text-primary shrink-0" />
                  <div className="min-w-0">
                    <div className="text-xs font-semibold text-foreground leading-tight">Admin</div>
                    <div className="text-[10px] text-muted-foreground truncate">Toàn quyền hệ thống</div>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={fillViewerAccount}
                  className="flex items-center gap-2 rounded-lg border border-border bg-card p-2.5 text-left transition-all hover:bg-accent/60 hover:border-border/80 cursor-pointer"
                >
                  <UserCheck className="h-4 w-4 text-muted-foreground shrink-0" />
                  <div className="min-w-0">
                    <div className="text-xs font-semibold text-foreground leading-tight">Viewer</div>
                    <div className="text-[10px] text-muted-foreground truncate">Chỉ đọc báo cáo</div>
                  </div>
                </button>
              </div>
            </div>

            {/* Form đăng nhập thật kết nối API FastAPI */}
            <form onSubmit={handleLogin} className="space-y-3">
              <div className="space-y-1">
                <Label htmlFor="username" className="text-xs font-medium">
                  Tên đăng nhập
                </Label>
                <Input
                  id="username"
                  type="text"
                  placeholder="admin hoặc viewer"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="h-9 text-xs sm:text-sm"
                  autoComplete="username"
                  disabled={isLoading}
                  required
                />
              </div>

              <div className="space-y-1">
                <Label htmlFor="password" className="text-xs font-medium">
                  Mật khẩu
                </Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="h-9 text-xs sm:text-sm"
                  autoComplete="current-password"
                  disabled={isLoading}
                  required
                />
              </div>

              <Button
                type="submit"
                className="w-full cursor-pointer h-9 text-xs sm:text-sm font-medium mt-1"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Đang xác thực...
                  </>
                ) : (
                  "Đăng nhập hệ thống"
                )}
              </Button>
            </form>
          </CardContent>

          <CardFooter className="flex flex-col border-t border-border/50 py-3.5 px-4 sm:px-6 text-center text-xs text-muted-foreground gap-1">
            <div className="flex items-center justify-center gap-1.5 font-medium text-foreground text-xs">
              <Sparkles className="h-3.5 w-3.5 text-primary shrink-0" />
              <span>Đồ án HTKDTM - Nhóm 03 (65HTTT)</span>
            </div>
            <p className="text-[11px] text-muted-foreground">
              Phiên làm việc được ký bằng JWT và lưu trong <code>localStorage</code>
            </p>
          </CardFooter>
        </Card>
      </div>
    </div>
  )
}
