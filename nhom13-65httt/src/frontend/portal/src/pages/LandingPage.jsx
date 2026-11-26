import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Activity,
  ArrowRight,
  ArrowUpRight,
  BarChart3,
  Bot,
  CheckCircle2,
  Database,
  EyeOff,
  FileSpreadsheet,
  KeyRound,
  Layers,
  Lock,
  Mail,
  Menu,
  ScanLine,
  Send,
  ShieldCheck,
  Sparkles,
  Users,
  X,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import BrandWordmark from '../components/brand/BrandWordmark'
import BoulderShape from '../components/brand/BoulderShape'
import BrokenLine from '../components/brand/BrokenLine'

const METRICS = [
  {
    value: '98.62%',
    label: 'Độ chính xác NLP tiếng Việt',
    detail: 'Weighted F1-Score (89.88% trên từ lóng mới)',
  },
  {
    value: '8.77%',
    label: 'Sai số dự báo 30 ngày',
    detail: 'Mô hình SARIMAX (vượt chuẩn KPI < 15%)',
  },
  {
    value: '87.8 ms',
    label: 'Tốc độ tải BI Superset',
    detail: 'Trung bình trên 18 biểu đồ & 3 Dashboard',
  },
  {
    value: '100%',
    label: 'Dữ liệu thật Zero Hallucination',
    detail: 'Gemini Function Calling khóa chặt user_id',
  },
]

const DATA_SOURCES = [
  {
    num: '01',
    icon: FileSpreadsheet,
    title: 'Tải lên Sao kê Excel, CSV & PDF',
    desc: 'Hỗ trợ trực tiếp sổ phụ MB Bank (.xlsx), Vietcombank, Techcombank, MoMo. Tự động trích xuất tên đối tác, ngân hàng nhận và che ẩn số tài khoản (****6868).',
    badge: 'Đang hoạt động • 5 luật Data Quality',
  },
  {
    num: '02',
    icon: ScanLine,
    title: 'Quét Ảnh Hóa Đơn (OCR Tiếng Việt)',
    desc: 'Chụp hóa đơn siêu thị, quán ăn hay biên lai chuyển khoản — Tesseract OCR tiếng Việt tự động bóc tách tổng tiền, ngày giờ và phân loại danh mục bằng AI.',
    badge: 'Tesseract OCR • Tự động phân loại',
  },
  {
    num: '03',
    icon: Mail,
    title: 'Đồng bộ Email Biến động Số dư (IMAP)',
    desc: 'Chỉ đọc (Read-only) email thông báo biến động từ ngân hàng theo lịch tự động. Google App Password được mã hóa bằng Fernet (AES-128) trước khi lưu trữ.',
    badge: 'Không yêu cầu mật khẩu ngân hàng',
  },
  {
    num: '04',
    icon: Send,
    title: 'Ghi chép & Cảnh báo qua Telegram Bot',
    desc: 'Gửi nhanh giao dịch tiền mặt hoặc ảnh hóa đơn ngay trên điện thoại. Hệ thống tự động gửi báo cáo dòng tiền hàng tuần và cảnh báo chi tiêu bất thường.',
    badge: 'Tức thời • Báo cáo định kỳ',
  },
]

const GEMINI_DEMOS = [
  {
    id: 'top5',
    tabLabel: 'Top 5 nguồn tiền gửi đi tháng 10',
    question: 'Hãy giúp tôi kiểm tra xem trong tháng 10 vừa rồi 5 nguồn tiền gửi đi nhiều nhất trong tháng',
    tool: 'get_top_recipients(year=2026, month=10, limit=5)',
    summary:
      'Dựa trên sao kê thực tế tháng 10/2026 trong PostgreSQL, khoản chi lớn nhất thuộc về đối tác HA KIEU LIEN (6,053,200 đ), tiếp theo là THIEU QUANG GIA BAO (1,050,000 đ) và TRINH THI VAN (900,000 đ).',
    columns: ['Đối tác nhận tiền', 'Số TK', 'Ngân hàng', 'Lần', 'Tổng tiền'],
    rows: [
      ['HA KIEU LIEN', '****6868', 'MB', '1', '6,053,200 đ'],
      ['THIEU QUANG GIA BAO', '****4663', 'TECHCOMBANK', '1', '1,050,000 đ'],
      ['TRINH THI VAN', '****0374', 'MB', '2', '900,000 đ'],
      ['HKD QUAN PHO CO HAI', '****7025', 'VIETCOMBANK', '2', '150,000 đ'],
      ['VO VIET TRUNG', '****6710', 'VIETINBANK', '4', '150,000 đ'],
    ],
  },
  {
    id: 'budget',
    tabLabel: 'So sánh ngân sách danh mục',
    question: 'Thống kê chi tiêu từng danh mục so với hạn mức ngân sách tháng gần nhất',
    tool: 'get_spending_by_category(year=2026, month=10)',
    summary:
      'Nhóm Chuyển khoản & Cá nhân chiếm tỷ trọng cao nhất trong kỳ. Danh mục Ăn uống đang nằm trong ngưỡng an toàn (68.4% hạn mức), cần theo dõi sát nhóm Mua sắm cuối tháng.',
    columns: ['Danh mục', 'Số GD', 'Hạn mức tháng', 'Thực chi', 'Trạng thái'],
    rows: [
      ['Chuyển khoản / Cá nhân', '18', '8,000,000 đ', '8,303,200 đ', '+3.8%'],
      ['Ăn uống & Cà phê', '29', '3,500,000 đ', '2,394,000 đ', 'An toàn'],
      ['Di chuyển & Xăng xe', '11', '1,500,000 đ', '980,000 đ', 'An toàn'],
      ['Hóa đơn & Tiện ích', '6', '2,000,000 đ', '1,645,000 đ', 'An toàn'],
    ],
  },
  {
    id: 'anomaly',
    tabLabel: 'Giao dịch bất thường AI',
    question: 'Liệt kê các giao dịch bất thường do AI Isolation Forest + Z-Score đánh dấu',
    tool: 'get_anomalies(limit=5)',
    summary:
      'Mô hình kết hợp Isolation Forest và Z-Score (> 2.5σ theo từng danh mục) phát hiện các giao dịch có giá trị đột biến so với thói quen chi tiêu lịch sử của bạn để rà soát kịp thời.',
    columns: ['Ngày', 'Danh mục', 'Đối tác', 'Số tiền', 'Điểm AI'],
    rows: [
      ['2026-10-21', 'Chuyển khoản', 'HA KIEU LIEN', '-6,053,200 đ', '3.42σ'],
      ['2026-10-14', 'Mua sắm', 'DIEN MAY XANH', '-4,890,000 đ', '2.95σ'],
      ['2026-09-28', 'Du lịch', 'VIETNAM AIRLINES', '-3,650,000 đ', '2.71σ'],
    ],
  },
]

const PIPELINE_STEPS = [
  {
    step: '01',
    title: 'Thu thập đa kênh',
    desc: 'Tiếp nhận sao kê Excel/CSV/PDF, ảnh hóa đơn OCR, Email IMAP và Telegram vào vùng Staging.',
  },
  {
    step: '02',
    title: 'Làm sạch & Khử trùng',
    desc: 'Chuẩn hóa nội dung tiếng Việt, tách chuyển khoản nội bộ và khử trùng bằng Exact Ref + Jaro-Winkler (≥ 0.80).',
  },
  {
    step: '03',
    title: 'Phân loại & Dự báo AI',
    desc: 'Calibrated LinearSVC phân loại danh mục, Isolation Forest + Z-Score tìm bất thường và SARIMAX dự báo 30 ngày.',
  },
  {
    step: '04',
    title: 'BI Superset & Gemini AI',
    desc: 'Lưu kho Star Schema phục vụ trực tiếp 3 Dashboard Apache Superset và Trợ lý hỏi đáp Gemini.',
  },
]

const SUPERSET_DASHBOARDS = [
  {
    id: '01',
    title: '01. Tổng quan Dòng tiền (Cashflow Overview)',
    charts: '6 biểu đồ tương tác',
    desc: 'Theo dõi Tổng thu nhập, Tổng chi tiêu thực, Tỷ lệ tiết kiệm ròng theo tháng và dòng tiền tích lũy (đã tự động loại trừ giao dịch chuyển qua lại giữa các ví nội bộ).',
    highlights: ['KPI Big Number Thu – Chi – Tiết kiệm', 'Xu hướng dòng tiền 12 tháng', 'Tỷ lệ tiết kiệm ròng (%)'],
  },
  {
    id: '02',
    title: '02. Hành vi Chi tiêu (Spending Behavior)',
    charts: '6 biểu đồ phân tích sâu',
    desc: 'Giải mã thói quen chi tiêu vi mô qua bản đồ nhiệt (Heatmap) theo thứ trong tuần, biểu đồ Donut tỷ trọng danh mục và so sánh thực chi với ngân sách mục tiêu.',
    highlights: ['Heatmap chi tiêu theo ngày', 'Cơ cấu danh mục (Donut)', 'Cảnh báo vượt trần ngân sách'],
  },
  {
    id: '03',
    title: '03. Dự báo 30 ngày & Bất thường AI',
    charts: '6 biểu đồ AI Intelligence',
    desc: 'Hiển thị đường dự báo chi tiêu 30 ngày tới kèm khoảng tin cậy của SARIMAX, tốc độ đốt tiền hàng ngày (Burn-rate) và bảng kiểm toán giao dịch bất thường.',
    highlights: ['Dự báo SARIMAX 30 ngày', 'Dự phóng số dư cuối tháng', 'Bảng đối soát bất thường (>2.5σ)'],
  },
]

const SECURITY_PILLARS = [
  {
    icon: KeyRound,
    title: 'Xác thực JWT & Mật khẩu Bcrypt',
    desc: 'Mật khẩu được băm một chiều có salt ngẫu nhiên bằng bcrypt; mọi phiên làm việc xác thực bằng JWT HS256.',
  },
  {
    icon: Lock,
    title: 'Mã hóa Fernet (AES-128)',
    desc: 'App Password Email IMAP và cấu hình Telegram của từng người dùng được mã hóa đối xứng trước khi lưu xuống PostgreSQL.',
  },
  {
    icon: EyeOff,
    title: 'Che ẩn Số tài khoản & Không xâm phạm',
    desc: 'Không bao giờ yêu cầu mật khẩu Internet Banking. Số tài khoản đối tác tự động chuẩn hóa về dạng ****6868.',
  },
  {
    icon: Users,
    title: 'Cô lập dữ liệu tuyệt đối (user_id)',
    desc: 'Toàn bộ truy vấn KPI, lịch sử tải sao kê và 7 công cụ SQL của Gemini AI đều khóa chặt theo tài khoản đang đăng nhập.',
  },
]

export default function LandingPage() {
  const { token, login } = useAuth()
  const navigate = useNavigate()

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [activeDemoId, setActiveDemoId] = useState('top5')
  const [activeDashId, setActiveDashId] = useState('01')
  const [demoLoading, setDemoLoading] = useState(false)
  const [demoError, setDemoError] = useState('')

  const activeDemo = GEMINI_DEMOS.find((d) => d.id === activeDemoId) || GEMINI_DEMOS[0]
  const activeDash = SUPERSET_DASHBOARDS.find((d) => d.id === activeDashId) || SUPERSET_DASHBOARDS[0]

  const handleQuickDemo = async () => {
    setDemoError('')
    setDemoLoading(true)
    try {
      await login('demo@finance.local', 'Demo@123')
      navigate('/dashboard')
    } catch (err) {
      setDemoError('Không thể kết nối máy chủ Demo lúc này. Đang chuyển tới trang đăng nhập...')
      setTimeout(() => navigate('/login?mode=login'), 900)
    } finally {
      setDemoLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-boulder-ehakivi text-boulder-mustkivi">
      {/* =====================================================================
          SECTION 1: MINIMALIST STICKY NAVIGATION BAR
      ===================================================================== */}
      <header className="sticky top-0 z-50 bg-boulder-ehakivi/90 backdrop-blur-md border-b border-boulder-hellamaa">
        <div className="max-w-7xl mx-auto px-6 lg:px-10 h-20 flex items-center justify-between gap-4">
          <Link to="/" aria-label="personal.cfo Trang chủ">
            <BrandWordmark />
          </Link>

          {/* Desktop nav links */}
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-boulder-majakivi">
            <a href="#sources" className="hover:text-estonia-blue transition-colors">
              Kênh dữ liệu
            </a>
            <a href="#gemini-ai" className="hover:text-estonia-blue transition-colors">
              Trợ lý Gemini AI
            </a>
            <a href="#architecture" className="hover:text-estonia-blue transition-colors">
              Kiến trúc
            </a>
            <a href="#security" className="hover:text-estonia-blue transition-colors">
              BI & Bảo mật
            </a>
          </nav>

          {/* Desktop actions */}
          <div className="hidden md:flex items-center gap-3">
            {token ? (
              <Link
                to="/dashboard"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-estonia-blue hover:bg-estonia-paldiski text-white text-sm font-semibold transition-colors"
              >
                Vào Bảng điều khiển
                <ArrowRight className="w-4 h-4" />
              </Link>
            ) : (
              <>
                <Link
                  to="/login?mode=login"
                  className="px-4 py-2.5 text-sm font-semibold text-boulder-mustkivi hover:text-estonia-blue transition-colors"
                >
                  Đăng nhập
                </Link>
                <Link
                  to="/login?mode=register"
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-estonia-blue hover:bg-estonia-paldiski text-white text-sm font-semibold transition-colors"
                >
                  Tạo tài khoản
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </>
            )}
          </div>

          {/* Mobile menu button */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen((v) => !v)}
            className="md:hidden p-2 rounded-lg border border-boulder-hellamaa text-boulder-mustkivi"
            aria-label="Mở menu điều hướng"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>

        {/* Mobile dropdown */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-boulder-ehakivi border-t border-boulder-hellamaa px-6 py-5 space-y-4">
            <div className="flex flex-col space-y-3 text-sm font-medium text-boulder-majakivi">
              <a href="#sources" onClick={() => setMobileMenuOpen(false)} className="hover:text-estonia-blue">
                Kênh dữ liệu
              </a>
              <a href="#gemini-ai" onClick={() => setMobileMenuOpen(false)} className="hover:text-estonia-blue">
                Trợ lý Gemini AI
              </a>
              <a href="#architecture" onClick={() => setMobileMenuOpen(false)} className="hover:text-estonia-blue">
                Kiến trúc
              </a>
              <a href="#security" onClick={() => setMobileMenuOpen(false)} className="hover:text-estonia-blue">
                BI & Bảo mật
              </a>
            </div>
            <div className="pt-4 border-t border-boulder-hellamaa flex flex-col gap-2.5">
              {token ? (
                <Link
                  to="/dashboard"
                  className="w-full py-2.5 px-4 rounded-full bg-estonia-blue text-white text-sm font-semibold text-center"
                >
                  Vào Bảng điều khiển
                </Link>
              ) : (
                <>
                  <Link
                    to="/login?mode=login"
                    className="w-full py-2.5 px-4 rounded-full border border-boulder-mustkivi text-boulder-mustkivi text-sm font-semibold text-center"
                  >
                    Đăng nhập
                  </Link>
                  <Link
                    to="/login?mode=register"
                    className="w-full py-2.5 px-4 rounded-full bg-estonia-blue text-white text-sm font-semibold text-center"
                  >
                    Tạo tài khoản miễn phí
                  </Link>
                </>
              )}
            </div>
          </div>
        )}
      </header>

      {/* =====================================================================
          SECTION 2: EDITORIAL ASYMMETRIC HERO SECTION
      ===================================================================== */}
      <section className="relative overflow-hidden bg-boulder-ehakivi pt-14 pb-20 lg:pt-20 lg:pb-28">
        <div className="max-w-7xl mx-auto px-6 lg:px-10">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-10 items-center">
            {/* Left 7 columns — Editorial left-aligned hierarchy */}
            <div className="lg:col-span-7 text-left">
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-estonia-parnu text-estonia-blue text-xs font-semibold tracking-wider uppercase mb-6">
                <span className="w-2 h-2 rounded-full bg-estonia-blue" />
                Hệ thống Tài chính Cá nhân Thông minh • Nhóm 13 — 65HTTT
              </div>

              <h1 className="font-display font-bold text-4xl sm:text-5xl lg:text-[56px] leading-[1.08] tracking-[-0.03em] text-boulder-mustkivi">
                Nhìn rõ từng dòng tiền.
                <br />
                <span className="text-estonia-blue">Làm chủ mọi quyết định.</span>
              </h1>

              <div className="mt-5 mb-7">
                <BrokenLine color="#0030DE" className="w-52 h-3" strokeWidth={3} />
              </div>

              <p className="text-base sm:text-lg text-boulder-majakivi leading-relaxed max-w-xl">
                Chấm dứt tình trạng <strong className="text-boulder-mustkivi font-semibold">mù mờ dòng tiền vi mô</strong>.
                Tự động tổng hợp sao kê đa ngân hàng không xâm phạm, phân loại giao dịch bằng AI tiếng Việt, trực quan hóa
                Apache Superset và hỏi đáp trực tiếp trên dữ liệu thật qua <strong className="text-boulder-mustkivi font-semibold">Google Gemini AI</strong>.
              </p>

              {/* CTA Cluster */}
              <div className="mt-9 flex flex-wrap items-center gap-4">
                <Link
                  to={token ? '/dashboard' : '/login?mode=register'}
                  className="inline-flex items-center gap-2.5 px-7 py-3.5 rounded-full bg-estonia-blue hover:bg-estonia-paldiski text-white text-sm font-semibold transition-colors"
                >
                  {token ? 'Mở Bảng điều khiển' : 'Tạo tài khoản miễn phí'}
                  <ArrowRight className="w-4 h-4" />
                </Link>

                <button
                  type="button"
                  onClick={handleQuickDemo}
                  disabled={demoLoading}
                  className="inline-flex items-center gap-2.5 px-6 py-3.5 rounded-full bg-boulder-ehakivi hover:bg-boulder-mustkivi text-boulder-mustkivi hover:text-white border border-boulder-mustkivi text-sm font-semibold transition-colors disabled:opacity-60"
                >
                  <Sparkles className="w-4 h-4 text-estonia-blue group-hover:text-estonia-narva" />
                  {demoLoading ? 'Đang vào bản Demo...' : 'Trải nghiệm Demo (776 GD thật)'}
                </button>
              </div>

              {demoError && (
                <p className="mt-3 text-xs font-medium text-rose-600">{demoError}</p>
              )}

              <div className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-2 text-xs font-medium text-boulder-kabelikivi">
                <span className="inline-flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-estonia-blue" />
                  Không yêu cầu mật khẩu ngân hàng
                </span>
                <span className="inline-flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-estonia-blue" />
                  Cô lập dữ liệu từng tài khoản
                </span>
                <span className="inline-flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-estonia-blue" />
                  100% số liệu PostgreSQL thật
                </span>
              </div>
            </div>

            {/* Right 5 columns — Boulder-Framed Real Data Showcase */}
            <div className="lg:col-span-5 relative flex items-center justify-center py-4">
              {/* Primary organic Boulder backdrop (Kupukivi) */}
              <BoulderShape
                variant="kupukivi"
                fill="#CEE2FD"
                className="w-[108%] max-w-[460px] h-auto select-none pointer-events-none"
              />
              {/* Secondary deep blue Boulder accent */}
              <BoulderShape
                variant="silmakivi"
                fill="#0030DE"
                opacity={0.14}
                className="w-44 h-auto absolute -bottom-3 -right-2 select-none pointer-events-none"
              />

              {/* Floating Limestone Preview Card */}
              <div className="absolute inset-x-2 sm:inset-x-4 bg-boulder-ehakivi rounded-limestone-lg border border-boulder-hellamaa p-5 sm:p-6 shadow-[0_20px_50px_rgba(0,48,222,0.10)]">
                <div className="flex items-center justify-between gap-2 pb-3.5 border-b border-boulder-pahkla">
                  <div className="flex items-center gap-2.5">
                    <span className="w-8 h-8 rounded-xl bg-estonia-blue text-white flex items-center justify-center">
                      <Bot className="w-4 h-4" />
                    </span>
                    <div>
                      <p className="font-display font-bold text-xs text-boulder-mustkivi">
                        Trợ lý Gemini AI • Dữ liệu thật
                      </p>
                      <p className="font-mono text-[11px] text-estonia-blue">
                        get_top_recipients(2026, 10)
                      </p>
                    </div>
                  </div>
                  <span className="px-2.5 py-1 rounded-full bg-estonia-haapsalu text-boulder-mustkivi text-[10px] font-bold uppercase tracking-wide">
                    Live SQL
                  </span>
                </div>

                <p className="mt-3.5 text-xs text-boulder-majakivi bg-boulder-pahkla rounded-xl px-3.5 py-2.5">
                  “Kiểm tra giúp tôi Top 5 nguồn tiền gửi đi nhiều nhất tháng 10?”
                </p>

                <div className="mt-3.5 space-y-2">
                  {[
                    { name: 'HA KIEU LIEN', meta: '****6868 • MB', amt: '6,053,200 đ' },
                    { name: 'THIEU QUANG GIA BAO', meta: '****4663 • TCB', amt: '1,050,000 đ' },
                    { name: 'TRINH THI VAN', meta: '****0374 • MB', amt: '900,000 đ' },
                  ].map((item, idx) => (
                    <div
                      key={item.name}
                      className="flex items-center justify-between gap-3 px-3 py-2 rounded-xl border border-boulder-pahkla hover:border-estonia-parnu transition-colors"
                    >
                      <div className="min-w-0">
                        <p className="text-xs font-semibold text-boulder-mustkivi truncate">
                          <span className="text-estonia-blue font-mono mr-1.5">0{idx + 1}</span>
                          {item.name}
                        </p>
                        <p className="text-[11px] font-mono text-boulder-kabelikivi">{item.meta}</p>
                      </div>
                      <span className="text-xs font-bold text-boulder-mustkivi tabular-nums-vnd whitespace-nowrap">
                        {item.amt}
                      </span>
                    </div>
                  ))}
                </div>

                <div className="mt-4 pt-3 border-t border-boulder-pahkla flex items-center justify-between text-[11px]">
                  <span className="inline-flex items-center gap-1.5 text-emerald-700 font-semibold">
                    <span className="w-2 h-2 rounded-full bg-emerald-500" />
                    Zero Hallucination
                  </span>
                  <span className="text-boulder-kabelikivi font-mono">PostgreSQL Star Schema</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =====================================================================
          SECTION 3: TRUST & REAL METRICS STRIP (PAHKLA #F1F5F9)
      ===================================================================== */}
      <section className="bg-boulder-pahkla border-y border-boulder-hellamaa py-12 lg:py-16">
        <div className="max-w-7xl mx-auto px-6 lg:px-10">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-0 lg:divide-x lg:divide-boulder-hellamaa">
            {METRICS.map((m) => (
              <div key={m.label} className="lg:px-8 first:lg:pl-0 last:lg:pr-0 text-left">
                <div className="font-display font-bold text-4xl tracking-tight text-estonia-blue tabular-nums-vnd">
                  {m.value}
                </div>
                <div className="mt-2 font-display font-semibold text-sm text-boulder-mustkivi">{m.label}</div>
                <p className="mt-1 text-xs text-boulder-kabelikivi leading-relaxed">{m.detail}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* =====================================================================
          SECTION 4: 4 KÊNH TÙY CHỌN LẤY DỮ LIỆU NGÂN HÀNG (COLOR-FLIP CARDS)
      ===================================================================== */}
      <section id="sources" className="py-20 lg:py-28 bg-boulder-ehakivi">
        <div className="max-w-7xl mx-auto px-6 lg:px-10">
          <div className="max-w-2xl text-left mb-14">
            <p className="text-xs font-semibold uppercase tracking-widest text-estonia-blue mb-3">
              Thu thập dữ liệu không xâm phạm
            </p>
            <h2 className="font-display font-bold text-3xl sm:text-4xl leading-[1.15] tracking-[-0.025em] text-boulder-mustkivi">
              Tự chọn cách kết nối dữ liệu ngân hàng của riêng bạn.
            </h2>
            <p className="mt-4 text-base text-boulder-majakivi leading-relaxed">
              Dù bạn muốn tải lên file sao kê Excel hàng tháng, chụp hóa đơn siêu thị hay đồng bộ tự động qua Email
              biến động — toàn bộ dữ liệu đều đi qua bộ lọc làm sạch và khử trùng lặp chuẩn kho dữ liệu.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {DATA_SOURCES.map(({ num, icon: Icon, title, desc, badge }) => (
              <div
                key={num}
                className="group bg-boulder-ehakivi hover:bg-estonia-blue border border-boulder-hellamaa hover:border-estonia-blue rounded-limestone p-8 transition-colors duration-200 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <div className="w-12 h-12 rounded-2xl bg-estonia-parnu/70 group-hover:bg-white/15 text-estonia-blue group-hover:text-white flex items-center justify-center transition-colors duration-200">
                      <Icon className="w-6 h-6" strokeWidth={2} />
                    </div>
                    <span className="font-mono text-sm font-semibold text-boulder-kabelikivi group-hover:text-estonia-parnu transition-colors duration-200">
                      {num}
                    </span>
                  </div>

                  <h3 className="font-display font-semibold text-xl text-boulder-mustkivi group-hover:text-white transition-colors duration-200">
                    {title}
                  </h3>
                  <p className="mt-3 text-sm text-boulder-majakivi group-hover:text-estonia-parnu leading-relaxed transition-colors duration-200">
                    {desc}
                  </p>
                </div>

                <div className="mt-7 pt-4 border-t border-boulder-pahkla group-hover:border-white/20 flex items-center justify-between text-xs font-semibold transition-colors duration-200">
                  <span className="text-estonia-blue group-hover:text-estonia-narva">{badge}</span>
                  <ArrowUpRight className="w-4 h-4 text-boulder-kabelikivi group-hover:text-white group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform duration-200" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* =====================================================================
          SECTION 5: TÂM ĐIỂM — TRỢ LÝ GEMINI AI FUNCTION CALLING (LIIVI #000087)
      ===================================================================== */}
      <section id="gemini-ai" className="relative overflow-hidden bg-estonia-liivi text-white py-20 lg:py-28">
        {/* Subtle Boulder accent */}
        <BoulderShape
          variant="ukukivi"
          fill="#0030DE"
          opacity={0.35}
          className="w-[520px] h-auto absolute -top-24 -right-24 pointer-events-none select-none"
        />

        <div className="relative max-w-7xl mx-auto px-6 lg:px-10">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
            {/* Left 5 cols */}
            <div className="lg:col-span-5 text-left">
              <p className="text-xs font-semibold uppercase tracking-widest text-estonia-narva mb-3">
                Personal CFO • Google Gemini API
              </p>
              <h2 className="font-display font-bold text-3xl sm:text-4xl leading-[1.15] tracking-[-0.025em] text-white">
                Hỏi bằng tiếng Việt tự nhiên. Nhận số liệu chính xác từng đồng.
              </h2>

              <div className="mt-5 mb-6">
                <BrokenLine color="#00C3FF" className="w-44 h-3" strokeWidth={3} />
              </div>

              <p className="text-sm sm:text-base text-estonia-parnu leading-relaxed">
                Khác với chatbot thông thường dễ bịa số, trợ lý Gemini trong hệ thống sử dụng cơ chế{' '}
                <strong className="text-white">Function Calling</strong> kết nối trực tiếp 7 công cụ SQL Read-Only trên
                PostgreSQL Data Warehouse.
              </p>

              <ul className="mt-7 space-y-4 text-sm text-estonia-parnu">
                <li className="flex items-start gap-3">
                  <Database className="w-5 h-5 text-estonia-narva shrink-0 mt-0.5" strokeWidth={2} />
                  <span>
                    <strong className="text-white">7 công cụ SQL chuyên biệt:</strong> Top đối tác nhận/gửi tiền, dòng tiền
                    theo tháng, ngân sách danh mục, Burn-rate và giao dịch bất thường.
                  </span>
                </li>
                <li className="flex items-start gap-3">
                  <ShieldCheck className="w-5 h-5 text-estonia-narva shrink-0 mt-0.5" strokeWidth={2} />
                  <span>
                    <strong className="text-white">Khóa chặt theo tài khoản:</strong> Mọi lệnh truy vấn tự động gắn
                    <code className="mx-1 px-1.5 py-0.5 rounded bg-white/10 font-mono text-xs text-estonia-narva">
                      WHERE user_id = :uid
                    </code>
                    ở tầng Backend.
                  </span>
                </li>
                <li className="flex items-start gap-3">
                  <BarChart3 className="w-5 h-5 text-estonia-narva shrink-0 mt-0.5" strokeWidth={2} />
                  <span>
                    <strong className="text-white">Xuất kèm bảng đối chiếu thật:</strong> Mỗi câu trả lời đều hiển thị
                    tên công cụ đã gọi cùng bảng dữ liệu gốc để kiểm chứng.
                  </span>
                </li>
              </ul>

              <div className="mt-9">
                <Link
                  to={token ? '/chat' : '/login?mode=register'}
                  className="inline-flex items-center gap-2.5 px-6 py-3.5 rounded-full bg-boulder-ehakivi hover:bg-estonia-parnu text-estonia-blue text-sm font-semibold transition-colors"
                >
                  Hỏi thử trên dữ liệu của bạn
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </div>

            {/* Right 7 cols — Interactive 3-Prompt Live Preview */}
            <div className="lg:col-span-7">
              <div className="bg-boulder-ehakivi text-boulder-mustkivi rounded-limestone-lg border border-white/15 p-5 sm:p-7 shadow-2xl">
                <div className="flex items-center justify-between flex-wrap gap-2 pb-4 border-b border-boulder-pahkla">
                  <span className="text-xs font-semibold uppercase tracking-wider text-boulder-kabelikivi">
                    Chọn câu hỏi mẫu để xem cách AI truy xuất dữ liệu thật
                  </span>
                  <span className="font-mono text-[11px] px-2.5 py-1 rounded-full bg-estonia-parnu/60 text-estonia-blue font-semibold">
                    gemini-3.5-flash
                  </span>
                </div>

                {/* Prompt Tabs */}
                <div className="mt-4 flex flex-wrap gap-2">
                  {GEMINI_DEMOS.map((demo) => (
                    <button
                      key={demo.id}
                      type="button"
                      onClick={() => setActiveDemoId(demo.id)}
                      className={`px-3.5 py-2 rounded-full text-xs font-semibold transition-colors ${
                        activeDemoId === demo.id
                          ? 'bg-estonia-blue text-white'
                          : 'bg-boulder-pahkla text-boulder-majakivi hover:bg-estonia-parnu/70 hover:text-estonia-blue'
                      }`}
                    >
                      {demo.tabLabel}
                    </button>
                  ))}
                </div>

                {/* Simulated User Question */}
                <div className="mt-5 flex justify-end">
                  <div className="max-w-lg rounded-2xl rounded-tr-sm bg-estonia-blue text-white px-4 py-3 text-xs sm:text-sm leading-relaxed">
                    {activeDemo.question}
                  </div>
                </div>

                {/* Simulated AI Answer + Tool Badge + Real Table */}
                <div className="mt-4 rounded-2xl bg-boulder-pahkla/70 border border-boulder-hellamaa/80 p-4 sm:p-5">
                  <div className="flex flex-wrap items-center gap-2 mb-3">
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-boulder-ehakivi border border-boulder-hellamaa font-mono text-[11px] text-estonia-blue">
                      <Database className="w-3 h-3" />
                      {activeDemo.tool}
                    </span>
                    <span className="text-[11px] font-semibold text-emerald-700">✓ Đã đối chiếu PostgreSQL</span>
                  </div>

                  <p className="text-xs sm:text-sm text-boulder-majakivi leading-relaxed mb-4">
                    {activeDemo.summary}
                  </p>

                  <div className="rounded-xl border border-boulder-hellamaa bg-boulder-ehakivi overflow-hidden">
                    <div className="overflow-x-auto">
                      <table className="min-w-full text-xs">
                        <thead className="bg-boulder-pahkla text-boulder-majakivi">
                          <tr>
                            {activeDemo.columns.map((c) => (
                              <th key={c} className="px-3.5 py-2.5 text-left font-semibold whitespace-nowrap">
                                {c}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-boulder-pahkla">
                          {activeDemo.rows.map((row, rIdx) => (
                            <tr key={rIdx} className="hover:bg-estonia-parnu/25 transition-colors">
                              {row.map((cell, cIdx) => (
                                <td
                                  key={cIdx}
                                  className={`px-3.5 py-2.5 whitespace-nowrap ${
                                    cIdx === 0
                                      ? 'font-semibold text-boulder-mustkivi'
                                      : cIdx === row.length - 1
                                      ? 'font-semibold text-estonia-blue tabular-nums-vnd'
                                      : 'text-boulder-majakivi font-mono text-[11px]'
                                  }`}
                                >
                                  {cell}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =====================================================================
          SECTION 6: QUY TRÌNH DỮ LIỆU 4 BƯỚC NỐI BẰNG BROKEN LINE
      ===================================================================== */}
      <section id="architecture" className="py-20 lg:py-28 bg-boulder-ehakivi">
        <div className="max-w-7xl mx-auto px-6 lg:px-10">
          <div className="max-w-2xl text-left mb-14">
            <p className="text-xs font-semibold uppercase tracking-widest text-estonia-blue mb-3">
              Kiến trúc Data Warehouse 5 tầng
            </p>
            <h2 className="font-display font-bold text-3xl sm:text-4xl leading-[1.15] tracking-[-0.025em] text-boulder-mustkivi">
              Từ sao kê thô rời rạc đến quyết định tài chính sắc nét.
            </h2>
          </div>

          {/* Connecting Broken Line on Desktop */}
          <div className="hidden lg:block mb-6">
            <BrokenLine color="#0030DE" className="w-full h-3" strokeWidth={2.5} />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {PIPELINE_STEPS.map((item) => (
              <div
                key={item.step}
                className="bg-boulder-ehakivi rounded-limestone border border-boulder-hellamaa p-6 flex flex-col justify-between"
              >
                <div>
                  <span className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-estonia-parnu text-estonia-blue font-mono font-bold text-sm mb-5">
                    {item.step}
                  </span>
                  <h3 className="font-display font-semibold text-lg text-boulder-mustkivi">{item.title}</h3>
                  <p className="mt-2.5 text-sm text-boulder-majakivi leading-relaxed">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* =====================================================================
          SECTION 7: 3 DASHBOARD APACHE SUPERSET & 4 CAM KẾT BẢO MẬT
      ===================================================================== */}
      <section id="security" className="py-20 lg:py-28 bg-boulder-pahkla border-t border-boulder-hellamaa">
        <div className="max-w-7xl mx-auto px-6 lg:px-10">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
            {/* Left 6 cols — Apache Superset BI Dashboards */}
            <div className="lg:col-span-6 text-left">
              <p className="text-xs font-semibold uppercase tracking-widest text-estonia-blue mb-3">
                Trực quan hóa Apache Superset 6.1
              </p>
              <h2 className="font-display font-bold text-3xl leading-[1.15] tracking-[-0.025em] text-boulder-mustkivi">
                3 Dashboard BI nhúng trực tiếp vào Portal.
              </h2>
              <p className="mt-3 text-sm text-boulder-majakivi leading-relaxed">
                18 biểu đồ ECharts được dựng tự động trên 8 PostgreSQL Semantic Views, tải trung bình chỉ 87.8 ms.
              </p>

              <div className="mt-7 space-y-3">
                {SUPERSET_DASHBOARDS.map((dash) => {
                  const selected = dash.id === activeDashId
                  return (
                    <button
                      key={dash.id}
                      type="button"
                      onClick={() => setActiveDashId(dash.id)}
                      className={`w-full text-left p-5 rounded-limestone border transition-colors ${
                        selected
                          ? 'bg-estonia-blue text-white border-estonia-blue'
                          : 'bg-boulder-ehakivi text-boulder-mustkivi border-boulder-hellamaa hover:border-estonia-blue'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-display font-semibold text-base">{dash.title}</span>
                        <span
                          className={`text-[11px] font-mono px-2.5 py-0.5 rounded-full ${
                            selected ? 'bg-white/15 text-estonia-parnu' : 'bg-boulder-pahkla text-boulder-kabelikivi'
                          }`}
                        >
                          {dash.charts}
                        </span>
                      </div>
                      {selected && (
                        <div className="mt-3 space-y-3">
                          <p className="text-xs sm:text-sm text-estonia-parnu leading-relaxed">{dash.desc}</p>
                          <div className="flex flex-wrap gap-2">
                            {dash.highlights.map((h) => (
                              <span
                                key={h}
                                className="px-2.5 py-1 rounded-full bg-white/10 text-[11px] font-medium text-white"
                              >
                                {h}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Right 6 cols — Security Pillars */}
            <div className="lg:col-span-6 text-left">
              <p className="text-xs font-semibold uppercase tracking-widest text-estonia-blue mb-3">
                An toàn & Riêng tư đa người dùng
              </p>
              <h2 className="font-display font-bold text-3xl leading-[1.15] tracking-[-0.025em] text-boulder-mustkivi">
                Dữ liệu tài chính của bạn thuộc về riêng bạn.
              </h2>
              <p className="mt-3 text-sm text-boulder-majakivi leading-relaxed">
                Thiết kế theo kiến trúc bảo mật nhiều lớp: không lưu mật khẩu ngân hàng, mã hóa cấu hình nhạy cảm và
                cô lập tuyệt đối giữa các tài khoản.
              </p>

              <div className="mt-7 grid grid-cols-1 sm:grid-cols-2 gap-4">
                {SECURITY_PILLARS.map(({ icon: Icon, title, desc }) => (
                  <div
                    key={title}
                    className="bg-boulder-ehakivi rounded-limestone border border-boulder-hellamaa p-5"
                  >
                    <div className="w-10 h-10 rounded-xl bg-estonia-parnu/70 text-estonia-blue flex items-center justify-center mb-4">
                      <Icon className="w-5 h-5" strokeWidth={2} />
                    </div>
                    <h3 className="font-display font-semibold text-sm text-boulder-mustkivi">{title}</h3>
                    <p className="mt-2 text-xs text-boulder-majakivi leading-relaxed">{desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =====================================================================
          SECTION 8: BOULDER FINAL CTA BANNER & MINIMALIST FOOTER
      ===================================================================== */}
      <section className="py-20 bg-boulder-ehakivi">
        <div className="max-w-7xl mx-auto px-6 lg:px-10">
          <div className="relative overflow-hidden rounded-limestone-lg bg-estonia-blue text-white px-8 py-14 sm:px-14 sm:py-16">
            <BoulderShape
              variant="kupukivi"
              fill="#0062F5"
              opacity={0.75}
              className="w-80 sm:w-[420px] h-auto absolute -right-16 -bottom-24 pointer-events-none select-none"
            />
            <BoulderShape
              variant="silmakivi"
              fill="#000087"
              opacity={0.4}
              className="w-60 h-auto absolute -top-20 right-44 pointer-events-none select-none"
            />

            <div className="relative max-w-2xl text-left">
              <div className="mb-5">
                <BrokenLine color="#00C3FF" className="w-40 h-3" strokeWidth={3} />
              </div>
              <h2 className="font-display font-bold text-3xl sm:text-4xl leading-[1.15] tracking-[-0.025em]">
                Sẵn sàng nhìn rõ toàn bộ dòng tiền của bạn?
              </h2>
              <p className="mt-4 text-sm sm:text-base text-estonia-parnu leading-relaxed">
                Tạo tài khoản riêng trong 15 giây để tải sao kê ngân hàng của bạn, hoặc trải nghiệm ngay tài khoản Demo
                với 776 giao dịch thật & sao kê MB Bank chỉ với một cú nhấp chuột.
              </p>

              <div className="mt-8 flex flex-wrap items-center gap-4">
                <Link
                  to={token ? '/dashboard' : '/login?mode=register'}
                  className="inline-flex items-center gap-2.5 px-7 py-3.5 rounded-full bg-boulder-ehakivi hover:bg-estonia-parnu text-estonia-blue text-sm font-semibold transition-colors"
                >
                  {token ? 'Mở Bảng điều khiển' : 'Tạo tài khoản miễn phí'}
                  <ArrowRight className="w-4 h-4" />
                </Link>

                <button
                  type="button"
                  onClick={handleQuickDemo}
                  disabled={demoLoading}
                  className="inline-flex items-center gap-2.5 px-6 py-3.5 rounded-full border border-estonia-parnu/70 hover:bg-estonia-liivi text-white text-sm font-semibold transition-colors disabled:opacity-60"
                >
                  <Sparkles className="w-4 h-4 text-estonia-narva" />
                  {demoLoading ? 'Đang đăng nhập...' : 'Vào ngay tài khoản Demo'}
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      <footer className="bg-boulder-mustkivi text-boulder-hellamaa py-14">
        <div className="max-w-7xl mx-auto px-6 lg:px-10">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-10 pb-10 border-b border-white/10">
            <div className="md:col-span-6 text-left">
              <BrandWordmark dark subtitle="Hệ thống Quản lý Tài chính Cá nhân Thông minh" />
              <p className="mt-4 text-xs sm:text-sm text-boulder-kabelikivi max-w-md leading-relaxed">
                Đồ án học phần Hệ thống Kinh doanh Thông minh (HTKDTM) — Nhóm 13, Lớp 65HTTT. Thiết kế giao diện lấy cảm
                hứng từ phong cách tối giản Bắc Âu của Brand Estonia (DDS 2.0).
              </p>
            </div>

            <div className="md:col-span-3 text-left">
              <h4 className="font-display font-semibold text-xs uppercase tracking-wider text-white mb-4">
                Truy cập nhanh
              </h4>
              <ul className="space-y-2.5 text-sm text-boulder-kabelikivi">
                <li>
                  <Link to="/login?mode=register" className="hover:text-estonia-narva transition-colors">
                    Tạo tài khoản mới
                  </Link>
                </li>
                <li>
                  <Link to="/login?mode=login" className="hover:text-estonia-narva transition-colors">
                    Đăng nhập hệ thống
                  </Link>
                </li>
                <li>
                  <button
                    type="button"
                    onClick={handleQuickDemo}
                    className="hover:text-estonia-narva transition-colors"
                  >
                    Trải nghiệm tài khoản Demo
                  </button>
                </li>
              </ul>
            </div>

            <div className="md:col-span-3 text-left">
              <h4 className="font-display font-semibold text-xs uppercase tracking-wider text-white mb-4">
                Công nghệ lõi
              </h4>
              <ul className="space-y-2 text-xs font-mono text-boulder-kabelikivi">
                <li className="inline-flex items-center gap-2">
                  <Layers className="w-3.5 h-3.5 text-estonia-narva" />
                  React 18 • TailwindCSS • Nginx
                </li>
                <li className="flex items-center gap-2">
                  <Activity className="w-3.5 h-3.5 text-estonia-narva" />
                  FastAPI • PostgreSQL 16 Star Schema
                </li>
                <li className="flex items-center gap-2">
                  <BarChart3 className="w-3.5 h-3.5 text-estonia-narva" />
                  Apache Superset 6.1 • SARIMAX
                </li>
                <li className="flex items-center gap-2">
                  <Bot className="w-3.5 h-3.5 text-estonia-narva" />
                  Google Gemini AI Function Calling
                </li>
              </ul>
            </div>
          </div>

          <div className="pt-6 flex flex-wrap items-center justify-between gap-4 text-xs text-boulder-kabelikivi">
            <span>© 2026 personal.cfo — Nhóm 13, Lớp 65HTTT.</span>
            <span>Estonian Blue & Boulders Design Language</span>
          </div>
        </div>
      </footer>
    </div>
  )
}
