// app/api/payment/webhook/route.ts

import { NextRequest, NextResponse } from 'next/server'
import { tossPayments } from '@/lib/toss'
import { getOrderInfo, updateOrderStatus } from '../prepare/route'

export async function POST(request: NextRequest) {
  try {
    // 웹훅 페이로드 읽기
    const payload = await request.text()
    const signature = request.headers.get('toss-signature') || ''

    // 웹훅 서명 검증
    if (!tossPayments.verifyWebhook(payload, signature)) {
      console.error('웹훅 서명 검증 실패')
      return NextResponse.json(
        { error: 'Invalid signature' },
        { status: 401 }
      )
    }

    // 페이로드 파싱
    const webhookData = JSON.parse(payload)
    const { eventType, data: paymentData } = webhookData

    console.log(`웹훅 수신: ${eventType}`, paymentData)

    switch (eventType) {
      case 'PAYMENT_STATUS_CHANGED':
        await handlePaymentStatusChanged(paymentData)
        break
        
      case 'PAYMENT_CANCELED':
        await handlePaymentCanceled(paymentData)
        break
        
      case 'PAYMENT_FAILED':
        await handlePaymentFailed(paymentData)
        break
        
      default:
        console.log(`처리되지 않은 웹훅 이벤트: ${eventType}`)
    }

    // 성공 응답 (토스페이먼츠에서 웹훅 재전송 방지)
    return NextResponse.json({ success: true })

  } catch (error) {
    console.error('웹훅 처리 오류:', error)
    return NextResponse.json(
      { error: 'Webhook processing failed' },
      { status: 500 }
    )
  }
}

// 결제 상태 변경 처리
async function handlePaymentStatusChanged(paymentData: any) {
  const { orderId, status, paymentKey } = paymentData

  try {
    // 주문 정보 조회
    const orderInfo = getOrderInfo(orderId)
    if (!orderInfo) {
      console.error(`주문 정보 없음: ${orderId}`)
      return
    }

    console.log(`결제 상태 변경: ${orderId} -> ${status}`)

    switch (status) {
      case 'DONE':
        // 결제 완료
        updateOrderStatus(orderId, 'confirmed')
        
        // 멤버십 업그레이드 (중복 방지)
        if (orderInfo.status !== 'confirmed') {
          await upgradeUserMembership(orderInfo.planName, orderInfo.period)
          
          // 완료 알림 이메일 발송
          await sendPaymentCompleteEmail(orderInfo)
        }
        break
        
      case 'PARTIAL_CANCELED':
      case 'CANCELED':
        // 결제 취소
        updateOrderStatus(orderId, 'failed')
        await handleMembershipDowngrade(orderInfo)
        break
        
      case 'FAILED':
        // 결제 실패
        updateOrderStatus(orderId, 'failed')
        break
    }

    // 결제 상세 정보 동기화
    if (paymentKey) {
      await syncPaymentDetails(paymentKey, orderId)
    }

  } catch (error) {
    console.error('결제 상태 변경 처리 오류:', error)
  }
}

// 결제 취소 처리
async function handlePaymentCanceled(paymentData: any) {
  const { orderId, cancelReason, canceledAt } = paymentData

  try {
    console.log(`결제 취소: ${orderId}, 사유: ${cancelReason}`)
    
    const orderInfo = getOrderInfo(orderId)
    if (orderInfo) {
      updateOrderStatus(orderId, 'failed')
      
      // 멤버십 다운그레이드
      await handleMembershipDowngrade(orderInfo)
      
      // 취소 알림 이메일
      await sendPaymentCancelEmail(orderInfo, cancelReason)
    }

  } catch (error) {
    console.error('결제 취소 처리 오류:', error)
  }
}

// 결제 실패 처리
async function handlePaymentFailed(paymentData: any) {
  const { orderId, failure } = paymentData

  try {
    console.log(`결제 실패: ${orderId}`, failure)
    
    const orderInfo = getOrderInfo(orderId)
    if (orderInfo) {
      updateOrderStatus(orderId, 'failed')
      
      // 실패 알림 (선택사항)
      await sendPaymentFailEmail(orderInfo, failure)
    }

  } catch (error) {
    console.error('결제 실패 처리 오류:', error)
  }
}

// 결제 상세 정보 동기화
async function syncPaymentDetails(paymentKey: string, orderId: string) {
  try {
    const paymentDetails = await tossPayments.getPayment(paymentKey)
    
    // 실제 환경에서는 데이터베이스에 상세 정보 저장
    console.log(`결제 정보 동기화: ${orderId}`, {
      method: paymentDetails.method,
      card: paymentDetails.card?.company,
      approvedAt: paymentDetails.approvedAt
    })
    
  } catch (error) {
    console.error('결제 정보 동기화 오류:', error)
  }
}

// 멤버십 업그레이드
async function upgradeUserMembership(planName: string, period: string) {
  // 실제 구현에서는 데이터베이스 업데이트
  console.log(`멤버십 업그레이드 실행: ${planName} (${period})`)
  
  try {
    // 1. 사용자 멤버십 정보 업데이트
    // 2. 구독 만료일 계산 및 설정
    // 3. 기능 권한 업데이트
    
    const expiryDate = calculateExpiryDate(period)
    console.log(`새로운 만료일: ${expiryDate}`)
    
  } catch (error) {
    console.error('멤버십 업그레이드 오류:', error)
    throw error
  }
}

// 멤버십 다운그레이드 처리
async function handleMembershipDowngrade(orderInfo: any) {
  console.log(`멤버십 다운그레이드: ${orderInfo.orderId}`)
  
  try {
    // 1. 사용자를 이전 플랜으로 되돌리기
    // 2. 권한 제한
    // 3. 환불 처리 (필요시)
    
  } catch (error) {
    console.error('멤버십 다운그레이드 오류:', error)
  }
}

// 만료일 계산
function calculateExpiryDate(period: string): Date {
  const now = new Date()
  
  if (period === 'monthly') {
    return new Date(now.getFullYear(), now.getMonth() + 1, now.getDate())
  } else if (period === 'quarterly') {
    return new Date(now.getFullYear(), now.getMonth() + 3, now.getDate())
  }
  
  return now
}

// 이메일 발송 함수들 (실제 구현 필요)
async function sendPaymentCompleteEmail(orderInfo: any) {
  console.log(`결제 완료 이메일 발송: ${orderInfo.customerEmail}`)
  // 실제 이메일 발송 로직 구현
}

async function sendPaymentCancelEmail(orderInfo: any, reason: string) {
  console.log(`결제 취소 이메일 발송: ${orderInfo.customerEmail}`)
  // 실제 이메일 발송 로직 구현
}

async function sendPaymentFailEmail(orderInfo: any, failure: any) {
  console.log(`결제 실패 이메일 발송: ${orderInfo.customerEmail}`)
  // 실제 이메일 발송 로직 구현 (선택사항)
}