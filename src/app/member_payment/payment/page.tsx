'use client'

import { useState, useEffect } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, Shield, CheckCircle, Loader } from 'lucide-react'
import TossPaymentComponent from '@/components/TossPayment'

interface PaymentInfo {
  plan: string
  period: string
  price: number
}

interface PreparedPayment {
  orderId: string
  orderName: string
  amount: number
  customerEmail: string
  customerName: string
}

export default function TossPaymentPage() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const [paymentInfo, setPaymentInfo] = useState<PaymentInfo | null>(null)
  const [preparedPayment, setPreparedPayment] = useState<PreparedPayment | null>(null)
  const [preparing, setPreparing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const plan = searchParams.get('plan')
    const period = searchParams.get('period')
    const price = searchParams.get('price')

    if (plan && period && price) {
      const paymentInfo = {
        plan,
        period,
        price: parseInt(price)
      }
      setPaymentInfo(paymentInfo)
      preparePayment(paymentInfo)
    } else {
      router.push('/member_payment')
    }
  }, [searchParams, router])

  const preparePayment = async (info: PaymentInfo) => {
    setPreparing(true)
    setError(null)

    try {
      const response = await fetch('/api/payment/prepare', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          planName: info.plan,
          period: info.period,
          amount: info.price,
          customerEmail: 'user@example.com', // 실제 환경에서는 로그인 사용자 정보
          customerName: '홍길동' // 실제 환경에서는 로그인 사용자 정보
        })
      })

      const result = await response.json()

      if (result.success) {
        setPreparedPayment(result.data)
      } else {
        setError(result.error || '결제 준비 중 오류가 발생했습니다.')
      }

    } catch (err) {
      console.error('결제 준비 오류:', err)
      setError('결제 준비 중 네트워크 오류가 발생했습니다.')
    } finally {
      setPreparing(false)
    }
  }

  const getPlanName = (plan: string) => {
    const plans = {
      'basic': 'Basic',
      'advanced': 'Advanced', 
      'premium': 'Premium'
    }
    return plans[plan as keyof typeof plans] || plan
  }

  const getPlanDescription = (plan: string) => {
    const descriptions = {
      'basic': 'Free',
      'advanced': '실전 퀀트 투자를 위한 핵심 기능',
      'premium': '프리미엄 투자 전략과 고급 분석'
    }
    return descriptions[plan as keyof typeof descriptions] || ''
  }

  const getPeriodText = (period: string) => {
    return period === 'monthly' ? '월간 결제' : '3개월 결제'
  }

  const handlePaymentSuccess = (data: any) => {
    console.log('결제 성공:', data)
    // 토스페이먼츠에서 자동으로 successUrl로 리디렉션됨
  }

  const handlePaymentError = (error: any) => {
    console.error('결제 오류:', error)
    // 토스페이먼츠에서 자동으로 failUrl로 리디렉션되거나
    // 여기서 에러 처리
    setError(error.message)
  }

  if (!paymentInfo) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <Loader className="animate-spin h-8 w-8 text-blue-500 mx-auto mb-4" />
          <p className="text-white text-lg">결제 정보를 불러오는 중...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900 py-12">
      <div className="max-w-4xl mx-auto px-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 주문 정보 */}
          <div className="bg-gray-800 rounded-xl p-6">
            <h2 className="text-2xl font-bold text-white mb-6">주문 정보</h2>
            
            <div className="space-y-4">
              <div className="bg-gray-700 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-white mb-2">
                  {getPlanName(paymentInfo.plan)} 플랜
                </h3>
                <p className="text-gray-300 text-sm mb-3">
                  {getPlanDescription(paymentInfo.plan)}
                </p>
                <div className="flex justify-between items-center">
                  <span className="text-gray-300">{getPeriodText(paymentInfo.period)}</span>
                  <span className="text-xl font-bold text-white">
                    {paymentInfo.price.toLocaleString()}원
                  </span>
                </div>
              </div>

              {paymentInfo.period === 'quarterly' && (
                <div className="bg-green-600/10 border border-green-600/20 rounded-lg p-4">
                  <div className="flex items-center text-green-400 mb-2">
                    <CheckCircle className="w-4 h-4 mr-2" />
                    <span className="font-medium">3개월 결제 할인 적용</span>
                  </div>
                  <p className="text-sm text-gray-300">
                    월간 결제 대비 10% 할인된 금액입니다
                  </p>
                </div>
              )}

              <div className="border-t border-gray-600 pt-4">
                <div className="flex justify-between items-center text-lg">
                  <span className="text-white font-semibold">총 결제금액</span>
                  <span className="text-2xl font-bold text-green-400">
                    {paymentInfo.price.toLocaleString()}원
                  </span>
                </div>
              </div>

              {/* 혜택 안내 */}
              <div className="bg-blue-600/10 border border-blue-600/20 rounded-lg p-4">
                <h4 className="text-blue-400 font-medium mb-2">플랜 혜택</h4>
                <ul className="text-sm text-gray-300 space-y-1">
                  {paymentInfo.plan === 'advanced' && (
                    <>
                      <li>• 백테스트 기간: 2000년~현재 (한국), 2010년~현재 (미국)</li>
                      <li>• 1일 백테스트 100회</li>
                      <li>• 실행 개수: 3개</li>
                      <li>• 자동매매 연동</li>
                    </>
                  )}
                  {paymentInfo.plan === 'premium' && (
                    <>
                      <li>• 백테스트 기간: 2000년~현재 (한국), 2010년~현재 (미국)</li>
                      <li>• 1일 백테스트 100회</li>
                      <li>• 실행 개수: 3개</li>
                      <li>• 자동매매 연동</li>
                      <li>• 프리미엄 투자 전략</li>
                    </>
                  )}
                </ul>
              </div>
            </div>
          </div>

          {/* 결제 수단 */}
          <div className="space-y-6">
            {preparing && (
              <div className="bg-gray-800 rounded-xl p-6 text-center">
                <Loader className="animate-spin h-8 w-8 text-blue-500 mx-auto mb-4" />
                <p className="text-white text-lg">결제를 준비하는 중입니다...</p>
                <p className="text-gray-400 text-sm mt-2">잠시만 기다려주세요</p>
              </div>
            )}

            {error && (
              <div className="bg-red-600/10 border border-red-600/20 rounded-lg p-4">
                <h3 className="text-red-400 font-semibold mb-2">오류 발생</h3>
                <p className="text-gray-300 text-sm">{error}</p>
                <button 
                  onClick={() => paymentInfo && preparePayment(paymentInfo)}
                  className="mt-3 px-4 py-2 bg-red-600 hover:bg-red-500 text-white text-sm rounded transition-colors"
                >
                  다시 시도
                </button>
              </div>
            )}

            {preparedPayment && !preparing && !error && (
              <TossPaymentComponent
                orderId={preparedPayment.orderId}
                orderName={preparedPayment.orderName}
                amount={preparedPayment.amount}
                customerEmail={preparedPayment.customerEmail}
                customerName={preparedPayment.customerName}
                onSuccess={handlePaymentSuccess}
                onError={handlePaymentError}
              />
            )}

            {/* 보안 정보 */}
            <div className="bg-gray-800 rounded-xl p-6">
              <div className="flex items-center text-green-400 mb-4">
                <Shield className="w-5 h-5 mr-2" />
                <span className="font-medium">안전한 결제</span>
              </div>
              <ul className="text-gray-300 text-sm space-y-2">
                <li>• SSL 암호화 통신으로 결제 정보 보호</li>
                <li>• PCI DSS 인증받은 토스페이먼츠 사용</li>
                <li>• 카드 정보는 저장되지 않습니다</li>
                <li>• 24시간 결제 모니터링 시스템 운영</li>
              </ul>
            </div>

            {/* 결제 안내 */}
            <div className="bg-gray-700/50 rounded-lg p-4">
              <h4 className="text-white font-medium mb-2">결제 안내사항</h4>
              <ul className="text-gray-300 text-xs space-y-1">
                <li>• 결제 완료 후 즉시 서비스 이용이 가능합니다</li>
                <li>• 구독 취소는 언제든지 가능하며, 잔여 기간까지 서비스 이용 가능합니다</li>
                <li>• 결제 영수증은 이메일로 자동 발송됩니다</li>
                <li>• 문의사항은 고객센터(support@intelliquant.ai)로 연락주세요</li>
              </ul>
            </div>
          </div>
        </div>

        {/* 돌아가기 버튼 */}
        <div className="mt-8 text-center">
          <Link href="/member_payment">
            <button className="inline-flex items-center px-6 py-2 text-gray-400 hover:text-white transition-colors">
              <ArrowLeft className="w-4 h-4 mr-2" />
              멤버십 선택으로 돌아가기
            </button>
          </Link>
        </div>
      </div>
    </div>
  )
}