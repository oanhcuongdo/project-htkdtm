import type { ReactNode } from 'react'
import { RoleRoute } from '@/components/auth/ProtectedRoute'
import { AdminLayout } from '@/layouts/AdminLayout'

export default function AdminGroupLayout({ children }: { children: ReactNode }) {
  return (
    <RoleRoute allowedRoles={['admin']}>
      <AdminLayout>{children}</AdminLayout>
    </RoleRoute>
  )
}
