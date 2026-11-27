export type UserRole = "customer" | "vendor" | "admin";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_simulated: boolean;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest extends LoginRequest {
  full_name: string;
  role: "customer" | "vendor";
}

export interface SessionTokens {
  access_token: string;
  refresh_token: string;
}

export interface TokenResponse extends SessionTokens {
  token_type: "bearer";
  expires_in: number;
  user: User;
}
