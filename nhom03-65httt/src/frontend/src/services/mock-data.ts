/**
 * Dữ liệu MINH HỌA cho giao diện (không phải dữ liệu thật).
 * Khi có API FastAPI, thay các hằng số này bằng lời gọi trong services/api.ts.
 */

export type PlatformGroup = "Trong nước" | "Quốc tế"

export interface MockPlatform {
  name: string
  group: PlatformGroup
  rating: number
  sentiment: number
  bhi: number
  reviews: number
}

export const DATA_AS_OF = "31/10/2026, 09:42"

export const platforms: MockPlatform[] = [
  { name: "ELSA Speak", group: "Trong nước", rating: 4.6, sentiment: 82, bhi: 88, reviews: 4820 },
  { name: "VUIHOC", group: "Trong nước", rating: 4.4, sentiment: 77, bhi: 84, reviews: 3750 },
  { name: "HOCMAI", group: "Trong nước", rating: 4.2, sentiment: 72, bhi: 79, reviews: 4100 },
  { name: "MONKEY", group: "Trong nước", rating: 4.5, sentiment: 80, bhi: 86, reviews: 3260 },
  { name: "DUOLINGO", group: "Quốc tế", rating: 4.7, sentiment: 86, bhi: 92, reviews: 5630 },
  { name: "Busuu", group: "Quốc tế", rating: 4.3, sentiment: 74, bhi: 81, reviews: 2210 },
  { name: "Khan Academy", group: "Quốc tế", rating: 4.8, sentiment: 89, bhi: 95, reviews: 2870 },
  { name: "Memrise", group: "Quốc tế", rating: 4.1, sentiment: 69, bhi: 76, reviews: 1080 },
  { name: "Quizlet", group: "Quốc tế", rating: 4.4, sentiment: 78, bhi: 83, reviews: 918 },
]

export const sentimentTrend = [
  { date: "01/10", positive: 64, neutral: 23, negative: 13 },
  { date: "05/10", positive: 67, neutral: 21, negative: 12 },
  { date: "09/10", positive: 62, neutral: 25, negative: 13 },
  { date: "13/10", positive: 71, neutral: 19, negative: 10 },
  { date: "17/10", positive: 68, neutral: 22, negative: 10 },
  { date: "21/10", positive: 74, neutral: 18, negative: 8 },
  { date: "25/10", positive: 72, neutral: 19, negative: 9 },
  { date: "29/10", positive: 79, neutral: 15, negative: 6 },
]

export const sources = [
  { name: "Google Play", reviews: 10240 },
  { name: "App Store", reviews: 8340 },
  { name: "YouTube", reviews: 5920 },
  { name: "Tin tức", reviews: 4138 },
]

export const kpis = [
  { title: "Tổng lượt đánh giá", value: "28.638", unit: "lượt", change: "12,8%", positive: true, data: [32, 45, 38, 58, 48, 71, 66, 84], color: "#6366f1" },
  { title: "Điểm cảm xúc trung bình", value: "74,2", unit: "/ 100", change: "4,6%", positive: true, data: [48, 51, 49, 63, 58, 67, 70, 74], color: "#10b981" },
  { title: "Đánh giá tiêu cực", value: "12,6", unit: "%", change: "2,1%", positive: true, data: [27, 24, 28, 20, 22, 17, 19, 13], color: "#f59e0b" },
  { title: "Chỉ số sức khỏe thương hiệu (BHI)", value: "84", unit: "/ 100", change: "6,3%", positive: true, data: [58, 62, 60, 69, 71, 74, 78, 84], color: "#8b5cf6" },
]

/** 4 khía cạnh theo đề cương (dim_aspect). */
export const aspects = ["Kỹ thuật", "Học thuật", "CSKH", "Giá"] as const
export type AspectName = (typeof aspects)[number]

/** Điểm cảm xúc tích cực (0-100) theo [Kỹ thuật, Học thuật, CSKH, Giá]. */
export const aspectScores: { name: string; group: PlatformGroup; scores: number[] }[] = [
  { name: "ELSA Speak", group: "Trong nước", scores: [64, 88, 74, 58] },
  { name: "VUIHOC", group: "Trong nước", scores: [70, 84, 80, 72] },
  { name: "HOCMAI", group: "Trong nước", scores: [61, 78, 73, 65] },
  { name: "MONKEY", group: "Trong nước", scores: [77, 86, 81, 71] },
  { name: "DUOLINGO", group: "Quốc tế", scores: [87, 88, 76, 69] },
  { name: "Busuu", group: "Quốc tế", scores: [72, 80, 70, 66] },
  { name: "Khan Academy", group: "Quốc tế", scores: [90, 93, 78, 95] },
  { name: "Memrise", group: "Quốc tế", scores: [63, 75, 60, 52] },
  { name: "Quizlet", group: "Quốc tế", scores: [68, 79, 65, 62] },
]

export const aspectMix: { label: AspectName; positive: number; neutral: number; negative: number }[] = [
  { label: "Kỹ thuật", positive: 38, neutral: 20, negative: 42 },
  { label: "Học thuật", positive: 79, neutral: 14, negative: 7 },
  { label: "CSKH", positive: 58, neutral: 24, negative: 18 },
  { label: "Giá", positive: 49, neutral: 18, negative: 33 },
]

export const recommendations = [
  { priority: "Cao", title: "Ưu tiên khắc phục lỗi đăng nhập trên Android", detail: "Tỷ lệ phản hồi tiêu cực tăng 18% trong 7 ngày qua." },
  { priority: "Trung bình", title: "Rà soát trải nghiệm gia hạn gói học", detail: "1.240 lượt đề cập đến chi phí và gia hạn tự động." },
  { priority: "Thấp", title: "Khai thác nội dung học theo chủ đề", detail: "Chủ đề học ngắn ghi nhận mức hài lòng cao nhất." },
]

export const voiceSamples = [
  { source: "Google Play", platform: "ELSA Speak", mood: "Tích cực", stars: 5, text: "Ứng dụng nhận diện phát âm rất tốt, bài học ngắn gọn và dễ theo dõi. Mình đã tự tin hơn khi giao tiếp." },
  { source: "App Store", platform: "VUIHOC", mood: "Trung lập", stars: 3, text: "Nội dung học rất ổn, tuy nhiên mức phí gia hạn hơi cao so với kỳ vọng của gia đình." },
  { source: "YouTube", platform: "HOCMAI", mood: "Tiêu cực", stars: 2, text: "Sau bản cập nhật mới ứng dụng hay bị đứng khi xem lại bài giảng. Mong đội ngũ sớm khắc phục." },
]

// ---------------------------------------------------------------- Xu hướng & dự báo (theo tháng)
export const months: string[] = (() => {
  const values: string[] = []
  for (let year = 2024; year <= 2026; year++) {
    for (let month = 1; month <= 12; month++) {
      if (year === 2026 && month > 10) break
      values.push(`${year}-${String(month).padStart(2, "0")}`)
    }
  }
  return values
})()

/** Chuỗi Sentiment Index giả lập (-1..1) theo tháng. */
export const sentimentSeries: number[] = months.map((_, index) =>
  Number((0.32 + Math.sin(index * 0.42) * 0.18 + index * 0.009 + Math.cos(index * 0.14) * 0.07).toFixed(2)),
)

export const trendEvents = [
  { month: "2024-09", title: "Cập nhật phiên bản", color: "#6366f1" },
  { month: "2025-06", title: "Mùa thi", color: "#f59e0b" },
  { month: "2026-03", title: "Khuyến mãi", color: "#10b981" },
]

/** MAE giả lập: mô hình nền, LightGBM không có đặc trưng cảm xúc, LightGBM có đặc trưng cảm xúc. */
export const maeCompare = {
  sentiment: { baseline: 0.121, withoutSentiment: 0.101, withSentiment: 0.084, unit: "điểm SI" },
  negative: { baseline: 6.8, withoutSentiment: 5.6, withSentiment: 4.7, unit: "điểm %" },
}

// ---------------------------------------------------------------- Review Explorer
export interface ReviewRow {
  id: string
  text: string
  platform: string
  source: string
  sentiment: "Tích cực" | "Trung lập" | "Tiêu cực"
  aspect: AspectName
  date: string
  misaligned: boolean
}

export const reviewRows: ReviewRow[] = [
  { id: "RV-28401", text: "Ứng dụng dễ dùng, bài học ngắn giúp mình duy trì thói quen mỗi ngày.", platform: "DUOLINGO", source: "Google Play", sentiment: "Tích cực", aspect: "Học thuật", date: "2026-10-30", misaligned: false },
  { id: "RV-28376", text: "Giá gia hạn tăng nhưng thông báo chưa rõ ràng, cần minh bạch hơn.", platform: "ELSA Speak", source: "App Store", sentiment: "Tiêu cực", aspect: "Giá", date: "2026-10-29", misaligned: true },
  { id: "RV-28319", text: "Nội dung tốt, đôi khi ứng dụng bị thoát khi mở bài luyện tập.", platform: "VUIHOC", source: "Google Play", sentiment: "Trung lập", aspect: "Kỹ thuật", date: "2026-10-29", misaligned: false },
  { id: "RV-28298", text: "Giáo viên giải thích dễ hiểu, con tôi tiến bộ rõ sau một tháng.", platform: "HOCMAI", source: "YouTube", sentiment: "Tích cực", aspect: "Học thuật", date: "2026-10-28", misaligned: false },
  { id: "RV-28240", text: "Đã gửi yêu cầu hỗ trợ nhiều lần nhưng chưa nhận được phản hồi.", platform: "Memrise", source: "App Store", sentiment: "Tiêu cực", aspect: "CSKH", date: "2026-10-27", misaligned: true },
  { id: "RV-28177", text: "Giao diện mới nhìn đẹp hơn, vẫn cần thêm chế độ học ngoại tuyến.", platform: "Busuu", source: "Google Play", sentiment: "Trung lập", aspect: "Kỹ thuật", date: "2026-10-26", misaligned: false },
  { id: "RV-28102", text: "Bài học nhiều chủ đề thực tế, phần phát âm nhận diện tốt.", platform: "MONKEY", source: "App Store", sentiment: "Tích cực", aspect: "Học thuật", date: "2026-10-25", misaligned: false },
  { id: "RV-28046", text: "Ứng dụng khá ổn nhưng đồng bộ tiến độ giữa các thiết bị bị lỗi.", platform: "Quizlet", source: "Google Play", sentiment: "Tiêu cực", aspect: "Kỹ thuật", date: "2026-10-24", misaligned: true },
  { id: "RV-27990", text: "Miễn phí mà chất lượng bài giảng rất cao, cảm ơn đội ngũ phát triển.", platform: "Khan Academy", source: "Google Play", sentiment: "Tích cực", aspect: "Giá", date: "2026-10-23", misaligned: false },
  { id: "RV-27944", text: "Nhân viên tư vấn nhiệt tình, hoàn tiền nhanh khi mình đổi gói.", platform: "VUIHOC", source: "App Store", sentiment: "Tích cực", aspect: "CSKH", date: "2026-10-22", misaligned: false },
  { id: "RV-27901", text: "Gói cao cấp quá đắt so với số bài học thực sự mở khóa.", platform: "Memrise", source: "Google Play", sentiment: "Tiêu cực", aspect: "Giá", date: "2026-10-21", misaligned: false },
  { id: "RV-27855", text: "Video bài giảng thỉnh thoảng bị giật khi mạng yếu.", platform: "HOCMAI", source: "YouTube", sentiment: "Trung lập", aspect: "Kỹ thuật", date: "2026-10-20", misaligned: false },
  { id: "RV-27810", text: "Bài tập luyện phát âm sát thực tế, tiến bộ thấy rõ sau hai tuần.", platform: "ELSA Speak", source: "Google Play", sentiment: "Tích cực", aspect: "Học thuật", date: "2026-10-19", misaligned: false },
  { id: "RV-27768", text: "Ứng dụng tự gia hạn mà không báo trước, rất khó chịu.", platform: "DUOLINGO", source: "App Store", sentiment: "Tiêu cực", aspect: "Giá", date: "2026-10-18", misaligned: true },
  { id: "RV-27720", text: "Bộ thẻ ghi nhớ tiện, nhưng đôi lúc đồng bộ bị chậm.", platform: "Quizlet", source: "App Store", sentiment: "Trung lập", aspect: "Kỹ thuật", date: "2026-10-17", misaligned: false },
  { id: "RV-27690", text: "Hỗ trợ trả lời trong ngày, giải quyết đúng vấn đề thanh toán.", platform: "MONKEY", source: "Google Play", sentiment: "Tích cực", aspect: "CSKH", date: "2026-10-16", misaligned: false },
  { id: "RV-27644", text: "Bài học lặp lại nhiều, mình mong có lộ trình nâng cao hơn.", platform: "Busuu", source: "App Store", sentiment: "Trung lập", aspect: "Học thuật", date: "2026-10-15", misaligned: false },
  { id: "RV-27602", text: "Cập nhật mới làm ứng dụng khởi động chậm hẳn trên máy cũ.", platform: "ELSA Speak", source: "Google Play", sentiment: "Tiêu cực", aspect: "Kỹ thuật", date: "2026-10-14", misaligned: true },
]

// ---------------------------------------------------------------- Cảnh báo & khuyến nghị
export interface MockAlert {
  id: string
  severity: "Cao" | "Trung bình" | "Thấp"
  title: string
  detail: string
  platform: string
  action: string
  age: string
}

export const alertItems: MockAlert[] = [
  { id: "alert-1", severity: "Cao", title: "Phản hồi tiêu cực về lỗi đăng nhập tăng nhanh", detail: "Tăng 18% trong 7 ngày · tập trung ở Android 14 và 15.", platform: "ELSA Speak", action: "Ưu tiên kiểm tra lỗi xác thực và phát hành bản vá nóng.", age: "12 phút trước" },
  { id: "alert-2", severity: "Cao", title: "Tỷ lệ phàn nàn về giá gia hạn vượt ngưỡng", detail: "33% đánh giá tiêu cực đề cập phí gia hạn tự động.", platform: "Memrise", action: "Rà soát thông báo gia hạn và hiển thị giá trước khi thanh toán.", age: "48 phút trước" },
  { id: "alert-3", severity: "Trung bình", title: "Lượng đánh giá giảm bất thường", detail: "Số đánh giá mới giảm 22% so với trung bình 4 tuần.", platform: "VUIHOC", action: "Kiểm tra pipeline thu thập và xác nhận không có gián đoạn nguồn.", age: "2 giờ trước" },
  { id: "alert-4", severity: "Thấp", title: "Cơ hội cải thiện chủ đề học ngắn", detail: "Phản hồi tích cực với bài học 5 phút cao hơn 14%.", platform: "MONKEY", action: "Mở rộng nội dung dạng micro-learning ở các nhóm chủ đề phổ biến.", age: "Hôm qua" },
]

// ---------------------------------------------------------------- Trợ lý AI
export const chatSuggestions = [
  "Nền tảng nào bị phàn nàn về giá nhiều nhất?",
  "Tóm tắt xu hướng cảm xúc tháng này",
  "So sánh ELSA Speak và DUOLINGO",
]

export const chatAnswers: Record<string, string> = {
  "Nền tảng nào bị phàn nàn về giá nhiều nhất?":
    "Dựa trên dữ liệu minh họa, Memrise có tỷ lệ phản hồi tiêu cực về chi phí cao nhất (33%), tiếp theo là ELSA Speak (27%). Các bình luận tập trung vào mức phí gia hạn và tính năng bị giới hạn ở gói miễn phí.",
  "Tóm tắt xu hướng cảm xúc tháng này":
    "Tỷ lệ cảm xúc tích cực tăng từ 64% (đầu tháng 10) lên 79% (cuối tháng), tỷ lệ tiêu cực giảm từ 13% xuống 6%. Khía cạnh Học thuật dẫn đầu; khía cạnh Kỹ thuật vẫn cần theo dõi.",
  "So sánh ELSA Speak và DUOLINGO":
    "DUOLINGO có BHI 92 so với 88 của ELSA Speak. ELSA Speak mạnh ở Học thuật (88) nhưng yếu ở Giá (58); DUOLINGO đều hơn ở Kỹ thuật (87) và Học thuật (88).",
}

export const chatFallback =
  "Đây là phản hồi minh họa. Khi chatbot LLM được kết nối với kho dữ liệu, câu trả lời sẽ được tạo từ số liệu thật kèm nguồn trích dẫn."

// ---------------------------------------------------------------- Quản trị
export const adminUsers = [
  { name: "Anh Tuấn", email: "tuan.anh@eduvision.vn", role: "Admin", active: true, last: "Hôm nay, 09:42" },
  { name: "Nguyễn Minh", email: "minh.nguyen@eduvision.vn", role: "Viewer", active: true, last: "Hôm nay, 08:15" },
  { name: "Linh Phạm", email: "linh.pham@eduvision.vn", role: "Viewer", active: true, last: "Hôm qua, 16:30" },
  { name: "Quang Hà", email: "ha.quang@eduvision.vn", role: "Viewer", active: false, last: "12/10/2026" },
]

export const etlSources = [
  { name: "Google Play Reviews", status: "Thành công", time: "31/10/2026 · 09:30", count: "10.240" },
  { name: "App Store", status: "Thành công", time: "31/10/2026 · 09:28", count: "8.340" },
  { name: "YouTube Comments", status: "Đang chạy", time: "31/10/2026 · 09:41", count: "5.920" },
  { name: "Báo chí (RSS)", status: "Cảnh báo", time: "31/10/2026 · 08:05", count: "4.138" },
]

export const activityLog = [
  { text: "Anh Tuấn đã đăng nhập vào hệ thống", time: "Hôm nay, 09:42" },
  { text: "Pipeline Google Play hoàn tất đồng bộ 1.248 bản ghi mới", time: "Hôm nay, 09:30" },
  { text: "Nguyễn Minh đã xuất báo cáo tổng quan", time: "Hôm nay, 08:15" },
  { text: "Pipeline YouTube bắt đầu đồng bộ dữ liệu", time: "Hôm nay, 07:15" },
]
