import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Download, Plus, Search, Upload } from 'lucide-react';
import {
  Button,
  Card,
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
import { listProducts, listSuppliers } from '@/mocks/api';
import { CATEGORIES } from '@/mocks/data';
import { downloadCsv } from '@/lib/csv';
import { dateTime, money, quantity } from '@/lib/format';
import type { Product } from '@/types/domain';

export function ProductsPage() {
  const [searchParams] = useSearchParams();
  const urlQuery = searchParams.get('q') ?? '';
  const [term, setTerm] = useState(urlQuery);
  const [categoryId, setCategoryId] = useState('');
  const [supplierId, setSupplierId] = useState('');
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(1);
  const q = useDebouncedValue(term);

  useEffect(() => {
    setTerm(urlQuery);
    setPage(1);
  }, [urlQuery]);

  const { data, loading, error, reload } = useAsync(
    () =>
      Promise.all([
        listProducts({
          q,
          categoryId: categoryId || undefined,
          supplierId: supplierId || undefined,
          status: status || undefined,
          page,
          pageSize: 10,
        }),
        listSuppliers(),
      ]).then(([products, suppliers]) => ({ products, suppliers })),
    [q, categoryId, supplierId, status, page],
  );

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
    {
      key: 'name',
      header: 'Sản phẩm',
      sortable: true,
      sortValue: (p) => p.name,
      render: (p) => (
        <div className="min-w-0">
          <p className="truncate font-medium text-ink">{p.name}</p>
          {p.variantName ? <p className="text-xs text-muted">{p.variantName}</p> : null}
        </div>
      ),
    },
    { key: 'category', header: 'Danh mục', render: (p) => <span className="text-muted">{p.categoryName}</span> },
    {
      key: 'supplier',
      header: 'Nhà cung cấp',
      render: (p) => <span className="text-muted">{p.supplierName ?? '—'}</span>,
    },
    {
      key: 'cost',
      header: 'Giá vốn',
      align: 'right',
      sortable: true,
      sortValue: (p) => p.unitCost,
      render: (p) => <span className="tnum">{money(p.unitCost)}</span>,
    },
    {
      key: 'price',
      header: 'Giá bán',
      align: 'right',
      sortable: true,
      sortValue: (p) => p.currentPrice,
      render: (p) => <span className="tnum">{money(p.currentPrice)}</span>,
    },
    {
      key: 'available',
      header: 'Tồn khả dụng',
      align: 'right',
      sortable: true,
      sortValue: (p) => p.availableQty ?? -1,
      render: (p) => <span className="tnum">{quantity(p.availableQty)}</span>,
    },
    {
      key: 'status',
      header: 'Trạng thái',
      render: (p) =>
        p.status === 'ACTIVE' ? (
          <StatusPill tone="success">Đang bán</StatusPill>
        ) : (
          <StatusPill tone="neutral">Lưu trữ</StatusPill>
        ),
    },
    {
      key: 'updated',
      header: 'Cập nhật',
      align: 'right',
      render: (p) => <span className="tnum text-muted">{dateTime(p.updatedAt)}</span>,
    },
  ];

  function exportCsv() {
    const rows = (data?.products.data ?? []).map((p) => [
      p.skuCode,
      p.name,
      p.categoryName,
      p.supplierName ?? '',
      p.unitCost,
      p.currentPrice,
      p.availableQty,
      p.status,
    ]);
    downloadCsv(
      'san-pham.csv',
      ['SKU', 'Sản phẩm', 'Danh mục', 'Nhà cung cấp', 'Giá vốn', 'Giá bán', 'Tồn khả dụng', 'Trạng thái'],
      rows,
    );
  }

  return (
    <>
      <PageHeader
        title="Sản phẩm / SKU"
        description="Danh mục sản phẩm, giá vốn và giá bán hiện tại. Không xoá cứng sản phẩm đã phát sinh lịch sử."
        actions={
          <>
            <DemoBadge />
            <Button
              variant="secondary"
              size="sm"
              onClick={exportCsv}
              disabled={!data || data.products.data.length === 0}
            >
              <Download className="size-4" aria-hidden="true" />
              Xuất CSV
            </Button>
            <Button
              variant="secondary"
              size="sm"
              disabled
              title="Chưa khả dụng trong bản demo — cần API import"
            >
              <Upload className="size-4" aria-hidden="true" />
              Import CSV
            </Button>
            <Button
              variant="primary"
              size="sm"
              disabled
              title="Chưa khả dụng trong bản demo — cần API tạo sản phẩm"
            >
              <Plus className="size-4" aria-hidden="true" />
              Tạo sản phẩm
            </Button>
          </>
        }
      />

      <Card>
        <div className="flex flex-col gap-3 border-b border-border p-4 lg:flex-row lg:items-center">
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted" aria-hidden="true" />
            <Input
              value={term}
              onChange={(e) => {
                setTerm(e.target.value);
                setPage(1);
              }}
              placeholder="Tìm theo mã SKU hoặc tên sản phẩm…"
              aria-label="Tìm sản phẩm"
              className="pl-8"
            />
          </div>
          <Select
            value={categoryId}
            onChange={(e) => {
              setCategoryId(e.target.value);
              setPage(1);
            }}
            aria-label="Lọc theo danh mục"
            className="lg:w-44"
          >
            <option value="">Tất cả danh mục</option>
            {CATEGORIES.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </Select>
          <Select
            value={supplierId}
            onChange={(e) => {
              setSupplierId(e.target.value);
              setPage(1);
            }}
            aria-label="Lọc theo nhà cung cấp"
            className="lg:w-52"
          >
            <option value="">Tất cả nhà cung cấp</option>
            {(data?.suppliers ?? []).map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </Select>
          <Select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
            aria-label="Lọc theo trạng thái"
            className="lg:w-40"
          >
            <option value="">Mọi trạng thái</option>
            <option value="ACTIVE">Đang bán</option>
            <option value="ARCHIVED">Lưu trữ</option>
          </Select>
        </div>

        {loading && !data ? (
          <LoadingState />
        ) : error || !data ? (
          <ErrorState message={error ?? 'Không tải được sản phẩm.'} onRetry={reload} />
        ) : (
          <>
            <DataTable
              columns={columns}
              rows={data.products.data}
              rowKey={(p) => p.id}
              caption="Danh sách sản phẩm"
              emptyMessage="Không có sản phẩm phù hợp bộ lọc."
            />
            <Pagination
              page={data.products.meta.page}
              totalPages={data.products.meta.totalPages}
              total={data.products.meta.total}
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

      <p className="mt-3 text-xs text-muted">
        Tổng {data ? quantity(data.products.meta.total) : '—'} SKU · giá vốn và giá bán hiển thị
        theo VND.
      </p>
    </>
  );
}
