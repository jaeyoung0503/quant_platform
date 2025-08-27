// lib/payment.ts - MVP 결제 로직
import { PaymentRequest, PaymentResponse, PaymentVerification } from './types';
import { TOSS_CONFIG } from './config';

export function generateOrderId(planId: string): string {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substr(2, 9);
  return `ORDER_${planId}_${timestamp}_${random}`;
}

export async function createPayment(request: PaymentRequest): Promise<PaymentResponse> {
  try {
    const orderId = generateOrderId(request.planId);
    
    // MVP에서는 클라이언트에서 직접 결제 위젯 호출하므로
    // 단순히 주문 ID만 생성하여 반환
    return {
      success: true,
      orderId,
      paymentUrl: '/checkout',
      message: '결제 준비 완료'
    };
  } catch (error) {
    console.error('Payment creation error:', error);
    return {
      success: false,
      error: '결제 요청 생성에 실패했습니다.'
    };
  }
}

export async function verifyPayment(verification: PaymentVerification): Promise<PaymentResponse> {
  try {
    const { paymentKey, orderId, amount } = verification;
    
    // 토스페이먼츠에서 결제 정보 확인
    const response = await fetch(`${TOSS_CONFIG.apiUrl}/v1/payments/${paymentKey}`, {
      method: 'GET',
      headers: {
        'Authorization': `Basic ${Buffer.from(TOSS_CONFIG.secretKey + ':').toString('base64')}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'Payment verification failed');
    }

    const paymentData = await response.json();
    
    // 결제 정보 검증
    if (paymentData.orderId !== orderId || paymentData.totalAmount !== amount) {
      throw new Error('결제 정보가 일치하지 않습니다.');
    }

    if (paymentData.status !== 'DONE') {
      throw new Error('결제가 완료되지 않았습니다.');
    }

    // MVP에서는 간단한 로깅만
    console.log('Payment verified successfully:', {
      paymentKey,
      orderId,
      amount,
      method: paymentData.method,
      approvedAt: paymentData.approvedAt,
    });

    return {
      success: true,
      message: '결제가 성공적으로 완료되었습니다.'
    };

  } catch (error) {
    console.error('Payment verification error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : '결제 검증에 실패했습니다.'
    };
  }
}

export async function cancelPayment(paymentKey: string): Promise<PaymentResponse> {
  try {
    const response = await fetch(`${TOSS_CONFIG.apiUrl}/v1/payments/${paymentKey}/cancel`, {
      method: 'POST',
      headers: {
        'Authorization': `Basic ${Buffer.from(TOSS_CONFIG.secretKey + ':').toString('base64')}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        cancelReason: '고객 요청에 의한 취소',
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'Payment cancellation failed');
    }

    const cancelData = await response.json();
    
    console.log('Payment cancelled successfully:', {
      paymentKey,
      cancelledAt: cancelData.cancelledAt,
      cancelReason: cancelData.cancelReason,
    });

    return {
      success: true,
      message: '결제가 성공적으로 취소되었습니다.'
    };

  } catch (error) {
    console.error('Payment cancellation error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : '결제 취소에 실패했습니다.'
    };
  }
}

// 토스페이먼츠 웹훅 검증
export function verifyWebhookSignature(signature: string, payload: string): boolean {
  try {
    const crypto = require('crypto');
    const expectedSignature = crypto
      .createHmac('sha256', TOSS_CONFIG.secretKey)
      .update(payload)
      .digest('base64');
    
    return signature === expectedSignature;
  } catch (error) {
    console.error('Webhook verification error:', error);
    return false;
  }
}

// 결제 정보 조회 (추가 기능)
export async function getPaymentDetails(paymentKey: string) {
  try {
    const response = await fetch(`${TOSS_CONFIG.apiUrl}/v1/payments/${paymentKey}`, {
      method: 'GET',
      headers: {
        'Authorization': `Basic ${Buffer.from(TOSS_CONFIG.secretKey + ':').toString('base64')}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Failed to get payment details');
    }

    const paymentData = await response.json();
    
    return {
      success: true,
      data: paymentData,
      message: '결제 정보를 성공적으로 조회했습니다.'
    };

  } catch (error) {
    console.error('Get payment details error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : '결제 정보 조회에 실패했습니다.'
    };
  }
}