'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';

const QuantStrategyMain = () => {
  const [showMenu, setShowMenu] = useState(false);
  const router = useRouter();

  const menuItems = [
    { name: 'Backtesting', icon: '', path: '/backtesting' },
    { name: '종목별 분석', icon: '', path: '/onestock' },
    { name: 'My 전략', icon: '', path: '/quant-strategy' },
    { name: '모의거래', icon: '', path: '/mock_trading' },
    { name: '실제거래', icon: '', path: '/actual_trading' },
    { name: 'Membership', icon: '', path: '/member_payment' },
    { name: 'Community', icon: '', path: '/community' }    
  ];

  const handleMenuClick = (path) => {
    router.push(path);
    setShowMenu(false);
  };

  return (
    <div className="min-h-screen bg-gray-900 relative">
      {/* Header */}
      <div className="bg-black text-white p-4">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-400">quantmaster.com</span>
        </div>
        
        <div className="flex items-center justify-center mt-4">  {/*menu 중앙정렬*/}
          <div className="flex items-center space-x-8">
            <div className="flex items-center space-x-2">
              <span className="text-blue-400 font-bold text-lg">QUANT</span>
              <span className="text-white font-bold text-lg">MASTER</span>
              <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
                <div className="w-3 h-3 bg-white rounded-full"></div>
              </div>
            </div>
            
            {/* Navigation Menu */}
            <div className="hidden lg:flex items-center gap-6">
              {menuItems.map((item, index) => (
                <button 
                  key={index}
                  onClick={() => handleMenuClick(item.path)}
                  className="text-white hover:text-blue-400 transition-colors text-lg font-medium"
                >
                  {item.name}
                </button>
              ))}
            </div>
          </div>
{/*     hamburger menu      
          <button 
            onClick={() => setShowMenu(true)}
            className="text-white"
          >
            <div className="space-y-1">
              <div className="w-6 h-0.5 bg-white"></div>
              <div className="w-6 h-0.5 bg-white"></div>
              <div className="w-6 h-0.5 bg-white"></div>
            </div>
          </button> */}
        </div>

        {/* Mobile Menu - 작은 화면에서만 보이는 메뉴 */}
        <div className="lg:hidden mt-4 flex flex-wrap gap-3 justify-center">
          {menuItems.map((item, index) => (
            <button 
              key={index}
              onClick={() => handleMenuClick(item.path)}
              className="text-white py-2 px-3 hover:bg-gray-800 rounded-lg transition-colors text-lg font-medium"
            >
              {item.name}
            </button>
          ))}
        </div>
      </div>

      {/* Main Content */}
      {/* <div className="p-8 max-w-2xl mx-auto"> */}
      <div className="min-h-screen bg-gray-900 relative flex flex-col items-center justify-startter p-8 mt-12">
        {/* Branding Section */}
        <div className="bg-gray-800 rounded-2xl border border-gray-700 p-8 text-center mb-8">
          <h1 className="text-3xl lg:text-4xl font-bold text-gray-100 mb-4">
            Welcome to
            <br />
            <span className="text-blue-400">QuantMaster</span>
          </h1>
          
          {/* <div className="flex justify-center gap-8 mt-6 text-gray-300">
            <span>고급 차트 및 시각화</span>
            <span>맞춤형 대시보드</span>
          </div> */}
        </div>

        {/* Auth Section */}
        <div className="bg-gray-800 rounded-2xl border border-gray-700 p-8  ">
          <h2 className="text-2xl font-bold text-gray-100 mb-6 text-center">
            {/* Quantitative Trading<br /> */}
            <span className="text-blue-400">Beginner to Expert</span>
          </h2>

          {/* Description */}
          <p className="text-gray-300 text-lg mb-8 leading-relaxed text-center ">
            퀀트 전략부터 백테스팅 까지 하나의 플랫폼으로 완성하세요
            {/* Power your quantitative research with a cutting-edge, unified API 
            for research, backtesting, and live trading on the world's 
            leading algorithmic trading platform. */}
          </p>

          {/* CTA Buttons */}
          <div className="space-y-4">
            <button 
              onClick={() => router.push('/signin')}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-4 rounded-xl transition-colors"
            >
              로그인
            </button>
            
            <button 
              onClick={() => router.push('/member_page')}
              className="w-full bg-gray-700 hover:bg-gray-600 text-white font-semibold py-3 px-4 rounded-xl transition-colors border border-gray-600"
            >
              Create Free Account
            </button>
          </div>

          {/* Award Banner */}
          <div className="text-center text-blue-400 font-semibold tracking-wider mt-6">
            AWARD WINNING QUANT ANALYTICS
          </div>
        </div>
      </div>

      {/* Side Menu Overlay */}
      {showMenu && (
        <div className="fixed inset-0 bg-black bg-opacity-90 z-50 flex items-center justify-center">
          <div className="bg-gray-900 w-80 max-w-sm mx-4 rounded-2xl border border-gray-700 p-6">
            {/* Close Button */}
            <div className="flex justify-end mb-6">
              <button 
                onClick={() => setShowMenu(false)}
                className="w-10 h-10 bg-gray-600 rounded-full flex items-center justify-center text-white hover:bg-gray-500 transition-colors"
              >
                ×
              </button>
            </div>

            {/* Platform Section */}
            <div className="mb-8">
              <h3 className="text-gray-400 text-sm mb-4 uppercase tracking-wider">
                PLATFORM
              </h3>
              <div className="space-y-2">
                {menuItems.map((item, index) => (
                  <button 
                    key={index}
                    onClick={() => handleMenuClick(item.path)}
                    className="w-full text-left text-white py-3 px-4 hover:bg-gray-800 rounded-xl transition-colors flex items-center space-x-3"
                  >
                    <span className="text-xl">{item.icon}</span>
                    <span className="text-lg">{item.name}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Sign In Section */}
            <div className="border-t border-gray-700 pt-6">
              <h3 className="text-gray-400 text-sm mb-4 uppercase tracking-wider">
                ACCOUNT
              </h3>
              
              <div className="space-y-3">
                <button 
                  onClick={() => {
                    router.push('/signin');
                    setShowMenu(false);
                  }}
                  className="w-full bg-white text-black py-3 rounded-xl font-semibold hover:bg-gray-100 transition-colors"
                >
                  Sign in
                </button>
                
                <button 
                  onClick={() => {
                    router.push('/signup');
                    setShowMenu(false);
                  }}
                  className="w-full bg-blue-600 text-white py-3 rounded-xl font-semibold hover:bg-blue-700 transition-colors"
                >
                  Sign up for Free
                </button>
              </div>
              
              <p className="text-gray-300 text-center text-sm mt-4">
                Don't have an account? Join<br />
                QuantMaster Today
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Navigation Bar */}
      <div className="fixed bottom-0 left-0 right-0 bg-black h-12 flex items-center justify-center">
        <div className="flex space-x-8">
          <div className="w-8 h-1 bg-white"></div>
          <div className="w-8 h-8 border-2 border-white rounded"></div>
          <div className="w-0 h-0 border-l-4 border-l-transparent border-r-4 border-r-transparent border-b-8 border-b-white"></div>
        </div>
      </div>
    </div>
  );
};

export default QuantStrategyMain;