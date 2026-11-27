import {
  Card,
  DemoBadge,
  ErrorState,
  LoadingState,
  PageHeader,
  StatusPill,
} from '@/components/ui/primitives';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { useAsync } from '@/hooks/useAsync';
import { listUsers } from '@/mocks/api';
import { ROLE_LABELS } from '@/lib/rbac';
import { dateOnly, dateTime } from '@/lib/format';
import type { User } from '@/types/domain';

export function UsersPage() {
  const { data, loading, error, reload } = useAsync(() => listUsers(), []);

  const columns: Column<User>[] = [
    {
      key: 'name',
      header: 'Người dùng',
      sortable: true,
      sortValue: (u) => u.fullName,
      render: (u) => (
        <div>
          <p className="font-medium text-ink">{u.fullName}</p>
          <p className="text-xs text-muted">{u.email}</p>
        </div>
      ),
    },
    {
      key: 'role',
      header: 'Vai trò',
      render: (u) => <StatusPill tone="neutral">{ROLE_LABELS[u.role]}</StatusPill>,
    },
    {
      key: 'status',
      header: 'Trạng thái',
      render: (u) =>
        u.isActive ? <StatusPill tone="success">Hoạt động</StatusPill> : <StatusPill tone="danger">Vô hiệu</StatusPill>,
    },
    {
      key: 'createdAt',
      header: 'Tạo tài khoản',
      align: 'right',
      render: (u) => <span className="tnum text-muted">{dateOnly(u.createdAt)}</span>,
    },
    {
      key: 'lastLogin',
      header: 'Đăng nhập gần nhất',
      align: 'right',
      render: (u) => <span className="tnum text-muted">{dateTime(u.lastLoginAt)}</span>,
    },
  ];

  return (
    <>
      <PageHeader
        title="Người dùng & vai trò"
        description="Quản lý tài khoản nội bộ. Quyền thực thi vẫn được kiểm tra ở backend."
        actions={<DemoBadge />}
      />
      <Card>
        {loading ? (
          <LoadingState />
        ) : error || !data ? (
          <ErrorState message={error ?? 'Không tải được người dùng.'} onRetry={reload} />
        ) : (
          <DataTable
            columns={columns}
            rows={data}
            rowKey={(u) => u.id}
            caption="Danh sách người dùng"
            emptyMessage="Chưa có người dùng."
          />
        )}
        <p className="border-t border-border px-4 py-3 text-xs text-muted">
          Tạo, sửa vai trò và vô hiệu hoá tài khoản cần API quản trị — chưa bật trong bản demo.
        </p>
      </Card>
    </>
  );
}