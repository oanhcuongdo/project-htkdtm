import { useState } from "react";
import { useAuth } from "../../hooks/useAuth";
import AuthDialog, {
  type AuthDialogKind,
} from "../../components/auth/AuthDialog";
import MaterialIcon from "../../components/auth/MaterialIcon";
import AuthLayout from "./AuthLayout";

export default function AuthSessionState({
  mode,
}: {
  mode: "login" | "register";
}) {
  const { status, error, retry, signOut } = useAuth();
  const [dialog, setDialog] = useState<AuthDialogKind | null>(null);
  return (
    <AuthLayout
      mode={mode}
      title={
        status === "error"
          ? "Chưa kết nối được tài khoản"
          : mode === "login"
            ? "Chào mừng bạn trở lại"
            : "Tạo tài khoản"
      }
      intro={
        status === "error"
          ? "Bạn có thể thử kết nối lại hoặc bắt đầu một phiên đăng nhập mới."
          : "Chờ một chút để Vị Việt kiểm tra phiên đăng nhập của bạn."
      }
      onOpenDialog={setDialog}
    >
      {status === "loading" ? (
        <p className="auth-session-loading" role="status">
          <span className="auth-spinner" aria-hidden="true" />
          Đang kiểm tra phiên đăng nhập…
        </p>
      ) : (
        <>
          <p className="auth-notice auth-notice--error" role="alert">
            <MaterialIcon name="info" />
            {error}
          </p>
          <button className="auth-primary-button" type="button" onClick={retry}>
            Thử lại
          </button>
          <button
            className="auth-text-button auth-session-reset"
            type="button"
            onClick={signOut}
          >
            Đăng nhập lại
          </button>
        </>
      )}
      {dialog && <AuthDialog kind={dialog} onClose={() => setDialog(null)} />}
    </AuthLayout>
  );
}
