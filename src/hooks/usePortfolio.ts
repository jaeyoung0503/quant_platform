// ===== 5. 포트폴리오 Hook (hooks/usePortfolio.ts) =====
import { useState, useEffect, useCallback } from 'react';
import { backtestAPI } from '../services/api'; // 이 줄 추가
import type { BacktestResult, PortfolioStock, Strategy } from '../types/api';

export function usePortfolio() {
  const [portfolioStocks, setPortfolioStocks] = useState<PortfolioStock[]>([]);
  const [portfolioName, setPortfolioName] = useState('퀀트포트폴리오2024');
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const addStock = useCallback((stock: BacktestResult) => {
    setPortfolioStocks(prev => {
      if (prev.find(p => p.stockCode === stock.stockCode)) {
        return prev;
      }
      
      const newStock: PortfolioStock = {
        stockCode: stock.stockCode,
        stockName: stock.stockName,
        score: stock.compositeScore,
        grade: stock.grade,
        weight: 0,
      };
      
      const newPortfolio = [...prev, newStock];
      const equalWeight = 100 / newPortfolio.length;
      
      return newPortfolio.map(s => ({ ...s, weight: equalWeight }));
    });
  }, []);

  const removeStock = useCallback((stockCode: string) => {
    setPortfolioStocks(prev => {
      const filtered = prev.filter(p => p.stockCode !== stockCode);
      if (filtered.length === 0) return [];
      
      const equalWeight = 100 / filtered.length;
      return filtered.map(s => ({ ...s, weight: equalWeight }));
    });
  }, []);

  const savePortfolio = useCallback(async (strategies: Strategy[]) => {
    if (portfolioStocks.length === 0) {
      setSaveError('포트폴리오에 종목을 추가해주세요.');
      return false;
    }

    setIsSaving(true);
    setSaveError(null);
    
    try {
      const portfolioData = {
        name: portfolioName,
        stocks: portfolioStocks.map(s => s.stockCode),
        strategies: strategies.filter(s => s.selected),
        createdAt: new Date().toISOString(),
      };

      const response = await backtestAPI.savePortfolio(portfolioData);
      
      if (response.success) {
        return true;
      } else {
        setSaveError('포트폴리오 저장에 실패했습니다.');
        return false;
      }
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : '포트폴리오 저장 중 오류가 발생했습니다.');
      return false;
    } finally {
      setIsSaving(false);
    }
  }, [portfolioStocks, portfolioName]);

  const portfolioStats = {
    avgScore: portfolioStocks.length > 0 
      ? portfolioStocks.reduce((sum, s) => sum + s.score, 0) / portfolioStocks.length 
      : 0,
    totalStocks: portfolioStocks.length,
    gradeDistribution: portfolioStocks.reduce((acc, s) => {
      acc[s.grade] = (acc[s.grade] || 0) + 1;
      return acc;
    }, {} as Record<string, number>),
  };

  return {
    portfolioStocks,
    portfolioName,
    setPortfolioName,
    addStock,
    removeStock,
    savePortfolio,
    isSaving,
    saveError,
    portfolioStats,
    clearSaveError: () => setSaveError(null),
  };
}
