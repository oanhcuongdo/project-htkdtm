import { Link } from "react-router-dom";
export default function NotFoundPage() {
  return (
    <section className="status-card">
      <span className="eyebrow">404 · VỊ VIỆT</span>
      <h1>Chưa tìm thấy trang bạn cần.</h1>
      <p>Cùng quay về và bắt đầu lại nhé.</p>
      <Link className="button" to="/">
        Về trang chủ
      </Link>
    </section>
  );
}
