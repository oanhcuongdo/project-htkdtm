import { useContext } from "react";
import { AuthContext } from "../contexts/authState";

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth cần nằm trong AuthProvider.");
  return value;
}
