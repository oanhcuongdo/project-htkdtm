/**
 * EduVision BI - Dịch vụ API kết nối Backend FastAPI (EduVision BI, Nhóm 03).
 *
 * HA2: Kết nối API thật (FastAPI) cho tìm kiếm, lọc và phân trang đánh giá.
 * URL cấu hình duy nhất từ biến môi trường Vite VITE_API_BASE_URL.
 */

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1"

/**
 * Lấy Bearer token từ localStorage nếu người dùng đã đăng nhập.
 */
function getAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  }
  try {
    const token = localStorage.getItem("eduvision.token")
    if (token) {
      headers["Authorization"] = `Bearer ${token}`
    }
  } catch {
    // Không truy cập được localStorage
  }
  return headers
}

/**
 * Hàm gọi API tổng quát, xử lý lỗi mạng và trả thông báo tiếng Việt thân thiện (HA2.3).
 * Tự động chuyển hướng về trang /login và xóa session khi gặp lỗi 401 Unauthorized (B7).
 */
async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`
  const headers = {
    ...getAuthHeaders(),
    ...(options.headers as Record<string, string> | undefined),
  }

  let response: Response
  try {
    response = await fetch(url, { ...options, headers })
  } catch {
    throw new Error(
      `Không thể kết nối đến máy chủ API (${API_BASE_URL}). Vui lòng kiểm tra lại dịch vụ backend.`
    )
  }

  // B7: Xử lý 401 Unauthorized
  if (response.status === 401) {
    try {
      localStorage.removeItem("eduvision.token")
      localStorage.removeItem("eduvision.session")
    } catch {
      // Bỏ qua lỗi truy cập storage
    }
    if (typeof window !== "undefined" && window.location.pathname !== "/login") {
      window.location.href = "/login"
    }
    throw new Error("Phiên đăng nhập đã hết hạn hoặc không hợp lệ. Vui lòng đăng nhập lại.")
  }

  if (!response.ok) {
    let errorDetail = `Lỗi yêu cầu máy chủ: mã trạng thái ${response.status}`
    try {
      const data = await response.json()
      if (data.detail) {
        errorDetail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail)
      }
    } catch {
      // Giữ thông báo mã trạng thái mặc định
    }
    throw new Error(errorDetail)
  }

  return response.json() as Promise<T>
}

// ============================================================================
// Các kiểu dữ liệu DTO
// ============================================================================

export interface PlatformItem {
  id: string
  name: string
  code: string
  category: "domestic" | "international"
  groupName: string // "Trong nước" hoặc "Quốc tế"
}

export interface ReviewItem {
  review_key: number
  review_id: string
  platform: string
  source: string
  rating: number | null
  created_at: string | null
  text: string | null
  sentiment: string | null // "Tích cực", "Trung lập", "Tiêu cực", hoặc null nếu chưa có nhãn
  sentiment_score: number | null
  aspect: string | null
  aspects: string[]
  misaligned: boolean
}

export interface ReviewsResponse {
  total: number
  page: number
  page_size: number
  total_pages: number
  items: ReviewItem[]
}

export interface ReviewFilterParams {
  platform?: string
  start_date?: string
  end_date?: string
  sentiment?: string
  aspect?: string
  keyword?: string
  rating?: number
  misaligned_only?: boolean
  source?: string
  page?: number
  page_size?: number
}

// ============================================================================
// Các hàm API thật (HA2)
// ============================================================================

/**
 * Lấy danh sách 9 nền tảng E-learning từ GET /api/v1/platforms (từ tệp cấu hình chuẩn platforms.yml)
 */
export async function fetchPlatforms(): Promise<PlatformItem[]> {
  interface RawPlatform {
    id: string
    group: string
    play_id?: string | null
    ios_id?: string | null
  }

  const raw = await fetchApi<RawPlatform[]>("/platforms")
  return raw.map((item, idx) => {
    const isDomestic = item.group === "trong_nuoc"
    return {
      id: String(idx + 1),
      name: item.id,
      code: item.id,
      category: isDomestic ? "domestic" : "international",
      groupName: isDomestic ? "Trong nước" : "Quốc tế",
    }
  })
}

/**
 * Tìm kiếm và lọc đánh giá từ GET /api/v1/reviews (HA2.4, HA2.5, HA2.6)
 */
export async function fetchReviews(params: ReviewFilterParams = {}): Promise<ReviewsResponse> {
  const query = new URLSearchParams()

  if (params.platform && params.platform !== "Tất cả nền tảng") {
    query.set("platform", params.platform)
  }
  if (params.source && params.source !== "Tất cả nguồn") {
    query.set("source", params.source)
  }
  if (params.sentiment && params.sentiment !== "Tất cả cảm xúc") {
    query.set("sentiment", params.sentiment)
  }
  if (params.aspect && params.aspect !== "Tất cả khía cạnh") {
    query.set("aspect", params.aspect)
  }
  if (params.keyword?.trim()) {
    query.set("keyword", params.keyword.trim())
  }
  if (params.rating) {
    query.set("rating", String(params.rating))
  }
  if (params.misaligned_only) {
    query.set("misaligned_only", "true")
  }
  if (params.start_date) {
    query.set("start_date", params.start_date)
  }
  if (params.end_date) {
    query.set("end_date", params.end_date)
  }
  if (params.page) {
    query.set("page", String(params.page))
  }
  if (params.page_size) {
    query.set("page_size", String(params.page_size))
  }

  const queryString = query.toString()
  const endpoint = `/reviews${queryString ? `?${queryString}` : ""}`
  return fetchApi<ReviewsResponse>(endpoint)
}

/**
 * Lấy chi tiết một đánh giá theo khóa review_key từ GET /api/v1/reviews/{review_key}
 */
export async function fetchReviewByKey(reviewKey: number): Promise<ReviewItem> {
  return fetchApi<ReviewItem>(`/reviews/${reviewKey}`)
}
