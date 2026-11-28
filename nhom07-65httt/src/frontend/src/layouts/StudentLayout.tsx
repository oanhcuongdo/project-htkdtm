'use client'

import { type ReactNode } from 'react'
import { MainLayout } from '../components/layout/MainLayout'
import { StudentSidebar } from '../components/layout/StudentSidebar'

export function StudentLayout({ children }: { children: ReactNode }) {
  return (
    <MainLayout sidebar={<StudentSidebar />}>
      {children}
    </MainLayout>
  )
}
