// pages/api/payment/request.ts
import { NextApiRequest, NextApiResponse } from 'next';
import { PaymentService } from '../../../services/PaymentService';
import { PaymentRequest, ApiResponse, PaymentResponse } from '../../../types/payment';
import { SUBSCRIPTION_PLANS } from '../../../config/payment';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<ApiResponse<PaymentResponse>>
) {
  if (req.method !== 'POST') {
    return res.status(405).json({
      success: false,
      error: 'Method not allowed'
    });
  }

  try {
    const { planId, userId } = req.body;

    // 입력 검증
    if (!planId || !userId) {
      return res.status(400).json({
        success: false,
        error: '필수 파라미터가 누락되었습니다.'
      });
    }

    // 플랜 유효성 검사
    const plan = SUBSCRIPTION_PLANS.find(p => p.id === planId);
    if (!plan) {
      return res.status(400).json({
        success: false,
        error: '유효하지 않은 플랜입니다.'
      });
    }

    // 결제 요청 생성
    const paymentRequest: PaymentRequest = {
      planId,
      userId,
      successUrl: `${process.env.NEXT_PUBLIC_BASE_URL}/payment/success`,
      failUrl: `${process.env.NEXT_PUBLIC_BASE_URL}/payment/fail`,
    };

    const paymentService = new PaymentService();
    const paymentResponse = await paymentService.createPaymentRequest(paymentRequest);

    res.status(200).json({
      success: true,
      data: paymentResponse,
      message: '결제 요청이 생성되었습니다.'
    });

  } catch (error) {
    console.error('Payment request error:', error);
    res.status(500).json({
      success: false,
      error: '결제 요청 처리 중 오류가 발생했습니다.'
    });
  }
}