import { useMemo, useState } from "react"
import { ArrowDownRight } from "lucide-react"
import { Area, Bar, BarChart, CartesianGrid, Cell, ComposedChart, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"

import { MockNotice, PageHeading, Panel, SelectControl } from "@/components/shared/common"
import { maeCompare, months, platforms, sentimentSeries, trendEvents } from "@/services/mock-data"

type Metric = "sentiment" | "negative"

interface TrendPoint {
  month: string
  actual?: number
  forecast?: number
  baseline: number
  lower?: number
  band?: number
}

const GRID = "hsl(var(--border))"
const TICK = { fontSize: 10, fill: "hsl(var(--muted-foreground))" }
const BASELINE: Record<Metric, number> = { sentiment: 0.3, negative: 34 }

function nextMonthKey(last: string, offset: number) {
  const date = new Date(Number(last.slice(0, 4)), Number(last.slice(5)) + offset)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`
}

function TrendTooltip({
  active,
  payload,
  label,
  metric,
}: {
  active?: boolean
  payload?: { dataKey?: string | number; name?: string; value?: number; color?: string }[]
  label?: string
  metric: Metric
}) {
  if (!active || !payload?.length) return null
  const visible = payload.filter((item) => ["actual", "forecast", "baseline"].includes(String(item.dataKey)) && typeof item.value === "number")
  if (!visible.length) return null
  return (
    <div className="rounded-xl border border-border bg-card p-3 text-xs shadow-lg">
      <div className="mb-2 font-semibold text-foreground">{label}</div>
      {visible.map((item) => (
        <div key={String(item.dataKey)} className="mt-1 flex items-center justify-between gap-5">
          <span className="text-muted-foreground">{item.name}</span>
          <b style={{ color: item.color }}>{metric === "sentiment" ? (item.value as number).toFixed(2) : `${item.value}%`}</b>
        </div>
      ))}
    </div>
  )
}

export default function XuHuongPage() {
  const [platform, setPlatform] = useState<string>(platforms[0].name)
  const [metric, setMetric] = useState<Metric>("sentiment")
  const [horizon, setHorizon] = useState(1)
  const [startMonth, setStartMonth] = useState("2024-01")
  const [endMonth, setEndMonth] = useState("2026-10")

  const actuals = useMemo(() => {
    const start = Math.max(0, months.indexOf(startMonth))
    const end = months.indexOf(endMonth)
    const offset = platform === "DUOLINGO" ? 0.06 : platform === "Khan Academy" ? 0.1 : 0
    return months.slice(start, end + 1).map((month) => {
      const index = months.indexOf(month)
      const value = sentimentSeries[index] + offset
      return {
        month,
        actual: metric === "sentiment" ? Math.min(1, Number(value.toFixed(2))) : Math.round((0.42 - value * 0.24 + (index % 4) * 0.008) * 100),
      }
    })
  }, [startMonth, endMonth, platform, metric])

  const chartData = useMemo<TrendPoint[]>(() => {
    const last = actuals.at(-1)
    if (!last) return []
    const baseline = BASELINE[metric]
    const history: TrendPoint[] = actuals.map((point) => ({ month: point.month, actual: point.actual, baseline }))
    // Điểm nối giữa đường thực tế và đường dự báo.
    const junction: TrendPoint = { month: last.month, actual: last.actual, forecast: last.actual, baseline, lower: last.actual, band: 0 }
    const future: TrendPoint[] = Array.from({ length: horizon }, (_, index) => {
      const value =
        metric === "sentiment"
          ? Math.min(0.95, Number((last.actual + 0.025 * (index + 1)).toFixed(2)))
          : Math.max(4, Math.round(last.actual - 1.8 * (index + 1)))
      const spread = metric === "sentiment" ? 0.12 + index * 0.025 : 7 + index * 2
      const lower = Math.max(metric === "sentiment" ? -1 : 0, value - spread)
      const upper = Math.min(metric === "sentiment" ? 1 : 100, value + spread)
      return { month: nextMonthKey(last.month, index), forecast: value, baseline, lower, band: upper - lower }
    })
    return [...history.slice(0, -1), junction, ...future]
  }, [actuals, horizon, metric])

  const startOptions = months.filter((month) => month < endMonth)
  const endOptions = months.filter((month) => month > startMonth)
  const lastActual = actuals.at(-1)?.actual ?? 0
  const lastForecast = chartData.at(-1)?.forecast ?? lastActual
  const visibleEvents = trendEvents.filter((event) => event.month >= startMonth && event.month <= endMonth)
  const compare = maeCompare[metric]
  const maeRows = [
    { name: "Mô hình nền", value: compare.baseline },
    { name: "LightGBM, không có cảm xúc", value: compare.withoutSentiment },
    { name: "LightGBM, có đặc trưng cảm xúc", value: compare.withSentiment },
  ]
  const accuracy = metric === "sentiment" ? 78.6 : 74.2
  const domain: [number, number] = metric === "sentiment" ? [-1, 1] : [0, 100]
  const fmt = (v: number) => (metric === "sentiment" ? v.toFixed(2) : `${v}%`)

  return (
    <>
      <PageHeading eyebrow="TÍN HIỆU THỊ TRƯỜNG" title="Xu hướng & dự báo" description="Theo dõi diễn biến theo tháng, dự báo tháng kế tiếp theo từng nền tảng và so sánh với mô hình nền." />

      <Panel title="Xu hướng và dự báo theo tháng" subtitle="Mô hình M3 (LightGBM) · dự báo ngắn hạn 1–3 tháng" action={<MockNotice />}>
        <div className="mb-5 flex flex-wrap items-end gap-3">
          <SelectControl label="Nền tảng" value={platform} onChange={setPlatform} options={platforms.map((item) => item.name)} />
          <div className="flex flex-col gap-1.5">
            <span className="text-[10px] font-medium text-muted-foreground">Chỉ số</span>
            <div className="flex rounded-lg border border-border p-0.5">
              {([["sentiment", "Sentiment Index"], ["negative", "Tỷ lệ tiêu cực (%)"]] as const).map(([key, label]) => (
                <button key={key} onClick={() => setMetric(key)} className={`rounded-md px-3 py-2 text-xs font-medium ${metric === key ? "bg-indigo-600 text-white" : "text-muted-foreground"}`}>
                  {label}
                </button>
              ))}
            </div>
          </div>
          <SelectControl label="Khoảng dự báo" value={`${horizon} tháng`} onChange={(value) => setHorizon(Number(value.split(" ")[0]))} options={["1 tháng", "2 tháng", "3 tháng"]} />
          <SelectControl label="Từ tháng" value={startMonth} onChange={setStartMonth} options={startOptions} />
          <SelectControl label="Đến tháng" value={endMonth} onChange={setEndMonth} options={endOptions} />
        </div>

        <div className="mb-3 flex flex-wrap gap-x-4 gap-y-2 text-[10px] text-muted-foreground">
          <span><i className="mr-1.5 inline-block h-0.5 w-4 bg-indigo-600 align-middle" />Thực tế</span>
          <span><i className="mr-1.5 inline-block h-0.5 w-4 border-t-2 border-dashed border-violet-500 align-middle" />Dự báo LightGBM</span>
          <span><i className="mr-1.5 inline-block h-0.5 w-4 border-t-2 border-dotted border-slate-400 align-middle" />Mô hình nền</span>
          <span><i className="mr-1.5 inline-block h-3 w-4 rounded-sm bg-violet-400/30 align-middle" />Khoảng tin cậy</span>
        </div>

        <div className="h-[340px] min-w-0">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ left: 8, right: 12, top: 12, bottom: 6 }}>
              <CartesianGrid strokeDasharray="3 5" vertical={false} stroke={GRID} />
              <XAxis dataKey="month" interval="preserveStartEnd" tickLine={false} axisLine={false} tick={TICK} minTickGap={28} />
              <YAxis
                domain={domain}
                tickLine={false}
                axisLine={false}
                tick={TICK}
                tickFormatter={(value) => (metric === "negative" ? `${value}%` : String(value))}
                label={{ value: metric === "sentiment" ? "Sentiment Index" : "Tỷ lệ tiêu cực (%)", angle: -90, position: "insideLeft", style: { fill: "hsl(var(--muted-foreground))", fontSize: 10 } }}
              />
              <Tooltip content={<TrendTooltip metric={metric} />} />
              {/* Dải tin cậy: vùng 'lower' trong suốt cộng dồn với vùng 'band' có màu */}
              <Area dataKey="lower" stackId="ci" stroke="none" fill="transparent" isAnimationActive={false} legendType="none" />
              <Area dataKey="band" stackId="ci" stroke="none" fill="#8b5cf6" fillOpacity={0.22} isAnimationActive={false} legendType="none" />
              {visibleEvents.map((event) => (
                <ReferenceLine
                  key={event.month}
                  x={event.month}
                  stroke={event.color}
                  strokeDasharray="3 4"
                  label={{ value: event.title, position: "insideTopLeft", fill: event.color, fontSize: 9 }}
                />
              ))}
              <Line dataKey="baseline" name="Mô hình nền" stroke="#94a3b8" strokeWidth={1.5} strokeDasharray="2 5" dot={false} activeDot={false} isAnimationActive={false} />
              <Line dataKey="actual" name="Thực tế" stroke="#4f46e5" strokeWidth={2.5} dot={false} connectNulls={false} isAnimationActive={false} />
              <Line dataKey="forecast" name="Dự báo LightGBM" stroke="#8b5cf6" strokeWidth={2.5} strokeDasharray="7 5" dot={{ r: 3, fill: "#8b5cf6" }} connectNulls={false} isAnimationActive={false} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        <div className="mt-2 flex flex-wrap items-center gap-x-5 gap-y-1 border-t border-border pt-3 text-[10px] text-muted-foreground">
          {visibleEvents.map((event) => (
            <span key={event.month} className="flex items-center gap-1.5">
              <i className="size-1.5 rounded-full" style={{ backgroundColor: event.color }} />
              {event.month} · {event.title}
            </span>
          ))}
        </div>
      </Panel>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Panel title="MAE · Sai số tuyệt đối trung bình" subtitle="Đánh giá walk-forward trên các kỳ gần nhất">
          <div className="text-3xl font-semibold tracking-tight text-foreground">{String(compare.withSentiment).replace(".", ",")}</div>
          <div className="mt-2 text-[11px] text-muted-foreground">{compare.unit} · thấp hơn là tốt hơn</div>
          <div className="mt-4 flex items-center gap-1 text-[11px] font-medium text-emerald-600">
            <ArrowDownRight size={14} /> {(compare.baseline - compare.withSentiment).toFixed(metric === "sentiment" ? 3 : 1).replace(".", ",")} so với mô hình nền
          </div>
        </Panel>

        <Panel title="Dự báo đúng chiều" subtitle="Tỷ lệ xu hướng dự báo đúng trong 12 kỳ gần nhất">
          <div className="flex items-end gap-2">
            <div className="text-3xl font-semibold tracking-tight text-foreground">{String(accuracy).replace(".", ",")}%</div>
            <div className="mb-1 text-xs text-muted-foreground">12 tháng</div>
          </div>
          <div className="mt-4 h-2 overflow-hidden rounded-full bg-muted">
            <div className="h-full rounded-full bg-emerald-500" style={{ width: `${accuracy}%` }} />
          </div>
          <div className="mt-2 flex justify-between text-[10px] text-muted-foreground">
            <span>Hiện tại {fmt(lastActual)}</span>
            <span>Dự báo {fmt(lastForecast)}</span>
          </div>
        </Panel>

        <Panel title="Giá trị của đặc trưng cảm xúc" subtitle={`So sánh MAE (${compare.unit}) · thấp hơn là tốt hơn`}>
          <div className="h-[130px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={maeRows} layout="vertical" margin={{ left: 4, right: 28, top: 4, bottom: 0 }}>
                <XAxis type="number" hide domain={[0, "dataMax"]} />
                <YAxis type="category" dataKey="name" width={150} axisLine={false} tickLine={false} tick={{ fontSize: 9, fill: "hsl(var(--muted-foreground))" }} />
                <Tooltip formatter={(value) => [String(value).replace(".", ","), "MAE"]} />
                <Bar dataKey="value" radius={[0, 6, 6, 0]} barSize={16} label={{ position: "right", fontSize: 10, fill: "hsl(var(--muted-foreground))" }} isAnimationActive={false}>
                  {maeRows.map((row, index) => (
                    <Cell key={row.name} fill={index === 2 ? "#6366f1" : index === 1 ? "#a5b4fc" : "#cbd5e1"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>
    </>
  )
}
