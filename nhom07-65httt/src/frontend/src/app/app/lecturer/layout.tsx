import type { ReactNode } from 'react'
import { RoleRoute } from '@/components/auth/ProtectedRoute'
import { LecturerLayout } from '@/layouts/LecturerLayout'

export default function LecturerGroupLayout({ children }: { children: ReactNode }) {
  return (
    <RoleRoute allowedRoles={['lecturer']}>
      <LecturerLayout>{children}</LecturerLayout>
    </RoleRoute>
  )
}
