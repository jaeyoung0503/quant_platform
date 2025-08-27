'use client'

import { useState, useEffect } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { CheckCircle, ArrowRight, Home, CreditCard } from 'lucide-react'

export default function PaymentSuccessPage() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const [paymentResult, setPaymentResult] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const paymentKey = searchParams.get('paymentKey')
    const orderId = searchParams.get('orderId')
    const amount = searchParams.get('amount')

    if (paymentKey && orderId && amount) {
      confirmPayment(paymentKey, orderId, amount)
    } else {
      setLoading(false)
    }
  }, [searchParams])

  const confirmPayment = async (paymentKey: string, orderId: string, amount: string) => {
    try {
      const response = await fetch('/api/payment/confirm', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          paymentKey,
          orderId,
          amount: parseInt(amount)
        })
      })

      const result = await response.json()
      
      if (result.success) {
        setPaymentResult(result.data)
      } else {
        console.error('결제 승인 실패:', result.error)
        router.push('/payment/fail?error=' + encodeURIComponent(result.error))
      }
    } catch (error) {
      console.error('결제 승인 요청 실패:', error)
      router.push('/payment/fail?error=' + encodeURIComponent('결제 승인 중 오류가 발생했습니다'))
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const getPaymentMethodName = (method: string) => {
    const methods = {
      '카드': '신용/체크카드',
      '가상계좌': '가상계좌',
      '계좌이체': '실시간 계좌이체',
      '휴대폰': '휴대폰 소액결제'
    }
    return methods[method as keyof typeof methods] || method
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-white text-lg">결제를 승인하는 중입니다...</p>
          <p className="text-gray-400 text-sm mt-2">잠시만 기다려주세요</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900 py-12">
      <div className="max-w-2xl mx-auto px-6">
        <div className="bg-gray-800 rounded-xl p-8 text-center">
          {/* Success Icon */}
          <div className="mb-6">
            <CheckCircle className="w-20 h-20 text-green-500 mx-auto mb-4" />
            <h1 className="text-3xl font-bold text-white mb-2">결제가 완료되었습니다!</h1>
            <p className="text-gray-300">
              Intelliquant 서비스를 이용해 주셔서 감사합니다.
            </p>
          </div>

          {/* Payment Details */}
          {paymentResult && (
            <div className="bg-gray-700 rounded-lg p-6 mb-8 text-left">
              <h3 className="text-white font-semibold text-lg mb-4 flex items-center">
                <CreditCard className="w-5 h-5 mr-2" />
                결제 상세내역
              </h3>
              
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-300">주문번호</span>
                  <span className="text-white font-mono text-sm">{paymentResult.orderId}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">결제상품</span>
                  <span className="text-white">{paymentResult.orderName}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">결제금액</span>
                  <span className="text-white font-semibold">{paymentResult.totalAmount?.toLocaleString()}원</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">결제수단</span>
                  <span className="text-white">
                    {getPaymentMethodName(paymentResult.method)}
                    {paymentResult.card && ` (${paymentResult.card.company} ${paymentResult.card.number})`}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">결제일시</span>
                  <span className="text-white">{formatDate(paymentResult.approvedAt)}</span>
                </div>
                {paymentResult.receipt && (
                  <div className="pt-3 border-t border-gray-600">
                    <a 
                      href={paymentResult.receipt.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-400 hover:text-blue-300 text-sm underline"
                    >
                      영수증 확인하기 →
                    </a>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Service Information */}
          <div className="bg-green-600/10 border border-green-600/20 rounded-lg p-6 mb-8">
            <h3 className="text-green-400 font-semibold mb-3">🎉 서비스 이용 안내</h3>
            <ul className="text-gray-300 text-sm space-y-2 text-left">
              <li>• 결제 완료와 동시에 선택하신 플랜으로 업그레이드되었습니다</li>
              <li>• 추가된 기능들을 지금 바로 이용하실 수 있습니다</li>
              <li>• 구독 관리는 마이페이지에서 확인 가능합니다</li>
              <li>• 문의사항이 있으시면 고객지원팀으로 연락해 주세요</li>
            </ul>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-4">
            <Link href="/dashboard" className="flex-1">
              <button className="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold py-3 px-6 rounded-lg transition-colors flex items-center justify-center">
                <ArrowRight className="w-4 h-4 mr-2" />
                서비스 이용하기
              </button>
            </Link>
            
            <Link href="/membership" className="flex-1">
              <button className="w-full bg-gray-600 hover:bg-gray-500 text-white font-semibold py-3 px-6 rounded-lg transition-colors flex items-center justify-center">
                <Home className="w-4 h-4 mr-2" />
                멤버십 관리
              </button>
            </Link>
          </div>

          {/* Support Information */}
          <div className="mt-8 pt-6 border-t border-gray-600 text-center">
            <p className="text-gray-400 text-sm mb-2">
              결제 관련 문의사항이 있으시면 언제든지 연락해 주세요
            </p>
            <div className="flex justify-center space-x-6 text-sm">
              <a href="mailto:support@intelliquant.ai" className="text-blue-400 hover:text-blue-300">
                support@intelliquant.ai
              </a>
              <span className="text-gray-500">|</span>
              <a href="tel:02-1234-5678" className="text-blue-400 hover:text-blue-300">
                02-1234-5678
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}