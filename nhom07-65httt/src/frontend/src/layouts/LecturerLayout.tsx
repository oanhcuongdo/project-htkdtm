'use client'

import { type ReactNode } from 'react'
import { MainLayout } from '../components/layout/MainLayout'
import { LecturerSidebar } from '../components/layout/LecturerSidebar'

export function LecturerLayout({ children }: { children: ReactNode }) {
  return (
    <MainLayout sidebar={<LecturerSidebar />}>
      {children}
    </MainLayout>
  )
}
