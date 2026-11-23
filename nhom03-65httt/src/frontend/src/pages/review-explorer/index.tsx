import { useEffect, useMemo, useState } from "react"
import { AlertTriangle, ChevronLeft, ChevronRight, Search } from "lucide-react"

import { MockNotice, PageHeading, Panel, SelectControl, sentimentTone, toneClass } from "@/components/shared/common"
import { aspects, platforms, reviewRows, sources } from "@/services/mock-data"

const PAGE_SIZE = 6
const ALL_PLATFORMS = "Tất cả nền tảng"
const ALL_SOURCES = "Tất cả nguồn"
const ALL_SENTIMENTS = "Tất cả cảm xúc"
const ALL_ASPECTS = "Tất cả khía cạnh"

export default function ReviewExplorerPage() {
  const [query, setQuery] = useState("")
  const [platform, setPlatform] = useState(ALL_PLATFORMS)
  const [source, setSource] = useState(ALL_SOURCES)
  const [sentiment, setSentiment] = useState(ALL_SENTIMENTS)
  const [aspect, setAspect] = useState(ALL_ASPECTS)
  const [onlyMisaligned, setOnlyMisaligned] = useState(false)
  const [page, setPage] = useState(1)

  const filtered = useMemo(() => {
    const keyword = query.trim().toLowerCase()
    return reviewRows.filter(
      (row) =>
        (!keyword || `${row.text} ${row.id} ${row.platform}`.toLowerCase().includes(keyword)) &&
        (platform === ALL_PLATFORMS || row.platform === platform) &&
        (source === ALL_SOURCES || row.source === source) &&
        (sentiment === ALL_SENTIMENTS || row.sentiment === sentiment) &&
        (aspect === ALL_ASPECTS || row.aspect === aspect) &&
        (!onlyMisaligned || row.misaligned),
    )
  }, [query, platform, source, sentiment, aspect, onlyMisaligned])

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const safePage = Math.min(page, pageCount)
  const visible = filtered.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE)

  // Quay về trang 1 khi đổi bộ lọc.
  useEffect(() => {
    setPage(1)
  }, [query, platform, source, sentiment, aspect, onlyMisaligned])

  return (
    <>
      <PageHeading eyebrow="KHO DỮ LIỆU ĐÁNH GIÁ" title="Review Explorer" description="Tìm kiếm, lọc và rà soát các đánh giá đã được AI gắn nhãn." />

      <Panel title="Bộ lọc đánh giá" subtitle="Dùng bộ lọc để thu hẹp kết quả" action={<MockNotice />}>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-5">
          <label className="flex flex-col gap-1.5 text-[10px] font-medium text-muted-foreground">
            Tìm kiếm
            <div className="relative">
              <Search className="absolute left-3 top-2.5 text-muted-foreground" size={14} />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Từ khóa hoặc mã review"
                className="w-full rounded-lg border border-border bg-background py-2 pl-9 pr-3 text-xs text-foreground outline-none focus:border-indigo-400"
              />
            </div>
          </label>
          <SelectControl label="Nền tảng" value={platform} onChange={setPlatform} options={[ALL_PLATFORMS, ...platforms.map((item) => item.name)]} />
          <SelectControl label="Nguồn" value={source} onChange={setSource} options={[ALL_SOURCES, ...sources.map((item) => item.name)]} />
          <SelectControl label="Cảm xúc" value={sentiment} onChange={setSentiment} options={[ALL_SENTIMENTS, "Tích cực", "Trung lập", "Tiêu cực"]} />
          <SelectControl label="Khía cạnh" value={aspect} onChange={setAspect} options={[ALL_ASPECTS, ...aspects]} />
        </div>
        <label className="mt-4 flex w-fit cursor-pointer items-center gap-2 text-xs text-muted-foreground">
          <input type="checkbox" checked={onlyMisaligned} onChange={(event) => setOnlyMisaligned(event.target.checked)} />
          Chỉ hiện đánh giá lệch pha (số sao và nội dung mâu thuẫn)
        </label>
      </Panel>

      <Panel title="Kết quả đánh giá" subtitle={`${filtered.length} đánh giá phù hợp với bộ lọc`} className="mt-4">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[820px] text-left text-xs">
            <thead>
              <tr className="text-[10px] uppercase tracking-wider text-muted-foreground">
                <th className="pb-3 font-medium">Đánh giá</th>
                <th className="pb-3 font-medium">Nền tảng / nguồn</th>
                <th className="pb-3 font-medium">Cảm xúc</th>
                <th className="pb-3 font-medium">Khía cạnh</th>
                <th className="pb-3 font-medium">Ngày</th>
                <th className="pb-3 font-medium">Cờ lệch pha</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((row) => (
                <tr key={row.id} className="border-t border-border align-top">
                  <td className="max-w-[360px] py-4 pr-4">
                    <div className="mb-1 text-[10px] font-semibold text-indigo-600">{row.id}</div>
                    <p className="leading-relaxed text-foreground/80">{row.text}</p>
                  </td>
                  <td className="py-4">
                    <div className="font-semibold text-foreground">{row.platform}</div>
                    <div className="mt-1 text-[10px] text-muted-foreground">{row.source}</div>
                  </td>
                  <td className="py-4">
                    <span className={`whitespace-nowrap rounded-full px-2 py-1 text-[10px] font-medium ${sentimentTone(row.sentiment)}`}>{row.sentiment}</span>
                  </td>
                  <td className="py-4">
                    <span className="whitespace-nowrap rounded-md border border-border px-2 py-1 text-[10px] text-foreground/80">{row.aspect}</span>
                  </td>
                  <td className="whitespace-nowrap py-4 text-muted-foreground">{row.date}</td>
                  <td className="py-4">
                    {row.misaligned ? (
                      <span className={`inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2 py-1 text-[10px] font-medium ${toneClass.neutral}`}>
                        <AlertTriangle size={11} />Lệch pha
                      </span>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {filtered.length === 0 && <div className="py-12 text-center text-xs text-muted-foreground">Không tìm thấy đánh giá phù hợp.</div>}
        </div>

        {filtered.length > 0 && (
          <div className="mt-4 flex items-center justify-between border-t border-border pt-4 text-xs text-muted-foreground">
            <span>Trang {safePage}/{pageCount}</span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(safePage - 1)}
                disabled={safePage <= 1}
                aria-label="Trang trước"
                className="grid size-8 place-items-center rounded-lg border border-border hover:bg-muted disabled:opacity-40"
              >
                <ChevronLeft size={15} />
              </button>
              <button
                onClick={() => setPage(safePage + 1)}
                disabled={safePage >= pageCount}
                aria-label="Trang sau"
                className="grid size-8 place-items-center rounded-lg border border-border hover:bg-muted disabled:opacity-40"
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
