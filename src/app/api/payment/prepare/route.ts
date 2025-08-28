// app/api/payment/prepare/route.ts

import { NextRequest, NextResponse } from 'next/server'
import { generateOrderId, validateAmount, checkMinimumAmount } from '@/lib/toss'

// 결제 준비 요청 타입
interface PreparePaymentRequest {
  planName: string
  period: string
  amount: number
  customerEmail?: string
  customerName?: string
}

// 메모리 저장소 (실제 환경에서는 데이터베이스 사용)
const pendingPayments = new Map<string, {
  orderId: string
  planName: string
  period: string
  amount: number
  status: 'pending' | 'confirmed' | 'failed'
  createdAt: Date
  customerEmail?: string
  customerName?: string
}>()

export async function POST(request: NextRequest) {
  try {
    const body: PreparePaymentRequest = await request.json()
    const { planName, period, amount, customerEmail, customerName } = body

    // 유효성 검사
    if (!planName || !period || !amount) {
      return NextResponse.json(
        { error: '필수 파라미터가 누락되었습니다.' },
        { status: 400 }
      )
    }

    // 금액 유효성 검사
    if (!validateAmount(amount)) {
      return NextResponse.json(
        { error: '올바르지 않은 금액입니다.' },
        { status: 400 }
      )
    }

    // 최소 금액 체크
    if (!checkMinimumAmount(amount, 'card')) {
      return NextResponse.json(
        { error: '최소 결제 금액은 100원입니다.' },
        { status: 400 }
      )
    }

    // 플랜별 금액 검증
    const validAmounts = {
      'advanced-monthly': 9900,
      'advanced-quarterly': 8910, // 10% 할인
      'premium-monthly': 19900,
      'premium-quarterly': 17910, // 10% 할인
    }

    const planKey = `${planName.toLowerCase()}-${period}` as keyof typeof validAmounts
    if (validAmounts[planKey] && validAmounts[planKey] !== amount) {
      return NextResponse.json(
        { error: '금액이 일치하지 않습니다.' },
        { status: 400 }
      )
    }

    // 주문 ID 생성
    const orderId = generateOrderId()

    // 주문 정보 저장 (실제 환경에서는 데이터베이스에 저장)
    const orderInfo = {
      orderId,
      planName,
      period,
      amount,
      status: 'pending' as const,
      createdAt: new Date(),
      customerEmail,
      customerName,
    }

    pendingPayments.set(orderId, orderInfo)

    // 5분 후 자동 만료 (실제 환경에서는 크론 잡 사용)
    setTimeout(() => {
      const order = pendingPayments.get(orderId)
      if (order && order.status === 'pending') {
        pendingPayments.delete(orderId)
        console.log(`주문 ${orderId} 자동 만료`)
      }
    }, 5 * 60 * 1000)

    // 주문명 생성
    const planDisplayName = {
      basic: 'Basic',
      advanced: 'Advanced', 
      premium: 'Premium'
    }[planName.toLowerCase()] || planName

    const periodDisplayName = period === 'monthly' ? '월간' : '3개월'
    const orderName = `${planDisplayName} 플랜 - ${periodDisplayName}`

    return NextResponse.json({
      success: true,
      data: {
        orderId,
        orderName,
        amount,
        customerEmail: customerEmail || 'guest@intelliquant.ai',
        customerName: customerName || '게스트',
      }
    })

  } catch (error) {
    console.error('결제 준비 오류:', error)
    return NextResponse.json(
      { error: '결제 준비 중 오류가 발생했습니다.' },
      { status: 500 }
    )
  }
}

// 주문 정보 조회 API
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const orderId = searchParams.get('orderId')

    if (!orderId) {
      return NextResponse.json(
        { error: '주문 ID가 필요합니다.' },
        { status: 400 }
      )
    }

    const orderInfo = pendingPayments.get(orderId)
    
    if (!orderInfo) {
      return NextResponse.json(
        { error: '주문 정보를 찾을 수 없습니다.' },
        { status: 404 }
      )
    }

    return NextResponse.json({
      success: true,
      data: orderInfo
    })

  } catch (error) {
    console.error('주문 조회 오류:', error)
    return NextResponse.json(
      { error: '주문 조회 중 오류가 발생했습니다.' },
      { status: 500 }
    )
  }
}

// 주문 상태 업데이트 (내부 사용)
export function updateOrderStatus(
  orderId: string, 
  status: 'pending' | 'confirmed' | 'failed'
) {
  const order = pendingPayments.get(orderId)
  if (order) {
    order.status = status
    pendingPayments.set(orderId, order)
  }
}

// 주문 정보 조회 (내부 사용)
export function getOrderInfo(orderId: string) {
  return pendingPayments.get(orderId)
}