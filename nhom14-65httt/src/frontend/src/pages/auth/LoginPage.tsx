import { useRef, useState, type FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import AuthSessionState from "./AuthSessionState";
import { useAuth } from "../../hooks/useAuth";
import { useAuthErrors } from "../../hooks/useAuthErrors";
import { roleHome, safeReturnTo } from "../../utils/auth";
import { validateLogin } from "../../utils/authValidation";
import AuthField from "../../components/auth/AuthField";
import AuthButton from "../../components/auth/AuthButton";
import AuthDialog, {
  type AuthDialogKind,
} from "../../components/auth/AuthDialog";
import MaterialIcon from "../../components/auth/MaterialIcon";
import AuthLayout from "./AuthLayout";

export default function LoginPage() {
  const { user, status, signIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as {
    email?: string;
    registered?: boolean;
    returnTo?: string;
  } | null;
  const [email, setEmail] = useState(state?.email || "");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(true);
  const [pending, setPending] = useState(false);
  const [dialog, setDialog] = useState<AuthDialogKind | null>(null);
  const inFlight = useRef(false);
  const feedback = useAuthErrors(validateLogin(email, password));
  if (status === "loading" || status === "error")
    return <AuthSessionState mode="login" />;
  if (user)
    return (
      <Navigate
        to={safeReturnTo(state?.returnTo, roleHome(user.role))}
        replace
      />
    );
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    if (inFlight.current || !feedback.check(form)) return;
    inFlight.current = true;
    setPending(true);
    try {
      const current = await signIn({ email: email.trim(), password }, remember);
      setPassword("");
      navigate(safeReturnTo(state?.returnTo, roleHome(current.role)), {
        replace: true,
      });
    } catch (error) {
      feedback.fail(error, form);
    } finally {
      inFlight.current = false;
      setPending(false);
    }
  }
  return (
    <AuthLayout
      title="Chào mừng bạn trở lại"
      intro="Đăng nhập để tiếp tục hành trình khám phá hương vị Việt."
      onOpenDialog={setDialog}
    >
      {state?.registered && (
        <p className="auth-notice auth-notice--success" role="status">
          <MaterialIcon name="check_circle" />
          Đã tạo tài khoản. Bạn có thể đăng nhập ngay.
        </p>
      )}
      {feedback.formError && (
        <p className="auth-notice auth-notice--error" role="alert">
          <MaterialIcon name="info" />
          {feedback.formError}
        </p>
      )}
      <form
        className="auth-form"
        onSubmit={submit}
        aria-busy={pending}
        noValidate
      >
        <fieldset disabled={pending}>
          <legend className="sr-only">Thông tin đăng nhập</legend>
          <AuthField
            id="login-email"
            name="email"
            label="Email"
            type="email"
            icon="mail"
            autoComplete="username"
            required
            value={email}
            placeholder="ban@example.vn"
            error={feedback.errors.email}
            onBlur={() => feedback.touch("email")}
            onChange={(event) => {
              setEmail(event.target.value);
              feedback.clear("email");
            }}
          />
          <AuthField
            id="login-password"
            name="password"
            label="Mật khẩu"
            icon="lock"
            passwordToggle
            autoComplete="current-password"
            required
            value={password}
            error={feedback.errors.password}
            onBlur={() => feedback.touch("password")}
            onChange={(event) => {
              setPassword(event.target.value);
              feedback.clear("password");
            }}
          />
          <div className="auth-login-options">
            <label className="auth-checkbox-label">
              <input
                type="checkbox"
                name="remember"
                checked={remember}
                onChange={(event) => setRemember(event.target.checked)}
              />
              <span>Ghi nhớ đăng nhập</span>
            </label>
            <button
              type="button"
              className="auth-text-button"
              onClick={() => setDialog("recovery")}
            >
              Quên mật khẩu?
            </button>
          </div>
          <AuthButton
            label="Đăng nhập"
            loadingLabel="Đang đăng nhập…"
            pending={pending}
          />
        </fieldset>
      </form>
      <p className="auth-switch-md">
        Chưa có tài khoản? <Link to="/register">Đăng ký</Link>
      </p>
      <p className="auth-trust-note">
        <MaterialIcon name="shield" />
        An tâm bắt đầu cùng Vị Việt.
      </p>
      {dialog && <AuthDialog kind={dialog} onClose={() => setDialog(null)} />}
    </AuthLayout>
  );
}
