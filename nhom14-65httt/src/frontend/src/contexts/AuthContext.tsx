import { useEffect, useState, type ReactNode } from "react";
import * as auth from "../api/auth";
import {
  AUTH_STORAGE_KEY,
  apiClient,
  errorMessage,
  SessionChangedError,
} from "../api/client";
import { AuthContext, type AuthState } from "./authState";

type Snapshot = Pick<AuthState, "user" | "status" | "error" | "persisted">;
const anonymous: Snapshot = {
  user: null,
  status: "anonymous",
  error: "",
  persisted: true,
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [snapshot, setSnapshot] = useState<Snapshot>({
    ...anonymous,
    status: "loading",
  });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let active = true;
    async function restore() {
      if (!apiClient.hasSession) {
        setSnapshot(anonymous);
        return;
      }
      const version = apiClient.version;
      setSnapshot({ ...anonymous, status: "loading" });
      try {
        const user = await auth.me();
        if (active && version === apiClient.version) {
          setSnapshot({
            user,
            status: "authenticated",
            error: "",
            persisted: apiClient.persisted,
          });
        }
      } catch (error) {
        if (
          !active ||
          version !== apiClient.version ||
          error instanceof SessionChangedError
        )
          return;
        setSnapshot(
          apiClient.hasSession
            ? { ...anonymous, status: "error", error: errorMessage(error) }
            : anonymous,
        );
      }
    }
    const unsubscribe = apiClient.subscribe((event) => {
      if (!active) return;
      if (event.kind === "login") {
        setSnapshot({
          user: event.user,
          status: "authenticated",
          error: "",
          persisted: apiClient.persisted,
        });
      } else if (event.kind === "logout") setSnapshot(anonymous);
      else void restore();
    });
    const onStorage = (event: StorageEvent) => {
      if (event.key === AUTH_STORAGE_KEY || event.key === null)
        apiClient.syncFromStorage();
    };
    window.addEventListener("storage", onStorage);
    void restore();
    return () => {
      active = false;
      unsubscribe();
      window.removeEventListener("storage", onStorage);
    };
  }, [attempt]);

  return (
    <AuthContext.Provider
      value={{
        ...snapshot,
        signIn: auth.login,
        signOut: auth.logout,
        retry: () => setAttempt((value) => value + 1),
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
