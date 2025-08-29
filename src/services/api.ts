// services/api.ts
const BASE_URL = '/api'; // localhost:8000 대신 변경

export const backtestAPI = {
  getStrategies: async () => {
    try {
      const response = await fetch(`${BASE_URL}/strategies`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('전략 API 호출 오류:', error);
      throw error;
    }
  },
  
  runBacktest: async (request) => {
    try {
      const response = await fetch(`${BASE_URL}/backtest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request)
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('백테스트 API 호출 오류:', error);
      throw error;
    }
  },
  
  savePortfolio: async (portfolio) => {
    try {
      const response = await fetch(`${BASE_URL}/portfolio`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(portfolio)
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('포트폴리오 저장 API 호출 오류:', error);
      throw error;
    }
  }
};