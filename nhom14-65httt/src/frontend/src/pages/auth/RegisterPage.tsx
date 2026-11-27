import { useRef, useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import * as auth from "../../api/auth";
import AuthSessionState from "./AuthSessionState";
import { useAuth } from "../../hooks/useAuth";
import { useAuthErrors } from "../../hooks/useAuthErrors";
import { roleHome } from "../../utils/auth";
import { validateRegister } from "../../utils/authValidation";
import AuthField from "../../components/auth/AuthField";
import AuthButton from "../../components/auth/AuthButton";
import AuthDialog, {
  type AuthDialogKind,
} from "../../components/auth/AuthDialog";
import MaterialIcon from "../../components/auth/MaterialIcon";
import AuthLayout from "./AuthLayout";

export default function RegisterPage() {
  const { user, status } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [role, setRole] = useState<"customer" | "vendor">("customer");
  const [consent, setConsent] = useState(false);
  const [pending, setPending] = useState(false);
  const [dialog, setDialog] = useState<AuthDialogKind | null>(null);
  const inFlight = useRef(false);
  const feedback = useAuthErrors(
    validateRegister({
      full_name: fullName,
      email,
      password,
      confirm,
      consent,
    }),
  );
  if (status === "loading" || status === "error")
    return <AuthSessionState mode="register" />;
  if (user) return <Navigate to={roleHome(user.role)} replace />;
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    if (inFlight.current || !feedback.check(form)) return;
    inFlight.current = true;
    setPending(true);
    try {
      const created = await auth.register({
        email: email.trim(),
        full_name: fullName.trim(),
        password,
        role,
      });
      setPassword("");
      setConfirm("");
      navigate("/login", {
        replace: true,
        state: { email: created.email, registered: true },
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
      mode="register"
      title="Tạo tài khoản"
      intro="Một bước nhỏ để bắt đầu những trải nghiệm ngon lành."
      onOpenDialog={setDialog}
    >
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
          <legend className="sr-only">Thông tin đăng ký</legend>
          <AuthField
            id="register-name"
            name="full_name"
            label="Họ và tên"
            icon="person"
            autoComplete="name"
            required
            value={fullName}
            placeholder="Nguyễn Văn A"
            error={feedback.errors.full_name}
            onBlur={() => feedback.touch("full_name")}
            onChange={(event) => {
              setFullName(event.target.value);
              feedback.clear("full_name");
            }}
          />
          <AuthField
            id="register-email"
            name="email"
            label="Email"
            icon="mail"
            type="email"
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
          <div className="auth-password-pair">
            <AuthField
              id="register-password"
              name="password"
              label="Mật khẩu"
              icon="lock"
              passwordToggle
              autoComplete="new-password"
              aria-describedby="register-password-hint"
              required
              value={password}
              error={feedback.errors.password}
              onBlur={() => feedback.touch("password")}
              onChange={(event) => {
                setPassword(event.target.value);
                feedback.clear("password");
              }}
            />
            <AuthField
              id="register-confirm"
              name="confirm"
              label="Xác nhận mật khẩu"
              icon="lock"
              passwordToggle
              autoComplete="new-password"
              required
              value={confirm}
              error={feedback.errors.confirm}
              onBlur={() => feedback.touch("confirm")}
              onChange={(event) => {
                setConfirm(event.target.value);
                feedback.clear("confirm");
              }}
            />
          </div>
          <p className="auth-password-hint" id="register-password-hint">
            <MaterialIcon name="info" />
            Dùng 8–128 ký tự, không chỉ gồm khoảng trắng.
          </p>
          <div className="auth-role-field">
            <label htmlFor="register-role">Loại tài khoản</label>
            <select
              id="register-role"
              name="role"
              value={role}
              onChange={(event) =>
                setRole(event.target.value as "customer" | "vendor")
              }
            >
              <option value="customer">Khách hàng</option>
              <option value="vendor">Chủ quán</option>
            </select>
          </div>
          {role === "vendor" && (
            <p className="auth-field-hint">
              Tài khoản chủ quán cần được liên kết với quán để sử dụng chức năng
              quản lý.
            </p>
          )}
          <div className="auth-consent">
            <label className="auth-checkbox-hitbox">
              <input
                id="register-consent"
                type="checkbox"
                name="consent"
                required
                checked={consent}
                aria-labelledby="register-consent-copy"
                aria-invalid={Boolean(feedback.errors.consent)}
                aria-describedby={
                  feedback.errors.consent ? "register-consent-error" : undefined
                }
                onChange={(event) => {
                  setConsent(event.target.checked);
                  feedback.clear("consent");
                }}
              />
            </label>
            <div id="register-consent-copy">
              <label htmlFor="register-consent">Tôi đồng ý với </label>
              <button
                type="button"
                className="auth-inline-policy"
                onClick={() => setDialog("terms")}
              >
                Điều khoản sử dụng
              </button>
              <span> và </span>
              <button
                type="button"
                className="auth-inline-policy"
                onClick={() => setDialog("privacy")}
              >
                Chính sách bảo mật
              </button>
              <span> của Vị Việt.</span>
            </div>
          </div>
          {feedback.errors.consent && (
            <p
              className="auth-field-error"
              id="register-consent-error"
              role="alert"
            >
              <MaterialIcon name="info" />
              {feedback.errors.consent}
            </p>
          )}
          <AuthButton
            label="Tạo tài khoản"
            loadingLabel="Đang tạo tài khoản…"
            pending={pending}
          />
        </fieldset>
      </form>
      <p className="auth-switch-md">
        Đã có tài khoản? <Link to="/login">Đăng nhập</Link>
      </p>
      {dialog && <AuthDialog kind={dialog} onClose={() => setDialog(null)} />}
    </AuthLayout>
  );
}
