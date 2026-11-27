import { useState, type ReactNode } from 'react';
import { Link, useParams } from 'react-router-dom';
import { AlertTriangle, ArrowLeft } from 'lucide-react';
import {
  Button,
  Card,
  CardBody,
  CardHeader,
  DemoBadge,
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
  StatusPill,
} from '@/components/ui/primitives';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { useAsync } from '@/hooks/useAsync';
import { getProductDetail } from '@/mocks/api';
import { dateTime, money, percent, quantity } from '@/lib/format';
import { mappingSyncStatus, recommendationStatus } from '@/lib/status';
import type { ChannelListing, Recommendation } from '@/types/domain';

type Tab = 'overview' | 'cost' | 'stock' | 'pricing' | 'listings';

const TABS: { key: Tab; label: string }[] = [
  { key: 'overview', label: 'Thông tin chung' },
  { key: 'cost', label: 'Giá vốn' },
  { key: 'stock', label: 'Tồn kho' },
  { key: 'pricing', label: 'Lịch sử định giá' },
  { key: 'listings', label: 'Listing kênh' },
];

function Row({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-border py-2.5 last:border-0">
      <span className="text-xs text-muted">{label}</span>
      <span className="text-right text-sm font-medium text-ink">{value}</span>
    </div>
  );
}

export function ProductDetailPage() {
  const { id = '' } = useParams();
  const { data, loading, error, reload } = useAsync(() => getProductDetail(id), [id]);
  const [tab, setTab] = useState<Tab>('overview');

  if (loading) return <LoadingState label="Đang tải sản phẩm…" />;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (!data) return <ErrorState message="Không tìm thấy sản phẩm." onRetry={reload} />;

  const { product, inventory, recommendations, listings } = data;
  const landedCost =
    product.costBreakdown.purchase +
    product.costBreakdown.inbound +
    product.costBreakdown.packaging +
    product.costBreakdown.other;
  const available = inventory
    ? inventory.onHandQty - inventory.reservedQty
    : null;
  const lowStock =
    inventory !== null && available !== null && available <= inventory.reorderPoint;

  const costRows = [
    { label: 'Giá mua', value: product.costBreakdown.purchase },
    { label: 'Vận chuyển đầu vào', value: product.costBreakdown.inbound },
    { label: 'Đóng gói', value: product.costBreakdown.packaging },
    { label: 'Chi phí khác', value: product.costBreakdown.other },
  ];

  const recommendationColumns: Column<Recommendation>[] = [
    {
      key: 'id',
      header: 'Mã',
      render: (r) => (
        <Link
          to={`/pricing/recommendations/${r.id}`}
          className="font-mono text-xs font-medium text-primary hover:underline"
        >
          {r.id}
        </Link>
      ),
    },
    { key: 'channel', header: 'Kênh', render: (r) => r.channelName },
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
      render: (r) => <span className="tnum font-medium">{money(r.recommendedPrice)}</span>,
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
      render: (r) => {
        const s = recommendationStatus(r.status);
        return <StatusPill tone={s.tone}>{s.label}</StatusPill>;
      },
    },
    {
      key: 'created',
      header: 'Tạo lúc',
      align: 'right',
      render: (r) => <span className="tnum text-muted">{dateTime(r.createdAt)}</span>,
    },
  ];

  const listingColumns: Column<ChannelListing>[] = [
    { key: 'channel', header: 'Kênh', render: (l) => l.channelName },
    {
      key: 'external',
      header: 'Listing ID',
      render: (l) => <span className="font-mono text-xs">{l.externalListingId}</span>,
    },
    {
      key: 'externalSku',
      header: 'SKU sàn',
      render: (l) => <span className="font-mono text-xs text-muted">{l.externalSku}</span>,
    },
    {
      key: 'price',
      header: 'Giá đang bán',
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
      key: 'lastSynced',
      header: 'Lần cuối',
      align: 'right',
      render: (l) => <span className="tnum text-muted">{dateTime(l.lastSyncedAt)}</span>,
    },
  ];

  return (
    <>
      <Link
        to="/products"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted hover:text-ink"
      >
        <ArrowLeft className="size-4" aria-hidden="true" />
        Quay lại danh sách
      </Link>

      <PageHeader
        title={product.name}
        description={`${product.skuCode}${product.variantName ? ` · ${product.variantName}` : ''} · ${product.categoryName}`}
        actions={
          <>
            <DemoBadge />
            {product.status === 'ACTIVE' ? (
              <StatusPill tone="success">Đang bán</StatusPill>
            ) : (
              <StatusPill tone="neutral">Lưu trữ</StatusPill>
            )}
            <Button
              variant="secondary"
              size="sm"
              disabled
              title="Chưa khả dụng trong bản demo"
            >
              Sửa sản phẩm
            </Button>
          </>
        }
      />

      <div className="mb-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Card className="p-4">
          <p className="text-xs text-muted">Giá bán hiện tại</p>
          <p className="tnum mt-1 text-lg font-semibold">{money(product.currentPrice)}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-muted">Landed cost / đơn vị</p>
          <p className="tnum mt-1 text-lg font-semibold">{money(landedCost)}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-muted">Tồn khả dụng</p>
          <p className={`tnum mt-1 text-lg font-semibold ${lowStock ? 'text-danger' : 'text-ink'}`}>
            {quantity(available)}
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-muted">Biên gộp ước tính</p>
          <p className="tnum mt-1 text-lg font-semibold">
            {percent(
              product.currentPrice > 0
                ? (product.currentPrice - landedCost) / product.currentPrice
                : null,
              1,
            )}
          </p>
        </Card>
      </div>

      <div className="mb-4 flex flex-wrap gap-1 border-b border-border" role="tablist" aria-label="Chi tiết sản phẩm">
        {TABS.map((item) => (
          <button
            key={item.key}
            type="button"
            role="tab"
            aria-selected={tab === item.key}
            onClick={() => setTab(item.key)}
            className={`-mb-px border-b-2 px-3 py-2 text-sm transition-colors ${
              tab === item.key
                ? 'border-primary font-medium text-primary'
                : 'border-transparent text-muted hover:text-ink'
            }`}
          >
            {item.label}
          </button>
        ))}
      </div>

      {tab === 'overview' ? (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader title="Thông tin SKU" />
            <CardBody className="py-1">
              <Row label="Mã SKU" value={<span className="font-mono">{product.skuCode}</span>} />
              <Row label="Danh mục" value={product.categoryName} />
              <Row label="Đơn vị tính" value={product.unit} />
              <Row label="Nhà cung cấp" value={product.supplierName ?? '—'} />
              <Row label="Cập nhật lúc" value={dateTime(product.updatedAt)} />
            </CardBody>
          </Card>
          <Card>
            <CardHeader title="Cấu trúc giá" subtitle="Giá vốn chưa bao gồm phí kênh" />
            <CardBody className="py-1">
              <Row label="Landed cost" value={money(landedCost)} />
              <Row label="Giá bán hiện tại" value={money(product.currentPrice)} />
              <Row
                label="Lợi nhuận gộp / đơn vị (chưa trừ phí kênh)"
                value={money(product.currentPrice - landedCost)}
              />
              <Row
                label="Cảnh báo tồn kho"
                value={
                  lowStock ? (
                    <span className="inline-flex items-center gap-1.5 text-danger">
                      <AlertTriangle className="size-3.5" aria-hidden="true" />
                      Dưới ngưỡng đặt lại
                    </span>
                  ) : (
                    'Không'
                  )
                }
              />
            </CardBody>
          </Card>
        </div>
      ) : null}

      {tab === 'cost' ? (
        <Card>
          <CardHeader
            title="Giá vốn cấu thành"
            subtitle="Chi phí hiện hành dùng cho lần chạy định giá tiếp theo"
          />
          <CardBody>
            <div className="overflow-hidden rounded-[var(--radius-control)] border border-border">
              <table className="w-full text-sm">
                <caption className="sr-only">Cấu thành giá vốn</caption>
                <thead>
                  <tr className="border-b border-border bg-surface-subtle text-xs text-muted">
                    <th scope="col" className="px-3 py-2 text-left font-medium">Thành phần</th>
                    <th scope="col" className="px-3 py-2 text-right font-medium">Giá trị</th>
                    <th scope="col" className="px-3 py-2 text-right font-medium">Tỷ trọng</th>
                  </tr>
                </thead>
                <tbody>
                  {costRows.map((row) => (
                    <tr key={row.label} className="border-b border-border last:border-0">
                      <td className="px-3 py-2">{row.label}</td>
                      <td className="tnum px-3 py-2 text-right">{money(row.value)}</td>
                      <td className="tnum px-3 py-2 text-right text-muted">
                        {percent(landedCost > 0 ? row.value / landedCost : null, 1)}
                      </td>
                    </tr>
                  ))}
                  <tr className="bg-surface-subtle font-medium">
                    <td className="px-3 py-2">Tổng landed cost</td>
                    <td className="tnum px-3 py-2 text-right">{money(landedCost)}</td>
                    <td className="tnum px-3 py-2 text-right">100.0%</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p className="mt-3 text-xs text-muted">
              Phí kênh là chi phí biến đổi theo giá bán, không cộng vào giá vốn để tránh tính
              hai lần (SPEC §7.4).
            </p>
          </CardBody>
        </Card>
      ) : null}

      {tab === 'stock' ? (
        inventory ? (
          <Card>
            <CardHeader title="Tồn kho hiện tại" subtitle={inventory.warehouseName} />
            <CardBody>
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                <div>
                  <p className="text-xs text-muted">Tồn thực tế</p>
                  <p className="tnum mt-1 text-lg font-semibold">{quantity(inventory.onHandQty)}</p>
                </div>
                <div>
                  <p className="text-xs text-muted">Giữ chỗ</p>
                  <p className="tnum mt-1 text-lg font-semibold text-muted">
                    {quantity(inventory.reservedQty)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted">Khả dụng</p>
                  <p className={`tnum mt-1 text-lg font-semibold ${lowStock ? 'text-danger' : 'text-ink'}`}>
                    {quantity(available)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted">Ngưỡng đặt lại</p>
                  <p className="tnum mt-1 text-lg font-semibold text-muted">
                    {quantity(inventory.reorderPoint)}
                  </p>
                </div>
              </div>
              <p className="mt-4 text-xs text-muted">
                available = on_hand − reserved · Cập nhật {dateTime(inventory.updatedAt)}. Tồn
                thấp chỉ là tín hiệu cho analyst, không tự động giảm giá.
              </p>
            </CardBody>
          </Card>
        ) : (
          <Card>
            <EmptyState
              title="SKU chưa có bản ghi tồn kho"
              description="Thêm tồn kho cho SKU này trước khi chạy định giá tự động."
            />
          </Card>
        )
      ) : null}

      {tab === 'pricing' ? (
        <Card>
          <CardHeader
            title="Lịch sử định giá"
            subtitle={`${recommendations.length} đề xuất cho SKU này`}
            action={
              <Link
                to="/pricing/run"
                className="text-xs font-medium text-primary hover:underline"
              >
                Chạy định giá
              </Link>
            }
          />
          <DataTable
            columns={recommendationColumns}
            rows={recommendations}
            rowKey={(r) => r.id}
            caption="Lịch sử đề xuất giá của SKU"
            emptyMessage="Chưa có đề xuất nào cho SKU này."
          />
        </Card>
      ) : null}

      {tab === 'listings' ? (
        <Card>
          <CardHeader
            title="Listing trên kênh bán"
            subtitle="Mapping SKU nội bộ với listing của sàn"
          />
          <DataTable
            columns={listingColumns}
            rows={listings}
            rowKey={(l) => l.id}
            caption="Listing kênh của SKU"
            emptyMessage="SKU chưa được map lên kênh nào."
          />
        </Card>
      ) : null}
    </>
  );
}
