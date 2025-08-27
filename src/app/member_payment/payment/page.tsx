'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, CreditCard, Shield, Check } from 'lucide-react'
import { loadTossPayments } from '@tosspayments/payment-sdk'

export default function PaymentPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [tossPayments, setTossPayments] = useState(null)
  
  const [paymentInfo, setPaymentInfo] = useState({
    plan: '',
    period: '',
    price: 0
  })

  const [paymentData, setPaymentData] = useState({
    email: '',
    phone: '',
    customerName: '',
    agreeTerms: false,
    agreePrivacy: false
  })

  // 토스페이먼츠 초기화
  useEffect(() => {
    async function initializeTossPayments() {
      try {
        const tossPayments = await loadTossPayments(process.env.NEXT_PUBLIC_TOSS_CLIENT_KEY || 'test_ck_D5GePWvyJnrK0W0k6q8gLzN97Eoq')
        setTossPayments(tossPayments)
      } catch (error) {
        console.error('토스페이먼츠 초기화 실패:', error)
      }
    }
    initializeTossPayments()
  }, [])

  // URL 파라미터에서 결제 정보 설정
  useEffect(() => {
    const plan = searchParams.get('plan') || ''
    const period = searchParams.get('period') || ''
    const price = parseInt(searchParams.get('price') || '0')
    
    setPaymentInfo({ plan, period, price })
  }, [searchParams])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target
    setPaymentData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
  }

  const generateOrderId = () => {
    return `order_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  const handleTossPayment = async () => {
    if (!tossPayments) {
      alert('결제 시스템을 초기화하는 중입니다. 잠시 후 다시 시도해주세요.')
      return
    }

    if (!paymentData.agreeTerms || !paymentData.agreePrivacy) {
      alert('약관에 동의해주세요.')
      return
    }

    if (!paymentData.email || !paymentData.phone || !paymentData.customerName) {
      alert('필수 정보를 모두 입력해주세요.')
      return
    }

    const orderId = generateOrderId()
    const amount = Math.floor(paymentInfo.price * 1.1) // VAT 포함

    try {
      await tossPayments.requestPayment('카드', {
        amount: amount,
        orderId: orderId,
        orderName: `${getPlanDisplayName(paymentInfo.plan)} 플랜 - ${getPeriodDisplayName(paymentInfo.period)}`,
        customerName: paymentData.customerName,
        customerEmail: paymentData.email,
        successUrl: `${window.location.origin}/payment/success`,
        failUrl: `${window.location.origin}/payment/fail`,
      })
    } catch (error) {
      console.error('결제 요청 실패:', error)
      alert('결제 요청에 실패했습니다. 다시 시도해주세요.')
    }
  }

  const getPlanDisplayName = (plan: string) => {
    const planNames = {
      'advanced': 'Advanced',
      'premium': 'Premium'
    }
    return planNames[plan as keyof typeof planNames] || plan
  }

  const getPeriodDisplayName = (period: string) => {
    return period === 'monthly' ? '월간' : '3개월'
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <div className="max-w-4xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="flex items-center space-x-4 mb-8">
          <Link href="/membership">
            <button className="p-2 text-gray-400 hover:text-white transition-colors">
              <ArrowLeft className="w-6 h-6" />
            </button>
          </Link>
          <h1 className="text-3xl font-bold text-white">결제하기</h1>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Payment Form */}
          <div className="lg:col-span-2 space-y-6">
            {/* TossPayments Info */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-white text-lg font-semibold mb-4 flex items-center">
                <CreditCard className="w-5 h-5 mr-2" />
                토스페이먼츠 안전결제
              </h3>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-blue-800 text-sm">
                  • 신용카드, 체크카드, 계좌이체, 가상계좌 등 다양한 결제수단 지원<br/>
                  • 국내 최고 수준의 보안 시스템으로 안전한 결제<br/>
                  • 결제 후 즉시 서비스 이용 가능
                </p>
              </div>
            </div>

            {/* Customer Information */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-white text-lg font-semibold mb-4">고객 정보</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-white text-sm font-medium mb-2">
                    이름 <span className="text-red-400">*</span>
                  </label>
                  <input
                    type="text"
                    name="customerName"
                    value={paymentData.customerName}
                    onChange={handleInputChange}
                    placeholder="홍길동"
                    className="w-full bg-gray-700 text-white border border-gray-600 rounded-lg px-4 py-3 focus:outline-none focus:border-green-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-white text-sm font-medium mb-2">
                    이메일 <span className="text-red-400">*</span>
                  </label>
                  <input
                    type="email"
                    name="email"
                    value={paymentData.email}
                    onChange={handleInputChange}
                    placeholder="example@email.com"
                    className="w-full bg-gray-700 text-white border border-gray-600 rounded-lg px-4 py-3 focus:outline-none focus:border-green-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-white text-sm font-medium mb-2">
                    연락처 <span className="text-red-400">*</span>
                  </label>
                  <input
                    type="tel"
                    name="phone"
                    value={paymentData.phone}
                    onChange={handleInputChange}
                    placeholder="010-1234-5678"
                    className="w-full bg-gray-700 text-white border border-gray-600 rounded-lg px-4 py-3 focus:outline-none focus:border-green-500"
                    required
                  />
                </div>
              </div>
            </div>

            {/* Terms Agreement */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-white text-lg font-semibold mb-4">약관 동의</h3>
              <div className="space-y-3">
                <label className="flex items-start">
                  <input
                    type="checkbox"
                    name="agreeTerms"
                    checked={paymentData.agreeTerms}
                    onChange={handleInputChange}
                    className="mt-1 mr-3"
                  />
                  <span className="text-white text-sm">
                    <span className="text-red-400">*</span> 이용약관에 동의합니다
                    <Link href="/terms" className="text-blue-400 hover:underline ml-2">
                      [보기]
                    </Link>
                  </span>
                </label>
                <label className="flex items-start">
                  <input
                    type="checkbox"
                    name="agreePrivacy"
                    checked={paymentData.agreePrivacy}
                    onChange={handleInputChange}
                    className="mt-1 mr-3"
                  />
                  <span className="text-white text-sm">
                    <span className="text-red-400">*</span> 개인정보 처리방침에 동의합니다
                    <Link href="/privacy" className="text-blue-400 hover:underline ml-2">
                      [보기]
                    </Link>
                  </span>
                </label>
              </div>
            </div>
          </div>

          {/* Order Summary */}
          <div className="lg:col-span-1">
            <div className="bg-gray-800 rounded-lg p-6 sticky top-8">
              <h3 className="text-white text-lg font-semibold mb-4">주문 요약</h3>
              
              <div className="space-y-4">
                <div className="border-b border-gray-600 pb-4">
                  <div className="flex justify-between text-white mb-2">
                    <span className="font-medium">{getPlanDisplayName(paymentInfo.plan)} 플랜</span>
                  </div>
                  <div className="text-gray-400 text-sm">
                    {getPeriodDisplayName(paymentInfo.period)} 구독
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-white">
                    <span>구독료</span>
                    <span>{paymentInfo.price.toLocaleString()}원</span>
                  </div>
                  <div className="flex justify-between text-white">
                    <span>VAT (10%)</span>
                    <span>{Math.floor(paymentInfo.price * 0.1).toLocaleString()}원</span>
                  </div>
                </div>

                <div className="border-t border-gray-600 pt-4">
                  <div className="flex justify-between text-white font-semibold text-lg">
                    <span>총 결제금액</span>
                    <span>{Math.floor(paymentInfo.price * 1.1).toLocaleString()}원</span>
                  </div>
                </div>
              </div>

              <button
                onClick={handleTossPayment}
                disabled={!paymentData.agreeTerms || !paymentData.agreePrivacy || !tossPayments}
                className="w-full bg-blue-600 hover:bg-blue-500 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-semibold py-4 px-4 rounded-lg mt-6 transition-colors duration-200 flex items-center justify-center"
              >
                <img 
                  src="https://static.toss.im/logos/png/blue-toss-logo.png" 
                  alt="Toss" 
                  className="h-5 mr-2"
                />
                토스페이먼츠로 결제하기
              </button>

              <div className="flex items-center justify-center mt-4 text-gray-400 text-sm">
                <Shield className="w-4 h-4 mr-2" />
                <span>SSL 보안 결제</span>
              </div>

              <div className="mt-6 p-4 bg-gray-700 rounded-lg">
                <h4 className="text-white font-medium mb-2 flex items-center">
                  <Check className="w-4 h-4 mr-2 text-green-400" />
                  결제 후 즉시 이용 가능
                </h4>
                <ul className="text-gray-300 text-sm space-y-1">
                  <li>• 결제 완료 즉시 플랜 업그레이드</li>
                  <li>• 언제든지 구독 취소 가능</li>
                  <li>• 7일 무료 체험 기간 제공</li>
                  <li>• 24시간 고객 지원</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}