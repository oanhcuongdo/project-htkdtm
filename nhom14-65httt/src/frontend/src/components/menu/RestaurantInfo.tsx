import type { RestaurantPublic } from "../../types/restaurant";
import { restaurantAvailability } from "../../utils/catalog";
import MapView from "../map/MapView";

export default function RestaurantInfo({
  restaurant,
}: {
  restaurant: RestaurantPublic;
}) {
  return (
    <>
      <p
        className={`catalog-availability ${restaurant.can_receive_orders ? "available" : "unavailable"}`}
      >
        {restaurantAvailability(restaurant)}
      </p>
      <dl className="catalog-facts">
        <div>
          <dt>Địa chỉ</dt>
          <dd>{restaurant.address}</dd>
        </div>
        <div>
          <dt>Giờ phục vụ</dt>
          <dd>
            {restaurant.opens_at === restaurant.closes_at
              ? "Cả ngày"
              : `${restaurant.opens_at} – ${restaurant.closes_at}`}
            {restaurant.opens_at > restaurant.closes_at ? " (qua đêm)" : ""}
            <small>Giờ Việt Nam</small>
          </dd>
        </div>
        <div>
          <dt>Bán kính phục vụ</dt>
          <dd>{restaurant.delivery_radius_km} km</dd>
        </div>
      </dl>
      <MapView
        latitude={restaurant.latitude}
        longitude={restaurant.longitude}
        name={restaurant.name}
      />
    </>
  );
}
