import { useMemo, useState } from "react"
import { Legend, PolarAngleAxis, PolarGrid, PolarRadiusAxis, Radar, RadarChart, ResponsiveContainer, Tooltip } from "recharts"

import { FilterPills, MockNotice, PageHeading, Panel, formatNumber, toneClass } from "@/components/shared/common"
import { platforms, type MockPlatform } from "@/services/mock-data"

type SortKey = "bhi" | "rating" | "sentiment" | "reviews"

const RADAR_COLORS = ["#6366f1", "#10b981", "#f59e0b"]
const columns: { label: string; key: SortKey }[] = [
  { label: "Điểm BHI", key: "bhi" },
  { label: "Đánh giá", key: "rating" },
  { label: "Cảm xúc tích cực", key: "sentiment" },
  { label: "Lượt đánh giá", key: "reviews" },
]

/** Quy mọi chỉ số về thang 0-100 để vẽ radar. */
function radarValue(p: MockPlatform, metric: string): number {
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
  const [selected, setSelected] = useState<string[]>(["DUOLINGO", "ELSA Speak", "HOCMAI"])

  const rows = useMemo(
    () =>
      platforms
        .filter((p) => filter === "Tất cả" || p.group === filter)
        .slice()
        .sort((a, b) => b[sortKey] - a[sortKey]),
    [filter, sortKey],
  )

  const radarData = useMemo(
    () =>
      ["Cảm xúc", "Đánh giá sao", "BHI", "Độ phủ"].map((metric) => {
        const row: Record<string, string | number> = { metric }
        for (const name of selected) {
          const platform = platforms.find((p) => p.name === name)
          if (platform) row[name] = radarValue(platform, metric)
        }
        return row
      }),
    [selected],
  )

  const toggle = (name: string) =>
    setSelected((current) =>
      current.includes(name) ? current.filter((v) => v !== name) : current.length < 3 ? [...current, name] : current,
    )

  return (
    <>
      <PageHeading eyebrow="PHÂN TÍCH CẠNH TRANH" title="So sánh nền tảng" description="Đối chiếu hiệu suất thương hiệu và cảm nhận học viên giữa 9 nền tảng." />

      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <FilterPills options={["Tất cả", "Trong nước", "Quốc tế"]} value={filter} onChange={setFilter} />
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <MockNotice />
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
                    <th key={column.key} className="cursor-pointer select-none pb-3 font-medium hover:text-foreground" onClick={() => setSortKey(column.key)}>
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
                        <span className="grid size-6 place-items-center rounded-md bg-muted text-[10px] font-semibold text-muted-foreground">{i + 1}</span>
                        <span className="font-semibold text-foreground">{p.name}</span>
                      </div>
                    </td>
                    <td><span className={`rounded-md px-2 py-1 font-semibold ${toneClass.brand}`}>{p.bhi}</span></td>
                    <td>★ {p.rating}</td>
                    <td className="font-medium text-emerald-600">{p.sentiment}%</td>
                    <td className="text-muted-foreground">{formatNumber(p.reviews)}</td>
                    <td>
                      <span className={`rounded-full px-2 py-1 text-[9px] ${p.group === "Trong nước" ? toneClass.info : toneClass.brand}`}>{p.group}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel title="Bản đồ năng lực" subtitle="Chọn tối đa 3 nền tảng để đối chiếu">
          <div className="mb-3 flex flex-wrap gap-2">
            {platforms.map((p) => (
              <button
                key={p.name}
                onClick={() => toggle(p.name)}
                className={`rounded-full border px-2.5 py-1 text-[10px] ${
                  selected.includes(p.name) ? "border-indigo-300 bg-indigo-500/10 text-indigo-600" : "border-border text-muted-foreground hover:bg-muted"
                }`}
              >
                {selected.includes(p.name) && <span className="mr-1">✓</span>}
                {p.name}
              </button>
            ))}
          </div>
          <div className="h-[330px]">
            {selected.length === 0 ? (
              <div className="grid h-full place-items-center text-xs text-muted-foreground">Chọn ít nhất một nền tảng để xem biểu đồ.</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData} outerRadius="70%">
                  <PolarGrid stroke="hsl(var(--border))" />
                  <PolarAngleAxis dataKey="metric" tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} />
                  <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
                  {selected.map((name, index) => (
                    <Radar key={name} name={name} dataKey={name} stroke={RADAR_COLORS[index]} fill={RADAR_COLORS[index]} fillOpacity={0.14} />
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
