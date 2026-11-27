import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertTriangle,
  ArrowRight,
  Boxes,
  CircleDollarSign,
  Clock,
  Percent,
  ShieldAlert,
  TrendingDown,
  TrendingUp,
} from 'lucide-react';
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
  StatusPill,
} from '@/components/ui/primitives';
import { ChartLegend, ChartSurface, ChartTable } from '@/components/ui/chart';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { useAsync } from '@/hooks/useAsync';
import {
  getDashboard,
  listExecutions,
  listInventory,
  listRecommendations,
} from '@/mocks/api';
import { dateOnly, dateTime, money, percent, quantity, signedPercent } from '@/lib/format';
import { executionStatus } from '@/lib/status';
import type {
  ExecutionRun,
  InventoryBalance,
  Recommendation,
} from '@/types/domain';

const REVENUE_COLOR = '#1D4ED8';
const PROFIT_COLOR = '#15803D';

function ChartTooltip({
  active,
  payload,
  label,
  kind,
}: {
  active?: boolean;
  payload?: { value: number; name: string }[];
  label?: string;
  kind: 'money' | 'count';
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-[var(--radius-control)] border border-border bg-surface px-3 py-2 text-xs shadow-lg">
      <p className="mb-1 font-medium text-ink">{label}</p>
      {payload.map((p) => (
        <p key={p.name} className="tnum text-muted">
          {p.name}: {kind === 'money' ? money(p.value) : quantity(p.value)}
        </p>
      ))}
    </div>
  );
}

/** Period-over-period change, computed from the trend series (no fake %). */
function DeltaHint({ value }: { value: number | null }) {
  if (value === null) return <span>Chưa đủ dữ liệu so sánh</span>;
  const up = value >= 0;
  const Icon = up ? TrendingUp : TrendingDown;
  return (
    <span className={up ? 'text-success' : 'text-danger'}>
      <Icon className="mr-1 inline size-3.5" aria-hidden="true" />
      {signedPercent(Math.abs(value))} so với 7 ngày trước
    </span>
  );
}

export function DashboardPage() {
  const [windowDays, setWindowDays] = useState<'7' | '14'>('14');

  const { data, loading, error, reload } = useAsync(
    () =>
      Promise.all([
        getDashboard(),
        listRecommendations({ status: 'PENDING_APPROVAL', pageSize: 5 }),
        listInventory(),
        listExecutions({ pageSize: 100 }),
      ]).then(([summary, pending, inventory, executions]) => ({
        summary,
        pending,
        inventory,
        executions,
      })),
    [],
  );

  const derived = useMemo(() => {
    const trend = data?.summary.revenueTrend ?? [];
    // Last 7 days vs the 7 days before that, always over the 14-day series.
    const half = Math.floor(trend.length / 2);
    const previous = trend.slice(0, half);
    const recent = trend.slice(half);
    const sum = (rows: typeof trend, key: 'revenue' | 'profit') =>
      rows.reduce((total, row) => total + row[key], 0);
    const delta = (key: 'revenue' | 'profit') => {
      const before = sum(previous, key);
      const after = sum(recent, key);
      return before > 0 ? (after - before) / before : null;
    };
    return {
      revenueDelta: delta('revenue'),
      profitDelta: delta('profit'),
      trendWindow: trend.slice(-Number(windowDays)),
      recentChanges: (data?.executions.data ?? [])
        .filter((e) => e.status === 'SUCCEEDED')
        .sort((a, b) => b.createdAt.localeCompare(a.createdAt))
        .slice(0, 5),
      lowStock: (data?.inventory ?? [])
        .filter((i) => i.onHandQty - i.reservedQty <= i.reorderPoint)
        .slice(0, 5),
    };
  }, [data, windowDays]);

  if (loading && !data) return <LoadingState label="Đang tải tổng quan…" />;
  if (error || !data) return <ErrorState message={error ?? 'Không có dữ liệu.'} onRetry={reload} />;

  const { summary, pending } = data;

  const pendingColumns: Column<Recommendation>[] = [
    {
      key: 'sku',
      header: 'SKU',
      render: (r) => (
        <Link to={`/pricing/recommendations/${r.id}`} className="font-medium text-primary hover:underline">
          {r.skuCode}
        </Link>
      ),
    },
    { key: 'product', header: 'Sản phẩm', render: (r) => <span className="line-clamp-1">{r.productName}</span> },
    { key: 'channel', header: 'Kênh', render: (r) => r.channelName },
    {
      key: 'recommended',
      header: 'Giá đề xuất',
      align: 'right',
      render: (r) => <span className="tnum">{money(r.recommendedPrice)}</span>,
    },
    {
      key: 'margin',
      header: 'Biên',
      align: 'right',
      render: (r) => <span className="tnum">{percent(r.expectedMargin, 1)}</span>,
    },
    {
      key: 'status',
      header: 'Trạng thái',
      render: () => <StatusPill tone="warning">Chờ duyệt</StatusPill>,
    },
  ];

  const lowStockColumns: Column<InventoryBalance>[] = [
    { key: 'sku', header: 'SKU', render: (i) => <span className="font-medium">{i.skuCode}</span> },
    { key: 'product', header: 'Sản phẩm', render: (i) => <span className="line-clamp-1">{i.productName}</span> },
    { key: 'warehouse', header: 'Kho', render: (i) => i.warehouseName },
    {
      key: 'available',
      header: 'Khả dụng',
      align: 'right',
      render: (i) => (
        <span className="tnum font-medium text-danger">
          {quantity(i.onHandQty - i.reservedQty)}
        </span>
      ),
    },
    {
      key: 'reorder',
      header: 'Ngưỡng',
      align: 'right',
      render: (i) => <span className="tnum text-muted">{quantity(i.reorderPoint)}</span>,
    },
  ];

  const changeColumns: Column<ExecutionRun>[] = [
    { key: 'sku', header: 'SKU', render: (e) => <span className="font-mono text-xs">{e.skuCode}</span> },
    { key: 'channel', header: 'Kênh', render: (e) => <span className="text-muted">{e.channelName}</span> },
    {
      key: 'mode',
      header: 'Chế độ',
      render: (e) => (
        <StatusPill tone={e.mode === 'LIVE' ? 'danger' : 'info'}>{e.mode}</StatusPill>
      ),
    },
    {
      key: 'from',
      header: 'Giá cũ',
      align: 'right',
      render: (e) => <span className="tnum text-muted">{money(e.previousPrice)}</span>,
    },
    {
      key: 'to',
      header: 'Giá mới',
      align: 'right',
      render: (e) => <span className="tnum font-medium">{money(e.requestedPrice)}</span>,
    },
    {
      key: 'status',
      header: 'Kết quả',
      render: (e) => {
        const s = executionStatus(e.status);
        return <StatusPill tone={s.tone}>{s.label}</StatusPill>;
      },
    },
    {
      key: 'time',
      header: 'Thời điểm',
      align: 'right',
      render: (e) => <span className="tnum text-muted">{dateTime(e.createdAt)}</span>,
    },
  ];

  return (
    <>
      <PageHeader
        title="Tổng quan"
        description="Tình hình kinh doanh và các điểm cần can thiệp về giá và tồn kho."
        actions={<DemoBadge />}
      />

      <div className="mb-4 flex flex-wrap items-center gap-2 text-xs text-muted">
        <label htmlFor="dashboard-window" className="font-medium text-ink">
          Khoảng thời gian
        </label>
        <Select
          id="dashboard-window"
          value={windowDays}
          onChange={(e) => setWindowDays(e.target.value as '7' | '14')}
          className="h-8 w-40"
        >
          <option value="7">7 ngày gần nhất</option>
          <option value="14">14 ngày gần nhất</option>
        </Select>
        <span>· Dữ liệu doanh thu là fixture DEMO, không suy ra từ giá niêm yết</span>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <KpiCard
          label="Doanh thu (DEMO)"
          value={money(summary.revenue)}
          hint={<DeltaHint value={derived.revenueDelta} />}
          icon={<CircleDollarSign className="size-4" />}
        />
        <KpiCard
          label="Lợi nhuận gộp ước tính"
          value={money(summary.grossProfit)}
          hint={<DeltaHint value={derived.profitDelta} />}
          icon={<Percent className="size-4" />}
        />
        <KpiCard
          label="Biên lợi nhuận"
          value={percent(summary.margin)}
          hint="Ước tính theo cấu hình phí và giá vốn"
          icon={<Percent className="size-4" />}
        />
        <KpiCard
          label="SKU dưới giá sàn"
          value={quantity(summary.skusBelowFloor)}
          tone={summary.skusBelowFloor === 0 ? 'success' : 'danger'}
          hint={
            summary.skusBelowFloor === 0
              ? 'Margin Guard đang hoạt động'
              : 'Cần điều tra ngay'
          }
          icon={<ShieldAlert className="size-4" />}
        />
        <KpiCard
          label="Cảnh báo tồn kho"
          value={quantity(summary.lowStockCount)}
          tone={summary.lowStockCount === 0 ? 'success' : 'danger'}
          hint={
            summary.lowStockCount === 0
              ? 'Không có SKU dưới ngưỡng'
              : 'Xem danh sách bên dưới'
          }
          icon={<AlertTriangle className="size-4" />}
        />
        <KpiCard
          label="Chờ duyệt"
          value={quantity(summary.pendingApprovals)}
          tone="warning"
          hint={
            <Link to="/pricing/recommendations" className="text-primary hover:underline">
              Xem hàng chờ duyệt
            </Link>
          }
          icon={<Clock className="size-4" />}
        />
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader
            title="Doanh thu & lợi nhuận theo ngày"
            subtitle={`${windowDays} ngày gần nhất · VND · dữ liệu DEMO`}
          />
          <CardBody>
            <ChartLegend
              items={[
                { label: 'Doanh thu', color: REVENUE_COLOR },
                { label: 'Lợi nhuận', color: PROFIT_COLOR },
              ]}
            />
            <ChartSurface
              label={`Biểu đồ doanh thu và lợi nhuận ${windowDays} ngày gần nhất`}
              table={
                <ChartTable
                  caption="Dữ liệu doanh thu và lợi nhuận theo ngày"
                  head={['Ngày', 'Doanh thu', 'Lợi nhuận']}
                  rows={derived.trendWindow.map((row) => [
                    dateOnly(row.date),
                    money(row.revenue),
                    money(row.profit),
                  ])}
                />
              }
            >
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={derived.trendWindow} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
                  <CartesianGrid stroke="#E4E7EC" strokeDasharray="3 3" vertical={false} />
                  <XAxis
                    dataKey="date"
                    tickFormatter={(v: string) => dateOnly(v).slice(0, 5)}
                    tick={{ fontSize: 11, fill: '#667085' }}
                    tickLine={false}
                    axisLine={{ stroke: '#E4E7EC' }}
                  />
                  <YAxis
                    tickFormatter={(v: number) => `${Math.round(v / 1e6)}tr`}
                    tick={{ fontSize: 11, fill: '#667085' }}
                    tickLine={false}
                    axisLine={false}
                    width={44}
                  />
                  <Tooltip content={<ChartTooltip kind="money" />} />
                  <Line
                    type="monotone"
                    dataKey="revenue"
                    name="Doanh thu"
                    stroke={REVENUE_COLOR}
                    strokeWidth={2}
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="profit"
                    name="Lợi nhuận"
                    stroke={PROFIT_COLOR}
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </ChartSurface>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Lợi nhuận theo kênh" subtitle="Ước tính · VND" />
          <CardBody>
            <ChartSurface
              label="Biểu đồ lợi nhuận ước tính theo kênh bán"
              table={
                <ChartTable
                  caption="Lợi nhuận ước tính theo kênh"
                  head={['Kênh', 'Lợi nhuận']}
                  rows={summary.profitByChannel.map((row) => [row.channel, money(row.profit)])}
                />
              }
            >
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={summary.profitByChannel} layout="vertical" margin={{ left: 8, right: 8 }}>
                  <CartesianGrid stroke="#E4E7EC" strokeDasharray="3 3" horizontal={false} />
                  <XAxis
                    type="number"
                    tickFormatter={(v: number) => `${Math.round(v / 1e6)}tr`}
                    tick={{ fontSize: 11, fill: '#667085' }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    type="category"
                    dataKey="channel"
                    tick={{ fontSize: 11, fill: '#667085' }}
                    tickLine={false}
                    axisLine={false}
                    width={72}
                  />
                  <Tooltip content={<ChartTooltip kind="money" />} />
                  <Bar dataKey="profit" name="Lợi nhuận" radius={[0, 4, 4, 0]}>
                    {summary.profitByChannel.map((entry, i) => (
                      <Cell key={entry.channel} fill={i === 0 ? REVENUE_COLOR : '#93A9E8'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </ChartSurface>
          </CardBody>
        </Card>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-3">
        <Card>
          <CardHeader
            title="Vị thế giá so với đối thủ"
            subtitle="Số SKU theo chênh lệch giá"
          />
          <CardBody>
            <ChartSurface
              label="Biểu đồ số SKU thấp hơn, tương đương hoặc cao hơn giá đối thủ"
              table={
                <ChartTable
                  caption="Vị thế giá so với đối thủ"
                  head={['Vị thế', 'Số SKU']}
                  rows={summary.priceVsCompetitor.map((row) => [row.bucket, row.count])}
                />
              }
            >
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={summary.priceVsCompetitor} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid stroke="#E4E7EC" strokeDasharray="3 3" vertical={false} />
                  <XAxis
                    dataKey="bucket"
                    tick={{ fontSize: 11, fill: '#667085' }}
                    tickLine={false}
                    axisLine={{ stroke: '#E4E7EC' }}
                  />
                  <YAxis
                    allowDecimals={false}
                    tick={{ fontSize: 11, fill: '#667085' }}
                    tickLine={false}
                    axisLine={false}
                    width={28}
                  />
                  <Tooltip content={<ChartTooltip kind="count" />} />
                  <Bar dataKey="count" name="Số SKU" fill={REVENUE_COLOR} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </ChartSurface>
          </CardBody>
        </Card>

        <Card className="xl:col-span-2">
          <CardHeader
            title="Thay đổi giá gần đây"
            subtitle="Các lần thực thi thành công (mô phỏng)"
            action={
              <Link
                to="/automation/runs"
                className="inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline"
              >
                Tất cả <ArrowRight className="size-3.5" aria-hidden="true" />
              </Link>
            }
          />
          <DataTable
            columns={changeColumns}
            rows={derived.recentChanges}
            rowKey={(e) => e.id}
            caption="Thay đổi giá gần đây"
            emptyMessage="Chưa có thay đổi giá nào."
          />
        </Card>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader
            title="Đề xuất cần duyệt"
            subtitle={`${pending.meta.total} đề xuất đang chờ`}
            action={
              <Link
                to="/pricing/recommendations"
                className="inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline"
              >
                Tất cả <ArrowRight className="size-3.5" aria-hidden="true" />
              </Link>
            }
          />
          <DataTable
            columns={pendingColumns}
            rows={pending.data}
            rowKey={(r) => r.id}
            caption="Đề xuất giá cần duyệt"
            emptyMessage="Không có đề xuất nào chờ duyệt."
          />
        </Card>

        <Card>
          <CardHeader
            title="Cảnh báo tồn kho"
            subtitle={`${summary.lowStockCount} SKU dưới ngưỡng`}
            action={<Boxes className="size-4 text-muted" aria-hidden="true" />}
          />
          <DataTable
            columns={lowStockColumns}
            rows={derived.lowStock}
            rowKey={(i) => i.id}
            caption="SKU tồn thấp"
            emptyMessage="Không có cảnh báo tồn kho."
          />
          <div className="flex items-start gap-2 border-t border-border px-4 py-3 text-xs text-muted">
            <AlertTriangle className="mt-0.5 size-3.5 shrink-0 text-warning" aria-hidden="true" />
            Tồn thấp không tự động nghĩa là phải giảm giá — chỉ là tín hiệu cho analyst.
          </div>
        </Card>
      </div>
    </>
  );
}
