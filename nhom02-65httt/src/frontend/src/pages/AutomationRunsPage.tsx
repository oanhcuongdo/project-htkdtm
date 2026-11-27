import { useMemo, useState } from 'react';
import { Ban, RotateCcw, ShieldAlert } from 'lucide-react';
import {
  Button,
  Card,
  DemoBadge,
  ErrorState,
  KpiCard,
  LoadingState,
  PageHeader,
  StatusPill,
} from '@/components/ui/primitives';
import { DataTable, Pagination, type Column } from '@/components/ui/DataTable';
import { Modal } from '@/components/ui/Modal';
import { useAsync } from '@/hooks/useAsync';
import {
  MAX_ATTEMPTS,
  cancelExecution,
  listExecutions,
  retryExecution,
} from '@/mocks/api';
import { useAuth } from '@/auth/AuthContext';
import { dateTime, money, quantity } from '@/lib/format';
import { executionStatus } from '@/lib/status';
import type { ExecutionRun } from '@/types/domain';

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-border py-2 last:border-0">
      <span className="text-xs text-muted">{label}</span>
      <span className="text-right text-xs font-medium text-ink">{value}</span>
    </div>
  );
}

export function AutomationRunsPage() {
  const { has } = useAuth();
  const [page, setPage] = useState(1);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [detail, setDetail] = useState<ExecutionRun | null>(null);
  const { data, loading, error, reload } = useAsync(
    () => listExecutions({ page, pageSize: 10 }),
    [page],
  );

  const counts = useMemo(() => {
    const items = data?.data ?? [];
    return {
      total: data?.meta.total ?? 0,
      queued: items.filter((e) => e.status === 'QUEUED').length,
      succeeded: items.filter((e) => e.status === 'SUCCEEDED').length,
      failed: items.filter((e) => e.status === 'FAILED').length,
      partial: items.filter((e) => e.status === 'PARTIAL').length,
      retrying: items.filter((e) => e.attempts > 1).length,
    };
  }, [data]);

  async function act(id: string, action: () => Promise<void>) {
    setBusyId(id);
    setActionError(null);
    try {
      await action();
      setDetail(null);
      reload();
    } catch (err) {
      setActionError(
        err instanceof Error ? err.message : 'Không thực hiện được thao tác.',
      );
    } finally {
      setBusyId(null);
    }
  }

  const columns: Column<ExecutionRun>[] = [
    { key: 'id', header: 'Mã', render: (e) => <span className="font-mono text-xs">{e.id}</span> },
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
      key: 'prev',
      header: 'Giá cũ',
      align: 'right',
      render: (e) => <span className="tnum text-muted">{money(e.previousPrice)}</span>,
    },
    {
      key: 'req',
      header: 'Giá yêu cầu',
      align: 'right',
      render: (e) => <span className="tnum">{money(e.requestedPrice)}</span>,
    },
    {
      key: 'status',
      header: 'Trạng thái',
      render: (e) => {
        const s = executionStatus(e.status);
        return <StatusPill tone={s.tone}>{s.label}</StatusPill>;
      },
    },
    {
      key: 'attempts',
      header: 'Lần thử',
      align: 'right',
      render: (e) => (
        <span className={`tnum ${e.attempts >= MAX_ATTEMPTS ? 'font-medium text-danger' : ''}`}>
          {e.attempts}/{MAX_ATTEMPTS}
        </span>
      ),
    },
    {
      key: 'error',
      header: 'Lỗi',
      render: (e) =>
        e.errorCode ? (
          <span className="font-mono text-xs text-danger">{e.errorCode}</span>
        ) : (
          <span className="text-xs text-muted">—</span>
        ),
    },
    {
      key: 'created',
      header: 'Thời điểm',
      align: 'right',
      render: (e) => <span className="tnum text-muted">{dateTime(e.createdAt)}</span>,
    },
    {
      key: 'action',
      header: '',
      align: 'right',
      render: (e) => {
        const canRetry = e.status === 'FAILED' && has('execution.run');
        const canCancel = e.status === 'QUEUED' && has('execution.run');
        return (
          <div className="flex items-center justify-end gap-1">
            <Button size="sm" variant="ghost" onClick={() => setDetail(e)}>
              Chi tiết
            </Button>
            {canRetry ? (
              <Button
                size="sm"
                variant="secondary"
                disabled={busyId === e.id || e.attempts >= MAX_ATTEMPTS}
                title={
                  e.attempts >= MAX_ATTEMPTS
                    ? `Đã đạt giới hạn ${MAX_ATTEMPTS} lần thử — cần tác vụ khôi phục`
                    : 'Thử lại tác vụ thất bại'
                }
                onClick={() => act(e.id, () => retryExecution(e.id))}
              >
                <RotateCcw className="size-3.5" aria-hidden="true" />
                Thử lại
              </Button>
            ) : null}
            {canCancel ? (
              <Button
                size="sm"
                variant="ghost"
                disabled={busyId === e.id}
                onClick={() => act(e.id, () => cancelExecution(e.id))}
              >
                <Ban className="size-3.5" aria-hidden="true" />
                Huỷ
              </Button>
            ) : null}
          </div>
        );
      },
    },
  ];

  return (
    <>
      <PageHeader
        title="Lịch sử thực thi"
        description="Tác vụ mô phỏng và live execution. Retry chỉ cho lỗi transient, tối đa 3 lần."
        actions={<DemoBadge />}
      />

      <div className="mb-4 flex items-start gap-2 rounded-[var(--radius-card)] border border-warning/30 bg-warning/5 px-4 py-3 text-sm text-ink">
        <ShieldAlert className="mt-0.5 size-4 shrink-0 text-warning" aria-hidden="true" />
        <p>
          Mặc định <span className="font-medium">SIMULATION</span>. Không đánh dấu thành công nếu
          chưa xác minh trạng thái provider.
        </p>
      </div>

      {actionError ? (
        <p
          role="alert"
          className="mb-4 rounded-[var(--radius-control)] bg-danger/10 px-3 py-2 text-xs text-danger"
        >
          {actionError}
        </p>
      ) : null}

      <div className="mb-4 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <KpiCard label="Tổng tác vụ" value={quantity(counts.total)} />
        <KpiCard label="Đang chờ" value={quantity(counts.queued)} />
        <KpiCard label="Thành công" value={quantity(counts.succeeded)} tone="success" />
        <KpiCard label="Một phần" value={quantity(counts.partial)} tone="warning" />
        <KpiCard label="Thất bại" value={quantity(counts.failed)} tone="danger" />
        <KpiCard
          label="Có retry"
          value={quantity(counts.retrying)}
          tone="warning"
          hint={`Giới hạn ${MAX_ATTEMPTS} lần thử / tác vụ`}
        />
      </div>

      <Card>
        {loading && !data ? (
          <LoadingState />
        ) : error || !data ? (
          <ErrorState message={error ?? 'Không tải được lịch sử thực thi.'} onRetry={reload} />
        ) : (
          <>
            <DataTable
              columns={columns}
              rows={data.data}
              rowKey={(e) => e.id}
              caption="Lịch sử thực thi giá"
              emptyMessage="Chưa có tác vụ thực thi."
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

      <Modal
        open={detail !== null}
        title={detail ? `Execution ${detail.id}` : 'Execution'}
        description="Request/response đã lọc secrets trước khi hiển thị."
        onClose={() => setDetail(null)}
        width="md"
        footer={
          <Button variant="secondary" size="sm" onClick={() => setDetail(null)}>
            Đóng
          </Button>
        }
      >
        {detail ? (
          <div className="py-1">
            <DetailRow label="SKU" value={detail.skuCode} />
            <DetailRow label="Kênh" value={detail.channelName} />
            <DetailRow label="Chế độ" value={detail.mode} />
            <DetailRow label="Giá cũ" value={money(detail.previousPrice)} />
            <DetailRow label="Giá yêu cầu" value={money(detail.requestedPrice)} />
            <DetailRow label="Trạng thái" value={executionStatus(detail.status).label} />
            <DetailRow label="Số lần thử" value={`${detail.attempts}/${MAX_ATTEMPTS}`} />
            <DetailRow label="Mã lỗi" value={detail.errorCode ?? '—'} />
            <DetailRow label="Idempotency key" value={detail.idempotencyKey} />
            <DetailRow label="Tạo lúc" value={dateTime(detail.createdAt)} />
            <DetailRow label="Cập nhật lúc" value={dateTime(detail.updatedAt)} />
            <p className="mt-3 text-xs text-muted">
              Tác vụ running không huỷ cứng nếu provider đã nhận request — cần reconciliation
              trước khi gửi lại (BUSINESS_RULES §5).
            </p>
          </div>
        ) : null}
      </Modal>
    </>
  );
}
