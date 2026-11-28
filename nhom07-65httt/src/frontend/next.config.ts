import fs from 'node:fs'
import path from 'node:path'
import type { NextConfig } from 'next'

// Load shared workspace root .env (nhom07-65httt/src/.env) if present
function loadSharedEnv() {
  const candidates = [
    path.resolve(process.cwd(), '../.env'),
    path.resolve(process.cwd(), '.env'),
  ]
  for (const envPath of candidates) {
    if (!fs.existsSync(envPath)) continue
    const content = fs.readFileSync(envPath, 'utf8')
    for (const rawLine of content.split(/\r?\n/)) {
      const line = rawLine.trim()
      if (!line || line.startsWith('#')) continue
      const eqIdx = line.indexOf('=')
      if (eqIdx <= 0) continue
      const key = line.slice(0, eqIdx).trim()
      let val = line.slice(eqIdx + 1).trim()
      if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
        val = val.slice(1, -1)
      }
      if (process.env[key] === undefined) {
        process.env[key] = val
      }
    }
  }
}

loadSharedEnv()

const internalApiBase = (process.env.INTERNAL_API_URL || 'http://localhost:8000').replace(/\/+$/, '')

function normalizePublicApiUrl(raw?: string): string {
  const trimmed = (raw || '').trim().replace(/^["']|["']$/g, '')
  if (!trimmed) return '/api/v1'
  if (trimmed.startsWith('/')) {
    return trimmed.replace(/\/+$/, '') || '/api/v1'
  }
  if (/^https?:\/\//i.test(trimmed)) {
    const clean = trimmed.replace(/\/+$/, '')
    return clean.includes('/api/v1') ? clean : `${clean}/api/v1`
  }
  if (/^api(\/|$)/i.test(trimmed)) {
    return '/' + trimmed.replace(/^\/+|\/+$/g, '')
  }
  if (/^[a-z0-9.-]+\.[a-z]{2,}(\/.*)?$/i.test(trimmed)) {
    const clean = `https://${trimmed}`.replace(/\/+$/, '')
    return clean.includes('/api/v1') ? clean : `${clean}/api/v1`
  }
  return '/api/v1'
}

const nextConfig: NextConfig = {
  output: 'standalone',
  images: {
    unoptimized: true,
  },
  env: {
    NEXT_PUBLIC_API_URL: normalizePublicApiUrl(process.env.NEXT_PUBLIC_API_URL || process.env.VITE_API_URL),
    NEXT_PUBLIC_GOOGLE_CLIENT_ID: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || process.env.VITE_GOOGLE_CLIENT_ID || '',
    NEXT_PUBLIC_FACEBOOK_APP_ID: process.env.NEXT_PUBLIC_FACEBOOK_APP_ID || process.env.VITE_FACEBOOK_APP_ID || '',
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${internalApiBase}/api/:path*`,
      },
    ]
  },
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
        ],
      },
    ]
  },
}

export default nextConfig
