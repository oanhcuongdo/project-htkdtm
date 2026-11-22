import { useNavigate } from "react-router-dom"
import { ShieldAlert, ArrowLeft, LogOut } from "lucide-react"

import { useAuth } from "@/auth/AuthContext"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export default function KhongCoQuyenPage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate("/login")
  }

  return (
    <div className="flex min-h-[70vh] w-full flex-col items-center justify-center p-3 sm:p-6">
      <Card className="w-full max-w-lg border-destructive/30 shadow-md">
        <CardHeader className="text-center pb-2 px-4 sm:px-6">
          <div className="mx-auto mb-2.5 flex h-12 w-12 sm:h-14 sm:w-14 items-center justify-center rounded-full bg-destructive/10 text-destructive">
            <ShieldAlert className="h-6 w-6 sm:h-8 sm:w-8" />
          </div>
          <CardTitle className="text-lg sm:text-xl font-bold text-destructive">
            Không có quyền truy cập
          </CardTitle>
          <CardDescription className="text-xs sm:text-sm mt-1 leading-relaxed">
            Trang này chỉ dành cho tài khoản có vai trò <strong>Quản trị viên (Admin)</strong>.
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-3 text-center text-xs sm:text-sm text-muted-foreground px-4 sm:px-6">
          <div className="rounded-md bg-muted p-3 text-xs text-left space-y-1">
            <p><strong>Tài khoản hiện tại:</strong> {user?.name || "Người dùng"}</p>
            <p className="truncate"><strong>Email:</strong> {user?.email || "Chưa xác định"}</p>
            <div className="mt-1 flex items-center gap-1.5 flex-wrap">
              <strong>Vai trò:</strong>
              <Badge variant="outline" className="text-[10px] py-0 h-4">
                {user?.role === "admin" ? "Quản trị viên" : "Người xem (Viewer)"}
              </Badge>
            </div>
          </div>
          <p className="leading-relaxed">
            Nếu bạn cần truy cập trang Quản trị, vui lòng đăng xuất và đăng nhập lại bằng tài khoản Quản trị viên.
          </p>
        </CardContent>

        <CardFooter className="flex flex-col sm:flex-row gap-2 justify-center border-t border-border/50 pt-3.5 px-4 sm:px-6">
          <Button
            variant="default"
            onClick={() => navigate("/tong-quan")}
            className="w-full sm:w-auto gap-1.5 cursor-pointer text-xs sm:text-sm h-9"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>Về trang Tổng quan</span>
          </Button>
          <Button
            variant="outline"
            onClick={handleLogout}
            className="w-full sm:w-auto gap-1.5 text-destructive hover:text-destructive cursor-pointer text-xs sm:text-sm h-9"
          >
            <LogOut className="h-4 w-4" />
            <span>Đăng nhập tài khoản khác</span>
          </Button>
        </CardFooter>
      </Card>
    </div>
  )
}
