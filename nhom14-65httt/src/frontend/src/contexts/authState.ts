import { createContext } from "react";
import type { LoginRequest, User } from "../types/auth";

export interface AuthState {
  user: User | null;
  status: "loading" | "authenticated" | "anonymous" | "error";
  error: string;
  persisted: boolean;
  signIn: (payload: LoginRequest, remember?: boolean) => Promise<User>;
  signOut: () => void;
  retry: () => void;
}

export const AuthContext = createContext<AuthState | null>(null);
