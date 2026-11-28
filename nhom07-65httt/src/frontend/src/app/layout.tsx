import type { Metadata } from 'next'
import type { ReactNode } from 'react'
import '../index.css'
import '../components/ui/markdown.css'
import { Providers } from '../components/providers/Providers'

export const metadata: Metadata = {
  title: 'Learning Hub · AI Study Workspace',
  description: 'Nền tảng phát triển năng lực và đào tạo thông minh dành cho sinh viên',
  icons: {
    icon: '/favicon.svg',
  },
}

const themeInitScript = `(function () {
  try {
    var stored = localStorage.getItem('theme');
    var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    var theme = stored || 'light';
    var isDark = theme === 'dark' || (theme === 'system' && prefersDark);
    if (isDark) document.documentElement.classList.add('dark');
  } catch (_) {}
})();`

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="vi" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        {/* eslint-disable-next-line @next/next/no-page-custom-font */}
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
