import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Bell, ChevronRight, LogOut, Menu, Search } from 'lucide-react';
import { useAuth } from '@/auth/AuthContext';
import { ROLE_LABELS } from '@/lib/rbac';
import { Button, StatusPill } from '@/components/ui/primitives';
import { sectionForPath, titleForPath } from './nav';
import { useEffect, useRef, useState, type FormEvent } from 'react';

function Breadcrumbs() {
  const { pathname } = useLocation();
  const title = titleForPath(pathname);
  const section = sectionForPath(pathname);
  const isDashboard = pathname === '/dashboard';

  return (
    <nav aria-label="Breadcrumb" className="hidden min-w-0 items-center gap-1.5 text-sm sm:flex">
      {!isDashboard ? (
        <>
          <Link to="/dashboard" className="text-muted hover:text-ink">
            Tổng quan
          </Link>
          <ChevronRight className="size-3.5 shrink-0 text-muted" aria-hidden="true" />
        </>
      ) : null}
      {section && section !== title ? (
        <>
          <span className="hidden text-muted lg:inline">{section}</span>
          <ChevronRight className="hidden size-3.5 shrink-0 text-muted lg:inline" aria-hidden="true" />
        </>
      ) : null}
      <span className="truncate font-medium text-ink">{title}</span>
    </nav>
  );
}

function GlobalSearch() {
  const navigate = useNavigate();
  const [term, setTerm] = useState('');

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const value = term.trim();
    navigate(value ? `/products?q=${encodeURIComponent(value)}` : '/products');
  }

  return (
    <form onSubmit={onSubmit} className="relative hidden md:block" role="search">
      <Search
        className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted"
        aria-hidden="true"
      />
      <input
        type="search"
        value={term}
        onChange={(e) => setTerm(e.target.value)}
        placeholder="Tìm SKU, sản phẩm…"
        aria-label="Tìm SKU hoặc sản phẩm"
        className="h-9 w-56 rounded-[var(--radius-control)] border border-border bg-surface-subtle pl-8 pr-3 text-sm text-ink placeholder:text-muted/70"
      />
    </form>
  );
}

const NOTIFICATIONS = [
  { label: 'Đề xuất giá đang chờ duyệt', to: '/pricing/recommendations' },
  { label: 'Quan sát giá đối thủ cũ hơn 24 giờ', to: '/competitor-prices' },
  { label: 'SKU dưới ngưỡng tồn kho', to: '/inventory' },
];

function NotificationMenu() {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener('mousedown', onDoc);
    return () => document.removeEventListener('mousedown', onDoc);
  }, []);

  return (
    <div className="relative" ref={ref}>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setOpen((v) => !v)}
        aria-label="Thông báo và cảnh báo"
        aria-haspopup="menu"
        aria-expanded={open}
        className="relative"
      >
        <Bell className="size-4" aria-hidden="true" />
        <span className="absolute right-1.5 top-1.5 size-1.5 rounded-full bg-danger" aria-hidden="true" />
      </Button>
      {open ? (
        <div
          role="menu"
          className="absolute right-0 mt-2 w-64 rounded-[var(--radius-card)] border border-border bg-surface p-1 shadow-xl"
        >
          <p className="px-3 py-2 text-[11px] font-semibold uppercase tracking-wide text-muted">
            Cần chú ý
          </p>
          {NOTIFICATIONS.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              role="menuitem"
              onClick={() => setOpen(false)}
              className="flex items-center gap-2 rounded-[var(--radius-control)] px-3 py-2 text-sm text-ink hover:bg-surface-subtle"
            >
              <span className="size-1.5 shrink-0 rounded-full bg-warning" aria-hidden="true" />
              {item.label}
            </Link>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function UserMenu() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener('mousedown', onDoc);
    return () => document.removeEventListener('mousedown', onDoc);
  }, []);

  if (!user) return null;
  const initials = user.fullName
    .split(' ')
    .slice(-2)
    .map((p) => p[0])
    .join('')
    .toUpperCase();

  return (
    <div className="relative" ref={ref}>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={open}
        className="gap-2"
      >
        <span className="flex size-7 items-center justify-center rounded-full bg-primary/10 text-[11px] font-semibold text-primary">
          {initials}
        </span>
        <span className="hidden text-left sm:block">
          <span className="block text-xs font-medium leading-tight text-ink">
            {user.fullName}
          </span>
          <span className="block text-[11px] leading-tight text-muted">
            {ROLE_LABELS[user.role]}
          </span>
        </span>
      </Button>
      {open ? (
        <div
          role="menu"
          className="absolute right-0 mt-2 w-56 rounded-[var(--radius-card)] border border-border bg-surface p-1 shadow-xl"
        >
          <div className="border-b border-border px-3 py-2">
            <p className="text-xs font-medium text-ink">{user.fullName}</p>
            <p className="text-[11px] text-muted">{user.email}</p>
          </div>
          <button
            type="button"
            role="menuitem"
            onClick={logout}
            className="flex w-full items-center gap-2 rounded-[var(--radius-control)] px-3 py-2 text-left text-sm text-ink hover:bg-surface-subtle"
          >
            <LogOut className="size-4" aria-hidden="true" />
            Đăng xuất
          </button>
        </div>
      ) : null}
    </div>
  );
}

export function Topbar({ onOpenMobile }: { onOpenMobile: () => void }) {
  const { pathname } = useLocation();

  // UI_SPEC §12 — every route carries a title.
  useEffect(() => {
    document.title = `${titleForPath(pathname)} · ERP Smart Pricing`;
  }, [pathname]);

  return (
    <header className="flex h-16 shrink-0 items-center justify-between gap-3 border-b border-border bg-surface px-4 lg:px-6">
      <div className="flex min-w-0 items-center gap-3">
        <Button
          variant="ghost"
          size="sm"
          className="lg:hidden"
          onClick={onOpenMobile}
          aria-label="Mở menu"
        >
          <Menu className="size-5" aria-hidden="true" />
        </Button>
        <Breadcrumbs />
      </div>

      <div className="flex items-center gap-2">
        <GlobalSearch />

        <StatusPill tone="warning" className="hidden sm:inline-flex">
          <span className="size-1.5 rounded-full bg-warning" aria-hidden="true" />
          SIMULATED
        </StatusPill>

        <NotificationMenu />
        <UserMenu />
      </div>
    </header>
  );
}
