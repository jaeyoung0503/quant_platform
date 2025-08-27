'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Search, ChevronLeft, ChevronRight } from 'lucide-react'

export default function CommunityPage() {
  const [activeTab, setActiveTab] = useState('공지사항')
  const [searchQuery, setSearchQuery] = useState('')
  const [currentPage, setCurrentPage] = useState(1)

  const menuItems = [
    { title: '전략토론방', key: 'strategy' },
    { title: '자유게시판', key: 'free' },
    { title: '마켓브리핑', key: 'market' },
    { title: '공지사항', key: 'notice' }
  ]

  // 샘플 데이터 - 실제로는 API에서 가져올 데이터
  const samplePosts = {
    notice: [
      {
        id: 1,
        title: '2025년 1분기 재무데이터 업데이트 완료 (2025/06/02 16시 20분 기준)',
        author: 'IntelliQuant',
        date: '2025.06.02',
        time: '18:26',
        views: 22
      },
      {
        id: 2,
        title: '2024년 4분기 재무데이터 업데이트 완료 (2025/04/01 16시 50분 기준)',
        author: 'IntelliQuant',
        date: '2025.04.01',
        time: '16:50',
        views: 34
      },
      {
        id: 3,
        title: '시스템 점검 안내 (2025/03/15 02:00~04:00)',
        author: 'IntelliQuant',
        date: '2025.03.14',
        time: '15:30',
        views: 156
      }
    ],
    strategy: [
      {
        id: 1,
        title: '모멘텀 전략 백테스팅 결과 공유',
        author: '퀀트투자자',
        date: '2025.06.01',
        time: '14:30',
        views: 87
      },
      {
        id: 2,
        title: '저PER 전략의 최근 성과는?',
        author: '가치투자맨',
        date: '2025.05.31',
        time: '09:15',
        views: 142
      }
    ],
    free: [
      {
        id: 1,
        title: '초보자를 위한 퀀트 투자 가이드',
        author: '퀀트선생',
        date: '2025.06.01',
        time: '16:45',
        views: 203
      }
    ],
    market: [
      {
        id: 1,
        title: '오늘의 시장 분석 - 코스피 상승 요인',
        author: '마켓분석가',
        date: '2025.06.02',
        time: '09:00',
        views: 89
      }
    ]
  }

  const getCurrentPosts = () => {
    const tabKey = menuItems.find(item => item.title === activeTab)?.key || 'notice'
    return samplePosts[tabKey] || []
  }

  const handleSearch = () => {
    // 검색 로직 구현
    console.log('Searching for:', searchQuery)
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <div className="px-6 py-8">
        {/* Header Section */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-white mb-4">
            커뮤니티
          </h1>
          <p className="text-gray-300 text-lg">
            내가 만든 전략들과 지식을 공유하고 토론합니다.
          </p>
        </div>

        {/* Tab Menu */}
        <div className="max-w-4xl mx-auto mb-8">
          <div className="flex space-x-1 border-b border-gray-700">
            {menuItems.map((item) => (
              <button
                key={item.key}
                onClick={() => setActiveTab(item.title)}
                className={`px-6 py-3 font-medium transition-colors duration-200 ${
                  activeTab === item.title
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600 hover:text-white'
                }`}
              >
                {item.title}
              </button>
            ))}
          </div>
        </div>

        {/* Content Section */}
        <div className="max-w-4xl mx-auto">
          {/* Write Button */}
          <div className="flex justify-end mb-4">
            <Link href={`/community/write?category=${menuItems.find(item => item.title === activeTab)?.key || 'notice'}`}>
              <button className="bg-green-600 hover:bg-green-500 text-white px-6 py-3 rounded-lg transition-colors duration-200 flex items-center space-x-2">
                <span>글쓰기</span>
              </button>
            </Link>
          </div>

          {/* Posts List */}
          <div className="bg-gray-800 rounded-lg overflow-hidden">
            {getCurrentPosts().map((post, index) => (
              <div key={post.id} className={`p-6 border-b border-gray-700 hover:bg-gray-750 cursor-pointer transition-colors duration-200 ${
                index === getCurrentPosts().length - 1 ? 'border-b-0' : ''
              }`}>
                <h3 className="text-white text-lg font-medium mb-3 leading-relaxed">
                  {post.title}
                </h3>
                <div className="text-gray-400 text-sm">
                  {post.author} | {post.date} {post.time} | 조회수 {post.views} |
                </div>
              </div>
            ))}
          </div>

          {/* Search and Pagination */}
          <div className="mt-8 flex justify-between items-center">
            {/* Search */}
            <div className="flex items-center space-x-2">
              <div className="relative">
                <input
                  type="text"
                  placeholder="문서 검색"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  className="bg-gray-700 text-white px-4 py-2 pl-10 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-600"
                />
                <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
              </div>
              <button
                onClick={handleSearch}
                className="bg-green-600 hover:bg-green-500 text-white px-4 py-2 rounded-lg transition-colors duration-200"
              >
                검색
              </button>
            </div>

            {/* Pagination */}
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className="p-2 text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <span className="text-gray-300 px-3">
                {currentPage} / 3
              </span>
              <button
                onClick={() => setCurrentPage(Math.min(3, currentPage + 1))}
                disabled={currentPage === 3}
                className="p-2 text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
              <span className="text-gray-400 ml-4">다음 페이지</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}