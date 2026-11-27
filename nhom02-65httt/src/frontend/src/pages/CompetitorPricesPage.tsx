import { useState } from 'react';
import { Search, Upload } from 'lucide-react';
import {
  Button,
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
import { listCompetitorPrices } from '@/mocks/api';
import { freshness, money, percent } from '@/lib/format';
import type { CompetitorPrice } from '@/types/domain';

export function CompetitorPricesPage() {
  const [term, setTerm] = useState('');
  const [marketplace, setMarketplace] = useState('');
  const [sourceType, setSourceType] = useState('');
  const [staleOnly, setStaleOnly] = useState(false);
  const [page, setPage] = useState(1);
  const q = useDebouncedValue(term);

  const { data, loading, error, reload } = useAsync(
    () =>
      listCompetitorPrices({
        q,
        marketplace: marketplace || undefined,
        sourceType: sourceType || undefined,
        staleOnly,
        page,
        pageSize: 10,
      }),
    [q, marketplace, sourceType, staleOnly, page],
  );

  const columns: Column<CompetitorPrice>[] = [
    {
      key: 'sku',
      header: 'SKU',
      sortable: true,
      sortValue: (p) => p.skuCode,
      render: (p) => <span className="font-mono text-xs font-medium">{p.skuCode}</span>,
    },
    { key: 'product', header: 'Sản phẩm', render: (p) => <span className="line-clamp-1">{p.productName}</span> },
    { key: 'competitor', header: 'Đối thủ', render: (p) => <span className="text-muted">{p.competitorName}</span> },
    {
      key: 'market',
      header: 'Sàn',
      render: (p) => <StatusPill tone="neutral">{p.marketplaceCode}</StatusPill>,
    },
    {
      key: 'listed',
      header: 'Giá niêm yết',
      align: 'right',
      sortable: true,
      sortValue: (p) => p.listedPrice,
      render: (p) => <span className="tnum">{money(p.listedPrice)}</span>,
    },
    {
      key: 'effective',
      header: 'Giá hiệu lực',
      align: 'right',
      render: (p) => <span className="tnum text-muted">{money(p.effectivePrice)}</span>,
    },
    {
      key: 'source',
      header: 'Nguồn',
      render: (p) => (
        <div className="text-xs">
          <p className="font-medium text-ink">{p.sourceType}</p>
          <p className="text-muted">{p.sourceName}</p>
        </div>
      ),
    },
    {
      key: 'freshness',
      header: 'Độ tươi',
      render: (p) => {
        const f = freshness(p.observedAt, 24);
        return (
          <div className="space-y-1">
            <StatusPill tone={f.stale ? 'danger' : 'success'}>
              {f.stale ? 'Stale' : 'Fresh'}
            </StatusPill>
            <p className="text-xs text-muted">{f.label}</p>
          </div>
        );
      },
    },
    {
      key: 'confidence',
      header: 'Tin cậy',
      align: 'right',
      render: (p) => <span className="tnum text-muted">{percent(p.confidence, 0)}</span>,
    },
    {
      key: 'flag',
      header: 'Cờ',
      render: (p) =>
        p.isOutlier ? (
          <StatusPill tone="warning">Outlier</StatusPill>
        ) : (
          <span className="text-xs text-muted">—</span>
        ),
    },
  ];

  return (
    <>
      <PageHeader
        title="Theo dõi giá đối thủ"
        description="Mỗi quan sát có nguồn, thời điểm và độ tin cậy. Stale/outlier luôn có nhãn chữ, không chỉ dựa vào màu."
        actions={
          <>
            <DemoBadge />
            <Button
              variant="secondary"
              size="sm"
              disabled
              title="Chưa khả dụng trong bản demo — cần API import CSV"
            >
              <Upload className="size-4" aria-hidden="true" />
              Import CSV
            </Button>
          </>
        }
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
              placeholder="Tìm SKU, sản phẩm, đối thủ…"
              aria-label="Tìm giá đối thủ"
              className="pl-8"
            />
          </div>
          <Select
            value={marketplace}
            onChange={(e) => {
              setMarketplace(e.target.value);
              setPage(1);
            }}
            aria-label="Lọc theo sàn"
            className="lg:w-44"
          >
            <option value="">Tất cả sàn</option>
            <option value="SHOPEE">Shopee</option>
            <option value="TIKTOK_SHOP">TikTok Shop</option>
            <option value="LAZADA">Lazada</option>
          </Select>
          <Select
            value={sourceType}
            onChange={(e) => {
              setSourceType(e.target.value);
              setPage(1);
            }}
            aria-label="Lọc theo nguồn dữ liệu"
            className="lg:w-44"
          >
            <option value="">Mọi nguồn</option>
            <option value="DEMO">DEMO</option>
            <option value="CSV">CSV</option>
            <option value="MANUAL">Nhập tay</option>
            <option value="API">API</option>
          </Select>
          <label className="flex items-center gap-2 whitespace-nowrap text-sm text-ink">
            <input
              type="checkbox"
              checked={staleOnly}
              onChange={(e) => {
                setStaleOnly(e.target.checked);
                setPage(1);
              }}
              className="size-4 rounded border-border accent-[var(--color-primary)]"
            />
            Chỉ hiện stale
          </label>
        </div>

        {loading && !data ? (
          <LoadingState />
        ) : error || !data ? (
          <ErrorState message={error ?? 'Không tải được giá đối thủ.'} onRetry={reload} />
        ) : (
          <>
            <DataTable
              columns={columns}
              rows={data.data}
              rowKey={(p) => p.id}
              caption="Quan sát giá đối thủ"
              emptyMessage="Không có quan sát giá phù hợp."
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

      <p className="mt-3 text-xs text-muted">
        Ngưỡng stale mặc định 24 giờ (BUSINESS_RULES §8). Không cộng giá voucher vào giá niêm yết.
      </p>
    </>
  );
}
