import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { Play } from 'lucide-react';
import {
  Button,
  Card,
  CardHeader,
  DemoBadge,
  ErrorState,
  KpiCard,
  LoadingState,
  PageHeader,
  StatusPill,
  type Tone,
} from '@/components/ui/primitives';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { useAsync } from '@/hooks/useAsync';
import { listPricingJobs, listPricingSchedules } from '@/mocks/api';
import { dateTime, percent } from '@/lib/format';
import type { PricingJob, PricingJobStatus, PricingSchedule } from '@/types/domain';

const JOB_STATUS: Record<PricingJobStatus, { label: string; tone: Tone }> = {
  QUEUED: { label: 'Đang chờ', tone: 'neutral' },
  COMPLETED: { label: 'Hoàn tất', tone: 'success' },
  PARTIAL: { label: 'Một phần', tone: 'warning' },
  FAILED: { label: 'Thất bại', tone: 'danger' },
};

const OBJECTIVE_LABEL: Record<PricingJob['objective'], string> = {
  PROFIT: 'Tối ưu lợi nhuận',
  COMPETITIVE: 'Bám giá cạnh tranh',
  CLEAR_STOCK: 'Xả tồn',
};

export function PricingJobsPage() {
  const { data, loading, error, reload } = useAsync(
    () =>
      Promise.all([listPricingJobs(), listPricingSchedules()]).then(
        ([jobs, schedules]) => ({ jobs, schedules }),
      ),
    [],
  );

  const counts = useMemo(() => {
    const jobs = data?.jobs ?? [];
    return {
      total: jobs.length,
      completed: jobs.filter((j) => j.status === 'COMPLETED').length,
      partial: jobs.filter((j) => j.status === 'PARTIAL').length,
      noSafe: jobs.reduce((sum, j) => sum + j.noSafePriceCount, 0),
    };
  }, [data]);

  const jobColumns: Column<PricingJob>[] = [
    { key: 'id', header: 'Mã job', render: (j) => <span className="font-mono text-xs">{j.id}</span> },
    { key: 'channel', header: 'Kênh', render: (j) => j.channelName },
    { key: 'objective', header: 'Mục tiêu', render: (j) => OBJECTIVE_LABEL[j.objective] },
    {
      key: 'mode',
      header: 'Thuật toán',
      render: (j) => (
        <StatusPill tone={j.mode === 'ML_ASSISTED' ? 'warning' : 'neutral'}>
          {j.mode === 'ML_ASSISTED' ? 'ML-assisted' : 'Rule-based'}
        </StatusPill>
      ),
    },
    {
      key: 'margin',
      header: 'Biên mục tiêu',
      align: 'right',
      render: (j) => <span className="tnum">{percent(j.targetMargin, 1)}</span>,
    },
    {
      key: 'skus',
      header: 'SKU',
      align: 'right',
      render: (j) => <span className="tnum text-muted">{j.skuCount}</span>,
    },
    {
      key: 'results',
      header: 'Kết quả',
      align: 'right',
      render: (j) => <span className="tnum">{j.resultCount}</span>,
    },
    {
      key: 'noSafe',
      header: 'NO_SAFE_PRICE',
      align: 'right',
      render: (j) =>
        j.noSafePriceCount > 0 ? (
          <span className="tnum font-medium text-danger">{j.noSafePriceCount}</span>
        ) : (
          <span className="tnum text-muted">0</span>
        ),
    },
    {
      key: 'status',
      header: 'Trạng thái',
      render: (j) => {
        const s = JOB_STATUS[j.status];
        return <StatusPill tone={s.tone}>{s.label}</StatusPill>;
      },
    },
    {
      key: 'created',
      header: 'Tạo lúc',
      align: 'right',
      render: (j) => <span className="tnum text-muted">{dateTime(j.createdAt)}</span>,
    },
  ];

  const scheduleColumns: Column<PricingSchedule>[] = [
    {
      key: 'name',
      header: 'Lịch',
      render: (s) => (
        <div>
          <p className="font-medium text-ink">{s.name}</p>
          <p className="text-xs text-muted">{s.ruleName}</p>
        </div>
      ),
    },
    { key: 'cron', header: 'Chu kỳ', render: (s) => <span className="text-muted">{s.cronLabel}</span> },
    {
      key: 'mode',
      header: 'Chế độ',
      render: (s) => (
        <StatusPill tone={s.mode === 'LIVE' ? 'danger' : 'info'}>{s.mode}</StatusPill>
      ),
    },
    {
      key: 'next',
      header: 'Lần chạy tới',
      align: 'right',
      render: (s) => <span className="tnum text-muted">{dateTime(s.nextRunAt)}</span>,
    },
    {
      key: 'enabled',
      header: 'Bật',
      render: (s) =>
        s.enabled ? (
          <StatusPill tone="success">Đang bật</StatusPill>
        ) : (
          <StatusPill tone="neutral">Tắt</StatusPill>
        ),
    },
  ];

  return (
    <>
      <PageHeader
        title="Lịch sử chạy định giá"
        description="Mỗi lần chạy lưu mục tiêu, thuật toán và số SKU không có giá an toàn để tái hiện kết quả."
        actions={
          <>
            <DemoBadge />
            <Link to="/pricing/run">
              <Button variant="primary" size="sm">
                <Play className="size-4" aria-hidden="true" />
                Chạy định giá
              </Button>
            </Link>
          </>
        }
      />

      <div className="mb-4 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Tổng lần chạy" value={String(counts.total)} />
        <KpiCard label="Hoàn tất" value={String(counts.completed)} tone="success" />
        <KpiCard label="Một phần" value={String(counts.partial)} tone="warning" />
        <KpiCard
          label="SKU không có giá an toàn"
          value={String(counts.noSafe)}
          tone={counts.noSafe > 0 ? 'danger' : 'success'}
          hint="NO_SAFE_PRICE cần xem lại phí hoặc biên mục tiêu"
        />
      </div>

      <Card>
        {loading && !data ? (
          <LoadingState />
        ) : error || !data ? (
          <ErrorState message={error ?? 'Không tải được lịch sử chạy.'} onRetry={reload} />
        ) : (
          <DataTable
            columns={jobColumns}
            rows={data.jobs}
            rowKey={(j) => j.id}
            caption="Lịch sử chạy định giá"
            emptyMessage="Chưa có lần chạy nào."
          />
        )}
      </Card>

      <Card className="mt-4">
        <CardHeader
          title="Lịch chạy tự động"
          subtitle="Cấu hình phía backend (Celery) · DEMO"
        />
        <DataTable
          columns={scheduleColumns}
          rows={data?.schedules ?? []}
          rowKey={(s) => s.id}
          caption="Lịch chạy tự động"
          emptyMessage="Chưa có lịch chạy."
        />
      </Card>
    </>
  );
}
