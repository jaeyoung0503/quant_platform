import { NextRequest, NextResponse } from 'next/server'

const TOSS_SECRET_KEY = process.env.TOSS_SECRET_KEY || 'test_sk_zXLkKEypNArWmo50nX3lmeaxYG5R'
const TOSS_PAYMENTS_BASE_URL = 'https://api.tosspayments.com/v1/payments'

export async function POST(request: NextRequest) {
  try {
    const { paymentKey, orderId, amount } = await request.json()

    if (!paymentKey || !orderId || !amount) {
      return NextResponse.json({
        success: false,
        error: '필수 파라미터가 누락되었습니다.'
      }, { status: 400 })
    }

    // 토스페이먼츠 결제 승인 요청
    const response = await fetch(`${TOSS_PAYMENTS_BASE_URL}/confirm`, {
      method: 'POST',
      headers: {
        'Authorization': `Basic ${Buffer.from(TOSS_SECRET_KEY + ':').toString('base64')}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        paymentKey,
        orderId,
        amount
      })
    })

    const paymentData = await response.json()

    if (!response.ok) {
      console.error('토스페이먼츠 결제 승인 실패:', paymentData)
      return NextResponse.json({
        success: false,
        error: paymentData.message || '결제 승인에 실패했습니다.'
      }, { status: response.status })
    }

    // 여기에서 데이터베이스에 결제 정보 저장 등의 비즈니스 로직 처리
    console.log('결제 승인 완료:', {
      orderId: paymentData.orderId,
      amount: paymentData.totalAmount,
      status: paymentData.status
    })

    return NextResponse.json({
      success: true,
      data: paymentData
    })

  } catch (error) {
    console.error('결제 승인 API 오류:', error)
    return NextResponse.json({
      success: false,
      error: '서버 오류가 발생했습니다.'
    }, { status: 500 })
  }
}