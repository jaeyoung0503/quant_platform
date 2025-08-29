// hooks/useStrategies.ts
import { useState, useEffect, useCallback } from 'react';
import { backtestAPI } from '../services/api';
import type { Strategy } from '../types/api';

export function useStrategies() {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadStrategies = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        console.log('전략 로딩 시작');
        
        // 직접 fetch 사용하여 우회
        const response = await fetch('/api/strategies');
        const data = await response.json();
        
        console.log('API 응답:', data);
        console.log('전략 데이터:', data.strategies);
        console.log('전략 개수:', data.strategies?.length);
        
        if (data.success && Array.isArray(data.strategies) && data.strategies.length > 0) {
          const mappedStrategies: Strategy[] = data.strategies.map((s: any) => ({
            id: s.id,
            name: s.name,
            description: s.description,
            selected: false,
            weight: 0,
            params: { ...s.defaultParams },
            defaultParams: { ...s.defaultParams },
            paramSchema: s.paramSchema || {},
          }));
          
          console.log('매핑된 전략:', mappedStrategies);
          
          // React 상태 업데이트
          setStrategies(mappedStrategies);
          
          // 상태 업데이트 확인
          setTimeout(() => {
            console.log('상태 업데이트 후 확인 - strategies.length:', strategies.length);
          }, 100);
          
        } else {
          const errorMsg = `API 응답 형식 오류: ${JSON.stringify(data)}`;
          console.error(errorMsg);
          setError(errorMsg);
        }
        
      } catch (err) {
        console.error('전략 로딩 에러:', err);
        setError(err instanceof Error ? err.message : '전략 로딩 실패');
      } finally {
        setIsLoading(false);
      }
    };

    loadStrategies();
  }, []);

  const updateStrategy = useCallback((id: string, updates: Partial<Strategy>) => {
    setStrategies(prev => prev.map(strategy => 
      strategy.id === id ? { ...strategy, ...updates } : strategy
    ));
  }, []);

  const normalizeWeights = useCallback(() => {
    setStrategies(prev => {
      const selected = prev.filter(s => s.selected);
      const totalWeight = selected.reduce((sum, s) => sum + s.weight, 0);
      
      if (totalWeight > 0 && Math.abs(totalWeight - 100) > 0.1) {
        return prev.map(strategy => ({
          ...strategy,
          weight: strategy.selected ? (strategy.weight / totalWeight) * 100 : 0
        }));
      }
      
      return prev;
    });
  }, []);

  console.log('현재 상태:', { isLoading, error, strategiesCount: strategies.length });

  return { 
    strategies, 
    setStrategies, 
    updateStrategy,
    normalizeWeights,
    isLoading, 
    error 
  };
}