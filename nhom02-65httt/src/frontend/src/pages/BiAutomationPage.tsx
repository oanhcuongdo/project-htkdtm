import { useMemo, useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
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
import { listExecutions } from '@/mocks/api';
import { Select } from '@/components/ui/primitives';
import { dateTime, percent } from '@/lib/format';
import { executionStatus } from '@/lib/status';
import type { ExecutionRun } from '@/types/domain';

const OUTCOME_TONES: Record<string, string> = {
  SUCCEEDED: '#15803D',
  FAILED: '#B42318',
  PARTIAL: '#B45309',
  RUNNING: '#1D4ED8',
  QUEUED: '#475467',
  CANCELLED: '#98A2B3',
};

export function BiAutomationPage() {
  const [mode, setMode] = useState<'ALL' | 'SIMULATED' | 'LIVE'>('ALL');
  const { data, loading, error, reload } = useAsync(
    () => listExecutions({ pageSize: 100 }),
    [],
  );

  const stats = useMemo(() => {
    const all = data?.data ?? [];
    // BI_SPEC §6 — SIMULATED and LIVE are never mixed in one success rate.
    const items = mode === 'ALL' ? all : all.filter((e) => e.mode === mode);
    const completed = items.filter((e) =>
      ['SUCCEEDED', 'PARTIAL', 'FAILED'].includes(e.status),
    );
    const succeeded = items.filter((e) => e.status === 'SUCCEEDED');
    const withRetry = items.filter((e) => e.attempts > 1);
    const byStatus = ['SUCCEEDED', 'PARTIAL', 'FAILED', 'RUNNING', 'QUEUED', 'CANCELLED'].map(
      (s) => ({ status: s, count: items.filter((e) => e.status === s).length }),
    );
    return {
      total: items.length,
      successRate: completed.length ? succeeded.length / completed.length : null,
      retryRate: items.length ? withRetry.length / items.length : null,
      byStatus,
      failed: items.filter((e) => e.status === 'FAILED'),
    };
  }, [data, mode]);

  if (loading && !data) return <LoadingState label="Đang tải dashboard tự động hoá…" />;
  if (error || !data) return <ErrorState message={error ?? 'Không có dữ liệu.'} onRetry={reload} />;

  const failedColumns: Column<ExecutionRun>[] = [
    { key: 'id', header: 'Mã', render: (e) => <span className="font-mono text-xs">{e.id}</span> },
    { key: 'sku', header: 'SKU', render: (e) => <span className="font-mono text-xs">{e.skuCode}</span> },
    { key: 'channel', header: 'Kênh', render: (e) => e.channelName },
    {
      key: 'mode',
      header: 'Chế độ',
      render: (e) => <StatusPill tone={e.mode === 'LIVE' ? 'danger' : 'info'}>{e.mode}</StatusPill>,
    },
    {
      key: 'error',
      header: 'Mã lỗi',
      render: (e) => <span className="font-mono text-xs text-danger">{e.errorCode ?? '—'}</span>,
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
        title="BI · Hiệu suất tự động hoá"
        description="Tỷ lệ thành công, retry và lỗi theo chế độ. Tách bạch SIMULATED và LIVE."
        actions={<DemoBadge />}
      />

      <div className="mb-4 flex flex-wrap items-center gap-2 text-xs text-muted">
        <label htmlFor="bi-mode" className="font-medium text-ink">
          Chế độ thực thi
        </label>
        <Select
          id="bi-mode"
          value={mode}
          onChange={(e) => setMode(e.target.value as typeof mode)}
          className="h-8 w-44"
        >
          <option value="ALL">Tất cả</option>
          <option value="SIMULATED">Chỉ SIMULATED</option>
          <option value="LIVE">Chỉ LIVE</option>
        </Select>
        <span>· Nguồn: fixture DEMO · không phải dữ liệu realtime</span>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Tổng execution" value={String(stats.total)} />
        <KpiCard
          label="Tỷ lệ thành công"
          value={stats.successRate === null ? '—' : percent(stats.successRate, 1)}
          tone={stats.successRate !== null && stats.successRate > 0.9 ? 'success' : 'warning'}
          hint="Trên số tác vụ đã hoàn tất"
        />
        <KpiCard
          label="Tỷ lệ retry"
          value={stats.retryRate === null ? '—' : percent(stats.retryRate, 1)}
          tone="warning"
        />
        <KpiCard label="Thất bại" value={String(stats.failed.length)} tone="danger" />
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-2">
        <Card>
          <CardHeader title="Kết quả theo trạng thái" subtitle="Số lượng execution" />
          <CardBody>
            <ChartSurface
              label="Biểu đồ số lượng execution theo trạng thái"
              table={
                <ChartTable
                  caption="Số lượng execution theo trạng thái"
                  head={['Trạng thái', 'Số lượng']}
                  rows={stats.byStatus.map((row) => [
                    executionStatus(row.status as ExecutionRun['status']).label,
                    row.count,
                  ])}
                />
              }
            >
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stats.byStatus} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid stroke="#E4E7EC" strokeDasharray="3 3" vertical={false} />
                  <XAxis
                    dataKey="status"
                    tickFormatter={(s: string) => executionStatus(s as ExecutionRun['status']).label}
                    tick={{ fontSize: 10, fill: '#667085' }}
                    tickLine={false}
                    axisLine={{ stroke: '#E4E7EC' }}
                  />
                  <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: '#667085' }} tickLine={false} axisLine={false} width={28} />
                  <Tooltip formatter={(v: number) => [`${v} tác vụ`, 'Số lượng']} />
                  <Bar dataKey="count" name="Số lượng" radius={[4, 4, 0, 0]}>
                    {stats.byStatus.map((s) => (
                      <Cell key={s.status} fill={OUTCOME_TONES[s.status] ?? '#475467'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </ChartSurface>
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Execution thất bại" subtitle="Cần điều tra nguyên nhân" />
          <DataTable
            columns={failedColumns}
            rows={stats.failed}
            rowKey={(e) => e.id}
            caption="Execution thất bại"
            emptyMessage="Không có execution thất bại."
          />
        </Card>
      </div>

      <p className="mt-3 text-xs text-muted">
        Approval latency và rule impact cần dữ liệu thời gian thực từ DB — chưa hiển thị để tránh số liệu giả.
      </p>
    </>
  );
}