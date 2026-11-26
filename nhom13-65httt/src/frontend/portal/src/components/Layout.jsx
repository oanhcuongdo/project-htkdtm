import React from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { BarChart3, Bot, Database, Home, LogOut } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import BrandWordmark from './brand/BrandWordmark'

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard BI', icon: BarChart3 },
  { to: '/chat', label: 'Trợ lý Gemini AI', icon: Bot },
  { to: '/data-sources', label: 'Nguồn Dữ liệu', icon: Database },
]

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <div className="min-h-screen flex bg-boulder-pahkla">
      {/* Sidebar — Brand Estonia Mustkivi Dark */}
      <aside className="w-64 bg-boulder-mustkivi text-boulder-ehakivi flex flex-col shrink-0 border-r border-white/10">
        <div className="px-5 py-5 border-b border-white/10">
          <Link to="/" title="Về trang giới thiệu">
            <BrandWordmark dark subtitle="Nhóm 13 • 65HTTT" />
          </Link>
        </div>

        <nav className="flex-1 px-3 py-5 space-y-1.5">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold transition-colors ${
                  isActive
                    ? 'bg-estonia-blue text-white'
                    : 'text-boulder-hellamaa hover:bg-white/10 hover:text-white'
                }`
              }
            >
              <Icon className="w-4 h-4" strokeWidth={2} />
              {label}
            </NavLink>
          ))}

          <div className="pt-3 mt-3 border-t border-white/10">
            <Link
              to="/"
              className="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-medium text-boulder-kabelikivi hover:bg-white/5 hover:text-estonia-parnu transition-colors"
            >
              <Home className="w-4 h-4" strokeWidth={2} />
              Trang giới thiệu (Landing)
            </Link>
          </div>
        </nav>

        <div className="p-4 border-t border-white/10">
          <div className="mb-3 px-2">
            <p className="text-sm font-semibold text-white truncate">{user?.full_name || 'Người dùng'}</p>
            <p className="text-xs text-boulder-kabelikivi truncate">{user?.email}</p>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl text-xs font-semibold bg-white/10 hover:bg-rose-600 text-boulder-hellamaa hover:text-white transition-colors"
          >
            <LogOut className="w-3.5 h-3.5" />
            Đăng xuất
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 min-w-0 overflow-auto">
        <div className="max-w-7xl mx-auto p-6 lg:p-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
