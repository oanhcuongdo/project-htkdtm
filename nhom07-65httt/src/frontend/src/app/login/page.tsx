import { Suspense } from 'react'
import { LoginPage } from '@/views/AuthPage'

export default function LoginRoutePage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-background" />}>
      <LoginPage />
    </Suspense>
  )
}
