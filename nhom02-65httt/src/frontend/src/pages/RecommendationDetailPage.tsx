import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  Check,
  PlayCircle,
  Send,
  ShieldCheck,
  X,
} from 'lucide-react';
import {
  Button,
  Card,
  CardBody,
  CardHeader,
  DemoBadge,
  ErrorState,
  Field,
  LoadingState,
  PageHeader,
  Select,
  StatusPill,
} from '@/components/ui/primitives';
import { Modal } from '@/components/ui/Modal';
import { useAsync } from '@/hooks/useAsync';
import { getRecommendation, updateRecommendationStatus } from '@/mocks/api';
import { useAuth } from '@/auth/AuthContext';
import { dateTime, money, percent, signedPercent } from '@/lib/format';
import { dataQuality, recommendationStatus } from '@/lib/status';
import type { ExplanationFactor } from '@/types/domain';

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-xs text-muted">{label}</span>
      <span className="text-right text-xs font-medium text-ink">{value}</span>
    </div>
  );
}

function factorValue(factor: ExplanationFactor): string {
  if (factor.format === 'money') return money(Number(factor.value));
  if (factor.format === 'percent') return percent(Number(factor.value), 1);
  return factor.value;
}

const IMPACT_LABEL: Record<ExplanationFactor['impact'], string> = {
  raises_floor: 'Nâng giá sàn',
  anchors_price: 'Neo giá',
  lowers_price: 'Hạ giá',
  neutral: 'Trung tính',
};

export function RecommendationDetailPage() {
  const { id = '' } = useParams();
  const { has } = useAuth();
  const { data, loading, error, reload } = useAsync(() => getRecommendation(id), [id]);

  const [dialog, setDialog] = useState<null | 'approve' | 'reject'>(null);
  const [reason, setReason] = useState('');
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<{ tone: 'success' | 'danger'; text: string } | null>(
    null,
  );

  if (loading) return <LoadingState label="Đang tải đề xuất…" />;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (!data) return <ErrorState message="Không tìm thấy đề xuất." onRetry={reload} />;

  const status = recommendationStatus(data.status);
  const dq = dataQuality(data.dataQuality);
  const delta = (data.recommendedPrice - data.currentPrice) / data.currentPrice;
  const expired = data.expiresAt ? new Date(data.expiresAt).getTime() < Date.now() : false;
  const canApprove = has('pricing.approve') && data.status === 'PENDING_APPROVAL' && !expired;
  const canSubmit = has('pricing.run') && data.status === 'DRAFT';
  const canSimulate = has('pricing.run');

  async function run(action: () => Promise<void>, successText: string) {
    setBusy(true);
    setNotice(null);
    try {
      await action();
      setNotice({ tone: 'success', text: successText });
      setDialog(null);
      setReason('');
      reload();
    } catch (err) {
      setNotice({
        tone: 'danger',
        text: err instanceof Error ? err.message : 'Thao tác thất bại, thử lại sau.',
      });
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <Link
        to="/pricing/recommendations"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted hover:text-ink"
      >
        <ArrowLeft className="size-4" aria-hidden="true" />
        Quay lại danh sách
      </Link>

      <PageHeader
        title={`Đề xuất ${data.id}`}
        description={`${data.skuCode} · ${data.productName} · ${data.channelName}`}
        actions={
          <>
            <DemoBadge />
            <StatusPill tone={status.tone}>{status.label}</StatusPill>
          </>
        }
      />

      {notice ? (
        <div
          className={`mb-4 rounded-[var(--radius-control)] border px-4 py-2.5 text-sm ${
            notice.tone === 'success'
              ? 'border-success/30 bg-success/5 text-ink'
              : 'border-danger/30 bg-danger/5 text-danger'
          }`}
          role={notice.tone === 'success' ? 'status' : 'alert'}
        >
          {notice.text}
        </div>
      ) : null}

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <div className="space-y-4 xl:col-span-2">
          <Card>
            <CardHeader title="Phân tích giá" subtitle="So sánh giá hiện tại, giá sàn và đề xuất" />
            <CardBody>
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                <div>
                  <p className="text-xs text-muted">Giá hiện tại</p>
                  <p className="tnum mt-1 text-lg font-semibold">{money(data.currentPrice)}</p>
                </div>
                <div>
                  <p className="text-xs text-muted">Giá sàn</p>
                  <p className="tnum mt-1 text-lg font-semibold text-muted">{money(data.floorPrice)}</p>
                </div>
                <div>
                  <p className="text-xs text-muted">Giá đề xuất</p>
                  <p className="tnum mt-1 text-lg font-semibold text-primary">{money(data.recommendedPrice)}</p>
                </div>
                <div>
                  <p className="text-xs text-muted">Thay đổi</p>
                  <p className={`tnum mt-1 text-lg font-semibold ${delta >= 0 ? 'text-success' : 'text-danger'}`}>
                    {signedPercent(delta, 1)}
                  </p>
                </div>
              </div>
              <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
                <div>
                  <p className="text-xs text-muted">Lợi nhuận / đơn vị</p>
                  <p className="tnum mt-1 font-medium">{money(data.expectedProfitPerUnit)}</p>
                </div>
                <div>
                  <p className="text-xs text-muted">Biên lợi nhuận</p>
                  <p className="tnum mt-1 font-medium">{percent(data.expectedMargin, 2)}</p>
                </div>
                <div>
                  <p className="text-xs text-muted">Kênh</p>
                  <p className="mt-1 font-medium">{data.channelName}</p>
                </div>
                <div>
                  <p className="text-xs text-muted">Chất lượng dữ liệu</p>
                  <p className="mt-1">
                    <StatusPill tone={dq.tone}>{dq.label}</StatusPill>
                  </p>
                </div>
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardHeader title="Snapshot đầu vào" subtitle="Dữ liệu engine đã dùng — tái lập được" />
            <CardBody>
              <div className="grid grid-cols-1 gap-x-8 sm:grid-cols-2">
                <Row label="Giá vốn đơn vị" value={money(data.unitCost)} />
                <Row label="Phí kênh" value={percent(data.channelFeeRate, 1)} />
                <Row label="Trung vị đối thủ" value={money(data.competitorMedian)} />
                <Row label="Biên mục tiêu" value={percent(data.targetMargin, 1)} />
                <Row label="Giá sàn tính được" value={money(data.floorPrice)} />
                <Row
                  label="Sàn biến động tối đa (−20%)"
                  value={money(Math.round((data.currentPrice * 0.8) / 1000) * 1000)}
                />
              </div>
              {data.recommendedPrice < data.floorPrice ? (
                <p className="mt-3 rounded-[var(--radius-control)] bg-danger/10 px-3 py-2 text-xs text-danger">
                  Cảnh báo: giá đề xuất thấp hơn giá sàn — không được phép thực thi tự động.
                </p>
              ) : null}
            </CardBody>
          </Card>

          <Card>
            <CardHeader title="Giải thích" subtitle={data.explanation.summary} />
            <CardBody className="space-y-3">
              <div className="overflow-hidden rounded-[var(--radius-control)] border border-border">
                <table className="w-full text-sm">
                  <caption className="sr-only">Các yếu tố ảnh hưởng giá đề xuất</caption>
                  <thead>
                    <tr className="border-b border-border bg-surface-subtle text-xs text-muted">
                      <th scope="col" className="px-3 py-2 text-left font-medium">Yếu tố</th>
                      <th scope="col" className="px-3 py-2 text-right font-medium">Giá trị</th>
                      <th scope="col" className="px-3 py-2 text-left font-medium">Tác động</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.explanation.factors.map((f) => (
                      <tr key={f.key} className="border-b border-border last:border-0">
                        <td className="px-3 py-2">{f.label}</td>
                        <td className="tnum px-3 py-2 text-right text-muted">{factorValue(f)}</td>
                        <td className="px-3 py-2">
                          <StatusPill tone={f.impact === 'raises_floor' ? 'warning' : 'info'}>
                            {IMPACT_LABEL[f.impact]}
                          </StatusPill>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
                {[
                  { label: 'Không dưới giá sàn', ok: data.explanation.constraints.floorPassed },
                  { label: 'Trong giới hạn biến động', ok: data.explanation.constraints.maxChangePassed },
                  { label: 'Giá đối thủ còn mới', ok: data.explanation.constraints.competitorFresh },
                ].map((c) => (
                  <div
                    key={c.label}
                    className={`flex items-center gap-2 rounded-[var(--radius-control)] border px-3 py-2 text-xs ${
                      c.ok ? 'border-success/30 bg-success/5 text-ink' : 'border-danger/30 bg-danger/5 text-danger'
                    }`}
                  >
                    {c.ok ? (
                      <ShieldCheck className="size-4 text-success" aria-hidden="true" />
                    ) : (
                      <X className="size-4 text-danger" aria-hidden="true" />
                    )}
                    {c.label}
                  </div>
                ))}
              </div>
            </CardBody>
          </Card>
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader title="Thông tin phiên bản" subtitle="Tái lập được từ snapshot" />
            <CardBody className="space-y-2 text-sm">
              <Row label="Thuật toán" value={data.algorithmType} />
              <Row label="Phiên bản" value={data.algorithmVersion} />
              <Row label="Người tạo" value={data.createdBy} />
              <Row label="Tạo lúc" value={dateTime(data.createdAt)} />
              <Row label="Hết hạn" value={dateTime(data.expiresAt)} />
              <Row label="Kênh" value={data.channelName} />
            </CardBody>
          </Card>

          <Card>
            <CardHeader title="Hành động" subtitle="Theo quyền và trạng thái hiện tại" />
            <CardBody className="space-y-2">
              {canSubmit ? (
                <Button
                  variant="primary"
                  className="w-full"
                  disabled={busy}
                  onClick={() =>
                    run(
                      () => updateRecommendationStatus(data.id, 'PENDING_APPROVAL'),
                      'Đã gửi duyệt (DEMO). Người có quyền duyệt sẽ nhận được đề xuất này.',
                    )
                  }
                >
                  <Send className="size-4" aria-hidden="true" />
                  Gửi duyệt
                </Button>
              ) : null}
              {canApprove ? (
                <>
                  <Button variant="primary" className="w-full" onClick={() => setDialog('approve')}>
                    <Check className="size-4" aria-hidden="true" />
                    Duyệt đề xuất
                  </Button>
                  <Button variant="danger" className="w-full" onClick={() => setDialog('reject')}>
                    <X className="size-4" aria-hidden="true" />
                    Từ chối
                  </Button>
                  <Button
                    variant="secondary"
                    className="w-full"
                    disabled
                    title="Chưa khả dụng trong bản demo — revision cần API mới"
                  >
                    Yêu cầu chỉnh sửa
                  </Button>
                </>
              ) : null}
              {canSimulate ? (
                <Button
                  variant="secondary"
                  className="w-full"
                  disabled={busy}
                  onClick={() =>
                    run(async () => {
                      await new Promise((resolve) => setTimeout(resolve, 300));
                    }, 'Đã chạy mô phỏng (SIMULATED). Không gọi sàn, không thay đổi giá thật.')
                  }
                >
                  <PlayCircle className="size-4" aria-hidden="true" />
                  Chạy mô phỏng
                </Button>
              ) : null}
              {!canSubmit && !canApprove && !canSimulate ? (
                <p className="text-xs text-muted">Không có hành động khả dụng cho vai trò hiện tại.</p>
              ) : null}
              {expired ? (
                <p className="text-xs text-danger">
                  Đề xuất đã hết hạn — không thể duyệt, cần chạy lại định giá.
                </p>
              ) : null}
            </CardBody>
          </Card>
        </div>
      </div>

      <Modal
        open={dialog !== null}
        title={dialog === 'reject' ? 'Từ chối đề xuất' : 'Duyệt đề xuất'}
        description={
          dialog === 'reject'
            ? 'Bắt buộc nhập lý do từ chối. Hành động được ghi audit log.'
            : 'Xác nhận duyệt giá đề xuất. Hành động được ghi audit log.'
        }
        onClose={() => setDialog(null)}
        footer={
          <>
            <Button variant="secondary" size="sm" onClick={() => setDialog(null)}>
              Huỷ
            </Button>
            <Button
              variant={dialog === 'reject' ? 'danger' : 'primary'}
              size="sm"
              disabled={busy || (dialog === 'reject' && !reason.trim())}
              onClick={() =>
                run(
                  () =>
                    updateRecommendationStatus(
                      data.id,
                      dialog === 'reject' ? 'REJECTED' : 'APPROVED',
                    ),
                  dialog === 'reject'
                    ? 'Đã từ chối đề xuất (DEMO).'
                    : 'Đã duyệt đề xuất (DEMO). Bước tiếp theo: mô phỏng thực thi.',
                )
              }
            >
              {busy ? 'Đang lưu…' : dialog === 'reject' ? 'Từ chối' : 'Duyệt'}
            </Button>
          </>
        }
      >
        <div className="space-y-3 text-sm">
          <div className="rounded-[var(--radius-control)] border border-border bg-surface-subtle p-3">
            <Row label="SKU" value={data.skuCode} />
            <Row label="Kênh" value={data.channelName} />
            <Row label="Giá cũ" value={money(data.currentPrice)} />
            <Row label="Giá đề xuất" value={money(data.recommendedPrice)} />
            <Row label="Thay đổi" value={signedPercent(delta, 1)} />
            <Row label="Biên sau thay đổi" value={percent(data.expectedMargin, 2)} />
          </div>
          {dialog === 'reject' ? (
            <Field label="Lý do từ chối" htmlFor="reject-reason">
              <Select id="reject-reason" value={reason} onChange={(e) => setReason(e.target.value)}>
                <option value="">Chọn lý do…</option>
                <option value="Biên lợi nhuận quá sát giá sàn">Biên lợi nhuận quá sát giá sàn</option>
                <option value="Dữ liệu đối thủ chưa đủ tin cậy">Dữ liệu đối thủ chưa đủ tin cậy</option>
                <option value="Chưa đúng chiến lược kinh doanh">Chưa đúng chiến lược kinh doanh</option>
              </Select>
            </Field>
          ) : null}
        </div>
      </Modal>
    </>
  );
}
