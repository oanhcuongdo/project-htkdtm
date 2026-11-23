import { useMemo, useState } from "react"
import { Activity, CheckCircle2 } from "lucide-react"

import { FilterPills, MockNotice, PageHeading, toneClass } from "@/components/shared/common"
import { alertItems, type MockAlert } from "@/services/mock-data"

const severityTone: Record<MockAlert["severity"], string> = {
  Cao: toneClass.negative,
  "Trung bình": toneClass.neutral,
  Thấp: toneClass.info,
}

export default function CanhBaoPage() {
  const [filter, setFilter] = useState("Tất cả")
  const [done, setDone] = useState<string[]>([])

  const alerts = useMemo(() => alertItems.filter((alert) => filter === "Tất cả" || alert.severity === filter), [filter])
  const pending = alertItems.filter((alert) => !done.includes(alert.id)).length

  return (
    <>
      <PageHeading eyebrow="THEO DÕI CHỦ ĐỘNG" title="Cảnh báo & khuyến nghị" description="Ưu tiên tín hiệu cần xử lý và hành động gợi ý dựa trên dữ liệu." />

      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <FilterPills options={["Tất cả", "Cao", "Trung bình", "Thấp"]} value={filter} onChange={setFilter} />
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <MockNotice />
          <span>{pending} cảnh báo chưa xử lý</span>
        </div>
      </div>

      <div className="flex flex-col gap-3">
        {alerts.map((alert) => {
          const completed = done.includes(alert.id)
          return (
            <article
              key={alert.id}
              className={`rounded-2xl border bg-card p-5 shadow-sm ${completed ? "border-emerald-500/40 opacity-70" : "border-border"}`}
            >
              <div className="flex flex-col gap-4 sm:flex-row">
                <div className={`grid size-10 shrink-0 place-items-center rounded-xl ${completed ? toneClass.positive : severityTone[alert.severity]}`}>
                  {completed ? <CheckCircle2 size={19} /> : <Activity size={19} />}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="text-sm font-semibold text-foreground">{alert.title}</h2>
                    <span className={`rounded-full px-2 py-1 text-[9px] font-semibold ${severityTone[alert.severity]}`}>Mức {alert.severity}</span>
                    {completed && <span className="text-[10px] text-emerald-600">Đã xử lý</span>}
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">{alert.detail}</p>
                  <div className="mt-3 flex flex-wrap gap-3 text-[10px] text-muted-foreground">
                    <span>{alert.platform}</span>
                    <span>·</span>
                    <span>{alert.age}</span>
                  </div>
                  <div className="mt-4 rounded-xl bg-muted/60 p-3">
                    <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Hành động đề xuất</div>
                    <p className="mt-1 text-xs leading-relaxed text-foreground/80">{alert.action}</p>
                  </div>
                </div>
                <button
                  onClick={() => setDone((items) => (completed ? items.filter((id) => id !== alert.id) : [...items, alert.id]))}
                  className={`h-fit shrink-0 rounded-lg px-3 py-2 text-xs font-semibold ${
                    completed ? "border border-border text-muted-foreground hover:bg-muted" : "bg-indigo-600 text-white hover:bg-indigo-700"
                  }`}
                >
                  {completed ? "Mở lại" : "Đánh dấu xử lý"}
                </button>
              </div>
            </article>
          )
        })}
        {alerts.length === 0 && <div className="rounded-2xl border border-dashed border-border py-12 text-center text-xs text-muted-foreground">Không có cảnh báo ở mức này.</div>}
      </div>
    </>
  )
}
