import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import type { UserRole } from "../../types/auth";

export function SessionStatus() {
  const { status, error, retry, signOut } = useAuth();
  if (status === "loading")
    return (
      <div className="status-card" role="status">
        Đang kiểm tra phiên đăng nhập…
      </div>
    );
  return (
    <div className="status-card">
      <h1>Chưa kết nối được tài khoản</h1>
      <p role="alert">{error}</p>
      <div className="button-row">
        <button className="button" onClick={retry}>
          Thử lại
        </button>
        <button className="button secondary" onClick={signOut}>
          Đăng nhập lại
        </button>
      </div>
    </div>
  );
}

export default function RoleGuard({ roles }: { roles?: UserRole[] }) {
  const { user, status } = useAuth();
  const location = useLocation();
  if (status === "loading" || status === "error") return <SessionStatus />;
  if (!user)
    return (
      <Navigate
        to="/login"
        replace
        state={{ returnTo: location.pathname + location.search }}
      />
    );
  if (roles && !roles.includes(user.role))
    return <Navigate to="/forbidden" replace />;
  return <Outlet />;
}
