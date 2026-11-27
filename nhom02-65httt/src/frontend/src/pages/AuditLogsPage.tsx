import { useState } from 'react';
import {
  Card,
  DemoBadge,
  ErrorState,
  LoadingState,
  PageHeader,
  StatusPill,
} from '@/components/ui/primitives';
import { DataTable, Pagination, type Column } from '@/components/ui/DataTable';
import { useAsync } from '@/hooks/useAsync';
import { listAuditLogs } from '@/mocks/api';
import { dateTime } from '@/lib/format';
import type { AuditLog } from '@/types/domain';

export function AuditLogsPage() {
  const [page, setPage] = useState(1);
  const { data, loading, error, reload } = useAsync(() => listAuditLogs(page, 10), [page]);

  const columns: Column<AuditLog>[] = [
    { key: 'time', header: 'Thời điểm', sortable: true, sortValue: (a) => a.createdAt, render: (a) => <span className="tnum text-muted">{dateTime(a.createdAt)}</span> },
    { key: 'actor', header: 'Người thực hiện', render: (a) => <span className="font-medium">{a.actor}</span> },
    { key: 'action', header: 'Hành động', render: (a) => <StatusPill tone="info">{a.action}</StatusPill> },
    { key: 'resource', header: 'Tài nguyên', render: (a) => <span className="font-mono text-xs text-muted">{a.resourceType}</span> },
    {
      key: 'change',
      header: 'Trước → Sau',
      render: (a) => (
        <span className="text-xs text-muted">
          {a.beforeSummary ?? '—'} → {a.afterSummary ?? '—'}
        </span>
      ),
    },
    { key: 'reason', header: 'Lý do', render: (a) => <span className="text-muted">{a.reason ?? '—'}</span> },
    {
      key: 'requestId',
      header: 'Request ID',
      render: (a) => <span className="font-mono text-[11px] text-muted">{a.requestId}</span>,
    },
  ];

  return (
    <>
      <PageHeader
        title="Nhật ký hoạt động"
        description="Audit log append-only cho thao tác giá, tồn kho, quy tắc và phân quyền, kèm request ID để đối chiếu."
        actions={<DemoBadge />}
      />
      <Card>
        {loading ? (
          <LoadingState />
        ) : error || !data ? (
          <ErrorState message={error ?? 'Không tải được nhật ký.'} onRetry={reload} />
        ) : (
          <>
            <DataTable
              columns={columns}
              rows={data.data}
              rowKey={(a) => a.id}
              caption="Audit logs"
              emptyMessage="Chưa có bản ghi."
            />
            <Pagination page={data.meta.page} totalPages={data.meta.totalPages} total={data.meta.total} onPage={setPage} />
          </>
        )}
      </Card>
    </>
  );
}