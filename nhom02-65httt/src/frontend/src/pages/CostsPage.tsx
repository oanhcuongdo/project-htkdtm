import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Download, Search } from 'lucide-react';
import {
  Button,
  Card,
  CardBody,
  DemoBadge,
  ErrorState,
  Input,
  KpiCard,
  LoadingState,
  PageHeader,
  Select,
} from '@/components/ui/primitives';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { useAsync } from '@/hooks/useAsync';
import { useDebouncedValue } from '@/hooks/useDebouncedValue';
import { listProducts, listSuppliers } from '@/mocks/api';
import { downloadCsv } from '@/lib/csv';
import { money } from '@/lib/format';
import type { Product } from '@/types/domain';

export function CostsPage() {
  const [term, setTerm] = useState('');
  const [supplierId, setSupplierId] = useState('');
  const q = useDebouncedValue(term);

  const { data, loading, error, reload } = useAsync(
    () =>
      Promise.all([
        listProducts({ q, supplierId: supplierId || undefined, pageSize: 100 }),
        listSuppliers(),
      ]).then(([products, suppliers]) => ({ products, suppliers })),
    [q, supplierId],
  );

  const landed = (p: Product) =>
    p.costBreakdown.purchase +
    p.costBreakdown.inbound +
    p.costBreakdown.packaging +
    p.costBreakdown.other;

  const summary = useMemo(() => {
    const items = data?.products.data ?? [];
    if (items.length === 0) return { count: 0, avg: null as number | null };
    return {
      count: items.length,
      avg: Math.round(items.reduce((sum, p) => sum + landed(p), 0) / items.length),
    };
  }, [data]);

  const columns: Column<Product>[] = [
    {
      key: 'sku',
      header: 'SKU',
      sortable: true,
      sortValue: (p) => p.skuCode,
      render: (p) => (
        <Link
          to={`/products/${p.id}`}
          className="font-mono text-xs font-medium text-primary hover:underline"
        >
          {p.skuCode}
        </Link>
      ),
    },
    { key: 'name', header: 'Sản phẩm', render: (p) => <span className="line-clamp-1">{p.name}</span> },
    {
      key: 'supplier',
      header: 'Nhà cung cấp',
      render: (p) => <span className="text-muted">{p.supplierName ?? '—'}</span>,
    },
    {
      key: 'purchase',
      header: 'Giá mua',
      align: 'right',
      render: (p) => <span className="tnum">{money(p.costBreakdown.purchase)}</span>,
    },
    {
      key: 'inbound',
      header: 'Vận chuyển',
      align: 'right',
      render: (p) => <span className="tnum text-muted">{money(p.costBreakdown.inbound)}</span>,
    },
    {
      key: 'packaging',
      header: 'Đóng gói',
      align: 'right',
      render: (p) => <span className="tnum text-muted">{money(p.costBreakdown.packaging)}</span>,
    },
    {
      key: 'other',
      header: 'Khác',
      align: 'right',
      render: (p) => <span className="tnum text-muted">{money(p.costBreakdown.other)}</span>,
    },
    {
      key: 'landed',
      header: 'Landed cost',
      align: 'right',
      sortable: true,
      sortValue: landed,
      render: (p) => <span className="tnum font-medium">{money(landed(p))}</span>,
    },
    {
      key: 'price',
      header: 'Giá bán',
      align: 'right',
      render: (p) => <span className="tnum text-muted">{money(p.currentPrice)}</span>,
    },
  ];

  function exportCsv() {
    const rows = (data?.products.data ?? []).map((p) => [
      p.skuCode,
      p.name,
      p.supplierName ?? '',
      p.costBreakdown.purchase,
      p.costBreakdown.inbound,
      p.costBreakdown.packaging,
      p.costBreakdown.other,
      landed(p),
      p.currentPrice,
    ]);
    downloadCsv(
      'gia-von.csv',
      [
        'SKU',
        'Sản phẩm',
        'Nhà cung cấp',
        'Giá mua',
        'Vận chuyển',
        'Đóng gói',
        'Chi phí khác',
        'Landed cost',
        'Giá bán',
      ],
      rows,
    );
  }

  return (
    <>
      <PageHeader
        title="Giá vốn"
        description="Landed cost = giá mua + vận chuyển đầu vào + đóng gói + chi phí khác. Phí kênh không nằm trong giá vốn."
        actions={
          <>
            <DemoBadge />
            <Button variant="secondary" size="sm" onClick={exportCsv} disabled={!data}>
              <Download className="size-4" aria-hidden="true" />
              Xuất CSV
            </Button>
          </>
        }
      />

      <div className="mb-4 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="SKU theo bộ lọc" value={String(summary.count)} />
        <KpiCard label="Landed cost trung bình" value={money(summary.avg)} />
        <KpiCard label="Nhà cung cấp" value={String(data?.suppliers.length ?? 0)} />
        <KpiCard
          label="Đơn vị tiền tệ"
          value="VND"
          hint="Định dạng vi-VN, không dùng số lẻ"
        />
      </div>

      <Card>
        <div className="flex flex-col gap-3 border-b border-border p-4 lg:flex-row lg:items-center">
          <div className="relative flex-1">
            <Search
              className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted"
              aria-hidden="true"
            />
            <Input
              value={term}
              onChange={(e) => setTerm(e.target.value)}
              placeholder="Tìm SKU hoặc tên sản phẩm…"
              aria-label="Tìm theo SKU"
              className="pl-8"
            />
          </div>
          <Select
            value={supplierId}
            onChange={(e) => setSupplierId(e.target.value)}
            aria-label="Lọc theo nhà cung cấp"
            className="lg:w-64"
          >
            <option value="">Tất cả nhà cung cấp</option>
            {(data?.suppliers ?? []).map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </Select>
        </div>

        {loading && !data ? (
          <LoadingState />
        ) : error || !data ? (
          <ErrorState message={error ?? 'Không tải được giá vốn.'} onRetry={reload} />
        ) : (
          <DataTable
            columns={columns}
            rows={data.products.data}
            rowKey={(p) => p.id}
            caption="Bảng giá vốn theo SKU"
            emptyMessage="Không có SKU phù hợp bộ lọc."
          />
        )}
      </Card>

      <CardBody className="mt-3 rounded-[var(--radius-card)] border border-border bg-surface-subtle text-xs text-muted">
        Chi phí trong bảng là dữ liệu DEMO phân bổ theo cấu hình. Lịch sử báo giá theo nhà cung
        cấp và ngày hiệu lực sẽ do backend trả về khi nối API thật.
      </CardBody>
    </>
  );
}
