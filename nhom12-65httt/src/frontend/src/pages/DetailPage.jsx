import { ArrowLeft } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';

export function DetailPage() {
  const { id } = useParams();

  return (
    <div className="space-y-4">
      <Link
        to="/"
        className="inline-flex min-h-11 items-center gap-1.5 text-sm font-medium text-[#0F766E] hover:underline"
      >
        <ArrowLeft className="h-4 w-4" />
        Quay lại trang chủ
      </Link>

      <section className="rounded-2xl border border-dashed border-teal-200 bg-white p-8">
        <h1 className="text-xl font-bold text-[#134E4A]">Trang Chi tiết phòng trọ (Khung chờ)</h1>
        <p className="mt-2 text-sm text-[#475569]">
          Mã phòng đang chọn: <code className="rounded bg-slate-100 px-2 py-0.5">{id}</code>
        </p>
        <p className="mt-2 text-sm text-[#475569]">
          Khu vực dành cho <strong>Gói Chức năng 3</strong>: hiển thị đầy đủ hình ảnh, tiện nghi, máy tính tổng chi phí thuê, thẻ cảnh báo rủi ro, checklist đi xem phòng và form báo cáo tin sai sự thật.
        </p>
      </section>
    </div>
  );
}
