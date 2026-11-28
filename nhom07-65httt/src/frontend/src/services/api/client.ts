import axios from 'axios'

const DEFAULT_API_URL = '/api/v1'

function normalizeApiBase(raw?: string): string {
  const trimmed = (raw || '').trim().replace(/^["']|["']$/g, '')
  if (!trimmed) return DEFAULT_API_URL
  if (trimmed.startsWith('/')) {
    return trimmed.replace(/\/+$/, '') || DEFAULT_API_URL
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
  return DEFAULT_API_URL
}

const API_BASE = normalizeApiBase(process.env.NEXT_PUBLIC_API_URL)

export const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
})

// Access tokens live only in memory. Refresh tokens are HttpOnly cookies set by the API.
let accessToken: string | null = null

export const setAccessToken = (token: string | null) => {
  accessToken = token
}

export const getAccessToken = () => accessToken

export const clearAccessToken = () => {
  accessToken = null
}


let isRefreshing = false
let failedQueue: Array<{
  resolve: (token: string | null) => void
  reject: (error: unknown) => void
}> = []

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

type RateLimitListener = (msg: string) => void
let rateLimitListener: RateLimitListener | null = null

export const setRateLimitListener = (listener: RateLimitListener) => {
  rateLimitListener = listener
}

api.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  // When payload is FormData, NEVER send an explicit Content-Type header so the browser
  // can set 'multipart/form-data; boundary=----WebKitFormBoundary...' correctly.
  if (config.data instanceof FormData) {
    const headers = config.headers as unknown as { delete?: (k: string) => void }
    if (typeof headers?.delete === 'function') {
      headers.delete('Content-Type')
      headers.delete('content-type')
    } else if (config.headers) {
      delete (config.headers as Record<string, unknown>)['Content-Type']
      delete (config.headers as Record<string, unknown>)['content-type']
    }
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    const requestUrl = originalRequest?.url || ''
    const isAuthRequest = requestUrl.includes('/auth/login') || requestUrl.includes('/auth/register') || requestUrl.includes('/auth/refresh')

    if (error.response?.status === 401 && isAuthRequest) {
      return Promise.reject(error)
    }

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise(function (resolve, reject) {
          failedQueue.push({ resolve, reject })
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            return api(originalRequest)
          })
          .catch((err) => {
            return Promise.reject(err)
          })
      }

      originalRequest._retry = true
      isRefreshing = true

      if (typeof document !== 'undefined') {
        try {
          const res = await axios.post(`${API_BASE}/auth/refresh`, {}, { withCredentials: true })
          const { access_token } = res.data
          setAccessToken(access_token)
          originalRequest.headers.Authorization = `Bearer ${access_token}`
          processQueue(null, access_token)
          return api(originalRequest)
        } catch (err) {
          processQueue(err, null)
          clearAccessToken()
          if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
            // eslint-disable-next-line @next/next/no-location-assign-relative-destination
            window.location.href = '/login'
          }
          return Promise.reject(err)
        } finally {
          isRefreshing = false
        }
      }

      isRefreshing = false
      return Promise.reject(error)
    }

    if (error.response?.status === 429) {
      const msg = error.response.data?.message || 'Too many requests. Please try again later.'
      if (rateLimitListener) {
        rateLimitListener(msg)
      }
    }
    return Promise.reject(error)
  }
)

/** Resolve a backend file_url into a same-origin absolute viewer URL. */
export const resolveViewerUrl = (fileUrl?: string) => {
  if (!fileUrl) return undefined
  if (/^https?:\/\//i.test(fileUrl) || fileUrl.startsWith('blob:') || fileUrl.startsWith('data:')) return fileUrl
  const base = (api.defaults.baseURL || '').replace(/\/+$/, '').replace(/\/api\/v1$/, '')
  const path = fileUrl.startsWith('/') ? fileUrl : `/${fileUrl}`
  return `${base}${path}`
}

/** Append the in-memory access token so <iframe>/<video>/<audio> can stream auth-gated content. */
export const withAuthToken = (url?: string, tokenOverride?: string | null) => {
  if (!url) return undefined
  const token = tokenOverride || accessToken
  if (!token) return url
  try {
    const base = typeof window !== 'undefined' ? window.location.origin : 'http://localhost'
    const u = new URL(url, base)
    if (!u.searchParams.get('token')) {
      u.searchParams.set('token', token)
    }
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      return `${u.pathname}${u.search}${u.hash}`
    }
    return u.toString()
  } catch {
    const separator = url.includes('?') ? '&' : '?'
    return `${url}${separator}token=${encodeURIComponent(token)}`
  }
}

export default api
