'use client'
import { useEffect, useState } from 'react'
import {
  LineChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Line,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell
} from 'recharts'

// 아이콘 컴포넌트들
const TrendingUp = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <polyline points="22,7 13.5,15.5 8.5,10.5 2,17"></polyline>
    <polyline points="16,7 22,7 22,13"></polyline>
  </svg>
)

const TrendingDown = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <polyline points="22,17 13.5,8.5 8.5,13.5 2,7"></polyline>
    <polyline points="16,17 22,17 22,11"></polyline>
  </svg>
)

const BarChart3 = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <path d="M3 3v18h18"></path>
    <path d="M18 17V9"></path>
    <path d="M13 17V5"></path>
    <path d="M8 17v-3"></path>
  </svg>
)

const Activity = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <polyline points="22,12 18,12 15,21 9,3 6,12 2,12"></polyline>
  </svg>
)

const Settings = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <circle cx="12" cy="12" r="3"></circle>
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1 1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
  </svg>
)

const Play = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <polygon points="5,3 19,12 5,21"></polygon>
  </svg>
)

const Wallet = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <path d="M21 12V7H5a2 2 0 0 1 0-4h14v4"></path>
    <path d="M3 5v14a2 2 0 0 0 2 2h16v-5"></path>
    <path d="M18 12a2 2 0 0 0 0 4h4v-4Z"></path>
  </svg>
)

const Target = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <circle cx="12" cy="12" r="10"></circle>
    <circle cx="12" cy="12" r="6"></circle>
    <circle cx="12" cy="12" r="2"></circle>
  </svg>
)

const RefreshCw = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <polyline points="23,4 23,10 17,10"></polyline>
    <polyline points="1,20 1,14 7,14"></polyline>
    <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"></path>
  </svg>
)

const Clock = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <circle cx="12" cy="12" r="10"></circle>
    <polyline points="12,6 12,12 16,14"></polyline>
  </svg>
)

// 유틸리티 함수들
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

const formatTime = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

// 인터페이스 정의
interface AccountInfo {
  account_number: string
  available_cash: number
  total_cash: number
  credit_limit: number
}

interface AutoTradingStatus {
  is_running: boolean
  active_strategies: number
  today_trades: number
  total_return: number
  running_time: number
}

interface RiskSettings {
  daily_loss_limit: number
  position_size_limit: number
  max_positions: number
  stop_loss_rate: number
  take_profit_rate: number
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
  unrealized_pnl_rate: number
  weight: number
}

interface Trade {
  id: number
  time: string
  stock_code: string
  stock_name: string
  type: 'BUY' | 'SELL'
  quantity: number
  price: number
  status: 'COMPLETED' | 'PENDING' | 'CANCELLED'
}

interface Strategy {
  id: number
  name: string
  is_active: boolean
  today_profit: number
  win_rate: number
  max_loss: number
  signals_waiting: number
  signals_processed: number
  signals_rejected: number
}

export default function KiwoomStyleDashboard() {
  const [selectedTab, setSelectedTab] = useState<'positions' | 'charts' | 'trading' | 'strategies'>('positions')
  const [accountInfo] = useState<AccountInfo>({
    account_number: "8012345-01",
    available_cash: 24000000,
    total_cash: 50000000,
    credit_limit: 10000000
  })

  const [autoTradingStatus, setAutoTradingStatus] = useState<AutoTradingStatus>({
    is_running: true,
    active_strategies: 2,
    today_trades: 8,
    total_return: 2.34,
    running_time: 7875
  })

  const [connectionStatus, setConnectionStatus] = useState({
    is_connecting: false,
    steps: [
      { name: '키움 API 연결', status: 'completed' },
      { name: '계좌 인증', status: 'completed' },
      { name: '시장 데이터 연결', status: 'completed' },
      { name: '전략 초기화', status: 'completed' },
      { name: '자동매매 준비완료', status: 'completed' }
    ]
  })

  const [tradingMode, setTradingMode] = useState<'real' | 'simulation'>('simulation')

  const [riskSettings, setRiskSettings] = useState<RiskSettings>({
    daily_loss_limit: -2.0,
    position_size_limit: 5.0,
    max_positions: 10,
    stop_loss_rate: -3.0,
    take_profit_rate: 5.0
  })

  const [positions] = useState<Position[]>([
    {
      id: 1,
      strategy_name: "볼린저밴드",
      stock_code: "005930",
      stock_name: "삼성전자",
      quantity: 150,
      avg_price: 70000,
      current_price: 72000,
      unrealized_pnl: 300000,
      unrealized_pnl_rate: 2.86,
      weight: 35.2
    },
    {
      id: 2,
      strategy_name: "RSI 역추세",
      stock_code: "035720",
      stock_name: "카카오",
      quantity: 80,
      avg_price: 52000,
      current_price: 50500,
      unrealized_pnl: -120000,
      unrealized_pnl_rate: -2.88,
      weight: 22.1
    },
    {
      id: 3,
      strategy_name: "모멘텀",
      stock_code: "035420",
      stock_name: "NAVER",
      quantity: 25,
      avg_price: 180000,
      current_price: 185000,
      unrealized_pnl: 125000,
      unrealized_pnl_rate: 2.78,
      weight: 15.3
    }
  ])

  const [trades] = useState<Trade[]>([
    {
      id: 1,
      time: "09:15:23",
      stock_code: "005930",
      stock_name: "삼성전자",
      type: "BUY",
      quantity: 50,
      price: 71000,
      status: "COMPLETED"
    },
    {
      id: 2,
      time: "09:32:15",
      stock_code: "035720",
      stock_name: "카카오",
      type: "SELL",
      quantity: 30,
      price: 51500,
      status: "COMPLETED"
    },
    {
      id: 3,
      time: "10:15:45",
      stock_code: "035420",
      stock_name: "NAVER",
      type: "BUY",
      quantity: 10,
      price: 183000,
      status: "PENDING"
    }
  ])

  const [strategies] = useState<Strategy[]>([
    {
      id: 1,
      name: "볼린저밴드 전략",
      is_active: true,
      today_profit: 125000,
      win_rate: 68,
      max_loss: -45000,
      signals_waiting: 2,
      signals_processed: 8,
      signals_rejected: 1
    },
    {
      id: 2,
      name: "RSI 역추세 전략",
      is_active: true,
      today_profit: -30000,
      win_rate: 45,
      max_loss: -80000,
      signals_waiting: 1,
      signals_processed: 7,
      signals_rejected: 1
    },
    {
      id: 3,
      name: "모멘텀 전략",
      is_active: false,
      today_profit: 0,
      win_rate: 0,
      max_loss: 0,
      signals_waiting: 0,
      signals_processed: 0,
      signals_rejected: 0
    }
  ])
  
  const [lastUpdate, setLastUpdate] = useState<string>(getCurrentTime())
  const [mounted, setMounted] = useState(false)

  // 컴포넌트 마운트 및 자동 업데이트
  useEffect(() => {
    setMounted(true)
    const interval = setInterval(() => {
      setLastUpdate(getCurrentTime())
      if (autoTradingStatus.is_running) {
        setAutoTradingStatus(prev => ({
          ...prev,
          running_time: prev.running_time + 5
        }))
      }
    }, 5000)
    return () => clearInterval(interval)
  }, [autoTradingStatus.is_running])

  const toggleAutoTrading = () => {
    if (!autoTradingStatus.is_running) {
      // 자동매매 시작 시 연결 진행 상태 표시
      setConnectionStatus({
        is_connecting: true,
        steps: [
          { name: '키움 API 연결', status: 'pending' },
          { name: '계좌 인증', status: 'waiting' },
          { name: '시장 데이터 연결', status: 'waiting' },
          { name: '전략 초기화', status: 'waiting' },
          { name: '자동매매 준비완료', status: 'waiting' }
        ]
      })
      
      // 연결 진행 시뮬레이션
      let stepIndex = 0
      const interval = setInterval(() => {
        setConnectionStatus(prev => {
          const newSteps = [...prev.steps]
          if (stepIndex < newSteps.length) {
            newSteps[stepIndex] = { ...newSteps[stepIndex], status: 'completed' }
            if (stepIndex + 1 < newSteps.length) {
              newSteps[stepIndex + 1] = { ...newSteps[stepIndex + 1], status: 'pending' }
            }
            stepIndex++
          }
          
          if (stepIndex >= newSteps.length) {
            clearInterval(interval)
            setAutoTradingStatus(prev => ({ ...prev, is_running: true }))
            return { is_connecting: false, steps: newSteps }
          }
          
          return { ...prev, steps: newSteps }
        })
      }, 1000)
    } else {
      setAutoTradingStatus(prev => ({ ...prev, is_running: false }))
    }
  }

  const saveRiskSettings = () => {
    alert('리스크 설정이 저장되었습니다.')
  }

  if (!mounted) {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-900">
      {/* 헤더 */}
      <header className="bg-gradient-to-r from-gray-800 to-gray-700 border-b border-gray-600 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                <BarChart3 className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">QuanTrade Pro</h1>
                <p className="text-gray-300 text-sm">Professional Auto Trading System</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-6">
              <div className="text-right">
                <p className="text-gray-300 text-sm">거래 모드</p>
                <div className="flex items-center space-x-2">
                  <div className={`w-2 h-2 rounded-full ${tradingMode === 'real' ? 'bg-red-500' : 'bg-blue-500'}`}></div>
                  <span className={`font-semibold text-sm ${tradingMode === 'real' ? 'text-red-400' : 'text-blue-400'}`}>
                    {tradingMode === 'real' ? '실제매매' : '모의투자'}
                  </span>
                  <button 
                    onClick={() => setTradingMode(tradingMode === 'real' ? 'simulation' : 'real')}
                    className="text-gray-400 hover:text-white text-xs px-2 py-1 border border-gray-600 rounded hover:border-gray-400 transition-all"
                  >
                    전환
                  </button>
                </div>
              </div>
              
              <div className="text-right">
                <p className="text-gray-300 text-sm">키움 API</p>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></div>
                  <span className="text-white font-semibold">연결됨</span>
                </div>
              </div>
              
              <div className="text-right">
                <p className="text-gray-300 text-sm">마지막 업데이트</p>
                <p className="text-white font-mono">{lastUpdate}</p>
              </div>
              
              <button
                onClick={toggleAutoTrading}
                disabled={connectionStatus.is_connecting}
                className={`px-6 py-3 rounded-xl font-semibold transition-all ${
                  connectionStatus.is_connecting
                    ? 'bg-gradient-to-r from-gray-500 to-gray-600 text-white cursor-not-allowed'
                    : autoTradingStatus.is_running
                    ? 'bg-gradient-to-r from-red-500 to-red-600 text-white shadow-lg'
                    : 'bg-gradient-to-r from-green-500 to-green-600 text-white shadow-lg'
                } hover:shadow-xl disabled:hover:shadow-lg`}
              >
                {connectionStatus.is_connecting ? '연결 중...' : autoTradingStatus.is_running ? '자동매매 중지' : '자동매매 시작'}
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 xl:grid-cols-4 gap-8">
          
          {/* 왼쪽 사이드바 */}
          <div className="xl:col-span-1 space-y-6">
            
            {/* 계좌 정보 */}
            <div className="bg-gradient-to-br from-gray-800 to-gray-700 rounded-2xl border border-gray-600 p-6 shadow-xl">
              <h2 className="text-lg font-bold text-white mb-4 flex items-center">
                <Wallet className="w-5 h-5 mr-2 text-blue-400" />
                계좌 정보
              </h2>
              
              <div className="space-y-4">
                <div className="bg-gray-700/50 border border-gray-600 rounded-xl p-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-gray-300 text-sm">계좌번호</span>
                    <span className="text-white font-mono text-sm">{accountInfo.account_number}</span>
                  </div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-gray-300 text-sm">가용자금</span>
                    <span className="text-green-400 font-bold">{formatCurrency(accountInfo.available_cash)}</span>
                  </div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-gray-300 text-sm">총 자산</span>
                    <span className="text-white font-bold">{formatCurrency(accountInfo.total_cash)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-300 text-sm">신용한도</span>
                    <span className="text-blue-400 font-bold">{formatCurrency(accountInfo.credit_limit)}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* 자동매매 상태 */}
            <div className="bg-gradient-to-br from-gray-800 to-gray-700 rounded-2xl border border-gray-600 p-6 shadow-xl">
              <h2 className="text-lg font-bold text-white mb-4 flex items-center">
                <Activity className="w-5 h-5 mr-2 text-green-400" />
                자동매매 상태
              </h2>
              
              <div className="space-y-4">
                <div className="bg-gray-700/50 border border-gray-600 rounded-xl p-4">
                  <div className="flex justify-between items-center mb-3">
                    <span className="text-gray-300 text-sm">현재 상태</span>
                    <div className="flex items-center space-x-2">
                      <div className={`w-2 h-2 rounded-full ${
                        autoTradingStatus.is_running ? 'bg-green-400 animate-pulse' : 'bg-gray-400'
                      }`}></div>
                      <span className={`font-semibold text-sm ${
                        autoTradingStatus.is_running ? 'text-green-400' : 'text-gray-400'
                      }`}>
                        {autoTradingStatus.is_running ? '실행중' : '중지'}
                      </span>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div className="text-center p-2 bg-gray-600/50 rounded-lg">
                      <p className="text-gray-400">실행된 전략</p>
                      <p className="text-white font-bold">{autoTradingStatus.active_strategies}개</p>
                    </div>
                    <div className="text-center p-2 bg-gray-600/50 rounded-lg">
                      <p className="text-gray-400">오늘 체결</p>
                      <p className="text-white font-bold">{autoTradingStatus.today_trades}건</p>
                    </div>
                  </div>
                  
                  <div className="mt-3 text-center">
                    <p className="text-gray-400 text-sm">총 수익률</p>
                    <p className="text-green-400 font-bold text-lg">
                      {formatPercentage(autoTradingStatus.total_return)}
                    </p>
                  </div>
                  
                  {autoTradingStatus.is_running && (
                    <div className="mt-3 text-center">
                      <p className="text-gray-400 text-sm">실행 시간</p>
                      <p className="text-white font-mono">{formatTime(autoTradingStatus.running_time)}</p>
                    </div>
                  )}
                </div>

                {/* 연결 상태 표시 */}
                {connectionStatus.is_connecting && (
                  <div className="bg-gray-700/50 border border-gray-600 rounded-xl p-4 mt-4">
                    <h4 className="text-white font-semibold mb-3 text-center">자동매매 시작 중...</h4>
                    <div className="space-y-2">
                      {connectionStatus.steps.map((step, index) => (
                        <div key={index} className="flex items-center space-x-3">
                          <div className={`w-3 h-3 rounded-full ${
                            step.status === 'completed' ? 'bg-green-400' :
                            step.status === 'pending' ? 'bg-yellow-400 animate-pulse' :
                            'bg-gray-500'
                          }`}></div>
                          <span className={`text-sm ${
                            step.status === 'completed' ? 'text-green-400' :
                            step.status === 'pending' ? 'text-yellow-400' :
                            'text-gray-400'
                          }`}>
                            {step.name}
                          </span>
                          {step.status === 'completed' && (
                            <span className="text-green-400 text-xs">✓</span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* 리스크 관리 */}
            <div className="bg-gradient-to-br from-gray-800 to-gray-700 rounded-2xl border border-gray-600 p-6 shadow-xl">
              <h2 className="text-lg font-bold text-white mb-4 flex items-center">
                <Settings className="w-5 h-5 mr-2 text-red-400" />
                리스크 관리
              </h2>
              
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <label className="text-gray-300 text-sm">일일손실한도</label>
                  <div className="flex items-center space-x-1">
                    <input
                      type="number"
                      step="0.1"
                      value={riskSettings.daily_loss_limit}
                      onChange={(e) => setRiskSettings(prev => ({
                        ...prev,
                        daily_loss_limit: parseFloat(e.target.value)
                      }))}
                      className="w-16 px-2 py-1 bg-gray-700 border border-gray-600 text-white text-sm rounded focus:border-blue-500"
                    />
                    <span className="text-gray-400 text-sm">%</span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <label className="text-gray-300 text-sm">포지션크기</label>
                  <div className="flex items-center space-x-1">
                    <input
                      type="number"
                      step="0.1"
                      value={riskSettings.position_size_limit}
                      onChange={(e) => setRiskSettings(prev => ({
                        ...prev,
                        position_size_limit: parseFloat(e.target.value)
                      }))}
                      className="w-16 px-2 py-1 bg-gray-700 border border-gray-600 text-white text-sm rounded focus:border-blue-500"
                    />
                    <span className="text-gray-400 text-sm">%</span>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <label className="text-gray-300 text-sm">최대보유</label>
                  <div className="flex items-center space-x-1">
                    <input
                      type="number"
                      value={riskSettings.max_positions}
                      onChange={(e) => setRiskSettings(prev => ({
                        ...prev,
                        max_positions: parseInt(e.target.value)
                      }))}
                      className="w-16 px-2 py-1 bg-gray-700 border border-gray-600 text-white text-sm rounded focus:border-blue-500"
                    />
                    <span className="text-gray-400 text-sm">개</span>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <label className="text-gray-300 text-sm">손절기준</label>
                  <div className="flex items-center space-x-1">
                    <input
                      type="number"
                      step="0.1"
                      value={riskSettings.stop_loss_rate}
                      onChange={(e) => setRiskSettings(prev => ({
                        ...prev,
                        stop_loss_rate: parseFloat(e.target.value)
                      }))}
                      className="w-16 px-2 py-1 bg-gray-700 border border-gray-600 text-white text-sm rounded focus:border-blue-500"
                    />
                    <span className="text-gray-400 text-sm">%</span>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <label className="text-gray-300 text-sm">익절기준</label>
                  <div className="flex items-center space-x-1">
                    <input
                      type="number"
                      step="0.1"
                      value={riskSettings.take_profit_rate}
                      onChange={(e) => setRiskSettings(prev => ({
                        ...prev,
                        take_profit_rate: parseFloat(e.target.value)
                      }))}
                      className="w-16 px-2 py-1 bg-gray-700 border border-gray-600 text-white text-sm rounded focus:border-blue-500"
                    />
                    <span className="text-gray-400 text-sm">%</span>
                  </div>
                </div>

                <button
                  onClick={saveRiskSettings}
                  className="w-full mt-4 bg-gradient-to-r from-orange-500 to-red-600 text-white py-2 rounded-xl font-medium hover:from-orange-600 hover:to-red-700 transition-all"
                >
                  설정 저장
                </button>
              </div>
            </div>
          </div>

          {/* 메인 컨텐츠 영역 */}
          <div className="xl:col-span-3">
            {/* 탭 네비게이션 */}
            <div className="flex space-x-1 bg-gray-800 rounded-2xl p-1 mb-8 border border-gray-700">
              {[
                { id: 'positions', label: '실시간포지션', icon: Target },
                { id: 'charts', label: '일일손익현황', icon: TrendingUp },
                { id: 'trading', label: '거래현황', icon: Activity },
                { id: 'strategies', label: '자동매매전략', icon: Settings }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setSelectedTab(tab.id as any)}
                  className={`flex items-center space-x-2 px-6 py-3 rounded-xl font-semibold transition-all flex-1 justify-center ${
                    selectedTab === tab.id
                      ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg'
                      : 'text-gray-400 hover:text-white hover:bg-gray-700'
                  }`}
                >
                  <tab.icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              ))}
            </div>

            {/* 탭 컨텐츠 */}
            {selectedTab === 'positions' && (
              <div className="space-y-6">
                {/* 포지션 요약 카드 */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  <div className="bg-gradient-to-br from-gray-800 to-gray-700 rounded-2xl border border-gray-600 p-6 shadow-xl">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-lg font-semibold text-white">총 평가액</h3>
                      <Wallet className="w-5 h-5 text-green-400" />
                    </div>
                    <p className="text-3xl font-bold text-white mb-1">
                      {formatCurrency(positions.reduce((sum, pos) => sum + (pos.quantity * pos.current_price), 0))}
                    </p>
                    <p className="text-gray-400 text-sm">현재 보유 주식 가치</p>
                  </div>

                  <div className="bg-gradient-to-br from-gray-800 to-gray-700 rounded-2xl border border-gray-600 p-6 shadow-xl">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-lg font-semibold text-white">평가손익</h3>
                      {positions.reduce((sum, pos) => sum + pos.unrealized_pnl, 0) >= 0 ?
                        <TrendingUp className="w-5 h-5 text-green-400" /> :
                        <TrendingDown className="w-5 h-5 text-red-400" />
                      }
                    </div>
                    <p className={`text-3xl font-bold mb-1 ${
                      positions.reduce((sum, pos) => sum + pos.unrealized_pnl, 0) >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {formatCurrency(positions.reduce((sum, pos) => sum + pos.unrealized_pnl, 0))}
                    </p>
                    <p className={`text-sm font-semibold ${
                      positions.reduce((sum, pos) => sum + pos.unrealized_pnl, 0) >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {formatPercentage(positions.reduce((sum, pos) => sum + pos.unrealized_pnl_rate * pos.weight, 0) / 100)}
                    </p>
                  </div>

                  <div className="bg-gradient-to-br from-gray-800 to-gray-700 rounded-2xl border border-gray-600 p-6 shadow-xl">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-lg font-semibold text-white">보유종목</h3>
                      <Target className="w-5 h-5 text-purple-400" />
                    </div>
                    <p className="text-3xl font-bold text-white mb-1">{positions.length}</p>
                    <p className="text-gray-400 text-sm">개 종목 보유중</p>
                  </div>

                  <div className="bg-gradient-to-br from-gray-800 to-gray-700 rounded-2xl border border-gray-600 p-6 shadow-xl">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-lg font-semibold text-white">업데이트</h3>
                      <RefreshCw className="w-5 h-5 text-blue-400 animate-spin" />
                    </div>
                    <p className="text-lg font-bold text-white mb-1">실시간</p>
                    <p className="text-gray-400 text-sm">자동 새로고침 ON</p>
                  </div>
                </div>

                {/* 실시간 포지션 테이블 */}
                <div className="bg-gradient-to-br from-gray-800 to-gray-700 rounded-2xl border border-gray-600 p-6 shadow-xl">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-xl font-bold text-white flex items-center">
                      <Activity className="w-6 h-6 mr-2 text-yellow-400" />
                      현재 보유 포지션
                    </h3>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                      <span className="text-green-400 text-sm font-semibold">실시간 업데이트</span>
                    </div>
                  </div>
                  
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="text-gray-400 text-sm border-b border-gray-600">
                          <th className="text-left py-4 px-2">전략/종목</th>
                          <th className="text-right py-4 px-2">수량</th>
                          <th className="text-right py-4 px-2">평균단가</th>
                          <th className="text-right py-4 px-2">현재가</th>
                          <th className="text-right py-4 px-2">평가액</th>
                          <th className="text-right py-4 px-2">손익</th>
                          <th className="text-right py-4 px-2">손익률</th>
                          <th className="text-right py-4 px-2">비중</th>
                        </tr>
                      </thead>
                      <tbody>
                        {positions.map((position, index) => (
                          <tr key={position.id} className="border-b border-gray-700 hover:bg-gray-750 transition-all">
                            <td className="py-4 px-2">
                              <div>
                                <p className="text-white font-semibold">{position.stock_name}</p>
                                <p className="text-gray-400 text-sm">{position.strategy_name}</p>
                                <p className="text-gray-500 text-xs">{position.stock_code}</p>
                              </div>
                            </td>
                            <td className="text-right py-4 px-2 text-white font-mono">
                              {position.quantity.toLocaleString()}주
                            </td>
                            <td className="text-right py-4 px-2 text-gray-300 font-mono">
                              {formatCurrency(position.avg_price)}
                            </td>
                            <td className="text-right py-4 px-2 text-white font-mono font-bold">
                              {formatCurrency(position.current_price)}
                            </td>
                            <td className="text-right py-4 px-2 text-white font-mono font-bold">
                              {formatCurrency(position.quantity * position.current_price)}
                            </td>
                            <td className={`text-right py-4 px-2 font-mono font-bold ${
                              position.unrealized_pnl >= 0 ? 'text-green-400' : 'text-red-400'
                            }`}>
                              {position.unrealized_pnl >= 0 ? '+' : ''}{formatCurrency(position.unrealized_pnl)}
                            </td>
                            <td className={`text-right py-4 px-2 font-mono font-bold ${
                              position.unrealized_pnl_rate >= 0 ? 'text-green-400' : 'text-red-400'
                            }`}>
                              {formatPercentage(position.unrealized_pnl_rate)}
                            </td>
                            <td className="text-right py-4 px-2 text-blue-400 font-mono">
                              {position.weight}%
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {selectedTab === 'charts' && (
              <div className="space-y-6">
                {/* 일일 손익 현황 */}
                <div className="bg-gradient-to-br from-gray-800 to-gray-700 rounded-2xl border border-gray-600 p-6 shadow-xl">
                  <h3 className="text-xl font-bold text-white mb-6 flex items-center">
                    <TrendingUp className="w-6 h-6 mr-2 text-green-400" />
                    일일 손익 현황
                  </h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                    <div className="text-center p-4 bg-green-500/20 border border-green-500 rounded-xl">
                      <p className="text-green-400 font-bold text-2xl">+₩95,000</p>
                      <p className="text-green-300 text-sm">오늘 실현손익</p>
                    </div>
                    
                    <div className="text-center p-4 bg-blue-500/20 border border-blue-500 rounded-xl">
                      <p className="text-blue-400 font-bold text-2xl">+₩305,000</p>
                      <p className="text-blue-300 text-sm">평가손익</p>
                    </div>
                    
                    <div className="text-center p-4 bg-purple-500/20 border border-purple-500 rounded-xl">
                      <p className="text-purple-400 font-bold text-2xl">+₩400,000</p>
                      <p className="text-purple-300 text-sm">총 손익</p>
                    </div>
                    
                    <div className="text-center p-4 bg-yellow-500/20 border border-yellow-500 rounded-xl">
                      <p className="text-yellow-400 font-bold text-2xl">+2.34%</p>
                      <p className="text-yellow-300 text-sm">수익률</p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="bg-gray-700/50 border border-gray-600 rounded-xl p-4">
                      <h4 className="text-white font-semibold mb-4">시간별 손익</h4>
                      <div className="space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-gray-400 text-sm">09:00-10:00</span>
                          <span className="text-green-400 font-semibold">+₩45,000</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-gray-400 text-sm">10:00-11:00</span>
                          <span className="text-red-400 font-semibold">-₩15,000</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-gray-400 text-sm">11:00-12:00</span>
                          <span className="text-green-400 font-semibold">+₩25,000</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-gray-400 text-sm">13:00-14:00</span>
                          <span className="text-green-400 font-semibold">+₩40,000</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-gray-400 text-sm">14:00-현재</span>
                          <span className="text-blue-400 font-semibold">진행중</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-gray-700/50 border border-gray-600 rounded-xl p-4">
                      <h4 className="text-white font-semibold mb-4">전략별 수익</h4>
                      <div className="space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-gray-400 text-sm">볼린저밴드</span>
                          <span className="text-green-400 font-semibold">+₩125,000</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-gray-400 text-sm">RSI 역추세</span>
                          <span className="text-red-400 font-semibold">-₩30,000</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-gray-400 text-sm">모멘텀</span>
                          <span className="text-gray-500 font-semibold">₩0</span>
                        </div>
                        <div className="border-t border-gray-600 pt-2 mt-3">
                          <div className="flex justify-between items-center">
                            <span className="text-white font-semibold">총합</span>
                            <span className="text-green-400 font-bold">+₩95,000</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* 신호 현황 */}
                <div className="bg-gradient-to-br from-gray-800 to-gray-700 rounded-2xl border border-gray-600 p-6 shadow-xl">
                  <h3 className="text-xl font-bold text-white mb-6 flex items-center">
                    <Target className="w-6 h-6 mr-2 text-cyan-400" />
                    실시간 신호 현황
                  </h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                    <div className="text-center p-4 bg-yellow-500/20 border border-yellow-500 rounded-xl">
                      <p className="text-yellow-400 font-bold text-2xl">
                        {strategies.reduce((sum, s) => sum + s.signals_waiting, 0)}개
                      </p>
                      <p className="text-yellow-300 text-sm">대기중 신호</p>
                    </div>
                    
                    <div className="text-center p-4 bg-green-500/20 border border-green-500 rounded-xl">
                      <p className="text-green-400 font-bold text-2xl">
                        {strategies.reduce((sum, s) => sum + s.signals_processed, 0)}개
                      </p>
                      <p className="text-green-300 text-sm">처리된 신호</p>
                    </div>
                    
                    <div className="text-center p-4 bg-red-500/20 border border-red-500 rounded-xl">
                      <p className="text-red-400 font-bold text-2xl">
                        {strategies.reduce((sum, s) => sum + s.signals_rejected, 0)}개
                      </p>
                      <p className="text-red-300 text-sm">거부된 신호</p>
                    </div>
                  </div>

                  <div className="bg-gray-700/50 border border-gray-600 rounded-xl p-4">
                    <h4 className="text-white font-semibold mb-4">최근 신호</h4>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between p-3 bg-gray-600/50 rounded-lg">
                        <div className="flex items-center space-x-3">
                          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                          <div>
                            <p className="text-white font-semibold">삼성전자 매수</p>
                            <p className="text-gray-400 text-sm">볼린저밴드 전략 • 14:25:30</p>
                          </div>
                        </div>
                        <span className="px-2 py-1 bg-green-500 text-white text-xs rounded">처리됨</span>
                      </div>
                      
                      <div className="flex items-center justify-between p-3 bg-gray-600/50 rounded-lg">
                        <div className="flex items-center space-x-3">
                          <div className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse"></div>
                          <div>
                            <p className="text-white font-semibold">NAVER 매도</p>
                            <p className="text-gray-400 text-sm">RSI 역추세 전략 • 14:23:15</p>
                          </div>
                        </div>
                        <span className="px-2 py-1 bg-yellow-500 text-white text-xs rounded">대기중</span>
                      </div>
                      
                      <div className="flex items-center justify-between p-3 bg-gray-600/50 rounded-lg">
                        <div className="flex items-center space-x-3">
                          <div className="w-2 h-2 bg-red-400 rounded-full"></div>
                          <div>
                            <p className="text-white font-semibold">카카오 매수</p>
                            <p className="text-gray-400 text-sm">모멘텀 전략 • 14:20:45</p>
                          </div>
                        </div>
                        <span className="px-2 py-1 bg-red-500 text-white text-xs rounded">거부됨</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {selectedTab === 'trading' && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="bg-gradient-to-br from-gray-800 to-gray-700 rounded-2xl border border-gray-600 p-6 shadow-xl">
                    <h3 className="text-lg font-semibold text-white mb-3">오늘 총 거래</h3>
                    <p className="text-3xl font-bold text-white">{trades.length}건</p>
                    <p className="text-gray-400 text-sm">매수 {trades.filter(t => t.type === 'BUY').length}건 / 매도 {trades.filter(t => t.type === 'SELL').length}건</p>
                  </div>
                  
                  <div className="bg-gradient-to-br from-gray-800 to-gray-700 rounded-2xl border border-gray-600 p-6 shadow-xl">
                    <h3 className="text-lg font-semibold text-white mb-3">거래 금액</h3>
                    <p className="text-3xl font-bold text-green-400">
                      {formatCurrency(trades.reduce((sum, t) => sum + (t.quantity * t.price), 0))}
                    </p>
                    <p className="text-gray-400 text-sm">총 거래대금</p>
                  </div>
                  
                  <div className="bg-gradient-to-br from-gray-800 to-gray-700 rounded-2xl border border-gray-600 p-6 shadow-xl">
                    <h3 className="text-lg font-semibold text-white mb-3">평균 체결시간</h3>
                    <p className="text-3xl font-bold text-blue-400">0.3초</p>
                    <p className="text-gray-400 text-sm">수수료 총액: ₩15,200</p>
                  </div>
                </div>

                <div className="bg-gradient-to-br from-gray-800 to-gray-700 rounded-2xl border border-gray-600 p-6 shadow-xl">
                  <h3 className="text-xl font-bold text-white mb-6 flex items-center">
                    <Clock className="w-6 h-6 mr-2 text-green-400" />
                    최근 거래내역
                  </h3>
                  
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="text-gray-400 text-sm border-b border-gray-600">
                          <th className="text-left py-4 px-2">시간</th>
                          <th className="text-left py-4 px-2">종목</th>
                          <th className="text-center py-4 px-2">구분</th>
                          <th className="text-right py-4 px-2">수량</th>
                          <th className="text-right py-4 px-2">단가</th>
                          <th className="text-right py-4 px-2">거래금액</th>
                          <th className="text-center py-4 px-2">상태</th>
                        </tr>
                      </thead>
                      <tbody>
                        {trades.map((trade) => (
                          <tr key={trade.id} className="border-b border-gray-700 hover:bg-gray-750 transition-all">
                            <td className="py-4 px-2 text-gray-300 font-mono">{trade.time}</td>
                            <td className="py-4 px-2">
                              <div>
                                <p className="text-white font-semibold">{trade.stock_name}</p>
                                <p className="text-gray-400 text-xs">{trade.stock_code}</p>
                              </div>
                            </td>
                            <td className="text-center py-4 px-2">
                              <span className={`px-3 py-1 rounded-lg text-xs font-semibold ${
                                trade.type === 'BUY'
                                  ? 'bg-red-500 text-white'
                                  : 'bg-blue-500 text-white'
                              }`}>
                                {trade.type === 'BUY' ? '매수' : '매도'}
                              </span>
                            </td>
                            <td className="text-right py-4 px-2 text-white font-mono">
                              {trade.quantity.toLocaleString()}주
                            </td>
                            <td className="text-right py-4 px-2 text-white font-mono">
                              {formatCurrency(trade.price)}
                            </td>
                            <td className="text-right py-4 px-2 text-white font-mono font-bold">
                              {formatCurrency(trade.quantity * trade.price)}
                            </td>
                            <td className="text-center py-4 px-2">
                              <span className={`px-3 py-1 rounded-lg text-xs font-semibold ${
                                trade.status === 'COMPLETED' ? 'bg-green-500 text-white' :
                                trade.status === 'PENDING' ? 'bg-yellow-500 text-white' :
                                'bg-gray-500 text-white'
                              }`}>
                                {trade.status === 'COMPLETED' ? '체결' :
                                 trade.status === 'PENDING' ? '대기' : '취소'}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {selectedTab === 'strategies' && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="bg-gradient-to-br from-gray-800 to-gray-700 rounded-2xl border border-gray-600 p-6 shadow-xl">
                    <h3 className="text-lg font-semibold text-white mb-3">오늘 수익</h3>
                    <p className="text-3xl font-bold text-green-400">
                      +{formatCurrency(strategies.reduce((sum, s) => sum + s.today_profit, 0))}
                    </p>
                    <p className="text-gray-400 text-sm">전략별 합계</p>
                  </div>
                  
                  <div className="bg-gradient-to-br from-gray-800 to-gray-700 rounded-2xl border border-gray-600 p-6 shadow-xl">
                    <h3 className="text-lg font-semibold text-white mb-3">평균 승률</h3>
                    <p className="text-3xl font-bold text-blue-400">
                      {Math.round(strategies.reduce((sum, s) => sum + s.win_rate, 0) / strategies.filter(s => s.is_active).length)}%
                    </p>
                    <p className="text-gray-400 text-sm">활성 전략 기준</p>
                  </div>
                  
                  <div className="bg-gradient-to-br from-gray-800 to-gray-700 rounded-2xl border border-gray-600 p-6 shadow-xl">
                    <h3 className="text-lg font-semibold text-white mb-3">최대손실</h3>
                    <p className="text-3xl font-bold text-red-400">
                      {formatCurrency(Math.min(...strategies.map(s => s.max_loss)))}
                    </p>
                    <p className="text-gray-400 text-sm">단일 전략 최대</p>
                  </div>
                </div>

                <div className="bg-gradient-to-br from-gray-800 to-gray-700 rounded-2xl border border-gray-600 p-6 shadow-xl">
                  <h3 className="text-xl font-bold text-white mb-6 flex items-center">
                    <Settings className="w-6 h-6 mr-2 text-purple-400" />
                    자동매매 전략 관리
                  </h3>
                  
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {strategies.map((strategy) => (
                      <div key={strategy.id} className={`p-6 rounded-xl border transition-all ${
                        strategy.is_active
                          ? 'bg-gradient-to-r from-blue-500/20 to-purple-600/20 border-blue-500'
                          : 'bg-gray-700/50 border-gray-600'
                      }`}>
                        <div className="flex items-center justify-between mb-4">
                          <h4 className="text-lg font-semibold text-white">{strategy.name}</h4>
                          <div className={`w-3 h-3 rounded-full ${
                            strategy.is_active ? 'bg-green-400 animate-pulse' : 'bg-gray-500'
                          }`}></div>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4 mb-4">
                          <div>
                            <p className="text-gray-400 text-sm">오늘 수익</p>
                            <p className={`font-bold ${
                              strategy.today_profit >= 0 ? 'text-green-400' : 'text-red-400'
                            }`}>
                              {strategy.today_profit >= 0 ? '+' : ''}{formatCurrency(strategy.today_profit)}
                            </p>
                          </div>
                          <div>
                            <p className="text-gray-400 text-sm">승률</p>
                            <p className="text-white font-bold">{strategy.win_rate}%</p>
                          </div>
                        </div>
                        
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-400">대기 신호:</span>
                            <span className="text-yellow-400 font-semibold">{strategy.signals_waiting}개</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-400">처리 완료:</span>
                            <span className="text-green-400 font-semibold">{strategy.signals_processed}개</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-400">신호 거부:</span>
                            <span className="text-red-400 font-semibold">{strategy.signals_rejected}개</span>
                          </div>
                        </div>
                        
                        <div className="mt-4 pt-4 border-t border-gray-600">
                          <button className={`w-full py-2 rounded-lg font-medium transition-all ${
                            strategy.is_active
                              ? 'bg-gradient-to-r from-red-500 to-red-600 text-white hover:from-red-600 hover:to-red-700'
                              : 'bg-gradient-to-r from-green-500 to-green-600 text-white hover:from-green-600 hover:to-green-700'
                          }`}>
                            {strategy.is_active ? '전략 중지' : '전략 시작'}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-gradient-to-br from-gray-800 to-gray-700 rounded-2xl border border-gray-600 p-6 shadow-xl">
                  <h3 className="text-xl font-bold text-white mb-6 flex items-center">
                    <Target className="w-6 h-6 mr-2 text-cyan-400" />
                    신호 현황
                  </h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="text-center p-4 bg-yellow-500/20 border border-yellow-500 rounded-xl">
                      <p className="text-yellow-400 font-bold text-2xl">
                        {strategies.reduce((sum, s) => sum + s.signals_waiting, 0)}개
                      </p>
                      <p className="text-yellow-300 text-sm">대기중 신호</p>
                    </div>
                    
                    <div className="text-center p-4 bg-green-500/20 border border-green-500 rounded-xl">
                      <p className="text-green-400 font-bold text-2xl">
                        {strategies.reduce((sum, s) => sum + s.signals_processed, 0)}개
                      </p>
                      <p className="text-green-300 text-sm">처리된 신호</p>
                    </div>
                    
                    <div className="text-center p-4 bg-red-500/20 border border-red-500 rounded-xl">
                      <p className="text-red-400 font-bold text-2xl">
                        {strategies.reduce((sum, s) => sum + s.signals_rejected, 0)}개
                      </p>
                      <p className="text-red-300 text-sm">거부된 신호</p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}