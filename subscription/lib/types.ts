// lib/types.ts - MVP 타입 정의
export interface Plan {
  id: string;
  name: string;
  price: number;
  features: string[];
  popular?: boolean;
}

export interface PaymentRequest {
  planId: string;
  amount: number;
  customerName?: string;
  customerEmail?: string;
}

export interface PaymentResponse {
  success: boolean;
  paymentUrl?: string;
  orderId?: string;
  clientSecret?: string;
  error?: string;
  message?: string;
}

export interface PaymentVerification {
  paymentKey: string;
  orderId: string;
  amount: number;
}

export interface TossPaymentWidget {
  requestPayment: (options: {
    amount: number;
    orderId: string;
    orderName: string;
    customerName?: string;
    customerEmail?: string;
    successUrl: string;
    failUrl: string;
  }) => Promise<void>;
  renderPaymentMethods: (selector: string, options: any, variant?: any) => Promise<void>;
  renderAgreement: (selector: string, options?: any) => Promise<void>;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

declare global {
  interface Window {
    PaymentWidget: (clientKey: string, customerKey: string) => TossPaymentWidget;
  }
}
