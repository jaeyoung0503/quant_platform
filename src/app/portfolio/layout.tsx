// src/app/layout.tsx

import type { Metadata, Viewport } from 'next'
import { Inter } from 'next/font/google'

const inter = Inter({ subsets: ['latin'] })

// Metadata export (viewport 제외)
export const metadata: Metadata = {
  title: 'quant-platform',
  description: 'quant backtesting platform',
}

// 별도의 Viewport export
export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko">
      <body className={inter.className}>
        {children}
      </body>
    </html>
  )
}