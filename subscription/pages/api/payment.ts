// pages/api/payment.ts - 통합 결제 API
import { NextApiRequest, NextApiResponse } from 'next';
import { createPayment, verifyPayment, cancelPayment, verifyWebhookSignature } from '../../lib/payment';
import { PLANS } from '../../lib/config';
import { ApiResponse, PaymentResponse } from '../../lib/types';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<ApiResponse>
) {
  const { method } = req;

  // CORS 헤더 설정
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  try {
    switch (method) {
      case 'POST':
        await handlePost(req, res);
        break;
      case 'PUT':
        await handlePut(req, res);
        break;
      case 'DELETE':
        await handleDelete(req, res);
        break;
      default:
        res.setHeader('Allow', ['POST', 'PUT', 'DELETE']);
        res.status(405).json({ 
          success: false,
          error: `Method ${method} Not Allowed` 
        });
    }
  } catch (error) {
    console.error('API error:', error);
    res.status(500).json({ 
      success: false,
      error: '서버 오류가 발생했습니다.',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}

// POST: 결제 요청 생성 또는 웹훅 처리
async function handlePost(req: NextApiRequest, res: NextApiResponse<ApiResponse>) {
  const { action } = req.query;

  // 웹훅 처리
  if (action === 'webhook') {
    await handleWebhook(req, res);
    return;
  }

  // 결제 요청 생성
  const { planId, customerName, customerEmail } = req.body;

  // 입력 검증
  if (!planId) {
    return res.status(400).json({ 
      success: false,
      error: '플랜 ID가 필요합니다.' 
    });
  }

  // 플랜 유효성 검사
  const plan = PLANS.find(p => p.id === planId);
  if (!plan) {
    return res.status(400).json({ 
      success: false,
      error: '유효하지 않은 플랜입니다.' 
    });
  }

  // 결제 요청 생성
  const paymentRequest = {
    planId,
    amount: plan.price,
    customerName: customerName || '고객',
    customerEmail: customerEmail || 'customer@example.com',
  };

  const result = await createPayment(paymentRequest);

  if (result.success) {
    res.status(200).json({
      success: true,
      data: result,
      message: result.message
    });
  } else {
    res.status(400).json({
      success: false,
      error: result.error
    });
  }
}

// PUT: 결제 검증
async function handlePut(req: NextApiRequest, res: NextApiResponse<ApiResponse>) {
  const { paymentKey, orderId, amount } = req.body;

  // 입력 검증
  if (!paymentKey || !orderId || !amount) {
    return res.status(400).json({ 
      success: false,
      error: '필수 파라미터가 누락되었습니다. (paymentKey, orderId, amount)' 
    });
  }

  // 결제 검증
  const result = await verifyPayment({ paymentKey, orderId, amount });

  if (result.success) {
    res.status(200).json({
      success: true,
      data: result,
      message: result.message
    });
  } else {
    res.status(400).json({
      success: false,
      error: result.error
    });
  }
}

// DELETE: 결제 취소
async function handleDelete(req: NextApiRequest, res: NextApiResponse<ApiResponse>) {
  const { paymentKey } = req.body;

  // 입력 검증
  if (!paymentKey) {
    return res.status(400).json({ 
      success: false,
      error: 'paymentKey가 필요합니다.' 
    });
  }

  // 결제 취소
  const result = await cancelPayment(paymentKey);

  if (result.success) {
    res.status(200).json({
      success: true,
      data: result,
      message: result.message
    });
  } else {
    res.status(400).json({
      success: false,
      error: result.error
    });
  }
}

// 웹훅 처리
async function handleWebhook(req: NextApiRequest, res: NextApiResponse<ApiResponse>) {
  try {
    const signature = req.headers['x-tosspayments-signature'] as string;
    const payload = JSON.stringify(req.body);

    // 웹훅 서명 검증
    if (!signature || !verifyWebhookSignature(signature, payload)) {
      console.error('Invalid webhook signature');
      return res.status(401).json({ 
        success: false,
        error: 'Invalid signature' 
      });
    }

    const { eventType, data } = req.body;

    // 웹훅 이벤트 처리
    switch (eventType) {
      case 'Payment.PaymentSuccess':
        console.log('✅ Payment success webhook received:', {
          orderId: data.orderId,
          paymentKey: data.paymentKey,
          amount: data.totalAmount,
          method: data.method,
          approvedAt: data.approvedAt,
        });
        
        // MVP에서는 로깅만 수행
        // 실제 서비스에서는 데이터베이스 업데이트, 이메일 발송 등 수행
        break;
      
      case 'Payment.PaymentCanceled':
        console.log('❌ Payment canceled webhook received:', {
          orderId: data.orderId,
          paymentKey: data.paymentKey,
          cancelReason: data.cancelReason,
          canceledAt: data.canceledAt,
        });
        break;
      
      case 'Payment.PaymentFailed':
        console.log('⚠️ Payment failed webhook received:', {
          orderId: data.orderId,
          paymentKey: data.paymentKey,
          failReason: data.failReason,
          failedAt: data.failedAt,
        });
        break;
      
      default:
        console.log('🔍 Unhandled webhook event:', eventType, data);
    }

    res.status(200).json({ 
      success: true,
      message: 'Webhook processed successfully'
    });

  } catch (error) {
    console.error('Webhook processing error:', error);
    res.status(500).json({ 
      success: false,
      error: 'Webhook processing failed' 
    });
  }
} 
