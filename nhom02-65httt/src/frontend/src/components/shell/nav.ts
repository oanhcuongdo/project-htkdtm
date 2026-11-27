import type { LucideIcon } from 'lucide-react';
import {
  Boxes,
  FileBarChart,
  Gauge,
  ListChecks,
  Package,
  Settings2,
  Swords,
  Zap,
} from 'lucide-react';
import type { Permission } from '@/lib/rbac';

export interface NavChild {
  label: string;
  to: string;
  permission: Permission;
}

export interface NavGroup {
  key: string;
  label: string;
  icon: LucideIcon;
  permission: Permission;
  children?: NavChild[];
  to?: string;
}

export const NAV: NavGroup[] = [
  { key: 'dashboard', label: 'Tổng quan', icon: Gauge, to: '/dashboard', permission: 'bi.read' },
  {
    key: 'catalog',
    label: 'Sản phẩm & Nguồn hàng',
    icon: Package,
    permission: 'product.read',
    children: [
      { label: 'Sản phẩm / SKU', to: '/products', permission: 'product.read' },
      { label: 'Nhà cung cấp', to: '/suppliers', permission: 'product.read' },
      { label: 'Giá vốn', to: '/costs', permission: 'product.read' },
    ],
  },
  {
    key: 'inventory',
    label: 'Tồn kho & Kênh bán',
    icon: Boxes,
    permission: 'inventory.read',
    children: [
      { label: 'Tồn kho', to: '/inventory', permission: 'inventory.read' },
      { label: 'Kênh bán & mapping', to: '/channels', permission: 'channel.read' },
    ],
  },
  {
    key: 'market',
    label: 'Đối thủ & Thị trường',
    icon: Swords,
    permission: 'competitor.read',
    children: [
      { label: 'Đối thủ', to: '/competitors', permission: 'competitor.read' },
      { label: 'Theo dõi giá', to: '/competitor-prices', permission: 'competitor.read' },
      { label: 'Dữ liệu thu thập', to: '/competitor-prices/collected', permission: 'competitor.read' },
    ],
  },
  {
    key: 'pricing',
    label: 'AI Smart Pricing',
    icon: Zap,
    permission: 'pricing.read',
    children: [
      { label: 'Chạy định giá', to: '/pricing/run', permission: 'pricing.run' },
      {
        label: 'Đề xuất giá',
        to: '/pricing/recommendations',
        permission: 'pricing.read',
      },
      { label: 'Lịch sử chạy', to: '/pricing/runs', permission: 'pricing.read' },
    ],
  },
  {
    key: 'rules',
    label: 'Pricing Rules',
    icon: ListChecks,
    permission: 'rule.read',
    children: [
      { label: 'Danh sách quy tắc', to: '/pricing-rules', permission: 'rule.read' },
      { label: 'Lịch sử thực thi', to: '/automation/runs', permission: 'execution.read' },
    ],
  },
  {
    key: 'bi',
    label: 'BI & Báo cáo',
    icon: FileBarChart,
    permission: 'bi.read',
    children: [
      { label: 'Lợi nhuận', to: '/bi/profitability', permission: 'bi.read' },
      { label: 'Đối thủ & Nguồn hàng', to: '/bi/competitors', permission: 'bi.read' },
      { label: 'Hiệu suất tự động hoá', to: '/bi/automation', permission: 'bi.read' },
    ],
  },
  {
    key: 'settings',
    label: 'Quản trị',
    icon: Settings2,
    permission: 'settings.read',
    children: [
      { label: 'Người dùng & vai trò', to: '/settings/users', permission: 'settings.read' },
      { label: 'Cấu hình phí', to: '/settings/channel-fees', permission: 'settings.read' },
      { label: 'Nhật ký hoạt động', to: '/settings/audit-logs', permission: 'audit.read' },
    ],
  },
];

/** Flat route title map for breadcrumbs and document titles. */
export const ROUTE_TITLES: Record<string, string> = {
  '/dashboard': 'Tổng quan',
  '/products': 'Sản phẩm / SKU',
  '/suppliers': 'Nhà cung cấp',
  '/costs': 'Giá vốn',
  '/inventory': 'Tồn kho',
  '/channels': 'Kênh bán & mapping',
  '/competitors': 'Đối thủ',
  '/competitor-prices': 'Theo dõi giá',
  '/competitor-prices/collected': 'Dữ liệu thu thập',
  '/pricing/run': 'Chạy định giá',
  '/pricing/recommendations': 'Đề xuất giá',
  '/pricing/runs': 'Lịch sử chạy',
  '/pricing-rules': 'Pricing Rules',
  '/automation/runs': 'Lịch sử thực thi',
  '/bi/profitability': 'Lợi nhuận',
  '/bi/competitors': 'Đối thủ & Nguồn hàng',
  '/bi/automation': 'Hiệu suất tự động hoá',
  '/settings/users': 'Người dùng & vai trò',
  '/settings/channel-fees': 'Cấu hình phí',
  '/settings/audit-logs': 'Nhật ký hoạt động',
};

const DETAIL_TITLES: { pattern: RegExp; title: string }[] = [
  { pattern: /^\/products\/[^/]+$/, title: 'Chi tiết sản phẩm' },
  { pattern: /^\/pricing\/recommendations\/[^/]+$/, title: 'Chi tiết đề xuất' },
];

export function titleForPath(pathname: string): string {
  const exact = ROUTE_TITLES[pathname];
  if (exact) return exact;
  const detail = DETAIL_TITLES.find((d) => d.pattern.test(pathname));
  return detail ? detail.title : 'Trang';
}

/** Sidebar section that owns the current path, for the breadcrumb trail. */
export function sectionForPath(pathname: string): string | null {
  for (const group of NAV) {
    if (group.to && pathname === group.to) return group.label;
    for (const child of group.children ?? []) {
      if (pathname === child.to || pathname.startsWith(`${child.to}/`)) {
        return group.label;
      }
    }
  }
  return null;
}
