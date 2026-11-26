import { useEffect, useState, useCallback } from "react"
import { AlertTriangle, ChevronLeft, ChevronRight, Search, Loader2, RefreshCw } from "lucide-react"

import { PageHeading, Panel, SelectControl, sentimentTone, toneClass } from "@/components/shared/common"
import { fetchPlatforms, fetchReviews, type ReviewItem, type PlatformItem } from "@/services/api"
import { aspects } from "@/services/mock-data"

const PAGE_SIZE = 6
const ALL_PLATFORMS = "Tất cả nền tảng"
const ALL_SOURCES = "Tất cả nguồn"
const ALL_SENTIMENTS = "Tất cả cảm xúc"
const ALL_ASPECTS = "Tất cả khía cạnh"

const SOURCE_OPTIONS = [
  { label: ALL_SOURCES, value: ALL_SOURCES },
  { label: "Google Play", value: "google_play" },
  { label: "App Store", value: "app_store_vn" },
  { label: "YouTube", value: "youtube" },
]

export default function ReviewExplorerPage() {
  const [query, setQuery] = useState("")
  const [platform, setPlatform] = useState(ALL_PLATFORMS)
  const [source, setSource] = useState(ALL_SOURCES)
  const [sentiment, setSentiment] = useState(ALL_SENTIMENTS)
  const [aspect, setAspect] = useState(ALL_ASPECTS)
  const [onlyMisaligned, setOnlyMisaligned] = useState(false)
  const [page, setPage] = useState(1)

  const [availablePlatforms, setAvailablePlatforms] = useState<PlatformItem[]>([])
  const [reviews, setReviews] = useState<ReviewItem[]>([])
  const [total, setTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(1)
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [isLiveApi, setIsLiveApi] = useState(false)

  // Tải danh sách nền tảng từ API
  useEffect(() => {
    let mounted = true
    fetchPlatforms()
      .then((data) => {
        if (mounted) {
          setAvailablePlatforms(data)
        }
      })
      .catch(() => {
        // Nếu lỗi, giữ danh sách rỗng, không làm sập giao diện
      })
    return () => {
      mounted = false
    }
  }, [])

  // Tải dữ liệu đánh giá từ API thật
  const loadReviews = useCallback(async () => {
    setIsLoading(true)
    setErrorMessage(null)
    try {
      const res = await fetchReviews({
        platform: platform !== ALL_PLATFORMS ? platform : undefined,
        source: source !== ALL_SOURCES ? source : undefined,
        sentiment: sentiment !== ALL_SENTIMENTS ? sentiment : undefined,
        aspect: aspect !== ALL_ASPECTS ? aspect : undefined,
        keyword: query.trim() || undefined,
        misaligned_only: onlyMisaligned,
        page,
        page_size: PAGE_SIZE,
      })
      setReviews(res.items)
      setTotal(res.total)
      setTotalPages(res.total_pages || 1)
      setIsLiveApi(true)
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : "Không thể tải dữ liệu đánh giá từ API."
      )
      setIsLiveApi(false)
    } finally {
      setIsLoading(false)
    }
  }, [platform, source, sentiment, aspect, query, onlyMisaligned, page])

  // Reset về trang 1 khi thay đổi điều kiện lọc
  useEffect(() => {
    setPage(1)
  }, [query, platform, source, sentiment, aspect, onlyMisaligned])

  useEffect(() => {
    loadReviews()
  }, [loadReviews])

  const platformOptions = [
    ALL_PLATFORMS,
    ...availablePlatforms.map((p) => p.name),
  ]

  return (
    <>
      <PageHeading
        eyebrow="KHO DỮ LIỆU ĐÁNH GIÁ"
        title="Review Explorer"
        description="Tìm kiếm, lọc và rà soát các đánh giá đã được AI gắn nhãn từ kho dữ liệu chuẩn."
      />

      <Panel
        title="Bộ lọc đánh giá"
        subtitle="Dùng bộ lọc để thu hẹp kết quả"
        action={
          isLiveApi ? (
            <span className="rounded-full bg-emerald-500/10 px-2.5 py-1 text-[10px] font-semibold text-emerald-600">
              API máy chủ (Live)
            </span>
          ) : null
        }
      >
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-5">
          <label className="flex flex-col gap-1.5 text-[10px] font-medium text-muted-foreground">
            Tìm kiếm
            <div className="relative">
              <Search className="absolute left-3 top-2.5 text-muted-foreground" size={14} />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Từ khóa trong nội dung..."
                className="w-full rounded-lg border border-border bg-background py-2 pl-9 pr-3 text-xs text-foreground outline-none focus:border-indigo-400"
              />
            </div>
          </label>
          <SelectControl
            label="Nền tảng"
            value={platform}
            onChange={setPlatform}
            options={platformOptions.length > 1 ? platformOptions : [ALL_PLATFORMS, "ELSA Speak", "Duolingo", "Vuihoc", "HOCMAI", "Monkey Junior", "Quizlet", "Khan Academy", "Busuu", "Memrise"]}
          />
          <SelectControl
            label="Nguồn"
            value={source}
            onChange={setSource}
            options={SOURCE_OPTIONS}
          />
          <SelectControl
            label="Cảm xúc"
            value={sentiment}
            onChange={setSentiment}
            options={[ALL_SENTIMENTS, "Tích cực", "Trung lập", "Tiêu cực"]}
          />
          <SelectControl
            label="Khía cạnh"
            value={aspect}
            onChange={setAspect}
            options={[ALL_ASPECTS, ...aspects]}
          />
        </div>
        <label className="mt-4 flex w-fit cursor-pointer items-center gap-2 text-xs text-muted-foreground">
          <input
            type="checkbox"
            checked={onlyMisaligned}
            onChange={(event) => setOnlyMisaligned(event.target.checked)}
          />
          Chỉ hiện đánh giá lệch pha (số sao và nội dung mâu thuẫn)
        </label>
      </Panel>

      <Panel
        title="Kết quả đánh giá"
        subtitle={
          isLoading
            ? "Đang tải dữ liệu từ máy chủ API..."
            : `${total} đánh giá phù hợp với bộ lọc (trang ${page}/${totalPages})`
        }
        className="mt-4"
      >
        {/* Trường hợp lỗi API (HA2.3: Báo lỗi rõ, không trắng trang) */}
        {errorMessage ? (
          <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-6 text-center">
            <div className="mx-auto mb-2.5 flex h-10 w-10 items-center justify-center rounded-full bg-destructive/10 text-destructive">
              <AlertTriangle className="h-5 w-5" />
            </div>
            <h3 className="text-sm font-semibold text-foreground">Không thể kết nối API máy chủ</h3>
            <p className="mt-1 text-xs text-muted-foreground max-w-md mx-auto">{errorMessage}</p>
            <button
              onClick={loadReviews}
              className="mt-4 inline-flex items-center gap-1.5 rounded-lg border border-border bg-card px-3.5 py-1.5 text-xs font-medium text-foreground hover:bg-muted cursor-pointer transition-colors"
            >
              <RefreshCw className="h-3.5 w-3.5" /> Thử lại
            </button>
          </div>
        ) : isLoading ? (
          <div className="py-16 text-center text-xs text-muted-foreground flex flex-col items-center justify-center gap-2">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
            <span>Đang truy vấn dữ liệu từ API...</span>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[820px] text-left text-xs">
              <thead>
                <tr className="text-[10px] uppercase tracking-wider text-muted-foreground">
                  <th className="pb-3 font-medium">Đánh giá</th>
                  <th className="pb-3 font-medium">Nền tảng / Nguồn</th>
                  <th className="pb-3 font-medium">Số sao</th>
                  <th className="pb-3 font-medium">Cảm xúc</th>
                  <th className="pb-3 font-medium">Khía cạnh</th>
                  <th className="pb-3 font-medium">Ngày đăng</th>
                  <th className="pb-3 font-medium">Cờ lệch pha</th>
                </tr>
              </thead>
              <tbody>
                {reviews.map((row) => (
                  <tr key={row.review_key || row.review_id} className="border-t border-border align-top">
                    <td className="max-w-[360px] py-4 pr-4">
                      <div className="mb-1 text-[10px] font-semibold text-indigo-600">
                        {row.review_id}
                      </div>
                      <p className="leading-relaxed text-foreground/80">{row.text || "—"}</p>
                    </td>
                    <td className="py-4">
                      <div className="font-semibold text-foreground">{row.platform}</div>
                      <div className="mt-1 text-[10px] text-muted-foreground">{row.source}</div>
                    </td>
                    <td className="py-4">
                      <span className="font-semibold text-foreground">
                        {row.rating ? `${row.rating} ★` : "—"}
                      </span>
                    </td>
                    <td className="py-4">
                      {row.sentiment ? (
                        <span
                          className={`whitespace-nowrap rounded-full px-2 py-1 text-[10px] font-medium ${sentimentTone(
                            row.sentiment
                          )}`}
                        >
                          {row.sentiment}
                        </span>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </td>
                    <td className="py-4">
                      <span className="whitespace-nowrap rounded-md border border-border px-2 py-1 text-[10px] text-foreground/80">
                        {row.aspect || (row.aspects && row.aspects[0]) || "Chung"}
                      </span>
                    </td>
                    <td className="whitespace-nowrap py-4 text-muted-foreground">
                      {row.created_at || "—"}
                    </td>
                    <td className="py-4">
                      {row.misaligned ? (
                        <span
                          className={`inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2 py-1 text-[10px] font-medium ${toneClass.neutral}`}
                        >
                          <AlertTriangle size={11} />
                          Lệch pha
                        </span>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {reviews.length === 0 && (
              <div className="py-12 text-center text-xs text-muted-foreground">
                Không tìm thấy đánh giá nào phù hợp với bộ lọc hiện tại.
              </div>
            )}
          </div>
        )}

        {/* Phân trang chuẩn */}
        {!errorMessage && total > 0 && (
          <div className="mt-4 flex items-center justify-between border-t border-border pt-4 text-xs text-muted-foreground">
            <span>
              Trang {page}/{totalPages} (Tổng cộng {total} đánh giá)
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1 || isLoading}
                aria-label="Trang trước"
                className="grid size-8 place-items-center rounded-lg border border-border hover:bg-muted disabled:opacity-40 cursor-pointer"
              >
                <ChevronLeft size={15} />
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages || isLoading}
                aria-label="Trang sau"
                className="grid size-8 place-items-center rounded-lg border border-border hover:bg-muted disabled:opacity-40 cursor-pointer"
              >
                <ChevronRight size={15} />
              </button>
            </div>
          </div>
        )}
      </Panel>
    </>
  )
}
