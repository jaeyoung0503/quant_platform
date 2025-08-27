// pages/api/subscription/status.ts
import { NextApiRequest, NextApiResponse } from 'next';
import { SubscriptionService } from '../../../services/SubscriptionService';
import { ApiResponse, Subscription } from '../../../types/payment';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<ApiResponse<Subscription>>
) {
  if (req.method !== 'GET') {
    return res.status(405).json({
      success: false,
      error: 'Method not allowed'
    });
  }

  try {
    const { userId } = req.query;

    if (!userId || typeof userId !== 'string') {
      return res.status(400).json({
        success: false,
        error: '사용자 ID가 필요합니다.'
      });
    }

    const subscriptionService = new SubscriptionService();
    const activeSubscription = await subscriptionService.getActiveSubscription(userId);

    if (!activeSubscription) {
      return res.status(200).json({
        success: true,
        data: null,
        message: '활성 구독이 없습니다.'
      });
    }

    res.status(200).json({
      success: true,
      data: activeSubscription,
      message: '구독 정보를 조회했습니다.'
    });

  } catch (error) {
    console.error('Subscription status error:', error);
    res.status(500).json({
      success: false,
      error: '구독 상태 조회 중 오류가 발생했습니다.'
    });
  }
}