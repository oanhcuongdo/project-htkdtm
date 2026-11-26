import React, { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { ArrowLeft, ArrowRight, CheckCircle2, Lock, Mail, Sparkles, User } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import BrandWordmark from '../components/brand/BrandWordmark'
import BoulderShape from '../components/brand/BoulderShape'
import BrokenLine from '../components/brand/BrokenLine'

export default function LoginPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const initialMode = searchParams.get('mode') === 'register' ? 'register' : 'login'

  const [mode, setMode] = useState(initialMode)
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const { login, register } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    const m = searchParams.get('mode')
    if (m === 'register' || m === 'login') {
      setMode(m)
      setError('')
    }
  }, [searchParams])

  const switchMode = (nextMode) => {
    setMode(nextMode)
    setError('')
    setSearchParams({ mode: nextMode })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      if (mode === 'login') {
        await login(email, password)
        navigate('/dashboard')
      } else {
        await register(fullName, email, password)
        // Tài khoản mới đi thẳng tới trung tâm chọn nguồn lấy dữ liệu ngân hàng
        navigate('/data-sources')
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Đã xảy ra lỗi. Vui lòng thử lại.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDemoLogin = async () => {
    setError('')
    setSubmitting(true)
    try {
      await login('demo@finance.local', 'Demo@123')
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Không thể đăng nhập tài khoản Demo.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen grid grid-cols-1 lg:grid-cols-12 bg-boulder-ehakivi">
      {/* Left 5 columns — Brand Estonia Deep Navy Split Panel */}
      <div className="lg:col-span-5 relative overflow-hidden bg-estonia-liivi text-white p-8 sm:p-12 flex flex-col justify-between">
        <BoulderShape
          variant="kupukivi"
          fill="#0030DE"
          opacity={0.55}
          className="w-[420px] h-auto absolute -bottom-24 -right-20 pointer-events-none select-none"
        />
        <BoulderShape
          variant="silmakivi"
          fill="#0062F5"
          opacity={0.25}
          className="w-64 h-auto absolute -top-16 -left-16 pointer-events-none select-none"
        />

        <div className="relative">
          <Link
            to="/"
            className="inline-flex items-center gap-2 text-xs font-semibold text-estonia-parnu hover:text-white transition-colors mb-10"
          >
            <ArrowLeft className="w-4 h-4" />
            Quay lại trang giới thiệu
          </Link>

          <div>
            <BrandWordmark dark subtitle="Nhóm 13 • Lớp 65HTTT" />
          </div>

          <h1 className="mt-10 font-display font-bold text-3xl sm:text-4xl leading-[1.15] tracking-[-0.025em]">
            Minh bạch từng giao dịch. Chủ động mọi kế hoạch tài chính.
          </h1>

          <div className="mt-5 mb-6">
            <BrokenLine color="#00C3FF" className="w-40 h-3" strokeWidth={3} />
          </div>

          <p className="text-sm text-estonia-parnu leading-relaxed max-w-md">
            Mỗi tài khoản sở hữu không gian dữ liệu riêng biệt: tự chọn kênh tải sao kê ngân hàng, theo dõi 3 Dashboard
            Apache Superset và hỏi đáp số liệu thật với Google Gemini AI.
          </p>
        </div>

        <div className="relative mt-10 pt-6 border-t border-white/15 space-y-3 text-xs text-estonia-parnu">
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-estonia-narva shrink-0" />
            <span>Tùy chọn kết nối linh hoạt: Excel/CSV/PDF, OCR, Email IMAP, Telegram</span>
          </div>
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-estonia-narva shrink-0" />
            <span>Phân loại giao dịch NLP tiếng Việt đạt 98.62% F1-Score</span>
          </div>
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-estonia-narva shrink-0" />
            <span>Trợ lý Gemini AI truy vấn trực tiếp PostgreSQL (Zero Hallucination)</span>
          </div>
        </div>
      </div>

      {/* Right 7 columns — Clean Nordic Auth Form */}
      <div className="lg:col-span-7 flex items-center justify-center p-6 sm:p-12 bg-boulder-ehakivi">
        <div className="w-full max-w-md">
          <div className="text-left mb-8">
            <p className="text-xs font-semibold uppercase tracking-widest text-estonia-blue mb-2">
              {mode === 'login' ? 'Chào mừng trở lại' : 'Bắt đầu trong 15 giây'}
            </p>
            <h2 className="font-display font-bold text-3xl tracking-tight text-boulder-mustkivi">
              {mode === 'login' ? 'Đăng nhập vào Portal' : 'Tạo tài khoản cá nhân'}
            </h2>
            <p className="mt-2 text-sm text-boulder-kabelikivi">
              {mode === 'login'
                ? 'Truy cập kho dữ liệu dòng tiền và trợ lý AI của riêng bạn.'
                : 'Tạo không gian cô lập theo tài khoản để tải lên sao kê ngân hàng của bạn.'}
            </p>
          </div>

          {/* Segmented Mode Switcher */}
          <div className="grid grid-cols-2 bg-boulder-pahkla p-1 rounded-full border border-boulder-hellamaa/70 mb-6">
            <button
              type="button"
              onClick={() => switchMode('login')}
              className={`py-2.5 text-sm font-semibold rounded-full transition-colors ${
                mode === 'login'
                  ? 'bg-estonia-blue text-white'
                  : 'text-boulder-majakivi hover:text-boulder-mustkivi'
              }`}
            >
              Đăng nhập
            </button>
            <button
              type="button"
              onClick={() => switchMode('register')}
              className={`py-2.5 text-sm font-semibold rounded-full transition-colors ${
                mode === 'register'
                  ? 'bg-estonia-blue text-white'
                  : 'text-boulder-majakivi hover:text-boulder-mustkivi'
              }`}
            >
              Tạo tài khoản
            </button>
          </div>

          {error && (
            <div className="mb-5 px-4 py-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === 'register' && (
              <div>
                <label className="block text-xs font-semibold text-boulder-mustkivi mb-1.5">Họ và tên</label>
                <div className="relative">
                  <User className="w-4 h-4 text-boulder-kabelikivi absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Nguyễn Văn A"
                    className="w-full pl-10 pr-4 py-3 text-sm border border-boulder-hellamaa rounded-xl bg-boulder-ehakivi focus:outline-none focus:border-estonia-blue focus:ring-2 focus:ring-estonia-parnu transition"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-boulder-mustkivi mb-1.5">Email</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-boulder-kabelikivi absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="tenban@email.com"
                  className="w-full pl-10 pr-4 py-3 text-sm border border-boulder-hellamaa rounded-xl bg-boulder-ehakivi focus:outline-none focus:border-estonia-blue focus:ring-2 focus:ring-estonia-parnu transition"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-boulder-mustkivi mb-1.5">Mật khẩu</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-boulder-kabelikivi absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  required
                  minLength={6}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Tối thiểu 6 ký tự"
                  className="w-full pl-10 pr-4 py-3 text-sm border border-boulder-hellamaa rounded-xl bg-boulder-ehakivi focus:outline-none focus:border-estonia-blue focus:ring-2 focus:ring-estonia-parnu transition"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full py-3.5 px-5 bg-estonia-blue hover:bg-estonia-paldiski disabled:opacity-60 text-white text-sm font-semibold rounded-full flex items-center justify-center gap-2 transition-colors mt-2"
            >
              {submitting ? 'Đang xử lý...' : mode === 'login' ? 'Đăng nhập vào hệ thống' : 'Đăng ký & Chọn nguồn dữ liệu'}
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Haapsalu Warm Sand Demo Callout */}
          <div className="mt-7 pt-6 border-t border-boulder-hellamaa/70">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-boulder-kabelikivi mb-2.5">
              Hoặc trải nghiệm nhanh không cần tạo tài khoản
            </p>
            <button
              type="button"
              onClick={handleDemoLogin}
              disabled={submitting}
              className="w-full py-3 px-4 bg-estonia-haapsalu hover:bg-[#F9E3A6] text-boulder-mustkivi border border-[#E5CFA0] text-xs font-semibold rounded-xl flex items-center justify-center gap-2 transition-colors disabled:opacity-60"
            >
              <Sparkles className="w-4 h-4 text-estonia-blue shrink-0" />
              Đăng nhập nhanh Tài khoản Demo (776 giao dịch mẫu + MB Bank thật)
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
