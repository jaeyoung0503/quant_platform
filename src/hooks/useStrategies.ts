// ===== 4. 전략 Hook (hooks/useStrategies.ts) =====
import { useState, useEffect, useCallback } from 'react';
import { backtestAPI } from '../services/api'; // 이 줄 추가
import type { Strategy } from '../types/api';

export function useStrategies() {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadStrategies = async () => {
      try {
        setIsLoading(true);
        const response = await backtestAPI.getStrategies();
        
        if (response.success && response.strategies) {
          const mappedStrategies = response.strategies.map(s => ({
            id: s.id,
            name: s.name,
            description: s.description,
            selected: false,
            weight: 0,
            params: { ...s.defaultParams },
            defaultParams: { ...s.defaultParams },
            paramSchema: s.paramSchema,
          }));
          setStrategies(mappedStrategies);
        } else {
          setError(response.error || '전략 로딩 실패');
        }
      } catch (err) {
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

  console.log('전략 개수:', strategies.length);
  console.log('전략 데이터:', strategies);

  return { 
    strategies, 
    setStrategies, 
    updateStrategy,
    normalizeWeights,
    isLoading, 
    error 
  };
  
}

