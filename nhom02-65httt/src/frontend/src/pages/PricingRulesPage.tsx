import { useMemo, useState } from 'react';
import { AlertTriangle, CheckCircle2, Pause, Play, Plus, ShieldCheck } from 'lucide-react';
import {
  Button,
  Card,
  DemoBadge,
  ErrorState,
  LoadingState,
  PageHeader,
  StatusPill,
} from '@/components/ui/primitives';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { useAsync } from '@/hooks/useAsync';
import { listRules, setRuleStatus } from '@/mocks/api';
import { useAuth } from '@/auth/AuthContext';
import { dateOnly, percent } from '@/lib/format';
import { ruleStatus, ruleTypeLabel } from '@/lib/status';
import type { PricingRule } from '@/types/domain';

export function PricingRulesPage() {
  const { has } = useAuth();
  const { data, loading, error, reload } = useAsync(() => listRules(), []);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  /** BUSINESS_RULES §3 — same priority + same scope must be reported, not auto-resolved. */
  const conflicts = useMemo(() => {
    const items = (data ?? []).filter((r) => r.status !== 'ARCHIVED');
    const pairs: { a: PricingRule; b: PricingRule }[] = [];
    for (let i = 0; i < items.length; i += 1) {
      for (let j = i + 1; j < items.length; j += 1) {
        const a = items[i]!;
        const b = items[j]!;
        if (a.priority === b.priority && a.scopeLabel === b.scopeLabel) {
          pairs.push({ a, b });
        }
      }
    }
    return pairs;
  }, [data]);

  async function toggle(rule: PricingRule) {
    setBusyId(rule.id);
    setActionError(null);
    try {
      await setRuleStatus(rule.id, rule.status === 'ACTIVE' ? 'PAUSED' : 'ACTIVE');
      reload();
    } catch (err) {
      setActionError(
        err instanceof Error ? err.message : 'Không cập nhật được trạng thái quy tắc.',
      );
    } finally {
      setBusyId(null);
    }
  }

  const columns: Column<PricingRule>[] = [
    {
      key: 'name',
      header: 'Quy tắc',
      sortable: true,
      sortValue: (r) => r.name,
      render: (r) => (
        <div>
          <p className="font-medium text-ink">{r.name}</p>
          <p className="text-xs text-muted">{r.scopeLabel}</p>
        </div>
      ),
    },
    {
      key: 'type',
      header: 'Loại',
      render: (r) => (
        <StatusPill tone={r.ruleType === 'MARGIN_GUARD' ? 'danger' : 'neutral'}>
          {r.ruleType === 'MARGIN_GUARD' ? <ShieldCheck className="size-3" aria-hidden="true" /> : null}
          {ruleTypeLabel(r.ruleType)}
        </StatusPill>
      ),
    },
    {
      key: 'priority',
      header: 'Ưu tiên',
      align: 'right',
      sortable: true,
      sortValue: (r) => r.priority,
      render: (r) => <span className="tnum">{r.priority}</span>,
    },
    {
      key: 'minMargin',
      header: 'Biên tối thiểu',
      align: 'right',
      render: (r) => <span className="tnum">{percent(r.minMargin, 1)}</span>,
    },
    {
      key: 'maxChange',
      header: 'Δ tối đa',
      align: 'right',
      render: (r) => <span className="tnum">{percent(r.maxPriceChangePct, 0)}</span>,
    },
    {
      key: 'window',
      header: 'Hiệu lực',
      render: (r) => (
        <span className="tnum text-xs text-muted">
          {dateOnly(r.startsAt)} → {r.endsAt ? dateOnly(r.endsAt) : '∞'}
        </span>
      ),
    },
    {
      key: 'approval',
      header: 'Duyệt',
      render: (r) =>
        r.approvalRequired ? (
          <StatusPill tone="warning">Bắt buộc</StatusPill>
        ) : (
          <StatusPill tone="neutral">Không</StatusPill>
        ),
    },
    {
      key: 'status',
      header: 'Trạng thái',
      render: (r) => {
        const s = ruleStatus(r.status);
        return <StatusPill tone={s.tone}>{s.label}</StatusPill>;
      },
    },
    {
      key: 'actions',
      header: '',
      align: 'right',
      render: (r) => {
        if (!has('rule.write') || r.ruleType === 'MARGIN_GUARD') {
          return <span className="text-xs text-muted">—</span>;
        }
        const activate = r.status !== 'ACTIVE';
        const blocked = r.status === 'ARCHIVED';
        return (
          <Button
            size="sm"
            variant={activate ? 'secondary' : 'ghost'}
            disabled={busyId === r.id || blocked}
            title={blocked ? 'Quy tắc đã lưu trữ' : undefined}
            onClick={() => toggle(r)}
          >
            {activate ? (
              <>
                <Play className="size-3.5" aria-hidden="true" /> Bật
              </>
            ) : (
              <>
                <Pause className="size-3.5" aria-hidden="true" /> Tạm dừng
              </>
            )}
          </Button>
        );
      },
    },
  ];

  return (
    <>
      <PageHeader
        title="Pricing Rules"
        description="Rule ưu tiên cao chạy trước; Margin Guard là rào chắn cuối không thể bị ghi đè."
        actions={
          <>
            <DemoBadge />
            {has('rule.write') ? (
              <Button
                variant="primary"
                size="sm"
                disabled
                title="Chưa khả dụng trong bản demo — cần API tạo quy tắc"
              >
                <Plus className="size-4" aria-hidden="true" />
                Tạo quy tắc
              </Button>
            ) : null}
          </>
        }
      />

      <div
        className={`mb-4 flex items-start gap-2 rounded-[var(--radius-card)] border px-4 py-3 text-sm ${
          conflicts.length > 0
            ? 'border-warning/30 bg-warning/5 text-ink'
            : 'border-border bg-surface-subtle text-muted'
        }`}
      >
        {conflicts.length > 0 ? (
          <AlertTriangle className="mt-0.5 size-4 shrink-0 text-warning" aria-hidden="true" />
        ) : (
          <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-success" aria-hidden="true" />
        )}
        <div>
          <p className="font-medium text-ink">
            {conflicts.length > 0
              ? `${conflicts.length} xung đột ưu tiên cần xử lý`
              : 'Không phát hiện xung đột rule'}
          </p>
          {conflicts.length > 0 ? (
            <ul className="mt-1 space-y-0.5 text-xs">
              {conflicts.map(({ a, b }) => (
                <li key={`${a.id}-${b.id}`}>
                  “{a.name}” và “{b.name}” cùng ưu tiên {a.priority} trên cùng phạm vi — hệ thống
                  không tự chọn rule thắng.
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-0.5 text-xs">
              Kiểm tra dựa trên priority và phạm vi của các rule chưa lưu trữ.
            </p>
          )}
        </div>
      </div>

      {actionError ? (
        <p
          role="alert"
          className="mb-4 rounded-[var(--radius-control)] bg-danger/10 px-3 py-2 text-xs text-danger"
        >
          {actionError}
        </p>
      ) : null}

      <Card>
        {loading && !data ? (
          <LoadingState />
        ) : error || !data ? (
          <ErrorState message={error ?? 'Không tải được quy tắc.'} onRetry={reload} />
        ) : (
          <DataTable
            columns={columns}
            rows={data}
            rowKey={(r) => r.id}
            caption="Danh sách pricing rules"
            emptyMessage="Chưa có quy tắc."
          />
        )}
      </Card>

      <p className="mt-3 text-xs text-muted">
        Rule không thể bật nếu thiếu phạm vi, thời gian hiệu lực, biên tối thiểu hoặc giới hạn
        biến động (BUSINESS_RULES §3).
      </p>
    </>
  );
}
