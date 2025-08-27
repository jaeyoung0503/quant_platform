'use client'

import { useEffect, useState } from 'react'

// 유틸리티 함수들을 컴포넌트 내부에 정의
const formatCurrency = (amount: number): string => {
  if (amount === 0) return '₩0'
  
  const isNegative = amount < 0
  const absAmount = Math.abs(amount)
  
  let formatted: string
  
  if (absAmount >= 100000000) {
    formatted = `₩${(absAmount / 100000000).toFixed(1)}억`
  } else if (absAmount >= 10000) {
    formatted = `₩${(absAmount / 10000).toFixed(1)}만`
  } else {
    formatted = `₩${absAmount.toLocaleString()}`
  }
  
  return isNegative ? `-${formatted}` : formatted
}

const formatPercentage = (percentage: number): string => {
  const sign = percentage >= 0 ? '+' : ''
  return `${sign}${percentage.toFixed(2)}%`
}

const getCurrentTime = (): string => {
  return new Date().toLocaleTimeString('ko-KR', { 
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

interface PortfolioData {
  total_value: number
  cash: number
  invested_amount: number
  realized_pnl: number
  unrealized_pnl: number
  daily_pnl: number
  total_return: number
  timestamp: string
}

interface Position {
  id: number
  strategy_name: string
  stock_code: string
  stock_name: string
  quantity: number
  avg_price: number
  current_price: number
  unrealized_pnl: number
  realized_pnl: number
}

interface Order {
  id: number
  strategy_id: number
  stock_code: string
  stock_name: string
  order_type: string
  quantity: number
  price: number
  status: string
  order_time: string
  fill_time?: string
  fill_price?: number
}

interface Strategy {
  id: number
  name: string
  strategy_type: string
  is_active: boolean
  investment_amount: number
  target_stocks: string[]
  parameters: Record<string, any>
}

export default function DashboardPage() {
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null)
  const [positions, setPositions] = useState<Position[]>([])
  const [orders, setOrders] = useState<Order[]>([])
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<string>('')
  const [isConnected, setIsConnected] = useState(true)
  const [tradingStatus, setTradingStatus] = useState('stopped')

  // 실시간 데이터 업데이트
  useEffect(() => {
    const fetchData = async () => {
      try {
        // 포트폴리오 데이터
        const portfolioRes = await fetch('/api/proxy/portfolio')
        if (!portfolioRes.ok) throw new Error('포트폴리오 데이터 로드 실패')
        const portfolioData = await portfolioRes.json()
        setPortfolio(portfolioData)

        // 포지션 데이터
        const positionsRes = await fetch('/api/proxy/portfolio/positions')
        if (!positionsRes.ok) throw new Error('포지션 데이터 로드 실패')
        const positionsData = await positionsRes.json()
        setPositions(positionsData)

        // 주문 내역
        const ordersRes = await fetch('/api/proxy/orders?limit=10')
        if (!ordersRes.ok) throw new Error('주문 내역 로드 실패')
        const ordersData = await ordersRes.json()
        setOrders(ordersData)

        // 전략 목록
        const strategiesRes = await fetch('/api/proxy/strategies')
        if (!strategiesRes.ok) throw new Error('전략 목록 로드 실패')
        const strategiesData = await strategiesRes.json()
        setStrategies(strategiesData)

        // 시스템 상태
        try {
          const statusRes = await fetch('/api/proxy/system/status')
          if (statusRes.ok) {
            const statusData = await statusRes.json()
            setIsConnected(statusData.api_connected)
            setTradingStatus(statusData.is_running ? 'running' : 'stopped')
          }
        } catch (statusError) {
          console.warn('시스템 상태 조회 실패:', statusError)
        }

        setLastUpdate(getCurrentTime())
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : '데이터 로드 실패')
        console.error('Data fetch error:', err)
      } finally {
        setIsLoading(false)
      }
    }

    // 초기 로드
    fetchData()

    // 실시간 업데이트 (5초마다로 변경 - 너무 빈번한 요청 방지)
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [])

  // 전략 토글
  const toggleStrategy = async (strategyId: number) => {
    try {
      const strategy = strategies.find(s => s.id === strategyId)
      if (!strategy) return

      const response = await fetch('/api/proxy/strategies/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: strategyId,
          active: !strategy.is_active
        })
      })

      if (response.ok) {
        setStrategies(prev =>
          prev.map(s =>
            s.id === strategyId ? { ...s, is_active: !s.is_active } : s
          )
        )
      } else {
        const errorData = await response.json()
        alert(`전략 토글 실패: ${errorData.detail || '알 수 없는 오류'}`)
      }
    } catch (error) {
      console.error('전략 토글 실패:', error)
      alert('전략 토글 중 오류가 발생했습니다.')
    }
  }

  // 트레이딩 제어
  const startTrading = async () => {
    try {
      const response = await fetch('/api/proxy/trading/start', { method: 'POST' })
      if (response.ok) {
        setTradingStatus('running')
        alert('자동매매가 시작됩니다.')
      } else {
        const errorData = await response.json()
        alert(`자동매매 시작 실패: ${errorData.detail || '알 수 없는 오류'}`)
      }
    } catch (error) {
      console.error('자동매매 시작 실패:', error)
      alert('자동매매 시작 중 오류가 발생했습니다.')
    }
  }

  const stopTrading = async () => {
    try {
      const response = await fetch('/api/proxy/trading/stop', { method: 'POST' })
      if (response.ok) {
        setTradingStatus('stopped')
        alert('자동매매가 중지됩니다.')
      } else {
        const errorData = await response.json()
        alert(`자동매매 중지 실패: ${errorData.detail || '알 수 없는 오류'}`)
      }
    } catch (error) {
      console.error('자동매매 중지 실패:', error)
      alert('자동매매 중지 중 오류가 발생했습니다.')
    }
  }

  const emergencyStop = async () => {
    if (confirm('모든 주문을 취소하고 긴급중단하시겠습니까?')) {
      try {
        const response = await fetch('/api/proxy/trading/emergency-stop', { method: 'POST' })
        if (response.ok) {
          setTradingStatus('emergency_stopped')
          alert('긴급중단 실행됨')
        } else {
          const errorData = await response.json()
          alert(`긴급중단 실패: ${errorData.detail || '알 수 없는 오류'}`)
        }
      } catch (error) {
        console.error('긴급중단 실패:', error)
        alert('긴급중단 중 오류가 발생했습니다.')
      }
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">시스템 로딩 중...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-red-400 text-xl">{error}</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* 헤더 */}
      <header className="bg-gray-800 px-6 py-4 flex items-center justify-between border-b border-gray-700">
        <div className="flex items-center space-x-4">
          <h1 className="text-2xl font-bold text-green-400">QuanTrade Pro</h1>
          <div className="flex items-center space-x-2">
            <span className="text-sm">키움 API</span>
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`}></div>
            <span className="text-sm">{isConnected ? '연결됨' : '연결 끊김'}</span>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-400">마지막 업데이트: {lastUpdate}</span>
        </div>

        <div className="flex space-x-2">
          <button
            onClick={startTrading}
            disabled={tradingStatus === 'running'}
            className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-4 py-2 rounded text-sm font-medium transition-colors"
          >
            자동매매 시작
          </button>
          <button
            onClick={stopTrading}
            disabled={tradingStatus === 'stopped'}
            className="bg-red-600 hover:bg-red-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-4 py-2 rounded text-sm font-medium transition-colors"
          >
            중지
          </button>
          <button
            onClick={emergencyStop}
            className="bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded text-sm font-medium animate-pulse transition-colors"
          >
            긴급중단
          </button>
        </div>
      </header>

      <div className="flex h-[calc(100vh-80px)]">
        {/* 사이드바 - 전략 관리 */}
        <div className="w-80 bg-gray-800 p-6 overflow-y-auto border-r border-gray-700">
          <h2 className="text-lg font-semibold mb-4 text-gray-300">활성 전략</h2>
          
          <div className="space-y-4">
            {strategies.map(strategy => (
              <div key={strategy.id} className="bg-gray-700 p-4 rounded-lg">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-medium text-white">{strategy.name}</h3>
                  <button
                    onClick={() => toggleStrategy(strategy.id)}
                    className={`relative w-12 h-6 rounded-full transition-colors ${
                      strategy.is_active ? 'bg-green-500' : 'bg-gray-500'
                    }`}
                  >
                    <div
                      className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
                        strategy.is_active ? 'translate-x-7' : 'translate-x-1'
                      }`}
                    ></div>
                  </button>
                </div>
                
                <div className="text-sm text-gray-300 space-y-1">
                  <div>투자금액: {formatCurrency(strategy.investment_amount)}</div>
                  <div>대상종목: {strategy.target_stocks?.join(', ') || 'N/A'}</div>
                  <div className={`inline-block px-2 py-1 rounded text-xs ${
                    strategy.is_active 
                      ? 'bg-green-900 text-green-300' 
                      : 'bg-gray-600 text-gray-400'
                  }`}>
                    {strategy.is_active ? '활성' : '비활성'}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* 리스크 관리 */}
          <div className="mt-8">
            <h3 className="text-lg font-semibold mb-4 text-gray-300">리스크 관리</h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">일일 손실한도:</span>
                <span className="text-red-400">-2%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">포지션 크기:</span>
                <span className="text-blue-400">5%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">최대 보유종목:</span>
                <span className="text-blue-400">10개</span>
              </div>
            </div>
          </div>
        </div>

        {/* 메인 콘텐츠 */}
        <div className="flex-1 flex flex-col">
          {/* 포트폴리오 개요 */}
          <div className="bg-gray-800 p-6 border-b border-gray-700">
            <div className="grid grid-cols-4 gap-6">
              <div className="bg-gray-700 p-4 rounded-lg text-center">
                <div className="text-sm text-gray-400 mb-1">총 평가금액</div>
                <div className="text-2xl font-bold text-white">
                  {formatCurrency(portfolio?.total_value || 0)}
                </div>
                <div className="text-sm text-green-400">
                  +{formatCurrency(portfolio?.daily_pnl || 0)}
                </div>
              </div>

              <div className="bg-gray-700 p-4 rounded-lg text-center">
                <div className="text-sm text-gray-400 mb-1">실시간 손익</div>
                <div className={`text-2xl font-bold ${
                  (portfolio?.unrealized_pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  {formatCurrency(portfolio?.unrealized_pnl || 0)}
                </div>
                <div className="text-sm text-gray-400">
                  실현: {formatCurrency(portfolio?.realized_pnl || 0)}
                </div>
              </div>

              <div className="bg-gray-700 p-4 rounded-lg text-center">
                <div className="text-sm text-gray-400 mb-1">수익률</div>
                <div className={`text-2xl font-bold ${
                  (portfolio?.total_return || 0) >= 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  {formatPercentage(portfolio?.total_return || 0)}
                </div>
                <div className="text-sm text-gray-400">
                  {(portfolio?.total_return || 0) >= 0 ? '+' : ''}{((portfolio?.daily_pnl || 0) / (portfolio?.total_value || 1) * 100).toFixed(1)}% (오늘)
                </div>
              </div>

              <div className="bg-gray-700 p-4 rounded-lg text-center">
                <div className="text-sm text-gray-400 mb-1">활성 포지션</div>
                <div className="text-2xl font-bold text-white">{positions.length}개</div>
                <div className="text-sm text-gray-400">
                  투자: {formatCurrency(portfolio?.invested_amount || 0)}
                </div>
              </div>
            </div>
          </div>

          {/* 실시간 수익 및 포지션 */}
          <div className="flex-1 flex">
            {/* 실시간 수익 현황 */}
            <div className="flex-1 p-6">
              <div className="bg-gray-700 rounded-lg p-4 h-full">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold">실시간 수익 현황</h3>
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                </div>

                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {positions.map(position => (
                    <div key={position.id} className="bg-gray-600 p-3 rounded flex items-center justify-between">
                      <div className="flex-1">
                        <div className="font-medium">{position.strategy_name} - {position.stock_name}</div>
                        <div className="text-sm text-gray-400">
                          {position.stock_code} | {position.quantity}주 @ {formatCurrency(position.avg_price)}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className={`font-bold ${
                          position.unrealized_pnl >= 0 ? 'text-green-400' : 'text-red-400'
                        }`}>
                          {position.unrealized_pnl >= 0 ? '+' : ''}{formatCurrency(position.unrealized_pnl)}
                        </div>
                        <div className={`text-sm ${
                          position.unrealized_pnl >= 0 ? 'text-green-400' : 'text-red-400'
                        }`}>
                          {position.unrealized_pnl >= 0 ? '+' : ''}{formatPercentage(
                            ((position.current_price - position.avg_price) / position.avg_price) * 100
                          )}
                        </div>
                      </div>
                    </div>
                  ))}

                  {positions.length === 0 && (
                    <div className="text-center text-gray-400 py-8">
                      현재 보유 포지션이 없습니다
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* 최근 주문 내역 */}
            <div className="w-96 p-6 pl-0">
              <div className="bg-gray-700 rounded-lg p-4 h-full">
                <h3 className="text-lg font-semibold mb-4">최근 주문 내역</h3>
                
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {orders.map(order => (
                    <div key={order.id} className="bg-gray-600 p-3 rounded text-sm">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium">{order.stock_name}</span>
                        <span className={`px-2 py-1 rounded text-xs ${
                          order.order_type === 'buy' 
                            ? 'bg-blue-900 text-blue-300' 
                            : 'bg-red-900 text-red-300'
                        }`}>
                          {order.order_type === 'buy' ? '매수' : '매도'}
                        </span>
                      </div>
                      <div className="text-gray-400">
                        {order.quantity}주 @ {formatCurrency(order.price)}
                      </div>
                      <div className="flex items-center justify-between mt-1">
                        <span className={`text-xs px-2 py-1 rounded ${
                          order.status === 'filled' 
                            ? 'bg-green-900 text-green-300'
                            : order.status === 'pending'
                            ? 'bg-yellow-900 text-yellow-300'
                            : 'bg-gray-900 text-gray-400'
                        }`}>
                          {order.status === 'filled' ? '체결' : 
                           order.status === 'pending' ? '대기' : '취소'}
                        </span>
                        <span className="text-xs text-gray-500">
                          {new Date(order.order_time).toLocaleTimeString('ko-KR')}
                        </span>
                      </div>
                    </div>
                  ))}

                  {orders.length === 0 && (
                    <div className="text-center text-gray-400 py-8">
                      주문 내역이 없습니다
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}