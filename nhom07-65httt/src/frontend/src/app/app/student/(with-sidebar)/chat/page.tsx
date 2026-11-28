import { Suspense } from 'react'
import { ChatPanel } from '@/features/chat/ChatPanel'

export default function StudentChatRoutePage() {
  return (
    <Suspense fallback={<div className="min-h-[60vh] bg-background" />}>
      <ChatPanel />
    </Suspense>
  )
}
