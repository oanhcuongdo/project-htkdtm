import {
  BarChart3,
  Building2,
  GitCompareArrows,
  Heart,
  LogIn,
  LogOut,
  Map,
  Menu,
  MessageSquareText,
  ShieldAlert,
  X,
} from 'lucide-react';
import { useState } from 'react';
import { Link, NavLink } from 'react-router-dom';
import { useSession } from '../../contexts/SessionContext';

export function Navbar({ onOpenChat }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { user, isAdmin, logout } = useSession();

  const navItems = [
    { to: '/', label: 'Trang chủ', icon: Building2 },
    { to: '/map', label: 'Bản đồ', icon: Map },
    { to: '/compare', label: 'So sánh', icon: GitCompareArrows },
    { to: '/wishlist', label: 'Yêu thích', icon: Heart },
    { to: '/analytics', label: 'Thị trường BI', icon: BarChart3 },
  ];

  if (isAdmin) {
    navItems.push({ to: '/admin', label: 'Quản trị', icon: ShieldAlert });
  }

  return (
    <header className="glass-nav sticky top-0 z-40 border-b border-teal-100">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
        <Link to="/" className="flex items-center gap-2.5 text-[#134E4A]">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#0F766E] text-white shadow-xs">
            <Building2 className="h-5 w-5" aria-hidden="true" />
          </div>
          <div>
            <span className="block text-base font-bold leading-tight">SmartRent Hà Nội</span>
            <span className="block text-xs text-[#475569]">Nhóm 12 · 65HTTT</span>
          </div>
        </Link>

        <nav className="hidden items-center gap-1 lg:flex" aria-label="Điều hướng chính">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `inline-flex min-h-11 items-center gap-1.5 rounded-xl px-3.5 py-2 text-sm font-medium transition-colors ${
                    isActive ? 'bg-[#0F766E] text-white' : 'text-[#134E4A] hover:bg-teal-50'
                  }`
                }
              >
                <Icon className="h-4 w-4" aria-hidden="true" />
                {item.label}
              </NavLink>
            );
          })}
        </nav>

        <div className="hidden items-center gap-2 lg:flex">
          <button
            type="button"
            onClick={onOpenChat}
            className="inline-flex min-h-11 items-center gap-1.5 rounded-xl bg-[#0369A1] px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-[#075985]"
          >
            <MessageSquareText className="h-4 w-4" aria-hidden="true" />
            Trợ lý AI
          </button>

          {user ? (
            <button
              type="button"
              onClick={logout}
              className="inline-flex min-h-11 items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-sm font-medium text-[#134E4A] hover:bg-slate-50"
            >
              <LogOut className="h-4 w-4" aria-hidden="true" />
              {user.full_name}
            </button>
          ) : (
            <Link
              to="/login"
              className="inline-flex min-h-11 items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-sm font-medium text-[#134E4A] hover:bg-slate-50"
            >
              <LogIn className="h-4 w-4" aria-hidden="true" />
              Đăng nhập
            </Link>
          )}
        </div>

        <button
          type="button"
          onClick={() => setMobileOpen((v) => !v)}
          aria-label="Mở menu điều hướng"
          className="flex h-11 w-11 items-center justify-center rounded-xl border border-slate-200 bg-white text-[#134E4A] lg:hidden"
        >
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {mobileOpen && (
        <div className="border-t border-teal-100 bg-white px-4 py-3 lg:hidden">
          <div className="flex flex-col gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  onClick={() => setMobileOpen(false)}
                  className={({ isActive }) =>
                    `inline-flex min-h-11 items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium ${
                      isActive ? 'bg-[#0F766E] text-white' : 'text-[#134E4A] hover:bg-teal-50'
                    }`
                  }
                >
                  <Icon className="h-4 w-4" aria-hidden="true" />
                  {item.label}
                </NavLink>
              );
            })}
            <button
              type="button"
              onClick={() => {
                setMobileOpen(false);
                onOpenChat();
              }}
              className="mt-1 inline-flex min-h-11 items-center gap-2 rounded-xl bg-[#0369A1] px-3 py-2 text-sm font-semibold text-white"
            >
              <MessageSquareText className="h-4 w-4" aria-hidden="true" />
              Trợ lý AI
            </button>
          </div>
        </div>
      )}
    </header>
  );
}
