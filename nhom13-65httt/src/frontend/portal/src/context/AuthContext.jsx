import React, { createContext, useContext, useEffect, useState } from 'react'
import api from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem('pfi_user')
      return saved ? JSON.parse(saved) : null
    } catch {
      return null
    }
  })
  const [token, setToken] = useState(() => localStorage.getItem('pfi_token'))
  const [loading, setLoading] = useState(Boolean(token))

  useEffect(() => {
    if (!token) {
      setLoading(false)
      return
    }
    api
      .get('/auth/me')
      .then((res) => {
        setUser(res.data)
        localStorage.setItem('pfi_user', JSON.stringify(res.data))
      })
      .catch(() => {
        logout()
      })
      .finally(() => setLoading(false))
  }, [token])

  const saveSession = (data) => {
    localStorage.setItem('pfi_token', data.access_token)
    localStorage.setItem('pfi_user', JSON.stringify(data.user))
    setToken(data.access_token)
    setUser(data.user)
  }

  const login = async (email, password) => {
    const res = await api.post('/auth/login', { email, password })
    saveSession(res.data)
    return res.data
  }

  const register = async (full_name, email, password) => {
    const res = await api.post('/auth/register', { full_name, email, password })
    saveSession(res.data)
    return res.data
  }

  const logout = () => {
    localStorage.removeItem('pfi_token')
    localStorage.removeItem('pfi_user')
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout, setUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
