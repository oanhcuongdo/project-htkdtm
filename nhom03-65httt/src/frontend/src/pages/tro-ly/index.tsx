import { useEffect, useRef, useState } from "react"
import { ArrowUp, BookOpen, Sparkles } from "lucide-react"

import { MockNotice, PageHeading, formatNumber } from "@/components/shared/common"
import { chatAnswers, chatFallback, chatSuggestions, sources } from "@/services/mock-data"

interface ChatMessage {
  from: "user" | "ai"
  text: string
}

const TOTAL = sources.reduce((sum, item) => sum + item.reviews, 0)

export default function TroLyPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      from: "ai",
      text: "Xin chào! Tôi là trợ lý phân tích EduVision. Tôi có thể giúp bạn khám phá dữ liệu về trải nghiệm học viên và các nền tảng e-learning.",
    },
  ])
  const [input, setInput] = useState("")
  const [typing, setTyping] = useState(false)
  const timer = useRef<number | undefined>(undefined)
  const bottom = useRef<HTMLDivElement>(null)

  // Lưu ý: hàm trong useEffect không được trả về giá trị nào khác ngoài hàm dọn dẹp.
  // Một số tiện ích trình duyệt làm scrollIntoView trả về Promise, nên phải dùng thân hàm có dấu ngoặc nhọn.
  useEffect(() => {
    return () => window.clearTimeout(timer.current)
  }, [])
  useEffect(() => {
    bottom.current?.scrollIntoView({ block: "nearest" })
  }, [messages, typing])

  const ask = (raw: string) => {
    const text = raw.trim()
    if (!text || typing) return
    setMessages((current) => [...current, { from: "user", text }])
    setInput("")
    setTyping(true)
    timer.current = window.setTimeout(() => {
      setMessages((current) => [...current, { from: "ai", text: chatAnswers[text] ?? chatFallback }])
      setTyping(false)
    }, 900)
  }

  return (
    <>
      <PageHeading eyebrow="PHÂN TÍCH ĐỐI THOẠI" title="Trợ lý AI" description="Đặt câu hỏi bằng ngôn ngữ tự nhiên về dữ liệu học viên." />

      <div className="mx-auto max-w-4xl overflow-hidden rounded-2xl border border-border bg-card shadow-sm">
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <div className="flex items-center gap-3">
            <div className="grid size-9 place-items-center rounded-xl bg-indigo-600 text-white"><Sparkles size={17} /></div>
            <div>
              <div className="text-xs font-semibold text-foreground">EduVision AI</div>
              <div className="mt-0.5 flex items-center gap-1.5 text-[10px] text-muted-foreground">
                <span className="size-1.5 rounded-full bg-emerald-500" />Sẵn sàng phân tích
              </div>
            </div>
          </div>
          <MockNotice />
        </div>

        <div className="flex max-h-[460px] min-h-[390px] flex-col gap-5 overflow-y-auto bg-muted/40 p-5">
          {messages.map((message, index) => (
            <div key={index} className={`flex gap-3 ${message.from === "user" ? "justify-end" : ""}`}>
              {message.from === "ai" && (
                <div className="grid size-8 shrink-0 place-items-center rounded-lg bg-indigo-600 text-white"><Sparkles size={14} /></div>
              )}
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 text-xs leading-relaxed ${
                  message.from === "user" ? "rounded-tr-md bg-indigo-600 text-white" : "rounded-tl-md border border-border bg-card text-foreground"
                }`}
              >
                {message.text}
                {message.from === "ai" && index > 0 && (
                  <div className="mt-3 flex items-center gap-1.5 border-t border-border pt-2 text-[10px] text-muted-foreground">
                    <BookOpen size={11} />Nguồn: đánh giá ứng dụng · {formatNumber(TOTAL)} mẫu (minh họa)
                  </div>
                )}
              </div>
            </div>
          ))}
          {typing && (
            <div className="flex gap-3">
              <div className="grid size-8 place-items-center rounded-lg bg-indigo-600 text-white"><Sparkles size={14} /></div>
              <div className="flex items-center gap-1 rounded-2xl border border-border bg-card px-4">
                <i className="size-1.5 animate-bounce rounded-full bg-muted-foreground" />
                <i className="size-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:150ms]" />
                <i className="size-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:300ms]" />
              </div>
            </div>
          )}
          <div ref={bottom} />
        </div>

        <div className="border-t border-border p-4">
          <div className="mb-3 flex flex-wrap gap-2">
            {chatSuggestions.map((question) => (
              <button
                key={question}
                onClick={() => ask(question)}
                disabled={typing}
                className="rounded-full border border-border px-3 py-1.5 text-[10px] text-muted-foreground transition hover:border-indigo-300 hover:bg-indigo-500/10 hover:text-indigo-600 disabled:opacity-50"
              >
                {question}
              </button>
            ))}
          </div>
          <form
            onSubmit={(event) => {
              event.preventDefault()
              ask(input)
            }}
            className="flex items-center gap-2 rounded-xl border border-border bg-background p-1.5 focus-within:border-indigo-300"
          >
            <input
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Hỏi bất kỳ điều gì về dữ liệu..."
              className="min-w-0 flex-1 bg-transparent px-3 py-2 text-xs text-foreground outline-none placeholder:text-muted-foreground"
            />
            <button
              type="submit"
              disabled={!input.trim() || typing}
              aria-label="Gửi câu hỏi"
              className="grid size-9 place-items-center rounded-lg bg-indigo-600 text-white transition hover:bg-indigo-700 disabled:opacity-40"
            >
              <ArrowUp size={17} />
            </button>
          </form>
          <div className="mt-2 text-center text-[9px] text-muted-foreground">AI có thể mắc lỗi. Vui lòng kiểm tra lại thông tin quan trọng.</div>
        </div>
      </div>
    </>
  )
}
