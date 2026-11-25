import { useEffect, useMemo, useState } from "react"
import { Legend, PolarAngleAxis, PolarGrid, PolarRadiusAxis, Radar, RadarChart, ResponsiveContainer, Tooltip } from "recharts"
import { AlertTriangle, RefreshCw } from "lucide-react"

import { FilterPills, PageHeading, Panel, formatNumber, toneClass } from "@/components/shared/common"
import { fetchPlatforms, type PlatformItem } from "@/services/api"
import { platforms as fallbackPlatforms } from "@/services/mock-data"

type SortKey = "bhi" | "rating" | "sentiment" | "reviews"

const RADAR_COLORS = ["#6366f1", "#10b981", "#f59e0b"]
const columns: { label: string; key: SortKey }[] = [
  { label: "Điểm BHI", key: "bhi" },
  { label: "Đánh giá", key: "rating" },
  { label: "Cảm xúc tích cực", key: "sentiment" },
  { label: "Lượt đánh giá", key: "reviews" },
]

interface CompareRow {
  name: string
  bhi: number
  rating: number
  sentiment: number
  reviews: number
  group: string
}

function radarValue(p: CompareRow, metric: string): number {
  switch (metric) {
    case "Cảm xúc":
      return p.sentiment
    case "Đánh giá sao":
      return Math.round(p.rating * 20)
    case "BHI":
      return p.bhi
    default:
      return Math.min(100, Math.round(p.reviews / 60))
  }
}

export default function SoSanhPage() {
  const [filter, setFilter] = useState("Tất cả")
  const [sortKey, setSortKey] = useState<SortKey>("bhi")
  const [selected, setSelected] = useState<string[]>(["Duolingo", "ELSA Speak", "HOCMAI"])
  const [platformList, setPlatformList] = useState<CompareRow[]>([])
  const [isLiveApi, setIsLiveApi] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const loadPlatforms = () => {
    setErrorMessage(null)
    fetchPlatforms()
      .then((data) => {
        const mapped: CompareRow[] = data.map((p) => ({
          name: p.name,
          bhi: p.bhiScore,
          rating: p.avgRating,
          sentiment: Math.round(p.sentimentPositiveRatio * 100),
          reviews: p.totalReviews,
          group: p.groupName,
        }))
        setPlatformList(mapped)
        setIsLiveApi(true)
      })
      .catch((err) => {
        setErrorMessage(
          err instanceof Error ? err.message : "Không thể kết nối đến máy chủ API."
        )
        // Fallback sang dữ liệu cục bộ an toàn
        setPlatformList(
          fallbackPlatforms.map((p) => ({
            name: p.name,
            bhi: p.bhi,
            rating: p.rating,
            sentiment: p.sentiment,
            reviews: p.reviews,
            group: p.group,
          }))
        )
        setIsLiveApi(false)
      })
  }

  useEffect(() => {
    loadPlatforms()
  }, [])

  const rows = useMemo(() => {
    return platformList
      .filter((p) => filter === "Tất cả" || p.group === filter)
      .slice()
      .sort((a, b) => b[sortKey] - a[sortKey])
  }, [platformList, filter, sortKey])

  const radarData = useMemo(() => {
    return ["Cảm xúc", "Đánh giá sao", "BHI", "Độ phủ"].map((metric) => {
      const row: Record<string, string | number> = { metric }
      for (const name of selected) {
        const platform = platformList.find((p) => p.name.toLowerCase() === name.toLowerCase())
        if (platform) row[name] = radarValue(platform, metric)
      }
      return row
    })
  }, [platformList, selected])

  const toggle = (name: string) =>
    setSelected((current) =>
      current.includes(name)
        ? current.filter((v) => v !== name)
        : current.length < 3
        ? [...current, name]
        : current
    )

  return (
    <>
      <PageHeading
        eyebrow="PHÂN TÍCH CẠNH TRANH"
        title="So sánh nền tảng"
        description="Đối chiếu hiệu suất thương hiệu và cảm nhận học viên giữa 9 nền tảng từ API máy chủ."
      />

      {errorMessage && (
        <div className="mb-4 flex items-center justify-between rounded-xl border border-destructive/30 bg-destructive/5 p-3.5 text-xs text-destructive">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <span>{errorMessage} (Hiển thị chế độ ngoại tuyến an toàn)</span>
          </div>
          <button
            onClick={loadPlatforms}
            className="inline-flex items-center gap-1 rounded border border-destructive/20 bg-card px-2 py-1 text-[11px] font-medium text-foreground hover:bg-muted cursor-pointer"
          >
            <RefreshCw className="h-3 w-3" /> Thử lại
          </button>
        </div>
      )}

      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <FilterPills
          options={["Tất cả", "Trong nước", "Quốc tế"]}
          value={filter}
          onChange={setFilter}
        />
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          {isLiveApi ? (
            <span className="rounded-full bg-emerald-500/10 px-2 py-1 text-[10px] font-semibold text-emerald-600">
              Dữ liệu API thật
            </span>
          ) : (
            <span className="rounded-full bg-amber-500/10 px-2 py-1 text-[10px] font-semibold text-amber-600">
              Dữ liệu ngoại tuyến
            </span>
          )}
          <span>{rows.length}/9 nền tảng</span>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1.3fr_1fr]">
        <Panel title="Bảng xếp hạng" subtitle="Chọn tiêu đề cột để sắp xếp (giảm dần)">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[650px] text-left text-xs">
              <thead>
                <tr className="text-[10px] uppercase tracking-wider text-muted-foreground">
                  <th className="pb-3 font-medium">Nền tảng</th>
                  {columns.map((column) => (
                    <th
                      key={column.key}
                      className="cursor-pointer select-none pb-3 font-medium hover:text-foreground"
                      onClick={() => setSortKey(column.key)}
                    >
                      {column.label} {sortKey === column.key ? "↓" : ""}
                    </th>
                  ))}
                  <th className="pb-3 font-medium">Nhóm</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((p, i) => (
                  <tr key={p.name} className="border-t border-border">
                    <td className="py-3.5">
                      <div className="flex items-center gap-2.5">
                        <span className="grid size-6 place-items-center rounded-md bg-muted text-[10px] font-semibold text-muted-foreground">
                          {i + 1}
                        </span>
                        <span className="font-semibold text-foreground">{p.name}</span>
                      </div>
                    </td>
                    <td>
                      <span className={`rounded-md px-2 py-1 font-semibold ${toneClass.brand}`}>
                        {p.bhi}
                      </span>
                    </td>
                    <td>★ {p.rating}</td>
                    <td className="font-medium text-emerald-600">{p.sentiment}%</td>
                    <td className="text-muted-foreground">{formatNumber(p.reviews)}</td>
                    <td>
                      <span
                        className={`rounded-full px-2 py-1 text-[9px] ${
                          p.group === "Trong nước" ? toneClass.info : toneClass.brand
                        }`}
                      >
                        {p.group}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel title="Bản đồ năng lực" subtitle="Chọn tối đa 3 nền tảng để đối chiếu">
          <div className="mb-3 flex flex-wrap gap-2">
            {platformList.map((p) => (
              <button
                key={p.name}
                onClick={() => toggle(p.name)}
                className={`rounded-full border px-2.5 py-1 text-[10px] cursor-pointer ${
                  selected.includes(p.name)
                    ? "border-indigo-300 bg-indigo-500/10 text-indigo-600"
                    : "border-border text-muted-foreground hover:bg-muted"
                }`}
              >
                {selected.includes(p.name) && <span className="mr-1">✓</span>}
                {p.name}
              </button>
            ))}
          </div>
          <div className="h-[330px]">
            {selected.length === 0 ? (
              <div className="grid h-full place-items-center text-xs text-muted-foreground">
                Chọn ít nhất một nền tảng để xem biểu đồ.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData} outerRadius="70%">
                  <PolarGrid stroke="hsl(var(--border))" />
                  <PolarAngleAxis
                    dataKey="metric"
                    tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
                  />
                  <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
                  {selected.map((name, index) => (
                    <Radar
                      key={name}
                      name={name}
                      dataKey={name}
                      stroke={RADAR_COLORS[index % RADAR_COLORS.length]}
                      fill={RADAR_COLORS[index % RADAR_COLORS.length]}
                      fillOpacity={0.14}
                    />
                  ))}
                  <Tooltip />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                </RadarChart>
              </ResponsiveContainer>
            )}
          </div>
        </Panel>
      </div>
    </>
  )
}
