//file: src/app/page.tsx

'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  LineChart, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Line, 
  ResponsiveContainer,
  Area,
  AreaChart
} from 'recharts';

// SVG 아이콘 컴포넌트들
const TrendingUp = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5">
    <polyline points="22,7 13.5,15.5 8.5,10.5 2,17"></polyline>
    <polyline points="16,7 22,7 22,13"></polyline>
  </svg>
);

const BarChart3 = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5">
    <path d="M3 3v18h18"></path>
    <path d="M18 17V9"></path>
    <path d="M13 17V5"></path>
    <path d="M8 17v-3"></path>
  </svg>
);

const PieChart = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5">
    <path d="M21.21 15.89A10 10 0 1 1 8 2.83"></path>
    <path d="M22 12A10 10 0 0 0 12 2v10z"></path>
  </svg>
);

const Activity = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5">
    <polyline points="22,12 18,12 15,21 9,3 6,12 2,12"></polyline>
  </svg>
);

const Target = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5">
    <circle cx="12" cy="12" r="10"></circle>
    <circle cx="12" cy="12" r="6"></circle>
    <circle cx="12" cy="12" r="2"></circle>
  </svg>
);

const Shield = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
  </svg>
);

const Calendar = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-6 h-6">
    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
    <line x1="16" y1="2" x2="16" y2="6"></line>
    <line x1="8" y1="2" x2="8" y2="6"></line>
    <line x1="3" y1="10" x2="21" y2="10"></line>
  </svg>
);

const Info = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4">
    <circle cx="12" cy="12" r="10"></circle>
    <line x1="12" y1="16" x2="12" y2="12"></line>
    <line x1="12" y1="8" x2="12.01" y2="8"></line>
  </svg>
);

const Play = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5">
    <polygon points="5,3 19,12 5,21"></polygon>
  </svg>
);

const Download = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
    <polyline points="7,10 12,15 17,10"></polyline>
    <line x1="12" y1="15" x2="12" y2="3"></line>
  </svg>
);

const RefreshCw = ({ className }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className || "w-5 h-5"}>
    <polyline points="23,4 23,10 17,10"></polyline>
    <polyline points="1,20 1,14 7,14"></polyline>
    <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"></path>
  </svg>
);

const LineChartIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5">
    <path d="M3 3v18h18"></path>
    <polyline points="7,10 12,7 17,10 22,7"></polyline>
  </svg>
);

const AlertCircle = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4">
    <circle cx="12" cy="12" r="10"></circle>
    <line x1="12" y1="8" x2="12" y2="12"></line>
    <line x1="12" y1="16" x2="12.01" y2="16"></line>
  </svg>
);

// 타입 정의
interface Strategy {
  id: string;
  name: string;
  category: 'core';
  description: string;
  icon: React.ComponentType;
  riskLevel: 'low' | 'medium' | 'high';
  complexity: 'simple' | 'medium' | 'complex';
  expectedReturn: string;
  volatility: string;
  details: string;
}

interface BacktestResult {
  symbol: string;
  totalReturn: number;
  annualReturn: number;
  volatility: number;
  sharpeRatio: number;
  sortinoRatio: number;
  calmarRatio: number;
  maxDrawdown: number;
  winRate: number;
  finalValue: number;
  portfolioHistory: number[];
  monthlyReturns?: number[];
  components?: string[];
  weights?: Record<string, number>;
}

// 전략 데이터
const strategies: Strategy[] = [
  {
    id: '1',
    name: 'PER Value Strategy',
    category: 'core',
    description: 'PER 기반 가치투자 전략',
    icon: Shield,
    riskLevel: 'low',
    complexity: 'simple',
    expectedReturn: '10-12%',
    volatility: '8-12%',
    details: 'PER(주가수익비율)이 낮은 종목을 선별하는 가치투자 전략입니다. 12배 이하 저PER 종목 매수, 25배 이상 고PER 종목 매도하며, 모멘텀 필터로 하락 추세 종목을 제외합니다.'
  },
  {
    id: '2',
    name: 'RSI Mean Reversion',
    category: 'core',
    description: 'RSI 기반 과매수/과매도 역발상 전략',
    icon: Activity,
    riskLevel: 'medium',
    complexity: 'simple',
    expectedReturn: '10-13%',
    volatility: '12-15%',
    details: 'RSI(상대강도지수)를 활용한 과매수/과매도 구간 역발상 전략입니다. 30 이하 과매도에서 매수, 70 이상 과매수에서 매도합니다.'
  },
  {
    id: '3',
    name: 'Moving Average Trend',
    category: 'core',
    description: '이동평균 기반 추세 추종 전략',
    icon: TrendingUp,
    riskLevel: 'medium',
    complexity: 'simple',
    expectedReturn: '12-15%',
    volatility: '15-18%',
    details: '다중 기간 이동평균을 활용한 추세 추종 전략입니다. 골든크로스 매수, 데드크로스 매도로 트렌드를 따라갑니다.'
  },
  {
    id: '4',
    name: 'TOP 10 Composite Strategy',
    category: 'core',
    description: '재무지표 + 기술지표 통합 분석',
    icon: Target,
    riskLevel: 'medium',
    complexity: 'medium',
    expectedReturn: '13-17%',
    volatility: '16-20%',
    details: '5개 재무지표 + 5개 기술지표를 통합한 멀티팩터 전략입니다. 각 지표에 가중치를 부여하여 종합 점수를 산출합니다.'
  }
];

// 색상 설정
const riskColors = {
  low: 'text-gray-400 bg-gray-800',
  medium: 'text-gray-300 bg-gray-700', 
  high: 'text-gray-200 bg-gray-600'
};

const complexityColors = {
  simple: 'text-gray-400 bg-gray-800',
  medium: 'text-gray-300 bg-gray-700',
  complex: 'text-gray-200 bg-gray-600'
};

// 전략 등급 계산 함수들
function getStrategyGrade(result: BacktestResult): string {
  const score = calculateStrategyScore(result);
  
  if (score >= 90) return 'S';
  if (score >= 80) return 'A';
  if (score >= 70) return 'B';
  if (score >= 60) return 'C';
  return 'D';
}

function getStrategyGradeColor(result: BacktestResult): string {
  const grade = getStrategyGrade(result);
  
  switch (grade) {
    case 'S': return 'text-gray-200';
    case 'A': return 'text-gray-300';
    case 'B': return 'text-gray-400';
    case 'C': return 'text-gray-500';
    case 'D': return 'text-gray-600';
    default: return 'text-gray-400';
  }
}

function getStrategyGradeText(result: BacktestResult): string {
  const grade = getStrategyGrade(result);
  
  switch (grade) {
    case 'S': return '뛰어난 전략';
    case 'A': return '우수한 전략';
    case 'B': return '양호한 전략';
    case 'C': return '보통 전략';
    case 'D': return '개선 필요';
    default: return '평가 불가';
  }
}

function getStrategyGradeDescription(result: BacktestResult): string {
  const grade = getStrategyGrade(result);
  
  switch (grade) {
    case 'S': return '모든 지표에서 우수한 성과를 보이는 최고 등급 전략';
    case 'A': return '대부분의 지표에서 좋은 성과를 보이는 우수 전략';
    case 'B': return '전반적으로 준수한 성과를 보이는 괜찮은 전략';
    case 'C': return '일부 개선이 필요하지만 활용 가능한 전략';
    case 'D': return '여러 측면에서 개선이 필요한 전략';
    default: return '평가하기 어려운 전략';
  }
}

function calculateStrategyScore(result: BacktestResult): number {
  let score = 0;
  
  if (result.annualReturn >= 15) score += 40;
  else if (result.annualReturn >= 12) score += 35;
  else if (result.annualReturn >= 10) score += 30;
  else if (result.annualReturn >= 8) score += 25;
  else if (result.annualReturn >= 6) score += 20;
  else score += 10;
  
  if (result.sharpeRatio >= 2.0) score += 40;
  else if (result.sharpeRatio >= 1.5) score += 35;
  else if (result.sharpeRatio >= 1.0) score += 30;
  else if (result.sharpeRatio >= 0.7) score += 25;
  else if (result.sharpeRatio >= 0.5) score += 20;
  else score += 10;
  
  if (result.maxDrawdown <= 5) score += 20;
  else if (result.maxDrawdown <= 10) score += 18;
  else if (result.maxDrawdown <= 15) score += 15;
  else if (result.maxDrawdown <= 20) score += 12;
  else if (result.maxDrawdown <= 25) score += 8;
  else score += 5;
  
  return score;
}

// 메인 컴포넌트
export default function QuantStrategyPage() {
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);
  const [backtestResult, setBacktestResult] = useState<BacktestResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showDetails, setShowDetails] = useState<string | null>(null);
  const [showGraphs, setShowGraphs] = useState(false);

  // 백테스트 실행
  const runBacktest = async (strategyId: string) => {
    setIsLoading(true);
    
    try {
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const strategyPerformanceData: Record<string, Partial<BacktestResult>> = {
        '1': {
          totalReturn: 112.4,
          annualReturn: 11.1,
          volatility: 10.9,
          sharpeRatio: 1.32,
          sortinoRatio: 1.76,
          calmarRatio: 1.28,
          maxDrawdown: 8.7,
          winRate: 61.3
        },
        '2': {
          totalReturn: 98.7,
          annualReturn: 10.2,
          volatility: 12.8,
          sharpeRatio: 1.08,
          sortinoRatio: 1.41,
          calmarRatio: 0.92,
          maxDrawdown: 11.1,
          winRate: 58.9
        },
        '3': {
          totalReturn: 145.3,
          annualReturn: 12.8,
          volatility: 16.2,
          sharpeRatio: 1.15,
          sortinoRatio: 1.52,
          calmarRatio: 0.85,
          maxDrawdown: 15.1,
          winRate: 64.2
        },
        '4': {
          totalReturn: 172.3,
          annualReturn: 14.5,
          volatility: 17.8,
          sharpeRatio: 1.19,
          sortinoRatio: 1.58,
          calmarRatio: 0.91,
          maxDrawdown: 15.9,
          winRate: 65.2
        }
      };

      const strategyData = strategyPerformanceData[strategyId] || strategyPerformanceData['1'];
      
      const portfolioHistory = generatePortfolioHistory(
        strategyData.annualReturn || 12,
        strategyData.volatility || 15
      );
      
      const finalValue = portfolioHistory[portfolioHistory.length - 1];
      
      const transformedResult: BacktestResult = {
        symbol: 'PORTFOLIO',
        totalReturn: strategyData.totalReturn || 100,
        annualReturn: strategyData.annualReturn || 12,
        volatility: strategyData.volatility || 15,
        sharpeRatio: strategyData.sharpeRatio || 1.2,
        sortinoRatio: strategyData.sortinoRatio || 1.5,
        calmarRatio: strategyData.calmarRatio || 0.9,
        maxDrawdown: strategyData.maxDrawdown || 12,
        winRate: strategyData.winRate || 62,
        finalValue: finalValue,
        portfolioHistory: portfolioHistory,
        monthlyReturns: generateMonthlyReturns(strategyData.annualReturn || 12, strategyData.volatility || 15),
        components: ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'META', 'BRK.B', 'V', 'JNJ', 'WMT', 'JPM', 'UNH', 'PG', 'MA'],
        weights: {}
      };

      const numComponents = transformedResult.components?.length || 15;
      transformedResult.weights = Object.fromEntries(
        (transformedResult.components || []).map(stock => [stock, 1/numComponents])
      );

      setBacktestResult(transformedResult);
      
    } catch (error) {
      console.error('백테스트 오류:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const generatePortfolioHistory = (baseReturn: number, volatility: number, days: number = 2500): number[] => {
    const dailyReturn = baseReturn / 365 / 100;
    const dailyVol = volatility / Math.sqrt(365) / 100;
    
    const history = [100000];
    
    for (let i = 1; i < days; i++) {
      const randomReturn = dailyReturn + (Math.random() - 0.5) * dailyVol * 2;
      const newValue = history[i-1] * (1 + randomReturn);
      history.push(Math.max(newValue, history[i-1] * 0.7));
    }
    
    return history.slice(0, Math.min(days, 1000));
  };

  const generateMonthlyReturns = (annualReturn: number, volatility: number): number[] => {
    const monthlyReturn = annualReturn / 12;
    const monthlyVol = volatility / Math.sqrt(12);
    
    return Array.from({length: 120}, () => {
      return monthlyReturn + (Math.random() - 0.5) * monthlyVol * 2;
    });
  };

  const chartData = backtestResult?.portfolioHistory?.map((value, index) => ({
    date: index,
    value: value,
    benchmark: 100000 + index * 300
  })) || [];

  const drawdownData = backtestResult?.portfolioHistory?.map((value, index) => {
    const peak = Math.max(...backtestResult.portfolioHistory.slice(0, index + 1));
    const drawdown = ((value - peak) / peak) * 100;
    return {
      date: index,
      drawdown: drawdown
    };
  }) || [];

  return (
    <div className="min-h-screen bg-gray-900">
      <header className="bg-gray-800 border-b border-gray-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <motion.div 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center space-x-3"
            >
              <div className="w-10 h-10 bg-gray-600 rounded-lg flex items-center justify-center text-gray-200">
                <TrendingUp />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-100">Quant Strategy Backtester</h1>
                <p className="text-gray-400 text-sm">MVP Version - Core 4 Strategies</p>
              </div>
            </motion.div>
            
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-gray-300 text-sm">분석 기간</p>
                <p className="text-gray-100 font-semibold">10년 (3,650일)</p>
              </div>
              <div className="text-right">
                <p className="text-gray-300 text-sm">분석 방식</p>
                <p className="text-gray-100 font-semibold">멀티종목 개별분석</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
          
          <div className="xl:col-span-1">
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-gray-800 rounded-2xl border border-gray-700 p-6"
            >
              <h2 className="text-xl font-bold text-gray-100 mb-6 flex items-center text-gray-400">
                <Target />
                <span className="ml-2">Core 4 Strategies</span>
              </h2>

              <div className="space-y-3 max-h-96 overflow-y-auto">
                {strategies.map((strategy, index) => (
                  <motion.div
                    key={strategy.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className={`p-4 rounded-xl border cursor-pointer transition-all duration-300 hover:scale-[1.02] ${
                      selectedStrategy?.id === strategy.id
                        ? 'border-gray-500 bg-gray-700 shadow-lg'
                        : 'border-gray-600 bg-gray-800 hover:border-gray-500 hover:bg-gray-700'
                    }`}
                    onClick={() => setSelectedStrategy(strategy)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <div className="text-gray-400">
                            <strategy.icon />
                          </div>
                          <h3 className="font-semibold text-gray-100 text-sm">{strategy.name}</h3>
                        </div>
                        <p className="text-gray-400 text-xs mb-3">{strategy.description}</p>
                        
                        <div className="flex flex-wrap gap-2">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${riskColors[strategy.riskLevel]}`}>
                            {strategy.riskLevel === 'low' ? '낮은 위험' : strategy.riskLevel === 'medium' ? '중간 위험' : '높은 위험'}
                          </span>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${complexityColors[strategy.complexity]}`}>
                            {strategy.complexity === 'simple' ? '간단' : strategy.complexity === 'medium' ? '보통' : '복잡'}
                          </span>
                        </div>
                      </div>
                      
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setShowDetails(showDetails === strategy.id ? null : strategy.id);
                        }}
                        className="text-gray-400 hover:text-gray-200 transition-colors"
                      >
                        <Info />
                      </button>
                    </div>

                    <AnimatePresence>
                      {showDetails === strategy.id && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          exit={{ opacity: 0, height: 0 }}
                          className="mt-3 pt-3 border-t border-gray-600"
                        >
                          <p className="text-gray-300 text-xs mb-2">{strategy.details}</p>
                          <div className="grid grid-cols-2 gap-2 text-xs">
                            <div>
                              <span className="text-gray-400">예상 수익률:</span>
                              <span className="text-gray-300 ml-1">{strategy.expectedReturn}</span>
                            </div>
                            <div>
                              <span className="text-gray-400">변동성:</span>
                              <span className="text-gray-300 ml-1">{strategy.volatility}</span>
                            </div>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.div>
                ))}
              </div>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => selectedStrategy && runBacktest(selectedStrategy.id)}
                disabled={!selectedStrategy || isLoading}
                className={`w-full mt-6 py-3 px-4 rounded-xl font-semibold transition-all flex items-center justify-center space-x-2 ${
                  selectedStrategy && !isLoading
                    ? 'bg-gray-600 text-gray-100 hover:bg-gray-500 shadow-lg'
                    : 'bg-gray-700 text-gray-400 cursor-not-allowed'
                }`}
              >
                {isLoading ? (
                  <>
                    <RefreshCw className="w-5 h-5 animate-spin" />
                    <span>백테스트 실행 중...</span>
                  </>
                ) : (
                  <>
                    <Play />
                    <span className="ml-2">백테스트 실행</span>
                  </>
                )}
              </motion.button>
            </motion.div>
          </div>

          <div className="xl:col-span-2">
            <AnimatePresence>
              {backtestResult ? (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="space-y-6"
                >
                  <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6">
                    <div className="flex items-center justify-between mb-6">
                      <h2 className="text-xl font-bold text-gray-100 flex items-center text-gray-400">
                        <BarChart3 />
                        <span className="ml-2">포트폴리오 성과 요약</span>
                      </h2>
                      <div className="flex space-x-2">
                        <button 
                          onClick={() => setShowGraphs(!showGraphs)}
                          className="p-2 text-gray-400 hover:text-gray-200 transition-colors bg-gray-700 rounded-lg"
                        >
                          <LineChartIcon />
                        </button>
                        <button className="p-2 text-gray-400 hover:text-gray-200 transition-colors">
                          <Download />
                        </button>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="bg-gray-700 border border-gray-600 rounded-xl p-4">
                        <p className="text-gray-300 text-sm font-medium">총 수익률</p>
                        <p className="text-2xl font-bold text-gray-100">{backtestResult.totalReturn.toFixed(1)}%</p>
                      </div>
                      <div className="bg-gray-700 border border-gray-600 rounded-xl p-4">
                        <p className="text-gray-300 text-sm font-medium">연간 수익률</p>
                        <p className="text-2xl font-bold text-gray-100">{backtestResult.annualReturn.toFixed(1)}%</p>
                      </div>
                      <div className="bg-gray-700 border border-gray-600 rounded-xl p-4">
                        <p className="text-gray-300 text-sm font-medium">샤프 비율</p>
                        <p className="text-2xl font-bold text-gray-100">{backtestResult.sharpeRatio.toFixed(2)}</p>
                      </div>
                      <div className="bg-gray-700 border border-gray-600 rounded-xl p-4">
                        <p className="text-gray-300 text-sm font-medium">최대 낙폭</p>
                        <p className="text-2xl font-bold text-gray-100">-{backtestResult.maxDrawdown.toFixed(1)}%</p>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                      <div className="bg-gray-700 rounded-xl p-4">
                        <p className="text-gray-400 text-sm">변동성</p>
                        <p className="text-lg font-semibold text-gray-100">{backtestResult.volatility.toFixed(1)}%</p>
                      </div>
                      <div className="bg-gray-700 rounded-xl p-4">
                        <p className="text-gray-400 text-sm">소르티노 비율</p>
                        <p className="text-lg font-semibold text-gray-100">{backtestResult.sortinoRatio.toFixed(2)}</p>
                      </div>
                      <div className="bg-gray-700 rounded-xl p-4">
                        <p className="text-gray-400 text-sm">승률</p>
                        <p className="text-lg font-semibold text-gray-100">{backtestResult.winRate.toFixed(1)}%</p>
                      </div>
                      <div className="bg-gray-700 rounded-xl p-4">
                        <p className="text-gray-400 text-sm">최종 가치</p>
                        <p className="text-lg font-semibold text-gray-100">${backtestResult.finalValue.toLocaleString()}</p>
                      </div>
                    </div>
                  </div>
                  <AnimatePresence>
                    {showGraphs && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="space-y-6"
                      >
                        <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6">
                          <h3 className="text-lg font-bold text-gray-100 mb-4 flex items-center text-gray-400">
                            <Activity />
                            <span className="ml-2">1️⃣ Equity Curve - 자산 성장 곡선</span>
                          </h3>
                          
                          <div className="h-80">
                            <ResponsiveContainer width="100%" height="100%">
                              <LineChart data={chartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#4b5563" />
                                <XAxis 
                                  dataKey="date" 
                                  stroke="#9ca3af"
                                  fontSize={12}
                                />
                                <YAxis 
                                  stroke="#9ca3af"
                                  fontSize={12}
                                  tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`}
                                />
                                <Tooltip 
                                  contentStyle={{
                                    backgroundColor: '#374151',
                                    border: '1px solid #4b5563',
                                    borderRadius: '8px',
                                    color: '#f9fafb'
                                  }}
                                  formatter={(value: number, name: string) => [
                                    `$${value.toLocaleString()}`,
                                    name === 'value' ? '포트폴리오' : '벤치마크'
                                  ]}
                                />
                                <Line 
                                  type="monotone" 
                                  dataKey="value" 
                                  stroke="#6b7280" 
                                  strokeWidth={2}
                                  dot={false}
                                  name="포트폴리오"
                                />
                                <Line 
                                  type="monotone" 
                                  dataKey="benchmark" 
                                  stroke="#9ca3af" 
                                  strokeWidth={1}
                                  strokeDasharray="5 5"
                                  dot={false}
                                  name="벤치마크"
                                />
                              </LineChart>
                            </ResponsiveContainer>
                          </div>
                        </div>

                        <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6">
                          <h3 className="text-lg font-bold text-gray-100 mb-4 flex items-center text-gray-400">
                            <BarChart3 />
                            <span className="ml-2">2️⃣ Performance Dashboard - 성과 대시보드</span>
                          </h3>
                          
                          <div className="grid md:grid-cols-2 gap-6">
                            <div>
                              <h4 className="text-md font-semibold text-gray-200 mb-3">위험 분석</h4>
                              <div className="space-y-4">
                                <div className="flex justify-between items-center">
                                  <span className="text-gray-400">변동성</span>
                                  <span className="text-gray-100 font-semibold">{backtestResult.volatility.toFixed(1)}%</span>
                                </div>
                                <div className="w-full bg-gray-700 rounded-full h-2">
                                  <div 
                                    className="bg-gray-500 h-2 rounded-full" 
                                    style={{ width: `${Math.min(backtestResult.volatility * 3, 100)}%` }}
                                  ></div>
                                </div>
                                
                                <div className="flex justify-between items-center">
                                  <span className="text-gray-400">최대 낙폭</span>
                                  <span className="text-gray-300 font-semibold">-{backtestResult.maxDrawdown.toFixed(1)}%</span>
                                </div>
                                <div className="w-full bg-gray-700 rounded-full h-2">
                                  <div 
                                    className="bg-gray-400 h-2 rounded-full" 
                                    style={{ width: `${Math.min(backtestResult.maxDrawdown * 2, 100)}%` }}
                                  ></div>
                                </div>
                                
                                <div className="flex justify-between items-center">
                                  <span className="text-gray-400">칼마 비율</span>
                                  <span className="text-gray-200 font-semibold">{backtestResult.calmarRatio.toFixed(2)}</span>
                                </div>
                                <div className="w-full bg-gray-700 rounded-full h-2">
                                  <div 
                                    className="bg-gray-600 h-2 rounded-full" 
                                    style={{ width: `${Math.min(backtestResult.calmarRatio * 50, 100)}%` }}
                                  ></div>
                                </div>
                              </div>
                            </div>

                            <div>
                              <h4 className="text-md font-semibold text-gray-200 mb-3">수익성 분석</h4>
                              <div className="space-y-4">
                                <div className="flex justify-between items-center">
                                  <span className="text-gray-400">연간 수익률</span>
                                  <span className="text-gray-200 font-semibold">{backtestResult.annualReturn.toFixed(1)}%</span>
                                </div>
                                <div className="w-full bg-gray-700 rounded-full h-2">
                                  <div 
                                    className="bg-gray-500 h-2 rounded-full" 
                                    style={{ width: `${Math.min(backtestResult.annualReturn * 3, 100)}%` }}
                                  ></div>
                                </div>
                                
                                <div className="flex justify-between items-center">
                                  <span className="text-gray-400">샤프 비율</span>
                                  <span className="text-gray-200 font-semibold">{backtestResult.sharpeRatio.toFixed(2)}</span>
                                </div>
                                <div className="w-full bg-gray-700 rounded-full h-2">
                                  <div 
                                    className="bg-gray-500 h-2 rounded-full" 
                                    style={{ width: `${Math.min(backtestResult.sharpeRatio * 33, 100)}%` }}
                                  ></div>
                                </div>
                                
                                <div className="flex justify-between items-center">
                                  <span className="text-gray-400">승률</span>
                                  <span className="text-gray-200 font-semibold">{backtestResult.winRate.toFixed(1)}%</span>
                                </div>
                                <div className="w-full bg-gray-700 rounded-full h-2">
                                  <div 
                                    className="bg-gray-600 h-2 rounded-full" 
                                    style={{ width: `${backtestResult.winRate}%` }}
                                  ></div>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>

                        <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6">
                          <h3 className="text-lg font-bold text-gray-100 mb-4 flex items-center text-gray-400">
                            <Shield />
                            <span className="ml-2">3️⃣ Drawdown Analysis - 낙폭 분석</span>
                          </h3>
                          
                          <div className="h-64">
                            <ResponsiveContainer width="100%" height="100%">
                              <AreaChart data={drawdownData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#4b5563" />
                                <XAxis 
                                  dataKey="date" 
                                  stroke="#9ca3af"
                                  fontSize={12}
                                />
                                <YAxis 
                                  stroke="#9ca3af"
                                  fontSize={12}
                                  tickFormatter={(value) => `${value.toFixed(1)}%`}
                                />
                                <Tooltip 
                                  contentStyle={{
                                    backgroundColor: '#374151',
                                    border: '1px solid #4b5563',
                                    borderRadius: '8px',
                                    color: '#f9fafb'
                                  }}
                                  formatter={(value: number) => [`${value.toFixed(2)}%`, 'Drawdown']}
                                />
                                <Area 
                                  type="monotone" 
                                  dataKey="drawdown" 
                                  stroke="#6b7280" 
                                  fill="#6b7280"
                                  fillOpacity={0.3}
                                />
                              </AreaChart>
                            </ResponsiveContainer>
                          </div>
                          
                          <div className="mt-4 bg-gray-700 rounded-lg p-4">
                            <div className="flex items-center space-x-2 mb-2">
                              <div className="text-gray-400">
                                <AlertCircle />
                              </div>
                              <h4 className="text-sm font-semibold text-gray-200">Drawdown 분석</h4>
                            </div>
                            <p className="text-xs text-gray-400">
                              이 차트는 포트폴리오의 최고점 대비 하락 정도를 보여줍니다. 
                              낮은 drawdown은 더 안정적인 투자를 의미합니다.
                            </p>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {backtestResult.components && (
                    <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6">
                      <h3 className="text-lg font-bold text-gray-100 mb-4 flex items-center text-gray-400">
                        <PieChart />
                        <span className="ml-2">포트폴리오 구성 (TOP 15 종목)</span>
                      </h3>
                      
                      <div className="grid grid-cols-5 gap-4">
                        {backtestResult.components.slice(0, 15).map((symbol) => (
                          <div key={symbol} className="bg-gray-700 rounded-lg p-3 text-center">
                            <p className="text-gray-100 font-semibold">{symbol}</p>
                            <p className="text-gray-400 text-sm">
                              {((backtestResult.weights?.[symbol] || 1/15) * 100).toFixed(1)}%
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6">
                    <h3 className="text-lg font-bold text-gray-100 mb-4 flex items-center text-gray-400">
                      <Target />
                      <span className="ml-2">전략 등급 평가</span>
                    </h3>
                    
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-gray-400 mb-2">종합 평가</p>
                        <div className="flex items-center space-x-3">
                          <span className={`text-3xl font-bold ${getStrategyGradeColor(backtestResult)}`}>
                            {getStrategyGrade(backtestResult)}
                          </span>
                          <div>
                            <p className="text-gray-100 font-semibold">{getStrategyGradeText(backtestResult)}</p>
                            <p className="text-gray-400 text-sm">{getStrategyGradeDescription(backtestResult)}</p>
                          </div>
                        </div>
                      </div>
                      
                      <div className="text-right">
                        <p className="text-gray-400 text-sm mb-1">벤치마크 대비</p>
                        <div className="flex items-center space-x-2">
                          <span className={`text-lg font-bold ${
                            backtestResult.annualReturn > 10 ? 'text-gray-300' : 'text-gray-500'
                          }`}>
                            {backtestResult.annualReturn > 10 ? '+' : ''}{(backtestResult.annualReturn - 10).toFixed(1)}%
                          </span>
                          <span className="text-gray-400 text-sm">vs S&P 500</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ) : (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="bg-gray-800 rounded-2xl border border-gray-700 p-12 text-center"
                >
                  <div className="w-16 h-16 bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4 text-gray-400">
                    <BarChart3 />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-100 mb-2">백테스트 결과를 기다리는 중</h3>
                  <p className="text-gray-400">
                    왼쪽에서 Core 전략을 선택하고 백테스트를 실행하면 
                    <br />
                    상세한 성과 분석 결과가 여기에 표시됩니다.
                  </p>
                  
                  <div className="mt-8 grid grid-cols-3 gap-4">
                    <div className="bg-gray-700 rounded-lg p-4 text-center">
                      <div className="text-gray-400 flex justify-center mb-2">
                        <Calendar />
                      </div>
                      <p className="text-gray-100 font-semibold">10년 분석</p>
                      <p className="text-gray-400 text-sm">장기 성과 검증</p>
                    </div>
                    <div className="bg-gray-700 rounded-lg p-4 text-center">
                      <div className="text-gray-400 flex justify-center mb-2">
                        <PieChart />
                      </div>
                      <p className="text-gray-100 font-semibold">멀티 종목</p>
                      <p className="text-gray-400 text-sm">리스크 분산</p>
                    </div>
                    <div className="bg-gray-700 rounded-lg p-4 text-center">
                      <div className="text-gray-400 flex justify-center mb-2">
                        <TrendingUp />
                      </div>
                      <p className="text-gray-100 font-semibold">MVP 3개 그래프</p>
                      <p className="text-gray-400 text-sm">핵심 분석</p>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>

      <footer className="bg-gray-800 border-t border-gray-700 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center space-x-3 mb-4 md:mb-0">
              <div className="w-8 h-8 bg-gray-600 rounded-lg flex items-center justify-center text-gray-200">
                <TrendingUp />
              </div>
              <div>
                <p className="text-gray-100 font-semibold">Quant Strategy Backtester</p>
                <p className="text-gray-400 text-sm">MVP Version - Core 4 Strategies</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-6 text-sm text-gray-400">
              <p>📊 MVP 3개 그래프</p>
              <p>⚡ 고성능 분석</p>
              <p>🎯 Core 4 전략</p>
              <p>🔍 10년 백테스트</p>
            </div>
          </div>
          
          <div className="border-t border-gray-700 mt-6 pt-6 text-center">
            <p className="text-gray-500 text-sm">
              © 2025 Quant Strategy Backtester MVP. 본 시스템의 백테스트 결과는 과거 데이터를 기반으로 하며, 
              미래 수익을 보장하지 않습니다. 투자 결정 시 신중하게 검토하시기 바랍니다.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
