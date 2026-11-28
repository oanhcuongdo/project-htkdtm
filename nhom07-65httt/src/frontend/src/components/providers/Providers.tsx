'use client'

import { useEffect, type ReactNode } from 'react'
import { GoogleOAuthProvider } from '@react-oauth/google'
import { ErrorBoundary } from '../common/ErrorBoundary'
import { ThemeProvider } from '../ui/ThemeProvider'
import { ToastContainer } from '../ui/Toast'
import { FloatingAiBot } from '../ai/FloatingAiBot'
import { useAppStore } from '../../stores/appStore'
import { setRateLimitListener } from '../../services/api'

const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || 'dummy-google-client-id'

export function Providers({ children }: { children: ReactNode }) {
  const restoreSession = useAppStore((s) => s.auth.restoreSession)

  useEffect(() => {
    setRateLimitListener((msg) => {
      useAppStore.getState().toasts.add({
        type: 'error',
        title: 'Rate Limited',
        message: msg,
      })
    })
    restoreSession()
  }, [restoreSession])

  return (
    <GoogleOAuthProvider clientId={googleClientId}>
      <ThemeProvider>
        <ErrorBoundary>
          {children}
          <FloatingAiBot />
          <ToastContainer />
        </ErrorBoundary>
      </ThemeProvider>
    </GoogleOAuthProvider>
  )
}
