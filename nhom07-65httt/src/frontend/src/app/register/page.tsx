import { Suspense } from 'react'
import { RegisterPage } from '@/views/AuthPage'

export default function RegisterRoutePage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-background" />}>
      <RegisterPage />
    </Suspense>
  )
}
