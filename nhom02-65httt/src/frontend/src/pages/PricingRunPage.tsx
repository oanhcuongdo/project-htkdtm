import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertTriangle,
  CheckCircle2,
  Info,
  Play,
  Search,
  Sparkles,
} from 'lucide-react';
import {
  Button,
  Card,
  CardBody,
  CardHeader,
  DemoBadge,
  ErrorState,
  Field,
  Input,
  LoadingState,
  PageHeader,
  Select,
  StatusPill,
} from '@/components/ui/primitives';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { useAsync } from '@/hooks/useAsync';
import {
  getPricingPreview,
  listChannels,
  listProducts,
  runPricing,
  type PricingRunResult,
} from '@/mocks/api';
import { dateTime, freshness, money, percent } from '@/lib/format';
import { dataQuality, recommendationStatus } from '@/lib/status';
import type { Recommendation } from '@/types/domain';

const OBJECTIVES = [
  { value: 'PROFIT', label: 'Tối ưu lợi nhuận (PROFIT)' },
  { value: 'COMPETITIVE', label: 'Bám giá cạnh tranh (COMPETITIVE)' },
  { value: 'CLEAR_STOCK', label: 'Xả tồn (CLEAR_STOCK)' },
] as const;

export function PricingRunPage() {
  const { data, loading, error, reload } = useAsync(
    () =>
      Promise.all([listChannels(), listProducts({ pageSize: 100 })]).then(
        ([channels, products]) => ({ channels, products: products.data }),
      ),
    [],
  );

  const [selected, setSelected] = useState<string[]>([]);
  const [skuFilter, setSkuFilter] = useState('');
  const [channelId, setChannelId] = useState('ch-shopee');
  const [objective, setObjective] =
    useState<'PROFIT' | 'COMPETITIVE' | 'CLEAR_STOCK'>('PROFIT');
  const [targetMargin, setTargetMargin] = useState('18');
  const [mode, setMode] = useState<'RULE_BASED' | 'ML_ASSISTED'>('RULE_BASED');
  const [competitorStrategy, setCompetitorStrategy] =
    useState<'IGNORE' | 'STAY_WITHIN_RANGE' | 'MATCH_MEDIAN'>('STAY_WITHIN_RANGE');
  const [stockStrategy, setStockStrategy] =
    useState<'NEUTRAL' | 'CLEAR_SLOW_MOVING'>('NEUTRAL');
  const [effectiveAt, setEffectiveAt] = useState('');
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<PricingRunResult | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const channel = data?.channels.find((c) => c.id === channelId);
  const selectedKey = selected.join(',');

  const preview = useAsync(
    () =>
      selected.length === 0
        ? Promise.resolve([])
        : getPricingPreview({ skuIds: selected, channelId }),
    [selectedKey, channelId],
  );

  const visibleProducts = useMemo(() => {
    const needle = skuFilter.trim().toLowerCase();
    const items = data?.products ?? [];
    if (!needle) return items;
    return items.filter((p) =>
      `${p.skuCode} ${p.name}`.toLowerCase().includes(needle),
    );
  }, [data, skuFilter]);

  function toggleSku(id: string) {
    setResult(null);
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  }

  async function onRun() {
    setFormError(null);
    setResult(null);
    if (selected.length === 0) {
      setFormError('Chọn ít nhất một SKU để chạy định giá.');
      return;
    }
    const margin = Number(targetMargin) / 100;
    if (!Number.isFinite(margin) || margin <= 0 || margin >= 1) {
      setFormError('Biên lợi nhuận mục tiêu phải trong khoảng 0–100%.');
      return;
    }
    if (channel && 1 - channel.feeRate - margin <= 0) {
      setFormError(
        `Phí kênh ${percent(channel.feeRate, 1)} + biên ${percent(margin, 1)} ≥ 100% → mọi SKU sẽ trả NO_SAFE_PRICE. Giảm biên mục tiêu trước khi chạy.`,
      );
      return;
    }
    setRunning(true);
    try {
      const response = await runPricing({
        skuIds: selected,
        channelId,
        objective,
        targetMargin: margin,
        mode,
        competitorStrategy,
        stockStrategy,
        effectiveAt: effectiveAt ? new Date(effectiveAt).toISOString() : null,
      });
      setResult(response);
    } catch (err) {
      setFormError(
        err instanceof Error ? err.message : 'Không khởi tạo được tác vụ định giá.',
      );
    } finally {
      setRunning(false);
    }
  }

  if (loading) return <LoadingState label="Đang tải cấu hình kênh…" />;
  if (error || !data) return <ErrorState message={error ?? 'Không tải được dữ liệu.'} onRetry={reload} />;

  const resultColumns: Column<Recommendation>[] = [
    {
      key: 'sku',
      header: 'SKU',
      render: (r) => <span className="font-mono text-xs font-medium">{r.skuCode}</span>,
    },
    {
      key: 'current',
      header: 'Giá hiện tại',
      align: 'right',
      render: (r) => <span className="tnum text-muted">{money(r.currentPrice)}</span>,
    },
    {
      key: 'floor',
      header: 'Giá sàn',
      align: 'right',
      render: (r) => <span className="tnum text-muted">{money(r.floorPrice)}</span>,
    },
    {
      key: 'recommended',
      header: 'Đề xuất',
      align: 'right',
      sortable: true,
      sortValue: (r) => r.recommendedPrice,
      render: (r) => <span className="tnum font-medium">{money(r.recommendedPrice)}</span>,
    },
    {
      key: 'profit',
      header: 'LN / đơn vị',
      align: 'right',
      render: (r) => <span className="tnum">{money(r.expectedProfitPerUnit)}</span>,
    },
    {
      key: 'margin',
      header: 'Biên',
      align: 'right',
      render: (r) => <span className="tnum">{percent(r.expectedMargin, 1)}</span>,
    },
    {
      key: 'quality',
      header: 'Chất lượng',
      render: (r) => {
        const dq = dataQuality(r.dataQuality);
        return <StatusPill tone={dq.tone}>{dq.label}</StatusPill>;
      },
    },
    {
      key: 'status',
      header: 'Trạng thái',
      render: (r) => {
        const s = recommendationStatus(r.status);
        return <StatusPill tone={s.tone}>{s.label}</StatusPill>;
      },
    },
    {
      key: 'open',
      header: '',
      align: 'right',
      render: (r) => (
        <Link
          to={`/pricing/recommendations/${r.id}`}
          className="text-xs font-medium text-primary hover:underline"
        >
          Chi tiết
        </Link>
      ),
    },
  ];

  return (
    <>
      <PageHeader
        title="Chạy AI Smart Pricing"
        description="Rule-based baseline. Không chạy nếu thiếu giá vốn hoặc phí kênh hợp lệ (BUSINESS_RULES BR-003)."
        actions={<DemoBadge />}
      />

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader title="Tham số chạy" subtitle="Chọn SKU, kênh và mục tiêu định giá" />
          <CardBody className="space-y-5">
            <fieldset>
              <legend className="mb-2 text-xs font-medium text-ink">
                SKU ({selected.length} đã chọn)
              </legend>
              <div className="relative mb-2">
                <Search
                  className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted"
                  aria-hidden="true"
                />
                <Input
                  value={skuFilter}
                  onChange={(e) => setSkuFilter(e.target.value)}
                  placeholder="Lọc SKU trong danh sách…"
                  aria-label="Lọc SKU"
                  className="pl-8"
                />
              </div>
              <div className="max-h-56 overflow-y-auto rounded-[var(--radius-control)] border border-border">
                {visibleProducts.length === 0 ? (
                  <p className="px-3 py-6 text-center text-xs text-muted">
                    Không có SKU phù hợp.
                  </p>
                ) : (
                  visibleProducts.map((p) => (
                    <label
                      key={p.id}
                      className="flex cursor-pointer items-center justify-between gap-3 border-b border-border px-3 py-2 text-sm last:border-0 hover:bg-surface-subtle"
                    >
                      <span className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={selected.includes(p.id)}
                          onChange={() => toggleSku(p.id)}
                          className="size-4 rounded border-border accent-[var(--color-primary)]"
                        />
                        <span>
                          <span className="font-mono text-xs text-muted">{p.skuCode}</span>{' '}
                          <span className="text-ink">{p.name}</span>
                        </span>
                      </span>
                      <span className="tnum text-xs text-muted">{money(p.currentPrice)}</span>
                    </label>
                  ))
                )}
              </div>
            </fieldset>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Field label="Kênh bán" htmlFor="channel">
                <Select id="channel" value={channelId} onChange={(e) => setChannelId(e.target.value)}>
                  {data.channels.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} · {c.integrationMode}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="Mục tiêu" htmlFor="objective">
                <Select
                  id="objective"
                  value={objective}
                  onChange={(e) => setObjective(e.target.value as typeof objective)}
                >
                  {OBJECTIVES.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="Biên lợi nhuận mục tiêu (%)" htmlFor="margin" hint="Ví dụ 18 = 18%">
                <Input
                  id="margin"
                  type="number"
                  min={1}
                  max={99}
                  step={0.5}
                  value={targetMargin}
                  onChange={(e) => setTargetMargin(e.target.value)}
                />
              </Field>
              <Field label="Thuật toán" htmlFor="mode" hint="ML chỉ bật khi model đạt chuẩn">
                <Select id="mode" value={mode} onChange={(e) => setMode(e.target.value as typeof mode)}>
                  <option value="RULE_BASED">Rule-based (mặc định)</option>
                  <option value="ML_ASSISTED">ML-assisted</option>
                </Select>
              </Field>
              <Field label="Chiến lược đối thủ" htmlFor="competitor-strategy">
                <Select
                  id="competitor-strategy"
                  value={competitorStrategy}
                  onChange={(e) =>
                    setCompetitorStrategy(e.target.value as typeof competitorStrategy)
                  }
                >
                  <option value="STAY_WITHIN_RANGE">Bám trong khoảng giá đối thủ</option>
                  <option value="MATCH_MEDIAN">Khớp trung vị đối thủ</option>
                  <option value="IGNORE">Không dùng tín hiệu đối thủ</option>
                </Select>
              </Field>
              <Field label="Chiến lược tồn kho" htmlFor="stock-strategy">
                <Select
                  id="stock-strategy"
                  value={stockStrategy}
                  onChange={(e) => setStockStrategy(e.target.value as typeof stockStrategy)}
                >
                  <option value="NEUTRAL">Trung tính</option>
                  <option value="CLEAR_SLOW_MOVING">Ưu tiên xả tồn lâu</option>
                </Select>
              </Field>
              <Field
                label="Áp dụng từ"
                htmlFor="effective-at"
                hint="Để trống = áp dụng ngay sau khi duyệt"
              >
                <Input
                  id="effective-at"
                  type="datetime-local"
                  value={effectiveAt}
                  onChange={(e) => setEffectiveAt(e.target.value)}
                />
              </Field>
            </div>

            {formError ? (
              <p role="alert" className="rounded-[var(--radius-control)] bg-danger/10 px-3 py-2 text-xs text-danger">
                {formError}
              </p>
            ) : null}

            <div className="flex flex-wrap items-center gap-2">
              <Button variant="primary" onClick={onRun} disabled={running}>
                <Play className="size-4" aria-hidden="true" />
                {running ? 'Đang tính giá…' : 'Chạy định giá'}
              </Button>
              <span className="text-xs text-muted">
                Kết quả được lưu thành đề xuất DRAFT, cần gửi duyệt trước khi thực thi.
              </span>
            </div>

            {result ? (
              <div
                className={`flex items-start gap-2 rounded-[var(--radius-control)] border px-3 py-2 text-sm ${
                  result.results.length === 0
                    ? 'border-danger/30 bg-danger/5'
                    : 'border-success/30 bg-success/5'
                }`}
              >
                {result.results.length === 0 ? (
                  <AlertTriangle className="mt-0.5 size-4 shrink-0 text-danger" aria-hidden="true" />
                ) : (
                  <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-success" aria-hidden="true" />
                )}
                <div>
                  <p className="font-medium text-ink">
                    {result.results.length > 0
                      ? `Đã tạo ${result.results.length} đề xuất (DEMO)`
                      : 'Không tạo được giá an toàn cho SKU nào'}
                  </p>
                  <p className="text-xs text-muted">
                    Job <span className="font-mono">{result.jobId}</span> ·{' '}
                    {result.requestedCount} SKU yêu cầu · {channel?.name}.
                  </p>
                  {result.noSafePriceSkuCodes.length > 0 ? (
                    <p className="mt-1 text-xs text-danger">
                      NO_SAFE_PRICE: {result.noSafePriceSkuCodes.join(', ')} — phí + biên mục
                      tiêu không còn chỗ cho giá sàn.
                    </p>
                  ) : null}
                  <p className="mt-1 text-xs">
                    <Link to="/pricing/runs" className="text-primary hover:underline">
                      Xem lịch sử chạy
                    </Link>
                    {' · '}
                    <Link to="/pricing/recommendations" className="text-primary hover:underline">
                      Xem đề xuất
                    </Link>
                  </p>
                </div>
              </div>
            ) : null}
          </CardBody>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader
              title="Xem trước đầu vào"
              subtitle="Dữ liệu engine sẽ dùng — không phải kết quả"
            />
            <CardBody className="space-y-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-muted">Kênh</span>
                <span className="font-medium">{channel?.name ?? '—'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted">Phí kênh</span>
                <span className="tnum font-medium">{percent(channel?.feeRate ?? null, 1)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted">Chế độ</span>
                <StatusPill tone={channel?.integrationMode === 'LIVE' ? 'danger' : 'info'}>
                  {channel?.integrationMode ?? '—'}
                </StatusPill>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted">Biên mục tiêu</span>
                <span className="tnum font-medium">{targetMargin || '0'}%</span>
              </div>
              <hr className="border-border" />
              {selected.length === 0 ? (
                <p className="text-xs text-muted">Chưa chọn SKU.</p>
              ) : preview.loading && !preview.data ? (
                <p className="text-xs text-muted">Đang tải dữ liệu đầu vào…</p>
              ) : preview.error ? (
                <p className="text-xs text-danger">{preview.error}</p>
              ) : (
                <ul className="space-y-2">
                  {(preview.data ?? []).slice(0, 5).map((row) => {
                    const f = freshness(row.competitorObservedAt, 24);
                    return (
                      <li key={row.skuId} className="rounded-[var(--radius-control)] bg-surface-subtle px-2.5 py-2">
                        <p className="truncate text-xs">
                          <span className="font-mono text-muted">{row.skuCode}</span>{' '}
                          <span className="text-ink">{row.productName}</span>
                        </p>
                        <dl className="mt-1 grid grid-cols-2 gap-x-2 text-[11px] text-muted">
                          <div className="flex justify-between gap-2">
                            <dt>Giá vốn</dt>
                            <dd className="tnum text-ink">{money(row.unitCost)}</dd>
                          </div>
                          <div className="flex justify-between gap-2">
                            <dt>Giá bán</dt>
                            <dd className="tnum text-ink">{money(row.currentPrice)}</dd>
                          </div>
                          <div className="flex justify-between gap-2">
                            <dt>Median ĐT</dt>
                            <dd className="tnum text-ink">{money(row.competitorMedian)}</dd>
                          </div>
                          <div className="flex justify-between gap-2">
                            <dt>Độ tươi</dt>
                            <dd className={f.stale ? 'text-danger' : 'text-ink'}>
                              {row.competitorMedian === null ? 'Thiếu' : f.label}
                            </dd>
                          </div>
                        </dl>
                      </li>
                    );
                  })}
                </ul>
              )}
              {selected.length > 5 && preview.data ? (
                <p className="text-[11px] text-muted">
                  Hiển thị 5 / {selected.length} SKU đã chọn.
                </p>
              ) : null}
            </CardBody>
          </Card>

          <div className="flex items-start gap-2 rounded-[var(--radius-card)] border border-border bg-surface-subtle px-4 py-3 text-xs text-muted">
            <Info className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
            <p>
              Giá sàn = (chi phí đơn vị + phí cố định) / (1 − phí kênh − biên mục tiêu). Nếu mẫu
              ≤ 0, kết quả là <span className="font-medium text-ink">NO_SAFE_PRICE</span>.
            </p>
          </div>

          <div className="flex items-start gap-2 rounded-[var(--radius-card)] border border-primary/20 bg-primary/5 px-4 py-3 text-xs text-ink">
            <Sparkles className="mt-0.5 size-4 shrink-0 text-primary" aria-hidden="true" />
            <p>Mọi lần chạy lưu snapshot, phiên bản thuật toán và giải thích để tái hiện.</p>
          </div>
        </div>
      </div>

      {result && result.results.length > 0 ? (
        <Card className="mt-4">
          <CardHeader
            title="Kết quả định giá"
            subtitle={`Job ${result.jobId} · tạo lúc ${dateTime(result.results[0]?.createdAt)}`}
            action={
              <Link
                to="/pricing/recommendations"
                className="text-xs font-medium text-primary hover:underline"
              >
                Tất cả đề xuất
              </Link>
            }
          />
          <DataTable
            columns={resultColumns}
            rows={result.results}
            rowKey={(r) => r.id}
            caption="Kết quả chạy định giá"
          />
        </Card>
      ) : null}
    </>
  );
}
