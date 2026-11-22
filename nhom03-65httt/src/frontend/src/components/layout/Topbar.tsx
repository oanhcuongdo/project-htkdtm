import { useLocation, useNavigate } from "react-router-dom"
import { LogOut, User, ShieldCheck, ChevronRight, Home } from "lucide-react"

import { useAuth } from "@/auth/AuthContext"
import { ThemeToggle } from "@/components/theme-toggle"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Button } from "@/components/ui/button"

const pageTitles: Record<string, string> = {
  "/tong-quan": "Tổng quan nền tảng",
  "/so-sanh": "So sánh nền tảng",
  "/khia-canh": "Phân tích khía cạnh (ABSA)",
  "/xu-huong": "Xu hướng & dự báo",
  "/dashboard": "Dashboard Superset",
  "/tro-ly": "Trợ lý AI",
  "/review-explorer": "Review Explorer",
  "/canh-bao": "Cảnh báo & khuyến nghị",
  "/quan-tri": "Quản trị hệ thống",
  "/khong-co-quyen": "Không có quyền",
}

export function Topbar() {
  const { user, role, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  const currentTitle = pageTitles[location.pathname] || "EduVision BI"

  const handleLogout = () => {
    logout()
    navigate("/login")
  }

  const getInitials = (name?: string) => {
    if (!name) return "EV"
    const parts = name.trim().split(" ")
    if (parts.length >= 2) {
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
    }
    return name.slice(0, 2).toUpperCase()
  }

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-2 sm:gap-4 border-b border-border/70 bg-background/95 px-2.5 sm:px-4 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <SidebarTrigger className="h-8 w-8 cursor-pointer shrink-0" />

      {/* Breadcrumb responsive */}
      <nav aria-label="Breadcrumb" className="flex items-center gap-1 sm:gap-1.5 text-xs sm:text-sm min-w-0 mr-auto">
        <span className="hidden sm:flex items-center text-muted-foreground">
          <Home className="h-3.5 w-3.5" />
        </span>
        <ChevronRight className="hidden sm:inline-block h-3.5 w-3.5 text-muted-foreground shrink-0" />
        <span className="font-semibold text-foreground truncate max-w-[130px] sm:max-w-[240px] md:max-w-none">
          {currentTitle}
        </span>
      </nav>

      {/* Actions góc phải */}
      <div className="flex items-center gap-1 sm:gap-2 shrink-0">
        <ThemeToggle />

        {/* User Dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              className="flex items-center gap-1.5 sm:gap-2 px-1.5 sm:px-2 py-1 h-8 sm:h-9 rounded-full hover:bg-accent cursor-pointer shrink-0"
            >
              <Avatar className="h-7 w-7 border border-border">
                <AvatarFallback className="bg-primary/10 text-primary text-xs font-semibold">
                  {getInitials(user?.name)}
                </AvatarFallback>
              </Avatar>
              <div className="hidden sm:flex flex-col items-start text-left">
                <span className="text-xs font-medium text-foreground leading-none truncate max-w-[120px]">
                  {user?.name || "Người dùng"}
                </span>
                <span className="text-[10px] text-muted-foreground leading-tight mt-0.5">
                  {role === "admin" ? "Quản trị viên" : "Người xem"}
                </span>
              </div>
              <Badge
                variant={role === "admin" ? "default" : "outline"}
                className="hidden md:inline-flex text-[10px] py-0 px-1.5 h-4"
              >
                {role === "admin" ? "Admin" : "Viewer"}
              </Badge>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel className="font-normal">
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-semibold leading-none">{user?.name}</p>
                <p className="text-xs leading-none text-muted-foreground truncate">{user?.email}</p>
                <div className="pt-1">
                  <Badge variant={role === "admin" ? "default" : "secondary"} className="text-[10px]">
                    {role === "admin" ? "Vai trò: Quản trị viên" : "Vai trò: Người xem"}
                  </Badge>
                </div>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => navigate("/tong-quan")} className="cursor-pointer">
              <User className="mr-2 h-4 w-4" />
              <span>Trang chủ EduVision</span>
            </DropdownMenuItem>
            {role === "admin" && (
              <DropdownMenuItem onClick={() => navigate("/quan-tri")} className="cursor-pointer">
                <ShieldCheck className="mr-2 h-4 w-4" />
                <span>Trang quản trị</span>
              </DropdownMenuItem>
            )}
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={handleLogout}
              className="text-destructive focus:text-destructive cursor-pointer"
            >
              <LogOut className="mr-2 h-4 w-4" />
              <span>Đăng xuất</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}
