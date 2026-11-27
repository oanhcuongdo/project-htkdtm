import { useEffect, useRef } from "react";
import MaterialIcon from "./MaterialIcon";

export type AuthDialogKind = "terms" | "privacy" | "recovery";
const titles: Record<AuthDialogKind, string> = {
  terms: "Điều khoản sử dụng",
  privacy: "Chính sách bảo mật",
  recovery: "Hỗ trợ đăng nhập",
};

export default function AuthDialog({
  kind,
  onClose,
}: {
  kind: AuthDialogKind;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    const trigger =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
    dialog.showModal();
    return () => {
      if (dialog.open) dialog.close();
      if (trigger?.isConnected) trigger.focus({ preventScroll: true });
    };
  }, []);
  return (
    <dialog
      ref={ref}
      className="auth-dialog"
      aria-labelledby="auth-dialog-title"
      onCancel={onClose}
    >
      <div className="auth-dialog-heading">
        <MaterialIcon name={kind === "recovery" ? "lock" : "shield"} />
        <button
          className="auth-icon-button"
          type="button"
          onClick={onClose}
          aria-label="Đóng hộp thoại"
        >
          <MaterialIcon name="close" />
        </button>
      </div>
      <h2 id="auth-dialog-title">{titles[kind]}</h2>
      {kind === "recovery" ? (
        <>
          <p>Vị Việt hiện chưa hỗ trợ đặt lại mật khẩu qua email.</p>
          <p>
            Bạn hãy kiểm tra email đã đăng ký và thử nhập lại mật khẩu. Nếu vẫn
            không đăng nhập được, hãy liên hệ người quản trị Vị Việt để được hỗ
            trợ.
          </p>
          <p>
            Không chia sẻ mật khẩu hoặc mã đăng nhập của bạn với người khác.
          </p>
        </>
      ) : kind === "terms" ? (
        <>
          <p>
            Thông tin áp dụng cho bản thử nghiệm Vị Việt của Nhóm 14 · 65HTTT.
          </p>
          <p>
            Bạn sử dụng thông tin đăng ký của mình, giữ bí mật mật khẩu và không
            truy cập tài khoản của người khác.
          </p>
          <p>
            Tài khoản chủ quán cần được liên kết với quán trước khi sử dụng chức
            năng quản lý. Hiện bản thử nghiệm cung cấp chức năng tài khoản; các
            tính năng giao dịch sẽ được giới thiệu riêng khi sẵn sàng.
          </p>
        </>
      ) : (
        <>
          <p>
            Vị Việt lưu họ tên, email, mật khẩu đã băm, vai trò và thời điểm tạo
            để cung cấp chức năng tài khoản. Mật khẩu không được lưu dưới dạng
            văn bản rõ.
          </p>
          <p>
            Khi bật “Ghi nhớ đăng nhập”, token được lưu trong trình duyệt để
            phục hồi tài khoản. Khi tắt, token chỉ được giữ trong phiên của tab
            hiện tại. Bạn có thể xóa phiên trên trình duyệt bằng nút Đăng xuất.
          </p>
          <p>
            Đăng xuất chưa thu hồi token đã cấp ở máy chủ. Không nhập dữ liệu
            nhạy cảm không cần thiết vào bản thử nghiệm hoặc chia sẻ phiên đăng
            nhập với người khác.
          </p>
        </>
      )}
      <button type="button" className="auth-primary-button" onClick={onClose}>
        Đã hiểu
      </button>
    </dialog>
  );
}
