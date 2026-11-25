import { useQuery } from '@tanstack/react-query';
import { EmptyState } from '../components/common/EmptyState';
import { ListingSkeleton } from '../components/common/ListingSkeleton';
import { ListingCard } from '../components/listing/ListingCard';
import { fetchListings } from '../services/listingService';

export function HomePage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['listings-base'],
    queryFn: () => fetchListings({ limit: 12, page: 1 }),
  });

  return (
    <div className="space-y-6">
      <section className="rounded-3xl border border-teal-100 bg-white p-6 shadow-xs sm:p-8">
        <div className="max-w-3xl">
          <span className="inline-flex items-center rounded-full bg-teal-50 px-3 py-1 text-xs font-semibold text-[#0F766E]">
            Giao diện nền tảng (Base UI) · Nhóm 12 - 65HTTT
          </span>
          <h1 className="mt-3 text-2xl font-bold tracking-tight text-[#134E4A] sm:text-3xl">
            Hệ thống tìm kiếm nhà thuê thông minh (Hà Nội)
          </h1>
          <p className="mt-2 text-sm text-[#475569] sm:text-base">
            Trang chủ hiển thị danh sách phòng mẫu từ Backend FastAPI & Supabase để các gói chức năng tích hợp bộ lọc, gợi ý AI và bản đồ.
          </p>
        </div>
      </section>

      <section className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-[#134E4A]">
          Danh sách phòng hiện có ({data?.total ?? 0})
        </h2>
      </section>

      {isLoading ? (
        <ListingSkeleton count={6} />
      ) : isError ? (
        <EmptyState
          title="Không kết nối được tới máy chủ API"
          description="Hãy đảm bảo Backend FastAPI đang chạy tại cổng 8000 (uvicorn src.backend.api.main:app --reload)."
        />
      ) : !data?.items?.length ? (
        <EmptyState
          title="Chưa có dữ liệu phòng"
          description="Hãy chạy pipeline thu thập dữ liệu để nạp phòng vào Supabase."
        />
      ) : (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {data.items.map((item) => (
            <ListingCard key={item.fact_id} listing={item} />
          ))}
        </div>
      )}
    </div>
  );
}
