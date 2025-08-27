import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './payment.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: '멤버십 - Intelliquant',
  description: '나에게 필요한 기능과 혜택에 맞는 멤버십에 가입해 보세요',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko">
      <body className={inter.className}>
        <div className="min-h-screen bg-gray-900">
          {children}
        </div>
      </body>
    </html>
  )
}