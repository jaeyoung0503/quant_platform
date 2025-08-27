//file: src/app/member_payment/layout.tsx

import type { Metadata } from 'next'
import './payment.css'

export const metadata: Metadata = {
  title: '멤버십 - Intelliquant',
  description: '나에게 필요한 기능과 혜택에 맞는 멤버십에 가입해 보세요',
}

export default function MemberPaymentLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-gray-900">
      {children}
    </div>
  )
}
