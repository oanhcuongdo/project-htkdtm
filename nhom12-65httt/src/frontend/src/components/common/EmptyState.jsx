import { SearchX } from 'lucide-react';

export function EmptyState({
  title = 'Chưa tìm thấy phòng phù hợp',
  description = 'Thử nới rộng khoảng giá, bỏ bớt bộ lọc hoặc tìm khu vực lân cận.',
  action,
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-teal-200 bg-white px-6 py-12 text-center">
      <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-teal-50 text-[#0F766E]">
        <SearchX className="h-6 w-6" aria-hidden="true" />
      </div>
      <h3 className="text-base font-semibold text-[#134E4A]">{title}</h3>
      <p className="mt-1 max-w-md text-sm text-[#475569]">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
