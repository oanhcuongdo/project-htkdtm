import React from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import { useAuth } from './context/AuthContext'
import ChatAIPage from './pages/ChatAIPage'
import DashboardPage from './pages/DashboardPage'
import DataSourcesPage from './pages/DataSourcesPage'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'

function ProtectedRoute({ children }) {
  const { token, loading } = useAuth()
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-boulder-pahkla text-boulder-kabelikivi text-sm font-medium">
        Đang tải phiên đăng nhập...
      </div>
    )
  }
  if (!token) {
    return <Navigate to="/login" replace />
  }
  return children
}

export default function App() {
  return (
    <Routes>
      {/* Trang giới thiệu công khai trước khi vào đăng nhập / tạo tài khoản */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />

      {/* Khu vực ứng dụng yêu cầu xác thực JWT */}
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/chat" element={<ChatAIPage />} />
        <Route path="/data-sources" element={<DataSourcesPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
