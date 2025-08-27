'use client'

import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { XCircle, ArrowLeft, RefreshCw, HelpCircle } from 'lucide-react'

export default function PaymentFailPage() {
  const searchParams = useSearchParams()
  const errorMessage = searchParams.get('message') || searchParams.get('error') || '결제 처리 중 오류가 발생했습니다'
  const errorCode = searchParams.get('code')

  const getErrorDescription = (message: string, code: string | null) => {
    const errorMap = {
      'CARD_COMPANY_NOT_AVAILABLE': '카드사 서비스가 일시적으로 중단되었습니다',
      'EXCEED_MAX_CARD_INSTALLMENT_PLAN': '설정 가능한 할부 개월 수를 초과했습니다',
      'INVALID_CARD_EXPIRATION': '카드 유효기간이 잘못되었습니다',
      'INVALID_STOPPED_CARD': '정지된 카드입니다',
      'LIMIT_EXCEEDED': '한도를 초과했습니다',
      'CARD_NOT_SUPPORTED': '지원하지 않는 카드입니다',
      'INVALID_CARD_NUMBER': '카드번호가 잘못되었습니다'
    }

    if (code && errorMap[code as keyof typeof errorMap]) {
      return errorMap[code as keyof typeof errorMap]
    }

    if (message.includes('한도')) return '카드 한도를 확인해 주세요'
    if (message.includes('승인')) return '카드 승인이 거절되었습니다'
    if (message.includes('취소')) return '사용자가 결제를 취소했습니다'
    
    return message
  }

  const getSolution = (message: string, code: string | null) => {
    if (code === 'CARD_COMPANY_NOT_AVAILABLE') {
      return '잠시 후 다시 시도하거나 다른 카드를 이용해 주세요'
    }
    if (code === 'LIMIT_EXCEEDED') {
      return '카드 한도를 확인하시거나 다른 결제수단을 이용해 주세요'
    }
    if (code?.includes('CARD')) {
      return '카드 정보를 다시 확인하시거나 다른 카드로 시도해 주세요'
    }
    if (message.includes('취소')) {
      return '결제를 계속 진행하시려면 다시 시도해 주세요'
    }
    
    return '잠시 후 다시 시도하시거나 고객지원팀에 문의해 주세요'
  }

  return (
    <div className="min-h-screen bg-gray-900 py-12">
      <div className="max-w-2xl mx-auto px-6">
        <div className="bg-gray-800 rounded-xl p-8 text-center">
          {/* Error Icon */}
          <div className="mb-6">
            <XCircle className="w-20 h-20 text-red-500 mx-auto mb-4" />
            <h1 className="text-3xl font-bold text-white mb-2">결제에 실패했습니다</h1>
            <p className="text-gray-300">
              결제 처리 중 문제가 발생했습니다
            </p>
          </div>

          {/* Error Details */}
          <div className="bg-red-600/10 border border-red-600/20 rounded-lg p-6 mb-8">
            <div className="text-left space-y-4">
              <div>
                <h3 className="text-red-400 font-semibold mb-2">오류 내용</h3>
                <p className="text-gray-300">{getErrorDescription(errorMessage, errorCode)}</p>
                {errorCode && (
                  <p className="text-gray-500 text-sm mt-1">오류 코드: {errorCode}</p>
                )}
              </div>
              
              <div>
                <h3 className="text-red-400 font-semibold mb-2">해결 방법</h3>
                <p className="text-gray-300">{getSolution(errorMessage, errorCode)}</p>
              </div>
            </div>
          </div>

          {/* Common Solutions */}
          <div className="bg-gray-700 rounded-lg p-6 mb-8 text-left">
            <h3 className="text-white font-semibold mb-4 flex items-center">
              <HelpCircle className="w-5 h-5 mr-2" />
              자주 발생하는 문제 해결방법
            </h3>
            
            <ul className="text-gray-300 space-y-2 text-sm">
              <li>• <strong>카드 한도 부족:</strong> 카드사에 문의하여 한도를 확인해 주세요</li>
              <li>• <strong>해외결제 차단:</strong> 카드사에 해외결제 허용을 요청해 주세요</li>
              <li>• <strong>카드 정보 오류:</strong> 카드번호, 유효기간, CVC를 다시 확인해 주세요</li>
              <li>• <strong>일시적 오류:</strong> 5-10분 후 다시 시도해 주세요</li>
              <li>• <strong>브라우저 문제:</strong> 캐시를 삭제하거나 다른 브라우저를 이용해 보세요</li>
            </ul>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 mb-8">
            <Link href="/payment" className="flex-1">
              <button className="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold py-3 px-6 rounded-lg transition-colors flex items-center justify-center">
                <RefreshCw className="w-4 h-4 mr-2" />
                다시 결제하기
              </button>
            </Link>
            
            <Link href="/membership" className="flex-1">
              <button className="w-full bg-gray-600 hover:bg-gray-500 text-white font-semibold py-3 px-6 rounded-lg transition-colors flex items-center justify-center">
                <ArrowLeft className="w-4 h-4 mr-2" />
                멤버십으로 돌아가기
              </button>
            </Link>
          </div>

          {/* Support Information */}
          <div className="pt-6 border-t border-gray-600 text-center">
            <p className="text-gray-400 text-sm mb-4">
              문제가 계속 발생하면 고객지원팀으로 연락해 주세요
            </p>
            
            <div className="bg-gray-700 rounded-lg p-4">
              <h4 className="text-white font-medium mb-3">고객지원</h4>
              <div className="flex flex-col sm:flex-row justify-center items-center space-y-2 sm:space-y-0 sm:space-x-6 text-sm">
                <a 
                  href="mailto:support@intelliquant.ai" 
                  className="text-blue-400 hover:text-blue-300 flex items-center"
                >
                  📧 support@intelliquant.ai
                </a>
                <a 
                  href="tel:02-1234-5678" 
                  className="text-blue-400 hover:text-blue-300 flex items-center"
                >
                  📞 02-1234-5678
                </a>
              </div>
              <p className="text-gray-400 text-xs mt-2">
                평일 09:00 - 18:00 (주말 및 공휴일 제외)
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}