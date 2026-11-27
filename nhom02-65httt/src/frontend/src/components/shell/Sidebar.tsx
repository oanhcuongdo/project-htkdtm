import { NavLink } from 'react-router-dom';
import { PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import { cn } from '@/lib/cn';
import { useAuth } from '@/auth/AuthContext';
import { Button } from '@/components/ui/primitives';
import { NAV } from './nav';

export function Sidebar({
  collapsed,
  onToggle,
  mobileOpen,
  onNavigate,
}: {
  collapsed: boolean;
  onToggle: () => void;
  mobileOpen: boolean;
  onNavigate: () => void;
}) {
  const { has } = useAuth();

  const childClass = ({ isActive }: { isActive: boolean }) =>
    cn(
      'flex items-center gap-2.5 rounded-[var(--radius-control)] px-3 py-2 text-[13px] transition-colors',
      isActive
        ? 'bg-primary/10 font-medium text-primary'
        : 'text-muted hover:bg-surface-subtle hover:text-ink',
    );

  const topLinkClass = ({ isActive }: { isActive: boolean }) =>
    cn(
      'flex items-center gap-2.5 rounded-[var(--radius-control)] px-3 py-2 text-sm font-semibold transition-colors',
      isActive
        ? 'bg-primary/10 text-primary'
        : 'text-ink hover:bg-surface-subtle',
      collapsed && 'justify-center px-0',
    );

  return (
    <aside
      className={cn(
        'fixed inset-y-0 left-0 z-40 flex flex-col border-r border-border bg-surface transition-transform lg:static lg:translate-x-0',
        collapsed ? 'w-[72px]' : 'w-[248px]',
        mobileOpen ? 'translate-x-0' : '-translate-x-full',
      )}
      aria-label="Điều hướng chính"
    >
      <div
        className={cn(
          'flex h-16 items-center gap-2.5 border-b border-border px-4',
          collapsed && 'justify-center px-0',
        )}
      >
        <img
          src="/android-chrome-192x192.png"
          alt="ERP Smart Pricing"
          width={32}
          height={32}
          className="size-8 shrink-0 rounded-[var(--radius-control)] object-contain"
        />
        {!collapsed ? (
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-ink">Smart Pricing</p>
            <p className="truncate text-[11px] text-muted">ERP đa kênh</p>
          </div>
        ) : null}
      </div>

      <nav className="flex-1 overflow-y-auto px-2 py-3">
        <ul className="space-y-1">
          {NAV.map((group) => {
            if (!has(group.permission)) return null;
            const Icon = group.icon;

            /* Single-link section: bold, clickable. */
            if (group.to) {
              return (
                <li key={group.key}>
                  <NavLink
                    to={group.to}
                    onClick={onNavigate}
                    className={topLinkClass}
                    title={collapsed ? group.label : undefined}
                  >
                    <Icon className="size-4 shrink-0" aria-hidden="true" />
                    {!collapsed ? <span>{group.label}</span> : null}
                  </NavLink>
                </li>
              );
            }

            /* Collapsed: show one group icon that expands the sidebar. */
            if (collapsed) {
              return (
                <li key={group.key}>
                  <button
                    type="button"
                    onClick={onToggle}
                    title={`${group.label} — bấm để mở rộng`}
                    className="flex w-full items-center justify-center rounded-[var(--radius-control)] py-2 text-ink transition-colors hover:bg-surface-subtle"
                  >
                    <Icon className="size-4" aria-hidden="true" />
                    <span className="sr-only">{group.label}</span>
                  </button>
                </li>
              );
            }

            const children = (group.children ?? []).filter((c) => has(c.permission));

            return (
              <li key={group.key}>
                {/* Section header: bold + darker, not a link. */}
                <p className="flex cursor-default select-none items-center gap-2 px-3 pb-1 pt-3 text-[11px] font-semibold uppercase tracking-wide text-ink/80">
                  <Icon className="size-3.5 shrink-0 text-muted" aria-hidden="true" />
                  {group.label}
                </p>
                <ul className="space-y-0.5 border-l border-border pl-2 ml-3">
                  {children.map((child) => (
                    <li key={child.to}>
                      <NavLink to={child.to} onClick={onNavigate} className={childClass}>
                        {child.label}
                      </NavLink>
                    </li>
                  ))}
                </ul>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="border-t border-border px-2 py-3">
        <div
          className={cn(
            'mb-2 flex items-center justify-center gap-2 rounded-[var(--radius-control)] bg-surface-subtle px-2 py-1.5 text-[11px] text-muted',
            collapsed && 'px-0',
          )}
          title="Chế độ dữ liệu demo"
        >
          <span className="size-1.5 rounded-full bg-warning" aria-hidden="true" />
          {!collapsed ? <span>DEMO · v0.1.0</span> : null}
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="w-full"
          onClick={onToggle}
          aria-label={collapsed ? 'Mở rộng thanh điều hướng' : 'Thu gọn thanh điều hướng'}
        >
          {collapsed ? (
            <PanelLeftOpen className="size-4" aria-hidden="true" />
          ) : (
            <>
              <PanelLeftClose className="size-4" aria-hidden="true" />
              <span>Thu gọn</span>
            </>
          )}
        </Button>
      </div>
    </aside>
  );
}