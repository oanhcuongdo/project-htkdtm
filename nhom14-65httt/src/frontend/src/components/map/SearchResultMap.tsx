import { useState } from "react";
import { Link } from "react-router-dom";
import type { RestaurantPublic } from "../../types/restaurant";
import MapView from "./MapView";

/** Chỉ dùng các quán trong trang kết quả hiện tại, không suy ra toàn bộ kết quả. */
export default function SearchResultMap({
  restaurants,
}: {
  restaurants: RestaurantPublic[];
}) {
  const unique = [
    ...new Map(
      restaurants.map((restaurant) => [restaurant.id, restaurant]),
    ).values(),
  ];
  const [selected, setSelected] = useState("");
  const restaurant = unique.find((item) => String(item.id) === selected);
  if (!unique.length) return null;
  return (
    <section
      className="search-result-map"
      aria-label="Bản đồ quán trong kết quả"
    >
      <h2>Xem vị trí quán</h2>
      <p>
        Chọn một quán trong trang kết quả hiện tại để xem bản đồ và chỉ đường.
        Các món cùng quán được gộp một lựa chọn.
      </p>
      <label htmlFor="result-map-restaurant">Quán cần xem vị trí</label>
      <select
        id="result-map-restaurant"
        value={selected}
        onChange={(event) => setSelected(event.target.value)}
      >
        <option value="">Chọn quán trong kết quả</option>
        {unique.map((item) => (
          <option key={item.id} value={item.id}>
            {item.name} — {item.address}
          </option>
        ))}
      </select>
      {restaurant && (
        <div key={restaurant.id}>
          <p>{restaurant.address}</p>
          <Link to={`/restaurants/${restaurant.id}`}>
            Xem thực đơn {restaurant.name}
          </Link>
          <MapView
            name={restaurant.name}
            latitude={restaurant.latitude}
            longitude={restaurant.longitude}
          />
        </div>
      )}
    </section>
  );
}
