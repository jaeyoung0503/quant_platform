// lib/toss.ts

export interface PaymentRequest {
  amount: number
  orderId: string
  orderName: string
  customerEmail?: string
  customerName?: string
}

export interface TossPaymentResponse {
  paymentKey: string
  orderId: string
  orderName: string
  method: string
  totalAmount: number
  balanceAmount: number
  status: string
  requestedAt: string
  approvedAt: string
  card?: {
    amount: number
    company: string
    number: string
    installmentPlanMonths: number
    approveNo: string
    useCardPoint: boolean
    cardType: string
    ownerType: string
    acquireStatus: string
    receiptUrl: string
  }
  virtualAccount?: {
    amount: number
    accountNumber: string
    bankCode: string
    customerName: string
    dueDate: string
    refundStatus: string
    expired: boolean
    settlementStatus: string
    refundReceiveAccount: any
  }
  transfer?: {
    amount: number
    bankCode: string
    settlementStatus: string
  }
  mobilePhone?: {
    amount: number
    customerMobilePhone: string
    settlementStatus: string
    receiptUrl: string
  }
  giftCertificate?: {
    amount: number
    approveNo: string
    settlementStatus: string
  }
  cashReceipt?: {
    type: string
    receiptKey: string
    issueNumber: string
    receiptUrl: string
    amount: number
    taxFreeAmount: number
  }
  cashReceipts?: Array<{
    receiptKey: string
    orderId: string
    orderName: string
    type: string
    issueNumber: string
    receiptUrl: string
    businessNumber: string
    transactionType: string
    amount: number
    taxFreeAmount: number
    issueStatus: string
    failure: any
    customerIdentityNumber: string
    requestedAt: string
  }>
  discount?: {
    amount: number
  }
  cancels?: Array<{
    cancelAmount: number
    cancelReason: string
    taxFreeAmount: number
    taxAmount: number
    refundableAmount: number
    easyPayDiscountAmount: number
    canceledAt: string
    transactionKey: string
    receiptKey: string
  }>
  secret?: string
  type: string
  easyPay?: {
    provider: string
    amount: number
    discountAmount: number
  }
  country: string
  failure?: {
    code: string
    message: string
  }
  isPartialCancelable: boolean
  receipt: {
    url: string
  }
  checkout: {
    url: string
  }
  currency: string
  culture: string
  suppliedAmount: number
  vat: number
  taxFreeAmount: number
}

class TossPayments {
  private clientKey: string
  private secretKey: string
  private baseUrl: string

  constructor() {
    this.clientKey = process.env.NEXT_PUBLIC_TOSS_CLIENT_KEY!
    this.secretKey = process.env.TOSS_SECRET_KEY!
    this.baseUrl = 'https://api.tosspayments.com/v1'
    
    if (!this.clientKey || !this.secretKey) {
      throw new Error('토스페이먼츠 키가 설정되지 않았습니다.')
    }
  }

  // 클라이언트 키 반환 (공개 키)
  getClientKey(): string {
    return this.clientKey
  }

  // 결제 승인
  async confirmPayment(
    paymentKey: string, 
    orderId: string, 
    amount: number
  ): Promise<TossPaymentResponse> {
    const url = `${this.baseUrl}/payments/confirm`
    const authorization = Buffer.from(`${this.secretKey}:`).toString('base64')

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Basic ${authorization}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        paymentKey,
        orderId,
        amount,
      }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(`결제 승인 실패: ${error.message}`)
    }

    return await response.json()
  }

  // 결제 조회
  async getPayment(paymentKey: string): Promise<TossPaymentResponse> {
    const url = `${this.baseUrl}/payments/${paymentKey}`
    const authorization = Buffer.from(`${this.secretKey}:`).toString('base64')

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Basic ${authorization}`,
      },
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(`결제 조회 실패: ${error.message}`)
    }

    return await response.json()
  }

  // 결제 취소
  async cancelPayment(
    paymentKey: string,
    cancelReason: string,
    cancelAmount?: number
  ): Promise<TossPaymentResponse> {
    const url = `${this.baseUrl}/payments/${paymentKey}/cancel`
    const authorization = Buffer.from(`${this.secretKey}:`).toString('base64')

    const body: any = { cancelReason }
    if (cancelAmount) {
      body.cancelAmount = cancelAmount
    }

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Basic ${authorization}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(`결제 취소 실패: ${error.message}`)
    }

    return await response.json()
  }

  // 웹훅 서명 검증
  verifyWebhook(payload: string, signature: string): boolean {
    const crypto = require('crypto')
    const webhookSecret = process.env.TOSS_WEBHOOK_SECRET
    
    if (!webhookSecret) {
      console.warn('웹훅 시크릿이 설정되지 않았습니다.')
      return true // 개발 환경에서는 검증 스킵
    }

    const expectedSignature = crypto
      .createHmac('sha256', webhookSecret)
      .update(payload)
      .digest('hex')

    return crypto.timingSafeEqual(
      Buffer.from(signature, 'hex'),
      Buffer.from(expectedSignature, 'hex')
    )
  }
}

// 싱글톤 인스턴스
export const tossPayments = new TossPayments()

// 주문 ID 생성 유틸리티
export function generateOrderId(): string {
  const timestamp = Date.now()
  const random = Math.random().toString(36).substring(2, 15)
  return `order_${timestamp}_${random}`
}

// 금액 유효성 검사
export function validateAmount(amount: number): boolean {
  return Number.isInteger(amount) && amount > 0 && amount <= 100000000 // 1억원 한도
}

// 결제 방법별 최소 금액 체크
export function checkMinimumAmount(amount: number, method: string): boolean {
  const minimums = {
    card: 100, // 카드 최소 100원
    virtualAccount: 1000, // 가상계좌 최소 1000원
    transfer: 1000, // 계좌이체 최소 1000원
    mobilePhone: 1000, // 휴대폰 최소 1000원
  }
  
  return amount >= (minimums[method as keyof typeof minimums] || 100)
}