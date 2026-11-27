export type MaterialIconName =
  | "arrow_back"
  | "arrow_forward"
  | "check"
  | "check_circle"
  | "close"
  | "info"
  | "lock"
  | "mail"
  | "person"
  | "restaurant"
  | "shield"
  | "visibility"
  | "visibility_off";

export default function MaterialIcon({
  name,
  className = "",
}: {
  name: MaterialIconName;
  className?: string;
}) {
  return (
    <span
      aria-hidden="true"
      className={`material-symbol ${className}`}
      data-icon={name}
    />
  );
}
