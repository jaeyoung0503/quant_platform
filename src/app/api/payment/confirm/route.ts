// app/api/payment/confirm/route.ts

import { NextRequest, NextResponse } from 'next/server'
import { tossPayments } from '@/lib/toss'
import { getOrderInfo, updateOrderStatus } from '../prepare/route'

interface ConfirmPaymentRequest {
  paymentKey: string
  orderId: string
  amount: number
}

export async function POST(request: NextRequest) {
  try {
    const body: ConfirmPaymentRequest = await request.json()
    const { paymentKey, orderId, amount } = body

    // 유효성 검사
    if (!paymentKey || !orderId || !amount) {
      return NextResponse.json(
        { 
          success: false, 
          error: '필수 파라미터가 누락되었습니다.' 
        },
        { status: 400 }
      )
    }

    // 주문 정보 확인
    const orderInfo = getOrderInfo(orderId)
    if (!orderInfo) {
      return NextResponse.json(
        { 
          success: false, 
          error: '주문 정보를 찾을 수 없습니다.' 
        },
        { status: 404 }
      )
    }

    // 결제 금액 검증
    if (orderInfo.amount !== amount) {
      console.error(`금액 불일치: 주문금액=${orderInfo.amount}, 결제금액=${amount}`)
      return NextResponse.json(
        { 
          success: false, 
          error: '결제 금액이 일치하지 않습니다.' 
        },
        { status: 400 }
      )
    }

    // 이미 처리된 주문 체크
    if (orderInfo.status !== 'pending') {
      return NextResponse.json(
        { 
          success: false, 
          error: '이미 처리된 주문입니다.' 
        },
        { status: 400 }
      )
    }

    try {
      // 토스페이먼츠 결제 승인 요청
      const paymentResult = await tossPayments.confirmPayment(
        paymentKey,
        orderId,
        amount
      )

      // 결제 성공 처리
      if (paymentResult.status === 'DONE') {
        // 주문 상태 업데이트
        updateOrderStatus(orderId, 'confirmed')

        // 멤버십 업그레이드 로직 (실제 환경에서 구현)
        await upgradeUserMembership(orderInfo.planName, orderInfo.period)

        // 성공 응답
        return NextResponse.json({
          success: true,
          data: {
            orderId: paymentResult.orderId,
            orderName: paymentResult.orderName,
            totalAmount: paymentResult.totalAmount,
            method: getPaymentMethodName(paymentResult.method),
            approvedAt: paymentResult.approvedAt,
            card: paymentResult.card ? {
              company: paymentResult.card.company,
              number: paymentResult.card.number
            } : undefined,
            receipt: paymentResult.receipt
          }
        })

      } else {
        // 결제 실패
        updateOrderStatus(orderId, 'failed')
        
        return NextResponse.json({
          success: false,
          error: `결제가 완료되지 않았습니다. (상태: ${paymentResult.status})`
        }, { status: 400 })
      }

    } catch (tossError: any) {
      console.error('토스페이먼츠 승인 오류:', tossError)
      
      // 주문 상태 업데이트
      updateOrderStatus(orderId, 'failed')

      // 토스페이먼츠 오류 메시지 파싱
      let errorMessage = '결제 승인 중 오류가 발생했습니다.'
      
      if (tossError.message) {
        if (tossError.message.includes('CARD_COMPANY_NOT_AVAILABLE')) {
          errorMessage = '카드사 서비스가 일시적으로 중단되었습니다.'
        } else if (tossError.message.includes('EXCEED_MAX_CARD_INSTALLMENT_PLAN')) {
          errorMessage = '설정 가능한 할부 개월 수를 초과했습니다.'
        } else if (tossError.message.includes('INVALID_CARD_EXPIRATION')) {
          errorMessage = '카드 유효기간이 잘못되었습니다.'
        } else if (tossError.message.includes('INVALID_STOPPED_CARD')) {
          errorMessage = '정지된 카드입니다.'
        } else if (tossError.message.includes('LIMIT_EXCEEDED')) {
          errorMessage = '한도를 초과했습니다.'
        } else if (tossError.message.includes('CARD_NOT_SUPPORTED')) {
          errorMessage = '지원하지 않는 카드입니다.'
        } else if (tossError.message.includes('INVALID_CARD_NUMBER')) {
          errorMessage = '카드번호가 잘못되었습니다.'
        }
      }

      return NextResponse.json({
        success: false,
        error: errorMessage
      }, { status: 400 })
    }

  } catch (error) {
    console.error('결제 승인 처리 오류:', error)
    return NextResponse.json(
      { 
        success: false, 
        error: '결제 승인 처리 중 시스템 오류가 발생했습니다.' 
      },
      { status: 500 }
    )
  }
}

// 결제 방법명 변환
function getPaymentMethodName(method: string): string {
  const methodMap: { [key: string]: string } = {
    '카드': '신용/체크카드',
    '가상계좌': '가상계좌',
    '계좌이체': '실시간 계좌이체',
    '휴대폰': '휴대폰 소액결제',
    'CARD': '신용/체크카드',
    'VIRTUAL_ACCOUNT': '가상계좌',
    'TRANSFER': '실시간 계좌이체',
    'MOBILE_PHONE': '휴대폰 소액결제'
  }
  
  return methodMap[method] || method
}

// 멤버십 업그레이드 로직 (실제 환경에서 구현)
async function upgradeUserMembership(planName: string, period: string) {
  // 실제 환경에서는 다음과 같은 작업을 수행:
  // 1. 사용자의 현재 멤버십 조회
  // 2. 새로운 플랜으로 업데이트
  // 3. 구독 만료일 설정
  // 4. 멤버십 히스토리 저장
  // 5. 이메일 알림 발송

  console.log(`멤버십 업그레이드: ${planName} (${period})`)
  
  // 예시 구현
  try {
    // 여기서 실제 데이터베이스 업데이트
    // await updateUserMembership(userId, planName, period)
    
    // 이메일 알림
    // await sendUpgradeEmail(userEmail, planName)
    
    console.log('멤버십 업그레이드 완료')
  } catch (error) {
    console.error('멤버십 업그레이드 오류:', error)
    // 결제는 완료되었지만 멤버십 업데이트 실패
    // 별도의 복구 로직이 필요할 수 있음
  }
}