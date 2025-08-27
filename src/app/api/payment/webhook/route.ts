import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const webhookData = await request.json()
    
    console.log('토스페이먼츠 웹훅 수신:', webhookData)

    // 웹훅 데이터 검증
    const { eventType, data } = webhookData

    switch (eventType) {
      case 'PAYMENT_STATUS_CHANGED':
        await handlePaymentStatusChange(data)
        break
      
      case 'PAYMENT_WAITING_FOR_DEPOSIT':
        await handleVirtualAccountWaiting(data)
        break
        
      case 'PAYMENT_EXPIRED':
        await handlePaymentExpired(data)
        break
        
      default:
        console.log(`처리되지 않은 웹훅 이벤트: ${eventType}`)
    }

    return NextResponse.json({ success: true })

  } catch (error) {
    console.error('웹훅 처리 오류:', error)
    return NextResponse.json({
      success: false,
      error: '웹훅 처리 중 오류가 발생했습니다.'
    }, { status: 500 })
  }
}

async function handlePaymentStatusChange(data: any) {
  console.log('결제 상태 변경:', data)
}

async function handleVirtualAccountWaiting(data: any) {
  console.log('가상계좌 입금 대기:', data)
}

async function handlePaymentExpired(data: any) {
  console.log('결제 만료:', data)
}