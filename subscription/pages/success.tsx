// pages/success.tsx - 결제 성공 페이지
import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import { PLANS } from '../lib/config';

interface VerificationState {
  isVerifying: boolean;
  isVerified: boolean;
  error: string | null;
  paymentInfo?: {
    orderId: string;
    paymentKey: string;
    amount: number;
    planName?: string;
  };
}

const PaymentSuccessPage: React.FC = () => {
  const router = useRouter();
  const [state, setState] = useState<VerificationState>({
    isVerifying: true,
    isVerified: false,
    error: null,
  });

  useEffect(() => {
    const { orderId, paymentKey, amount } = router.query;

    // URL 파라미터 확인
    if (!orderId || !paymentKey || !amount) {
      if (router.isReady) {
        setState({
          isVerifying: false,
          isVerified: false,
          error: '결제 정보가 올바르지 않습니다.',
        });
      }
      return;
    }

    verifyPayment({
      orderId: orderId as string,
      paymentKey: paymentKey as string,
      amount: Number(amount),
    });
  }, [router.query, router.isReady]);

  const verifyPayment = async (paymentInfo: { orderId: string; paymentKey: string; amount: number }) => {
    try {
      setState(prev => ({ ...prev, isVerifying: true }));

      const response = await fetch('/api/payment', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(paymentInfo),
      });

      const result = await response.json();

      if (result.success) {
        // 플랜 정보 추가
        const planName = getPlanNameFromOrderId(paymentInfo.orderId);
        
        setState({
          isVerifying: false,
          isVerified: true,
          error: null,
          paymentInfo: {
            ...paymentInfo,
            planName,
          },
        });
      } else {
        setState({
          isVerifying: false,
          isVerified: false,
          error: result.error || '결제 검증에 실패했습니다.',
        });
      }
    } catch (error) {
      console.error('Payment verification error:', error);
      setState({
        isVerifying: false,
        isVerified: false,
        error: '결제 검증 중 오류가 발생했습니다.',
      });
    }
  };

  const getPlanNameFromOrderId = (orderId: string): string => {
    const planId = orderId.split('_')[1]; // ORDER_basic_timestamp_random 형식에서 planId 추출
    const plan = PLANS.find(p => p.id === planId);
    return plan ? plan.name : '구독 서비스';
  };

  const handleGoToDashboard = () => {
    // 실제 서비스에서는 대시보드로 이동
    router.push('/');
  };

  const handleGoHome = () => {
    router.push('/');
  };

  const handleViewReceipt = () => {
    // 영수증 조회 기능 (추후 구현)
    alert('영수증 조회 기능은 준비 중입니다.');
  };

  return (
    <>
      <Head>
        <title>
          {state.isVerifying ? '결제 확인 중...' : state.isVerified ? '결제 완료!' : '결제 실패'}
        </title>
        <meta name="description" content="결제 결과를 확인합니다" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="robots" content="noindex, nofollow" />
      </Head>

      <div className="min-h-screen bg-gray-50 py-12">
        <div className="max-w-md mx-auto px-4 sm:px-6 lg:px-8">
          
          {/* 검증 중 상태 */}
          {state.isVerifying && (
            <div className="bg-white shadow-lg rounded-lg p-8 text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-600 border-t-transparent mx-auto mb-6"></div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                결제를 확인하고 있습니다
              </h2>
              <p className="text-gray-600">
                잠시만 기다려주세요. 결제 정보를 안전하게 검증하고 있습니다.
              </p>
            </div>
          )}

          {/* 검증 실패 상태 */}
          {!state.isVerifying && !state.isVerified && (
            <div className="bg-white shadow-lg rounded-lg p-8 text-center">
              <div className="w-16 h-16 mx-auto bg-red-100 rounded-full flex items-center justify-center mb-6">
                <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
              
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                결제 검증에 실패했습니다
              </h2>
              
              <p className="text-gray-600 mb-6">
                {state.error || '알 수 없는 오류가 발생했습니다.'}
              </p>
              
              <div className="space-y-3">
                <button
                  onClick={() => router.push('/pricing')}
                  className="w-full py-3 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  다시 시도하기
                </button>
                
                <button
                  onClick={handleGoHome}
                  className="w-full py-3 px-4 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors font-medium"
                >
                  홈으로 돌아가기
                </button>
              </div>
            </div>
          )}

          {/* 검증 성공 상태 */}
          {!state.isVerifying && state.isVerified && state.paymentInfo && (
            <div className="bg-white shadow-lg rounded-lg p-8 text-center">
              
              {/* 성공 아이콘 */}
              <div className="w-16 h-16 mx-auto bg-green-100 rounded-full flex items-center justify-center mb-6">
                <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              
              {/* 성공 메시지 */}
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                🎉 결제가 완료되었습니다!
              </h2>
              
              <p className="text-gray-600 mb-8">
                {state.paymentInfo.planName} 구독이 활성화되었습니다.<br />
                지금부터 모든 기능을 자유롭게 이용하세요!
              </p>
              
              {/* 결제 정보 */}
              <div className="bg-gray-50 rounded-lg p-6 mb-8">
                <h3 className="font-semibold text-gray-900 mb-4">결제 정보</h3>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">구독 플랜:</span>
                    <span className="font-medium text-gray-900">{state.paymentInfo.planName}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">결제 금액:</span>
                    <span className="font-bold text-blue-600">
                      {state.paymentInfo.amount.toLocaleString()}원
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">주문번호:</span>
                    <span className="font-mono text-xs text-gray-700">
                      {state.paymentInfo.orderId}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">결제일시:</span>
                    <span className="text-gray-700">
                      {new Date().toLocaleDateString('ko-KR', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                  </div>
                </div>
              </div>
              
              {/* 액션 버튼들 */}
              <div className="space-y-3">
                <button
                  onClick={handleGoToDashboard}
                  className="w-full py-3 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-semibold text-lg"
                >
                  🚀 서비스 시작하기
                </button>
                
                <div className="grid grid-cols-2 gap-3">
                  <button
                    onClick={handleViewReceipt}
                    className="py-2 px-4 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium text-sm"
                  >
                    📄 영수증 보기
                  </button>
                  
                  <button
                    onClick={handleGoHome}
                    className="py-2 px-4 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium text-sm"
                  >
                    🏠 홈으로 가기
                  </button>
                </div>
              </div>

              {/* 추가 안내 */}
              <div className="mt-8 p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-800">
                  <strong>💡 알아두세요!</strong><br />
                  • 구독은 매월 자동으로 갱신됩니다<br />
                  • 언제든지 플랜 변경이나 해지가 가능합니다<br />
                  • 7일 이내 전액 환불 가능합니다
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default PaymentSuccessPage; 
