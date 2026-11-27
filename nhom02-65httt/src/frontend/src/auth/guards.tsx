import { Navigate, Outlet, useLocation, useNavigate } from 'react-router-dom';
import type { ReactNode } from 'react';
import { useAuth } from '@/auth/AuthContext';
import type { Permission } from '@/lib/rbac';
import { EmptyState, Button } from '@/components/ui/primitives';

export function RequireAuth() {
  const { user } = useAuth();
  const location = useLocation();
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return <Outlet />;
}

export function Forbidden() {
  const navigate = useNavigate();
  return (
    <EmptyState
      title="Không đủ quyền truy cập"
      description="Vai trò hiện tại không được phép xem màn hình này. Liên hệ quản trị viên nếu cần."
      action={
        <Button variant="secondary" size="sm" onClick={() => navigate(-1)}>
          Quay lại
        </Button>
      }
    />
  );
}

export function RequirePermission({ permission }: { permission: Permission }) {
  const { has } = useAuth();
  if (!has(permission)) return <Forbidden />;
  return <Outlet />;
}

export function PermissionGate({
  permission,
  children,
}: {
  permission: Permission;
  children: ReactNode;
}) {
  const { has } = useAuth();
  return has(permission) ? <>{children}</> : <Forbidden />;
}