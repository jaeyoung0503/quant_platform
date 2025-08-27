// app/onestock/layout.tsx - 수정된 Layout (에러 수정)
// 종목별 백테스트 페이지 레이아웃
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Single Stock Technical Analysis | Quant Platform',
  description: 'Professional single stock technical analysis with 4 core strategies: Golden Cross, RSI Mean Reversion, Bollinger Bands, and MACD Crossover.',
  keywords: [
    'single stock analysis',
    'technical analysis', 
    'stock trading',
    'golden cross strategy',
    'RSI mean reversion',
    'bollinger bands strategy',
    'MACD crossover',
    'stock backtesting',
    'trading signals',
    '주식 분석',
    '기술적 분석',
    '매매 신호'
  ],
  authors: [{ name: 'Quant Platform Team' }],
  openGraph: {
    title: 'Single Stock Technical Analysis - 4 Core Strategies',
    description: 'Advanced technical analysis platform for individual stocks with professional trading strategies.',
    type: 'website',
    locale: 'ko_KR',
  },
  robots: {
    index: true,
    follow: true,
  }
}

interface OneStockLayoutProps {
  children: React.ReactNode;
}

export default function OneStockLayout({ children }: OneStockLayoutProps) {
  return (
    <>
      {/* SEO 최적화를 위한 구조화된 데이터 */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "WebApplication",
            "name": "Single Stock Technical Analysis",
            "description": "Professional technical analysis platform for individual stock analysis with 4 core trading strategies",
            "url": "https://quantplatform.com/onestock",
            "applicationCategory": "FinanceApplication",
            "operatingSystem": "Web Browser",
            "author": {
              "@type": "Organization",
              "name": "Quant Platform"
            }
          })
        }}
      />
      {children}
    </>
  );
}