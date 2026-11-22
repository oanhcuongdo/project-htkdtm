import React from "react"
import { Navigate, Outlet } from "react-router-dom"
import { useAuth, type UserRole } from "@/auth/AuthContext"

interface RoleGuardProps {
  allowedRoles: UserRole[]
}

export const RoleGuard: React.FC<RoleGuardProps> = ({ allowedRoles }) => {
  const { role, isAuthenticated } = useAuth()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (!role || !allowedRoles.includes(role)) {
    return <Navigate to="/khong-co-quyen" replace />
  }

  return <Outlet />
}
