import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Search } from 'lucide-react';
import {
  Card,
  DemoBadge,
  ErrorState,
  Input,
  LoadingState,
  PageHeader,
  Select,
  StatusPill,
} from '@/components/ui/primitives';
import { DataTable, Pagination, type Column } from '@/components/ui/DataTable';
import { useAsync } from '@/hooks/useAsync';
import { useDebouncedValue } from '@/hooks/useDebouncedValue';
import { listRecommendations } from '@/mocks/api';
import { money, percent, signedPercent } from '@/lib/format';
import { dataQuality, recommendationStatus } from '@/lib/status';
import type { Recommendation } from '@/types/domain';

export function RecommendationsPage() {
  const [status, setStatus] = useState('');
  const [term, setTerm] = useState('');
  const [page, setPage] = useState(1);
  const q = useDebouncedValue(term);

  const { data, loading, error, reload } = useAsync(
    () => listRecommendations({ status: status || undefined, q, page, pageSize: 10 }),
    [status, q, page],
  );

  const columns: Column<Recommendation>[] = [
    {
      key: 'id',
      header: 'Mã',
      render: (r) => (
        <Link to={`/pricing/recommendations/${r.id}`} className="font-mono text-xs font-medium text-primary hover:underline">
          {r.id}
        </Link>
      ),
    },
    {
      key: 'sku',
      header: 'SKU',
      sortable: true,
      sortValue: (r) => r.skuCode,
      render: (r) => <span className="font-mono text-xs">{r.skuCode}</span>,
    },
    { key: 'channel', header: 'Kênh', render: (r) => <span className="text-muted">{r.channelName}</span> },
    {
      key: 'old',
      header: 'Giá cũ',
      align: 'right',
      render: (r) => <span className="tnum text-muted">{money(r.currentPrice)}</span>,
    },
    {
      key: 'new',
      header: 'Đề xuất',
      align: 'right',
      sortable: true,
      sortValue: (r) => r.recommendedPrice,
      render: (r) => <span className="tnum font-medium">{money(r.recommendedPrice)}</span>,
    },
    {
      key: 'delta',
      header: 'Δ',
      align: 'right',
      render: (r) => {
        const d = (r.recommendedPrice - r.currentPrice) / r.currentPrice;
        return (
          <span className={`tnum ${d >= 0 ? 'text-success' : 'text-danger'}`}>
            {signedPercent(d, 1)}
          </span>
        );
      },
    },
    {
      key: 'floor',
      header: 'Giá sàn',
      align: 'right',
      render: (r) => <span className="tnum text-muted">{money(r.floorPrice)}</span>,
    },
    {
      key: 'margin',
      header: 'Biên',
      align: 'right',
      render: (r) => <span className="tnum">{percent(r.expectedMargin, 1)}</span>,
    },
    {
      key: 'createdBy',
      header: 'Người tạo',
      render: (r) => <span className="text-muted">{r.createdBy}</span>,
    },
    {
      key: 'quality',
      header: 'Chất lượng',
      render: (r) => {
        const dq = dataQuality(r.dataQuality);
        return <StatusPill tone={dq.tone}>{dq.label}</StatusPill>;
      },
    },
    {
      key: 'status',
      header: 'Trạng thái',
      render: (r) => {
        const s = recommendationStatus(r.status);
        return <StatusPill tone={s.tone}>{s.label}</StatusPill>;
      },
    },
  ];

  return (
    <>
      <PageHeader
        title="Đề xuất giá"
        description="Danh sách đề xuất từ engine. Mở chi tiết để xem snapshot, giải thích và phê duyệt."
        actions={<DemoBadge />}
      />

      <Card>
        <div className="flex flex-col gap-3 border-b border-border p-4 lg:flex-row lg:items-center">
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted" aria-hidden="true" />
            <Input
              value={term}
              onChange={(e) => {
                setTerm(e.target.value);
                setPage(1);
              }}
              placeholder="Tìm mã, SKU, sản phẩm…"
              aria-label="Tìm đề xuất"
              className="pl-8"
            />
          </div>
          <Select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
            aria-label="Lọc theo trạng thái"
            className="lg:w-52"
          >
            <option value="">Mọi trạng thái</option>
            <option value="PENDING_APPROVAL">Chờ duyệt</option>
            <option value="APPROVED">Đã duyệt</option>
            <option value="EXECUTED">Đã thực thi</option>
            <option value="DRAFT">Nháp</option>
            <option value="EXECUTION_QUEUED">Chờ thực thi</option>
            <option value="REJECTED">Từ chối</option>
            <option value="EXPIRED">Hết hạn</option>
          </Select>
        </div>

        {loading && !data ? (
          <LoadingState />
        ) : error || !data ? (
          <ErrorState message={error ?? 'Không tải được đề xuất.'} onRetry={reload} />
        ) : (
          <>
            <DataTable
              columns={columns}
              rows={data.data}
              rowKey={(r) => r.id}
              caption="Danh sách đề xuất giá"
              emptyMessage="Không có đề xuất phù hợp."
            />
            <Pagination
              page={data.meta.page}
              totalPages={data.meta.totalPages}
              total={data.meta.total}
              onPage={setPage}
            />
          </>
        )}
        {loading && data ? (
          <p className="px-4 pb-2 text-xs text-muted" role="status">
            Đang cập nhật…
          </p>
        ) : null}
      </Card>
    </>
  );
}