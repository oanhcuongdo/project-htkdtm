import type { UserRole } from "../types/auth";

export const roleLabels: Record<UserRole, string> = {
  customer: "Khách hàng",
  vendor: "Chủ quán",
  admin: "Quản trị viên",
};

export function roleHome(role: UserRole): string {
  return role === "vendor"
    ? "/vendor"
    : role === "admin"
      ? "/admin"
      : "/account";
}

export function safeReturnTo(value: unknown, fallback: string): string {
  if (
    typeof value !== "string" ||
    !value.startsWith("/") ||
    value.startsWith("//") ||
    value.includes("\\") ||
    Array.from(value).some((character) => character.charCodeAt(0) <= 32) ||
    !["/account", "/vendor", "/admin"].includes(value.split(/[?#]/, 1)[0])
  )
    return fallback;
  return value;
}
