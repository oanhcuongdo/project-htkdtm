import React, { createContext, useContext, useState, useEffect } from "react"

export type UserRole = "admin" | "viewer"

export interface UserSession {
  name: string
  email: string
  role: UserRole
}

interface AuthContextType {
  user: UserSession | null
  role: UserRole | null
  isAuthenticated: boolean
  login: (email: string, name?: string) => void
  loginAsAdmin: () => void
  loginAsViewer: () => void
  logout: () => void
}

const STORAGE_KEY = "eduvision.session"

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserSession | null>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      return stored ? JSON.parse(stored) : null
    } catch {
      return null
    }
  })

  useEffect(() => {
    if (user) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(user))
    } else {
      localStorage.removeItem(STORAGE_KEY)
    }
  }, [user])

  const login = (email: string, name?: string) => {
    const trimmedEmail = email.trim()
    const isAdmin = trimmedEmail.toLowerCase().includes("admin")
    const role: UserRole = isAdmin ? "admin" : "viewer"
    const displayName = name?.trim() || (isAdmin ? "Quản trị viên (Admin)" : "Người xem (Viewer)")

    const session: UserSession = {
      name: displayName,
      email: trimmedEmail || (isAdmin ? "admin@eduvision.vn" : "viewer@eduvision.vn"),
      role,
    }
    setUser(session)
  }

  const loginAsAdmin = () => {
    const adminSession: UserSession = {
      name: "Quản trị viên Demo",
      email: "admin@eduvision.vn",
      role: "admin",
    }
    setUser(adminSession)
  }

  const loginAsViewer = () => {
    const viewerSession: UserSession = {
      name: "Người xem Demo",
      email: "viewer@eduvision.vn",
      role: "viewer",
    }
    setUser(viewerSession)
  }

  const logout = () => {
    localStorage.removeItem(STORAGE_KEY)
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        role: user?.role ?? null,
        isAuthenticated: !!user,
        login,
        loginAsAdmin,
        loginAsViewer,
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
