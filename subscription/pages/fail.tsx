 // pages/fail.tsx - 결제 실패 페이지
import React from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';

const PaymentFailPage: React.FC = () => {
  const router = useRouter();
  const { code, message, orderId } = router.query;

  const getFailureMessage = (errorCode: string): string => {
    const messages: Record<string, string> = {
      'PAY_PROCESS_CANCELED': '고객님이 결제를 취소하셨습니다.',
      'PAY_PROCESS_ABORTED': '결제 진행 중 오류가 발생했습니다.',
      'REJECT_CARD_COMPANY': '카드사에서 결제를 거절했습니다.',
      'INSUFFICIENT_BALANCE': '잔액이 부족합니다.',
      'INVALID_CARD_EXPIRATION': '카드 유효기간이 만료되었습니다.',
      'INVALID_STOPPED_CARD': '정지된 카드입니다.',
      'EXCEED_MAX_DAILY_PAYMENT_COUNT': '일일 결제 한도를 초과했습니다.',
      'NOT_SUPPORTED_INSTALLMENT_PLAN_CARD_OR_MERCHANT': '할부가 지원되지 않는 카드입니다.',
      'INVALID_CARD_INSTALLMENT_PLAN': '잘못된 할부 개월수입니다.',
      'NOT_SUPPORTED_MONTHLY_INSTALLMENT_PLAN': '할부가 지원되지 않습니다.',
      'EXCEED_MAX_PAYMENT_MONEY': '결제 가능 금액을 초과했습니다.',
      'NOT_FOUND_TERMINAL_ID': '단말기 정보를 찾을 수 없습니다.',
      'INVALID_AUTHORIZE_AUTH': '유효하지 않은 인증입니다.',
      'INVALID_CARD_LOST_OR_STOLEN': '분실 또는 도난 카드입니다.',
      'INVALID_CARD_NUMBER': '잘못된 카드번호입니다.',
      'INVALID_UNREGISTERED_SUBMALL': '등록되지 않은 서브몰입니다.',
      'NOT_REGISTERED_BUSINESS': '등록되지 않은 사업자입니다.',
      'EXCEED_MAX_ONE_DAY_PAYMENT_MONEY': '일일 결제 한도를 초과했습니다.',
      'NOT_SUPPORTED_BANK': '지원하지 않는 은행입니다.',
      'INVALID_PASSWORD': '잘못된 비밀번호입니다.',
      'INCORRECT_BASIC_AUTH': '잘못된 인증 정보입니다.',
      'FDS_ERROR': '위험 거래로 분류되어 결제가 거절되었습니다.',
      'USER_CANCEL': '고객님이 결제를 취소하셨습니다.',
      'TIMEOUT': '결제 시간이 초과되었습니다.',
    };

    return messages[errorCode] || '알 수 없는 오류가 발생했습니다.';
  };

  const getFailureIcon = (errorCode: string): string => {
    if (errorCode === 'PAY_PROCESS_CANCELED' || errorCode === 'USER_CANCEL') {
      return '🚫';
    }
    if (errorCode === 'TIMEOUT') {
      return '⏰';
    }
    if (errorCode?.includes('CARD')) {
      return '💳';
    }
    return '❌';
  };

  const getSuggestedActions = (errorCode: string): string[] => {
    const suggestions: Record<string, string[]> = {
      'PAY_PROCESS_CANCELED': [
        '결제를 다시 시도해보세요',
        '다른 결제 수단을 이용해보세요'
      ],
      'INSUFFICIENT_BALANCE': [
        '계좌 잔액을 확인하고 충전해주세요',
        '다른 카드나 계좌를 이용해보세요'
      ],
      'INVALID_CARD_EXPIRATION': [
        '카드 유효기간을 확인해주세요',
        '새로운 카드를 등록해보세요'
      ],
      'EXCEED_MAX_DAILY_PAYMENT_COUNT': [
        '내일 다시 시도해보세요',
        '카드사에 문의하여 한도를 확인해보세요'
      ],
      'TIMEOUT': [
        '안정적인 인터넷 환경에서 다시 시도해보세요',
        '페이지를 새로고침하고 다시 결제해보세요'
      ]
    };

    return suggestions[errorCode] || [
      '카드 정보를 다시 확인해주세요',
      '다른 결제 수단을 이용해보세요',
      '문제가 지속되면 고객지원에 문의해주세요'
    ];
  };

  const handleRetry = () => {
    router.push('/pricing');
  };

  const handleGoHome = () => {
    router.push('/');
  };

  const handleContactSupport = () => {
    const subject = encodeURIComponent('결제 문의');
    const body = encodeURIComponent(`
주문번호: ${orderId || 'N/A'}
오류코드: ${code || 'N/A'}
오류메시지: ${message || 'N/A'}
발생시각: ${new Date().toLocaleString('ko-KR')}

문의내용:
`);
    
    // 실제 서비스에서는 고객지원 이메일 주소 사용
    window.location.href = `mailto:support@yourcompany.com?subject=${subject}&body=${body}`;
  };

  const displayMessage = code ? getFailureMessage(code as string) : (message || '결제 처리 중 오류가 발생했습니다.');
  const failureIcon = code ? getFailureIcon(code as string) : '❌';
  const suggestions = code ? getSuggestedActions(code as string) : [
    '카드 정보를 다시 확인해주세요',
    '다른 결제 수단을 이용해보세요',
    '문제가 지속되면 고객지원에 문의해주세요'
  ];

  return (
    <>
      <Head>
        <title>결제 실패 - 구독 서비스</title>
        <meta name="description" content="결제가 실패했습니다" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="robots" content="noindex, nofollow" />
      </Head>

      <div className="min-h-screen bg-gray-50 py-12">
        <div className="max-w-md mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white shadow-lg rounded-lg p-8 text-center">
            
            {/* 실패 아이콘 */}
            <div className="text-6xl mb-6">
              {failureIcon}
            </div>
            
            {/* 실패 메시지 */}
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              결제에 실패했습니다
            </h2>
            
            <p className="text-gray-600 mb-8 leading-relaxed">
              {displayMessage}
            </p>
            
            {/* 주문 정보 */}
            {orderId && (
              <div className="bg-gray-50 rounded-lg p-4 mb-8">
                <div className="text-sm space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">주문번호:</span>
                    <span className="font-mono text-xs text-gray-800 break-all">
                      {orderId}
                    </span>
                  </div>
                  {code && (
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">오류 코드:</span>
                      <span className="font-mono text-xs text-red-600">
                        {code}
                      </span>
                    </div>
                  )}
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">발생 시각:</span>
                    <span className="text-xs text-gray-700">
                      {new Date().toLocaleString('ko-KR')}
                    </span>
                  </div>
                </div>
              </div>
            )}
            
            {/* 해결 방법 제안 */}
            <div className="bg-blue-50 rounded-lg p-6 mb-8 text-left">
              <h3 className="font-semibold text-blue-900 mb-3 text-center">
                💡 해결 방법
              </h3>
              <ul className="space-y-2">
                {suggestions.map((suggestion, index) => (
                  <li key={index} className="text-sm text-blue-800 flex items-start">
                    <span className="text-blue-500 mr-2 mt-0.5">•</span>
                    {suggestion}
                  </li>
                ))}
              </ul>
            </div>
            
            {/* 액션 버튼들 */}
            <div className="space-y-3">
              <button
                onClick={handleRetry}
                className="w-full py-3 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-semibold"
              >
                🔄 다시 시도하기
              </button>
              
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={handleContactSupport}
                  className="py-3 px-4 bg-orange-100 text-orange-700 rounded-lg hover:bg-orange-200 transition-colors font-medium"
                >
                  📞 문의하기
                </button>
                
                <button
                  onClick={handleGoHome}
                  className="py-3 px-4 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors font-medium"
                >
                  🏠 홈으로
                </button>
              </div>
            </div>

            {/* 추가 도움말 */}
            <div className="mt-8 p-4 bg-yellow-50 rounded-lg">
              <p className="text-sm text-yellow-800">
                <strong>🔒 안전 보장</strong><br />
                결제가 실패하더라도 카드에서 결제되지 않습니다.<br />
                혹시 결제가 진행되었다면 1-2일 내 자동 취소됩니다.
              </p>
            </div>

            {/* 결제 방법 안내 */}
            <div className="mt-6 text-xs text-gray-500">
              <p>
                <strong>지원하는 결제 방법:</strong><br />
                💳 모든 국내 신용/체크카드 • 🏦 실시간 계좌이체 • 📱 간편결제
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default PaymentFailPage;
