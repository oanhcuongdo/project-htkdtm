import { ExternalLink } from 'lucide-react';
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
import { listCompetitors } from '@/mocks/api';
import type { Competitor } from '@/types/domain';

export function CompetitorsPage() {
  const { data, loading, error, reload } = useAsync(() => listCompetitors(), []);

  const columns: Column<Competitor>[] = [
    {
      key: 'name',
      header: 'Đối thủ',
      sortable: true,
      sortValue: (c) => c.name,
      render: (c) => <span className="font-medium text-ink">{c.name}</span>,
    },
    { key: 'marketplace', header: 'Sàn', render: (c) => <StatusPill tone="neutral">{c.marketplaceCode}</StatusPill> },
    {
      key: 'url',
      header: 'Gian hàng',
      render: (c) => (
        <a
          href={c.storeUrl}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
        >
          Mở <ExternalLink className="size-3" aria-hidden="true" />
        </a>
      ),
    },
    {
      key: 'status',
      header: 'Theo dõi',
      render: (c) =>
        c.status === 'TRACKING' ? (
          <StatusPill tone="success">Đang theo dõi</StatusPill>
        ) : (
          <StatusPill tone="neutral">Tạm dừng</StatusPill>
        ),
    },
  ];

  return (
    <>
      <PageHeader
        title="Đối thủ"
        description="Danh sách đối thủ và gian hàng đang theo dõi trên từng sàn."
        actions={<DemoBadge />}
      />
      <Card>
        {loading ? (
          <LoadingState />
        ) : error || !data ? (
          <ErrorState message={error ?? 'Không tải được đối thủ.'} onRetry={reload} />
        ) : (
          <DataTable
            columns={columns}
            rows={data}
            rowKey={(c) => c.id}
            caption="Danh sách đối thủ"
            emptyMessage="Chưa theo dõi đối thủ nào."
          />
        )}
      </Card>
    </>
  );
}