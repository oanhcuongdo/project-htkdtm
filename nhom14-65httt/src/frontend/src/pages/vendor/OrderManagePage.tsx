import { useCallback, useState } from "react";
import { Link } from "react-router-dom";
import { listVendorOrders as listOrders } from "../../api/vendor";
import { usePublicData as useRemoteData } from "../../hooks/usePublicData";
import { useAuth } from "../../hooks/useAuth";

import OrderCard from "../../components/order/OrderCard";
import OrderError from "../../components/order/OrderError";
import "../customer/orders.css";

export default function OrderListPage() {
  const { user } = useAuth();
  return user ? <OrderList key={user.id} /> : null;
}
function OrderList() {
  const [offset, setOffset] = useState(0);
  const load = useCallback(
    (signal: AbortSignal) => listOrders({ offset, limit: 11 }, { signal }),
    [offset],
  );
  const result = useRemoteData(load);
  return (
    <section className="orders-page">
      <header className="orders-heading">
        <span className="eyebrow">ĐƠN HÀNG TẠI QUÁN</span>
        <h1>Đơn hàng của quán</h1>
        <p>Xem món khách đặt, địa chỉ giao và trạng thái xử lý.</p>
        <button
          className="order-refresh"
          disabled={result.loading}
          onClick={result.retry}
        >
          Làm mới danh sách
        </button>
      </header>
      {result.loading ? (
        <p role="status">Đang tải đơn hàng…</p>
      ) : result.error ? (
        <OrderError
          error={result.error}
          retry={result.retry}
          listPath="/vendor/orders"
        />
      ) : (
        result.data && (
          <>
            {!result.data.length ? (
              <div className="order-empty">
                <h2>
                  {offset ? "Trang này chưa có đơn" : "Quán chưa có đơn hàng"}
                </h2>
                <p>
                  {offset
                    ? "Danh sách có thể đã thay đổi. Hãy quay lại trang trước."
                    : "Đơn mới sẽ xuất hiện khi khách đặt món tại quán."}
                </p>
                <Link className="button" to="/vendor">
                  Tài khoản chủ quán
                </Link>
              </div>
            ) : (
              <div className="order-list">
                {result.data.slice(0, 10).map((order) => (
                  <OrderCard
                    key={order.id}
                    order={order}
                    detailPath={`/vendor/orders/${order.id}`}
                  />
                ))}
              </div>
            )}
            {(offset > 0 || result.data.length > 10) && (
              <nav
                className="order-pagination"
                aria-label="Phân trang đơn hàng"
              >
                <button
                  disabled={!offset}
                  onClick={() => setOffset((value) => Math.max(0, value - 10))}
                >
                  Trang trước
                </button>
                <span>Trang {offset / 10 + 1}</span>
                <button
                  disabled={result.data.length <= 10}
                  onClick={() => setOffset((value) => value + 10)}
                >
                  Trang sau
                </button>
              </nav>
            )}
          </>
        )
      )}
    </section>
  );
}
