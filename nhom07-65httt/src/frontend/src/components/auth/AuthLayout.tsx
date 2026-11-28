'use client'

import { type ReactNode } from 'react'
import Link from 'next/link'
import { Sparkles, GraduationCap, BookOpen, CheckCircle2, ShieldCheck, ArrowLeft } from 'lucide-react'
import { cn } from '../../utils/cn'

export type AuthRole = 'student' | 'lecturer'

interface AuthLayoutProps {
  role: AuthRole
  children: ReactNode
}

export function AuthLayout({ role, children }: AuthLayoutProps) {
  const isStudent = role === 'student'

  const roleMeta = isStudent
    ? {
        roleName: 'Học viên',
        roleTag: 'Student Workspace',
        icon: GraduationCap,
        badgeClass: 'border-pink-500/25 bg-pink-500/10 text-pink-600 dark:text-pink-300',
        headline: 'Học tập thông minh cùng Trợ lý AI thế hệ mới.',
        subhead: 'Tối ưu hoá thời gian nghiên cứu, tạo flashcard tự động và nắm vững kiến thức chuyên sâu.',
        perks: [
          {
            title: 'Hỏi đáp đa tài liệu',
            desc: 'Tra cứu tức thì qua PDF, bài giảng video, audio và văn bản giáo trình.',
          },
          {
            title: 'Học chủ động & ghi nhớ sâu',
            desc: 'Tự động tạo bộ đề trắc nghiệm và flashcard tương tác từ bài học.',
          },
          {
            title: 'Chấm luận khách quan',
            desc: 'AI phân tích luận điểm, chỉ ra thiếu sót và đề xuất cách cải thiện.',
          },
        ],
        quote: {
          content: 'Đầu tư vào tri thức mang lại lợi nhuận cao nhất cho tương lai.',
          author: 'Benjamin Franklin',
        },
      }
    : {
        roleName: 'Giảng viên',
        roleTag: 'Faculty & Educator',
        icon: BookOpen,
        badgeClass: 'border-fuchsia-500/25 bg-fuchsia-500/10 text-fuchsia-700 dark:text-fuchsia-300',
        headline: 'Thiết kế bài giảng xuất sắc, dẫn dắt thế hệ tương lai.',
        subhead: 'Nền tảng trợ giảng AI giúp số hóa học liệu, tự động hóa chấm thi và thấu hiểu tiến độ học viên.',
        perks: [
          {
            title: 'Tự động hóa giáo trình',
            desc: 'Chuyển đổi tài liệu nghiên cứu thành bài học đa phương tiện chỉ trong vài phút.',
          },
          {
            title: 'Trợ lý chấm thi thông minh',
            desc: 'Rút ngắn 70% thời gian chấm bài tập và luận văn với nhận xét chuẩn học thuật.',
          },
          {
            title: 'Phân tích & Quản lý lớp học',
            desc: 'Theo dõi chi tiết sự tiến bộ và lỗ hổng kiến thức của từng học viên.',
          },
        ],
        quote: {
          content: 'Người thầy giỏi giải thích. Người thầy vĩ đại truyền cảm hứng.',
          author: 'William Arthur Ward',
        },
      }

  const RoleIcon = roleMeta.icon

  return (
    <div className="min-h-screen lg:h-screen lg:overflow-hidden w-full bg-background text-foreground flex flex-col lg:flex-row antialiased">
      {/* ─────────────────────────────────────────────────────────────
          LEFT EDITORIAL PANEL (Locked full-height on lg+, never scrolls)
          ───────────────────────────────────────────────────────────── */}
      <aside className="relative hidden lg:flex lg:h-full lg:w-[44%] xl:w-[43%] shrink-0 flex-col justify-between px-9 py-8 xl:px-12 xl:py-10 overflow-hidden border-r border-border bg-gradient-to-br from-fuchsia-50/90 via-surface to-pink-50/80 dark:from-[#1B0F26] dark:via-[#140B1C] dark:to-[#1E0F1D] text-foreground">
        {/* Subtle decorative background pattern */}
        <div className="absolute inset-0 pointer-events-none opacity-[0.04] dark:opacity-[0.06]">
          <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern id="auth-grid" width="32" height="32" patternUnits="userSpaceOnUse">
                <path d="M 32 0 L 0 0 0 32" fill="none" stroke="currentColor" strokeWidth="1" />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#auth-grid)" />
          </svg>
        </div>

        {/* Ambient Orchid & Rose Glows */}
        <div
          className={cn(
            'absolute -top-28 -left-24 w-80 h-80 rounded-full blur-3xl pointer-events-none opacity-25 dark:opacity-30',
            isStudent ? 'bg-pink-500' : 'bg-fuchsia-600'
          )}
        />
        <div
          className={cn(
            'absolute -bottom-28 -right-24 w-80 h-80 rounded-full blur-3xl pointer-events-none opacity-20 dark:opacity-25',
            isStudent ? 'bg-fuchsia-500' : 'bg-pink-500'
          )}
        />

        {/* Top Header: Brand */}
        <div className="relative z-10 flex items-center justify-between gap-3">
          <Link
            href="/welcome"
            className="group flex items-center gap-3 transition-opacity hover:opacity-90"
            title="Quay về trang chủ"
          >
            <div
              className={cn(
                'flex h-10 w-10 items-center justify-center rounded-xl text-white shadow-md transition-transform duration-200 group-hover:scale-105',
                isStudent
                  ? 'bg-gradient-to-br from-pink-500 to-fuchsia-600 shadow-pink-500/25'
                  : 'bg-gradient-to-br from-fuchsia-600 to-purple-700 shadow-fuchsia-600/25'
              )}
            >
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-display text-base font-bold tracking-tight text-foreground">
                  Learning Hub
                </span>
                <span className="rounded-full bg-primary/15 px-2 py-0.5 text-[10px] font-bold text-primary">
                  AI
                </span>
              </div>
              <p className="text-xs text-muted-foreground">Không gian học tập đa phương thức</p>
            </div>
          </Link>

          <Link
            href="/welcome"
            className="inline-flex items-center gap-1.5 rounded-full border border-border/80 bg-surface-elevated/70 px-3 py-1.5 text-xs font-medium text-muted-foreground backdrop-blur-sm transition-colors hover:border-primary/40 hover:text-foreground"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Trang chủ</span>
          </Link>
        </div>

        {/* Center: Editorial Narrative & Value Props */}
        <div className="relative z-10 my-auto py-4 space-y-5 max-w-md">
          <div
            className={cn(
              'inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold backdrop-blur-md',
              roleMeta.badgeClass
            )}
          >
            <RoleIcon className="h-3.5 w-3.5" />
            <span>{roleMeta.roleTag}</span>
          </div>

          <div className="space-y-2.5">
            <h2 className="font-display text-2xl xl:text-[1.75rem] font-bold tracking-tight text-foreground leading-snug">
              {roleMeta.headline}
            </h2>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {roleMeta.subhead}
            </p>
          </div>

          {/* Value props list */}
          <div className="space-y-2.5 pt-1">
            {roleMeta.perks.map((perk, idx) => (
              <div
                key={idx}
                className="flex items-start gap-3 rounded-xl p-3 border border-border/70 bg-surface-elevated/65 backdrop-blur-sm transition-all duration-200 hover:border-primary/30 hover:bg-surface-elevated/90"
              >
                <div
                  className={cn(
                    'mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg',
                    isStudent
                      ? 'bg-pink-500/12 text-pink-600 dark:text-pink-400'
                      : 'bg-fuchsia-500/12 text-fuchsia-600 dark:text-fuchsia-400'
                  )}
                >
                  <CheckCircle2 className="h-4 w-4" />
                </div>
                <div className="space-y-0.5">
                  <p className="text-xs font-semibold text-foreground">{perk.title}</p>
                  <p className="text-xs text-muted-foreground leading-relaxed">{perk.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom Quote & Trust signal */}
        <div className="relative z-10 pt-4 border-t border-border/70 space-y-2.5">
          <blockquote className="text-xs italic text-foreground/80 leading-relaxed">
            &ldquo;{roleMeta.quote.content}&rdquo;
          </blockquote>
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span className="font-semibold uppercase tracking-wider">— {roleMeta.quote.author}</span>
            <span className="inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-medium">
              <ShieldCheck className="h-3.5 w-3.5" />
              Bảo mật 256-bit SSL
            </span>
          </div>
        </div>
      </aside>

      {/* ─────────────────────────────────────────────────────────────
          RIGHT CONTENT PANEL (Independent vertical scroll on lg+)
          ───────────────────────────────────────────────────────────── */}
      <main
        id="auth-form-scroll"
        className="flex-1 min-h-0 lg:h-full overflow-y-auto scrollbar-thin bg-background"
      >
        <div className="min-h-full flex flex-col justify-between px-4 py-5 sm:px-8 sm:py-7 lg:px-10 lg:py-8">
          {/* Mobile Header (Hidden on lg+) */}
          <div className="lg:hidden flex items-center justify-between pb-4 mb-4 border-b border-border/60">
            <Link href="/welcome" className="flex items-center gap-2.5">
              <div
                className={cn(
                  'flex h-9 w-9 items-center justify-center rounded-lg text-white shadow-soft',
                  isStudent
                    ? 'bg-gradient-to-br from-pink-500 to-fuchsia-600'
                    : 'bg-gradient-to-br from-fuchsia-600 to-purple-700'
                )}
              >
                <Sparkles className="h-4 w-4" />
              </div>
              <div>
                <p className="text-sm font-bold text-foreground font-display leading-none">Learning Hub</p>
                <p className="text-xs text-muted-foreground mt-0.5">AI Learning Platform</p>
              </div>
            </Link>

            <div
              className={cn(
                'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border',
                roleMeta.badgeClass
              )}
            >
              <RoleIcon className="h-3 w-3" />
              <span>{roleMeta.roleName}</span>
            </div>
          </div>

          {/* Centered Form Wrapper */}
          <div className="w-full max-w-[440px] mx-auto my-auto py-2">
            {children}
          </div>

          {/* Global Footer Notes */}
          <footer className="w-full max-w-[440px] mx-auto pt-4 mt-2 border-t border-border/50 text-center text-xs text-muted-foreground space-y-1.5">
            <div className="flex items-center justify-center gap-3.5 text-xs">
              <Link href="/welcome" className="hover:text-foreground transition-colors">
                Giới thiệu
              </Link>
              <span>•</span>
              <a
                href="#terms"
                onClick={(e) => {
                  e.preventDefault()
                  alert('Điều khoản sử dụng được cập nhật cho phiên bản 2026.')
                }}
                className="hover:text-foreground transition-colors"
              >
                Điều khoản
              </a>
              <span>•</span>
              <a
                href="#privacy"
                onClick={(e) => {
                  e.preventDefault()
                  alert('Chính sách bảo mật: Dữ liệu cá nhân được mã hóa và không chia sẻ cho bên thứ ba.')
                }}
                className="hover:text-foreground transition-colors"
              >
                Bảo mật
              </a>
              <span>•</span>
              <a href="mailto:support@learninghubs.tech" className="hover:text-foreground transition-colors">
                Hỗ trợ
              </a>
            </div>
            <p className="text-[11px] text-muted-foreground/80">
              © 2026 Learning Hub. Đột phá không gian học tập cùng AI.
            </p>
          </footer>
        </div>
      </main>
    </div>
  )
}
