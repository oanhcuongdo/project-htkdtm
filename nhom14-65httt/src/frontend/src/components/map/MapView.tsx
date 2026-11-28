import { useState } from "react";
import { mapLinks } from "../../utils/mapLinks";
import "./map.css";

export default function MapView({
  latitude,
  longitude,
  name,
}: {
  latitude: number;
  longitude: number;
  name: string;
}) {
  const links = mapLinks(latitude, longitude);
  return links ? (
    <MapContent
      key={`${latitude},${longitude}`}
      links={links}
      name={name}
      latitude={latitude}
      longitude={longitude}
    />
  ) : (
    <p>Chưa có tọa độ hợp lệ để mở bản đồ quán.</p>
  );
}
function MapContent({
  links,
  name,
  latitude,
  longitude,
}: {
  links: NonNullable<ReturnType<typeof mapLinks>>;
  name: string;
  latitude: number;
  longitude: number;
}) {
  const [visible, setVisible] = useState(false);
  return (
    <section className="map-view" aria-label={`Vị trí quán ${name}`}>
      <h3>Vị trí quán</h3>
      <p>
        Tọa độ quán: {latitude}, {longitude}
      </p>
      <p>
        Bấm xem để tải bản đồ từ OpenStreetMap. Chỉ đường sẽ mở Google Maps ở
        tab mới để bạn chọn điểm xuất phát.
      </p>
      <div className="map-actions">
        <button
          type="button"
          className="button secondary"
          aria-expanded={visible}
          onClick={() => setVisible((value) => !value)}
        >
          {visible ? "Ẩn bản đồ" : "Xem bản đồ quán"}
        </button>
        <a href={links.directions} target="_blank" rel="noopener noreferrer">
          Chỉ đường đến quán (tab mới)
        </a>
      </div>
      {visible && (
        <>
          <iframe
            src={links.embed}
            title={`Bản đồ vị trí ${name}`}
            referrerPolicy="no-referrer"
          />
          <p>
            Nếu bản đồ không hiển thị, bạn vẫn có thể xem thực đơn và đặt món
            hoặc{" "}
            <a href={links.map} target="_blank" rel="noopener noreferrer">
              mở OpenStreetMap ở tab mới
            </a>
            .
          </p>
          <p>
            ©{" "}
            <a
              href="https://www.openstreetmap.org/copyright"
              target="_blank"
              rel="noopener noreferrer"
            >
              OpenStreetMap contributors
            </a>
          </p>
        </>
      )}
    </section>
  );
}
