import { useRef, useState, type FormEvent } from "react";
import { useLocation } from "../../hooks/useLocation";
import { parseCoordinates } from "../../utils/locationValidation";
export default function AddressFallback() {
  const { location, choose } = useLocation();
  const [latitude, setLatitude] = useState(
    location ? String(location.latitude) : "",
  );
  const [longitude, setLongitude] = useState(
    location ? String(location.longitude) : "",
  );
  const [label, setLabel] = useState(location?.label ?? "");
  const [errors, setErrors] = useState<{
    latitude?: string;
    longitude?: string;
  }>({});
  const latRef = useRef<HTMLInputElement>(null),
    lngRef = useRef<HTMLInputElement>(null);
  function submit(event: FormEvent) {
    event.preventDefault();
    const result = parseCoordinates(latitude, longitude);
    setErrors(result.errors);
    if (!result.point) {
      (result.errors.latitude ? latRef : lngRef).current?.focus();
      return;
    }
    choose({ ...result.point, label: label.trim() || "Vị trí đã chọn" });
  }
  return (
    <details className="manual-location" open={!location}>
      <summary>Nhập tọa độ thủ công</summary>
      <p>
        Chưa có tra cứu địa chỉ tự động. Bạn có thể lấy tọa độ từ bản đồ rồi
        nhập tại đây; tên địa điểm chỉ để bạn dễ nhận biết.
      </p>
      <form onSubmit={submit} noValidate>
        <label htmlFor="location-label">Tên địa điểm (không bắt buộc)</label>
        <input
          id="location-label"
          value={label}
          maxLength={160}
          onChange={(event) => setLabel(event.target.value)}
          placeholder="Ví dụ: Cổng trường"
        />
        <label htmlFor="latitude">Vĩ độ</label>
        <input
          id="latitude"
          ref={latRef}
          inputMode="decimal"
          value={latitude}
          onChange={(event) => {
            setLatitude(event.target.value);
            setErrors((previous) => ({ ...previous, latitude: undefined }));
          }}
          placeholder="Ví dụ: 21.0285"
          aria-invalid={Boolean(errors.latitude)}
          aria-describedby={errors.latitude ? "latitude-error" : undefined}
        />
        {errors.latitude && (
          <p id="latitude-error" className="search-error">
            {errors.latitude}
          </p>
        )}
        <label htmlFor="longitude">Kinh độ</label>
        <input
          id="longitude"
          ref={lngRef}
          inputMode="decimal"
          value={longitude}
          onChange={(event) => {
            setLongitude(event.target.value);
            setErrors((previous) => ({ ...previous, longitude: undefined }));
          }}
          placeholder="Ví dụ: 105.8542"
          aria-invalid={Boolean(errors.longitude)}
          aria-describedby={errors.longitude ? "longitude-error" : undefined}
        />
        {errors.longitude && (
          <p id="longitude-error" className="search-error">
            {errors.longitude}
          </p>
        )}
        <button type="submit" className="button secondary">
          Dùng tọa độ này
        </button>
      </form>
    </details>
  );
}
