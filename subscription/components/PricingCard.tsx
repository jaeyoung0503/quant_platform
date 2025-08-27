// components/PricingCard.tsx - MVP 요금제 카드
import React from 'react';
import { Plan } from '../lib/types';

interface PricingCardProps {
  plan: Plan;
  loading?: boolean;
  onSelect: () => void;
}

const PricingCard: React.FC<PricingCardProps> = ({ plan, loading = false, onSelect }) => {
  return (
    <div className={`relative rounded-lg shadow-lg transition-all duration-200 hover:shadow-xl ${
      plan.popular 
        ? 'border-2 border-blue-500 ring-2 ring-blue-200 ring-opacity-50' 
        : 'border border-gray-200'
    } bg-white ${loading ? 'opacity-75' : ''}`}>
      
      {/* 인기 배지 */}
      {plan.popular && (
        <div className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
          <span className="inline-flex px-4 py-1 rounded-full text-sm font-semibold tracking-wide uppercase bg-blue-500 text-white shadow-lg">
            🔥 추천
          </span>
        </div>
      )}
      
      <div className="p-6">
        {/* 플랜 제목 */}
        <div className="text-center mb-6">
          <h3 className="text-xl font-bold text-gray-900">{plan.name}</h3>
          <div className="mt-4">
            <span className="text-4xl font-extrabold text-gray-900">
              {plan.price.toLocaleString()}
            </span>
            <span className="text-lg font-medium text-gray-500">원</span>
            <span className="text-base font-medium text-gray-500">/월</span>
          </div>
          
          {/* 연간 할인 정보 */}
          <p className="mt-2 text-sm text-gray-500">
            월간 결제 • 언제든 변경 가능
          </p>
        </div>
        
        {/* 기능 목록 */}
        <ul className="space-y-3 mb-8">
          {plan.features.map((feature, index) => (
            <li key={index} className="flex items-start">
              <div className="flex-shrink-0">
                <svg
                  className="w-5 h-5 text-green-500 mt-0.5"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <span className="ml-3 text-sm text-gray-700 leading-5">{feature}</span>
            </li>
          ))}
        </ul>
        
        {/* 선택 버튼 */}
        <button
          onClick={onSelect}
          disabled={loading}
          className={`w-full py-3 px-6 border border-transparent rounded-lg text-base font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 ${
            plan.popular
              ? 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500 shadow-lg'
              : 'bg-blue-50 text-blue-600 hover:bg-blue-100 focus:ring-blue-500 border-blue-200'
          } ${loading ? 'cursor-not-allowed' : 'cursor-pointer hover:shadow-md'}`}
        >
          {loading ? (
            <div className="flex items-center justify-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-current" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              처리 중...
            </div>
          ) : (
            <>
              {plan.popular ? '🚀 지금 시작하기' : '선택하기'}
            </>
          )}
        </button>
        
        {/* 추가 정보 */}
        <p className="mt-3 text-xs text-gray-500 text-center">
          7일 무료 체험 • 언제든 취소 가능
        </p>
      </div>
    </div>
  );
};

export default PricingCard;