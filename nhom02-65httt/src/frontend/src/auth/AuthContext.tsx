import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import type { Role, User } from '@/types/domain';
import { can, type Permission } from '@/lib/rbac';
import { login as apiLogin } from '@/mocks/api';

interface AuthState {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  has: (permission: Permission) => boolean;
  canRole: (roles: Role[]) => boolean;
}

const STORAGE_KEY = 'esp.demo.session';

const AuthContext = createContext<AuthState | null>(null);

function readSession(): User | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as User) : null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(readSession);

  const login = useCallback(async (email: string, password: string) => {
    const { user: next } = await apiLogin(email, password);
    // DEMO session only. In production use httpOnly cookies (UI_SPEC §5 UI-01).
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    setUser(next);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setUser(null);
  }, []);

  const value = useMemo<AuthState>(
    () => ({
      user,
      login,
      logout,
      has: (permission) => can(user?.role, permission),
      canRole: (roles) => (user ? roles.includes(user.role) : false),
    }),
    [user, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}