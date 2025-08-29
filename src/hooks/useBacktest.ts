// ===== 3. 백테스트 Hook (hooks/useBacktest.ts) =====
import { useState, useCallback } from 'react';
import { backtestAPI } from '../services/api'; // 이 줄 추가
import type { BacktestRequest, BacktestResult } from '../types/api';

export function useBacktest() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<BacktestResult[]>([]);
  const [reliability, setReliability] = useState<any>(null);
  const [totalAnalyzed, setTotalAnalyzed] = useState(0);
  const [conditionMet, setConditionMet] = useState(0);

  const runBacktest = useCallback(async (request: BacktestRequest) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await backtestAPI.runBacktest(request);
      
      if (response.success && response.data) {
        setResults(response.data.results.map(r => ({ ...r, selected: false })));
        setReliability(response.data.reliability);
        setTotalAnalyzed(response.data.totalAnalyzed);
        setConditionMet(response.data.conditionMet);
      } else {
        setError(response.error || '백테스트 실행 중 오류가 발생했습니다.');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '네트워크 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const updateResults = useCallback((updatedResults: BacktestResult[]) => {
    setResults(updatedResults);
  }, []);

  return {
    isLoading,
    error,
    results,
    reliability,
    totalAnalyzed,
    conditionMet,
    runBacktest,
    updateResults,
    clearError: () => setError(null),
  };
}
