import { useState, type InputHTMLAttributes } from "react";
import MaterialIcon, { type MaterialIconName } from "./MaterialIcon";

interface Props extends InputHTMLAttributes<HTMLInputElement> {
  id: string;
  label: string;
  icon: MaterialIconName;
  hint?: string;
  error?: string;
  passwordToggle?: boolean;
}

export default function AuthField({
  id,
  label,
  icon,
  hint,
  error,
  passwordToggle,
  type,
  ...input
}: Props) {
  const [visible, setVisible] = useState(false);
  const describedBy = [
    input["aria-describedby"],
    hint ? `${id}-hint` : "",
    error ? `${id}-error` : "",
  ]
    .filter(Boolean)
    .join(" ");
  return (
    <div className={`auth-field${error ? " auth-field--error" : ""}`}>
      <div className="auth-field-outline">
        <label htmlFor={id}>{label}</label>
        <MaterialIcon name={icon} className="auth-field-icon" />
        <input
          {...input}
          id={id}
          type={passwordToggle ? (visible ? "text" : "password") : type}
          aria-invalid={Boolean(error)}
          aria-describedby={describedBy || undefined}
        />
        {passwordToggle && (
          <button
            type="button"
            className="auth-icon-button auth-password-toggle"
            aria-label={`${visible ? "Ẩn" : "Hiện"} ${label.toLowerCase()}`}
            aria-pressed={visible}
            aria-controls={id}
            onClick={() => setVisible((value) => !value)}
          >
            <MaterialIcon name={visible ? "visibility_off" : "visibility"} />
          </button>
        )}
      </div>
      {hint && (
        <p className="auth-field-hint" id={`${id}-hint`}>
          {hint}
        </p>
      )}
      {error && (
        <p className="auth-field-error" id={`${id}-error`} role="alert">
          <MaterialIcon name="info" />
          {error}
        </p>
      )}
    </div>
  );
}
