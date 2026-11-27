import { useState } from 'react';
import { Database, Search, TriangleAlert } from 'lucide-react';
import {
  Card,
  CardBody,
  ErrorState,
  Input,
  KpiCard,
  LoadingState,
  PageHeader,
  Select,
  StatusPill,
} from '@/components/ui/primitives';
import { DataTable, Pagination, type Column } from '@/components/ui/DataTable';
import { useAsync } from '@/hooks/useAsync';
import { useDebouncedValue } from '@/hooks/useDebouncedValue';
import {
  collectedMeta,
  collectedStats,
  listCollectedCompetitorPrices,
} from '@/mocks/api';
import { dateTime, money, percent, quantity } from '@/lib/format';
import type { CollectedCompetitorPrice } from '@/mocks/collected';

export function CompetitorCollectedPage() {
  const meta = collectedMeta();
  const stats = collectedStats();
  const categories = Object.entries(meta.categoryCounts);
  const categoryNames = new Map(Object.entries(stats.categoryNames));
  const outlierCount = stats.outlierCount;

  const [term, setTerm] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [page, setPage] = useState(1);
  const q = useDebouncedValue(term);

  const { data, loading, error, reload } = useAsync(
    () => listCollectedCompetitorPrices({ q, categoryId: categoryId || undefined, page, pageSize: 12 }),
    [q, categoryId, page],
  );

  const columns: Column<CollectedCompetitorPrice>[] = [
    {
      key: 'title',
      header: 'Sản phẩm',
      render: (r) => (
        <div className="min-w-0 max-w-md">
          <p className="truncate font-medium text-ink">{r.productTitle}</p>
          <p className="font-mono text-[11px] text-muted">{r.externalProductId}</p>
        </div>
      ),
    },
    { key: 'seller', header: 'Shop', render: (r) => <span className="text-muted">{r.sellerName}</span> },
    { key: 'category', header: 'Danh mục', render: (r) => <span className="text-xs text-muted">{r.categoryName}</span> },
    {
      key: 'listed',
      header: 'Giá gốc',
      align: 'right',
      render: (r) => <span className="tnum text-muted">{money(r.listedPrice)}</span>,
    },
    {
      key: 'effective',
      header: 'Giá bán',
      align: 'right',
      sortable: true,
      sortValue: (r) => r.effectivePrice,
      render: (r) => (
        <span className={`tnum font-medium ${r.isOutlier ? 'text-danger' : 'text-ink'}`}>
          {money(r.effectivePrice)}
        </span>
      ),
    },
    {
      key: 'discount',
      header: 'Giảm',
      align: 'right',
      render: (r) => (
        <span className="tnum text-muted">
          {r.discountPercent == null ? '—' : percent(r.discountPercent / 100, 0)}
        </span>
      ),
    },
    {
      key: 'sold',
      header: 'Đã bán',
      align: 'right',
      sortable: true,
      sortValue: (r) => r.soldCount,
      render: (r) => <span className="tnum">{quantity(r.soldCount)}</span>,
    },
    {
      key: 'sku',
      header: 'SKU',
      align: 'right',
      render: (r) => <span className="tnum text-muted">{quantity(r.skuCount)}</span>,
    },
    {
      key: 'flag',
      header: 'Cờ',
      render: (r) =>
        r.isOutlier ? <StatusPill tone="danger">Bait/Outlier</StatusPill> : r.isPromotional ? <StatusPill tone="info">Khuyến mãi</StatusPill> : <span className="text-xs text-muted">—</span>,
    },
  ];

  return (
    <>
      <PageHeader
        title="Dữ liệu đối thủ thu thập"
        description="Ảnh chụp (snapshot) dữ liệu công khai TikTok Shop VN qua API, không phải luồng realtime. Chưa map sang SKU nội bộ."
        actions={
          <>
            <StatusPill tone="neutral">SNAPSHOT</StatusPill>
            <StatusPill tone="success">
              <Database className="size-3" aria-hidden="true" />
              API · {meta.marketplaceCode}
            </StatusPill>
          </>
        }
      />

      <div className="mb-4 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Bản ghi" value={quantity(stats.total)} hint={`Thu thập ${dateTime(meta.collectedAt)}`} />
        <KpiCard label="Danh mục" value={quantity(stats.categoryCount)} hint="Nhóm SKU phụ kiện" />
        <KpiCard
          label="Bản ghi outlier"
          value={quantity(outlierCount)}
          tone="warning"
          hint="Giá ≤ 1.000 ₫ (bait) không dùng làm tín hiệu"
          icon={<TriangleAlert className="size-4" />}
        />
        <KpiCard label="Nguồn" value="ReefAPI" hint="tiktok-shop v1 · market=vn" />
      </div>

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
              placeholder="Tìm tên sản phẩm, shop, product id…"
              aria-label="Tìm dữ liệu thu thập"
              className="pl-8"
            />
          </div>
          <Select
            value={categoryId}
            onChange={(e) => {
              setCategoryId(e.target.value);
              setPage(1);
            }}
            aria-label="Lọc theo danh mục"
            className="lg:w-72"
          >
            <option value="">Tất cả danh mục</option>
            {categories.map(([id, count]) => (
              <option key={id} value={id}>
                {categoryNames.get(id) ?? id} ({count})
              </option>
            ))}
          </Select>
        </div>

        {loading && !data ? (
          <LoadingState />
        ) : error || !data ? (
          <ErrorState message={error ?? 'Không tải được dữ liệu.'} onRetry={reload} />
        ) : (
          <>
            <DataTable
              columns={columns}
              rows={data.data}
              rowKey={(r) => r.id}
              caption="Dữ liệu giá đối thủ thu thập từ TikTok Shop VN"
              emptyMessage="Không có bản ghi phù hợp."
            />
            <Pagination
              page={data.meta.page}
              totalPages={data.meta.totalPages}
              total={data.meta.total}
              onPage={setPage}
            />
          </>
        )}
      </Card>

      <CardBody className="mt-3 rounded-[var(--radius-card)] border border-border bg-surface-subtle text-xs text-muted">
        {meta.note} Nguồn: {meta.source}. Giá khuyến mãi và giá gốc được tách riêng; không dùng giá
        voucher làm giá niêm yết.
      </CardBody>
    </>
  );
}