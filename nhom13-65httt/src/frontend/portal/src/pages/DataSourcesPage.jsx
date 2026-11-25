import React, { useEffect, useState } from 'react'
import { CheckCircle2, Cpu, FileSpreadsheet, Image as ImageIcon, Mail, Save, Send, ShieldCheck, UploadCloud } from 'lucide-react'
import api from '../api/client'

export default function DataSourcesPage() {
  const [sources, setSources] = useState([])
  const [uploadResult, setUploadResult] = useState(null)
  const [ocrResult, setOcrResult] = useState(null)
  const [aiStatus, setAiStatus] = useState(null)
  const [busy, setBusy] = useState('')

  // Form cấu hình IMAP & Telegram
  const [imapEmail, setImapEmail] = useState('')
  const [imapPass, setImapPass] = useState('')
  const [imapEnabled, setImapEnabled] = useState(false)
  const [tgChatId, setTgChatId] = useState('')
  const [tgEnabled, setTgEnabled] = useState(false)
  const [saveMsg, setSaveMsg] = useState('')

  const loadSources = async () => {
    try {
      const res = await api.get('/sources')
      setSources(res.data.sources || [])
      const imap = res.data.sources.find((s) => s.source_type === 'EMAIL_IMAP')
      if (imap) {
        setImapEnabled(imap.is_enabled)
        setImapEmail(imap.config_masked?.imap_email || '')
      }
      const tg = res.data.sources.find((s) => s.source_type === 'TELEGRAM_OCR')
      if (tg) {
        setTgEnabled(tg.is_enabled)
        setTgChatId(tg.config_masked?.telegram_chat_id || '')
      }
    } catch (err) {
      console.error(err)
    }
  }

  useEffect(() => {
    loadSources()
  }, [])

  const handleStatementUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setBusy('upload')
    setUploadResult(null)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await api.post('/ingestion/upload-statement', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setUploadResult(res.data)
      loadSources()
    } catch (err) {
      setUploadResult({ error: err.response?.data?.detail || 'Lỗi tải lên file sao kê.' })
    } finally {
      setBusy('')
      e.target.value = ''
    }
  }

  const handleReceiptUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setBusy('ocr')
    setOcrResult(null)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await api.post('/ingestion/ingest-receipt-image', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setOcrResult(res.data)
      loadSources()
    } catch (err) {
      setOcrResult({ error: err.response?.data?.detail || 'Lỗi xử lý OCR biên lai.' })
    } finally {
      setBusy('')
      e.target.value = ''
    }
  }

  const handleSaveImap = async (e) => {
    e.preventDefault()
    setBusy('imap')
    setSaveMsg('')
    try {
      const res = await api.post('/sources/configure', {
        source_type: 'EMAIL_IMAP',
        is_enabled: imapEnabled,
        imap_email: imapEmail,
        imap_app_password: imapPass,
      })
      setSaveMsg(res.data.message)
      setImapPass('')
      loadSources()
    } catch (err) {
      setSaveMsg(err.response?.data?.detail || 'Lỗi lưu cấu hình Email.')
    } finally {
      setBusy('')
    }
  }

  const handleSaveTelegram = async (e) => {
    e.preventDefault()
    setBusy('tg')
    setSaveMsg('')
    try {
      const res = await api.post('/sources/configure', {
        source_type: 'TELEGRAM_OCR',
        is_enabled: tgEnabled,
        telegram_chat_id: tgChatId,
      })
      setSaveMsg(res.data.message)
      loadSources()
    } catch (err) {
      setSaveMsg(err.response?.data?.detail || 'Lỗi lưu cấu hình Telegram.')
    } finally {
      setBusy('')
    }
  }

  const handleRunAI = async () => {
    setBusy('ai')
    setAiStatus(null)
    try {
      const [anom, fc] = await Promise.all([
        api.post('/ai/detect-anomalies?persist=true'),
        api.post('/ai/forecast?horizon_days=30&persist=true'),
      ])
      setAiStatus({
        anomalies: anom.data.anomalies_detected,
        forecast_30d: fc.data.total_predicted_30d_expense,
        mape: fc.data.evaluation?.mape_pct,
      })
    } catch (err) {
      setAiStatus({ error: 'Không thể chạy cập nhật mô hình AI.' })
    } finally {
      setBusy('')
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Trung tâm Kết nối Nguồn Dữ liệu Ngân hàng</h2>
          <p className="text-sm text-slate-500">
            Tùy chọn cách lấy dữ liệu an toàn, không xâm phạm mật khẩu ngân hàng — dữ liệu tách biệt hoàn toàn theo tài khoản của bạn.
          </p>
        </div>
        <button
          onClick={handleRunAI}
          disabled={busy === 'ai'}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 text-white text-xs font-semibold shadow-sm transition"
        >
          <Cpu className="w-4 h-4" />
          {busy === 'ai' ? 'Đang chạy AI...' : 'Cập nhật Bất thường & Dự báo 30 ngày AI'}
        </button>
      </div>

      {aiStatus && (
        <div className="p-4 rounded-xl bg-indigo-50 border border-indigo-200 text-xs text-indigo-900 flex items-center gap-3">
          <CheckCircle2 className="w-4 h-4 text-indigo-600 shrink-0" />
          {aiStatus.error ? (
            <span>{aiStatus.error}</span>
          ) : (
            <span>
              Đã chạy xong AI: phát hiện <strong>{aiStatus.anomalies}</strong> giao dịch bất thường; dự báo 30 ngày tới{' '}
              <strong>{Number(aiStatus.forecast_30d || 0).toLocaleString('vi-VN')} VND</strong> (MAPE {aiStatus.mape}%).
            </span>
          )}
        </div>
      )}

      {saveMsg && (
        <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 font-medium flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          {saveMsg}
        </div>
      )}

      {/* Thống kê trạng thái 3 kênh */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {sources.map((src) => (
          <div key={src.source_type} className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-bold text-indigo-600">{src.source_type}</span>
              <span
                className={`px-2 py-0.5 rounded-full text-[11px] font-semibold ${
                  src.is_enabled ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'
                }`}
              >
                {src.is_enabled ? 'Đang bật' : 'Chưa kích hoạt'}
              </span>
            </div>
            <h3 className="text-sm font-semibold text-slate-900">{src.display_name}</h3>
            <p className="text-xs text-slate-500 mt-1">{src.description}</p>
            <div className="mt-3 pt-2.5 border-t border-slate-100 text-xs text-slate-600">
              Đã nạp: <strong className="text-slate-900">{src.transactions_ingested}</strong> giao dịch
            </div>
          </div>
        ))}
      </div>

      {/* Kênh 1 & Kênh 2: Upload Sao kê & OCR Hóa đơn */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upload Excel/CSV/PDF */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <FileSpreadsheet className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900 text-sm">1. Tải lên Sao kê Ngân hàng (Excel / CSV / PDF)</h3>
              <p className="text-xs text-slate-500">Hỗ trợ Sổ phụ MB Bank (.xlsx), Vietcombank, Techcombank, MoMo</p>
            </div>
          </div>

          <label className="block border-2 border-dashed border-slate-300 hover:border-indigo-400 rounded-2xl p-6 text-center cursor-pointer transition bg-slate-50/50">
            <UploadCloud className="w-8 h-8 text-indigo-500 mx-auto mb-2" />
            <span className="block text-sm font-semibold text-slate-700">
              {busy === 'upload' ? 'Đang bóc tách, khử trùng lặp & nạp DB...' : 'Chọn file .xlsx, .csv hoặc .pdf'}
            </span>
            <span className="block text-xs text-slate-400 mt-1">
              Tự động tách tên đối tác, ẩn số TK và chạy 5 luật Data Quality
            </span>
            <input
              type="file"
              accept=".xlsx,.xls,.csv,.pdf"
              onChange={handleStatementUpload}
              disabled={busy === 'upload'}
              className="hidden"
            />
          </label>

          {uploadResult && (
            <div className="mt-4 p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-1">
              {uploadResult.error ? (
                <p className="text-rose-600 font-medium">{uploadResult.error}</p>
              ) : (
                <>
                  <p className="font-semibold text-emerald-700">✓ Đã xử lý file: {uploadResult.file_name}</p>
                  <p>
                    Tổng đọc: <strong>{uploadResult.etl_summary?.total_input}</strong> • Nạp mới:{' '}
                    <strong className="text-emerald-700">{uploadResult.etl_summary?.inserted}</strong> • Khử trùng lặp:{' '}
                    <strong className="text-amber-700">{uploadResult.etl_summary?.deduplicated}</strong>
                  </p>
                  <p>
                    5 luật Data Quality:{' '}
                    <strong className="text-indigo-700">
                      {uploadResult.etl_summary?.data_quality_passed ? 'ĐẠT 100%' : 'Cần kiểm tra'}
                    </strong>
                  </p>
                </>
              )}
            </div>
          )}
        </div>

        {/* Upload Ảnh Hóa đơn OCR */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
              <ImageIcon className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900 text-sm">2. Quét Ảnh Hóa Đơn / Biên Lai (OCR Tiếng Việt)</h3>
              <p className="text-xs text-slate-500">Tesseract OCR tự động đọc số tiền, ngày giờ và tên cửa hàng</p>
            </div>
          </div>

          <label className="block border-2 border-dashed border-slate-300 hover:border-amber-400 rounded-2xl p-6 text-center cursor-pointer transition bg-slate-50/50">
            <ImageIcon className="w-8 h-8 text-amber-500 mx-auto mb-2" />
            <span className="block text-sm font-semibold text-slate-700">
              {busy === 'ocr' ? 'Đang chạy Tesseract OCR tiếng Việt...' : 'Chọn ảnh chụp hóa đơn (.jpg, .png)'}
            </span>
            <span className="block text-xs text-slate-400 mt-1">
              Tự động phân loại danh mục bằng AI NLP sau khi bóc tách
            </span>
            <input
              type="file"
              accept="image/*"
              onChange={handleReceiptUpload}
              disabled={busy === 'ocr'}
              className="hidden"
            />
          </label>

          {ocrResult && (
            <div className="mt-4 p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-1">
              {ocrResult.error || ocrResult.status === 'failed' ? (
                <p className="text-rose-600 font-medium">{ocrResult.error || ocrResult.message}</p>
              ) : (
                <>
                  <p className="font-semibold text-emerald-700">✓ Đã ghi nhận biên lai OCR!</p>
                  <p>
                    Số tiền: <strong>{Number(ocrResult.extracted?.amount || 0).toLocaleString('vi-VN')} VND</strong> • Đối
                    tác: <strong>{ocrResult.extracted?.merchant || 'Khác'}</strong>
                  </p>
                </>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Kênh 3 & 4: Cấu hình Email IMAP & Telegram Bot */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <form onSubmit={handleSaveImap} className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
                <Mail className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-slate-900 text-sm">3. Đồng bộ Email Biến động Số dư (IMAP)</h3>
                <p className="text-xs text-slate-500">Chỉ đọc (Read-only), mã hóa App Password bằng Fernet</p>
              </div>
            </div>
            <input
              type="checkbox"
              checked={imapEnabled}
              onChange={(e) => setImapEnabled(e.target.checked)}
              className="w-4 h-4 accent-indigo-600"
            />
          </div>

          <div className="space-y-3">
            <input
              type="email"
              placeholder="Địa chỉ Gmail nhận thông báo ngân hàng"
              value={imapEmail}
              onChange={(e) => setImapEmail(e.target.value)}
              className="w-full px-3.5 py-2 text-sm border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <input
              type="password"
              placeholder="Google App Password (16 ký tự)"
              value={imapPass}
              onChange={(e) => setImapPass(e.target.value)}
              className="w-full px-3.5 py-2 text-sm border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <button
            type="submit"
            disabled={busy === 'imap'}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-900 hover:bg-indigo-600 text-white text-xs font-semibold transition"
          >
            <Save className="w-3.5 h-3.5" />
            Lưu cấu hình Email IMAP
          </button>
        </form>

        <form onSubmit={handleSaveTelegram} className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center">
                <Send className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-slate-900 text-sm">4. Kết nối Bot Telegram Cá nhân</h3>
                <p className="text-xs text-slate-500">Nhận cảnh báo bất thường & gửi ảnh biên lai từ điện thoại</p>
              </div>
            </div>
            <input
              type="checkbox"
              checked={tgEnabled}
              onChange={(e) => setTgEnabled(e.target.checked)}
              className="w-4 h-4 accent-sky-600"
            />
          </div>

          <input
            type="text"
            placeholder="Telegram Chat ID của bạn (VD: 5123456789)"
            value={tgChatId}
            onChange={(e) => setTgChatId(e.target.value)}
            className="w-full px-3.5 py-2 text-sm border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-500"
          />

          <button
            type="submit"
            disabled={busy === 'tg'}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-900 hover:bg-sky-600 text-white text-xs font-semibold transition"
          >
            <Save className="w-3.5 h-3.5" />
            Lưu kết nối Telegram
          </button>
        </form>
      </div>
    </div>
  )
}
