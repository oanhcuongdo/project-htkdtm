import { useState } from 'react';
import { Cable, Link2, Loader2, Radio, Search, ShieldAlert } from 'lucide-react';
import {
  Button,
  Card,
  CardBody,
  CardHeader,
  DemoBadge,
  ErrorState,
  Input,
  LoadingState,
  PageHeader,
  Select,
  StatusPill,
} from '@/components/ui/primitives';
import { DataTable, Pagination, type Column } from '@/components/ui/DataTable';
import { useAsync } from '@/hooks/useAsync';
import { useDebouncedValue } from '@/hooks/useDebouncedValue';
import {
  listChannelListings,
  listChannels,
  testChannelConnection,
  type ConnectionTest,
} from '@/mocks/api';
import { dateTime, money, percent, quantity } from '@/lib/format';
import { connectionStatus, mappingSyncStatus } from '@/lib/status';
import type { Channel, ChannelListing } from '@/types/domain';

function ChannelCard({
  channel,
  test,
  busy,
  onTest,
}: {
  channel: Channel;
  test?: ConnectionTest;
  busy: boolean;
  onTest: () => void;
}) {
  const conn = connectionStatus(channel.connectionStatus);
  return (
    <Card>
      <CardHeader
        title={channel.name}
        subtitle={`Mã: ${channel.code}`}
        action={
          <StatusPill tone={channel.integrationMode === 'LIVE' ? 'danger' : 'info'}>
            <Radio className="size-3" aria-hidden="true" />
            {channel.integrationMode}
          </StatusPill>
        }
      />
      <CardBody className="space-y-3">
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted">Trạng thái kết nối</span>
          <StatusPill tone={conn.tone}>{conn.label}</StatusPill>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted">Phí kênh ước tính</span>
          <span className="tnum font-medium">{percent(channel.feeRate, 1)}</span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted">Listing đang map</span>
          <span className="tnum font-medium">{quantity(channel.listingCount)}</span>
        </div>
        <Button variant="secondary" size="sm" className="w-full" onClick={onTest} disabled={busy}>
          {busy ? (
            <Loader2 className="size-3.5 animate-spin" aria-hidden="true" />
          ) : (
            <Cable className="size-3.5" aria-hidden="true" />
          )}
          {busy ? 'Đang kiểm tra…' : 'Kiểm tra kết nối'}
        </Button>
        {test ? (
          <div
            role="status"
            className="rounded-[var(--radius-control)] border border-border bg-surface-subtle px-3 py-2 text-xs text-muted"
          >
            <p className="font-medium text-ink">
              {test.ok ? 'Adapter phản hồi' : 'Adapter lỗi'} · {test.mode}
            </p>
            <p className="mt-0.5">{test.message}</p>
            <p className="mt-0.5 tnum">{dateTime(test.checkedAt)}</p>
          </div>
        ) : null}
      </CardBody>
    </Card>
  );
}

export function ChannelsPage() {
  const [tests, setTests] = useState<Record<string, ConnectionTest>>({});
  const [busyId, setBusyId] = useState<string | null>(null);
  const [testError, setTestError] = useState<string | null>(null);

  const [term, setTerm] = useState('');
  const [listingChannel, setListingChannel] = useState('');
  const [syncStatus, setSyncStatus] = useState('');
  const [page, setPage] = useState(1);
  const q = useDebouncedValue(term);

  const { data, loading, error, reload } = useAsync(
    () =>
      Promise.all([
        listChannels(),
        listChannelListings({
          q,
          channelId: listingChannel || undefined,
          syncStatus: syncStatus || undefined,
          page,
          pageSize: 10,
        }),
      ]).then(([channels, listings]) => ({ channels, listings })),
    [q, listingChannel, syncStatus, page],
  );

  async function onTest(channelId: string) {
    setBusyId(channelId);
    setTestError(null);
    try {
      const result = await testChannelConnection(channelId);
      setTests((prev) => ({ ...prev, [channelId]: result }));
    } catch (err) {
      setTestError(
        err instanceof Error ? err.message : 'Không kiểm tra được kết nối.',
      );
    } finally {
      setBusyId(null);
    }
  }

  const listingColumns: Column<ChannelListing>[] = [
    {
      key: 'sku',
      header: 'SKU nội bộ',
      render: (l) => <span className="font-mono text-xs font-medium">{l.skuCode}</span>,
    },
    { key: 'product', header: 'Sản phẩm', render: (l) => <span className="line-clamp-1">{l.productName}</span> },
    { key: 'channel', header: 'Kênh', render: (l) => <span className="text-muted">{l.channelName}</span> },
    {
      key: 'external',
      header: 'Listing ID',
      render: (l) => <span className="font-mono text-xs text-muted">{l.externalListingId}</span>,
    },
    {
      key: 'price',
      header: 'Giá trên sàn',
      align: 'right',
      render: (l) => <span className="tnum">{money(l.currentPrice)}</span>,
    },
    {
      key: 'sync',
      header: 'Đồng bộ',
      render: (l) => {
        const s = mappingSyncStatus(l.syncStatus);
        return <StatusPill tone={s.tone}>{s.label}</StatusPill>;
      },
    },
    {
      key: 'last',
      header: 'Lần cuối',
      align: 'right',
      render: (l) => <span className="tnum text-muted">{dateTime(l.lastSyncedAt)}</span>,
    },
  ];

  return (
    <>
      <PageHeader
        title="Kênh bán & mapping"
        description="Cấu hình kênh, chế độ tích hợp, phí nền tảng và mapping SKU nội bộ với listing của sàn."
        actions={<DemoBadge />}
      />

      <div className="mb-4 flex items-start gap-2 rounded-[var(--radius-card)] border border-warning/30 bg-warning/5 px-4 py-3 text-sm text-ink">
        <ShieldAlert className="mt-0.5 size-4 shrink-0 text-warning" aria-hidden="true" />
        <p>
          Chỉ bật <span className="font-medium">LIVE</span> khi có credential, quyền API và kiểm thử
          sandbox hợp lệ. Nút cập nhật giá thật không hiển thị nếu thiếu quyền.
        </p>
      </div>

      {testError ? (
        <p
          role="alert"
          className="mb-4 rounded-[var(--radius-control)] bg-danger/10 px-3 py-2 text-xs text-danger"
        >
          {testError}
        </p>
      ) : null}

      {loading && !data ? (
        <LoadingState />
      ) : error || !data ? (
        <ErrorState message={error ?? 'Không tải được kênh bán.'} onRetry={reload} />
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
            {data.channels.map((c) => (
              <ChannelCard
                key={c.id}
                channel={c}
                test={tests[c.id]}
                busy={busyId === c.id}
                onTest={() => onTest(c.id)}
              />
            ))}
          </div>

          <Card className="mt-4">
            <CardHeader
              title="Mapping listing"
              subtitle="SKU nội bộ ↔ listing ID trên sàn · trạng thái đồng bộ"
              action={<Link2 className="size-4 text-muted" aria-hidden="true" />}
            />
            <div className="flex flex-col gap-3 border-b border-border p-4 lg:flex-row lg:items-center">
              <div className="relative flex-1">
                <Search
                  className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted"
                  aria-hidden="true"
                />
                <Input
                  value={term}
                  onChange={(e) => {
                    setTerm(e.target.value);
                    setPage(1);
                  }}
                  placeholder="Tìm SKU, sản phẩm, listing ID…"
                  aria-label="Tìm mapping listing"
                  className="pl-8"
                />
              </div>
              <Select
                value={listingChannel}
                onChange={(e) => {
                  setListingChannel(e.target.value);
                  setPage(1);
                }}
                aria-label="Lọc theo kênh"
                className="lg:w-48"
              >
                <option value="">Tất cả kênh</option>
                {data.channels.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </Select>
              <Select
                value={syncStatus}
                onChange={(e) => {
                  setSyncStatus(e.target.value);
                  setPage(1);
                }}
                aria-label="Lọc theo trạng thái đồng bộ"
                className="lg:w-48"
              >
                <option value="">Mọi trạng thái</option>
                <option value="SYNCED">Đã đồng bộ</option>
                <option value="PENDING">Chờ đồng bộ</option>
                <option value="ERROR">Lỗi đồng bộ</option>
                <option value="NOT_MAPPED">Chưa map</option>
              </Select>
            </div>

            {loading && !data ? (
              <LoadingState />
            ) : (
              <>
                <DataTable
                  columns={listingColumns}
                  rows={data.listings.data}
                  rowKey={(l) => l.id}
                  caption="Mapping listing theo kênh"
                  emptyMessage="Không có mapping phù hợp."
                />
                <Pagination
                  page={data.listings.meta.page}
                  totalPages={data.listings.meta.totalPages}
                  total={data.listings.meta.total}
                  onPage={setPage}
                />
              </>
            )}
            {loading && data ? (
              <p className="px-4 pb-2 text-xs text-muted" role="status">
                Đang cập nhật…
              </p>
            ) : null}
          </Card>
        </>
      )}
    </>
  );
}
