import { apiClient } from "./client";
import type { LoginRequest, RegisterRequest, User } from "../types/auth";

export function register(payload: RegisterRequest): Promise<User> {
  return apiClient.request("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
    authenticated: false,
  });
}

export const login = (payload: LoginRequest, remember = true) =>
  apiClient.login(payload, remember);
export const me = () => apiClient.request<User>("/auth/me");
export const logout = () => apiClient.logout();
