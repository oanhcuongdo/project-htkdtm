import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import MaterialIcon from "../../components/auth/MaterialIcon";
import type { AuthDialogKind } from "../../components/auth/AuthDialog";
import "@fontsource/be-vietnam-pro/400.css";
import "@fontsource/be-vietnam-pro/500.css";
import "@fontsource/be-vietnam-pro/600.css";
import "@fontsource/be-vietnam-pro/700.css";
import "../../auth.css";

export default function AuthLayout({
  children,
  title,
  intro,
  mode = "login",
  onOpenDialog,
}: {
  children: ReactNode;
  title: string;
  intro: string;
  mode?: "login" | "register";
  onOpenDialog: (kind: AuthDialogKind) => void;
}) {
  return (
    <div className={`auth-root auth-root--${mode}`}>
      <a className="skip-link" href="#auth-main">
        Đến biểu mẫu
      </a>
      <header className="auth-topbar">
        <Link to="/" className="auth-back-link">
          <MaterialIcon name="arrow_back" />
          Về trang chủ
        </Link>
        <span>Hương vị Việt, gần bạn hơn.</span>
      </header>
      <main className="auth-card" id="auth-main" tabIndex={-1}>
        <aside className="auth-brand-panel" aria-label="Về Vị Việt">
          <Link to="/" className="auth-brand" aria-label="Vị Việt — Trang chủ">
            <span className="auth-brand-logo">
              <MaterialIcon name="restaurant" />
            </span>
            <span>
              Vị Việt<span className="auth-brand-period">.</span>
            </span>
          </Link>
          <div className="auth-brand-copy">
            <span className="auth-overline">GẦN GŨI TỪ HƯƠNG VỊ</span>
            <h2>
              Món quen mỗi ngày.
              <br />
              <span>Niềm vui mỗi bữa.</span>
            </h2>
            <p>
              Một chút thân quen, một chút khám phá.
              <br />
              Cùng Vị Việt bắt đầu từ bữa ăn bạn yêu.
            </p>
          </div>
          <svg
            className="auth-illustration"
            viewBox="0 0 360 280"
            fill="none"
            aria-hidden="true"
          >
            <circle cx="178" cy="133" r="113" className="art-circle" />
            <circle cx="306" cy="61" r="14" className="art-accent" />
            <path
              d="M42 181a18 18 0 0 1 18-18h20v36H60a18 18 0 0 1-18-18Z"
              className="art-accent"
            />
            <path
              d="M72 149h211c-8 66-42 91-105 91s-96-25-106-91Z"
              className="art-bowl"
            />
            <ellipse cx="178" cy="149" rx="106" ry="23" className="art-rim" />
            <ellipse cx="178" cy="147" rx="86" ry="12" className="art-soup" />
            <path
              d="m119 145 25-9m12 15 29-16m6 15 26-14m8 10 17-8"
              className="art-noodles"
            />
            <path d="M145 240h66v10h-66z" className="art-foot" />
            <path d="m232 146 64-98m-50 100 65-96" className="art-chopsticks" />
            <path
              d="M126 105c-18-17 17-24 0-44m41 37c-17-18 17-27 0-47m35 56c-13-14 14-23 0-39"
              className="art-steam"
            />
            <path d="M73 251h211" className="art-table" />
            <path
              d="M285 200c-14-20-3-40 17-47 1 21 2 36-17 47Z"
              className="art-leaf"
            />
          </svg>
          <div className="auth-brand-note">
            <MaterialIcon name="check_circle" />
            <span>Đậm vị Việt. Trọn niềm vui.</span>
          </div>
        </aside>
        <section className="auth-form-panel-md" aria-labelledby="auth-title">
          <div className="auth-form-content">
            <span className="auth-form-overline">
              {mode === "register"
                ? "BẮT ĐẦU CÙNG VỊ VIỆT"
                : "CHÀO BẠN ĐẾN VỚI VỊ VIỆT"}
            </span>
            <h1 id="auth-title">{title}</h1>
            <p className="auth-intro">{intro}</p>
            {children}
          </div>
        </section>
      </main>
      <footer className="auth-footer">
        <span>Vị Việt · Nhóm 14 · 65HTTT</span>
        <div>
          <button type="button" onClick={() => onOpenDialog("terms")}>
            Điều khoản sử dụng
          </button>
          <button type="button" onClick={() => onOpenDialog("privacy")}>
            Chính sách bảo mật
          </button>
        </div>
      </footer>
    </div>
  );
}
