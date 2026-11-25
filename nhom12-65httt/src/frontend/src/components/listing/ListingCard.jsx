import { GraduationCap, MapPin } from 'lucide-react';
import { Link } from 'react-router-dom';
import { formatPricePerM2, formatVND } from '../../utils/formatters';

const FALLBACK_IMAGE =
  'https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=800&q=80';

export function ListingCard({ listing }) {
  const coverImage = listing.images?.[0] || FALLBACK_IMAGE;

  return (
    <article className="group flex flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xs transition-all duration-200 hover:border-[#14B8A6] hover:shadow-md">
      <Link to={`/listings/${listing.fact_id}`} className="relative block h-48 w-full overflow-hidden bg-[#E8F0F3]">
        <img
          src={coverImage}
          alt={listing.title}
          loading="lazy"
          className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
        />
        <span className="absolute left-3 top-3 rounded-full bg-[#134E4A]/85 px-2.5 py-1 text-xs font-medium text-white backdrop-blur-xs">
          {listing.type_name}
        </span>
      </Link>

      <div className="flex flex-1 flex-col justify-between p-4">
        <div>
          <div className="mb-2 flex items-baseline justify-between gap-2">
            <span className="text-lg font-bold text-[#0F766E] tabular-nums-data">
              {formatVND(listing.price)}
            </span>
            <span className="text-xs font-medium text-[#475569] tabular-nums-data">
              {listing.area ? `${listing.area} m²` : 'Chưa rõ m²'} · {formatPricePerM2(listing.price_per_m2)}
            </span>
          </div>

          <Link
            to={`/listings/${listing.fact_id}`}
            className="line-clamp-2 text-base font-semibold text-[#134E4A] transition-colors hover:text-[#0369A1]"
          >
            {listing.title}
          </Link>

          <div className="mt-2.5 space-y-1 text-xs text-[#475569]">
            <p className="flex items-center gap-1.5">
              <MapPin className="h-3.5 w-3.5 shrink-0 text-[#0F766E]" aria-hidden="true" />
              <span className="truncate">
                {[listing.street, listing.ward, listing.district].filter(Boolean).join(', ')}
              </span>
            </p>
            {listing.nearest_university && (
              <p className="flex items-center gap-1.5">
                <GraduationCap className="h-3.5 w-3.5 shrink-0 text-[#0369A1]" aria-hidden="true" />
                <span className="truncate">
                  Cách {listing.nearest_university} ~{listing.distance_to_university_km} km
                </span>
              </p>
            )}
          </div>
        </div>
      </div>
    </article>
  );
}
