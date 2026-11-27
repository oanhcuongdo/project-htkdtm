import { useState, type FormEvent } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, Loader2, LockKeyhole, ShieldCheck } from 'lucide-react';
import { useAuth } from '@/auth/AuthContext';
import { Button, Field, Input } from '@/components/ui/primitives';

const DEMO_ACCOUNTS = [
  { email: 'admin@erp.demo', role: 'Quản trị viên' },
  { email: 'manager@erp.demo', role: 'Quản lý' },
  { email: 'analyst@erp.demo', role: 'Chuyên viên định giá' },
];

export function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? '/dashboard';

  const [email, setEmail] = useState('admin@erp.demo');
  const [password, setPassword] = useState('demo1234');
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState<{
    email?: string;
    password?: string;
    form?: string;
  }>({});

  if (user) return <Navigate to={from} replace />;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const nextErrors: { email?: string; password?: string } = {};
    if (!email.trim()) {
      nextErrors.email = 'Vui lòng nhập email.';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      nextErrors.email = 'Email không đúng định dạng.';
    }
    if (!password) {
      nextErrors.password = 'Vui lòng nhập mật khẩu.';
    }
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;

    setSubmitting(true);
    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (err) {
      setErrors({
        form: err instanceof Error ? err.message : 'Đăng nhập thất bại.',
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="grid min-h-full lg:grid-cols-2">
      <div className="hidden flex-col justify-between border-r border-border bg-surface p-10 lg:flex">
        <div className="flex items-center gap-2.5">
          <img
            src="/android-chrome-192x192.png"
            alt="ERP Smart Pricing"
            width={36}
            height={36}
            className="size-9 shrink-0 rounded-[var(--radius-control)] object-contain"
          />
          <div>
            <p className="text-sm font-semibold text-ink">ERP Smart Pricing</p>
            <p className="text-xs text-muted">Định giá đa kênh tích hợp AI &amp; BI</p>
          </div>
        </div>

        <div className="max-w-md">
          <h1 className="text-3xl font-semibold leading-tight tracking-tight text-ink">
            Ra quyết định giá dựa trên dữ liệu, có kiểm soát.
          </h1>
          <p className="mt-3 text-sm leading-relaxed text-muted">
            Tập trung giá vốn, phí kênh, tồn kho và giá đối thủ. Mọi đề xuất đều có
            giá sàn bảo vệ biên lợi nhuận, giải thích và lịch sử kiểm toán.
          </p>
          <ul className="mt-6 space-y-3 text-sm text-ink">
            {[
              'Giá sàn là ràng buộc cứng, không tự động phá biên',
              'Dữ liệu đối thủ có nguồn, thời điểm và độ tươi',
              'Mặc định mô phỏng — không gọi sàn khi chưa có quyền',
            ].map((line) => (
              <li key={line} className="flex items-start gap-2">
                <ShieldCheck className="mt-0.5 size-4 shrink-0 text-success" aria-hidden="true" />
                <span>{line}</span>
              </li>
            ))}
          </ul>
        </div>

        <p className="text-xs text-muted">
          Bản demo học phần · Dữ liệu hiển thị là DEMO, không phải live.
        </p>
      </div>

      <div className="flex items-center justify-center p-6">
        <div className="w-full max-w-sm">
          <div className="mb-8 lg:hidden">
            <img
              src="/android-chrome-192x192.png"
              alt="ERP Smart Pricing"
              width={36}
              height={36}
              className="size-9 rounded-[var(--radius-control)] object-contain"
            />
            <h1 className="mt-3 text-xl font-semibold text-ink">ERP Smart Pricing</h1>
          </div>

          <h2 className="text-lg font-semibold tracking-tight text-ink">Đăng nhập</h2>
          <p className="mt-1 text-sm text-muted">
            Sử dụng tài khoản nội bộ để vào workspace.
          </p>

          <form onSubmit={onSubmit} className="mt-6 space-y-4" noValidate>
            <Field label="Email" htmlFor="email" error={errors.email}>
              <Input
                id="email"
                name="email"
                type="email"
                autoComplete="username"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="ban@congty.vn"
                aria-invalid={Boolean(errors.email)}
              />
            </Field>

            <Field label="Mật khẩu" htmlFor="password" error={errors.password}>
              <div className="relative">
                <Input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pr-10"
                  aria-invalid={Boolean(errors.password)}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1 text-muted hover:text-ink"
                  aria-label={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
                >
                  {showPassword ? (
                    <EyeOff className="size-4" aria-hidden="true" />
                  ) : (
                    <Eye className="size-4" aria-hidden="true" />
                  )}
                </button>
              </div>
            </Field>

            {errors.form ? (
              <p role="alert" className="rounded-[var(--radius-control)] bg-danger/10 px-3 py-2 text-xs text-danger">
                {errors.form}
              </p>
            ) : null}

            <Button type="submit" variant="primary" className="w-full" disabled={submitting}>
              {submitting ? (
                <>
                  <Loader2 className="size-4 animate-spin" aria-hidden="true" />
                  Đang đăng nhập…
                </>
              ) : (
                <>
                  <LockKeyhole className="size-4" aria-hidden="true" />
                  Đăng nhập
                </>
              )}
            </Button>
          </form>

          <div className="mt-6 rounded-[var(--radius-card)] border border-border bg-surface-subtle p-3">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-muted">
              Tài khoản demo · mật khẩu demo1234
            </p>
            <ul className="mt-2 space-y-1">
              {DEMO_ACCOUNTS.map((a) => (
                <li key={a.email} className="flex items-center justify-between gap-3 text-xs">
                  <button
                    type="button"
                    className="font-mono text-primary hover:underline"
                    onClick={() => {
                      setEmail(a.email);
                      setPassword('demo1234');
                    }}
                  >
                    {a.email}
                  </button>
                  <span className="text-muted">{a.role}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}