import * as React from "react"
import { useLocation, useNavigate } from "react-router-dom"
import {
  LayoutDashboard,
  ArrowLeftRight,
  Layers,
  TrendingUp,
  LineChart,
  Bot,
  MessageSquareText,
  AlertTriangle,
  ShieldCheck,
  GraduationCap,
} from "lucide-react"

import { useAuth } from "@/auth/AuthContext"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from "@/components/ui/sidebar"
import { Badge } from "@/components/ui/badge"

interface NavItem {
  title: string
  url: string
  icon: React.ComponentType<{ className?: string }>
  adminOnly?: boolean
  badge?: string
}

const navItems: NavItem[] = [
  {
    title: "Tổng quan",
    url: "/tong-quan",
    icon: LayoutDashboard,
  },
  {
    title: "So sánh nền tảng",
    url: "/so-sanh",
    icon: ArrowLeftRight,
  },
  {
    title: "Phân tích khía cạnh",
    url: "/khia-canh",
    icon: Layers,
  },
  {
    title: "Xu hướng & dự báo",
    url: "/xu-huong",
    icon: TrendingUp,
  },
  {
    title: "Dashboard Superset",
    url: "/dashboard",
    icon: LineChart,
  },
  {
    title: "Trợ lý AI",
    url: "/tro-ly",
    icon: Bot,
    badge: "AI",
  },
  {
    title: "Review Explorer",
    url: "/review-explorer",
    icon: MessageSquareText,
  },
  {
    title: "Cảnh báo & khuyến nghị",
    url: "/canh-bao",
    icon: AlertTriangle,
  },
  {
    title: "Quản trị",
    url: "/quan-tri",
    icon: ShieldCheck,
    adminOnly: true,
  },
]

export function AppSidebar() {
  const { role } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  // Filter items: Viewer does not see adminOnly items
  const visibleItems = navItems.filter((item) => !item.adminOnly || role === "admin")

  return (
    <Sidebar collapsible="icon" className="border-r border-border/70">
      <SidebarHeader className="border-b border-border/50 py-3">
        <div className="flex items-center gap-2 px-2">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm">
            <GraduationCap className="h-5 w-5" />
          </div>
          <div className="flex flex-col overflow-hidden group-data-[collapsible=icon]:hidden">
            <span className="font-bold text-base tracking-tight text-foreground truncate">
              EduVision BI
            </span>
            <span className="text-[11px] text-muted-foreground truncate">
              9 Nền tảng E-learning
            </span>
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
            Phân hệ nghiệp vụ
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {visibleItems.map((item) => {
                const isActive = location.pathname === item.url
                const Icon = item.icon
                return (
                  <SidebarMenuItem key={item.url}>
                    <SidebarMenuButton
                      tooltip={item.title}
                      isActive={isActive}
                      onClick={() => navigate(item.url)}
                      className={`cursor-pointer transition-colors ${
                        isActive
                          ? "bg-primary/10 text-primary font-semibold dark:bg-primary/20"
                          : "hover:bg-accent hover:text-accent-foreground"
                      }`}
                    >
                      <Icon className={`h-4 w-4 shrink-0 ${isActive ? "text-primary" : "text-muted-foreground"}`} />
                      <span className="truncate">{item.title}</span>
                      {item.badge && (
                        <Badge
                          variant="secondary"
                          className="ml-auto text-[10px] px-1.5 py-0 h-4 group-data-[collapsible=icon]:hidden"
                        >
                          {item.badge}
                        </Badge>
                      )}
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                )
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="border-t border-border/50 p-3">
        <div className="flex items-center gap-2 group-data-[collapsible=icon]:hidden text-xs text-muted-foreground px-1">
          <span className="inline-block h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>Hệ thống BI Nhóm 03</span>
        </div>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
