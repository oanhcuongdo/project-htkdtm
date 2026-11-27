import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import { roleHome, roleLabels } from "../../utils/auth";

export default function Navbar() {
  const { user, signOut, status } = useAuth();
  const navigate = useNavigate();
  function logout() {
    signOut();
    navigate("/login", { replace: true });
  }
  return (
    <header className="site-header">
      <Link className="brand" to="/" aria-label="Vị Việt — Trang chủ">
        <span className="brand-mark" aria-hidden="true">
          v.
        </span>
        Vị Việt<span className="brand-dot">.</span>
      </Link>
      <nav aria-label="Điều hướng chính">
        <NavLink to="/" end>
          Trang chủ
        </NavLink>
        {user ? (
          <>
            <NavLink to={roleHome(user.role)}>{roleLabels[user.role]}</NavLink>
            <button className="nav-action" onClick={logout}>
              Đăng xuất
            </button>
          </>
        ) : status === "anonymous" ? (
          <>
            <NavLink to="/login">Đăng nhập</NavLink>
            <Link className="button small" to="/register">
              Tạo tài khoản
            </Link>
          </>
        ) : (
          <span className="nav-muted">Đang kết nối tài khoản</span>
        )}
      </nav>
    </header>
  );
}
