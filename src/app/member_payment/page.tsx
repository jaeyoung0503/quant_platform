'use client'

import { useState } from 'react'

export default function MembershipPage() {
  const [isMonthly, setIsMonthly] = useState(true)

  const plans = [
    {
      name: 'Basic',
      subtitle: 'Free',
      price: 0,
      popular: false,
      headerColor: 'bg-gradient-to-r from-blue-600 to-green-500'
    },
    {
      name: 'Advanced',
      subtitle: '실전 퀀트 투자를 위한 핵심 기능',
      price: 9900,
      popular: false,
      headerColor: 'bg-gray-700'
    },
    {
      name: 'Premium',
      subtitle: '프리미엄 투자 전략과 고급 분석',
      price: 19900,
      popular: true,
      headerColor: 'bg-gray-700'
    }
  ]

  const features = [
    {
      name: '백테스트 기간',
      basic: '약 5년\n(5년 전 ~ 1개월 전)',
      advanced: '한국: 2000년 ~ 현재\n미국: 2010년 ~ 현재',
      premium: '한국: 2000년 ~ 현재\n미국: 2010년 ~ 현재'
    },
    {
      name: '알고리즘 동시 실행 개수',
      basic: '2',
      advanced: '2',
      premium: '2'
    },
    {
      name: '1일 백테스트 횟수',
      basic: '50회',
      advanced: '100회',
      premium: '100회'
    },
    {
      name: '실행 개수\n(만매/구독 알고리즘)',
      basic: '1 (제한적)',
      advanced: '3',
      premium: '3'
    },
    {
      name: '자동매매 연동 (나무증권)',
      basic: 'O',
      advanced: 'O',
      premium: 'O'
    },
    {
      name: '커뮤니티 토론방',
      basic: 'O',
      advanced: 'O',
      premium: 'O'
    },
    {
      name: '이메일 문의',
      basic: 'O',
      advanced: 'O',
      premium: 'O'
    },
    {
      name: '채널톡 상담',
      basic: '단순 문의',
      advanced: '단순 문의',
      premium: '단순 문의'
    }
  ]

  const getDiscountedPrice = (price: number) => {
    return Math.floor(price * 0.9)
  }

  const handlePayment = (planName: string, isMonthly: boolean, basePrice: number) => {
    const finalPrice = isMonthly ? basePrice : getDiscountedPrice(basePrice)
    const period = isMonthly ? 'monthly' : 'quarterly'
    
    // 결제 모듈로 이동 (실제 구현에서는 결제 서비스 API 연동)
    const paymentData = {
      planName,
      period,
      price: finalPrice,
      billingCycle: isMonthly ? 1 : 3
    }
    
    // 방법 1: 쿼리 파라미터로 결제 정보 전달
    const searchParams = new URLSearchParams({
      plan: planName.toLowerCase(),
      period: period,
      price: finalPrice.toString()
    })
    
    // 결제 페이지로 이동
    window.location.href = `/payment?${searchParams.toString()}`
    
    // 방법 2: 외부 결제 서비스 (예: 토스페이먼츠, 아임포트 등)
    // 실제 결제 모듈 연동시 사용
    // window.open(`https://payment-service.com/checkout?${searchParams.toString()}`, '_blank')
  }

  return (
    <div className="min-h-screen bg-gray-900 py-12">
      <div className="max-w-7xl mx-auto px-6">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-white mb-4">Membership</h1>
          <p className="text-gray-300 text-lg">
            나에게 필요한 기능과 혜택에 맞는 멤버십에 가입해 보세요.
          </p>
        </div>

        {/* Billing Toggle */}
        <div className="flex justify-center mb-12">
          <div className="bg-gray-800 rounded-full p-1 flex">
            <button
              onClick={() => setIsMonthly(true)}
              className={`px-6 py-3 rounded-full font-medium transition-all duration-200 ${
                isMonthly 
                  ? 'bg-green-600 text-white' 
                  : 'text-gray-300 hover:text-white'
              }`}
            >
              월 결제
            </button>
            <button
              onClick={() => setIsMonthly(false)}
              className={`px-6 py-3 rounded-full font-medium transition-all duration-200 ${
                !isMonthly 
                  ? 'bg-green-600 text-white' 
                  : 'text-gray-300 hover:text-white'
              }`}
            >
              3개월 결제
            </button>
          </div>
          {!isMonthly && (
            <div className="ml-4 flex items-center">
              <span className="text-green-400 font-semibold">10% 할인!</span>
            </div>
          )}
        </div>

        {/* Pricing Table */}
        <div className="bg-gray-800 rounded-xl overflow-hidden shadow-2xl">
          {/* Header Row */}
          <div className="grid grid-cols-4 bg-gray-700">
            <div className="p-6">
              <h3 className="text-white font-semibold text-lg">기능</h3>
            </div>
            {plans.map((plan, index) => (
              <div key={index} className={`p-6 ${plan.headerColor} relative`}>
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                    <span className="bg-orange-500 text-white text-xs px-3 py-1 rounded-full">
                      인기
                    </span>
                  </div>
                )}
                <div className="text-white">
                  <h3 className="font-bold text-xl mb-1">{plan.name}</h3>
                  <p className="text-sm opacity-90 mb-3">{plan.subtitle}</p>
                  <div className="text-2xl font-bold">
                    {plan.price === 0 ? (
                      <span>Free</span>
                    ) : (
                      <button
                        onClick={() => handlePayment(plan.name, isMonthly, plan.price)}
                        className="hover:bg-white/10 rounded-lg px-3 py-2 transition-colors duration-200 cursor-pointer"
                      >
                        {isMonthly ? (
                          `${plan.price.toLocaleString()}원/월`
                        ) : (
                          <>
                            <div className="line-through text-lg opacity-70">
                              {plan.price.toLocaleString()}원/월
                            </div>
                            <div>{getDiscountedPrice(plan.price).toLocaleString()}원/월</div>
                          </>
                        )}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Feature Rows */}
          {features.map((feature, index) => (
            <div key={index} className={`grid grid-cols-4 border-t border-gray-700 ${
              index % 2 === 0 ? 'bg-gray-800' : 'bg-gray-750'
            }`}>
              <div className="p-4 border-r border-gray-700">
                <span className="text-white font-medium whitespace-pre-line">
                  {feature.name}
                </span>
              </div>
              <div className="p-4 border-r border-gray-700 text-center">
                <span className="text-gray-300 whitespace-pre-line">
                  {feature.basic}
                </span>
              </div>
              <div className="p-4 border-r border-gray-700 text-center">
                <span className="text-gray-300 whitespace-pre-line">
                  {feature.advanced}
                </span>
              </div>
              <div className="p-4 text-center">
                <span className="text-gray-300 whitespace-pre-line">
                  {feature.premium}
                </span>
              </div>
            </div>
          ))}

          {/* Action Buttons */}
          <div className="grid grid-cols-4 bg-gray-700 border-t border-gray-600">
            <div className="p-6"></div>
            {plans.map((plan, index) => (
              <div key={index} className="p-6">
                {plan.price === 0 ? (
                  <button className="w-full py-3 px-4 rounded-lg font-semibold transition-colors duration-200 bg-gray-600 text-white hover:bg-gray-500 cursor-default">
                    현재 플랜
                  </button>
                ) : (
                  <button 
                    onClick={() => handlePayment(plan.name, isMonthly, plan.price)}
                    className="w-full py-3 px-4 rounded-lg font-semibold transition-colors duration-200 bg-green-600 text-white hover:bg-green-500"
                  >
                    선택하기
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}