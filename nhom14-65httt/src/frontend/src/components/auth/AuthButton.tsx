import MaterialIcon from "./MaterialIcon";

export default function AuthButton({
  label,
  loadingLabel,
  pending,
}: {
  label: string;
  loadingLabel: string;
  pending: boolean;
}) {
  return (
    <button type="submit" className="auth-primary-button" disabled={pending}>
      {pending ? <span className="auth-spinner" aria-hidden="true" /> : null}
      {pending ? loadingLabel : label}
      {!pending && <MaterialIcon name="arrow_forward" />}
    </button>
  );
}
