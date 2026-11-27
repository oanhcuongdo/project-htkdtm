import { Link } from 'react-router-dom';
import { Card } from '@/components/ui/primitives';

export function NotFoundPage() {
  return (
    <Card className="p-10 text-center">
      <p className="text-sm font-semibold text-muted">404</p>
      <h1 className="mt-2 text-xl font-semibold text-ink">Không tìm thấy trang</h1>
      <p className="mt-1 text-sm text-muted">Đường dẫn không tồn tại hoặc đã bị di chuyển.</p>
      <div className="mt-6 flex justify-center">
        <Link
          to="/dashboard"
          className="inline-flex h-9 items-center rounded-[var(--radius-control)] bg-primary px-4 text-sm font-medium text-white hover:bg-primary-hover"
        >
          Về tổng quan
        </Link>
      </div>
    </Card>
  );
}