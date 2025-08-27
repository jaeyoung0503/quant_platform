// app/layout.tsx

import type { Metadata, Viewport } from 'next'
import { Inter } from 'next/font/google'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'QuanTrade Pro - 퀀트 자동매매 시스템',
  description: '실시간 퀀트 자동매매 대시보드',
  keywords: '퀀트, 자동매매, 주식, 트레이딩, 대시보드',
  authors: [{ name: 'QuanTrade Team' }],
  robots: 'noindex, nofollow', // 보안상 검색엔진 차단
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#111827',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko" className="dark">
      <head>
        <link rel="icon" href="/favicon.ico" />
      </head>
      <body className={`${inter.className} bg-gray-900 text-white antialiased`}>
        <div id="root">
          {children}
        </div>
      </body>
    </html>
  )
}