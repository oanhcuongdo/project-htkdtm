import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { searchDishes, searchRestaurants } from "../../api/search";
import { errorMessage } from "../../api/client";
import LocationPicker from "../../components/map/LocationPicker";
import SearchResultMap from "../../components/map/SearchResultMap";
import { useLocation } from "../../hooks/useLocation";
import type { Page } from "../../types/common";
import type {
  DishSearchResult,
  RestaurantSearchResult,
} from "../../types/search";
import type { RestaurantPublic } from "../../types/restaurant";
import "./search.css";

type Mode = "dishes" | "restaurants";
type Result = { key: string } & (
  | { state: "ready"; mode: "dishes"; page: Page<DishSearchResult> }
  | { state: "ready"; mode: "restaurants"; page: Page<RestaurantSearchResult> }
  | { state: "error"; message: string }
);
const price = new Intl.NumberFormat("vi-VN", {
  style: "currency",
  currency: "VND",
});
const distance = (km: number) =>
  new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 2 }).format(km);
function availability(restaurant: RestaurantPublic) {
  return !restaurant.is_open
    ? "Đang đóng cửa"
    : !restaurant.accepting_orders
      ? "Đang tạm ngừng nhận đơn"
      : restaurant.can_receive_orders
        ? "Đang nhận đơn"
        : "Hiện chưa thể nhận đơn";
}

export default function SearchPage() {
  const { location } = useLocation();
  const [q, setQ] = useState("");
  const [radius, setRadius] = useState("5");
  const [query, setQuery] = useState({
    q: "",
    radius: 5,
    mode: "dishes" as Mode,
    offset: 0,
  });
  const [attempt, setAttempt] = useState(0);
  const [result, setResult] = useState<Result | null>(null);
  const [formError, setFormError] = useState("");
  const lat = location?.latitude,
    lng = location?.longitude;
  const key = JSON.stringify([lat, lng, query, attempt]);
  useEffect(() => {
    if (lat === undefined || lng === undefined) {
      setResult(null);
      return;
    }
    const controller = new AbortController();
    const params = {
      lat,
      lng,
      q: query.q,
      radius: query.radius,
      offset: query.offset,
      limit: 12,
    };
    const request =
      query.mode === "dishes"
        ? searchDishes(params, { signal: controller.signal }).then((page) => {
            if (!controller.signal.aborted)
              setResult({ key, state: "ready", mode: "dishes", page });
          })
        : searchRestaurants(params, { signal: controller.signal }).then(
            (page) => {
              if (!controller.signal.aborted)
                setResult({ key, state: "ready", mode: "restaurants", page });
            },
          );
    void request.catch((error: unknown) => {
      if (!controller.signal.aborted)
        setResult({ key, state: "error", message: errorMessage(error) });
    });
    return () => controller.abort();
  }, [lat, lng, query, key]);

  // Khi đổi vị trí, quay về trang đầu để không giữ offset của khu vực cũ.
  useEffect(() => {
    setQuery((previous) =>
      previous.offset ? { ...previous, offset: 0 } : previous,
    );
  }, [lat, lng]);
  const current = result?.key === key ? result : null;
  const loading = Boolean(location && !current);
  const ready = current?.state === "ready" ? current : null;
  function submit(event: FormEvent) {
    event.preventDefault();
    if (!location) {
      setFormError("Bạn hãy chọn vị trí trước khi tìm kiếm.");
      return;
    }
    setFormError("");
    setQuery({
      q: q.trim(),
      radius: Number(radius),
      mode: query.mode,
      offset: 0,
    });
    setAttempt((value) => value + 1);
  }
  return (
    <section className="search-page" aria-labelledby="search-heading">
      <header className="search-heading">
        <span className="eyebrow">KHÁM PHÁ VỊ VIỆT</span>
        <h1 id="search-heading">
          Một bữa ngon, <span>ngay gần bạn.</span>
        </h1>
        <p>
          Tìm món yêu thích hoặc một quán quen, theo vị trí và khoảng cách bạn
          chọn.
        </p>
      </header>
      <div className="search-layout">
        <LocationPicker />
        <div className="search-main">
          <form className="search-form" onSubmit={submit} role="search">
            <div>
              <label htmlFor="search-query">Bạn muốn tìm gì?</label>
              <input
                id="search-query"
                value={q}
                maxLength={180}
                onChange={(event) => setQ(event.target.value)}
                placeholder={
                  query.mode === "dishes"
                    ? "Tên món hoặc tên quán…"
                    : "Tên quán hoặc địa chỉ…"
                }
              />
            </div>
            <div>
              <label htmlFor="search-radius">Trong bán kính</label>
              <select
                id="search-radius"
                value={radius}
                onChange={(event) => setRadius(event.target.value)}
              >
                {[1, 3, 5, 10, 20, 50].map((value) => (
                  <option key={value} value={value}>
                    {value} km
                  </option>
                ))}
              </select>
            </div>
            <button className="button" type="submit">
              Tìm kiếm
            </button>
          </form>
          {formError && !location && (
            <p role="alert" className="search-error">
              {formError}
            </p>
          )}
          <div className="search-modes" role="group" aria-label="Loại kết quả">
            {(
              [
                ["dishes", "Món ăn"],
                ["restaurants", "Quán ăn"],
              ] as const
            ).map(([mode, label]) => (
              <button
                type="button"
                key={mode}
                aria-pressed={query.mode === mode}
                onClick={() =>
                  setQuery((previous) => ({ ...previous, mode, offset: 0 }))
                }
              >
                {label}
              </button>
            ))}
          </div>
          <div className="search-results" aria-busy={loading}>
            {!location ? (
              <div className="search-empty">
                <h2>Chọn vị trí để bắt đầu</h2>
                <p>
                  Dùng định vị hoặc nhập tọa độ. Bạn có thể xem kết quả mà chưa
                  cần đăng nhập.
                </p>
              </div>
            ) : loading ? (
              <p role="status">Đang tìm những lựa chọn gần bạn…</p>
            ) : current?.state === "error" ? (
              <div className="search-empty">
                <h2>Chưa tải được kết quả</h2>
                <p role="alert" className="search-error">
                  {current.message}
                </p>
                <button
                  className="button secondary"
                  onClick={() => setAttempt((value) => value + 1)}
                >
                  Thử lại
                </button>
              </div>
            ) : (
              ready && (
                <>
                  <p className="search-count" role="status">
                    {ready.page.total}{" "}
                    {ready.mode === "dishes" ? "món ăn" : "quán ăn"} trong phạm
                    vi {query.radius} km{query.q && <> cho “{query.q}”</>}
                  </p>
                  {!ready.page.items.length ? (
                    <div className="search-empty">
                      <h2>Chưa có kết quả phù hợp</h2>
                      <p>
                        Thử từ khóa khác hoặc chọn bán kính rộng hơn. Bạn cũng
                        có thể kiểm tra lại vị trí.
                      </p>
                    </div>
                  ) : (
                    <div className="search-grid">
                      {ready.mode === "dishes"
                        ? ready.page.items.map((item) => (
                            <article
                              className="search-result-card"
                              key={item.id}
                            >
                              <div className="result-top">
                                <span className="result-kind">
                                  {item.canonical_dish.region}
                                </span>
                                <span>{distance(item.distance_km)} km</span>
                              </div>
                              <h2>
                                <Link to={`/menu-items/${item.id}`}>
                                  {item.name}
                                </Link>
                              </h2>
                              <p className="result-price">
                                {price.format(item.price)}
                              </p>
                              <p className="result-restaurant">
                                <Link to={`/restaurants/${item.restaurant_id}`}>
                                  {item.restaurant_name}
                                </Link>
                              </p>
                              <p
                                className={
                                  item.restaurant.can_receive_orders
                                    ? "result-open"
                                    : "result-closed"
                                }
                              >
                                {availability(item.restaurant)}
                              </p>
                              <details>
                                <summary>Thông tin nguyên liệu</summary>
                                <p>
                                  {item.ingredients.length
                                    ? item.ingredients
                                        .map((ingredient) => ingredient.name)
                                        .join(", ")
                                    : "Quán chưa khai báo nguyên liệu."}
                                </p>
                                <p>
                                  {item.ingredients_verified
                                    ? "Quán đã xác nhận danh sách nguyên liệu."
                                    : "Danh sách nguyên liệu chưa được quán xác nhận."}{" "}
                                  Hãy hỏi quán nếu bạn có dị ứng.
                                </p>
                              </details>
                            </article>
                          ))
                        : ready.page.items.map((restaurant) => (
                            <article
                              className="search-result-card"
                              key={restaurant.id}
                            >
                              <div className="result-top">
                                <span className="result-kind">QUÁN ĂN</span>
                                <span>
                                  {distance(restaurant.distance_km)} km
                                </span>
                              </div>
                              <h2>
                                <Link to={`/restaurants/${restaurant.id}`}>
                                  {restaurant.name}
                                </Link>
                              </h2>
                              <p>{restaurant.address}</p>
                              <p
                                className={
                                  restaurant.can_receive_orders
                                    ? "result-open"
                                    : "result-closed"
                                }
                              >
                                {availability(restaurant)}
                              </p>
                              <p className="result-hours">
                                {restaurant.opens_at} – {restaurant.closes_at} ·
                                Bán kính phục vụ {restaurant.delivery_radius_km}{" "}
                                km
                              </p>
                            </article>
                          ))}
                    </div>
                  )}
                  {ready.page.total > 0 && (
                    <SearchResultMap
                      key={key}
                      restaurants={
                        ready.mode === "restaurants"
                          ? ready.page.items
                          : ready.page.items.map((item) => item.restaurant)
                      }
                    />
                  )}
                  {ready.page.total > 0 && (
                    <nav
                      className="search-pagination"
                      aria-label="Phân trang kết quả"
                    >
                      <button
                        type="button"
                        disabled={query.offset === 0}
                        onClick={() =>
                          setQuery((previous) => ({
                            ...previous,
                            offset: Math.max(0, previous.offset - 12),
                          }))
                        }
                      >
                        Trang trước
                      </button>
                      <span>
                        {ready.page.items.length
                          ? `${ready.page.offset + 1}–${ready.page.offset + ready.page.items.length}`
                          : "0"}{" "}
                        / {ready.page.total}
                      </span>
                      <button
                        type="button"
                        disabled={
                          ready.page.offset + ready.page.limit >=
                          ready.page.total
                        }
                        onClick={() =>
                          setQuery((previous) => ({
                            ...previous,
                            offset: previous.offset + 12,
                          }))
                        }
                      >
                        Trang sau
                      </button>
                    </nav>
                  )}
                </>
              )
            )}
          </div>
          <p className="search-footnote">
            Khoảng cách tính theo đường thẳng. Kết quả chỉ gồm quán đã duyệt
            trong phạm vi phục vụ, chưa được cá nhân hóa theo khẩu vị.
          </p>
        </div>
      </div>
    </section>
  );
}
