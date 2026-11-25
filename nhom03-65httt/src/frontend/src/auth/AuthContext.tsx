import React, { createContext, useContext, useState, useEffect } from "react"

export type UserRole = "admin" | "viewer"

export interface UserSession {
  name: string
  email: string
  role: UserRole
  username: string
}

interface AuthContextType {
  user: UserSession | null
  token: string | null
  role: UserRole | null
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
}

const STORAGE_KEY = "eduvision.session"
const TOKEN_KEY = "eduvision.token"

export const getAuthToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEY)
}

const API_BASE_URL =
  import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1"

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => {
    try {
      return localStorage.getItem(TOKEN_KEY)
    } catch {
      return null
    }
  })

  const [user, setUser] = useState<UserSession | null>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      return stored ? JSON.parse(stored) : null
    } catch {
      return null
    }
  })

  useEffect(() => {
    if (token) {
      localStorage.setItem(TOKEN_KEY, token)
    } else {
      localStorage.removeItem(TOKEN_KEY)
    }
  }, [token])

  useEffect(() => {
    if (user) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(user))
    } else {
      localStorage.removeItem(STORAGE_KEY)
    }
  }, [user])

  const login = async (username: string, password: string): Promise<void> => {
    const trimmedUsername = username.trim()
    if (!trimmedUsername || !password) {
      throw new Error("Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu")
    }

    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username: trimmedUsername,
          password,
        }),
      })

      if (!response.ok) {
        let errorDetail = "Tên đăng nhập hoặc mật khẩu không chính xác"
        try {
          const errorData = await response.json()
          if (errorData.detail) {
            errorDetail = errorData.detail
          }
        } catch {
          // Dùng thông báo mặc định nếu không đọc được JSON
        }
        throw new Error(errorDetail)
      }

      const data = await response.json()
      const rawRole = (data.role || "viewer").toLowerCase()
      const role: UserRole = rawRole === "admin" ? "admin" : "viewer"
      const displayName = role === "admin" ? `Quản trị viên (${trimmedUsername})` : `Người xem (${trimmedUsername})`

      const session: UserSession = {
        name: displayName,
        email: `${trimmedUsername}@eduvision.vn`,
        username: trimmedUsername,
        role,
      }

      setToken(data.access_token)
      setUser(session)
    } catch (err) {
      if (err instanceof Error) {
        throw err
      }
      throw new Error("Không thể kết nối đến máy chủ xác thực")
    }
  }

  const logout = () => {
    localStorage.removeItem(STORAGE_KEY)
    localStorage.removeItem(TOKEN_KEY)
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        role: user?.role ?? null,
        isAuthenticated: !!token && !!user,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
