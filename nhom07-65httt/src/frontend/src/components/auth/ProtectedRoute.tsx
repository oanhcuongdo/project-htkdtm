'use client'

import { useEffect, type ReactNode } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { useAppStore } from '../../stores/appStore'

interface ProtectedRouteProps {
  children: ReactNode
  allowedRoles?: string[]
}

export function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const isAuthenticated = useAppStore((s) => s.auth.isAuthenticated)
  const isLoadingUser = useAppStore((s) => s.auth.isLoadingUser)
  const user = useAppStore((s) => s.auth.user)
  const router = useRouter()
  const pathname = usePathname()

  const roleAllowed = !allowedRoles || (user?.role ? allowedRoles.includes(user.role) : true)

  useEffect(() => {
    if (isLoadingUser) return
    if (!isAuthenticated || !user) {
      const fromQuery = pathname ? `?from=${encodeURIComponent(pathname)}` : ''
      router.replace(`/welcome${fromQuery}`)
      return
    }
    if (!roleAllowed) {
      const rolePath = user.role === 'lecturer' ? '/app/lecturer' : '/app/student'
      router.replace(rolePath)
    }
  }, [isLoadingUser, isAuthenticated, user, roleAllowed, router, pathname])

  if (isLoadingUser || !isAuthenticated || !user || !roleAllowed) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          <p className="text-xs text-muted-foreground animate-pulse">Loading...</p>
        </div>
      </div>
    )
  }

  return <>{children}</>
}

export function RoleRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const isAuthenticated = useAppStore((s) => s.auth.isAuthenticated)
  const isLoadingUser = useAppStore((s) => s.auth.isLoadingUser)
  const user = useAppStore((s) => s.auth.user)
  const router = useRouter()

  const userRole = user?.role?.toLowerCase()
  const isAuthorized = Boolean(
    isAuthenticated &&
    user &&
    userRole &&
    (!allowedRoles || allowedRoles.map((r) => r.toLowerCase()).includes(userRole))
  )

  useEffect(() => {
    if (isLoadingUser) return
    if (!isAuthenticated || !user) {
      router.replace('/welcome')
      return
    }
    if (!isAuthorized) {
      router.replace('/unauthorized')
    }
  }, [isLoadingUser, isAuthenticated, user, isAuthorized, router])

  if (isLoadingUser || !isAuthenticated || !user || !isAuthorized) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          <p className="text-xs text-muted-foreground animate-pulse">Loading workspace...</p>
        </div>
      </div>
    )
  }

  return <>{children}</>
}
