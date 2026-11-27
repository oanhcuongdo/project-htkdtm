import { ApiError } from "../api/client";

export type AuthFieldName =
  "full_name" | "email" | "password" | "confirm" | "consent";
export type AuthErrors = Partial<Record<AuthFieldName, string>>;

export function validateLogin(email: string, password: string): AuthErrors {
  const errors: AuthErrors = {};
  if (!email.trim()) errors.email = "Vui lòng nhập email.";
  else if (
    email.trim().length > 254 ||
    !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())
  )
    errors.email = "Email chưa đúng định dạng. Ví dụ: ban@example.vn.";
  if (!password) errors.password = "Vui lòng nhập mật khẩu.";
  else if (Array.from(password).length > 128)
    errors.password = "Mật khẩu không được quá 128 ký tự.";
  return errors;
}

export function validateRegister(values: {
  full_name: string;
  email: string;
  password: string;
  confirm: string;
  consent: boolean;
}): AuthErrors {
  const errors = validateLogin(values.email, values.password);
  if (!values.full_name.trim()) errors.full_name = "Vui lòng nhập họ và tên.";
  else if (Array.from(values.full_name.trim()).length > 120)
    errors.full_name = "Họ và tên không được quá 120 ký tự.";
  if (
    values.password &&
    (!values.password.trim() || Array.from(values.password).length < 8)
  )
    errors.password =
      "Mật khẩu cần từ 8 đến 128 ký tự và không chỉ có khoảng trắng.";
  if (!values.confirm) errors.confirm = "Vui lòng xác nhận mật khẩu.";
  else if (values.confirm !== values.password)
    errors.confirm = "Mật khẩu xác nhận chưa khớp.";
  if (!values.consent)
    errors.consent =
      "Bạn cần đồng ý với điều khoản và chính sách bảo mật để đăng ký.";
  return errors;
}

export function authServerErrors(error: unknown): AuthErrors {
  if (!(error instanceof ApiError)) return {};
  if (error.code === "EMAIL_EXISTS")
    return {
      email:
        "Email đã được sử dụng. Bạn có thể đăng nhập hoặc dùng email khác.",
    };
  if (error.code === "INVALID_CREDENTIALS")
    return { password: "Email hoặc mật khẩu không đúng." };
  if (!Array.isArray(error.details)) return {};
  const result: AuthErrors = {};
  for (const detail of error.details) {
    if (!detail || !Array.isArray(detail.field)) continue;
    const field = detail.field[detail.field.length - 1];
    if (["full_name", "email", "password"].includes(field)) {
      result[field as AuthFieldName] =
        field === "email"
          ? "Vui lòng kiểm tra lại địa chỉ email."
          : field === "password"
            ? "Mật khẩu cần đáp ứng yêu cầu bên dưới."
            : "Vui lòng kiểm tra lại họ và tên.";
    }
  }
  return result;
}

export function focusFirstError(form: HTMLFormElement, errors: AuthErrors) {
  const order: AuthFieldName[] = [
    "full_name",
    "email",
    "password",
    "confirm",
    "consent",
  ];
  const first = order.find((field) => errors[field]);
  if (first && form.isConnected)
    form.querySelector<HTMLInputElement>(`[name="${first}"]`)?.focus();
}
