import { Bot, X } from 'lucide-react';

export function ChatAssistantDrawer({ open, onClose }) {
  if (!open) return null;

  return (
    <aside
      aria-label="Trợ lý Chatbot BI"
      className="fixed bottom-4 right-4 z-50 flex h-80 w-[min(92vw,360px)] flex-col overflow-hidden rounded-2xl border border-teal-200 bg-white shadow-2xl"
    >
      <div className="flex items-center justify-between bg-[#0F766E] px-4 py-3 text-white">
        <div className="flex items-center gap-2">
          <Bot className="h-5 w-5" aria-hidden="true" />
          <p className="text-sm font-semibold">Trợ lý Chatbot BI (Khung chờ)</p>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Đóng khung chat"
          className="flex h-10 w-10 items-center justify-center rounded-lg hover:bg-white/15"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      <div className="flex flex-1 items-center justify-center bg-[#F0FDFA] p-6 text-center text-sm text-[#475569]">
        Khung chờ giao diện Trợ lý Chatbot BI (Text-to-SQL) dành cho Gói Việt.
      </div>
    </aside>
  );
}
