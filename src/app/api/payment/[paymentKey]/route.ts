import { NextRequest, NextResponse } from 'next/server'

const TOSS_SECRET_KEY = process.env.TOSS_SECRET_KEY || 'test_sk_zXLkKEypNArWmo50nX3lmeaxYG5R'
const TOSS_PAYMENTS_BASE_URL = 'https://api.tosspayments.com/v1/payments'

export async function GET(
  request: NextRequest,
  { params }: { params: { paymentKey: string } }
) {
  try {
    const { paymentKey } = params

    if (!paymentKey) {
      return NextResponse.json({
        success: false,
        error: 'paymentKey가 필요합니다.'
      }, { status: 400 })
    }

    // 토스페이먼츠 결제 조회 요청
    const response = await fetch(`${TOSS_PAYMENTS_BASE_URL}/${paymentKey}`, {
      method: 'GET',
      headers: {
        'Authorization': `Basic ${Buffer.from(TOSS_SECRET_KEY + ':').toString('base64')}`,
        'Content-Type': 'application/json',
      }
    })

    const paymentData = await response.json()

    if (!response.ok) {
      console.error('토스페이먼츠 결제 조회 실패:', paymentData)
      return NextResponse.json({
        success: false,
        error: paymentData.message || '결제 조회에 실패했습니다.'
      }, { status: response.status })
    }

    return NextResponse.json({
      success: true,
      data: paymentData
    })

  } catch (error) {
    console.error('결제 조회 API 오류:', error)
    return NextResponse.json({
      success: false,
      error: '서버 오류가 발생했습니다.'
    }, { status: 500 })
  }
}