/**
 * EduVision BI - Dịch vụ API giả lập (Mock API Service)
 *
 * GHI CHÚ: Các hàm hiện tại trả về dữ liệu mẫu có độ trễ 300-600ms mô phỏng mạng.
 * TODO: Sẽ được thay thế bằng các lệnh gọi REST API đến backend FastAPI sau khi hoàn thiện.
 */

// Tiền tố API nếu có (lấy từ biến môi trường)
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1"

// Hàm tạo độ trễ ngẫu nhiên từ 300ms đến 600ms
const simulateLatency = <T>(data: T, minMs = 300, maxMs = 600): Promise<T> => {
  const latency = Math.floor(Math.random() * (maxMs - minMs + 1)) + minMs
  return new Promise((resolve) => setTimeout(() => resolve(data), latency))
}

// ============================================================================
// Các kiểu dữ liệu TypeScript (DTO)
// ============================================================================

export interface PlatformItem {
  id: string
  name: string
  code: string
  category: "domestic" | "international"
  totalReviews: number
  avgRating: number
  bhiScore: number // Brand Health Index (0 - 100)
  sentimentPositiveRatio: number
}

export interface AspectScore {
  aspectId: string
  aspectName: string
  description: string
  positiveRatio: number
  neutralRatio: number
  negativeRatio: number
  score: number
}

export interface BhiOverview {
  overallBhi: number
  trendDelta: number // Tăng giảm so với tháng trước
  totalReviewsProcessed: number
  lastUpdated: string
  topPlatform: string
}

export interface AlertItem {
  id: string
  platformCode: string
  platformName: string
  aspect: string
  department: "Đào tạo" | "Sản phẩm" | "Marketing" | "CSKH"
  severity: "high" | "medium" | "low"
  message: string
  suggestedAction: string
  createdAt: string
  resolved: boolean
}

export interface TrendForecastItem {
  period: string
  platformCode: string
  actualSentimentScore?: number
  forecastSentimentScore: number
  confidenceLower: number
  confidenceUpper: number
}

// ============================================================================
// Các hàm gọi API (Mock)
// ============================================================================

/**
 * Lấy danh sách 9 nền tảng E-learning
 * TODO: thay bằng gọi FastAPI sau: GET /platforms
 */
export async function fetchPlatforms(): Promise<PlatformItem[]> {
  const mockPlatforms: PlatformItem[] = [
    { id: "1", name: "ELSA Speak", code: "elsa", category: "domestic", totalReviews: 4200, avgRating: 4.6, bhiScore: 84.5, sentimentPositiveRatio: 0.82 },
    { id: "2", name: "Vuihoc", code: "vuihoc", category: "domestic", totalReviews: 2800, avgRating: 4.4, bhiScore: 78.2, sentimentPositiveRatio: 0.76 },
    { id: "3", name: "Monkey Junior", code: "monkey", category: "domestic", totalReviews: 1950, avgRating: 4.1, bhiScore: 71.0, sentimentPositiveRatio: 0.69 },
    { id: "4", name: "HOCMAI", code: "hocmai", category: "domestic", totalReviews: 1600, avgRating: 4.0, bhiScore: 68.4, sentimentPositiveRatio: 0.65 },
    { id: "5", name: "Duolingo", code: "duolingo", category: "international", totalReviews: 3600, avgRating: 4.7, bhiScore: 89.1, sentimentPositiveRatio: 0.88 },
    { id: "6", name: "Busuu", code: "busuu", category: "international", totalReviews: 850, avgRating: 4.3, bhiScore: 75.8, sentimentPositiveRatio: 0.74 },
    { id: "7", name: "Khan Academy", code: "khan", category: "international", totalReviews: 720, avgRating: 4.5, bhiScore: 82.0, sentimentPositiveRatio: 0.81 },
    { id: "8", name: "Memrise", code: "memrise", category: "international", totalReviews: 640, avgRating: 4.2, bhiScore: 73.5, sentimentPositiveRatio: 0.70 },
    { id: "9", name: "Quizlet", code: "quizlet", category: "international", totalReviews: 1250, avgRating: 4.6, bhiScore: 86.3, sentimentPositiveRatio: 0.85 },
  ]
  return simulateLatency(mockPlatforms)
}

/**
 * Lấy thông tin tổng quan chỉ số BHI
 * TODO: thay bằng gọi FastAPI sau: GET /metrics/bhi-overview
 */
export async function fetchBhiOverview(): Promise<BhiOverview> {
  const mockBhi: BhiOverview = {
    overallBhi: 78.7,
    trendDelta: +2.4,
    totalReviewsProcessed: 17610,
    lastUpdated: new Date().toISOString(),
    topPlatform: "Duolingo",
  }
  return simulateLatency(mockBhi)
}

/**
 * Lấy danh sách điểm số theo 4 khía cạnh trải nghiệm (ABSA)
 * TODO: thay bằng gọi FastAPI sau: GET /aspects/summary
 */
export async function fetchAspectScores(): Promise<AspectScore[]> {
  const mockAspects: AspectScore[] = [
    { aspectId: "content", aspectName: "Nội dung khóa học", description: "Chất lượng bài giảng, sự đa dạng của lộ trình học", positiveRatio: 0.78, neutralRatio: 0.12, negativeRatio: 0.10, score: 8.2 },
    { aspectId: "uiux", aspectName: "Giao diện & Trải nghiệm (UI/UX)", description: "Độ mượt mà, tính dễ dùng và thẩm mỹ ứng dụng", positiveRatio: 0.81, neutralRatio: 0.11, negativeRatio: 0.08, score: 8.5 },
    { aspectId: "pricing", aspectName: "Học phí & Giá trị", description: "Mức giá so với chất lượng nhận được, chính sách hoàn tiền", positiveRatio: 0.62, neutralRatio: 0.18, negativeRatio: 0.20, score: 6.8 },
    { aspectId: "support", aspectName: "Hỗ trợ & Ổn định kỹ thuật", description: "Tốc độ xử lý lỗi, CSKH, độ ổn định đường truyền server", positiveRatio: 0.68, neutralRatio: 0.14, negativeRatio: 0.18, score: 7.1 },
  ]
  return simulateLatency(mockAspects)
}

/**
 * Lấy danh sách cảnh báo tự động sinh từ mô hình AI
 * TODO: thay bằng gọi FastAPI sau: GET /alerts
 */
export async function fetchAlerts(): Promise<AlertItem[]> {
  const mockAlerts: AlertItem[] = [
    {
      id: "alt-01",
      platformCode: "vuihoc",
      platformName: "Vuihoc",
      aspect: "Học phí & Giá trị",
      department: "Marketing",
      severity: "high",
      message: "Tỷ lệ phàn nàn về chính sách tự động gia hạn tăng 18% trong 14 ngày qua.",
      suggestedAction: "Rà soát lại thông báo trước khi gia hạn thuê bao và hướng dẫn hủy gói rõ ràng trên app.",
      createdAt: "2026-11-20T08:30:00Z",
      resolved: false,
    },
    {
      id: "alt-02",
      platformCode: "hocmai",
      platformName: "HOCMAI",
      aspect: "Hỗ trợ & Ổn định kỹ thuật",
      department: "Sản phẩm",
      severity: "medium",
      message: "Lỗi tải video bài giảng trên phiên bản Android mới nhất ghi nhận 25 đánh giá 1 sao.",
      suggestedAction: "Kiểm tra CDN và cập nhật bản vá hotfix cho bộ giải mã video trên Android.",
      createdAt: "2026-11-19T14:15:00Z",
      resolved: false,
    },
    {
      id: "alt-03",
      platformCode: "elsa",
      platformName: "ELSA Speak",
      aspect: "Nội dung khóa học",
      department: "Đào tạo",
      severity: "low",
      message: "Học viên yêu cầu bổ sung thêm bài học ngữ cảnh chuyên ngành y khoa và tài chính.",
      suggestedAction: "Chuyển danh sách chủ đề đề xuất cho ban biên soạn nội dung kỳ tới.",
      createdAt: "2026-11-18T10:00:00Z",
      resolved: true,
    },
  ]
  return simulateLatency(mockAlerts)
}

/**
 * Kích hoạt cập nhật dữ liệu ETL (chỉ dành cho Quản trị viên)
 * TODO: thay bằng gọi FastAPI sau: POST /admin/trigger-etl
 */
export async function triggerDataUpdate(): Promise<{ success: boolean; message: string; runId: string }> {
  return simulateLatency({
    success: true,
    message: "Đã kích hoạt tiến trình thu thập và ETL nền thành công.",
    runId: `run-${Date.now()}`,
  }, 500, 800)
}
