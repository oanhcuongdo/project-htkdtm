import { Mail, Phone } from 'lucide-react';
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
import { listSuppliers } from '@/mocks/api';
import { dateOnly } from '@/lib/format';
import type { Supplier } from '@/types/domain';

export function SuppliersPage() {
  const { data, loading, error, reload } = useAsync(() => listSuppliers(), []);

  const columns: Column<Supplier>[] = [
    {
      key: 'name',
      header: 'Nhà cung cấp',
      sortable: true,
      sortValue: (s) => s.name,
      render: (s) => (
        <div>
          <p className="font-medium text-ink">{s.name}</p>
          <p className="font-mono text-xs text-muted">{s.supplierCode}</p>
        </div>
      ),
    },
    {
      key: 'contact',
      header: 'Liên hệ',
      render: (s) => (
        <div className="space-y-0.5 text-xs text-muted">
          {s.contactName ? <p className="text-ink">{s.contactName}</p> : null}
          {s.email ? (
            <p className="flex items-center gap-1">
              <Mail className="size-3" aria-hidden="true" /> {s.email}
            </p>
          ) : null}
          {s.phone ? (
            <p className="flex items-center gap-1">
              <Phone className="size-3" aria-hidden="true" /> {s.phone}
            </p>
          ) : null}
        </div>
      ),
    },
    {
      key: 'skuCount',
      header: 'Số SKU',
      align: 'right',
      sortable: true,
      sortValue: (s) => s.skuCount,
      render: (s) => <span className="tnum">{s.skuCount}</span>,
    },
    {
      key: 'quoted',
      header: 'Báo giá gần nhất',
      align: 'right',
      sortable: true,
      sortValue: (s) => s.lastQuotedAt ?? '',
      render: (s) => <span className="tnum text-muted">{dateOnly(s.lastQuotedAt)}</span>,
    },
    {
      key: 'status',
      header: 'Trạng thái',
      render: (s) =>
        s.status === 'ACTIVE' ? (
          <StatusPill tone="success">Đang hợp tác</StatusPill>
        ) : (
          <StatusPill tone="neutral">Ngừng</StatusPill>
        ),
    },
  ];

  return (
    <>
      <PageHeader
        title="Nhà cung cấp"
        description="Thông tin doanh nghiệp, số SKU cung cấp và lần báo giá gần nhất."
        actions={<DemoBadge />}
      />
      <Card>
        {loading ? (
          <LoadingState />
        ) : error || !data ? (
          <ErrorState message={error ?? 'Không tải được nhà cung cấp.'} onRetry={reload} />
        ) : (
          <DataTable
            columns={columns}
            rows={data}
            rowKey={(s) => s.id}
            caption="Danh sách nhà cung cấp"
            emptyMessage="Chưa có nhà cung cấp."
          />
        )}
      </Card>
    </>
  );
}