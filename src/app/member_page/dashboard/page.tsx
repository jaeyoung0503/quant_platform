'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

// 간단한 대시보드 구현
export default function Dashboard() {
  const [user, setUser] = useState(null);

  // Mock 사용자 데이터 (실제로는 인증 상태에서 가져옴)
  useEffect(() => {
    const mockUser = {
      id: '12345',
      email: 'user@example.com',
      created_at: new Date().toISOString()
    };
    setUser(mockUser);
  }, []);

  const handleSignOut = () => {
    window.location.href = '/';
  };

  return (
    <div className="min-h-screen bg-gray-900">
      <header className="bg-gray-800 border-b border-gray-700 p-4">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-100">대시보드</h1>
          <button
            onClick={handleSignOut}
            className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-xl"
          >
            로그아웃
          </button>
        </div>
      </header>

      <div className="max-w-4xl mx-auto p-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gray-800 rounded-2xl border border-gray-700 p-6"
        >
          <h2 className="text-xl font-bold text-gray-100 mb-4">환영합니다!</h2>
          <p className="text-gray-400 mb-4">간단한 인증 시스템이 성공적으로 작동합니다.</p>
          
          <div className="bg-gray-700 rounded-xl p-4">
            <h3 className="text-lg font-semibold text-gray-100 mb-2">사용자 정보</h3>
            <p className="text-gray-300">이메일: {user?.email}</p>
            <p className="text-gray-300">사용자 ID: {user?.id}</p>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
