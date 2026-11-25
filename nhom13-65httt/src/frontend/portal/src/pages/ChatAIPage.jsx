import React, { useEffect, useRef, useState } from 'react'
import { Bot, Database, Send, Sparkles, Trash2, User } from 'lucide-react'
import api from '../api/client'
import DataTablePreview from '../components/DataTablePreview'

const SUGGESTIONS = [
  'Hãy giúp tôi kiểm tra xem trong tháng 10 vừa rồi 5 nguồn tiền gửi đi nhiều nhất trong tháng',
  'Tỷ lệ tiết kiệm ròng 6 tháng gần đây của tôi như thế nào?',
  'Danh mục chi tiêu nào trong tháng 11 đang vượt trần ngân sách?',
  'Liệt kê các giao dịch bất thường AI đã phát hiện cần tôi xem lại',
]

export default function ChatAIPage() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const bottomRef = useRef(null)

  const loadHistory = async () => {
    try {
      const res = await api.get('/chat/history')
      setMessages(res.data.messages || [])
    } catch (err) {
      console.error(err)
    }
  }

  useEffect(() => {
    loadHistory()
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, sending])

  const sendQuestion = async (questionText) => {
    const q = (questionText || input).trim()
    if (!q || sending) return

    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: q }])
    setSending(true)

    try {
      const res = await api.post('/chat/ask', { question: q })
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: res.data.answer,
          structured_data: res.data.structured_data,
          tools_used: res.data.tools_used,
        },
      ])
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `Xin lỗi, đã xảy ra lỗi khi kết nối Gemini AI: ${err.response?.data?.detail || err.message}`,
        },
      ])
    } finally {
      setSending(false)
    }
  }

  const handleClear = async () => {
    try {
      await api.delete('/chat/history')
      setMessages([])
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-3rem)]">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-200">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center shadow-sm">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900">Trợ lý Chat AI Gemini (Dữ liệu thật)</h2>
            <p className="text-xs text-slate-500">
              Truy vấn trực tiếp PostgreSQL Data Warehouse bằng Function Calling — 100% con số chính xác theo tài khoản của bạn
            </p>
          </div>
        </div>
        <button
          onClick={handleClear}
          className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-white border border-slate-200 hover:bg-rose-50 hover:text-rose-700 hover:border-rose-200 text-xs font-semibold text-slate-600 transition"
        >
          <Trash2 className="w-3.5 h-3.5" />
          Xóa lịch sử
        </button>
      </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto py-5 space-y-4">
        {messages.length === 0 && (
          <div className="bg-white rounded-2xl border border-slate-200 p-6 max-w-3xl mx-auto mt-6 shadow-sm">
            <h3 className="text-sm font-bold text-slate-800 mb-2">
              Hỏi bất cứ điều gì về dòng tiền cá nhân của bạn!
            </h3>
            <p className="text-xs text-slate-500 mb-4">
              AI Gemini sẽ tự động gọi công cụ truy vấn trên kho dữ liệu thật của bạn và hiển thị bảng số liệu đối chiếu:
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {SUGGESTIONS.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => sendQuestion(q)}
                  className="text-left p-3 rounded-xl bg-slate-50 hover:bg-indigo-50 border border-slate-200 hover:border-indigo-300 text-xs text-slate-700 hover:text-indigo-900 transition"
                >
                  “{q}”
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center shrink-0 mt-1">
                <Bot className="w-4 h-4 text-white" />
              </div>
            )}

            <div
              className={`max-w-3xl rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-white border border-slate-200 text-slate-800 shadow-sm'
              }`}
            >
              <div className="whitespace-pre-wrap">{msg.content}</div>

              {msg.tools_used && msg.tools_used.length > 0 && (
                <div className="mt-2.5 pt-2 border-t border-slate-100 flex flex-wrap gap-1.5">
                  {msg.tools_used.map((t, tIdx) => (
                    <span
                      key={tIdx}
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-100 text-[11px] font-mono text-slate-600"
                    >
                      <Database className="w-3 h-3 text-indigo-500" />
                      {t}
                    </span>
                  ))}
                </div>
              )}

              <DataTablePreview tables={msg.structured_data} />
            </div>

            {msg.role === 'user' && (
              <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center shrink-0 mt-1">
                <User className="w-4 h-4 text-white" />
              </div>
            )}
          </div>
        ))}

        {sending && (
          <div className="flex gap-3 items-center text-xs text-slate-500">
            <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center animate-pulse">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <span>Gemini đang truy vấn PostgreSQL và tổng hợp phân tích dữ liệu thật...</span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <form
        onSubmit={(e) => {
          e.preventDefault()
          sendQuestion()
        }}
        className="pt-3 border-t border-slate-200 flex gap-2"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={sending}
          placeholder="Nhập câu hỏi về dòng tiền (VD: Tháng 10 vừa rồi 5 tài khoản nhận tiền nhiều nhất là ai?)..."
          className="flex-1 px-4 py-3 rounded-xl bg-white border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <button
          type="submit"
          disabled={sending || !input.trim()}
          className="px-5 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-sm font-semibold inline-flex items-center gap-2 shadow-sm transition"
        >
          <Send className="w-4 h-4" />
          Gửi
        </button>
      </form>
    </div>
  )
}
