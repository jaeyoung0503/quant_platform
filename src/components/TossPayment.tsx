'use client'

import { useEffect, useRef, useState } from 'react'
import { loadTossPayments, TossPayments } from '@tosspayments/payment-sdk'

interface TossPaymentProps {
  orderId: string
  orderName: string
  amount: number
  customerEmail?: string
  customerName?: string
  onSuccess?: (data: any) => void
  onError?: (error: any) => void
}

export default function TossPaymentComponent({
  orderId,
  orderName, 
  amount,
  customerEmail = 'guest@intelliquant.ai',
  customerName = '게스트',
  onSuccess,
  onError
}: TossPaymentProps) {
  const [tossPayments, setTossPayments] = useState<TossPayments | null>(null)
  const [selectedMethod, setSelectedMethod] = useState('CARD')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // 결제 위젯 컨테이너 refs
  const cardRef = useRef<HTMLDivElement>(null)
  const accountRef = useRef<HTMLDivElement>(null)
  const phoneRef = useRef<HTMLDivElement>(null)

  // 토스페이먼츠 SDK 초기화
  useEffect(() => {
    async function initializeTossPayments() {
      try {
        const clientKey = process.env.NEXT_PUBLIC_TOSS_CLIENT_KEY!
        const tossPaymentsInstance = await loadTossPayments(clientKey)
        setTossPayments(tossPaymentsInstance)
      } catch (err) {
        console.error('토스페이먼츠 초기화 실패:', err)
        setError('결제 모듈을 불러올 수 없습니다.')
      }
    }

    initializeTossPayments()
  }, [])

  // 결제 위젯 렌더링
  useEffect(() => {
    if (!tossPayments) return

    try {
      // 카드 결제 위젯
      if (cardRef.current && selectedMethod === 'CARD') {
        tossPayments.renderPaymentMethods({
          selector: cardRef.current,
          variantKey: 'DEFAULT',
          options: {
            currency: 'KRW'
          }
        })
      }

      // 계좌이체 위젯
      if (accountRef.current && selectedMethod === 'TRANSFER') {
        tossPayments.renderPaymentMethods({
          selector: accountRef.current,
          variantKey: 'TRANSFER',
          options: {
            currency: 'KRW'
          }
        })
      }

      // 휴대폰 결제 위젯
      if (phoneRef.current && selectedMethod === 'MOBILE_PHONE') {
        tossPayments.renderPaymentMethods({
          selector: phoneRef.current,
          variantKey: 'MOBILE_PHONE',
          options: {
            currency: 'KRW'
          }
        })
      }

    } catch (err) {
      console.error('결제 위젯 렌더링 실패:', err)
      setError('결제 위젯을 표시할 수 없습니다.')
    }
  }, [tossPayments, selectedMethod])

  // 결제 요청
  const handlePayment = async () => {
    if (!tossPayments) {
      setError('결제 모듈이 초기화되지 않았습니다.')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const baseUrl = process.env.NEXT_PUBLIC_APP_URL || window.location.origin

      const result = await tossPayments.requestPayment(selectedMethod, {
        amount,
        orderId,
        orderName,
        customerEmail,
        customerName,
        successUrl: `${baseUrl}/member_payment/payment/success`,
        failUrl: `${baseUrl}/member_payment/payment/fail`,
        // 추가 옵션들
        validHours: 1, // 결제 유효시간 1시간
        cashReceipt: {
          type: '소득공제'
        },
        // 카드 결제 옵션
        ...(selectedMethod === 'CARD' && {
          cardInstallmentPlan: [0, 2, 3, 4, 5, 6], // 할부 개월수
          maxCardInstallmentPlan: 12,
          useCardPoint: true,
          useAppCardOnly: false
        }),
        // 가상계좌 옵션
        ...(selectedMethod === 'VIRTUAL_ACCOUNT' && {
          virtualAccountCallbackUrl: `${baseUrl}/api/payment/virtual-account-callback`,
          validHours: 24 // 가상계좌 유효시간 24시간
        })
      })

      // 성공 시 콜백 실행
      if (onSuccess) {
        onSuccess(result)
      }

    } catch (err: any) {
      console.error('결제 요청 실패:', err)
      
      let errorMessage = '결제 중 오류가 발생했습니다.'
      
      if (err.code) {
        switch (err.code) {
          case 'USER_CANCEL':
            errorMessage = '사용자가 결제를 취소했습니다.'
            break
          case 'INVALID_CARD_NUMBER':
            errorMessage = '카드번호가 올바르지 않습니다.'
            break
          case 'INVALID_EXPIRY_DATE':
            errorMessage = '카드 유효기간을 확인해주세요.'
            break
          case 'INVALID_AUTH_VALUE':
            errorMessage = '카드 인증값이 올바르지 않습니다.'
            break
          case 'CARD_COMPANY_NOT_AVAILABLE':
            errorMessage = '카드사 서비스가 일시 중단되었습니다.'
            break
          case 'EXCEED_MAX_CARD_INSTALLMENT_PLAN':
            errorMessage = '할부 개월수를 확인해주세요.'
            break
          case 'INVALID_STOPPED_CARD':
            errorMessage = '정지된 카드입니다.'
            break
          case 'LIMIT_EXCEEDED':
            errorMessage = '카드 한도를 확인해주세요.'
            break
          default:
            errorMessage = err.message || errorMessage
        }
      }

      setError(errorMessage)
      
      if (onError) {
        onError({ ...err, message: errorMessage })
      }
    } finally {
      setLoading(false)
    }
  }

  const paymentMethods = [
    {
      key: 'CARD',
      name: '신용/체크카드',
      description: '국내외 모든 카드 사용 가능',
      icon: '💳'
    },
    {
      key: 'TRANSFER',
      name: '실시간 계좌이체',
      description: '은행 계좌에서 직접 이체',
      icon: '🏦'
    },
    {
      key: 'VIRTUAL_ACCOUNT',
      name: '가상계좌',
      description: '가상계좌로 입금 후 자동승인',
      icon: '📄'
    },
    {
      key: 'MOBILE_PHONE',
      name: '휴대폰 소액결제',
      description: '휴대폰 요금과 함께 결제',
      icon: '📱'
    }
  ]

  if (!tossPayments) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mr-3"></div>
        <span className="text-gray-300">결제 모듈을 불러오는 중...</span>
      </div>
    )
  }

  return (
    <div className="bg-gray-800 rounded-xl p-6">
      <h3 className="text-xl font-bold text-white mb-6">결제 수단 선택</h3>
      
      {/* 결제 수단 선택 */}
      <div className="space-y-3 mb-6">
        {paymentMethods.map((method) => (
          <div 
            key={method.key}
            className={`border-2 rounded-lg p-4 cursor-pointer transition-colors ${
              selectedMethod === method.key
                ? 'border-blue-500 bg-blue-500/10'
                : 'border-gray-600 hover:border-gray-500'
            }`}
            onClick={() => setSelectedMethod(method.key)}
          >
            <div className="flex items-center">
              <div className={`w-4 h-4 rounded-full border-2 mr-3 ${
                selectedMethod === method.key
                  ? 'border-blue-500 bg-blue-500'
                  : 'border-gray-400'
              }`} />
              <span className="text-2xl mr-3">{method.icon}</span>
              <div>
                <p className="text-white font-medium">{method.name}</p>
                <p className="text-gray-400 text-sm">{method.description}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 결제 위젯 컨테이너 */}
      <div className="mb-6">
        <div 
          ref={cardRef} 
          className={selectedMethod === 'CARD' ? 'block' : 'hidden'}
        />
        <div 
          ref={accountRef} 
          className={selectedMethod === 'TRANSFER' ? 'block' : 'hidden'}
        />
        <div 
          ref={phoneRef} 
          className={selectedMethod === 'MOBILE_PHONE' ? 'block' : 'hidden'}
        />
        {selectedMethod === 'VIRTUAL_ACCOUNT' && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-blue-800 text-sm">
              가상계좌 발급 후 24시간 내에 입금해주세요. 
              입금 확인 시 자동으로 결제가 승인됩니다.
            </p>
          </div>
        )}
      </div>

      {/* 에러 메시지 */}
      {error && (
        <div className="bg-red-600/10 border border-red-600/20 rounded-lg p-4 mb-6">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {/* 결제 버튼 */}
      <button
        onClick={handlePayment}
        disabled={loading}
        className={`w-full py-4 px-6 rounded-lg font-semibold text-lg transition-all duration-200 ${
          loading
            ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
            : 'bg-blue-600 hover:bg-blue-500 text-white'
        }`}
      >
        {loading ? (
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-400 mr-2"></div>
            결제 처리 중...
          </div>
        ) : (
          `${amount.toLocaleString()}원 결제하기`
        )}
      </button>

      {/* 이용약관 */}
      <div className="mt-6 text-center">
        <p className="text-gray-400 text-xs">
          결제 진행시{' '}
          <a href="#" className="text-blue-400 hover:text-blue-300 underline">
            이용약관
          </a>
          {' '}및{' '}
          <a href="#" className="text-blue-400 hover:text-blue-300 underline">
            개인정보처리방침
          </a>
          에 동의한 것으로 간주됩니다.
        </p>
      </div>
    </div>
  )
}