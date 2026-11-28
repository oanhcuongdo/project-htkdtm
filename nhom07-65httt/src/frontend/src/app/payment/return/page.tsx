import { Suspense } from 'react'
import { PaymentReturn } from '@/views/PaymentReturn'

export default function PaymentReturnRoutePage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-background" />}>
      <PaymentReturn />
    </Suspense>
  )
}
