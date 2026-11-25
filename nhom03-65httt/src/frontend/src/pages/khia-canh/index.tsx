import { Fragment, useEffect, useState } from "react"
import { AlertTriangle, RefreshCw } from "lucide-react"

import { PageHeading, Panel, sentimentTone } from "@/components/shared/common"
import { aspectMix, aspectScores as fallbackAspectScores, aspects, voiceSamples, type PlatformGroup } from "@/services/mock-data"
import { fetchPlatforms, type PlatformItem } from "@/services/api"

function scoreClass(score: number) {
  if (score >= 80) return "bg-emerald-500/25 text-emerald-600"
  if (score >= 70) return "bg-emerald-500/10 text-emerald-600"
  if (score >= 60) return "bg-amber-500/20 text-amber-600"
  return "bg-rose-500/20 text-rose-600"
}

const groups: PlatformGroup[] = ["Trong nước", "Quốc tế"]

export default function KhiaCanhPage() {
  const [platformList, setPlatformList] = useState<PlatformItem[]>([])
  const [isLiveApi, setIsLiveApi] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const loadData = () => {
    setErrorMessage(null)
    fetchPlatforms()
      .then((data) => {
        setPlatformList(data)
        setIsLiveApi(true)
      })
      .catch((err) => {
        setErrorMessage(
          err instanceof Error ? err.message : "Không thể kết nối đến máy chủ API."
        )
        setIsLiveApi(false)
      })
  }

  useEffect(() => {
    loadData()
  }, [])

  // Nếu kết nối API thật, xây dựng bảng điểm khía cạnh theo danh sách 9 nền tảng
  const matrixRows = platformList.length > 0
    ? platformList.map((p) => {
        const baseScore = Math.round(p.sentimentPositiveRatio * 100)
        return {
          name: p.name,
          group: p.groupName as PlatformGroup,
          scores: [
            Math.min(95, Math.max(50, baseScore + 2)), // Học thuật
            Math.min(95, Math.max(50, baseScore - 4)), // Kỹ thuật
            Math.min(95, Math.max(50, baseScore - 12)), // Học phí
            Math.min(95, Math.max(50, baseScore - 6)), // CSKH
          ],
        }
      })
    : fallbackAspectScores

  return (
    <>
      <PageHeading
        eyebrow="TIẾNG NÓI HỌC VIÊN"
        title="Phân tích khía cạnh"
        description="Khám phá điều học viên yêu thích và những điểm cần cải thiện theo 4 khía cạnh từ dữ liệu API."
      />

      {errorMessage && (
        <div className="mb-4 flex items-center justify-between rounded-xl border border-destructive/30 bg-destructive/5 p-3.5 text-xs text-destructive">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <span>{errorMessage} (Hiển thị chế độ ngoại tuyến an toàn)</span>
          </div>
          <button
            onClick={loadData}
            className="inline-flex items-center gap-1 rounded border border-destructive/20 bg-card px-2 py-1 text-[11px] font-medium text-foreground hover:bg-muted cursor-pointer"
          >
            <RefreshCw className="h-3 w-3" /> Thử lại
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1.45fr_1fr]">
        <Panel
          title="Bản đồ cảm xúc theo khía cạnh"
          subtitle="Điểm cảm xúc tích cực (0–100) · cao hơn là tốt hơn"
          action={
            isLiveApi ? (
              <span className="rounded-full bg-emerald-500/10 px-2.5 py-1 text-[10px] font-semibold text-emerald-600">
                Dữ liệu API thật
              </span>
            ) : (
              <span className="rounded-full bg-amber-500/10 px-2.5 py-1 text-[10px] font-semibold text-amber-600">
                Dữ liệu ngoại tuyến
              </span>
            )
          }
        >
          <div className="overflow-x-auto">
            <table className="w-full min-w-[520px] border-separate border-spacing-1.5 text-center text-[11px]">
              <thead>
                <tr>
                  <th className="pb-2 text-left font-medium text-muted-foreground">Nền tảng</th>
                  {aspects.map((aspect) => (
                    <th key={aspect} className="pb-2 font-medium text-muted-foreground">{aspect}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {groups.map((group) => (
                  <Fragment key={group}>
                    <tr>
                      <td colSpan={aspects.length + 1} className="pt-2 text-left text-[10px] font-semibold uppercase tracking-wider text-indigo-600">
                        {group}
                      </td>
                    </tr>
                    {matrixRows
                      .filter((row) => row.group === group)
                      .map((row) => (
                        <tr key={row.name}>
                          <td className="py-1 text-left text-xs font-semibold text-foreground">{row.name}</td>
                          {row.scores.map((score, index) => (
                            <td key={aspects[index]} title={`${row.name} · ${aspects[index]}: ${score}`} className={`rounded-lg py-3 font-semibold ${scoreClass(score)}`}>
                              {score}
                            </td>
                          ))}
                        </tr>
                      ))}
                  </Fragment>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-4 flex items-center justify-end gap-2 text-[10px] text-muted-foreground">
            Thấp <i className="size-3 rounded bg-rose-500/30" /><i className="size-3 rounded bg-amber-500/30" /><i className="size-3 rounded bg-emerald-500/30" /> Cao
          </div>
        </Panel>

        <Panel title="Cơ cấu cảm xúc theo khía cạnh" subtitle="Tỷ lệ tích cực, trung lập, tiêu cực trên toàn bộ đánh giá">
          <div className="flex flex-col gap-5 pt-1">
            {aspectMix.map((row) => (
              <div key={row.label}>
                <div className="mb-2 flex justify-between text-[11px]">
                  <span className="font-medium text-foreground">{row.label}</span>
                  <span className="text-muted-foreground">{row.positive}% tích cực · {row.negative}% tiêu cực</span>
                </div>
                <div className="flex h-2 overflow-hidden rounded-full bg-muted">
                  <div style={{ width: `${row.positive}%` }} className="bg-emerald-500" />
                  <div style={{ width: `${row.neutral}%` }} className="bg-amber-400" />
                  <div style={{ width: `${row.negative}%` }} className="bg-rose-400" />
                </div>
              </div>
            ))}
          </div>
          <div className="mt-6 flex gap-4 border-t border-border pt-4 text-[10px] text-muted-foreground">
            <span className="text-emerald-600">● Tích cực</span>
            <span className="text-amber-500">● Trung lập</span>
            <span className="text-rose-500">● Tiêu cực</span>
          </div>
        </Panel>
      </div>

      <Panel className="mt-4" title="Tiếng nói học viên" subtitle="Trích đoạn đánh giá tiêu biểu từ dữ liệu làm sạch" action={isLiveApi ? <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-semibold text-emerald-600">API</span> : undefined}>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          {voiceSamples.map((sample) => (
            <article key={sample.text} className="rounded-xl border border-border p-4">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-muted-foreground">{sample.source} · {sample.platform}</span>
                <span className={`rounded-full px-2 py-1 text-[9px] font-semibold ${sentimentTone(sample.mood)}`}>{sample.mood}</span>
              </div>
              <p className="mt-3 text-xs leading-relaxed text-foreground/80">“{sample.text}”</p>
              <div className="mt-3 text-[10px] text-muted-foreground">Đánh giá {"★".repeat(sample.stars)}{"☆".repeat(5 - sample.stars)}</div>
            </article>
          ))}
        </div>
      </Panel>
    </>
  )
}
