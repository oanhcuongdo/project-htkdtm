/*
 * Formatting rules — UI_SPEC.md §7.
 * - VND via Intl, 0 fraction digits.
 * - null shows em dash; 0 shows "0" (never conflated with missing).
 * - Dates dd/MM/yyyy HH:mm in Asia/Ho_Chi_Minh; storage is UTC.
 */

const VND = new Intl.NumberFormat('vi-VN', {
  style: 'currency',
  currency: 'VND',
  maximumFractionDigits: 0,
});

const NUMBER = new Intl.NumberFormat('vi-VN');

const DATE_TIME = new Intl.DateTimeFormat('vi-VN', {
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
  timeZone: 'Asia/Ho_Chi_Minh',
});

const DATE_ONLY = new Intl.DateTimeFormat('vi-VN', {
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
  timeZone: 'Asia/Ho_Chi_Minh',
});

export const EM_DASH = '\u2014';

export function isMissing(value: number | null | undefined): boolean {
  return value === null || value === undefined || Number.isNaN(value);
}

/** Money value. Returns em dash for missing. */
export function money(value: number | null | undefined): string {
  return isMissing(value) ? EM_DASH : VND.format(value as number);
}

/** Money without currency symbol (for tight table cells). */
export function moneyCompact(value: number | null | undefined): string {
  return isMissing(value) ? EM_DASH : NUMBER.format(Math.round(value as number));
}

/** Percent from a decimal ratio (0.12 -> "12.00%"). */
export function percent(
  ratio: number | null | undefined,
  digits = 2,
): string {
  if (isMissing(ratio)) return EM_DASH;
  return `${((ratio as number) * 100).toFixed(digits)}%`;
}

/** Signed delta as percent (0.03 -> "+3.00%"). */
export function signedPercent(
  ratio: number | null | undefined,
  digits = 2,
): string {
  if (isMissing(ratio)) return EM_DASH;
  const v = (ratio as number) * 100;
  const sign = v > 0 ? '+' : '';
  return `${sign}${v.toFixed(digits)}%`;
}

export function quantity(value: number | null | undefined, digits = 0): string {
  if (isMissing(value)) return EM_DASH;
  return (value as number).toLocaleString('vi-VN', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

export function dateTime(iso: string | null | undefined): string {
  if (!iso) return EM_DASH;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return EM_DASH;
  return DATE_TIME.format(d);
}

export function dateOnly(iso: string | null | undefined): string {
  if (!iso) return EM_DASH;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return EM_DASH;
  return DATE_ONLY.format(d);
}

/** Relative freshness label with a numeric age in hours. */
export function freshness(
  iso: string | null | undefined,
  staleAfterHours = 24,
): { label: string; stale: boolean; ageHours: number | null } {
  if (!iso) return { label: 'Không có dữ liệu', stale: true, ageHours: null };
  const d = new Date(iso);
  if (Number.isNaN(d.getTime()))
    return { label: 'Không có dữ liệu', stale: true, ageHours: null };
  const ageHours = (Date.now() - d.getTime()) / 36e5;
  const stale = ageHours > staleAfterHours;
  if (ageHours < 1) {
    const mins = Math.max(1, Math.round(ageHours * 60));
    return { label: `${mins} phút trước`, stale, ageHours };
  }
  if (ageHours < 24) {
    return { label: `${Math.round(ageHours)} giờ trước`, stale, ageHours };
  }
  const days = Math.round(ageHours / 24);
  return { label: `${days} ngày trước`, stale, ageHours };
}
