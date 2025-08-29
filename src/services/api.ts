// services/api.ts
const BASE_URL = '/api';

export const backtestAPI = {
  getStrategies: async () => {
    try {
      console.log('API 호출 시작:', `${BASE_URL}/strategies`);
      const response = await fetch(`${BASE_URL}/strategies`);
      
      console.log('응답 상태:', response.status, response.statusText);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('API 응답 데이터:', data);
      
      // 응답 형식 검증
      if (!data || typeof data !== 'object') {
        throw new Error('API 응답이 올바르지 않습니다');
      }
      
      if (!data.success) {
        throw new Error(data.error || 'API에서 실패 응답을 받았습니다');
      }
      
      if (!Array.isArray(data.strategies)) {
        throw new Error('strategies 배열이 없거나 올바르지 않습니다');
      }
      
      console.log('전략 개수 확인:', data.strategies.length);
      return data;
      
    } catch (error) {
      console.error('전략 API 호출 오류:', error);
      // 에러를 다시 throw하지 말고 실패 응답 반환
      return {
        success: false,
        error: error instanceof Error ? error.message : '알 수 없는 오류',
        strategies: []
      };
    }
  },

  runBacktest: async (request: any) => {
    try {
      console.log('백테스트 요청:', request);
      const response = await fetch(`${BASE_URL}/backtest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('백테스트 응답:', data);
      return data;
      
    } catch (error) {
      console.error('백테스트 API 호출 오류:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '백테스트 실행 실패'
      };
    }
  },

  savePortfolio: async (portfolio: any) => {
    try {
      console.log('포트폴리오 저장 요청:', portfolio);
      const response = await fetch(`${BASE_URL}/portfolio`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(portfolio)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('포트폴리오 저장 응답:', data);
      return data;
      
    } catch (error) {
      console.error('포트폴리오 저장 API 호출 오류:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '포트폴리오 저장 실패'
      };
    }
  }
};