'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  Sparkles,
  BookOpen,
  GraduationCap,
  ArrowRight,
  CheckCircle2,
  BrainCircuit,
  Award,
  FileText,
  Zap,
  ChevronDown,
  Laptop,
  Menu,
  Check,
  X,
  Target,
  Bot,
  Volume2,
  Play,
  Pause,
  Search,
  RotateCcw,
  Upload,
  Cpu,
  TrendingUp,
  Eye,
  ShieldCheck,
  Layers,
  Video,
  Presentation,
  FileCheck2
} from 'lucide-react'
import { ThemeToggle } from '../components/ui/ThemeToggle'
import { Button } from '../components/ui/Button'
import { cn } from '../utils/cn'

// Morphing keywords for dynamic headline (no emoji inside bg-clip-text!)
const morphKeywords = [
  {
    text: 'Giáo Trình PDF',
    icon: FileText,
    gradient: 'from-pink-600 via-fuchsia-600 to-primary dark:from-pink-400 dark:via-fuchsia-300 dark:to-rose-300',
    badgeBg: 'bg-pink-500/12 text-pink-600 dark:text-pink-400 border-pink-500/25'
  },
  {
    text: 'Video Bài Giảng',
    icon: Video,
    gradient: 'from-violet-600 via-purple-600 to-fuchsia-600 dark:from-violet-400 dark:via-purple-300 dark:to-pink-300',
    badgeBg: 'bg-purple-500/12 text-purple-600 dark:text-purple-400 border-purple-500/25'
  },
  {
    text: 'Slide Thuyết Trình',
    icon: Presentation,
    gradient: 'from-amber-600 via-orange-500 to-amber-500 dark:from-amber-400 dark:via-orange-300 dark:to-amber-200',
    badgeBg: 'bg-amber-500/12 text-amber-600 dark:text-amber-400 border-amber-500/25'
  },
  {
    text: 'Đề Thi & Bài Tập',
    icon: FileCheck2,
    gradient: 'from-emerald-600 via-teal-600 to-green-600 dark:from-emerald-400 dark:via-teal-300 dark:to-green-300',
    badgeBg: 'bg-emerald-500/12 text-emerald-600 dark:text-emerald-400 border-emerald-500/25'
  }
]

// Quick sample prompts for "Try It Live" command bar
const samplePrompts = [
  {
    id: 'rag',
    label: 'Tóm tắt Lan truyền ngược',
    query: 'Giải thích cơ chế Lan truyền ngược (Backpropagation) trong mạng nơ-ron?',
    tab: 'rag' as const
  },
  {
    id: 'quiz',
    label: 'Sinh câu hỏi QuickSort',
    query: 'Sinh câu hỏi trắc nghiệm đánh giá thuật toán QuickSort',
    tab: 'quiz' as const
  },
  {
    id: 'audio',
    label: 'Nghe AI Podcast bài giảng',
    query: 'Chuyển bài giảng video buổi 5 thành podcast giọng đọc AI',
    tab: 'audio' as const
  },
  {
    id: 'radar',
    label: 'Chẩn đoán lỗ hổng CSDL',
    query: 'Phân tích điểm mạnh yếu học phần Hệ Thống Kinh Doanh Thông Minh',
    tab: 'radar' as const
  }
]

// Animated number counter component
function AnimatedCounter({
  end,
  duration = 1800,
  suffix = '',
  decimals = 0
}: {
  end: number
  duration?: number
  suffix?: string
  decimals?: number
}) {
  const [count, setCount] = useState(0)

  useEffect(() => {
    let startTimestamp: number | null = null
    let animationFrameId: number

    const step = (timestamp: number) => {
      if (!startTimestamp) startTimestamp = timestamp
      const progress = Math.min((timestamp - startTimestamp) / duration, 1)
      const ease = 1 - Math.pow(1 - progress, 3)
      setCount(ease * end)

      if (progress < 1) {
        animationFrameId = requestAnimationFrame(step)
      }
    }

    animationFrameId = requestAnimationFrame(step)
    return () => cancelAnimationFrame(animationFrameId)
  }, [end, duration])

  return (
    <span>
      {decimals > 0 ? count.toFixed(decimals) : Math.floor(count).toLocaleString()}
      {suffix}
    </span>
  )
}

export function LandingPage() {
  const router = useRouter()
  const [activeRole, setActiveRole] = useState<'student' | 'lecturer'>('student')
  const [openFaq, setOpenFaq] = useState<number | null>(0)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  // Morphing Headline & "Try It Live" States
  const [keywordIndex, setKeywordIndex] = useState(0)
  const [promptInput, setPromptInput] = useState('')
  const [activeScenario, setActiveScenario] = useState<'rag' | 'quiz' | 'audio' | 'radar'>('rag')
  const [quizAnswer, setQuizAnswer] = useState<number | null>(null)
  const [audioPlaying, setAudioPlaying] = useState(false)
  const [audioProgress, setAudioProgress] = useState(42)

  useEffect(() => {
    const timer = setInterval(() => {
      setKeywordIndex((prev) => (prev + 1) % morphKeywords.length)
    }, 3000)
    return () => clearInterval(timer)
  }, [])

  const currentKeyword = morphKeywords[keywordIndex]
  const KeywordIcon = currentKeyword.icon

  const handleSelectPrompt = (prompt: typeof samplePrompts[0]) => {
    setPromptInput(prompt.query)
    setActiveScenario(prompt.tab)
    if (prompt.tab === 'quiz') {
      setQuizAnswer(null)
    }
  }

  const scrollToSection = (id: string) => {
    setMobileMenuOpen(false)
    const el = document.getElementById(id)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' })
    }
  }

  const faqs = [
    {
      q: 'AI của Learning Hub có bịa đặt (hallucination) kiến thức không?',
      a: 'Không. Hệ thống áp dụng kiến trúc RAG Đa phương thức (Multimodal Retrieval-Augmented Generation) nghiêm ngặt. Mọi câu trả lời của Trợ lý AI đều được neo chặt vào tài liệu học phần do giảng viên hoặc sinh viên tải lên, kèm trích dẫn chính xác số trang sách PDF hoặc mốc thời gian video để người học kiểm chứng tức thì.'
    },
    {
      q: 'Bảng màu công thái học (Eye-Care Technology) giúp ích gì cho sinh viên?',
      a: 'Hệ thống tuân thủ chuẩn tương phản WCAG AAA, sử dụng tông Slate Paper (#F8FAFC) cho Light Mode và Midnight Slate (#0B1323) cho Dark Mode. Bảng màu này loại bỏ hiện tượng chói lóa ánh sáng xanh và triệt tiêu bóng ma quang học (Halation Effect), giúp mắt không phải điều tiết quá mức khi học bài liên tục 4–6 tiếng.'
    },
    {
      q: 'Giảng viên có thể ứng dụng Learning Hub như thế nào?',
      a: 'Giảng viên có thể tạo khóa học theo cấu trúc chương mục, tải lên video bài giảng, PDF giáo trình; Trợ lý AI sẽ tự động phác thảo đề tài, sinh ngân hàng câu hỏi trắc nghiệm và cung cấp bảng điều khiển phân tích chi tiết những câu hỏi sinh viên hay làm sai nhất.'
    },
    {
      q: 'Nền tảng hỗ trợ những định dạng học liệu nào?',
      a: 'Learning Hub hỗ trợ đa định dạng: Tài liệu văn bản (PDF, DOCX, TXT), hình ảnh biểu đồ tài liệu, video bài giảng MP4, audio podcast (chuyển ngữ âm thanh bằng Whisper) và các liên kết bài giảng trực tuyến.'
    },
    {
      q: 'Hệ thống có thể dùng được trên điện thoại và máy tính bảng không?',
      a: 'Hoàn toàn được. Toàn bộ giao diện được thiết kế Responsive 100%, có thanh điều hướng Mobile Drawer tiện lợi, giúp bạn vừa học trên laptop vừa ôn bài qua điện thoại bất cứ lúc nào.'
    }
  ]

  return (
    <div className="min-h-screen bg-background text-foreground font-body selection:bg-primary/20 selection:text-foreground">
      {/* 1. STICKY NAVBAR */}
      <header className="sticky top-0 z-50 w-full border-b border-border/70 bg-background/80 backdrop-blur-xl transition-colors">
        <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-2 sm:gap-4">
          {/* Brand Logo */}
          <div
            onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
            className="flex items-center gap-2 sm:gap-2.5 cursor-pointer group shrink-0"
          >
            <div className="flex h-8 w-8 sm:h-9 sm:w-9 items-center justify-center rounded-xl bg-gradient-to-br from-primary via-fuchsia-600 to-accent text-primary-foreground shadow-sm shadow-primary/25 group-hover:scale-105 transition-transform shrink-0">
              <Zap className="h-4 w-4 sm:h-5 sm:w-5 fill-current" />
            </div>
            <span className="text-base sm:text-xl font-black tracking-tight text-foreground whitespace-nowrap">
              Learning Hub
            </span>
          </div>

          {/* Desktop Nav Links */}
          <nav className="hidden lg:flex items-center gap-5 xl:gap-7 text-sm font-semibold text-foreground/75">
            <button onClick={() => scrollToSection('features')} className="hover:text-primary transition-colors cursor-pointer whitespace-nowrap">
              Tính năng
            </button>
            <button onClick={() => scrollToSection('live-studio')} className="hover:text-primary transition-colors cursor-pointer whitespace-nowrap">
              Studio
            </button>
            <button onClick={() => scrollToSection('how-it-works')} className="hover:text-primary transition-colors cursor-pointer whitespace-nowrap">
              Quy trình
            </button>
            <button onClick={() => scrollToSection('roles')} className="hover:text-primary transition-colors cursor-pointer whitespace-nowrap">
              Vai trò
            </button>
            <button onClick={() => scrollToSection('faq')} className="hover:text-primary transition-colors cursor-pointer whitespace-nowrap">
              Hỏi đáp
            </button>
          </nav>

          {/* Right Action Buttons */}
          <div className="flex items-center gap-1.5 sm:gap-3 shrink-0">
            <ThemeToggle />
            <button
              onClick={() => router.push('/login')}
              className="hidden sm:inline-flex text-sm font-bold text-foreground/80 hover:text-primary px-3 py-2 rounded-xl transition-colors cursor-pointer whitespace-nowrap"
            >
              Đăng nhập
            </button>
            <Button
              onClick={() => router.push('/welcome')}
              className="h-8 sm:h-9 px-2.5 sm:px-4 rounded-xl text-xs sm:text-sm font-semibold bg-primary text-primary-foreground shadow-sm hover:opacity-95 transition-all whitespace-nowrap shrink-0"
            >
              <span className="sm:hidden">Bắt đầu</span>
              <span className="hidden sm:inline">Trải nghiệm ngay</span>
              <ArrowRight className="h-3.5 w-3.5 ml-1 hidden sm:inline" />
            </Button>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 rounded-xl text-muted-foreground hover:bg-muted shrink-0"
              aria-label="Menu"
              aria-expanded={mobileMenuOpen}
            >
              <Menu className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Mobile Nav Drawer */}
        {mobileMenuOpen && (
          <div
            role="dialog"
            aria-label="Menu điều hướng"
            className="lg:hidden border-t border-border bg-surface-elevated px-4 pt-3 pb-5 space-y-2 animate-fade-in shadow-lift"
          >
            <button onClick={() => scrollToSection('features')} className="block w-full text-left py-2 text-sm font-semibold text-foreground">
              Tính năng
            </button>
            <button onClick={() => scrollToSection('live-studio')} className="block w-full text-left py-2 text-sm font-semibold text-foreground">
              Studio
            </button>
            <button onClick={() => scrollToSection('how-it-works')} className="block w-full text-left py-2 text-sm font-semibold text-foreground">
              Quy trình
            </button>
            <button onClick={() => scrollToSection('roles')} className="block w-full text-left py-2 text-sm font-semibold text-foreground">
              Vai trò
            </button>
            <button onClick={() => scrollToSection('faq')} className="block w-full text-left py-2 text-sm font-semibold text-foreground">
              Hỏi đáp
            </button>
            <div className="pt-2 border-t border-border/60 sm:hidden">
              <button
                onClick={() => {
                  setMobileMenuOpen(false)
                  router.push('/login')
                }}
                className="block w-full text-left py-2 text-sm font-bold text-primary"
              >
                Đăng nhập
              </button>
            </div>
          </div>
        )}
      </header>

      {/* 2. HERO SECTION - VISUAL-FIRST SPLIT SHOWCASE */}
      <section className="relative overflow-hidden pt-10 pb-16 sm:pt-16 sm:pb-24 lg:pt-20 lg:pb-28">
        {/* Subtle Background Grid & Ambient Glows */}
        <div className="absolute inset-0 bg-grid-pattern mask-radial-faded pointer-events-none opacity-45 dark:opacity-25" />
        <div className="absolute -top-24 left-1/4 w-[520px] h-[360px] bg-primary/15 rounded-full blur-[130px] pointer-events-none" />
        <div className="absolute top-1/3 -right-20 w-[440px] h-[360px] bg-accent/15 rounded-full blur-[130px] pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-12 items-center">
            {/* LEFT COLUMN: Crisp Editorial Copy & CTAs */}
            <div className="lg:col-span-6 space-y-6 text-center lg:text-left">
              {/* Pill Badge */}
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-surface-elevated/90 border border-primary/25 text-primary text-xs font-bold shadow-soft backdrop-blur-md">
                <Sparkles className="h-3.5 w-3.5 text-primary" />
                <span>Nền tảng Học tập Đa phương thức AI Thế Hệ Mới</span>
                <span className="flex h-1.5 w-1.5 rounded-full bg-primary animate-pulse" />
              </div>

              {/* Clean, High-Craft Headline (No emoji blobs, no overlapping underlines) */}
              <h1 className="text-3xl sm:text-5xl xl:text-[3.35rem] font-black tracking-tight text-foreground leading-[1.15]">
                <span className="block">Biến Mọi</span>
                <span className="mt-1.5 mb-1.5 inline-flex items-center gap-2.5 flex-wrap justify-center lg:justify-start">
                  <span
                    key={`icon-${keywordIndex}`}
                    className={cn(
                      'inline-flex h-10 w-10 sm:h-12 sm:w-12 items-center justify-center rounded-2xl border shadow-xs animate-fade-in shrink-0',
                      currentKeyword.badgeBg
                    )}
                  >
                    <KeywordIcon className="h-5 w-5 sm:h-6 sm:w-6" />
                  </span>
                  <span
                    key={`text-${keywordIndex}`}
                    className={cn(
                      'bg-gradient-to-r bg-clip-text text-transparent animate-fade-in pb-0.5',
                      currentKeyword.gradient
                    )}
                  >
                    {currentKeyword.text}
                  </span>
                </span>
                <span className="block">
                  Thành{' '}
                  <span className="bg-gradient-to-r from-primary via-fuchsia-600 to-accent dark:from-fuchsia-400 dark:via-pink-400 dark:to-rose-300 bg-clip-text text-transparent">
                    Tri Thức Tương Tác
                  </span>
                </span>
              </h1>

              {/* Subtitle */}
              <p className="text-base sm:text-lg text-muted-foreground max-w-xl mx-auto lg:mx-0 leading-relaxed">
                Đột phá hiệu suất học tập với Gia sư AI đối chiếu chính xác số trang tài liệu gốc, tự động sinh đề trắc nghiệm và bảng màu công thái học bảo vệ mắt suốt 6 giờ liên tục.
              </p>

              {/* CTA Group */}
              <div className="flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-3.5 pt-1">
                <Button
                  onClick={() => router.push('/welcome')}
                  className="h-12 px-7 rounded-2xl text-base font-bold bg-primary text-primary-foreground shadow-md shadow-primary/25 hover:shadow-glow hover:opacity-95 transition-all w-full sm:w-auto"
                >
                  <span>Bắt đầu học miễn phí</span>
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
                <Button
                  variant="outline"
                  onClick={() => scrollToSection('live-studio')}
                  className="h-12 px-6 rounded-2xl text-base font-semibold border-border bg-surface-elevated hover:bg-muted text-foreground w-full sm:w-auto"
                >
                  <Play className="h-4 w-4 mr-2 text-primary fill-primary/20" />
                  <span>Dùng thử AI Studio</span>
                </Button>
              </div>

              {/* Trust Highlights */}
              <div className="flex flex-wrap items-center justify-center lg:justify-start gap-x-6 gap-y-2.5 pt-2 text-xs font-semibold text-muted-foreground">
                <div className="flex items-center gap-1.5">
                  <CheckCircle2 className="h-4 w-4 text-success shrink-0" />
                  <span>Chuẩn thị giác WCAG AAA</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <CheckCircle2 className="h-4 w-4 text-success shrink-0" />
                  <span>RAG PDF, Video, DOCX</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <CheckCircle2 className="h-4 w-4 text-success shrink-0" />
                  <span>Zero-Hallucination</span>
                </div>
              </div>
            </div>

            {/* RIGHT COLUMN: High-Craft 3D Hero Illustration + Floating Telemetry Cards */}
            <div className="lg:col-span-6 relative">
              {/* Outer Ambient Halo */}
              <div className="absolute -inset-3 rounded-[2rem] bg-gradient-to-tr from-primary/25 via-accent/15 to-emerald-500/20 blur-2xl opacity-70 dark:opacity-50 pointer-events-none" />

              {/* Framed Hero Visual */}
              <div className="relative rounded-3xl overflow-hidden border border-border/80 dark:border-primary/30 bg-slate-950 shadow-2xl shadow-primary/15 group">
                <img
                  src="/images/landing/hero-workspace.jpg"
                  alt="Không gian học tập đa phương thức AI Learning Hub"
                  className="w-full h-auto aspect-[16/10] object-cover transition-transform duration-700 group-hover:scale-[1.03]"
                />
                {/* Subtle vignette gradient for legibility of overlaid glass badges */}
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950/75 via-transparent to-slate-950/20 pointer-events-none" />

                {/* Top-Left Live Status Pill */}
                <div className="absolute top-4 left-4 flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/75 border border-white/15 backdrop-blur-md text-white text-2xs font-bold shadow-lg">
                  <span className="flex h-2 w-2 rounded-full bg-emerald-400 animate-ping" />
                  <span>Multimodal RAG Engine · Live</span>
                </div>

                {/* Bottom Overlay Bar inside visual */}
                <div className="absolute bottom-4 inset-x-4 flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2.5 px-3.5 py-2 rounded-2xl bg-slate-900/80 border border-white/15 backdrop-blur-md text-white shadow-lg">
                    <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-emerald-500/20 text-emerald-400 shrink-0">
                      <Target className="h-4 w-4" />
                    </div>
                    <div className="text-left">
                      <p className="text-2xs font-extrabold leading-tight">Trích dẫn nguồn chính xác</p>
                      <p className="text-3xs text-emerald-300 font-semibold">Khớp 99.2% số trang PDF & Video</p>
                    </div>
                  </div>

                  <div className="hidden sm:flex items-center gap-2.5 px-3.5 py-2 rounded-2xl bg-slate-900/80 border border-white/15 backdrop-blur-md text-white shadow-lg">
                    <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-fuchsia-500/25 text-fuchsia-300 shrink-0">
                      <Eye className="h-4 w-4" />
                    </div>
                    <div className="text-left">
                      <p className="text-2xs font-extrabold leading-tight">Eye-Care WCAG AAA</p>
                      <p className="text-3xs text-fuchsia-300 font-semibold">Giảm 40% căng thẳng mắt</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 3. METRICS BAR */}
      <section className="border-y border-border/80 bg-surface/60 py-10 sm:py-14">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8">
            {[
              {
                value: <AnimatedCounter end={5} suffix="x" />,
                label: 'Tốc độ tiếp thu giáo trình',
                sub: 'Tóm tắt & bóc tách trọng tâm tức thì',
                color: 'text-primary',
                iconBg: 'bg-primary/10 text-primary',
                icon: Zap
              },
              {
                value: <AnimatedCounter end={99.2} decimals={1} suffix="%" />,
                label: 'Độ chính xác trích dẫn RAG',
                sub: 'Đối chiếu sách gốc, loại bỏ bịa đặt',
                color: 'text-accent',
                iconBg: 'bg-accent/10 text-accent',
                icon: ShieldCheck
              },
              {
                value: <AnimatedCounter end={10000} suffix="+" />,
                label: 'Quiz & Flashcard tự động',
                sub: 'Sinh trắc nghiệm 4 lựa chọn có giải thích',
                color: 'text-success',
                iconBg: 'bg-success/10 text-success',
                icon: Layers
              },
              {
                value: <AnimatedCounter end={40} suffix="%" />,
                label: 'Giảm mỏi mắt khi học lâu',
                sub: 'Chuẩn công thái học thị giác WCAG AAA',
                color: 'text-warning',
                iconBg: 'bg-warning/10 text-warning',
                icon: Eye
              }
            ].map((stat, i) => {
              const Icon = stat.icon
              return (
                <div
                  key={i}
                  className="flex flex-col items-center text-center p-4 rounded-2xl bg-surface-elevated/70 border border-border/60 shadow-2xs"
                >
                  <div className={cn('h-9 w-9 rounded-xl flex items-center justify-center mb-3', stat.iconBg)}>
                    <Icon className="h-4 w-4" />
                  </div>
                  <p className={cn('text-3xl sm:text-4xl font-black tabular-nums', stat.color)}>
                    {stat.value}
                  </p>
                  <p className="text-xs sm:text-sm font-bold text-foreground mt-1">{stat.label}</p>
                  <p className="text-3xs text-muted-foreground mt-0.5">{stat.sub}</p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* 4. VISUAL BENTO GRID FEATURES */}
      <section id="features" className="py-16 sm:py-24 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center space-y-3 mb-12 sm:mb-16">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-bold uppercase tracking-wider">
            <Sparkles className="h-3.5 w-3.5" /> Bộ công cụ cốt lõi
          </span>
          <h2 className="text-2xl sm:text-4xl font-black text-foreground tracking-tight">
            Hệ Sinh Thái AI Chuyên Sâu Cho Người Học Hiện Đại
          </h2>
          <p className="text-sm sm:text-base text-muted-foreground max-w-2xl mx-auto">
            Kết hợp mô hình ngôn ngữ lớn, tìm kiếm ngữ nghĩa vector đa phương thức và giao diện công thái học để biến mọi giờ tự học thành kết quả thực chất.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-6 gap-6">
          {/* Card 1: Flagship Multimodal RAG (4 cols) */}
          <div className="md:col-span-4 rounded-3xl border border-border/80 bg-surface-elevated overflow-hidden hover:border-primary/40 hover:shadow-lift transition-all group flex flex-col">
            <div className="relative h-56 sm:h-64 w-full overflow-hidden bg-slate-950">
              <img
                src="/images/landing/feature-rag.jpg"
                alt="Gia sư AI Đa phương thức Multimodal RAG"
                className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-slate-950/10 to-transparent" />
              <div className="absolute bottom-4 left-6 flex items-center gap-2">
                <span className="px-3 py-1 rounded-full bg-primary/90 text-white text-2xs font-bold backdrop-blur-md shadow-sm">
                  Kiến trúc lõi · Multimodal RAG
                </span>
                <span className="px-2.5 py-1 rounded-full bg-slate-900/75 text-emerald-300 border border-emerald-400/30 text-2xs font-bold backdrop-blur-md">
                  Zero-Hallucination
                </span>
              </div>
            </div>
            <div className="p-6 sm:p-8 space-y-4 flex-1 flex flex-col justify-between">
              <div className="space-y-2.5">
                <div className="flex items-center gap-2.5">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
                    <BrainCircuit className="h-5 w-5" />
                  </div>
                  <h3 className="text-xl font-extrabold text-foreground">
                    Gia sư AI Đa phương thức (Multimodal RAG)
                  </h3>
                </div>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Truyền phát câu trả lời trực tiếp (SSE Streaming) từ tài liệu thực tế của bạn. Bóc tách biểu đồ, văn bản trong PDF, Slide PowerPoint và video bài giảng, kèm trích dẫn số trang chính xác giúp bạn tự tin kiểm chứng từng ý.
                </p>
              </div>
              <div className="pt-2 flex flex-wrap gap-2 text-2xs font-semibold text-muted-foreground">
                <span className="px-3 py-1.5 rounded-xl bg-surface border border-border">PDF & DOCX Deep Parsing</span>
                <span className="px-3 py-1.5 rounded-xl bg-surface border border-border">Qdrant Vector Database</span>
                <span className="px-3 py-1.5 rounded-xl bg-surface border border-border">Trích dẫn số trang & Timestamp</span>
              </div>
            </div>
          </div>

          {/* Card 2: AI Quiz & Flashcards (2 cols) */}
          <div className="md:col-span-2 rounded-3xl border border-border/80 bg-surface-elevated overflow-hidden hover:border-accent/40 hover:shadow-lift transition-all group flex flex-col">
            <div className="relative h-56 sm:h-64 w-full overflow-hidden bg-slate-950">
              <img
                src="/images/landing/feature-quiz.jpg"
                alt="Sinh Trắc Nghiệm và Flashcard Tức Thì"
                className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-slate-950/75 via-transparent to-transparent" />
              <div className="absolute bottom-4 left-5">
                <span className="px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-400/30 text-2xs font-bold backdrop-blur-md">
                  5 giây / bộ đề
                </span>
              </div>
            </div>
            <div className="p-6 space-y-3 flex-1 flex flex-col justify-between">
              <div className="space-y-2">
                <h3 className="text-lg font-extrabold text-foreground">Sinh Trắc Nghiệm & Flashcard</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Biến 50 trang tài liệu ôn tập thành ngân hàng đề thi 4 lựa chọn có giải thích chi tiết và thẻ ghi nhớ lặp lại ngắt quãng.
                </p>
              </div>
              <span className="inline-flex items-center text-xs font-bold text-accent pt-1">
                Luyện phản xạ đề thi thực chiến <ArrowRight className="h-3.5 w-3.5 ml-1" />
              </span>
            </div>
          </div>

          {/* Card 3: Knowledge Gap Radar (2 cols) */}
          <div className="md:col-span-2 rounded-3xl border border-border/80 bg-surface-elevated overflow-hidden hover:border-warning/40 hover:shadow-lift transition-all group flex flex-col">
            <div className="relative h-48 w-full overflow-hidden bg-slate-950">
              <img
                src="/images/landing/feature-radar.jpg"
                alt="Chẩn Đoán Lỗ Hổng Kiến Thức AI Radar"
                className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-slate-950/75 via-transparent to-transparent" />
              <div className="absolute bottom-3 left-5">
                <span className="px-2.5 py-1 rounded-full bg-amber-500/20 text-amber-300 border border-amber-400/30 text-2xs font-bold backdrop-blur-md">
                  Adaptive Remediation
                </span>
              </div>
            </div>
            <div className="p-6 space-y-3 flex-1 flex flex-col justify-between">
              <div className="space-y-2">
                <h3 className="text-lg font-extrabold text-foreground">Chẩn Đoán Lỗ Hổng Kiến Thức</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Theo dõi câu làm sai, định vị chính xác chuyên đề còn yếu và tự động tạo bộ bài tập bù đắp tức thì.
                </p>
              </div>
              <span className="inline-flex items-center text-xs font-bold text-warning pt-1">
                Học trúng đích, không học vẹt <ArrowRight className="h-3.5 w-3.5 ml-1" />
              </span>
            </div>
          </div>

          {/* Card 4: Essay Grading with Visual Rubric Card (2 cols) */}
          <div className="md:col-span-2 rounded-3xl border border-border/80 bg-surface-elevated p-6 hover:border-success/40 hover:shadow-lift transition-all flex flex-col justify-between gap-5">
            {/* Visual Mini UI Preview */}
            <div className="rounded-2xl bg-surface border border-border/80 p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="h-8 w-8 rounded-lg bg-success/15 text-success flex items-center justify-center">
                    <FileText className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-foreground">Chấm tự luận Rubric AI</p>
                    <p className="text-3xs text-muted-foreground">Đối chiếu giáo trình gốc</p>
                  </div>
                </div>
                <span className="px-2.5 py-1 rounded-xl bg-success/15 text-success font-black text-sm">
                  9.2/10
                </span>
              </div>
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-3xs font-semibold">
                  <span className="text-muted-foreground">Luận điểm & Dẫn chứng</span>
                  <span className="text-success">Đạt 95%</span>
                </div>
                <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                  <div className="h-full w-[95%] rounded-full bg-success" />
                </div>
                <div className="flex items-center justify-between text-3xs font-semibold pt-1">
                  <span className="text-muted-foreground">Cấu trúc lập luận</span>
                  <span className="text-primary">Đạt 88%</span>
                </div>
                <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                  <div className="h-full w-[88%] rounded-full bg-primary" />
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <h3 className="text-lg font-extrabold text-foreground">Chấm Tự Luận Đối Chiếu Nguồn</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                AI chấm điểm bài luận theo tiêu chí rubric, đối chiếu giáo trình gốc và chỉ rõ luận điểm còn thiếu sót để bạn cải thiện ngay.
              </p>
            </div>
          </div>

          {/* Card 5: Eye-Care Ergonomics with Visual Theme Swatch Preview (2 cols) */}
          <div className="md:col-span-2 rounded-3xl border border-border/80 bg-surface-elevated p-6 hover:border-primary/40 hover:shadow-lift transition-all flex flex-col justify-between gap-5">
            {/* Visual Light vs Dark Ergonomic Swatch */}
            <div className="rounded-2xl bg-surface border border-border/80 p-4 space-y-3">
              <div className="flex items-center justify-between text-2xs font-bold">
                <span className="flex items-center gap-1.5 text-foreground">
                  <Laptop className="h-3.5 w-3.5 text-primary" /> Bảng màu 60-30-10
                </span>
                <span className="px-2 py-0.5 rounded-full bg-primary/15 text-primary text-3xs">
                  WCAG AAA 14:1
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2.5">
                <div className="rounded-xl p-3 bg-[#F8FAFC] border border-slate-200 text-[#1A2536] space-y-1 shadow-2xs">
                  <div className="flex items-center gap-1.5">
                    <span className="h-2.5 w-2.5 rounded-full bg-[#A21CAF]" />
                    <span className="text-3xs font-extrabold">Slate Paper</span>
                  </div>
                  <p className="text-3xs text-slate-500">Ban ngày dịu mắt</p>
                </div>
                <div className="rounded-xl p-3 bg-[#0B1323] border border-slate-700 text-[#F8FAFC] space-y-1 shadow-2xs">
                  <div className="flex items-center gap-1.5">
                    <span className="h-2.5 w-2.5 rounded-full bg-[#EC4899]" />
                    <span className="text-3xs font-extrabold">Midnight</span>
                  </div>
                  <p className="text-3xs text-slate-400">Học đêm chống chói</p>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <h3 className="text-lg font-extrabold text-foreground">Công Thái Học Chống Mỏi Mắt</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Thiết kế theo quy tắc 60-30-10 với Slate Paper và Midnight Navy, triệt tiêu ánh sáng xanh gay gắt giúp tập trung bền bỉ suốt 6 giờ.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 5. INTERACTIVE "TRY IT LIVE" AI STUDIO SECTION */}
      <section id="live-studio" className="py-16 sm:py-24 bg-surface/60 border-y border-border/80 relative overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[640px] h-[260px] bg-primary/10 blur-[120px] pointer-events-none" />

        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 space-y-8">
          <div className="text-center space-y-3">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-bold uppercase tracking-wider">
              <Zap className="h-3.5 w-3.5" /> Tương tác trực tiếp
            </span>
            <h2 className="text-2xl sm:text-4xl font-black text-foreground tracking-tight">
              Trải Nghiệm AI Studio Ngay Trên Trình Duyệt
            </h2>
            <p className="text-sm sm:text-base text-muted-foreground max-w-2xl mx-auto">
              Chọn một kịch bản mẫu hoặc gõ câu hỏi bất kỳ để xem cách Learning Hub trích dẫn giáo trình, sinh đề trắc nghiệm, phát AI Podcast và chẩn đoán lỗ hổng kiến thức.
            </p>
          </div>

          {/* Prompt Command Bar */}
          <div className="max-w-3xl mx-auto w-full">
            <div className="p-2 rounded-2xl bg-surface-elevated border border-primary/30 shadow-lift transition-all focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/20">
              <div className="flex items-center gap-2 px-3 py-1.5">
                <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-primary/15 text-primary shrink-0">
                  <Search className="h-4 w-4" />
                </div>
                <input
                  type="text"
                  value={promptInput}
                  onChange={(e) => setPromptInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && promptInput) {
                      setActiveScenario('rag')
                    }
                  }}
                  placeholder="Gõ câu hỏi bất kỳ từ giáo trình hoặc chọn thử kịch bản bên dưới..."
                  className="w-full bg-transparent text-xs sm:text-sm text-foreground placeholder:text-muted-foreground/70 focus:outline-none"
                />
                <Button
                  onClick={() => {
                    if (!promptInput) setPromptInput('Giải thích cơ chế Lan truyền ngược trong mạng nơ-ron?')
                    setActiveScenario('rag')
                  }}
                  className="h-9 px-4 rounded-xl text-xs font-bold bg-primary text-primary-foreground shrink-0 shadow-xs hover:opacity-90 transition"
                >
                  <span>Chạy AI</span>
                  <ArrowRight className="h-3.5 w-3.5 ml-1" />
                </Button>
              </div>

              {/* Quick Sample Prompts */}
              <div className="pt-2 px-1 border-t border-border/50 flex items-center gap-1.5 overflow-x-auto text-2xs scrollbar-thin">
                <span className="text-muted-foreground font-semibold shrink-0 flex items-center gap-1 pl-1">
                  <Zap className="h-3 w-3 text-amber-500 fill-current" /> Thử nhanh:
                </span>
                {samplePrompts.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => handleSelectPrompt(p)}
                    className={cn(
                      'px-2.5 py-1 rounded-lg border text-left shrink-0 font-medium transition-all cursor-pointer',
                      activeScenario === p.tab && promptInput === p.query
                        ? 'bg-primary/15 border-primary text-primary font-bold shadow-2xs'
                        : 'bg-surface hover:bg-muted border-border/60 text-muted-foreground hover:text-foreground'
                    )}
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Interactive Mac Studio Window */}
          <div className="rounded-3xl border border-primary/20 bg-surface-elevated p-3 sm:p-5 shadow-2xl shadow-primary/10 relative overflow-hidden">
            <div className="absolute -top-px left-1/4 right-1/4 h-px bg-gradient-to-r from-transparent via-primary/60 to-transparent" />

            {/* Window Header */}
            <div className="flex flex-wrap items-center justify-between gap-3 px-3 py-2.5 border-b border-border/70 mb-4 bg-muted/30 rounded-xl">
              <div className="flex items-center gap-2">
                <div className="h-3 w-3 rounded-full bg-[#ff5f56]" />
                <div className="h-3 w-3 rounded-full bg-[#ffbd2e]" />
                <div className="h-3 w-3 rounded-full bg-[#27c93f]" />
                <span className="ml-2 text-2xs font-bold text-muted-foreground hidden xl:inline">
                  Learning Hub AI Studio · Hệ Thống Kinh Doanh Thông Minh (IS334)
                </span>
              </div>

              {/* Studio Tabs */}
              <div className="flex items-center p-1 rounded-xl bg-surface border border-border/60 gap-1 text-2xs font-bold overflow-x-auto">
                {[
                  { id: 'rag' as const, label: '1. Trích dẫn RAG' },
                  { id: 'quiz' as const, label: '2. Trắc nghiệm AI' },
                  { id: 'audio' as const, label: '3. AI Podcast' },
                  { id: 'radar' as const, label: '4. Radar lỗ hổng' }
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveScenario(tab.id)}
                    className={cn(
                      'px-3 py-1.5 rounded-lg transition-all cursor-pointer whitespace-nowrap',
                      activeScenario === tab.id
                        ? 'bg-primary text-primary-foreground shadow-xs font-bold'
                        : 'text-muted-foreground hover:text-foreground'
                    )}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              <div className="hidden sm:flex items-center gap-2">
                <span className="flex h-2 w-2 rounded-full bg-success animate-ping" />
                <span className="text-3xs font-extrabold text-success">LIVE RAG v2.4</span>
              </div>
            </div>

            {/* Split Screen Canvas */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 text-left">
              {/* LEFT PANEL: Live Document Viewer */}
              <div className="lg:col-span-5 rounded-2xl bg-surface/90 border border-border/80 p-4 space-y-3 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between pb-2 border-b border-border/60 text-2xs">
                    <span className="font-bold text-foreground flex items-center gap-1.5 truncate">
                      <FileText className="h-3.5 w-3.5 text-primary shrink-0" />
                      GiaoTrinh_KhaiPhaDuLieu.pdf
                    </span>
                    <span className="px-2 py-0.5 rounded-full bg-muted font-bold text-3xs text-muted-foreground shrink-0">
                      Trang 42 / 186
                    </span>
                  </div>

                  <div className="pt-3 space-y-2.5 text-2xs text-muted-foreground leading-relaxed">
                    <p className="font-extrabold text-xs text-foreground">
                      3.2 Kỹ thuật phân lớp cây quyết định & Mạng nơ-ron
                    </p>
                    <p>
                      Các giải thuật phổ biến bao gồm ID3, C4.5, CART và Multilayer Perceptron. Mục tiêu là phân tách tập dữ liệu thành các tập con thuần nhất dựa trên các thước đo entropy hoặc hàm mất mát.
                    </p>
                    <div className="p-3 rounded-xl bg-amber-500/10 border-l-4 border-amber-500 text-foreground space-y-1">
                      <div className="flex items-center justify-between text-3xs font-bold text-amber-600 dark:text-amber-400">
                        <span className="flex items-center gap-1">
                          <Sparkles className="h-3 w-3" /> Đoạn được AI trích dẫn
                        </span>
                        <span>Khớp 99.4%</span>
                      </div>
                      <p className="text-2xs font-semibold text-foreground/95 italic">
                        &ldquo;Thuật toán Backpropagation kết hợp Gradient Descent để giảm thiểu hàm tổn thất (Loss Function) qua từng epoch huấn luyện mô hình mạng nơ-ron sâu...&rdquo;
                      </p>
                    </div>
                    <p className="text-3xs text-muted-foreground/80 font-mono">
                      w_new = w_old - η * (∂L/∂w) (Chain Rule)
                    </p>
                  </div>
                </div>

                <div className="pt-2 border-t border-border/50 flex items-center justify-between text-3xs font-semibold text-muted-foreground">
                  <span className="flex items-center gap-1.5 text-primary font-bold">
                    <CheckCircle2 className="h-3.5 w-3.5 text-success" /> 1,420 Chunks Vector
                  </span>
                  <span>BAAI/bge-m3</span>
                </div>
              </div>

              {/* RIGHT PANEL: Dynamic AI Output */}
              <div className="lg:col-span-7 rounded-2xl bg-surface/90 border border-primary/20 p-4 flex flex-col justify-between">
                {activeScenario === 'rag' && (
                  <div className="space-y-3 animate-fade-in">
                    <div className="flex items-start gap-2.5 justify-end">
                      <div className="p-3 rounded-2xl bg-primary text-primary-foreground text-xs font-medium max-w-md shadow-xs">
                        {promptInput || 'Giải thích cơ chế Lan truyền ngược (Backpropagation) trong mạng nơ-ron?'}
                      </div>
                      <div className="flex h-7 w-7 rounded-full bg-muted items-center justify-center font-bold text-2xs shrink-0">
                        Bạn
                      </div>
                    </div>

                    <div className="p-4 rounded-2xl border border-primary/20 bg-surface-elevated space-y-2.5">
                      <div className="flex items-start gap-3">
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-accent text-primary-foreground shadow-xs">
                          <Bot className="h-4 w-4" />
                        </div>
                        <div className="space-y-2 flex-1">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <span className="text-xs font-bold text-foreground">Gia sư AI Tutor</span>
                            <span className="inline-flex items-center gap-1 text-3xs font-bold px-2 py-0.5 rounded-full bg-success/15 text-success">
                              <CheckCircle2 className="h-3 w-3" /> Đã kiểm chứng tài liệu gốc
                            </span>
                          </div>
                          <p className="text-xs text-foreground/90 leading-relaxed">
                            Thuật toán Lan truyền ngược (Backpropagation) tính đạo hàm riêng của hàm mất mát theo từng trọng số nhờ quy tắc chuỗi (Chain Rule), sau đó lan truyền sai số từ tầng ra ngược về các tầng ẩn để tối ưu trọng số qua Gradient Descent.
                          </p>
                          <div className="pt-1 flex flex-wrap items-center gap-2 text-3xs font-semibold">
                            <span className="px-2.5 py-1 rounded-lg bg-pink-500/10 text-pink-600 dark:text-pink-300 border border-pink-500/20">
                              Trang 42 · GiaoTrinh_KhaiPhaDuLieu.pdf
                            </span>
                            <span className="px-2.5 py-1 rounded-lg bg-purple-500/10 text-purple-600 dark:text-purple-300 border border-purple-500/20">
                              Mốc video: 14:25 · BaiGiang_Buoi5.mp4
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between pt-1 text-3xs text-muted-foreground">
                      <span>Gợi ý tiếp theo: &ldquo;Công thức toán học của Chain Rule?&rdquo;</span>
                      <button
                        onClick={() => setPromptInput('Công thức toán học của Chain Rule trong Backprop?')}
                        className="text-primary font-bold hover:underline cursor-pointer"
                      >
                        Hỏi ngay →
                      </button>
                    </div>
                  </div>
                )}

                {activeScenario === 'quiz' && (
                  <div className="space-y-3.5 animate-fade-in">
                    <div className="flex items-center justify-between pb-2 border-b border-border/50">
                      <span className="text-xs font-bold text-foreground flex items-center gap-1.5">
                        <Sparkles className="h-3.5 w-3.5 text-accent" />
                        Câu hỏi AI sinh tức thì từ giáo trình
                      </span>
                      <span className="text-3xs font-semibold text-muted-foreground">Bấm chọn thử</span>
                    </div>
                    <p className="text-sm font-bold text-foreground">
                      Độ phức tạp thời gian trung bình (Average Time Complexity) của giải thuật QuickSort là gì?
                    </p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-xs">
                      {[
                        { id: 0, text: 'A. O(N²)', correct: false },
                        { id: 1, text: 'B. O(N log N)', correct: true },
                        { id: 2, text: 'C. O(N)', correct: false },
                        { id: 3, text: 'D. O(log N)', correct: false }
                      ].map((opt) => (
                        <button
                          key={opt.id}
                          onClick={() => setQuizAnswer(opt.id)}
                          className={cn(
                            'p-3 rounded-xl border text-left font-medium transition-all cursor-pointer flex items-center justify-between',
                            quizAnswer === null && 'bg-surface-elevated hover:bg-muted border-border text-foreground',
                            quizAnswer === opt.id && opt.correct && 'bg-success/15 border-success text-success font-bold',
                            quizAnswer === opt.id && !opt.correct && 'bg-destructive/15 border-destructive text-destructive font-bold',
                            quizAnswer !== null && quizAnswer !== opt.id && opt.correct && 'bg-success/10 border-success/30 text-success',
                            quizAnswer !== null && quizAnswer !== opt.id && !opt.correct && 'bg-surface border-border opacity-50'
                          )}
                        >
                          <span>{opt.text}</span>
                          {quizAnswer === opt.id && (opt.correct ? <Check className="h-4 w-4 text-success" /> : <X className="h-4 w-4 text-destructive" />)}
                        </button>
                      ))}
                    </div>
                    {quizAnswer !== null ? (
                      <div className="p-3 rounded-xl bg-surface-elevated border border-border text-2xs">
                        {quizAnswer === 1 ? (
                          <span className="text-success font-bold">Chính xác! QuickSort có thời gian trung bình O(N log N).</span>
                        ) : (
                          <span className="text-amber-600 dark:text-amber-400 font-bold">Chưa chính xác. Đáp án đúng là B: O(N log N). Hãy xem lại slide phân tích thuật toán!</span>
                        )}
                      </div>
                    ) : (
                      <p className="text-3xs text-muted-foreground italic">
                        * AI tự động phân tích đáp án sai và gợi ý tài liệu ôn tập bù đắp kiến thức.
                      </p>
                    )}
                  </div>
                )}

                {activeScenario === 'audio' && (
                  <div className="space-y-4 animate-fade-in">
                    <div className="flex items-center justify-between pb-2 border-b border-border/50">
                      <span className="text-xs font-bold text-foreground flex items-center gap-1.5">
                        <Volume2 className="h-4 w-4 text-primary" />
                        AI Podcast & Giọng đọc tóm tắt bài giảng
                      </span>
                      <span className="text-3xs font-bold text-primary">Tốc độ: 1.25x</span>
                    </div>

                    <div className="p-4 rounded-2xl bg-surface-elevated border border-primary/20 space-y-3.5">
                      <div className="flex items-center justify-between gap-4">
                        <div>
                          <p className="text-sm font-bold text-foreground">
                            Tóm tắt bài học: Mạng Nơ-ron & Lan truyền ngược
                          </p>
                          <p className="text-3xs text-muted-foreground">Giọng đọc AI Studio · Nguồn: BaiGiang_Buoi5.mp4</p>
                        </div>
                        <div className="flex items-center gap-1 h-6 shrink-0">
                          <span className={cn('w-1 rounded-full bg-primary', audioPlaying ? 'animate-soundwave-1' : 'h-2')} />
                          <span className={cn('w-1 rounded-full bg-accent', audioPlaying ? 'animate-soundwave-2' : 'h-3')} />
                          <span className={cn('w-1 rounded-full bg-primary', audioPlaying ? 'animate-soundwave-3' : 'h-4')} />
                          <span className={cn('w-1 rounded-full bg-fuchsia-400', audioPlaying ? 'animate-soundwave-4' : 'h-2')} />
                        </div>
                      </div>

                      <div className="space-y-1">
                        <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
                          <div className="h-full bg-gradient-to-r from-primary to-accent rounded-full" style={{ width: `${audioProgress}%` }} />
                        </div>
                        <div className="flex justify-between text-3xs font-semibold text-muted-foreground">
                          <span>01:14</span>
                          <span>02:58</span>
                        </div>
                      </div>

                      <div className="flex items-center justify-between pt-1">
                        <button
                          onClick={() => setAudioProgress(10)}
                          className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted cursor-pointer transition"
                          title="Tua lại"
                        >
                          <RotateCcw className="h-3.5 w-3.5" />
                        </button>
                        <button
                          onClick={() => setAudioPlaying(!audioPlaying)}
                          className="h-9 px-5 rounded-xl bg-primary text-primary-foreground font-bold text-xs flex items-center gap-1.5 shadow-sm hover:opacity-90 transition cursor-pointer"
                        >
                          {audioPlaying ? <Pause className="h-3.5 w-3.5 fill-current" /> : <Play className="h-3.5 w-3.5 fill-current" />}
                          <span>{audioPlaying ? 'Tạm dừng' : 'Nghe ngay'}</span>
                        </button>
                        <span className="text-3xs font-bold text-success bg-success/15 px-2.5 py-1 rounded-full">
                          Whisper STT
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                {activeScenario === 'radar' && (
                  <div className="space-y-3.5 animate-fade-in">
                    <div className="flex items-center justify-between pb-2 border-b border-border/50">
                      <span className="text-xs font-bold text-foreground flex items-center gap-1.5">
                        <Award className="h-4 w-4 text-warning" />
                        Chẩn đoán mức độ nắm bắt kiến thức
                      </span>
                      <span className="text-3xs font-bold text-success">Đã hoàn thành 85%</span>
                    </div>
                    <div className="space-y-3 text-xs">
                      <div>
                        <div className="flex justify-between text-2xs font-semibold mb-1.5">
                          <span className="text-foreground">Chuẩn hóa CSDL (3NF, BCNF)</span>
                          <span className="text-success font-bold">95% (Vững chắc)</span>
                        </div>
                        <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
                          <div className="h-full bg-success rounded-full" style={{ width: '95%' }} />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between text-2xs font-semibold mb-1.5">
                          <span className="text-foreground">Kiến trúc Big Data & MapReduce</span>
                          <span className="text-amber-500 font-bold">58% (Cần ôn tập thêm)</span>
                        </div>
                        <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
                          <div className="h-full bg-amber-500 rounded-full" style={{ width: '58%' }} />
                        </div>
                      </div>
                    </div>
                    <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/25 text-2xs text-foreground/90 flex flex-wrap items-center justify-between gap-2">
                      <span>AI đã tạo bộ 5 câu ôn bù đắp cho phần MapReduce</span>
                      <button
                        onClick={() => router.push('/app/student/quiz')}
                        className="px-3 py-1.5 rounded-lg bg-amber-500 text-white font-bold hover:bg-amber-600 transition cursor-pointer"
                      >
                        Làm ngay →
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 6. HOW IT WORKS (3 STEPS) */}
      <section id="how-it-works" className="py-16 sm:py-24 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center space-y-3 mb-12 sm:mb-16">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-bold uppercase tracking-wider">
            Đơn giản & Tối ưu
          </span>
          <h2 className="text-2xl sm:text-4xl font-black text-foreground tracking-tight">
            3 Bước Bứt Phá Điểm Số Cùng Learning Hub
          </h2>
          <p className="text-sm sm:text-base text-muted-foreground max-w-xl mx-auto">
            Không cần cấu hình phức tạp, bắt đầu học tập thông minh chỉ sau vài giây.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8 relative">
          {/* Connecting Line on Desktop */}
          <div className="hidden md:block absolute top-14 left-[18%] right-[18%] h-0.5 bg-gradient-to-r from-primary/40 via-accent/40 to-success/40 pointer-events-none" />

          {[
            {
              step: '01',
              title: 'Nạp Tài Liệu Học Phần',
              desc: 'Kéo thả giáo trình PDF, slide bài giảng PPTX, file Word hoặc video ghi hình buổi học lên kho lưu trữ cá nhân.',
              icon: Upload,
              badgeClass: 'bg-primary text-primary-foreground shadow-primary/25'
            },
            {
              step: '02',
              title: 'AI Phân Tách & Lập Chỉ Mục',
              desc: 'Celery Worker phân tích văn bản, trích xuất thực thể, tạo nhúng vector và xây dựng mạng lưới tri thức học thuật.',
              icon: Cpu,
              badgeClass: 'bg-accent text-accent-foreground shadow-accent/25'
            },
            {
              step: '03',
              title: 'Tương Tác & Bứt Phá',
              desc: 'Hỏi đáp cùng Gia sư AI, luyện đề trắc nghiệm phản xạ, lấp lỗ hổng kiến thức và tự tin chinh phục điểm A+.',
              icon: TrendingUp,
              badgeClass: 'bg-success text-success-foreground shadow-success/25'
            }
          ].map((item) => {
            const StepIcon = item.icon
            return (
              <div
                key={item.step}
                className="rounded-3xl border border-border/80 bg-surface-elevated p-6 sm:p-8 space-y-5 relative z-10 shadow-soft hover:-translate-y-1 hover:shadow-lift transition-all"
              >
                <div className="flex items-center justify-between">
                  <div className={cn('flex h-12 w-12 items-center justify-center rounded-2xl shadow-md', item.badgeClass)}>
                    <StepIcon className="h-5 w-5" />
                  </div>
                  <span className="text-3xl font-black text-muted-foreground/20 tabular-nums">
                    {item.step}
                  </span>
                </div>
                <div className="space-y-2">
                  <h3 className="text-lg font-extrabold text-foreground">{item.title}</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">{item.desc}</p>
                </div>
              </div>
            )
          })}
        </div>
      </section>

      {/* 7. DUAL PERSONA SHOWCASE WITH EDITORIAL PHOTOGRAPHY */}
      <section id="roles" className="py-16 sm:py-24 bg-surface/60 border-y border-border/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center space-y-3 mb-10">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-bold uppercase tracking-wider">
              Giải pháp toàn diện
            </span>
            <h2 className="text-2xl sm:text-4xl font-black text-foreground tracking-tight">
              Thiết Kế Chuyên Biệt Cho Người Học & Người Dạy
            </h2>
            <p className="text-sm sm:text-base text-muted-foreground max-w-xl mx-auto">
              Chọn vai trò để khám phá không gian làm việc thông minh dành riêng cho bạn.
            </p>
          </div>

          {/* Tab Switcher */}
          <div className="flex justify-center mb-10">
            <div className="p-1.5 rounded-2xl bg-surface-elevated border border-border flex items-center gap-1.5 shadow-soft">
              <button
                onClick={() => setActiveRole('student')}
                className={cn(
                  'flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold transition-all cursor-pointer',
                  activeRole === 'student'
                    ? 'bg-primary text-primary-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                )}
              >
                <GraduationCap className="h-4 w-4" />
                <span>Dành cho Sinh viên</span>
              </button>
              <button
                onClick={() => setActiveRole('lecturer')}
                className={cn(
                  'flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold transition-all cursor-pointer',
                  activeRole === 'lecturer'
                    ? 'bg-primary text-primary-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                )}
              >
                <BookOpen className="h-4 w-4" />
                <span>Dành cho Giảng viên</span>
              </button>
            </div>
          </div>

          {/* Tab Content Card */}
          <div className="rounded-3xl border border-border/80 bg-surface-elevated p-6 sm:p-10 shadow-lift overflow-hidden">
            {activeRole === 'student' ? (
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-10 items-center animate-fade-in">
                <div className="lg:col-span-6 space-y-5">
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-pink-500/10 text-pink-600 dark:text-pink-400 text-xs font-bold">
                    <span>Trải nghiệm Học tập Chủ động</span>
                  </div>
                  <h3 className="text-2xl sm:text-3xl font-black text-foreground leading-tight">
                    Tự học cá nhân hóa, bứt phá kỳ thi không lo quá tải
                  </h3>
                  <ul className="space-y-3.5 text-sm text-foreground/85">
                    <li className="flex items-start gap-2.5">
                      <CheckCircle2 className="h-5 w-5 text-success shrink-0 mt-0.5" />
                      <span>Hỏi đáp mọi thắc mắc 24/7 với Gia sư AI bám sát giáo trình, kèm số trang trích dẫn.</span>
                    </li>
                    <li className="flex items-start gap-2.5">
                      <CheckCircle2 className="h-5 w-5 text-success shrink-0 mt-0.5" />
                      <span>Ôn tập thông minh với thẻ Flashcard lặp lại ngắt quãng (Spaced Repetition).</span>
                    </li>
                    <li className="flex items-start gap-2.5">
                      <CheckCircle2 className="h-5 w-5 text-success shrink-0 mt-0.5" />
                      <span>Theo dõi chuỗi học tập (Streak) và mục tiêu ngày để duy trì động lực bền bỉ.</span>
                    </li>
                  </ul>
                  <div className="pt-2">
                    <Button
                      onClick={() => router.push('/register?role=student')}
                      className="h-12 px-6 rounded-2xl font-bold bg-primary text-primary-foreground shadow-sm hover:opacity-95 transition-all"
                    >
                      <span>Vào Không gian Học viên</span>
                      <ArrowRight className="h-4 w-4 ml-2" />
                    </Button>
                  </div>
                </div>

                {/* Editorial Photo + Floating Glass Progress Card */}
                <div className="lg:col-span-6 relative">
                  <div className="relative rounded-2xl overflow-hidden border border-border/80 shadow-xl">
                    <img
                      src="/images/landing/persona-student.jpg"
                      alt="Sinh viên tự học thông minh cùng Learning Hub AI"
                      className="w-full h-auto aspect-[4/3] object-cover"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-slate-950/75 via-transparent to-transparent pointer-events-none" />

                    {/* Overlaid Live Progress Glass Widget */}
                    <div className="absolute bottom-4 inset-x-4 p-4 rounded-2xl bg-slate-900/80 border border-white/15 backdrop-blur-md text-white space-y-2.5 shadow-xl">
                      <div className="flex items-center justify-between text-xs font-bold">
                        <span>Mục tiêu học tập hôm nay</span>
                        <span className="text-emerald-400">Hoàn thành 75%</span>
                      </div>
                      <div className="h-1.5 w-full bg-white/15 rounded-full overflow-hidden">
                        <div className="h-full w-3/4 bg-gradient-to-r from-fuchsia-400 to-emerald-400 rounded-full" />
                      </div>
                      <div className="flex flex-wrap items-center justify-between gap-2 text-3xs text-slate-200 pt-0.5">
                        <span>Ôn trắc nghiệm Chương 2: Big Data</span>
                        <span className="px-2 py-0.5 rounded-full bg-emerald-500/25 text-emerald-300 font-bold">Đã xong</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-10 items-center animate-fade-in">
                <div className="lg:col-span-6 space-y-5">
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/10 text-purple-600 dark:text-purple-400 text-xs font-bold">
                    <span>Quản lý & Giảng dạy Thông minh</span>
                  </div>
                  <h3 className="text-2xl sm:text-3xl font-black text-foreground leading-tight">
                    Số hóa bài giảng, tự động hóa chấm bài & đánh giá năng lực
                  </h3>
                  <ul className="space-y-3.5 text-sm text-foreground/85">
                    <li className="flex items-start gap-2.5">
                      <CheckCircle2 className="h-5 w-5 text-success shrink-0 mt-0.5" />
                      <span>Xuất bản khóa học bài bản theo chương mục kèm học liệu video, slide và PDF.</span>
                    </li>
                    <li className="flex items-start gap-2.5">
                      <CheckCircle2 className="h-5 w-5 text-success shrink-0 mt-0.5" />
                      <span>Trợ lý AI phác thảo đề thi, bài tập và tóm tắt nội dung bài giảng nhanh chóng.</span>
                    </li>
                    <li className="flex items-start gap-2.5">
                      <CheckCircle2 className="h-5 w-5 text-success shrink-0 mt-0.5" />
                      <span>Biểu đồ Analytics trực quan chỉ ra chủ đề sinh viên hay làm sai nhất để giảng bù kịp thời.</span>
                    </li>
                  </ul>
                  <div className="pt-2">
                    <Button
                      onClick={() => router.push('/register?role=lecturer')}
                      className="h-12 px-6 rounded-2xl font-bold bg-primary text-primary-foreground shadow-sm hover:opacity-95 transition-all"
                    >
                      <span>Vào Không gian Giảng viên</span>
                      <ArrowRight className="h-4 w-4 ml-2" />
                    </Button>
                  </div>
                </div>

                {/* Editorial Photo + Floating Glass Analytics Card */}
                <div className="lg:col-span-6 relative">
                  <div className="relative rounded-2xl overflow-hidden border border-border/80 shadow-xl">
                    <img
                      src="/images/landing/persona-lecturer.jpg"
                      alt="Giảng viên quản lý lớp học và phân tích học tập với Learning Hub AI"
                      className="w-full h-auto aspect-[4/3] object-cover"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-slate-950/75 via-transparent to-transparent pointer-events-none" />

                    {/* Overlaid Live Analytics Glass Widget */}
                    <div className="absolute bottom-4 inset-x-4 p-4 rounded-2xl bg-slate-900/80 border border-white/15 backdrop-blur-md text-white space-y-2.5 shadow-xl">
                      <div className="flex items-center justify-between text-xs font-bold">
                        <span>Báo cáo tiến độ lớp học phần</span>
                        <span className="text-fuchsia-300">85 học viên</span>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-3xs">
                        <div className="p-2 rounded-xl bg-white/10 flex items-center justify-between">
                          <span className="text-slate-200">Hoàn thành GK</span>
                          <span className="font-extrabold text-emerald-400">92%</span>
                        </div>
                        <div className="p-2 rounded-xl bg-white/10 flex items-center justify-between">
                          <span className="text-slate-200">Cần giảng bù</span>
                          <span className="font-extrabold text-amber-300">3NF</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* 8. COMPARISON TABLE */}
      <section id="comparison" className="py-16 sm:py-24 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center space-y-3 mb-12 sm:mb-16">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-bold uppercase tracking-wider">
            Sự khác biệt
          </span>
          <h2 className="text-2xl sm:text-4xl font-black text-foreground tracking-tight">
            Học Tập Truyền Thống vs Learning Hub AI
          </h2>
          <p className="text-sm sm:text-base text-muted-foreground">
            So sánh hiệu quả học tập khi áp dụng nền tảng đào tạo AI đa phương thức.
          </p>
        </div>

        <div className="overflow-x-auto rounded-3xl border border-border/80 bg-surface-elevated shadow-lift">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="border-b border-border/80 bg-muted/40">
                <th className="p-4 sm:p-5 font-bold text-foreground">Tiêu chí học tập</th>
                <th className="p-4 sm:p-5 font-bold text-muted-foreground">Học truyền thống</th>
                <th className="p-4 sm:p-5 font-extrabold text-primary bg-primary/5">
                  <span className="inline-flex items-center gap-1.5">
                    <Sparkles className="h-4 w-4" /> Learning Hub AI
                  </span>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60">
              {[
                {
                  criteria: 'Tra cứu giáo trình',
                  old: 'Lật tìm thủ công từng trang sách mất thời gian',
                  modern: 'AI trích dẫn số trang chính xác sau 2 giây'
                },
                {
                  criteria: 'Ôn thi trắc nghiệm',
                  old: 'Tìm đề cũ trôi nổi, dễ lệch đề cương môn học',
                  modern: 'Sinh đề bám sát slide giáo trình của trường'
                },
                {
                  criteria: 'Phát hiện điểm yếu',
                  old: 'Chỉ biết lỗ hổng khi đã nhận điểm thi thấp',
                  modern: 'Thuật toán chẩn đoán và bù đắp tức thì'
                },
                {
                  criteria: 'Căng thẳng thị giác',
                  old: 'Mỏi mắt, chói lóa sau 1–2 giờ đọc tài liệu',
                  modern: 'Chuẩn WCAG AAA bảo vệ mắt suốt 6 giờ'
                }
              ].map((row, idx) => (
                <tr key={idx} className="hover:bg-surface/40 transition-colors">
                  <td className="p-4 sm:p-5 font-bold text-foreground">{row.criteria}</td>
                  <td className="p-4 sm:p-5 text-muted-foreground">
                    <span className="inline-flex items-start gap-2">
                      <X className="h-4 w-4 text-muted-foreground/60 shrink-0 mt-0.5" />
                      <span>{row.old}</span>
                    </span>
                  </td>
                  <td className="p-4 sm:p-5 font-bold text-foreground bg-primary/[0.03]">
                    <span className="inline-flex items-start gap-2">
                      <CheckCircle2 className="h-4 w-4 text-success shrink-0 mt-0.5" />
                      <span>{row.modern}</span>
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* 9. FAQ SECTION */}
      <section id="faq" className="py-16 sm:py-24 bg-surface/50 border-t border-border/80">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center space-y-3 mb-12 sm:mb-14">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-bold uppercase tracking-wider">
              Giải đáp
            </span>
            <h2 className="text-2xl sm:text-4xl font-black text-foreground tracking-tight">
              Câu Hỏi Thường Gặp
            </h2>
            <p className="text-sm sm:text-base text-muted-foreground">
              Mọi điều bạn cần biết về nền tảng Multimodal AI Learning Hub.
            </p>
          </div>

          <div className="space-y-3.5">
            {faqs.map((faq, idx) => (
              <div
                key={idx}
                className="rounded-2xl border border-border/80 bg-surface-elevated overflow-hidden transition-all shadow-2xs"
              >
                <button
                  onClick={() => setOpenFaq(openFaq === idx ? null : idx)}
                  aria-expanded={openFaq === idx}
                  className="w-full flex items-center justify-between p-4 sm:p-5 text-left font-bold text-foreground hover:text-primary transition-colors gap-4 cursor-pointer"
                >
                  <span className="text-sm sm:text-base">{faq.q}</span>
                  <ChevronDown
                    className={cn(
                      'h-4 w-4 shrink-0 transition-transform duration-200 text-muted-foreground',
                      openFaq === idx && 'rotate-180 text-primary'
                    )}
                  />
                </button>
                {openFaq === idx && (
                  <div className="px-4 pb-5 sm:px-5 sm:pb-6 text-xs sm:text-sm text-muted-foreground leading-relaxed border-t border-border/40 pt-3 animate-fade-in">
                    {faq.a}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 10. FINAL CTA BANNER WITH AMBIENT VISUAL BACKDROP */}
      <section className="py-16 sm:py-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="rounded-3xl border border-primary/30 bg-slate-950 p-8 sm:p-16 text-center space-y-6 shadow-2xl shadow-primary/15 relative overflow-hidden">
          {/* Blended Background Visual */}
          <img
            src="/images/landing/hero-workspace.jpg"
            alt=""
            aria-hidden="true"
            className="absolute inset-0 w-full h-full object-cover opacity-25 mix-blend-luminosity pointer-events-none"
          />
          <div className="absolute inset-0 bg-gradient-to-br from-fuchsia-950/90 via-slate-950/85 to-pink-950/90 pointer-events-none" />

          <div className="relative z-10 max-w-2xl mx-auto space-y-4">
            <span className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full bg-white/10 border border-white/15 text-fuchsia-200 text-xs font-bold backdrop-blur-md">
              <Sparkles className="h-3.5 w-3.5" /> Sẵn sàng bứt phá học kỳ này
            </span>
            <h2 className="text-2xl sm:text-4xl font-black text-white tracking-tight leading-tight">
              Sẵn Sàng Nâng Tầm Năng Lực Học Tập Cùng AI?
            </h2>
            <p className="text-sm sm:text-base text-slate-300 leading-relaxed">
              Gia nhập cùng hàng trăm sinh viên và giảng viên đang sử dụng Learning Hub để giải phóng thời gian và đạt kết quả học tập vượt trội.
            </p>
          </div>
          <div className="relative z-10 flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
            <Button
              onClick={() => router.push('/welcome')}
              className="h-12 px-8 rounded-2xl text-base font-bold bg-primary text-primary-foreground shadow-lg shadow-primary/30 hover:opacity-95 transition-all w-full sm:w-auto"
            >
              <span>Bắt đầu trải nghiệm miễn phí ngay</span>
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </div>
        </div>
      </section>

      {/* 11. FOOTER */}
      <footer className="border-t border-border/80 bg-surface/70 py-12 text-sm text-muted-foreground">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-6 text-center md:text-left">
          <div className="space-y-1">
            <div className="flex items-center justify-center md:justify-start gap-2">
              <div className="h-7 w-7 rounded-lg bg-primary text-primary-foreground flex items-center justify-center font-bold text-xs">
                <Zap className="h-3.5 w-3.5 fill-current" />
              </div>
              <span className="font-extrabold text-foreground text-base">Learning Hub</span>
            </div>
            <p className="text-xs">Multimodal AI Learning Hub · Nền tảng phát triển năng lực và đào tạo thông minh</p>
            <p className="text-3xs text-muted-foreground/80">
              Học phần: Hệ Thống Kinh Doanh Thông Minh · Lớp: 65HTTT · GVHD: Đỗ Oanh Cường
            </p>
          </div>

          <div className="flex flex-wrap justify-center gap-6 text-xs font-semibold">
            <button onClick={() => router.push('/welcome')} className="hover:text-foreground transition-colors cursor-pointer">
              Chọn vai trò
            </button>
            <button onClick={() => router.push('/login')} className="hover:text-foreground transition-colors cursor-pointer">
              Đăng nhập
            </button>
            <button onClick={() => router.push('/register')} className="hover:text-foreground transition-colors cursor-pointer">
              Đăng ký
            </button>
            <span className="text-muted-foreground/60">Nhóm 07 © 2026</span>
          </div>
        </div>
      </footer>
    </div>
  )
}
