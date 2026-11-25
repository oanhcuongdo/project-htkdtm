import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../contexts/SessionContext';
import { loginAccount, registerAccount } from '../services/authService';

export function LoginPage() {
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { setAuthSession } = useSession();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res =
        mode === 'login'
          ? await loginAccount({ email, password })
          : await registerAccount({ email, fullName, password });
      setAuthSession(res.access_token, res.user);
      navigate('/');
    } catch (err) {
      setError(err?.response?.data?.detail || 'Không thể xác thực tài khoản.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-md rounded-2xl border border-teal-200 bg-white p-6 shadow-xs">
      <h1 className="text-xl font-bold text-[#134E4A]">
        {mode === 'login' ? 'Đăng nhập hệ thống' : 'Đăng ký tài khoản'}
      </h1>
      <p className="mt-1 text-sm text-[#475569]">
        Đồng bộ Wishlist, lịch sử tìm kiếm và phân quyền Quản trị viên.
      </p>

      <form onSubmit={handleSubmit} className="mt-5 space-y-4">
        {mode === 'register' && (
          <div>
            <label className="block text-sm font-medium text-[#134E4A]" htmlFor="fullName">
              Họ và tên
            </label>
            <input
              id="fullName"
              type="text"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="mt-1 min-h-11 w-full rounded-xl border border-slate-200 px-3 text-sm"
            />
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-[#134E4A]" htmlFor="email">
            Email
          </label>
          <input
            id="email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 min-h-11 w-full rounded-xl border border-slate-200 px-3 text-sm"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-[#134E4A]" htmlFor="password">
            Mật khẩu
          </label>
          <input
            id="password"
            type="password"
            required
            minLength={6}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 min-h-11 w-full rounded-xl border border-slate-200 px-3 text-sm"
          />
        </div>

        {error && <p className="text-sm font-medium text-[#DC2626]">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="min-h-11 w-full rounded-xl bg-[#0F766E] text-sm font-semibold text-white hover:bg-[#0D9488] disabled:opacity-50"
        >
          {loading ? 'Đang xử lý...' : mode === 'login' ? 'Đăng nhập' : 'Tạo tài khoản'}
        </button>
      </form>

      <button
        type="button"
        onClick={() => setMode((m) => (m === 'login' ? 'register' : 'login'))}
        className="mt-4 w-full text-center text-sm font-medium text-[#0369A1] hover:underline"
      >
        {mode === 'login' ? 'Chưa có tài khoản? Đăng ký ngay' : 'Đã có tài khoản? Đăng nhập'}
      </button>
    </div>
  );
}
