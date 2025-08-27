'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

interface SystemStatus {
  current_mode: 'DEMO' | 'REAL'
  is_windows: boolean
  kiwoom_api_available: boolean
  account_connected: boolean
  account_info?: {
    account_number: string
    server_type: string
    available_cash: number
  }
}

export default function TradingModeSelector() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null)
  const [selectedMode, setSelectedMode] = useState<'DEMO' | 'REAL'>('DEMO')
  const [loading, setLoading] = useState(true)
  const [isChanging, setIsChanging] = useState(false)
  const [showRealTradeWarning, setShowRealTradeWarning] = useState(false)
  const [acceptedTerms, setAcceptedTerms] = useState(false)
  const [confirmationText, setConfirmationText] = useState('')
  const router = useRouter()

  useEffect(() => {
    checkSystemStatus()
  }, [])

  const checkSystemStatus = async () => {
    try {
      const response = await fetch('/api/proxy/system/trading-mode')
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      setSystemStatus(data)
      setSelectedMode(data.current_mode)
    } catch (error) {
      console.error('시스템 상태 확인 실패:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleModeChange = async (mode: 'DEMO' | 'REAL') => {
    if (mode === 'REAL') {
      setShowRealTradeWarning(true)
      return
    }
    
    await changeTradingMode(mode)
  }

  const changeTradingMode = async (mode: 'DEMO' | 'REAL') => {
    setIsChanging(true)
    
    try {
      const response = await fetch('/api/proxy/system/change-trading-mode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode })
      })

      if (response.ok) {
        setSelectedMode(mode)
        await checkSystemStatus()
        
        if (mode === 'DEMO') {
          alert('모의투자 모드로 변경되었습니다.')
        } else {
          alert('실거래 모드로 변경되었습니다. 주의해서 거래하세요!')
        }
      } else {
        const error = await response.json()
        alert(`모드 변경 실패: ${error.detail}`)
      }
    } catch (error) {
      console.error('모드 변경 실패:', error)
      alert('모드 변경 중 오류가 발생했습니다.')
    } finally {
      setIsChanging(false)
      setShowRealTradeWarning(false)
      setAcceptedTerms(false)
      setConfirmationText('')
    }
  }

  const handleRealTradeConfirm = () => {
    if (!acceptedTerms) {
      alert('위험 고지를 먼저 확인해주세요.')
      return
    }

    if (confirmationText !== 'START REAL TRADING') {
      alert('확인 텍스트를 정확히 입력해주세요.')
      return
    }

    changeTradingMode('REAL')
  }

  const startTrading = () => {
    router.push('/dashboard')
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">시스템 상태 확인 중...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* 헤더 */}
      <header className="bg-gray-800 px-6 py-4 border-b border-gray-700">
        <h1 className="text-2xl font-bold text-green-400">QuanTrade Pro - 거래 모드 선택</h1>
      </header>

      <div className="container mx-auto px-6 py-8">
        <div className="max-w-4xl mx-auto">
          
          {/* 현재 시스템 상태 */}
          <div className="bg-gray-800 rounded-lg p-6 mb-8">
            <button
              onClick={startTrading}
              className="px-8 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-semibold transition-all"
            >
              트레이딩 시작
            </button>
          </div>

          {/* 주의사항 */}
          <div className="bg-yellow-900/20 border border-yellow-600 rounded-lg p-6">
            <h3 className="text-yellow-400 font-semibold mb-3">⚠️ 중요 안내사항</h3>
            <ul className="space-y-2 text-sm">
              <li>• <strong>모의투자:</strong> 가상의 돈으로 거래하므로 실제 손익이 발생하지 않습니다</li>
              <li>• <strong>실거래:</strong> 실제 돈으로 거래하므로 투자 손실 위험이 있습니다</li>
              <li>• 실거래 전에는 반드시 모의투자로 충분한 테스트를 진행하세요</li>
              <li>• 시스템 오류나 네트워크 장애로 인한 손실 가능성이 있습니다</li>
              <li>• 소액으로 시작하여 점진적으로 투자금액을 늘려가세요</li>
            </ul>
          </div>
        </div>
      </div>

      {/* 실거래 확인 모달 */}
      {showRealTradeWarning && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-8 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="text-center mb-6">
              <div className="text-6xl mb-4">⚠️</div>
              <h2 className="text-2xl font-bold text-red-400">실거래 모드 경고</h2>
            </div>

            <div className="space-y-4 text-sm mb-6">
              <div className="bg-red-900/30 p-4 rounded">
                <h3 className="font-bold text-red-400 mb-2">🚨 위험 고지</h3>
                <ul className="space-y-1">
                  <li>• 이 소프트웨어는 실제 돈으로 자동매매를 실행합니다</li>
                  <li>• 투자원금 손실 위험이 있습니다</li>
                  <li>• 시스템 오류, 네트워크 장애로 인한 손실 가능성이 있습니다</li>
                  <li>• 급격한 시장 변동 시 큰 손실이 발생할 수 있습니다</li>
                  <li>• 개발자는 투자 손실에 대해 어떠한 책임도 지지 않습니다</li>
                </ul>
              </div>

              <div className="bg-yellow-900/30 p-4 rounded">
                <h3 className="font-bold text-yellow-400 mb-2">✅ 사전 준비사항</h3>
                <ul className="space-y-1">
                  <li>• 키움증권 계좌 개설 및 Open API+ 설치 완료</li>
                  <li>• 모의투자로 최소 1개월 이상 테스트 완료</li>
                  <li>• 손절/익절 설정 및 리스크 관리 설정 확인</li>
                  <li>• 투자 가능한 소액으로 시작 (권장: 10만원 이하)</li>
                  <li>• 실시간 모니터링 가능한 환경 구축</li>
                </ul>
              </div>
            </div>

            <div className="space-y-4">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={acceptedTerms}
                  onChange={(e) => setAcceptedTerms(e.target.checked)}
                  className="w-4 h-4"
                />
                <span className="text-sm">위험 고지를 모두 읽고 이해했으며, 모든 투자 손실에 대한 책임을 집니다</span>
              </label>

              <div>
                <label className="block text-sm mb-2">
                  확인을 위해 <span className="text-red-400 font-bold">"START REAL TRADING"</span>을 입력하세요:
                </label>
                <input
                  type="text"
                  value={confirmationText}
                  onChange={(e) => setConfirmationText(e.target.value)}
                  className="w-full p-3 bg-gray-700 rounded text-white"
                  placeholder="START REAL TRADING"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-4 mt-6">
              <button
                onClick={() => setShowRealTradeWarning(false)}
                className="px-6 py-2 bg-gray-600 hover:bg-gray-700 rounded text-white"
              >
                취소
              </button>
              <button
                onClick={handleRealTradeConfirm}
                disabled={!acceptedTerms || confirmationText !== 'START REAL TRADING'}
                className="px-6 py-2 bg-red-600 hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed rounded text-white font-semibold"
              >
                실거래 시작
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}<h2 className="text-xl font-semibold mb-4">📊 현재 시스템 상태</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gray-700 p-4 rounded">
                <div className="text-sm text-gray-400">현재 모드</div>
                <div className={`text-lg font-bold ${
                  systemStatus?.current_mode === 'REAL' ? 'text-red-400' : 'text-blue-400'
                }`}>
                  {systemStatus?.current_mode === 'REAL' ? '실거래' : '모의투자'}
                </div>
              </div>
              
              <div className="bg-gray-700 p-4 rounded">
                <div className="text-sm text-gray-400">운영체제</div>
                <div className={`text-lg font-bold ${
                  systemStatus?.is_windows ? 'text-green-400' : 'text-yellow-400'
                }`}>
                  {systemStatus?.is_windows ? 'Windows' : 'Other'}
                </div>
              </div>
              
              <div className="bg-gray-700 p-4 rounded">
                <div className="text-sm text-gray-400">키움 API</div>
                <div className={`text-lg font-bold ${
                  systemStatus?.kiwoom_api_available ? 'text-green-400' : 'text-red-400'
                }`}>
                  {systemStatus?.kiwoom_api_available ? '사용 가능' : '불가능'}
                </div>
              </div>
              
              <div className="bg-gray-700 p-4 rounded">
                <div className="text-sm text-gray-400">계좌 연결</div>
                <div className={`text-lg font-bold ${
                  systemStatus?.account_connected ? 'text-green-400' : 'text-gray-400'
                }`}>
                  {systemStatus?.account_connected ? '연결됨' : '미연결'}
                </div>
              </div>
            </div>

            {/* 계좌 정보 */}
            {systemStatus?.account_info && (
              <div className="mt-4 p-4 bg-gray-700 rounded">
                <div className="text-sm text-gray-400 mb-2">계좌 정보</div>
                <div className="flex justify-between items-center">
                  <span>계좌번호: {systemStatus.account_info.account_number}</span>
                  <span>서버: {systemStatus.account_info.server_type}</span>
                  <span>가용자금: ₩{systemStatus.account_info.available_cash.toLocaleString()}</span>
                </div>
              </div>
            )}
          </div>

          {/* 거래 모드 선택 */}
          <div className="grid md:grid-cols-2 gap-8 mb-8">
            
            {/* 모의투자 모드 */}
            <div className={`bg-gray-800 rounded-lg p-6 border-2 transition-all cursor-pointer ${
              selectedMode === 'DEMO' ? 'border-blue-500 bg-blue-900/20' : 'border-gray-600 hover:border-blue-400'
            }`} onClick={() => setSelectedMode('DEMO')}>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-blue-400">🎮 모의투자 모드</h3>
                <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${
                  selectedMode === 'DEMO' ? 'border-blue-500 bg-blue-500' : 'border-gray-400'
                }`}>
                  {selectedMode === 'DEMO' && <div className="w-3 h-3 bg-white rounded-full"></div>}
                </div>
              </div>
              
              <div className="space-y-3 text-sm">
                <div className="flex items-center space-x-2">
                  <span className="text-green-400">✅</span>
                  <span>실제 돈을 사용하지 않음</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-green-400">✅</span>
                  <span>모든 플랫폼에서 실행 가능</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-green-400">✅</span>
                  <span>전략 테스트 및 학습에 최적</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-green-400">✅</span>
                  <span>위험 없이 시스템 동작 확인</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-blue-400">💡</span>
                  <span>실시간 시세 시뮬레이션</span>
                </div>
              </div>

              <div className="mt-4 p-3 bg-blue-900/30 rounded text-xs">
                <strong>추천 대상:</strong> 초보자, 전략 개발자, 시스템 테스트
              </div>
            </div>

            {/* 실거래 모드 */}
            <div className={`bg-gray-800 rounded-lg p-6 border-2 transition-all cursor-pointer ${
              selectedMode === 'REAL' ? 'border-red-500 bg-red-900/20' : 'border-gray-600 hover:border-red-400'
            } ${!systemStatus?.is_windows || !systemStatus?.kiwoom_api_available ? 'opacity-50 cursor-not-allowed' : ''}`} 
            onClick={() => systemStatus?.is_windows && systemStatus?.kiwoom_api_available && setSelectedMode('REAL')}>
              
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-red-400">🔥 실거래 모드</h3>
                <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${
                  selectedMode === 'REAL' ? 'border-red-500 bg-red-500' : 'border-gray-400'
                }`}>
                  {selectedMode === 'REAL' && <div className="w-3 h-3 bg-white rounded-full"></div>}
                </div>
              </div>
              
              <div className="space-y-3 text-sm">
                <div className="flex items-center space-x-2">
                  <span className="text-red-400">⚠️</span>
                  <span>실제 돈으로 거래</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-yellow-400">🖥️</span>
                  <span>Windows 환경 필수</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-yellow-400">🔑</span>
                  <span>키움증권 계좌 필요</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-red-400">💰</span>
                  <span>투자 손실 위험</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-green-400">📈</span>
                  <span>실제 수익 가능</span>
                </div>
              </div>

              <div className="mt-4 p-3 bg-red-900/30 rounded text-xs">
                <strong>추천 대상:</strong> 경험자, 충분한 테스트 완료, 소액 투자 가능자
              </div>

              {/* 실거래 불가능한 경우 안내 */}
              {(!systemStatus?.is_windows || !systemStatus?.kiwoom_api_available) && (
                <div className="mt-4 p-3 bg-gray-700 rounded text-xs text-yellow-400">
                  <strong>실거래 불가능:</strong> 
                  {!systemStatus?.is_windows && " Windows 환경 필요"}
                  {!systemStatus?.kiwoom_api_available && " 키움 API 설치 필요"}
                </div>
              )}
            </div>
          </div>

          {/* 모드 변경 버튼 */}
          <div className="flex justify-center space-x-4 mb-8">
            {selectedMode !== systemStatus?.current_mode && (
              <button
                onClick={() => handleModeChange(selectedMode)}
                disabled={isChanging || (!systemStatus?.is_windows && selectedMode === 'REAL')}
                className={`px-8 py-3 rounded-lg font-semibold transition-all ${
                  selectedMode === 'REAL'
                    ? 'bg-red-600 hover:bg-red-700 text-white'
                    : 'bg-blue-600 hover:bg-blue-700 text-white'
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {isChanging ? '변경 중...' : `${selectedMode === 'REAL' ? '실거래' : '모의투자'} 모드로 변경`}
              </button>
            )}