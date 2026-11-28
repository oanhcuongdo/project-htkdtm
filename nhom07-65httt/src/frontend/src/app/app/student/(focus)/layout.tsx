import type { ReactNode } from 'react'
import { RoleRoute } from '@/components/auth/ProtectedRoute'
import { CourseFocusLayout } from '@/layouts/CourseFocusLayout'

export default function StudentFocusGroupLayout({ children }: { children: ReactNode }) {
  return (
    <RoleRoute allowedRoles={['student']}>
      <CourseFocusLayout>{children}</CourseFocusLayout>
    </RoleRoute>
  )
}
