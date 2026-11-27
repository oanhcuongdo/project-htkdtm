import { useAuth } from "../hooks/useAuth";
import { roleLabels } from "../utils/auth";

export default function AccountPage() {
  const { user, persisted } = useAuth();
  if (!user) return null;
  return (
    <section className="account-page">
      <span className="eyebrow">TÀI KHOẢN CỦA BẠN</span>
      <h1>Chào {user.full_name}.</h1>
      <p>Rất vui được gặp bạn tại Vị Việt.</p>
      {!persisted && (
        <p className="notice" role="status">
          Trình duyệt không cho lưu phiên. Bạn có thể cần đăng nhập lại khi tải
          lại trang.
        </p>
      )}
      <dl className="account-details">
        <div>
          <dt>Họ và tên</dt>
          <dd>{user.full_name}</dd>
        </div>
        <div>
          <dt>Email</dt>
          <dd>{user.email}</dd>
        </div>
        <div>
          <dt>Vai trò</dt>
          <dd>{roleLabels[user.role]}</dd>
        </div>
      </dl>
    </section>
  );
}
