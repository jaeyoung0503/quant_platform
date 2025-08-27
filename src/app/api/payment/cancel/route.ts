import { NextRequest, NextResponse } from 'next/server'

const TOSS_SECRET_KEY = process.env.TOSS_SECRET_KEY || 'test_sk_zXLkKEypNArWmo50nX3lmeaxYG5R'
const TOSS_PAYMENTS_BASE_URL = 'https://api.tosspayments.com/v1/payments'

export async function POST(request: NextRequest) {
  try {
    const { paymentKey, cancelReason } = await request.json()

    if (!paymentKey) {
      return NextResponse.json({
        success: false,
        error: 'paymentKey가 필요합니다.'
      }, { status: 400 })
    }

    // 토스페이먼츠 결제 취소 요청
    const response = await fetch(`${TOSS_PAYMENTS_BASE_URL}/${paymentKey}/cancel`, {
      method: 'POST',
      headers: {
        'Authorization': `Basic ${Buffer.from(TOSS_SECRET_KEY + ':').toString('base64')}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        cancelReason: cancelReason || '고객 요청'
      })
    })

    const cancelData = await response.json()

    if (!response.ok) {
      console.error('토스페이먼츠 결제 취소 실패:', cancelData)
      return NextResponse.json({
        success: false,
        error: cancelData.message || '결제 취소에 실패했습니다.'
      }, { status: response.status })
    }

    console.log('결제 취소 완료:', {
      paymentKey: cancelData.paymentKey,
      status: cancelData.status,
      cancelAmount: cancelData.cancelAmount
    })

    return NextResponse.json({
      success: true,
      data: cancelData
    })

  } catch (error) {
    console.error('결제 취소 API 오류:', error)
    return NextResponse.json({
      success: false,
      error: '서버 오류가 발생했습니다.'
    }, { status: 500 })
  }
}