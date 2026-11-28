import type { ReactNode } from 'react'
import { RoleRoute } from '@/components/auth/ProtectedRoute'
import { StudentLayout } from '@/layouts/StudentLayout'

export default function StudentSidebarGroupLayout({ children }: { children: ReactNode }) {
  return (
    <RoleRoute allowedRoles={['student']}>
      <StudentLayout>{children}</StudentLayout>
    </RoleRoute>
  )
}
