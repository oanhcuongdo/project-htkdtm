import { useMemo } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {
  Card,
  CardBody,
  CardHeader,
  DemoBadge,
  ErrorState,
  KpiCard,
  LoadingState,
  PageHeader,
  StatusPill,
} from '@/components/ui/primitives';
import { ChartSurface, ChartTable } from '@/components/ui/chart';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { useAsync } from '@/hooks/useAsync';
import { listCompetitorPrices, listProducts } from '@/mocks/api';
import { freshness, percent } from '@/lib/format';
import type { CompetitorPrice } from '@/types/domain';

export function BiCompetitorsPage() {
  const { data, loading, error, reload } = useAsync(
    () =>
      Promise.all([
        listCompetitorPrices({ pageSize: 100 }),
        listProducts({ pageSize: 100 }),
      ]).then(([cp, products]) => ({ cp: cp.data, products: products.data })),
    [],
  );

  const gap = useMemo(() => {
    const priceBySku = new Map((data?.products ?? []).map((p) => [p.id, p.currentPrice]));
    return (data?.cp ?? [])
      .map((o) => {
        const ours = priceBySku.get(o.skuId);
        return ours ? ((ours - o.listedPrice) / o.listedPrice) * 100 : null;
      })
      .filter((v): v is number => v !== null);
  }, [data]);

  const histogram = useMemo(() => {
    const buckets = [
      { bucket: '< -20%', min: -Infinity, max: -20 },
      { bucket: '-20 → -10%', min: -20, max: -10 },
      { bucket: '-10 → 0%', min: -10, max: 0 },
      { bucket: '0 → +10%', min: 0, max: 10 },
      { bucket: '> +10%', min: 10, max: Infinity },
    ];
    return buckets.map((b) => ({
      bucket: b.bucket,
      count: gap.filter((g) => g >= b.min && g < b.max).length,
    }));
  }, [gap]);

  const stale = useMemo(
    () => (data?.cp ?? []).filter((o) => freshness(o.observedAt, 24).stale),
    [data],
  );

  const avgGap = gap.length ? gap.reduce((a, b) => a + b, 0) / gap.length / 100 : null;

  if (loading) return <LoadingState label="Đang tải dashboard đối thủ…" />;
  if (error || !data) return <ErrorState message={error ?? 'Không có dữ liệu.'} onRetry={reload} />;

  const staleColumns: Column<CompetitorPrice>[] = [
    { key: 'sku', header: 'SKU', render: (o) => <span className="font-mono text-xs">{o.skuCode}</span> },
    { key: 'product', header: 'Sản phẩm', render: (o) => <span className="line-clamp-1">{o.productName}</span> },
    { key: 'competitor', header: 'Đối thủ', render: (o) => o.competitorName },
    {
      key: 'observed',
      header: 'Quan sát',
      render: (o) => {
        const f = freshness(o.observedAt, 24);
        return <StatusPill tone={f.stale ? 'danger' : 'success'}>{f.label}</StatusPill>;
      },
    },
  ];

  return (
    <>
      <PageHeader
        title="BI · Đối thủ & Nguồn hàng"
        description="Khoảng cách giá, phân bố chênh lệch và quan sát cũ cần làm mới."
        actions={<DemoBadge />}
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Quan sát giá" value={String(data.cp.length)} />
        <KpiCard
          label="Chênh lệch TB so đối thủ"
          value={avgGap === null ? '—' : percent(avgGap, 1)}
          hint="Dương = giá ta cao hơn"
        />
        <KpiCard label="Quan sát stale (>24h)" value={String(stale.length)} tone={stale.length ? 'danger' : 'success'} />
        <KpiCard label="Outlier bị gắn cờ" value={String(data.cp.filter((o) => o.isOutlier).length)} tone="warning" />
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader title="Phân bố chênh lệch giá" subtitle="(giá ta − giá đối thủ) / giá đối thủ" />
          <CardBody>
            <ChartSurface
              label="Biểu đồ phân bố chênh lệch giá so với đối thủ theo khoảng"
              table={
                <ChartTable
                  caption="Phân bố chênh lệch giá"
                  head={['Khoảng chênh lệch', 'Số SKU']}
                  rows={histogram.map((row) => [row.bucket, row.count])}
                />
              }
            >
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={histogram} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid stroke="#E4E7EC" strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="bucket" tick={{ fontSize: 11, fill: '#667085' }} tickLine={false} axisLine={{ stroke: '#E4E7EC' }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: '#667085' }} tickLine={false} axisLine={false} width={28} />
                  <Tooltip formatter={(v: number) => [`${v} SKU`, 'Số lượng']} />
                  <Bar dataKey="count" name="SKU" fill="#1D4ED8" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </ChartSurface>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Quan sát cần làm mới" subtitle="Stale vượt ngưỡng 24 giờ" />
          <DataTable
            columns={staleColumns}
            rows={stale.slice(0, 8)}
            rowKey={(o) => o.id}
            caption="Quan sát giá cũ"
            emptyMessage="Tất cả quan sát đều còn mới."
          />
        </Card>
      </div>

      <p className="mt-3 text-xs text-muted">
        Không dùng giá stale/outlier làm tín hiệu chính (BR-005). Giá voucher không gộp vào giá
        niêm yết. Nguồn: fixture DEMO · không phải dữ liệu realtime.
      </p>
    </>
  );
}