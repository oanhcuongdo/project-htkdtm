import { Link, Route, Routes } from "react-router-dom";
import AppShell from "./components/layout/AppShell";
import RoleGuard from "./components/layout/RoleGuard";
import HomePage from "./pages/HomePage";
import AccountPage from "./pages/AccountPage";
import LoginPage from "./pages/auth/LoginPage";
import RegisterPage from "./pages/auth/RegisterPage";

export default function AppRouter() {
  return (
    <Routes>
      <Route path="login" element={<LoginPage />} />
      <Route path="register" element={<RegisterPage />} />
      <Route element={<AppShell />}>
        <Route index element={<HomePage />} />
        <Route element={<RoleGuard />}>
          <Route path="account" element={<AccountPage />} />
        </Route>
        <Route element={<RoleGuard roles={["vendor"]} />}>
          <Route path="vendor" element={<AccountPage />} />
        </Route>
        <Route element={<RoleGuard roles={["admin"]} />}>
          <Route path="admin" element={<AccountPage />} />
        </Route>
        <Route
          path="forbidden"
          element={
            <section className="status-card">
              <span className="eyebrow">QUYỀN TRUY CẬP</span>
              <h1>Trang này dành cho vai trò khác.</h1>
              <p>
                Bạn có thể quay lại trang chủ hoặc đăng nhập bằng tài khoản phù
                hợp.
              </p>
              <Link className="button" to="/">
                Về trang chủ
              </Link>
            </section>
          }
        />
        <Route
          path="*"
          element={
            <section className="status-card">
              <span className="eyebrow">404 · VỊ VIỆT</span>
              <h1>Chưa tìm thấy trang bạn cần.</h1>
              <p>Cùng quay về và bắt đầu lại nhé.</p>
              <Link className="button" to="/">
                Về trang chủ
              </Link>
            </section>
          }
        />
      </Route>
    </Routes>
  );
}
