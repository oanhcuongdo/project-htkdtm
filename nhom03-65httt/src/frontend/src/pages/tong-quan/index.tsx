import { Link } from "react-router-dom"
import { Activity, AlertTriangle, Sparkles } from "lucide-react"
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"

import { KpiCard, PageHeading, Panel, formatNumber, toneClass } from "@/components/shared/common"
import { DATA_AS_OF, kpis, platforms, recommendations, sentimentTrend, sources } from "@/services/mock-data"

const GRID = "hsl(var(--border))"
const TICK = { fontSize: 10, fill: "hsl(var(--muted-foreground))" }
const SOURCE_COLORS = ["#6366f1", "#818cf8", "#a5b4fc", "#c7d2fe"]

export default function TongQuanPage() {
  const topPlatforms = [...platforms].sort((a, b) => b.bhi - a.bhi).slice(0, 4)
  const priorityTone = [toneClass.negative, toneClass.neutral, toneClass.muted]
  const totalReviews = sources.reduce((sum, item) => sum + item.reviews, 0)

  return (
    <>
      <div className="mb-4 flex items-center gap-2 rounded-lg border border-amber-500/20 bg-amber-500/10 px-4 py-2.5 text-xs text-amber-700 dark:text-amber-400">
        <AlertTriangle className="size-4 shrink-0" />
        <span>Dữ liệu minh họa, chưa nối API KPI</span>
      </div>

      <div className="mb-6 flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
        <PageHeading
          eyebrow="TỔNG QUAN"
          title="Tổng quan trải nghiệm học viên"
          description="Theo dõi sức khỏe thương hiệu trên 9 nền tảng học trực tuyến."
        />
        <div className="mb-6 flex items-center gap-2 text-xs text-muted-foreground sm:mb-6">
          <span className="rounded-full bg-amber-500/10 px-2 py-1 text-[10px] font-semibold text-amber-600">
            Dữ liệu minh họa
          </span>
          <span>Cập nhật {DATA_AS_OF}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {kpis.map((item) => (
          <KpiCard key={item.title} {...item} />
        ))}
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-[1.7fr_1fr]">
        <Panel title="Diễn biến cảm xúc theo thời gian" subtitle="Tỷ trọng cảm xúc qua các đánh giá · tháng 10/2026">
          <div className="mb-3 flex gap-4 text-[11px] text-muted-foreground">
            <span><i className="mr-1.5 inline-block size-2 rounded-full bg-indigo-500" />Tích cực</span>
            <span><i className="mr-1.5 inline-block size-2 rounded-full bg-amber-400" />Trung lập</span>
            <span><i className="mr-1.5 inline-block size-2 rounded-full bg-rose-400" />Tiêu cực</span>
          </div>
          <div className="h-[230px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={sentimentTrend} margin={{ left: -20, right: 4, top: 8, bottom: 0 }}>
                <defs>
                  <linearGradient id="posGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#6366f1" stopOpacity={0.18} />
                    <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 5" vertical={false} stroke={GRID} />
                <XAxis dataKey="date" tickLine={false} axisLine={false} tick={TICK} />
                <YAxis tickLine={false} axisLine={false} tick={TICK} tickFormatter={(v) => `${v}%`} />
                <Tooltip />
                <Area type="monotone" dataKey="positive" name="Tích cực" stroke="#6366f1" strokeWidth={2.5} fill="url(#posGradient)" />
                <Line type="monotone" dataKey="neutral" name="Trung lập" stroke="#f59e0b" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="negative" name="Tiêu cực" stroke="#fb7185" strokeWidth={2} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title="Lượt đánh giá theo nguồn" subtitle="Phân bổ dữ liệu thu thập được">
          <div className="h-[195px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sources} layout="vertical" margin={{ left: 0, right: 18, top: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 5" horizontal={false} stroke={GRID} />
                <XAxis type="number" hide />
                <YAxis type="category" dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} width={83} />
                <Tooltip formatter={(v) => formatNumber(Number(v))} />
                <Bar dataKey="reviews" name="Lượt đánh giá" radius={[0, 6, 6, 0]} barSize={16}>
                  {sources.map((item, index) => (
                    <Cell key={item.name} fill={SOURCE_COLORS[index % SOURCE_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-3 flex items-center justify-between border-t border-border pt-3 text-xs">
            <span className="text-muted-foreground">Tổng dữ liệu thu thập</span>
            <b className="text-foreground">{formatNumber(totalReviews)}</b>
          </div>
        </Panel>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-[1.45fr_1fr]">
        <Panel
          title="Bảng xếp hạng nổi bật"
          subtitle="Chỉ số sức khỏe thương hiệu (BHI) theo nền tảng"
          action={<Link to="/so-sanh" className="text-xs font-semibold text-indigo-600">Xem tất cả →</Link>}
        >
          <div className="overflow-x-auto">
            <table className="w-full min-w-[500px] text-left text-xs">
              <thead className="text-[10px] uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th className="pb-3 font-medium">Nền tảng</th>
                  <th className="pb-3 font-medium">Đánh giá</th>
                  <th className="pb-3 font-medium">Cảm xúc tích cực</th>
                  <th className="pb-3 text-right font-medium">BHI</th>
                </tr>
              </thead>
              <tbody>
                {topPlatforms.map((p, i) => (
                  <tr key={p.name} className="border-t border-border">
                    <td className="py-3 font-semibold text-foreground">
                      <span className="mr-2 text-muted-foreground">0{i + 1}</span>
                      {p.name}
                    </td>
                    <td className="py-3">★ {p.rating}</td>
                    <td className="py-3">
                      <span className="text-emerald-600">{p.sentiment}%</span>
                    </td>
                    <td className="py-3 text-right">
                      <span className={`rounded-md px-2 py-1 font-semibold ${toneClass.brand}`}>
                        {p.bhi}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel
          title="Khuyến nghị hành động"
          subtitle="Đề xuất ưu tiên dựa trên dữ liệu mới nhất"
          action={<span className={`rounded-full px-2 py-1 text-[10px] font-semibold ${toneClass.negative}`}>{recommendations.length} đề xuất</span>}
        >
          <div className="flex flex-col gap-3">
            {recommendations.map((item, i) => (
              <div key={item.title} className="flex gap-3 rounded-xl border border-border p-3">
                <div className={`grid size-8 shrink-0 place-items-center rounded-lg ${priorityTone[i] ?? toneClass.muted}`}>
                  {i === 0 ? <AlertTriangle size={15} /> : i === 1 ? <Activity size={15} /> : <Sparkles size={15} />}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-xs font-semibold leading-5 text-foreground">{item.title}</p>
                    <span className={`shrink-0 rounded-full px-2 py-0.5 text-[9px] font-semibold ${priorityTone[i] ?? toneClass.muted}`}>{item.priority}</span>
                  </div>
                  <p className="mt-1 text-[10px] leading-relaxed text-muted-foreground">{item.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </>
  )
}
