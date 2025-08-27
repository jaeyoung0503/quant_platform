// pages/checkout.tsx - MVP 결제 페이지
import React, { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import { PLANS, TOSS_CONFIG, APP_CONFIG, TEST_USER } from '../lib/config';
import { TossPaymentWidget } from '../lib/types';

const CheckoutPage: React.FC = () => {
  const router = useRouter();
  const { orderId, planId } = router.query;
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const paymentWidgetRef = useRef<TossPaymentWidget | null>(null);
  const paymentMethodsRef = useRef<HTMLDivElement>(null);
  const agreementRef = useRef<HTMLDivElement>(null);

  const plan = PLANS.find(p => p.id === planId);

  useEffect(() => {
    if (!orderId || !planId || !plan) {
      router.push('/pricing');
      return;
    }

    // 토스페이먼츠 스크립트 로드
    const script = document.createElement('script');
    script.src = 'https://js.tosspayments.com/v1/payment-widget';
    script.async = true;
    script.onload = initializePaymentWidget;
    script.onerror = () => {
      setError('결제 시스템을 불러오는데 실패했습니다.');
      setIsLoading(false);
    };
    
    document.head.appendChild(script);

    return () => {
      if (document.head.contains(script)) {
        document.head.removeChild(script);
      }
    };
  }, [orderId, planId, plan, router]);

  const initializePaymentWidget = async () => {
    try {
      if (!TOSS_CONFIG.clientKey) {
        throw new Error('토스페이먼츠 클라이언트 키가 설정되지 않았습니다.');
      }

      // PaymentWidget 초기화
      const paymentWidget = window.PaymentWidget(TOSS_CONFIG.clientKey, TEST_USER.id);
      paymentWidgetRef.current = paymentWidget;

      // 결제 수단 위젯 렌더링
      if (paymentMethodsRef.current && plan) {
        await paymentWidget.renderPaymentMethods(
          '#payment-methods',
          { value: plan.price },
          { variantKey: 'DEFAULT' }
        );

        // 이용약관 위젯 렌더링
        if (agreementRef.current) {
          await paymentWidget.renderAgreement(
            '#agreement', 
            { variantKey: 'AGREEMENT' }
          );
        }
      }

      setIsLoading(false);
    } catch (error) {
      console.error('Payment widget initialization error:', error);
      setError(error instanceof Error ? error.message : '결제 위젯 초기화에 실패했습니다.');
      setIsLoading(false);
    }
  };

  const handlePayment = async () => {
    if (!paymentWidgetRef.current || !plan || !orderId) {
      setError('결제 정보가 올바르지 않습니다.');
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      await paymentWidgetRef.current.requestPayment({
        orderId: orderId as string,
        orderName: `${plan.name} 구독 서비스`,
        amount: plan.price,
        customerName: TEST_USER.name,
        customerEmail: TEST_USER.email,
        successUrl: `${APP_CONFIG.baseUrl}/success`,
        failUrl: `${APP_CONFIG.baseUrl}/fail`,
      });
    } catch (error) {
      console.error('Payment request error:', error);
      setError('결제 요청에 실패했습니다. 다시 시도해주세요.');
      setIsProcessing(false);
    }
  };

  // 잘못된 접근인 경우
  if (!plan && !isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            잘못된 접근입니다
          </h2>
          <button
            onClick={() => router.push('/pricing')}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            요금제 페이지로 돌아가기
          </button>
        </div>
      </div>
    );
  }

  return (
    <>
      <Head>
        <title>결제하기 - {plan?.name} 플랜</title>
        <meta name="description" content={`${plan?.name} 플랜 결제를 진행합니다`} />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          
          {/* 뒤로가기 버튼 */}
          <button
            onClick={() => router.back()}
            className="flex items-center text-gray-600 hover:text-gray-900 mb-8 transition-colors"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            돌아가기
          </button>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            
            {/* 주문 정보 사이드바 */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-lg shadow-lg p-6 sticky top-8">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">주문 요약</h3>
                
                {plan && (
                  <>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-gray-600">{plan.name} 플랜</span>
                      <span className="font-medium">{plan.price.toLocaleString()}원</span>
                    </div>
                    
                    <div className="border-t pt-2 mt-4">
                      <div className="flex justify-between items-center">
                        <span className="text-lg font-semibold text-gray-900">총 결제금액</span>
                        <span className="text-lg font-bold text-blue-600">
                          {plan.price.toLocaleString()}원
                        </span>
                      </div>
                      <p className="text-sm text-gray-500 mt-1">월간 구독 (VAT 포함)</p>
                    </div>

                    <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                      <h4 className="font-medium text-gray-900 mb-2">포함된 혜택</h4>
                      <ul className="space-y-1">
                        {plan.features.slice(0, 3).map((feature, index) => (
                          <li key={index} className="text-sm text-gray-600 flex items-start">
                            <span className="text-green-500 mr-2">✓</span>
                            {feature}
                          </li>
                        ))}
                        {plan.features.length > 3 && (
                          <li className="text-sm text-gray-500">
                            + {plan.features.length - 3}개 혜택 더
                          </li>
                        )}
                      </ul>
                    </div>
                  </>
                )}

                <div className="mt-6 text-xs text-gray-500">
                  <p>주문번호: {orderId}</p>
                  <p className="mt-1">안전한 결제를 위해 토스페이먼츠를 사용합니다</p>
                </div>
              </div>
            </div>

            {/* 결제 폼 */}
            <div className="lg:col-span-2">
              <div className="bg-white rounded-lg shadow-lg overflow-hidden">
                
                {/* 헤더 */}
                <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-blue-600 to-blue-700">
                  <h2 className="text-xl font-semibold text-white">결제 정보</h2>
                  <p className="text-blue-100 mt-1">안전하고 간편한 결제를 위해 결제 수단을 선택해주세요</p>
                </div>

                {/* 에러 메시지 */}
                {error && (
                  <div className="px-6 py-4 bg-red-50 border-l-4 border-red-400">
                    <div className="flex">
                      <div className="flex-shrink-0">
                        <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                        </svg>
                      </div>
                      <div className="ml-3">
                        <p className="text-sm text-red-700">{error}</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* 로딩 상태 */}
                {isLoading && (
                  <div className="px-6 py-12 text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">결제 시스템을 준비하고 있습니다...</p>
                  </div>
                )}

                {/* 결제 위젯 */}
                {!isLoading && !error && (
                  <>
                    {/* 결제 수단 */}
                    <div className="px-6 py-6">
                      <h3 className="text-lg font-medium text-gray-900 mb-4">
                        결제 수단을 선택하세요
                      </h3>
                      <div ref={paymentMethodsRef} id="payment-methods"></div>
                    </div>

                    {/* 이용약관 */}
                    <div className="px-6 py-4">
                      <div ref={agreementRef} id="agreement"></div>
                    </div>

                    {/* 결제 버튼 */}
                    <div className="px-6 py-6 bg-gray-50">
                      <button
                        onClick={handlePayment}
                        disabled={isProcessing}
                        className={`w-full py-4 px-6 rounded-lg font-semibold text-lg transition-all duration-200 ${
                          isProcessing
                            ? 'bg-gray-400 text-gray-200 cursor-not-allowed'
                            : 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-4 focus:ring-blue-200'
                        }`}
                      >
                        {isProcessing ? (
                          <div className="flex items-center justify-center">
                            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            결제 처리 중...
                          </div>
                        ) : (
                          `${plan?.price.toLocaleString()}원 결제하기`
                        )}
                      </button>
                      
                      <p className="text-center text-sm text-gray-500 mt-3">
                        결제 정보는 암호화되어 안전하게 처리됩니다
                      </p>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default CheckoutPage;