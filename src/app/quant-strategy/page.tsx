//file: src/app/quant-strategy/page.tsx
//my strategy page

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
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  Area,
  AreaChart
} from 'recharts';

// 타입 정의들
interface StrategyConfig {
  name: string;
  weight: number;
  category: string;
  parameters: Record<string, any>;
}

interface BacktestConfig {
  investment_amount: number;
  start_date: string;
  end_date: string;
  rebalancing_freq: string;
  strategies: StrategyConfig[];
}

interface BacktestResult {
  strategyConfig: BacktestConfig;
  performanceSummary: {
    total_return: number;
    annual_return: number;
    annual_volatility: number;
    sharpe_ratio: number;
    max_drawdown: number;
    win_rate: number;
    sortino_ratio: number;
    calmar_ratio: number;
    var_95: number;
    profit_factor: number;
    total_trades: number;
    final_value: number;
    initial_value: number;
  };
  portfolioHistory: Array<{
    date: string;
    total_value: number;
    cash: number;
    invested_value: number;
    position_count: number;
  }>;
  tradeHistory: Array<{
    date: string;
    symbol: string;
    action: string;
    shares: number;
    price: number;
    total_value: number;
    commission: number;
    reason: string;
  }>;
}

// 아이콘 컴포넌트들
const TrendingUp = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <polyline points="22,7 13.5,15.5 8.5,10.5 2,17"></polyline>
    <polyline points="16,7 22,7 22,13"></polyline>
  </svg>
);

const TrendingDown = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <polyline points="22,17 13.5,8.5 8.5,13.5 2,7"></polyline>
    <polyline points="16,17 22,17 22,11"></polyline>
  </svg>
);

const BarChart3 = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <path d="M3 3v18h18"></path>
    <path d="M18 17V9"></path>
    <path d="M13 17V5"></path>
    <path d="M8 17v-3"></path>
  </svg>
);

const PieChartIcon = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <path d="M21.21 15.89A10 10 0 1 1 8 2.83"></path>
    <path d="M22 12A10 10 0 0 0 12 2v10z"></path>
  </svg>
);

const Target = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <circle cx="12" cy="12" r="10"></circle>
    <circle cx="12" cy="12" r="6"></circle>
    <circle cx="12" cy="12" r="2"></circle>
  </svg>
);

const Shield = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
  </svg>
);

const Activity = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <polyline points="22,12 18,12 15,21 9,3 6,12 2,12"></polyline>
  </svg>
);

const DollarSign = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <line x1="12" y1="1" x2="12" y2="23"></line>
    <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
  </svg>
);

const Download = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
    <polyline points="7,10 12,15 17,10"></polyline>
    <line x1="12" y1="15" x2="12" y2="3"></line>
  </svg>
);

const Eye = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
    <circle cx="12" cy="12" r="3"></circle>
  </svg>
);

const Play = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <polygon points="5,3 19,12 5,21"></polygon>
  </svg>
);

const Settings = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <circle cx="12" cy="12" r="3"></circle>
    <path d="M12 1v6m0 6v6m11-7h-6m-6 0H1"></path>
  </svg>
);

const Plus = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <line x1="12" y1="5" x2="12" y2="19"></line>
    <line x1="5" y1="12" x2="19" y2="12"></line>
  </svg>
);

const Trash2 = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <polyline points="3,6 5,6 21,6"></polyline>
    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
  </svg>
);

const RefreshCw = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <polyline points="23,4 23,10 17,10"></polyline>
    <polyline points="1,20 1,14 7,14"></polyline>
    <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"></path>
  </svg>
);

// 전략 정의
const availableStrategies = {
  '기술적 분석': {
    'Momentum': { 
      name: 'Momentum', 
      description: '과거 수익률 기반 모멘텀 전략',
      defaultParams: { lookback_period: 20, min_return_threshold: 0.02, top_n: 10 }
    },
    'RSI': { 
      name: 'RSI', 
      description: '상대강도지수 기반 역추세 전략',
      defaultParams: { period: 14, overbought: 70, oversold: 30, top_n: 10 }
    },
    'BollingerBands': { 
      name: 'BollingerBands', 
      description: '볼린저밴드 기반 평균회귀 전략',
      defaultParams: { period: 20, std_dev: 2.0, top_n: 10 }
    },
    'MACD': { 
      name: 'MACD', 
      description: 'MACD 기반 추세추종 전략',
      defaultParams: { fast_period: 12, slow_period: 26, signal_period: 9, top_n: 10 }
    }
  },
  '재무 기반': {
    'Value': { 
      name: 'Value', 
      description: 'PER, PBR 기반 가치투자 전략',
      defaultParams: { max_pe_ratio: 15, max_pb_ratio: 1.5, min_market_cap: 1000000000, top_n: 10 }
    },
    'Quality': { 
      name: 'Quality', 
      description: 'ROE, ROA 기반 퀄리티 전략',
      defaultParams: { min_roe: 15, min_roa: 8, max_debt_equity: 0.5, top_n: 10 }
    },
    'Growth': { 
      name: 'Growth', 
      description: '매출/이익 성장률 기반 성장투자',
      defaultParams: { min_revenue_growth: 10, min_earnings_growth: 15, top_n: 10 }
    },
    'Dividend': { 
      name: 'Dividend', 
      description: '배당수익률 기반 배당투자',
      defaultParams: { min_dividend_yield: 2.0, min_payout_ratio: 0.3, max_payout_ratio: 0.8, top_n: 10 }
    }
  },
  '혼합 전략': {
    'GARP': { 
      name: 'GARP', 
      description: '합리적 가격의 성장주 전략',
      defaultParams: { max_peg_ratio: 1.5, min_roe: 15, max_pe_ratio: 20, top_n: 10 }
    },
    'MomentumValue': { 
      name: 'MomentumValue', 
      description: '모멘텀과 가치투자 결합 전략',
      defaultParams: { momentum_weight: 0.6, value_weight: 0.4, lookback_period: 60, top_n: 15 }
    }
  }
};

// 모의 데이터 생성기
class BacktestDataGenerator {
  static generateMockResults(config: BacktestConfig): BacktestResult {
    // 포트폴리오 가치 히스토리 생성
    const portfolioHistory = [];
    const startDate = new Date(config.start_date);
    const endDate = new Date(config.end_date);
    let currentValue = config.investment_amount;
    
    for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 7)) {
      const volatility = 0.015;
      const return_rate = (Math.random() - 0.45) * volatility * 2;
      currentValue *= (1 + return_rate);
      
      portfolioHistory.push({
        date: d.toISOString().split('T')[0],
        total_value: currentValue,
        cash: currentValue * (0.05 + Math.random() * 0.1),
        invested_value: currentValue * (0.85 + Math.random() * 0.1),
        position_count: Math.floor(8 + Math.random() * 12)
      });
    }

    // 거래 히스토리 생성
    const tradeHistory = [];
    const symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'NVDA', 'META', 'JPM', 'JNJ', 'PG'];
    
    for (let i = 0; i < 85; i++) {
      const symbol = symbols[Math.floor(Math.random() * symbols.length)];
      const action = Math.random() > 0.5 ? 'buy' : 'sell';
      const shares = Math.floor(10 + Math.random() * 90);
      const price = 50 + Math.random() * 200;
      
      tradeHistory.push({
        date: new Date(startDate.getTime() + Math.random() * (endDate.getTime() - startDate.getTime())).toISOString().split('T')[0],
        symbol,
        action,
        shares,
        price,
        total_value: shares * price,
        commission: shares * price * 0.001,
        reason: action === 'buy' ? 'Rebalancing' : 'Profit Taking'
      });
    }

    // 성과 계산 (실제로는 전략에 따라 달라짐)
    const totalReturn = (currentValue - config.investment_amount) / config.investment_amount;
    const years = (endDate.getTime() - startDate.getTime()) / (365.25 * 24 * 60 * 60 * 1000);
    const annualReturn = Math.pow(1 + totalReturn, 1 / years) - 1;

    return {
      strategyConfig: config,
      performanceSummary: {
        total_return: totalReturn,
        annual_return: annualReturn,
        annual_volatility: 0.156,
        sharpe_ratio: 1.11,
        max_drawdown: -0.128,
        win_rate: 0.587,
        sortino_ratio: 1.67,
        calmar_ratio: 1.36,
        var_95: -0.025,
        profit_factor: 1.45,
        total_trades: 85,
        final_value: currentValue,
        initial_value: config.investment_amount
      },
      portfolioHistory,
      tradeHistory
    };
  }
}

// 메인 컴포넌트
export default function QuantResultsDisplay(): JSX.Element {
  const [selectedTab, setSelectedTab] = useState<string>('overview');

  // 백테스트 설정 상태
  const [investmentAmount, setInvestmentAmount] = useState<number>(100000);
  const [startDate, setStartDate] = useState<string>('2020-01-01');
  const [endDate, setEndDate] = useState<string>('2024-12-31');
  const [rebalancingFreq, setRebalancingFreq] = useState<string>('quarterly');
  const [selectedStrategies, setSelectedStrategies] = useState<StrategyConfig[]>([
    { name: 'Momentum', weight: 0.25, category: '기술적 분석', parameters: { lookback_period: 20, min_return_threshold: 0.02, top_n: 10 } },
    { name: 'Value', weight: 0.25, category: '재무 기반', parameters: { max_pe_ratio: 15, max_pb_ratio: 1.5, min_market_cap: 1000000000, top_n: 10 } },
    { name: 'Quality', weight: 0.25, category: '재무 기반', parameters: { min_roe: 15, min_roa: 8, max_debt_equity: 0.5, top_n: 10 } },
    { name: 'Growth', weight: 0.25, category: '재무 기반', parameters: { min_revenue_growth: 10, min_earnings_growth: 15, top_n: 10 } }
  ]);

  // 백테스트 결과 상태
  const [backtestResults, setBacktestResults] = useState<BacktestResult | null>(null);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [showParameterModal, setShowParameterModal] = useState<string | null>(null);

  const tabs = [
    { id: 'overview', name: '성과 개요', icon: BarChart3 },
    { id: 'portfolio', name: '포트폴리오', icon: PieChartIcon },
    { id: 'trades', name: '거래 내역', icon: Activity },
    { id: 'risk', name: '위험 분석', icon: Shield }
  ];

  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatPercentage = (value: number): string => {
    return `${(value * 100).toFixed(2)}%`;
  };

  const formatNumber = (value: number, decimals: number = 2): string => {
    return value.toFixed(decimals);
  };

  const getReturnColor = (value: number): string => {
    if (value > 0.05) return 'text-green-400';
    if (value > 0) return 'text-green-300';
    if (value > -0.05) return 'text-yellow-400';
    return 'text-red-400';
  };

  // 전략 추가
  const addStrategy = (categoryName: string, strategyName: string): void => {
    const strategy = availableStrategies[categoryName as keyof typeof availableStrategies][strategyName as any];
    if (!strategy) return;

    const newStrategy: StrategyConfig = {
      name: strategy.name,
      weight: 0.1,
      category: categoryName,
      parameters: { ...strategy.defaultParams }
    };

    setSelectedStrategies(prev => [...prev, newStrategy]);
  };

  // 전략 제거
  const removeStrategy = (index: number): void => {
    setSelectedStrategies(prev => prev.filter((_, i) => i !== index));
  };

  // 가중치 업데이트
  const updateStrategyWeight = (index: number, weight: number): void => {
    setSelectedStrategies(prev => 
      prev.map((strategy, i) => 
        i === index ? { ...strategy, weight } : strategy
      )
    );
  };

  // 파라미터 업데이트
  const updateStrategyParameters = (index: number, parameters: Record<string, any>): void => {
    setSelectedStrategies(prev => 
      prev.map((strategy, i) => 
        i === index ? { ...strategy, parameters } : strategy
      )
    );
  };

  // 새로운 백테스트 시작
  const startNewBacktest = (): void => {
    setBacktestResults(null);
    setSelectedTab('overview');
  };

  // 백테스트 실행
  const runBacktest = async (): Promise<void> => {
    setIsRunning(true);
    
    // 시뮬레이션 지연
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    const config: BacktestConfig = {
      investment_amount: investmentAmount,
      start_date: startDate,
      end_date: endDate,
      rebalancing_freq: rebalancingFreq,
      strategies: selectedStrategies
    };

    const results = BacktestDataGenerator.generateMockResults(config);
    setBacktestResults(results);
    setIsRunning(false);
  };

  // 리포트 다운로드 - 실제로 동작
  const downloadReport = (): void => {
    if (!backtestResults) return;
    
    const reportData = {
      timestamp: new Date().toISOString(),
      config: backtestResults.strategyConfig,
      performance: backtestResults.performanceSummary,
      portfolioHistory: backtestResults.portfolioHistory,
      tradeHistory: backtestResults.tradeHistory
    };
    
    const dataStr = JSON.stringify(reportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `backtest_report_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // 상세 분석 보기 - 실제로 동작
  const showDetailedAnalysis = (): void => {
    if (!backtestResults) return;
    
    // 새 창에서 상세 분석 표시
    const newWindow = window.open('', '_blank', 'width=1200,height=800');
    if (newWindow) {
      newWindow.document.write(`
        <html>
          <head>
            <title>상세 백테스트 분석</title>
            <style>
              body { font-family: Arial, sans-serif; margin: 20px; background: #111827; color: #f9fafb; }
              .header { border-bottom: 2px solid #374151; padding-bottom: 20px; margin-bottom: 20px; }
              .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
              .metric-card { background: #1f2937; padding: 15px; border-radius: 8px; }
              .metric-title { color: #9ca3af; font-size: 14px; margin-bottom: 5px; }
              .metric-value { font-size: 24px; font-weight: bold; }
              .positive { color: #10b981; }
              .negative { color: #ef4444; }
              .neutral { color: #f59e0b; }
              pre { background: #1f2937; padding: 15px; border-radius: 8px; overflow-x: auto; }
            </style>
          </head>
          <body>
            <div class="header">
              <h1>📊 퀀트 전략 백테스트 상세 분석 리포트</h1>
              <p>생성 시간: ${new Date().toLocaleString('ko-KR')}</p>
              <p>백테스트 기간: ${backtestResults.strategyConfig.start_date} ~ ${backtestResults.strategyConfig.end_date}</p>
            </div>
            
            <div class="metrics">
              <div class="metric-card">
                <div class="metric-title">총 수익률</div>
                <div class="metric-value ${backtestResults.performanceSummary.total_return > 0 ? 'positive' : 'negative'}">
                  ${formatPercentage(backtestResults.performanceSummary.total_return)}
                </div>
              </div>
              <div class="metric-card">
                <div class="metric-title">연평균 수익률</div>
                <div class="metric-value ${backtestResults.performanceSummary.annual_return > 0 ? 'positive' : 'negative'}">
                  ${formatPercentage(backtestResults.performanceSummary.annual_return)}
                </div>
              </div>
              <div class="metric-card">
                <div class="metric-title">샤프 비율</div>
                <div class="metric-value neutral">
                  ${formatNumber(backtestResults.performanceSummary.sharpe_ratio)}
                </div>
              </div>
              <div class="metric-card">
                <div class="metric-title">최대 낙폭</div>
                <div class="metric-value negative">
                  ${formatPercentage(backtestResults.performanceSummary.max_drawdown)}
                </div>
              </div>
            </div>
            
            <h2>📋 전체 데이터</h2>
            <pre>${JSON.stringify(backtestResults, null, 2)}</pre>
          </body>
        </html>
      `);
      newWindow.document.close();
    }
  };

  // 가중치 총합 계산
  const totalWeight = selectedStrategies.reduce((sum, strategy) => sum + strategy.weight, 0);

  // 차트 데이터 준비
  const chartData = backtestResults?.portfolioHistory.map(item => ({
    date: item.date,
    value: item.total_value,
    return: ((item.total_value / backtestResults.performanceSummary.initial_value) - 1) * 100
  })) || [];

  const strategyWeightData = backtestResults?.strategyConfig.strategies.map(strategy => ({
    name: strategy.name,
    weight: strategy.weight * 100,
    category: strategy.category
  })) || [];

  const COLORS = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444', '#06b6d4'];


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
              <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center text-white">
                <BarChart3 />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-100">Quant Strategy Backtest</h1>
                <p className="text-gray-400 text-sm">Combined Strategy Performance Analysis</p>
              </div>
            </motion.div>
            
            <div className="flex items-center space-x-4">
              {backtestResults && (
                <>
                  <button
                    onClick={startNewBacktest}
                    className="flex items-center space-x-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-100 rounded-lg transition-all"
                  >
                    <RefreshCw className="w-4 h-4" />
                    <span>새 백테스트</span>
                  </button>
                  <div className="text-right">
                    <p className="text-gray-300 text-xs">백테스트 기간</p>
                    <p className="text-gray-100 font-semibold">
                      {backtestResults.strategyConfig.start_date} ~ {backtestResults.strategyConfig.end_date}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-gray-300 text-xs">총 수익률</p>
                    <p className={`font-bold text-lg ${getReturnColor(backtestResults.performanceSummary.total_return)}`}>
                      {formatPercentage(backtestResults.performanceSummary.total_return)}
                    </p>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </header>
      
      



<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 xl:grid-cols-4 gap-8">
          
          {/* 왼쪽 설정 패널 */}
          <div className="xl:col-span-1 space-y-6">
            {/* 투자 설정 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-gray-800 rounded-2xl border border-gray-700 p-6"
            >
              <h2 className="text-xl font-bold text-gray-100 mb-6 flex items-center">
                <DollarSign className="w-5 h-5 mr-2 text-green-400" />
                투자 설정
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-gray-300 text-sm font-medium mb-2">투자 금액</label>
                  <input
                    type="number"
                    value={investmentAmount}
                    onChange={(e) => setInvestmentAmount(Number(e.target.value))}
                    className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 focus:outline-none focus:border-blue-400"
                    min="10000"
                    step="10000"
                  />
                </div>

                <div>
                  <label className="block text-gray-300 text-sm font-medium mb-2">시작 날짜</label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 focus:outline-none focus:border-blue-400"
                  />
                </div>

                <div>
                  <label className="block text-gray-300 text-sm font-medium mb-2">종료 날짜</label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 focus:outline-none focus:border-blue-400"
                  />
                </div>

                <div>
                  <label className="block text-gray-300 text-sm font-medium mb-2">리밸런싱 주기</label>
                  <select
                    value={rebalancingFreq}
                    onChange={(e) => setRebalancingFreq(e.target.value)}
                    className="w-full p-3 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 focus:outline-none focus:border-blue-400"
                  >
                    <option value="monthly">월간</option>
                    <option value="quarterly">분기</option>
                    <option value="yearly">연간</option>
                  </select>
                </div>
              </div>
            </motion.div>

            {/* 전략 선택 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-gray-800 rounded-2xl border border-gray-700 p-6"
            >
              <h2 className="text-xl font-bold text-gray-100 mb-6 flex items-center">
                <Target className="w-5 h-5 mr-2 text-blue-400" />
                전략 구성
              </h2>

              {/* 선택된 전략들 */}
              <div className="space-y-3 mb-6">
                {selectedStrategies.map((strategy, index) => (
                  <div key={index} className="bg-gray-700 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <div 
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: COLORS[index % COLORS.length] }}
                        ></div>
                        <span className="text-gray-100 font-semibold text-sm">{strategy.name}</span>
                      </div>
                      <button
                        onClick={() => removeStrategy(index)}
                        className="text-red-400 hover:text-red-300"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                    
                    <div className="flex items-center space-x-2 mb-2">
                      <label className="text-gray-300 text-xs">가중치:</label>
                      <input
                        type="number"
                        value={strategy.weight}
                        onChange={(e) => updateStrategyWeight(index, Number(e.target.value))}
                        className="w-20 p-1 bg-gray-600 border border-gray-500 rounded text-gray-100 text-xs"
                        min="0"
                        max="1"
                        step="0.05"
                      />
                      <span className="text-gray-400 text-xs">{formatPercentage(strategy.weight)}</span>
                    </div>

                    <button
                      onClick={() => setShowParameterModal(strategy.name)}
                      className="text-blue-400 hover:text-blue-300 text-xs flex items-center space-x-1"
                    >
                      <Settings className="w-3 h-3" />
                      <span>파라미터 설정</span>
                    </button>
                  </div>
                ))}
                
                {totalWeight !== 1.0 && (
                  <div className="bg-yellow-600 bg-opacity-20 border border-yellow-500 rounded-lg p-2">
                    <p className="text-yellow-400 text-xs">
                      총 가중치: {formatPercentage(totalWeight)} (100%가 되어야 함)
                    </p>
                  </div>
                )}
              </div>

              {/* 전략 추가 */}
              <div className="space-y-3">
                <h3 className="text-gray-100 font-semibold text-sm">전략 추가</h3>
                {Object.entries(availableStrategies).map(([categoryName, strategies]) => (
                  <div key={categoryName}>
                    <h4 className="text-gray-300 text-xs font-medium mb-2">{categoryName}</h4>
                    <div className="space-y-1">
                      {Object.entries(strategies).map(([strategyName, strategyInfo]) => (
                        <button
                          key={strategyName}
                          onClick={() => addStrategy(categoryName, strategyName)}
                          disabled={selectedStrategies.some(s => s.name === strategyInfo.name)}
                          className={`w-full text-left p-2 rounded text-xs transition-all flex items-center space-x-2 ${
                            selectedStrategies.some(s => s.name === strategyInfo.name)
                              ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                              : 'bg-gray-700 text-gray-100 hover:bg-gray-600'
                          }`}
                        >
                          <Plus className="w-3 h-3" />
                          <span>{strategyInfo.name}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              {/* 백테스트 실행 버튼 */}
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={runBacktest}
                disabled={selectedStrategies.length === 0 || isRunning || totalWeight <= 0}
                className={`w-full mt-6 py-3 px-4 rounded-xl font-semibold transition-all flex items-center justify-center space-x-2 ${
                  selectedStrategies.length > 0 && !isRunning && totalWeight > 0
                    ? 'bg-blue-600 text-white hover:bg-blue-500'
                    : 'bg-gray-600 text-gray-400 cursor-not-allowed'
                }`}
              >
                {isRunning ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>백테스트 실행 중...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    <span>백테스트 실행</span>
                  </>
                )}
              </motion.button>
            </motion.div>
          </div>

          {/* 오른쪽 결과 패널 */}
          <div className="xl:col-span-3">
            {backtestResults ? (
              <div className="space-y-6">
                {/* 핵심 성과 지표 카드들 */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6"
                >
                  <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-gray-300 text-sm font-medium">총 수익률</p>
                        <p className={`text-2xl font-bold ${getReturnColor(backtestResults.performanceSummary.total_return)}`}>
                          {formatPercentage(backtestResults.performanceSummary.total_return)}
                        </p>
                      </div>
                      <TrendingUp className="w-8 h-8 text-green-400" />
                    </div>
                    <div className="mt-4">
                      <p className="text-gray-400 text-xs">
                        초기 {formatCurrency(backtestResults.performanceSummary.initial_value)} → 
                        최종 {formatCurrency(backtestResults.performanceSummary.final_value)}
                      </p>
                    </div>
                  </div>

                  <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-gray-300 text-sm font-medium">샤프 비율</p>
                        <p className="text-2xl font-bold text-gray-100">
                          {formatNumber(backtestResults.performanceSummary.sharpe_ratio)}
                        </p>
                      </div>
                      <Target className="w-8 h-8 text-blue-400" />
                    </div>
                    <div className="mt-4">
                      <p className="text-gray-400 text-xs">
                        연간 변동성: {formatPercentage(backtestResults.performanceSummary.annual_volatility)}
                      </p>
                    </div>
                  </div>

                  <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-gray-300 text-sm font-medium">최대 낙폭</p>
                        <p className="text-2xl font-bold text-red-400">
                          {formatPercentage(backtestResults.performanceSummary.max_drawdown)}
                        </p>
                      </div>
                      <TrendingDown className="w-8 h-8 text-red-400" />
                    </div>
                    <div className="mt-4">
                      <p className="text-gray-400 text-xs">
                        칼마 비율: {formatNumber(backtestResults.performanceSummary.calmar_ratio)}
                      </p>
                    </div>
                  </div>

                  <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-gray-300 text-sm font-medium">총 거래</p>
                        <p className="text-2xl font-bold text-gray-100">
                          {backtestResults.performanceSummary.total_trades}
                        </p>
                      </div>
                      <Activity className="w-8 h-8 text-purple-400" />
                    </div>
                    <div className="mt-4">
                      <p className="text-gray-400 text-xs">
                        승률: {formatPercentage(backtestResults.performanceSummary.win_rate)}
                      </p>
                    </div>
                  </div>
                </motion.div>

                {/* 벤치마크 대비 성과 (한 줄로 축소) */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-gray-800 rounded-xl border border-gray-700 p-4"
                >
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-bold text-gray-100">벤치마크 대비 성과 (vs S&P 500)</h3>
                    <div className="flex items-center space-x-6">
                      <div className="text-center">
                        <span className="text-gray-300 text-xs">포트폴리오: </span>
                        <span className={`font-bold ${getReturnColor(backtestResults.performanceSummary.annual_return)}`}>
                          {formatPercentage(backtestResults.performanceSummary.annual_return)}
                        </span>
                      </div>
                      <div className="text-center">
                        <span className="text-gray-300 text-xs">S&P 500: </span>
                        <span className="text-blue-400 font-bold">10.5%</span>
                      </div>
                      <div className="text-center">
                        <span className="text-gray-300 text-xs">알파: </span>
                        <span className={`font-bold ${
                          (backtestResults.performanceSummary.annual_return - 0.105) > 0 ? 'text-green-400' : 'text-red-400'
                        }`}>
                          {formatPercentage(backtestResults.performanceSummary.annual_return - 0.105)}
                        </span>
                      </div>
                    </div>
                  </div>
                </motion.div>

                {/* 탭 네비게이션 */}
                <div className="bg-gray-800 rounded-2xl border border-gray-700">
                  <div className="flex border-b border-gray-700">
                    {tabs.map((tab, index) => (
                      <motion.button
                        key={tab.id}
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                        onClick={() => setSelectedTab(tab.id)}
                        className={`flex-1 px-6 py-4 text-sm font-medium transition-all flex items-center justify-center space-x-2 ${
                          selectedTab === tab.id
                            ? 'text-blue-400 border-b-2 border-blue-400 bg-gray-700'
                            : 'text-gray-400 hover:text-gray-300 hover:bg-gray-700'
                        }`}
                      >
                        <tab.icon className="w-4 h-4" />
                        <span>{tab.name}</span>
                      </motion.button>
                    ))}
                  </div>

                  {/* 탭 컨텐츠 */}
                  <div className="p-6">
                    <AnimatePresence mode="wait">
                      {selectedTab === 'overview' && (
                        <motion.div
                          key="overview"
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -20 }}
                          className="space-y-6"
                        >
                          {/* 수익률 차트 */}
                          <div className="bg-gray-700 rounded-xl p-6">
                            <h3 className="text-lg font-bold text-gray-100 mb-4 flex items-center">
                              <TrendingUp className="w-5 h-5 mr-2 text-green-400" />
                              포트폴리오 수익률 추이
                            </h3>
                            <div className="h-80">
                              <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={chartData}>
                                  <defs>
                                    <linearGradient id="colorReturn" x1="0" y1="0" x2="0" y2="1">
                                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                                      <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                                    </linearGradient>
                                  </defs>
                                  <CartesianGrid strokeDasharray="3 3" stroke="#4b5563" />
                                  <XAxis 
                                    dataKey="date" 
                                    stroke="#9ca3af"
                                    fontSize={12}
                                  />
                                  <YAxis 
                                    stroke="#9ca3af"
                                    fontSize={12}
                                    tickFormatter={(value) => `${value.toFixed(0)}%`}
                                  />
                                  <Tooltip 
                                    contentStyle={{
                                      backgroundColor: '#374151',
                                      border: '1px solid #4b5563',
                                      borderRadius: '8px',
                                      color: '#f9fafb'
                                    }}
                                    formatter={(value: any) => [`${value.toFixed(2)}%`, '수익률']}
                                  />
                                  <Area 
                                    type="monotone" 
                                    dataKey="return" 
                                    stroke="#10b981" 
                                    strokeWidth={2}
                                    fill="url(#colorReturn)"
                                  />
                                </AreaChart>
                              </ResponsiveContainer>
                            </div>
                          </div>

                          {/* 상세 성과 지표 */}
                          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                            <div className="bg-gray-700 rounded-xl p-6">
                              <h3 className="text-lg font-bold text-gray-100 mb-4">수익률 지표</h3>
                              <div className="space-y-3">
                                <div className="flex justify-between">
                                  <span className="text-gray-300">연평균 수익률</span>
                                  <span className="text-gray-100 font-semibold">
                                    {formatPercentage(backtestResults.performanceSummary.annual_return)}
                                  </span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-gray-300">소티노 비율</span>
                                  <span className="text-gray-100 font-semibold">
                                    {formatNumber(backtestResults.performanceSummary.sortino_ratio)}
                                  </span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-gray-300">손익 비율</span>
                                  <span className="text-gray-100 font-semibold">
                                    {formatNumber(backtestResults.performanceSummary.profit_factor)}
                                  </span>
                                </div>
                              </div>
                            </div>

                            <div className="bg-gray-700 rounded-xl p-6">
                              <h3 className="text-lg font-bold text-gray-100 mb-4">위험 지표</h3>
                              <div className="space-y-3">
                                <div className="flex justify-between">
                                  <span className="text-gray-300">VaR (95%)</span>
                                  <span className="text-red-400 font-semibold">
                                    {formatPercentage(backtestResults.performanceSummary.var_95)}
                                  </span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-gray-300 text-sm">손실 확률</span>
                                  <span className="text-yellow-400 font-semibold">
                                    {formatPercentage(1 - backtestResults.performanceSummary.win_rate)}
                                  </span>
                                </div>
                              </div>
                            </div>

                            <div className="bg-gray-700 rounded-xl p-6">
                              <div className="flex items-center space-x-2 mb-3">
                                <Target className="w-5 h-5 text-purple-400" />
                                <h3 className="text-lg font-bold text-gray-100">거래 성과</h3>
                              </div>
                              <div className="space-y-3">
                                <div className="flex justify-between">
                                  <span className="text-gray-300 text-sm">승률</span>
                                  <span className="text-green-400 font-semibold">
                                    {formatPercentage(backtestResults.performanceSummary.win_rate)}
                                  </span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-gray-300 text-sm">손익 비율</span>
                                  <span className="text-gray-100 font-semibold">
                                    {formatNumber(backtestResults.performanceSummary.profit_factor)}
                                  </span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-gray-300 text-sm">총 거래 수</span>
                                  <span className="text-gray-100 font-semibold">
                                    {backtestResults.performanceSummary.total_trades}
                                  </span>
                                </div>
                              </div>
                            </div>
                          </div>

                          {/* 월별 수익률 히트맵 */}
                          <div className="bg-gray-700 rounded-xl p-6">
                            <h3 className="text-lg font-bold text-gray-100 mb-4">월별 수익률 분포</h3>
                            <div className="grid grid-cols-12 gap-1">
                              {Array.from({ length: 60 }, (_, i) => {
                                const return_val = (Math.random() - 0.5) * 0.08;
                                const intensity = Math.abs(return_val) * 10;
                                const color = return_val > 0 ? 
                                  `rgba(16, 185, 129, ${Math.min(intensity, 1)})` : 
                                  `rgba(239, 68, 68, ${Math.min(intensity, 1)})`;
                                
                                return (
                                  <div
                                    key={i}
                                    className="aspect-square rounded-sm flex items-center justify-center text-xs font-semibold"
                                    style={{ backgroundColor: color }}
                                    title={`${formatPercentage(return_val)} 수익률`}
                                  >
                                    {Math.abs(return_val * 100) > 3 ? 
                                      (return_val > 0 ? '+' : '-') : ''
                                    }
                                  </div>
                                );
                              })}
                            </div>
                            <div className="flex justify-between mt-4 text-xs text-gray-400">
                              <span>2020</span>
                              <span>2021</span>
                              <span>2022</span>
                              <span>2023</span>
                              <span>2024</span>
                            </div>
                          </div>
                        </motion.div>
                      )}

                      {selectedTab === 'portfolio' && (
                        <motion.div
                          key="portfolio"
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -20 }}
                          className="space-y-6"
                        >
                          {/* 전략 구성 */}
                          <div className="bg-gray-700 rounded-xl p-6">
                            <h3 className="text-lg font-bold text-gray-100 mb-4 flex items-center">
                              <PieChartIcon className="w-5 h-5 mr-2 text-blue-400" />
                              전략 구성 비중
                            </h3>
                            
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                              <div className="h-64">
                                <ResponsiveContainer width="100%" height="100%">
                                  <PieChart>
                                    <Pie
                                      data={strategyWeightData}
                                      cx="50%"
                                      cy="50%"
                                      outerRadius={80}
                                      dataKey="weight"
                                      label={(entry) => `${entry.name}: ${entry.weight.toFixed(1)}%`}
                                    >
                                      {strategyWeightData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                      ))}
                                    </Pie>
                                    <Tooltip 
                                      contentStyle={{
                                        backgroundColor: '#374151',
                                        border: '1px solid #4b5563',
                                        borderRadius: '8px',
                                        color: '#f9fafb'
                                      }}
                                    />
                                  </PieChart>
                                </ResponsiveContainer>
                              </div>
                              
                              <div className="space-y-3">
                                {backtestResults.strategyConfig.strategies.map((strategy, index) => (
                                  <div key={strategy.name} className="flex items-center justify-between bg-gray-800 rounded-lg p-3">
                                    <div className="flex items-center space-x-3">
                                      <div 
                                        className="w-4 h-4 rounded-full"
                                        style={{ backgroundColor: COLORS[index % COLORS.length] }}
                                      ></div>
                                      <div>
                                        <p className="text-gray-100 font-semibold text-sm">{strategy.name}</p>
                                        <p className="text-gray-400 text-xs">{strategy.category}</p>
                                      </div>
                                    </div>
                                    <span className="text-gray-100 font-semibold">
                                      {formatPercentage(strategy.weight)}
                                    </span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </div>

                          {/* 포트폴리오 가치 변화 */}
                          <div className="bg-gray-700 rounded-xl p-6">
                            <h3 className="text-lg font-bold text-gray-100 mb-4 flex items-center">
                              <DollarSign className="w-5 h-5 mr-2 text-green-400" />
                              포트폴리오 가치 변화
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
                                    tickFormatter={(value) => formatCurrency(value)}
                                  />
                                  <Tooltip 
                                    contentStyle={{
                                      backgroundColor: '#374151',
                                      border: '1px solid #4b5563',
                                      borderRadius: '8px',
                                      color: '#f9fafb'
                                    }}
                                    formatter={(value: any) => [formatCurrency(value), '포트폴리오 가치']}
                                  />
                                  <Line 
                                    type="monotone" 
                                    dataKey="value" 
                                    stroke="#10b981" 
                                    strokeWidth={3}
                                    dot={false}
                                  />
                                </LineChart>
                              </ResponsiveContainer>
                            </div>
                          </div>
                        </motion.div>
                      )}

                      {selectedTab === 'trades' && (
                        <motion.div
                          key="trades"
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -20 }}
                          className="space-y-6"
                        >
                          {/* 거래 통계 */}
                          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                            <div className="bg-gray-700 rounded-xl p-6 text-center">
                              <div className="text-3xl font-bold text-gray-100 mb-2">
              
              
              
              
       
                                {backtestResults.performanceSummary.total_trades}
                              </div>
                              <p className="text-gray-300 text-sm">총 거래 횟수</p>
                            </div>
                            <div className="bg-gray-700 rounded-xl p-6 text-center">
                              <div className="text-3xl font-bold text-green-400 mb-2">
                                {Math.round(backtestResults.performanceSummary.total_trades * backtestResults.performanceSummary.win_rate)}
                              </div>
                              <p className="text-gray-300 text-sm">성공 거래</p>
                            </div>
                            <div className="bg-gray-700 rounded-xl p-6 text-center">
                              <div className="text-3xl font-bold text-red-400 mb-2">
                                {backtestResults.performanceSummary.total_trades - Math.round(backtestResults.performanceSummary.total_trades * backtestResults.performanceSummary.win_rate)}
                              </div>
                              <p className="text-gray-300 text-sm">손실 거래</p>
                            </div>
                          </div>

                          {/* 최근 거래 내역 */}
                          <div className="bg-gray-700 rounded-xl p-6">
                            <div className="flex items-center justify-between mb-4">
                              <h3 className="text-lg font-bold text-gray-100 flex items-center">
                                <Activity className="w-5 h-5 mr-2 text-purple-400" />
                                최근 거래 내역
                              </h3>
                            </div>
                            
                            <div className="overflow-hidden">
                              <div className="max-h-96 overflow-y-auto">
                                <div className="space-y-2">
                                  {backtestResults.tradeHistory
                                    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
                                    .slice(0, 20)
                                    .map((trade, index) => (
                                    <motion.div
                                      key={index}
                                      initial={{ opacity: 0, x: -20 }}
                                      animate={{ opacity: 1, x: 0 }}
                                      transition={{ delay: index * 0.05 }}
                                      className="bg-gray-800 rounded-lg p-4 flex items-center justify-between"
                                    >
                                      <div className="flex items-center space-x-4">
                                        <div className={`px-2 py-1 rounded text-xs font-semibold ${
                                          trade.action === 'buy' ? 'bg-green-600 text-green-100' : 'bg-red-600 text-red-100'
                                        }`}>
                                          {trade.action.toUpperCase()}
                                        </div>
                                        <div>
                                          <p className="text-gray-100 font-semibold">{trade.symbol}</p>
                                          <p className="text-gray-400 text-xs">{trade.date}</p>
                                        </div>
                                        <div className="text-right">
                                          <p className="text-gray-100">{trade.shares}주</p>
                                          <p className="text-gray-400 text-xs">${trade.price.toFixed(2)}</p>
                                        </div>
                                      </div>
                                      <div className="text-right">
                                        <p className="text-gray-100 font-semibold">{formatCurrency(trade.total_value)}</p>
                                        <p className="text-gray-400 text-xs">{trade.reason}</p>
                                      </div>
                                    </motion.div>
                                  ))}
                                </div>
                              </div>
                            </div>
                          </div>
                        </motion.div>
                      )}

                      {selectedTab === 'risk' && (
                        <motion.div
                          key="risk"
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -20 }}
                          className="space-y-6"
                        >
                          {/* 위험 메트릭스 */}
                          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            <div className="bg-gray-700 rounded-xl p-6">
                              <div className="flex items-center space-x-2 mb-3">
                                <Shield className="w-5 h-5 text-yellow-400" />
                                <h3 className="text-lg font-bold text-gray-100">위험 조정 수익률</h3>
                              </div>
                              <div className="space-y-3">
                                <div className="flex justify-between">
                                  <span className="text-gray-300 text-sm">샤프 비율</span>
                                  <span className="text-gray-100 font-semibold">
                                    {formatNumber(backtestResults.performanceSummary.sharpe_ratio)}
                                  </span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-gray-300 text-sm">소티노 비율</span>
                                  <span className="text-gray-100 font-semibold">
                                    {formatNumber(backtestResults.performanceSummary.sortino_ratio)}
                                  </span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-gray-300 text-sm">칼마 비율</span>
                                  <span className="text-gray-100 font-semibold">
                                    {formatNumber(backtestResults.performanceSummary.calmar_ratio)}
                                  </span>
                                </div>
                              </div>
                            </div>

                            <div className="bg-gray-700 rounded-xl p-6">
                              <div className="flex items-center space-x-2 mb-3">
                                <TrendingDown className="w-5 h-5 text-red-400" />
                                <h3 className="text-lg font-bold text-gray-100">하방 위험</h3>
                              </div>
                              <div className="space-y-3">
                                <div className="flex justify-between">
                                  <span className="text-gray-300 text-sm">최대 낙폭</span>
                                  <span className="text-red-400 font-semibold">
                                    {formatPercentage(backtestResults.performanceSummary.max_drawdown)}
                                  </span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-gray-300 text-sm">VaR (95%)</span>
                                  <span className="text-red-400 font-semibold">
                                    {formatPercentage(backtestResults.performanceSummary.var_95)}
                                  </span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-gray-300 text-sm">연간 변동성</span>
                                  <span className="text-yellow-400 font-semibold">
                                    {formatPercentage(backtestResults.performanceSummary.annual_volatility)}
                                  </span>
                                </div>
                              </div>
                            </div>

                            <div className="bg-gray-700 rounded-xl p-6">
                              <div className="flex items-center space-x-2 mb-3">
                                <Activity className="w-5 h-5 text-purple-400" />
                                <h3 className="text-lg font-bold text-gray-100">위험 분석</h3>
                              </div>
                              <div className="space-y-3">
                                <div className="flex justify-between">
                                  <span className="text-gray-300 text-sm">베타</span>
                                  <span className="text-gray-100 font-semibold">0.85</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-gray-300 text-sm">트래킹 에러</span>
                                  <span className="text-gray-100 font-semibold">4.2%</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-gray-300 text-sm">정보 비율</span>
                                  <span className="text-gray-100 font-semibold">0.68</span>
                                </div>
                              </div>
                            </div>
                          </div>

                          {/* 리스크 차트 */}
                          <div className="bg-gray-700 rounded-xl p-6">
                            <h3 className="text-lg font-bold text-gray-100 mb-4 flex items-center">
                              <Shield className="w-5 h-5 mr-2 text-red-400" />
                              위험 분석 차트
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
                                    tickFormatter={(value) => `${value.toFixed(0)}%`}
                                  />
                                  <Tooltip 
                                    contentStyle={{
                                      backgroundColor: '#374151',
                                      border: '1px solid #4b5563',
                                      borderRadius: '8px',
                                      color: '#f9fafb'
                                    }}
                                    formatter={(value: any) => [`${value.toFixed(2)}%`, 'Drawdown']}
                                  />
                                  <Line 
                                    type="monotone" 
                                    dataKey="return" 
                                    stroke="#ef4444" 
                                    strokeWidth={2}
                                    dot={false}
                                    name="Drawdown"
                                  />
                                </LineChart>
                              </ResponsiveContainer>
                            </div>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                </div>

                {/* 액션 버튼들 */}
                <div className="flex flex-col sm:flex-row gap-4 mt-6">
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={downloadReport}
                    className="flex-1 bg-blue-600 hover:bg-blue-500 text-white font-semibold py-3 px-6 rounded-xl transition-all flex items-center justify-center space-x-2"
                  >
                    <Download className="w-4 h-4" />
                    <span>전체 리포트 다운로드</span>
                  </motion.button>
                  
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={showDetailedAnalysis}
                    className="flex-1 bg-gray-600 hover:bg-gray-500 text-gray-100 font-semibold py-3 px-6 rounded-xl transition-all flex items-center justify-center space-x-2"
                  >
                    <Eye className="w-4 h-4" />
                    <span>상세 분석 보기</span>
                  </motion.button>
                </div>
              </div>
            ) : (
              /* 초기 상태 - 백테스트 실행 전 */
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="bg-gray-800 rounded-2xl border border-gray-700 p-12 text-center"
              >
                <div className="w-16 h-16 bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4 text-gray-400">
                  <BarChart3 className="w-8 h-8" />
                </div>
                <h3 className="text-xl font-semibold text-gray-100 mb-2">퀀트 전략 백테스트 준비 완료</h3>
                <p className="text-gray-400 mb-6">
                  왼쪽에서 투자 설정과 전략을 구성한 후 백테스트를 실행하세요
                  <br />
                  다양한 전략 조합으로 최적의 포트폴리오를 찾아보세요
                </p>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-gray-700 rounded-lg p-4 text-center">
                    <div className="text-2xl mb-2">💰</div>
                    <p className="text-gray-100 font-semibold">투자 설정</p>
                    <p className="text-gray-400 text-sm">금액, 기간, 리밸런싱</p>
                  </div>
                  <div className="bg-gray-700 rounded-lg p-4 text-center">
                    <div className="text-2xl mb-2">🎯</div>
                    <p className="text-gray-100 font-semibold">전략 조합</p>
                    <p className="text-gray-400 text-sm">기술적+재무적 분석</p>
                  </div>
                  <div className="bg-gray-700 rounded-lg p-4 text-center">
                    <div className="text-2xl mb-2">📊</div>
                    <p className="text-gray-100 font-semibold">성과 분석</p>
                    <p className="text-gray-400 text-sm">리스크 및 수익률</p>
                  </div>
                </div>
              </motion.div>
            )}
          </div>
        </div>

        {/* 파라미터 설정 모달 */}
        <AnimatePresence>
          {showParameterModal && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
              onClick={() => setShowParameterModal(null)}
            >
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                onClick={(e) => e.stopPropagation()}
                className="bg-gray-800 rounded-2xl border border-gray-700 p-6 max-w-md w-full max-h-96 overflow-y-auto"
              >
                <h3 className="text-lg font-bold text-gray-100 mb-4">
                  {showParameterModal} 전략 파라미터
                </h3>
                
                {(() => {
                  const strategyIndex = selectedStrategies.findIndex(s => s.name === showParameterModal);
                  if (strategyIndex === -1) return null;
                  
                  const strategy = selectedStrategies[strategyIndex];
                  
                  return (
                    <div className="space-y-4">
                      {Object.entries(strategy.parameters).map(([key, value]) => (
                        <div key={key}>
                          <label className="block text-gray-300 text-sm font-medium mb-1">
                            {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </label>
                          <input
                            type="number"
                            value={value}
                            onChange={(e) => {
                              const newParams = { ...strategy.parameters };
                              newParams[key] = Number(e.target.value);
                              updateStrategyParameters(strategyIndex, newParams);
                            }}
                            className="w-full p-2 bg-gray-700 border border-gray-600 rounded text-gray-100 text-sm focus:outline-none focus:border-blue-400"
                            step={typeof value === 'number' && value < 1 ? "0.01" : "1"}
                          />
                        </div>
                      ))}
                      
                      <div className="flex space-x-3 mt-6">
                        <button
                          onClick={() => setShowParameterModal(null)}
                          className="flex-1 bg-gray-600 hover:bg-gray-500 text-gray-100 font-semibold py-2 px-4 rounded-lg transition-all"
                        >
                          닫기
                        </button>
                      </div>
                    </div>
                  );
                })()}
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <footer className="bg-gray-800 border-t border-gray-700 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center space-x-3 mb-4 md:mb-0">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white">
                <BarChart3 />
              </div>
              <div>
                <p className="text-gray-100 font-semibold">Quant Strategy MVP</p>
                <p className="text-gray-400 text-sm">퀀트 전략 백테스팅 시스템</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-6 text-sm text-gray-400">
              <p>📈 기술적 + 재무 분석</p>
              <p>⚡ 실시간 백테스트</p>
              <p>🎯 전략 조합</p>
              <p>🔍 성과 분석</p>
            </div>
          </div>
          
          <div className="border-t border-gray-700 mt-6 pt-6 text-center">
            <p className="text-gray-500 text-sm">
              © 2025 Quant Strategy MVP. 백테스트 결과는 과거 데이터 기반 시뮬레이션이며, 
              미래 수익을 보장하지 않습니다. 투자 결정 시 신중하게 검토하시기 바랍니다.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
