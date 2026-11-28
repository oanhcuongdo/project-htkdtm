import { Suspense } from 'react'
import { MockPaymentGateway } from '@/views/MockPaymentGateway'

export default function MockPaymentGatewayRoutePage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-background" />}>
      <MockPaymentGateway />
    </Suspense>
  )
}
