import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { roleHome } from "../utils/auth";

export default function HomePage() {
  const { user } = useAuth();
  return (
    <section className="home-hero">
      <span className="eyebrow">VỊ VIỆT · HƯƠNG VỊ GẦN GŨI</span>
      <h1>
        Hẹn bạn
        <br />
        bên một bữa <em>ngon.</em>
      </h1>
      <p>
        Một nơi dành cho những người yêu món Việt.
        <br />
        Tạo tài khoản để bắt đầu cùng chúng mình.
      </p>
      <Link className="button" to={user ? roleHome(user.role) : "/register"}>
        {user ? "Đến tài khoản của bạn" : "Bắt đầu cùng Vị Việt"}
        <span aria-hidden="true">↗</span>
      </Link>
      {!user && (
        <p className="home-login">
          Đã có tài khoản? <Link to="/login">Đăng nhập</Link>
        </p>
      )}
      <div className="home-stamp" aria-hidden="true">
        ĐẬM ĐÀ
        <br />
        <span>vị Việt.</span>
        <br />
        THÂN QUEN
      </div>
    </section>
  );
}
