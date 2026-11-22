import React from "react"
import { RouterProvider } from "react-router-dom"
import { ThemeProvider } from "@/components/theme-provider"
import { AuthProvider } from "@/auth/AuthContext"
import { router } from "@/routes"
import { Toaster } from "@/components/ui/sonner"

export default function App() {
  return (
    <ThemeProvider defaultTheme="light" storageKey="eduvision.theme">
      <AuthProvider>
        <RouterProvider router={router} />
        <Toaster position="top-right" richColors />
      </AuthProvider>
    </ThemeProvider>
  )
}
