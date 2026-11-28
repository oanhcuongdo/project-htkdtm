import { useState } from "react";
import { useLocation } from "../../hooks/useLocation";
import AddressFallback from "./AddressFallback";

export default function LocationPicker({
  purpose = "search",
}: {
  purpose?: "search" | "delivery";
}) {
  const { location, locating, error, locate, clear } = useLocation();
  const [resetVersion, setResetVersion] = useState(0);
  return (
    <section className="search-location" aria-labelledby="location-heading">
      <span className="eyebrow">BẮT ĐẦU TỪ GẦN BẠN</span>
      <h2 id="location-heading">
        {purpose === "delivery" ? "Bạn muốn giao đến đâu?" : "Bạn đang ở đâu?"}
      </h2>
      <p>Chọn vị trí để tìm trong phạm vi quán có thể phục vụ.</p>
      <p className="location-privacy">
        {purpose === "delivery"
          ? "Chỉ xin quyền khi bạn bấm định vị. Khi gửi đơn, địa chỉ và tọa độ được lưu tạm trong tab để thử lại cùng yêu cầu nếu mất kết nối."
          : "Chỉ xin quyền khi bạn bấm định vị. Vị trí dùng cho tìm kiếm và chỉ được giữ trong bộ nhớ của trang."}
      </p>
      <button
        type="button"
        className="button"
        disabled={locating}
        onClick={locate}
      >
        {locating ? "Đang định vị…" : "Dùng vị trí hiện tại"}
      </button>
      {locating && <p role="status">Đang chờ vị trí từ trình duyệt…</p>}
      {error && (
        <p role="alert" className="search-error">
          {error}
        </p>
      )}
      <AddressFallback key={resetVersion} />
      {location && (
        <div className="chosen-location" role="status">
          <strong>{location.label}</strong>
          <span>
            {location.latitude.toFixed(5)}, {location.longitude.toFixed(5)}
          </span>
          <button
            type="button"
            onClick={() => {
              clear();
              setResetVersion((value) => value + 1);
            }}
          >
            Xóa vị trí
          </button>
        </div>
      )}
    </section>
  );
}
