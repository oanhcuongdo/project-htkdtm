import type { Role } from '@/types/domain';

/*
 * UI-only permission gates. SPEC.md §3.2 — the backend must still authorize
 * every request; hiding a button is not authorization.
 */
export const PERMISSIONS = [
  'product.read',
  'product.write',
  'inventory.read',
  'inventory.write',
  'channel.read',
  'competitor.read',
  'competitor.write',
  'pricing.read',
  'pricing.run',
  'pricing.approve',
  'rule.read',
  'rule.write',
  'execution.read',
  'execution.run',
  'bi.read',
  'settings.read',
  'settings.write',
  'audit.read',
] as const;

export type Permission = (typeof PERMISSIONS)[number];

const ROLE_PERMISSIONS: Record<Role, Permission[]> = {
  ADMIN: [...PERMISSIONS],
  MANAGER: [
    'product.read',
    'inventory.read',
    'channel.read',
    'competitor.read',
    'pricing.read',
    'pricing.approve',
    'rule.read',
    'rule.write',
    'execution.read',
    'execution.run',
    'bi.read',
    'audit.read',
  ],
  PRICING_ANALYST: [
    'product.read',
    'inventory.read',
    'competitor.read',
    'competitor.write',
    'pricing.read',
    'pricing.run',
    'rule.read',
    'rule.write',
    'bi.read',
  ],
  INVENTORY_STAFF: [
    'product.read',
    'product.write',
    'inventory.read',
    'inventory.write',
    'competitor.read',
    'pricing.read',
    'bi.read',
  ],
  VIEWER: ['product.read', 'inventory.read', 'competitor.read', 'pricing.read', 'rule.read', 'bi.read'],
};

export function can(role: Role | undefined, permission: Permission): boolean {
  if (!role) return false;
  return ROLE_PERMISSIONS[role].includes(permission);
}

export const ROLE_LABELS: Record<Role, string> = {
  ADMIN: 'Quản trị viên',
  MANAGER: 'Quản lý',
  PRICING_ANALYST: 'Chuyên viên định giá',
  INVENTORY_STAFF: 'Nhân viên kho',
  VIEWER: 'Chỉ xem',
};