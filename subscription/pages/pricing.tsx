 // pages/pricing.tsx - MVP 요금제 페이지
import React, { useState } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import { PLANS, TEST_USER } from '../lib/config';
import PricingCard from '../components/PricingCard';

const PricingPage: React.FC = () => {
  const router = useRouter();
  const [loading, setLoading] = useState<string | null>(null);

  const handleSelectPlan = async (planId: string) => {
    setLoading(planId);

    try {
      const response = await fetch('/api/payment', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          planId,
          customerName: TEST_USER.name,
          customerEmail: TEST_USER.email,
        }),
      });

      const result = await response.json();

      if (result.success && result.data) {
        // 결제 페이지로 이동
        router.push({
          pathname: '/checkout',
          query: {
            orderId: result.data.orderId,
            planId,
          },
        });
      } else {
        alert('결제 요청 생성에 실패했습니다: ' + (result.error || '알 수 없는 오류'));
      }
    } catch (error) {
      console.error('Payment request error:', error);
      alert('결제 요청 중 오류가 발생했습니다.');
    } finally {
      setLoading(null);
    }
  };

  return (
    <>
      <Head>
        <title>요금제 선택 - 구독 서비스</title>
        <meta name="description" content="당신에게 맞는 구독 플랜을 선택하세요" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <div className="min-h-screen bg-gray-50 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* 헤더 */}
          <div className="text-center">
            <h1 className="text-3xl font-extrabold text-gray-900 sm:text-4xl">
              요금제 선택
            </h1>
            <p className="mt-4 text-xl text-gray-600">
              당신에게 맞는 플랜을 선택하세요
            </p>
          </div>

          {/* 요금제 카드 */}
          <div className="mt-12 space-y-4 sm:mt-16 sm:space-y-0 sm:grid sm:grid-cols-2 sm:gap-6 lg:max-w-4xl lg:mx-auto">
            {PLANS.map((plan) => (
              <PricingCard
                key={plan.id}
                plan={plan}
                loading={loading === plan.id}
                onSelect={() => handleSelectPlan(plan.id)}
              />
            ))}
          </div>

          {/* 추가 정보 */}
          <div className="mt-16 text-center">
            <div className="max-w-3xl mx-auto">
              <h2 className="text-2xl font-bold text-gray-900 mb-8">
                모든 플랜에 포함된 기본 혜택
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="w-12 h-12 mx-auto bg-blue-100 rounded-full flex items-center justify-center mb-4">
                    <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-medium text-gray-900">안전한 결제</h3>
                  <p className="text-gray-600">SSL 암호화와 토스페이먼츠로 안전하게 보호</p>
                </div>
                
                <div className="text-center">
                  <div className="w-12 h-12 mx-auto bg-green-100 rounded-full flex items-center justify-center mb-4">
                    <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192L5.636 18.364M12 12h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-medium text-gray-900">24/7 지원</h3>
                  <p className="text-gray-600">언제든지 도움이 필요하면 연락주세요</p>
                </div>
                
                <div className="text-center">
                  <div className="w-12 h-12 mx-auto bg-purple-100 rounded-full flex items-center justify-center mb-4">
                    <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-medium text-gray-900">즉시 시작</h3>
                  <p className="text-gray-600">결제 후 바로 모든 기능을 사용할 수 있어요</p>
                </div>
              </div>
            </div>
          </div>

          {/* FAQ */}
          <div className="mt-16">
            <div className="max-w-3xl mx-auto">
              <h2 className="text-2xl font-bold text-gray-900 text-center mb-8">
                자주 묻는 질문
              </h2>
              
              <div className="space-y-4">
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="font-medium text-gray-900 mb-2">언제든 플랜을 변경할 수 있나요?</h3>
                  <p className="text-gray-600">네, 언제든지 플랜을 업그레이드하거나 다운그레이드할 수 있습니다.</p>
                </div>
                
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="font-medium text-gray-900 mb-2">환불이 가능한가요?</h3>
                  <p className="text-gray-600">서비스 이용 후 7일 이내에는 전액 환불이 가능합니다.</p>
                </div>
                
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="font-medium text-gray-900 mb-2">어떤 결제 수단을 지원하나요?</h3>
                  <p className="text-gray-600">토스페이먼츠를 통해 모든 국내 카드와 계좌이체를 지원합니다.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default PricingPage;
