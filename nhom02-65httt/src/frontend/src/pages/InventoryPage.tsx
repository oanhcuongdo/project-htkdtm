import { useMemo, useState } from 'react';
import { AlertTriangle, Boxes, PackageCheck, Search, Timer } from 'lucide-react';
import {
  Card,
  DemoBadge,
  ErrorState,
  Input,
  KpiCard,
  LoadingState,
  PageHeader,
  StatusPill,
} from '@/components/ui/primitives';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { useAsync } from '@/hooks/useAsync';
import { useDebouncedValue } from '@/hooks/useDebouncedValue';
import { listInventory } from '@/mocks/api';
import { dateTime, quantity } from '@/lib/format';
import type { InventoryBalance } from '@/types/domain';

export function InventoryPage() {
  const [term, setTerm] = useState('');
  const q = useDebouncedValue(term);
  const { data, loading, error, reload } = useAsync(() => listInventory(q), [q]);

  const kpis = useMemo(() => {
    const items = data ?? [];
    const available = (i: InventoryBalance) => i.onHandQty - i.reservedQty;
    return {
      total: items.length,
      low: items.filter((i) => available(i) <= i.reorderPoint).length,
      available: items.reduce((sum, i) => sum + available(i), 0),
      stale: items.filter((i) => Date.now() - new Date(i.updatedAt).getTime() > 2 * 36e5).length,
    };
  }, [data]);

  const columns: Column<InventoryBalance>[] = [
    {
      key: 'sku',
      header: 'SKU',
      sortable: true,
      sortValue: (i) => i.skuCode,
      render: (i) => <span className="font-mono text-xs font-medium">{i.skuCode}</span>,
    },
    { key: 'product', header: 'Sản phẩm', render: (i) => <span className="line-clamp-1">{i.productName}</span> },
    { key: 'warehouse', header: 'Kho', render: (i) => <span className="text-muted">{i.warehouseName}</span> },
    {
      key: 'onHand',
      header: 'Tồn thực tế',
      align: 'right',
      sortable: true,
      sortValue: (i) => i.onHandQty,
      render: (i) => <span className="tnum">{quantity(i.onHandQty)}</span>,
    },
    {
      key: 'reserved',
      header: 'Giữ chỗ',
      align: 'right',
      render: (i) => <span className="tnum text-muted">{quantity(i.reservedQty)}</span>,
    },
    {
      key: 'available',
      header: 'Khả dụng',
      align: 'right',
      sortable: true,
      sortValue: (i) => i.onHandQty - i.reservedQty,
      render: (i) => {
        const avail = i.onHandQty - i.reservedQty;
        return (
          <span className={`tnum font-medium ${avail <= i.reorderPoint ? 'text-danger' : 'text-ink'}`}>
            {quantity(avail)}
          </span>
        );
      },
    },
    {
      key: 'reorder',
      header: 'Ngưỡng',
      align: 'right',
      render: (i) => <span className="tnum text-muted">{quantity(i.reorderPoint)}</span>,
    },
    {
      key: 'updated',
      header: 'Cập nhật',
      align: 'right',
      render: (i) => <span className="tnum text-muted">{dateTime(i.updatedAt)}</span>,
    },
  ];

  return (
    <>
      <PageHeader
        title="Tồn kho"
        description="Tồn thực tế, giữ chỗ và khả dụng. available = on_hand − reserved."
        actions={<DemoBadge />}
      />

      <div className="mb-4 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Tổng SKU theo dõi" value={quantity(kpis.total)} icon={<Boxes className="size-4" />} />
        <KpiCard
          label="SKU tồn thấp"
          value={quantity(kpis.low)}
          tone="danger"
          hint={kpis.low > 0 ? 'Cần bổ sung hoặc điều chỉnh' : 'Trong ngưỡng an toàn'}
          icon={<AlertTriangle className="size-4" />}
        />
        <KpiCard label="Tổng khả dụng" value={quantity(kpis.available)} icon={<PackageCheck className="size-4" />} />
        <KpiCard
          label="Dữ liệu cũ > 2 giờ"
          value={quantity(kpis.stale)}
          tone={kpis.stale > 0 ? 'warning' : 'success'}
          hint="Đồng bộ kho theo ngưỡng cấu hình"
          icon={<Timer className="size-4" />}
        />
      </div>

      <Card>
        <div className="border-b border-border p-4">
          <div className="relative max-w-md">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted" aria-hidden="true" />
            <Input
              value={term}
              onChange={(e) => setTerm(e.target.value)}
              placeholder="Tìm SKU, sản phẩm, kho…"
              aria-label="Tìm tồn kho"
              className="pl-8"
            />
          </div>
        </div>

        {loading && !data ? (
          <LoadingState />
        ) : error || !data ? (
          <ErrorState message={error ?? 'Không tải được tồn kho.'} onRetry={reload} />
        ) : (
          <DataTable
            columns={columns}
            rows={data}
            rowKey={(i) => i.id}
            caption="Bảng tồn kho"
            emptyMessage="Không có bản ghi tồn kho phù hợp."
          />
        )}
        {loading && data ? (
          <p className="px-4 pb-2 text-xs text-muted" role="status">
            Đang cập nhật…
          </p>
        ) : null}
      </Card>

      <div className="mt-3 flex items-start gap-2 text-xs text-muted">
        <StatusPill tone="info">Lưu ý</StatusPill>
        Tồn thấp không tự động nghĩa là phải giảm giá; đây chỉ là tín hiệu cho analyst (UI_SPEC UI-05).
      </div>
    </>
  );
}