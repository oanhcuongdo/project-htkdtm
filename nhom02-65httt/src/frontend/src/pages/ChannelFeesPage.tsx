import { ShieldAlert } from 'lucide-react';
import {
  Button,
  Card,
  DemoBadge,
  ErrorState,
  LoadingState,
  PageHeader,
  StatusPill,
} from '@/components/ui/primitives';
import { useAsync } from '@/hooks/useAsync';
import { listChannelFees } from '@/mocks/api';
import { dateOnly, percent } from '@/lib/format';

export function ChannelFeesPage() {
  const { data, loading, error, reload } = useAsync(() => listChannelFees(), []);

  return (
    <>
      <PageHeader
        title="Cấu hình phí kênh"
        description="Phí nền tảng, thanh toán và affiliate được khai báo theo kênh. Phí chưa xác minh phải xác nhận trước khi chạy live."
        actions={<DemoBadge />}
      />

      <div className="mb-4 flex items-start gap-2 rounded-[var(--radius-card)] border border-warning/30 bg-warning/5 px-4 py-3 text-sm text-ink">
        <ShieldAlert className="mt-0.5 size-4 shrink-0 text-warning" aria-hidden="true" />
        <p>
          Phí dùng để tính giá sàn và lợi nhuận ước tính. Không cộng phí vào giá vốn để tránh
          tính hai lần (BUSINESS_RULES BR-004).
        </p>
      </div>

      {loading && !data ? (
        <LoadingState />
      ) : error || !data ? (
        <ErrorState message={error ?? 'Không tải được cấu hình phí.'} onRetry={reload} />
      ) : (
        <div className="space-y-4">
          {data.map((fee) => {
            const unverified = fee.components.filter((c) => !c.verified);
            return (
              <Card key={fee.channelId}>
                <div className="flex flex-wrap items-start justify-between gap-3 border-b border-border px-5 py-4">
                  <div>
                    <h2 className="text-sm font-semibold text-ink">{fee.channelName}</h2>
                    <p className="mt-0.5 text-xs text-muted">
                      Hiệu lực từ {dateOnly(fee.effectiveFrom)} · Nguồn: {fee.source}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <p className="tnum text-lg font-semibold text-ink">
                      {percent(fee.totalRate, 1)}
                    </p>
                    {unverified.length > 0 ? (
                      <StatusPill tone="warning">Chưa xác minh</StatusPill>
                    ) : (
                      <StatusPill tone="success">Đã xác minh</StatusPill>
                    )}
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full min-w-[560px] text-sm">
                    <caption className="sr-only">
                      Thành phần phí của {fee.channelName}
                    </caption>
                    <thead>
                      <tr className="border-b border-border bg-surface-subtle text-xs text-muted">
                        <th scope="col" className="px-4 py-2.5 text-left font-medium">
                          Thành phần
                        </th>
                        <th scope="col" className="px-4 py-2.5 text-left font-medium">
                          Loại
                        </th>
                        <th scope="col" className="px-4 py-2.5 text-right font-medium">
                          Giá trị
                        </th>
                        <th scope="col" className="px-4 py-2.5 text-left font-medium">
                          Xác minh
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {fee.components.map((component) => (
                        <tr key={component.name} className="border-b border-border last:border-0">
                          <td className="px-4 py-2.5 text-ink">{component.name}</td>
                          <td className="px-4 py-2.5 text-muted">
                            {component.type === 'PERCENT' ? 'Tỷ lệ doanh thu' : 'Phí cố định'}
                          </td>
                          <td className="tnum px-4 py-2.5 text-right">
                            {component.type === 'PERCENT'
                              ? percent(component.value, 1)
                              : component.value}
                          </td>
                          <td className="px-4 py-2.5">
                            {component.verified ? (
                              <StatusPill tone="success">Đã xác minh</StatusPill>
                            ) : (
                              <StatusPill tone="warning">Chưa xác minh</StatusPill>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="flex items-center justify-between gap-2 border-t border-border px-5 py-3">
                  <p className="text-xs text-muted">
                    Chỉ Admin cập nhật được cấu hình phí · thay đổi được ghi audit log.
                  </p>
                  <Button
                    variant="secondary"
                    size="sm"
                    disabled
                    title="Chưa khả dụng trong bản demo"
                  >
                    Chỉnh sửa phí
                  </Button>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </>
  );
}
