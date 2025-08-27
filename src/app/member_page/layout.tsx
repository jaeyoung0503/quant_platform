//file: src/app/member_page/layout.tsx

import type { Metadata } from 'next'


export const metadata: Metadata = {
  title: 'Minimal Auth System',
  description: 'Simple authentication with beautiful design',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko">
      <body className="bg-gray-900">
        {children}
      </body>
    </html>
  )
}
