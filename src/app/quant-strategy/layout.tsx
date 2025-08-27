//나만의 전략 만들기
// app/thirdpage/layout.tsx - Quant Strategy Backtest Results Layout

import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Quant Strategy Backtest Results | Quant Platform',
  description: 'Professional quantitative strategy backtesting results with comprehensive performance analysis including technical and fundamental strategies.',
  keywords: [
    'quant strategy',
    'backtest results',
    'quantitative analysis',
    'portfolio performance',
    'technical analysis',
    'fundamental analysis',
    'strategy combination',
    'risk analysis',
    'sharpe ratio',
    'maximum drawdown',
    '퀀트 전략',
    '백테스트 결과',
    '포트폴리오 성과',
    '전략 조합'
  ],
  authors: [{ name: 'Quant Platform Team' }],
  openGraph: {
    title: 'Quant Strategy Backtest Results - Professional Analysis',
    description: 'Advanced quantitative strategy backtesting platform with combined technical and fundamental analysis strategies.',
    type: 'website',
    locale: 'ko_KR',
  },
  robots: {
    index: true,
    follow: true,
  },
  other: {
    'theme-color': '#1f2937',
    'color-scheme': 'dark'
  }
}

interface QuantResultsLayoutProps {
  children: React.ReactNode;
}

export default function QuantResultsLayout({ children }: QuantResultsLayoutProps) {
  return (
    <>
      {/* SEO 최적화를 위한 구조화된 데이터 */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "WebApplication",
            "name": "Quant Strategy Backtest Results",
            "description": "Professional quantitative strategy backtesting platform with comprehensive performance analysis and risk metrics",
            "url": "https://quantplatform.com/results",
            "applicationCategory": "FinanceApplication",
            "operatingSystem": "Web Browser",
            "author": {
              "@type": "Organization",
              "name": "Quant Platform"
            },
            "features": [
              "Combined Strategy Backtesting",
              "Technical Analysis Strategies",
              "Fundamental Analysis Strategies", 
              "Risk-Adjusted Performance Metrics",
              "Portfolio Optimization",
              "Drawdown Analysis",
              "Sharpe Ratio Calculation"
            ]
          })
        }}
      />
      
      {/* 추가 메타 태그들 */}
      <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0" />
      <meta name="format-detection" content="telephone=no" />
      <meta name="apple-mobile-web-app-capable" content="yes" />
      <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
      
      {children}
    </>
  );
}