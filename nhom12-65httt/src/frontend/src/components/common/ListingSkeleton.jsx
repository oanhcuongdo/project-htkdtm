export function ListingSkeleton({ count = 6 }) {
  return (
    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: count }).map((_, idx) => (
        <div
          key={idx}
          className="overflow-hidden rounded-2xl border border-slate-200 bg-white p-4 shadow-xs animate-pulse"
        >
          <div className="mb-3 h-44 w-full rounded-xl bg-[#E8F0F3]" />
          <div className="mb-2 h-5 w-3/4 rounded bg-[#E8F0F3]" />
          <div className="mb-4 h-4 w-1/2 rounded bg-[#E8F0F3]" />
          <div className="flex items-center justify-between">
            <div className="h-6 w-28 rounded bg-[#E8F0F3]" />
            <div className="h-9 w-20 rounded-lg bg-[#E8F0F3]" />
          </div>
        </div>
      ))}
    </div>
  );
}
