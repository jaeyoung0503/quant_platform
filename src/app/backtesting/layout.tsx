import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Single Stock Technical Analysis',
  description: 'Advanced technical analysis for individual stocks with 4 core trading strategies',
  keywords: ['stock analysis', 'technical analysis', 'trading', 'investment', 'backtesting'],
  authors: [{ name: 'Stock Analysis Team' }],
  viewport: 'width=device-width, initial-scale=1',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko" className="scroll-smooth">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#111827" />
      </head>
      <body className={`${inter.className} antialiased bg-gray-900 text-gray-100 min-h-screen`}>
        {children}
      </body>
    </html>
  )
}