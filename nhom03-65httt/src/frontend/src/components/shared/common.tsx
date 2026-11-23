import type { ReactNode } from "react"
import { Area, AreaChart, ResponsiveContainer } from "recharts"
import { ArrowDownRight, ArrowUpRight } from "lucide-react"

/**
 * Thành phần dùng chung cho các trang nội dung.
 * Dùng màu theo biến theme (bg-card, text-foreground, ...) để chế độ sáng/tối hoạt động đúng.
 */

export const formatNumber = (value: number) => new Intl.NumberFormat("vi-VN").format(value)

export function PageHeading({ eyebrow, title, description }: { eyebrow?: string; title: string; description: string }) {
  return (
    <div className="mb-6">
      {eyebrow && <div className="text-[10px] font-semibold tracking-[.16em] text-indigo-600">{eyebrow}</div>}
      <h1 className="mt-1.5 text-2xl font-semibold tracking-tight text-foreground">{title}</h1>
      <p className="mt-1 text-sm text-muted-foreground">{description}</p>
    </div>
  )
}

export function Panel({
  title,
  subtitle,
  action,
  children,
  className = "",
}: {
  title: string
  subtitle?: string
  action?: ReactNode
  children: ReactNode
  className?: string
}) {
  return (
    <section className={`rounded-2xl border border-border bg-card p-5 shadow-sm ${className}`}>
      <div className="mb-5 flex items-start justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold tracking-tight text-foreground">{title}</h2>
          {subtitle && <p className="mt-1 text-xs text-muted-foreground">{subtitle}</p>}
        </div>
        {action}
      </div>
      {children}
    </section>
  )
}

export function SelectControl({
  label,
  value,
  onChange,
  options,
}: {
  label: string
  value: string
  onChange: (value: string) => void
  options: string[]
}) {
  return (
    <label className="flex flex-col gap-1.5 text-[10px] font-medium text-muted-foreground">
      {label}
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="min-w-32 rounded-lg border border-border bg-background px-3 py-2 text-xs text-foreground outline-none focus:border-indigo-400"
      >
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  )
}

/** Nhóm nút lọc dạng viên thuốc. */
export function FilterPills({
  options,
  value,
  onChange,
}: {
  options: string[]
  value: string
  onChange: (value: string) => void
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((option) => (
        <button
          key={option}
          onClick={() => onChange(option)}
          className={`rounded-lg px-3 py-2 text-xs font-medium ${
            value === option ? "bg-indigo-600 text-white" : "border border-border text-muted-foreground hover:bg-muted"
          }`}
        >
          {option}
        </button>
      ))}
    </div>
  )
}

export function KpiCard({
  title,
  value,
  unit,
  change,
  positive,
  data,
  color,
}: {
  title: string
  value: string
  unit: string
  change: string
  positive: boolean
  data: number[]
  color: string
}) {
  const points = data.map((v, i) => ({ i, v }))
  return (
    <div className="rounded-2xl border border-border bg-card p-4 shadow-sm sm:p-5">
      <span className="text-xs font-medium text-muted-foreground">{title}</span>
      <div className="mt-3 flex items-end justify-between">
        <div>
          <div className="text-[26px] font-semibold tracking-tight text-foreground">
            {value}
            <span className="ml-1 text-sm font-medium text-muted-foreground">{unit}</span>
          </div>
          <div className={`mt-1 flex items-center gap-1 text-[11px] font-semibold ${positive ? "text-emerald-600" : "text-rose-500"}`}>
            {positive ? <ArrowUpRight size={13} /> : <ArrowDownRight size={13} />} {change}
            <span className="font-normal text-muted-foreground"> so với kỳ trước</span>
          </div>
        </div>
        <div className="h-12 w-[86px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={points}>
              <Area type="monotone" dataKey="v" stroke={color} fill={color} fillOpacity={0.1} strokeWidth={2} isAnimationActive={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}

export const toneClass = {
  positive: "bg-emerald-500/10 text-emerald-600",
  neutral: "bg-amber-500/10 text-amber-600",
  negative: "bg-rose-500/10 text-rose-600",
  info: "bg-sky-500/10 text-sky-600",
  brand: "bg-indigo-500/10 text-indigo-600",
  muted: "bg-muted text-muted-foreground",
} as const

export function sentimentTone(label: string) {
  if (label === "Tích cực") return toneClass.positive
  if (label === "Tiêu cực") return toneClass.negative
  return toneClass.neutral
}

/** Ô nhỏ "Dữ liệu minh họa" hiển thị ở các trang dùng số liệu giả. */
export function MockNotice() {
  return (
    <span className="rounded-full bg-indigo-500/10 px-2 py-1 text-[10px] font-semibold text-indigo-600">Dữ liệu minh họa</span>
  )
}
