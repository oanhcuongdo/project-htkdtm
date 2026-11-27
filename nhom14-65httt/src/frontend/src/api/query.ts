/** Bỏ undefined, giữ số 0 và chuỗi rỗng; mã hóa chữ Việt/ký tự đặc biệt. */
export function queryString(
  params: Record<string, string | number | undefined>,
): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) query.set(key, String(value));
  }
  const encoded = query.toString();
  return encoded ? `?${encoded}` : "";
}

export interface ReadOptions {
  signal?: AbortSignal;
}
