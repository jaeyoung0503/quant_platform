export interface TossPaymentsInstance {
  requestPayment(method: string, options: PaymentRequest): Promise<void>
}

export interface PaymentRequest {
  amount: number
  orderId: string
  orderName: string
  customerName: string
  customerEmail: string
  successUrl: string
  failUrl: string
}

export interface PaymentResult {
  paymentKey: string
  orderId: string
  orderName: string
  method: string
  totalAmount: number
  status: string
  approvedAt: string
  receipt?: {
    url: string
  }
  card?: {
    company: string
    number: string
    installmentPlanMonths: number
  }
}