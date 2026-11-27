import { useMemo, useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
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
  Select,
} from '@/components/ui/primitives';
import { ChartLegend, ChartSurface, ChartTable } from '@/components/ui/chart';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { useAsync } from '@/hooks/useAsync';
import { getDashboard, listProducts } from '@/mocks/api';
import { dateOnly, money, percent, quantity } from '@/lib/format';
import type { Product } from '@/types/domain';

const REVENUE_COLOR = '#1D4ED8';
const PROFIT_COLOR = '#15803D';

function Tip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: { value: number; name: string }[];
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-[var(--radius-control)] border border-border bg-surface px-3 py-2 text-xs shadow-lg">
      <p className="mb-1 font-medium text-ink">{label}</p>
      {payload.map((p) => (
        <p key={p.name} className="tnum text-muted">
          {p.name}: {money(p.value)}
        </p>
      ))}
    </div>
  );
}

export function BiProfitabilityPage() {
  const [windowDays, setWindowDays] = useState<'7' | '14'>('14');
  const { data, loading, error, reload } = useAsync(
    () => Promise.all([getDashboard(), listProducts({ pageSize: 100 })]).then(([d, p]) => ({ d, p })),
    [],
  );

  const marginByCategory = useMemo(() => {
    const products = data?.p.data ?? [];
    const map = new Map<string, { sum: number; n: number }>();
    for (const p of products) {
      const margin = (p.currentPrice - p.unitCost) / p.currentPrice;
      const cur = map.get(p.categoryName) ?? { sum: 0, n: 0 };
      map.set(p.categoryName, { sum: cur.sum + margin, n: cur.n + 1 });
    }
    return [...map.entries()].map(([category, v]) => ({
      category,
      margin: v.n ? v.sum / v.n : 0,
    }));
  }, [data]);

  const ranked: Product[] = useMemo(() => {
    const products = data?.p.data ?? [];
    return [...products].sort(
      (a, b) =>
        (b.currentPrice - b.unitCost) / b.currentPrice -
        (a.currentPrice - a.unitCost) / a.currentPrice,
    );
  }, [data]);

  const avgProfitPerUnit = useMemo(() => {
    const products = data?.p.data ?? [];
    if (products.length === 0) return null;
    return (
      products.reduce((sum, p) => sum + (p.currentPrice - p.unitCost), 0) /
      products.length
    );
  }, [data]);

  if (loading && !data) return <LoadingState label="Đang tải dashboard lợi nhuận…" />;
  if (error || !data) return <ErrorState message={error ?? 'Không có dữ liệu.'} onRetry={reload} />;

  const { d } = data;
  const trend = d.revenueTrend.slice(-Number(windowDays));

  const columns: Column<Product>[] = [
    { key: 'sku', header: 'SKU', render: (p) => <span className="font-mono text-xs">{p.skuCode}</span> },
    { key: 'name', header: 'Sản phẩm', render: (p) => <span className="line-clamp-1">{p.name}</span> },
    {
      key: 'profit',
      header: 'Lợi nhuận/đơn vị',
      align: 'right',
      sortable: true,
      sortValue: (p) => p.currentPrice - p.unitCost,
      render: (p) => <span className="tnum">{money(p.currentPrice - p.unitCost)}</span>,
    },
    {
      key: 'margin',
      header: 'Biên ước tính',
      align: 'right',
      sortable: true,
      sortValue: (p) => (p.currentPrice - p.unitCost) / p.currentPrice,
      render: (p) => <span className="tnum font-medium">{percent((p.currentPrice - p.unitCost) / p.currentPrice, 1)}</span>,
    },
  ];

  return (
    <>
      <PageHeader
        title="BI · Lợi nhuận"
        description="Lợi nhuận đóng góp ước tính theo cấu hình phí và giá vốn. Không phải lợi nhuận kế toán."
        actions={<DemoBadge />}
      />

      <div className="mb-4 flex flex-wrap items-center gap-2 text-xs text-muted">
        <label htmlFor="bi-window" className="font-medium text-ink">
          Khoảng thời gian
        </label>
        <Select
          id="bi-window"
          value={windowDays}
          onChange={(e) => setWindowDays(e.target.value as '7' | '14')}
          className="h-8 w-40"
        >
          <option value="7">7 ngày gần nhất</option>
          <option value="14">14 ngày gần nhất</option>
        </Select>
        <span>· Nguồn: fixture DEMO Sales · không phải dữ liệu realtime</span>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <KpiCard label="Doanh thu (DEMO Sales)" value={money(d.revenue)} />
        <KpiCard label="Lợi nhuận gộp ước tính" value={money(d.grossProfit)} />
        <KpiCard label="Lợi nhuận/đơn vị TB" value={money(avgProfitPerUnit)} />
        <KpiCard label="Biên lợi nhuận" value={percent(d.margin)} />
        <KpiCard
          label="SKU dưới giá sàn"
          value={quantity(d.skusBelowFloor)}
          tone={d.skusBelowFloor === 0 ? 'success' : 'danger'}
        />
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader title="Lợi nhuận theo kênh" subtitle="VND · DEMO" />
          <CardBody>
            <ChartSurface
              label="Biểu đồ lợi nhuận ước tính theo kênh bán"
              table={
                <ChartTable
                  caption="Lợi nhuận ước tính theo kênh"
                  head={['Kênh', 'Lợi nhuận']}
                  rows={d.profitByChannel.map((row) => [row.channel, money(row.profit)])}
                />
              }
            >
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={d.profitByChannel} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid stroke="#E4E7EC" strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="channel" tick={{ fontSize: 11, fill: '#667085' }} tickLine={false} axisLine={{ stroke: '#E4E7EC' }} />
                  <YAxis tickFormatter={(v: number) => `${Math.round(v / 1e6)}tr`} tick={{ fontSize: 11, fill: '#667085' }} tickLine={false} axisLine={false} width={44} />
                  <Tooltip content={<Tip />} />
                  <Bar dataKey="profit" name="Lợi nhuận" radius={[4, 4, 0, 0]}>
                    {d.profitByChannel.map((entry, i) => (
                      <Cell key={entry.channel} fill={i === 0 ? REVENUE_COLOR : '#93A9E8'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </ChartSurface>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Biên theo danh mục" subtitle="Trung bình ước tính" />
          <CardBody>
            <ChartSurface
              label="Biểu đồ biên lợi nhuận trung bình theo danh mục"
              table={
                <ChartTable
                  caption="Biên lợi nhuận trung bình theo danh mục"
                  head={['Danh mục', 'Biên']}
                  rows={marginByCategory.map((row) => [row.category, percent(row.margin, 1)])}
                />
              }
            >
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={marginByCategory} layout="vertical" margin={{ left: 8, right: 8 }}>
                  <CartesianGrid stroke="#E4E7EC" strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" tickFormatter={(v: number) => `${Math.round(v * 100)}%`} tick={{ fontSize: 11, fill: '#667085' }} tickLine={false} axisLine={false} />
                  <YAxis type="category" dataKey="category" tick={{ fontSize: 11, fill: '#667085' }} tickLine={false} axisLine={false} width={76} />
                  <Tooltip formatter={(v: number) => percent(v, 1)} />
                  <Bar dataKey="margin" name="Biên" fill={PROFIT_COLOR} radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </ChartSurface>
          </CardBody>
        </Card>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader title="Xu hướng doanh thu & lợi nhuận" subtitle={`${windowDays} ngày · DEMO Sales`} />
          <CardBody>
            <ChartLegend
              items={[
                { label: 'Doanh thu', color: REVENUE_COLOR },
                { label: 'Lợi nhuận', color: PROFIT_COLOR },
              ]}
            />
            <ChartSurface
              label={`Biểu đồ doanh thu và lợi nhuận ${windowDays} ngày`}
              height={224}
              table={
                <ChartTable
                  caption="Doanh thu và lợi nhuận theo ngày"
                  head={['Ngày', 'Doanh thu', 'Lợi nhuận']}
                  rows={trend.map((row) => [dateOnly(row.date), money(row.revenue), money(row.profit)])}
                />
              }
            >
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trend} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid stroke="#E4E7EC" strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="date" tickFormatter={(v: string) => dateOnly(v).slice(0, 5)} tick={{ fontSize: 11, fill: '#667085' }} tickLine={false} axisLine={{ stroke: '#E4E7EC' }} />
                  <YAxis tickFormatter={(v: number) => `${Math.round(v / 1e6)}tr`} tick={{ fontSize: 11, fill: '#667085' }} tickLine={false} axisLine={false} width={44} />
                  <Tooltip content={<Tip />} />
                  <Line type="monotone" dataKey="revenue" name="Doanh thu" stroke={REVENUE_COLOR} strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="profit" name="Lợi nhuận" stroke={PROFIT_COLOR} strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </ChartSurface>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Xếp hạng SKU theo biên" subtitle="Cao nhất trước" />
          <DataTable
            columns={columns}
            rows={ranked.slice(0, 6)}
            rowKey={(p) => p.id}
            caption="SKU theo biên lợi nhuận"
          />
        </Card>
      </div>
    </>
  );
}
