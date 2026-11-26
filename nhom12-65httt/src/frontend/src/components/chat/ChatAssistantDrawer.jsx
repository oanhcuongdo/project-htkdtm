import {
  Bot,
  ChevronDown,
  ChevronUp,
  Code2,
  Copy,
  Check,
  Maximize2,
  Minimize2,
  Send,
  Sparkles,
  Trash2,
  User,
  X,
} from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { useSession } from '../../contexts/SessionContext';
import { queryChatbot } from '../../services/chatbotService';
import { ChatbotChartRenderer } from './ChatbotChartRenderer';

const QUICK_PROMPTS = [
  'So sánh mặt bằng giá thuê theo quận',
  'Nguồn cung phòng trọ quận nào nhiều nhất?',
  'Mặt bằng đơn giá thuê (k/m²)',
  'Thống kê số lượng theo loại hình phòng',
];

const ADMIN_QUICK_PROMPT = 'Top 10 tin đăng có rủi ro cao hoặc bị báo cáo';

export function ChatAssistantDrawer({ open, onClose }) {
  const { sessionId, isAdmin } = useSession();
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        'Xin chào! Tôi là Trợ lý BI Phân tích thị trường nhà thuê Hà Nội. Bạn có thể hỏi tôi về giá thuê, nguồn cung các quận, biến động thị trường hoặc bất kỳ chỉ số kinh doanh nào!',
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [expandedSqlIds, setExpandedSqlIds] = useState(new Set());
  const [copiedSqlId, setCopiedSqlId] = useState(null);

  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (open) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, open]);

  if (!open) return null;

  const toggleSql = (msgId) => {
    setExpandedSqlIds((prev) => {
      const next = new Set(prev);
      if (next.has(msgId)) next.delete(msgId);
      else next.add(msgId);
      return next;
    });
  };

  const copySql = (msgId, sql) => {
    navigator.clipboard.writeText(sql);
    setCopiedSqlId(msgId);
    setTimeout(() => setCopiedSqlId(null), 2000);
  };

  const handleSend = async (queryText) => {
    const text = (queryText || input).trim();
    if (!text || isLoading) return;

    const userMsgId = `user_${Date.now()}`;
    const botMsgId = `bot_${Date.now()}`;

    setMessages((prev) => [
      ...prev,
      { id: userMsgId, role: 'user', content: text },
    ]);
    setInput('');
    setIsLoading(true);

    try {
      const res = await queryChatbot(text, sessionId);
      setMessages((prev) => [
        ...prev,
        {
          id: botMsgId,
          role: 'assistant',
          content: res.insight || 'Đã phân tích xong dữ liệu truy vấn.',
          sql: res.sql,
          chartType: res.chart_type,
          columns: res.columns,
          rows: res.rows,
          totalRows: res.total_rows,
        },
      ]);
    } catch (err) {
      const errMsg =
        err?.response?.data?.detail ||
        'Rất tiếc, đã có lỗi xảy ra khi truy vấn dữ liệu. Vui lòng thử lại với câu hỏi khác!';
      setMessages((prev) => [
        ...prev,
        {
          id: botMsgId,
          role: 'assistant',
          isError: true,
          content: errMsg,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content:
          'Đã làm mới cuộc hội thoại. Hãy đặt câu hỏi bất kỳ về thị trường phòng trọ Hà Nội nhé!',
      },
    ]);
  };

  const promptList = isAdmin ? [...QUICK_PROMPTS, ADMIN_QUICK_PROMPT] : QUICK_PROMPTS;

  return (
    <aside
      aria-label="Trợ lý Chatbot BI"
      className={`fixed z-50 flex flex-col overflow-hidden bg-white shadow-2xl transition-all duration-300 ${
        isExpanded
          ? 'bottom-2 right-2 left-2 top-2 sm:bottom-4 sm:right-4 sm:left-auto sm:top-auto sm:h-[85vh] sm:w-[680px] rounded-2xl border border-teal-200'
          : 'bottom-4 right-4 h-[560px] w-[min(94vw,440px)] rounded-2xl border border-teal-200'
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between bg-gradient-to-r from-[#0F766E] to-[#134E4A] px-4 py-3 text-white">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/15">
            <Bot className="h-5 w-5" aria-hidden="true" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-sm font-bold">Trợ lý BI (Text-to-SQL)</span>
              {isAdmin && (
                <span className="rounded bg-amber-400/20 px-1.5 py-0.2 text-[10px] font-semibold text-amber-200">
                  Admin
                </span>
              )}
            </div>
            <p className="text-[11px] text-teal-100/90">Gemini Flash · PostgreSQL Star Schema</p>
          </div>
        </div>

        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={clearChat}
            title="Xóa lịch sử chat"
            className="flex h-8 w-8 items-center justify-center rounded-lg hover:bg-white/15 text-teal-100"
          >
            <Trash2 className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={() => setIsExpanded((v) => !v)}
            title={isExpanded ? 'Thu nhỏ' : 'Mở rộng'}
            className="hidden sm:flex h-8 w-8 items-center justify-center rounded-lg hover:bg-white/15 text-teal-100"
          >
            {isExpanded ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
          </button>
          <button
            type="button"
            onClick={onClose}
            aria-label="Đóng khung chat"
            className="flex h-8 w-8 items-center justify-center rounded-lg hover:bg-white/15 text-teal-100"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto bg-[#F8FAFC] p-4 space-y-4 text-sm">
        {messages.map((msg) => {
          const isBot = msg.role === 'assistant';
          const isSqlOpen = expandedSqlIds.has(msg.id);

          return (
            <div
              key={msg.id}
              className={`flex gap-2.5 ${isBot ? 'items-start' : 'items-start justify-end'}`}
            >
              {isBot && (
                <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#0F766E] text-white shadow-xs">
                  <Bot className="h-4 w-4" />
                </div>
              )}

              <div className={`max-w-[88%] ${isBot ? 'w-full' : ''}`}>
                <div
                  className={`rounded-2xl p-3 text-xs sm:text-sm ${
                    isBot
                      ? msg.isError
                        ? 'border border-red-200 bg-red-50 text-red-800'
                        : 'border border-teal-100 bg-white text-[#1E293B] shadow-xs'
                      : 'bg-[#0F766E] text-white shadow-xs ml-auto'
                  }`}
                >
                  {isBot && !msg.isError && (
                    <div className="mb-1 flex items-center gap-1 text-[11px] font-semibold text-[#0F766E]">
                      <Sparkles className="h-3 w-3" />
                      <span>Insight BI</span>
                    </div>
                  )}

                  <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>

                  {/* Khối hiển thị câu truy vấn SQL (Collapsible) */}
                  {msg.sql && (
                    <div className="mt-2.5 rounded-lg border border-slate-200 bg-slate-900 text-slate-100 overflow-hidden text-[11px]">
                      <div className="flex items-center justify-between bg-slate-800/90 px-2.5 py-1.5">
                        <button
                          type="button"
                          onClick={() => toggleSql(msg.id)}
                          className="flex items-center gap-1.5 font-mono text-teal-300 hover:text-teal-200"
                        >
                          <Code2 className="h-3.5 w-3.5" />
                          <span>SQL AST (READ ONLY)</span>
                          {isSqlOpen ? (
                            <ChevronUp className="h-3.5 w-3.5" />
                          ) : (
                            <ChevronDown className="h-3.5 w-3.5" />
                          )}
                        </button>

                        <button
                          type="button"
                          onClick={() => copySql(msg.id, msg.sql)}
                          className="flex items-center gap-1 rounded px-1.5 py-0.5 text-slate-300 hover:bg-slate-700 hover:text-white"
                          title="Sao chép SQL"
                        >
                          {copiedSqlId === msg.id ? (
                            <>
                              <Check className="h-3 w-3 text-emerald-400" /> Đã chép
                            </>
                          ) : (
                            <>
                              <Copy className="h-3 w-3" /> Copy
                            </>
                          )}
                        </button>
                      </div>

                      {isSqlOpen && (
                        <pre className="overflow-x-auto p-2.5 font-mono text-[11px] leading-tight text-teal-200">
                          {msg.sql}
                        </pre>
                      )}
                    </div>
                  )}

                  {/* Render Chart / Table */}
                  {msg.rows && msg.rows.length > 0 && (
                    <ChatbotChartRenderer
                      chartType={msg.chartType}
                      columns={msg.columns}
                      rows={msg.rows}
                    />
                  )}
                </div>
              </div>

              {!isBot && (
                <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-200 text-slate-700 shadow-xs">
                  <User className="h-4 w-4" />
                </div>
              )}
            </div>
          );
        })}

        {isLoading && (
          <div className="flex items-center gap-2 text-xs text-[#0F766E]">
            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-[#0F766E]/10 animate-pulse">
              <Bot className="h-3.5 w-3.5" />
            </div>
            <span>Đang chuyển câu hỏi thành SQL và phân tích dữ liệu thị trường...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Gợi ý câu hỏi nhanh (Prompt Chips) */}
      <div className="border-t border-slate-100 bg-white px-3 py-2 overflow-x-auto no-scrollbar">
        <div className="flex gap-1.5 whitespace-nowrap">
          {promptList.map((prompt) => (
            <button
              key={prompt}
              type="button"
              onClick={() => handleSend(prompt)}
              disabled={isLoading}
              className="inline-flex items-center gap-1 rounded-full border border-teal-200 bg-teal-50/70 px-2.5 py-1 text-[11px] font-medium text-[#134E4A] hover:bg-teal-100 transition-colors disabled:opacity-50"
            >
              <Sparkles className="h-2.5 w-2.5 text-[#0F766E]" />
              {prompt}
            </button>
          ))}
        </div>
      </div>

      {/* Input box */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="flex items-center gap-2 border-t border-slate-200 bg-white p-3"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Hỏi về giá thuê, khu vực, loại phòng..."
          disabled={isLoading}
          className="flex-1 rounded-xl border border-slate-200 px-3.5 py-2 text-xs sm:text-sm text-slate-800 focus:border-[#0F766E] focus:outline-none focus:ring-1 focus:ring-[#0F766E]"
        />
        <button
          type="submit"
          disabled={!input.trim() || isLoading}
          className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[#0F766E] text-white hover:bg-[#134E4A] transition-colors disabled:opacity-40"
          aria-label="Gửi tin nhắn"
        >
          <Send className="h-4 w-4" />
        </button>
      </form>
    </aside>
  );
}
