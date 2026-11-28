import { Link } from "react-router-dom";
import type { OrderDetail } from "../../types/order";
import { formatPrice } from "../../utils/catalog";
import { orderTime } from "../../utils/orders";
import OrderStatusBadge from "./OrderStatusBadge";
export default function OrderCard({
  order,
  detailPath,
}: {
  order: OrderDetail;
  detailPath: string;
}) {
  return (
    <article className="order-list-card">
      <div className="order-list-top">
        <h2>
          <Link to={detailPath}>Đơn #{order.id}</Link>
        </h2>
        <OrderStatusBadge status={order.status} />
      </div>
      <time dateTime={order.created_at}>
        {orderTime(order.created_at)} · Giờ Việt Nam
      </time>
      <p className="order-list-items">
        {order.items
          .map((item) => `${item.snapshot_name} × ${item.quantity}`)
          .join(", ")}
      </p>
      <p className="order-list-address">Giao đến: {order.delivery_address}</p>
      <div className="order-list-bottom">
        <strong>{formatPrice(order.total)}</strong>
        <Link to={detailPath} aria-label={`Xem đơn ${order.id}`}>
          Xem chi tiết <span aria-hidden="true">↗</span>
        </Link>
      </div>
    </article>
  );
}
