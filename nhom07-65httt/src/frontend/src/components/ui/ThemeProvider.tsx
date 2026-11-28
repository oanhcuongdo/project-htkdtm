'use client'

import { useEffect, useState, type ReactNode } from 'react'
import {
  ThemeContext,
  THEME_STORAGE_KEY,
  applyTheme,
  getSystemTheme,
  type ResolvedTheme,
  type Theme,
} from './theme-context'

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>('light')
  const [resolvedTheme, setResolvedTheme] = useState<ResolvedTheme>('light')

  useEffect(() => {
    const stored = (localStorage.getItem(THEME_STORAGE_KEY) as Theme | null) || 'light'
    const resolved = stored === 'system' ? getSystemTheme() : stored
    // Sync client preference after mount so SSR and initial hydration markup match.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setThemeState(stored)
    setResolvedTheme(resolved)
    applyTheme(resolved)

    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const handleSystemChange = () => {
      const current = (localStorage.getItem(THEME_STORAGE_KEY) as Theme | null) || 'light'
      if (current === 'system') {
        const next = getSystemTheme()
        setResolvedTheme(next)
        applyTheme(next)
      }
    }
    mq.addEventListener('change', handleSystemChange)
    return () => mq.removeEventListener('change', handleSystemChange)
  }, [])

  const setTheme = (next: Theme) => {
    setThemeState(next)
    localStorage.setItem(THEME_STORAGE_KEY, next)
    const resolved = next === 'system' ? getSystemTheme() : next
    setResolvedTheme(resolved)
    applyTheme(resolved)
  }

  return (
    <ThemeContext.Provider value={{ theme, resolvedTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}
