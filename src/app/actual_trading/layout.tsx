// app/actual_trading/layout.tsx
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'QuanTrade Pro - 퀀트 자동매매 시스템',
  description: '실시간 퀀트 자동매매 대시보드',
  keywords: '퀀트, 자동매매, 주식, 트레이딩, 대시보드',
  authors: [{ name: 'QuanTrade Team' }],
  robots: 'noindex, nofollow', // 보안상 검색엔진 차단
}

export default function ActualTradingLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {children}
    </div>
  )
}