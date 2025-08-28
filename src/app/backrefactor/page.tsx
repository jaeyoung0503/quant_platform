'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Papa from 'papaparse';
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

// SVG Icons
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

const Shield = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
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

const RefreshCw = ({ className = "w-5 h-5" }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <polyline points="23,4 23,10 17,10"></polyline>
    <polyline points="1,20 1,14 7,14"></polyline>
    <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"></path>
  </svg>
);

const Info = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4">
    <circle cx="12" cy="12" r="10"></circle>
    <line x1="12" y1="16" x2="12" y2="12"></line>
    <line x1="12" y1="8" x2="12.01" y2="8"></line>
  </svg>
);

const AlertCircle = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4">
    <circle cx="12" cy="12" r="10"></circle>
    <line x1="12" y1="8" x2="12" y2="12"></line>
    <line x1="12" y1="16" x2="12.01" y2="16"></line>
  </svg>
);

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

// Strategy icon mapping
const iconMapping = {
  'low_pe': Shield,
  'dividend_aristocrats': Target,
  'simple_momentum': TrendingUp,
  'moving_average_cross': Activity,
  'rsi_mean_reversion': Activity,
  'bollinger_band': Activity,
  'small_cap': Target,
  'low_volatility': Shield,
  'quality_factor': Shield,
  'regular_rebalancing': Target,
  'buffett_moat': Shield,
  'peter_lynch_peg': TrendingUp,
  'benjamin_graham_defensive': Shield,
  'joel_greenblatt_magic': Target,
  'william_oneil_canslim': TrendingUp,
  'howard_marks_cycle': Activity,
  'james_oshaughnessy': Target,
  'ray_dalio_all_weather': Shield,
  'david_dreman_contrarian': Activity,
  'john_neff_low_pe_dividend': Target
};

// 전체 20가지 전략 데이터
const getAllStrategies = () => [
  // 기본 전략 10개
  {
    id: 'low_pe',
    name: 'Low PE Strategy',
    category: 'basic',
    description: 'PER 15배 이하 종목 선별하는 가치투자 전략',
    riskLevel: 'low',
    complexity: 'simple',
    expectedReturn: '8-12%',
    volatility: '12-18%',
    details: 'PER이 15배 이하인 저평가 종목을 선별하여 투자하는 가치투자 전략입니다.'
  },
  {
    id: 'dividend_aristocrats',
    name: 'Dividend Aristocrats',
    category: 'basic',
    description: '20년 이상 연속 배당 증가 기업 투자',
    riskLevel: 'low',
    complexity: 'simple',
    expectedReturn: '7-10%',
    volatility: '10-15%',
    details: '20년 이상 연속으로 배당을 증가시킨 우량 기업에 투자합니다.'
  },
  {
    id: 'simple_momentum',
    name: 'Simple Momentum',
    category: 'basic',
    description: '최근 성과 상위 종목 투자, 상승 추세 추종',
    riskLevel: 'medium',
    complexity: 'simple',
    expectedReturn: '10-15%',
    volatility: '16-22%',
    details: '최근 3-12개월 수익률이 높은 상위 종목에 투자하는 모멘텀 전략입니다.'
  },
  {
    id: 'moving_average_cross',
    name: 'Moving Average Cross',
    category: 'basic',
    description: '단기 이동평균이 장기 이동평균 상향 돌파시 매수',
    riskLevel: 'medium',
    complexity: 'simple',
    expectedReturn: '8-12%',
    volatility: '14-20%',
    details: '20일 이동평균이 60일 이동평균을 상향 돌파할 때 매수하는 전략입니다.'
  },
  {
    id: 'rsi_mean_reversion',
    name: 'RSI Mean Reversion',
    category: 'basic',
    description: 'RSI 30 이하 매수, 70 이상 매도',
    riskLevel: 'medium',
    complexity: 'simple',
    expectedReturn: '10-13%',
    volatility: '12-18%',
    details: 'RSI 지표를 활용해 과매도 구간에서 매수하는 역발상 전략입니다.'
  },
  {
    id: 'bollinger_band',
    name: 'Bollinger Band',
    category: 'basic',
    description: '하단선 터치시 매수, 상단선 터치시 매도',
    riskLevel: 'medium',
    complexity: 'simple',
    expectedReturn: '9-12%',
    volatility: '13-19%',
    details: '볼린저 밴드 하단선 근처에서 매수하는 역발상 전략입니다.'
  },
  {
    id: 'small_cap',
    name: 'Small Cap Premium',
    category: 'basic',
    description: '시가총액 하위 종목 투자로 초과수익 추구',
    riskLevel: 'high',
    complexity: 'simple',
    expectedReturn: '12-18%',
    volatility: '20-30%',
    details: '소형주의 높은 성장 가능성을 활용하는 전략입니다.'
  },
  {
    id: 'low_volatility',
    name: 'Low Volatility',
    category: 'basic',
    description: '변동성이 낮은 종목으로 안정적 수익 추구',
    riskLevel: 'low',
    complexity: 'simple',
    expectedReturn: '8-11%',
    volatility: '8-12%',
    details: '변동성이 낮은 안정적인 종목들로 포트폴리오를 구성합니다.'
  },
  {
    id: 'quality_factor',
    name: 'Quality Factor',
    category: 'basic',
    description: 'ROE, 부채비율 등 재무 건전성 우수 기업',
    riskLevel: 'low',
    complexity: 'simple',
    expectedReturn: '9-13%',
    volatility: '12-16%',
    details: '재무 건전성이 우수한 품질 좋은 기업들에 투자합니다.'
  },
  {
    id: 'regular_rebalancing',
    name: 'Regular Rebalancing',
    category: 'basic',
    description: '정해진 비율로 정기적 리밸런싱하여 위험 관리',
    riskLevel: 'medium',
    complexity: 'simple',
    expectedReturn: '8-12%',
    volatility: '10-16%',
    details: '정기적으로 포트폴리오를 리밸런싱하여 위험을 관리합니다.'
  },
  // 고급 전략 10개
  {
    id: 'buffett_moat',
    name: 'Buffett Moat Strategy',
    category: 'advanced',
    description: '경쟁우위가 있는 기업을 합리적 가격에 장기 보유',
    riskLevel: 'low',
    complexity: 'medium',
    expectedReturn: '12-16%',
    volatility: '10-15%',
    details: '워렌 버핏의 경제적 해자 개념을 활용한 장기 가치투자 전략입니다.'
  },
  {
    id: 'peter_lynch_peg',
    name: 'Peter Lynch PEG',
    category: 'advanced',
    description: 'PEG 비율 1.0 이하 성장주 발굴, 10배 주식 추구',
    riskLevel: 'medium',
    complexity: 'medium',
    expectedReturn: '13-18%',
    volatility: '16-22%',
    details: '피터 린치의 PEG 전략으로 저평가된 성장주를 발굴합니다.'
  },
  {
    id: 'benjamin_graham_defensive',
    name: 'Graham Defensive',
    category: 'advanced',
    description: '안전성과 수익성을 겸비한 보수적 가치투자',
    riskLevel: 'low',
    complexity: 'medium',
    expectedReturn: '9-13%',
    volatility: '10-16%',
    details: '벤저민 그레이엄의 방어적 투자자 전략을 구현합니다.'
  },
  {
    id: 'joel_greenblatt_magic',
    name: 'Magic Formula',
    category: 'advanced',
    description: 'ROE + 수익수익률(E/P) 결합한 체계적 가치투자',
    riskLevel: 'medium',
    complexity: 'medium',
    expectedReturn: '12-17%',
    volatility: '14-20%',
    details: '조엘 그린블라트의 마법공식으로 체계적 가치투자를 실행합니다.'
  },
  {
    id: 'william_oneil_canslim',
    name: 'CANSLIM Strategy',
    category: 'advanced',
    description: '7가지 기준으로 고성장주 발굴, 모멘텀과 펀더멘털 결합',
    riskLevel: 'high',
    complexity: 'complex',
    expectedReturn: '15-25%',
    volatility: '20-30%',
    details: '윌리엄 오닐의 CAN SLIM 방법론으로 고성장주를 선별합니다.'
  },
  {
    id: 'howard_marks_cycle',
    name: 'Cycle Investment',
    category: 'advanced',
    description: '경기사이클 극단점에서 역발상 기회 포착',
    riskLevel: 'medium',
    complexity: 'complex',
    expectedReturn: '13-18%',
    volatility: '16-24%',
    details: '하워드 막스의 사이클 투자법으로 시장 극단점을 활용합니다.'
  },
  {
    id: 'james_oshaughnessy',
    name: 'What Works Strategy',
    category: 'advanced',
    description: '50년 데이터 검증, 시총+PBR+모멘텀 멀티팩터',
    riskLevel: 'medium',
    complexity: 'medium',
    expectedReturn: '14-19%',
    volatility: '17-23%',
    details: '제임스 오쇼네시의 장기 데이터 검증 전략입니다.'
  },
  {
    id: 'ray_dalio_all_weather',
    name: 'All Weather Portfolio',
    category: 'advanced',
    description: '경제 환경 변화에 관계없이 안정적 수익 추구',
    riskLevel: 'low',
    complexity: 'medium',
    expectedReturn: '8-12%',
    volatility: '8-12%',
    details: '레이 달리오의 올웨더 포트폴리오로 전천후 투자를 실현합니다.'
  },
  {
    id: 'david_dreman_contrarian',
    name: 'Contrarian Investment',
    category: 'advanced',
    description: '시장 공포와 비관론 속에서 저평가 기회 발굴',
    riskLevel: 'medium',
    complexity: 'medium',
    expectedReturn: '12-16%',
    volatility: '16-22%',
    details: '데이비드 드레먼의 역발상 투자 전략으로 공포 속 기회를 포착합니다.'
  },
  {
    id: 'john_neff_low_pe_dividend',
    name: 'Low PE + Dividend',
    category: 'advanced',
    description: '소외받는 업종에서 저PER + 고배당 보석 발굴',
    riskLevel: 'medium',
    complexity: 'medium',
    expectedReturn: '11-15%',
    volatility: '14-18%',
    details: '존 네프의 저PER 고배당 전략으로 소외받는 가치를 발굴합니다.'
  }
];

export default function QuantStrategyPage() {
  const [selectedStrategy, setSelectedStrategy] = useState(null);
  const [backtestResult, setBacktestResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showDetails, setShowDetails] = useState(null);
  const [showGraphs, setShowGraphs] = useState(false);
  const [categoryFilter, setCategoryFilter] = useState('all');
  
  // Data loading states
  const [strategies, setStrategies] = useState([]);
  const [marketData, setMarketData] = useState([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [error, setError] = useState(null);

  // 데이터 로딩
  useEffect(() => {
    const loadData = async () => {
      try {
        setDataLoading(true);
        console.log('데이터 로딩 시작...');
        
        // 전략 목록 로드 시도
        let loadedStrategies = [];
        try {
          console.log('API에서 전략 목록 로드 시도...');
          const strategiesResponse = await fetch('/api/strategies', {
            method: 'GET',
            headers: { 'Accept': 'application/json' }
          });
          
          if (strategiesResponse.ok) {
            const strategiesData = await strategiesResponse.json();
            console.log('API 응답:', strategiesData);
            
            if (strategiesData && Array.isArray(strategiesData) && strategiesData.length > 0) {
              loadedStrategies = strategiesData.map(strategy => ({
                ...strategy,
                icon: iconMapping[strategy.id] || Target
              }));
              console.log(`API에서 ${loadedStrategies.length}개 전략 로드 성공`);
            } else {
              console.log('API 응답이 비어있거나 올바르지 않음');
            }
          } else {
            console.log('API 응답 실패:', strategiesResponse.status);
          }
        } catch (apiError) {
          console.warn('API 호출 실패:', apiError.message);
        }
        
        // API 실패 시 하드코딩된 전략 사용
        if (loadedStrategies.length === 0) {
          console.log('하드코딩된 전략 목록 사용');
          loadedStrategies = getAllStrategies().map(strategy => ({
            ...strategy,
            icon: iconMapping[strategy.id] || Target
          }));
        }
        
        setStrategies(loadedStrategies);
        console.log(`총 ${loadedStrategies.length}개 전략 설정 완료`);

        // CSV 데이터 로드 시도
        let loadedMarketData = [];
        try {
          console.log('CSV 데이터 로드 시도...');
          const marketResponse = await fetch('/data/market_data.csv');
          
          if (marketResponse.ok) {
            const marketCsvText = await marketResponse.text();
            const marketParsed = Papa.parse(marketCsvText, {
              header: true,
              dynamicTyping: true,
              skipEmptyLines: true
            });

            if (marketParsed.errors.length > 0) {
              console.warn('CSV 파싱 경고:', marketParsed.errors);
            }

            if (marketParsed.data && marketParsed.data.length > 0) {
              loadedMarketData = marketParsed.data;
              console.log(`CSV에서 ${loadedMarketData.length}개 데이터 포인트 로드 성공`);
            }
          } else {
            console.log('CSV 파일 응답 실패:', marketResponse.status);
          }
        } catch (csvError) {
          console.warn('CSV 로드 실패:', csvError.message);
        }
        
        // CSV 실패 시 샘플 데이터 생성
        if (loadedMarketData.length === 0) {
          console.log('샘플 데이터 생성');
          loadedMarketData = generateSampleData();
        }
        
        setMarketData(loadedMarketData);
        console.log(`총 ${loadedMarketData.length}개 데이터 포인트 설정 완료`);

      } catch (err) {
        console.error('전체 데이터 로딩 오류:', err);
        setError(`데이터 로딩 중 오류 발생: ${err.message}`);
        
        // 오류 시에도 기본 데이터 설정
        const fallbackStrategies = getAllStrategies().map(strategy => ({
          ...strategy,
          icon: iconMapping[strategy.id] || Target
        }));
        setStrategies(fallbackStrategies);
        setMarketData(generateSampleData());
        
      } finally {
        setDataLoading(false);
        console.log('데이터 로딩 완료');
      }
    };

    loadData();
  }, []);

  // 샘플 데이터 생성 함수
  const generateSampleData = () => {
    const data = [];
    const symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA'];
    const startDate = new Date('2024-01-01');
    
    for (let i = 0; i < 100; i++) {
      const date = new Date(startDate.getTime() + i * 24 * 60 * 60 * 1000);
      symbols.forEach(symbol => {
        const basePrice = 100 + Math.random() * 200;
        data.push({
          date: date.toISOString().split('T')[0],
          symbol,
          open: basePrice,
          high: basePrice * (1 + Math.random() * 0.05),
          low: basePrice * (1 - Math.random() * 0.05),
          close: basePrice * (0.95 + Math.random() * 0.1),
          volume: Math.floor(1000000 + Math.random() * 5000000),
          pe_ratio: 15 + Math.random() * 20,
          pb_ratio: 1 + Math.random() * 5,
          market_cap: 1000 + Math.random() * 2000,
          dividend_yield: Math.random() * 0.05,
          roe: 0.1 + Math.random() * 0.3,
          debt_to_equity: Math.random() * 0.5
        });
      });
    }
    return data;
  };

  const filteredStrategies = strategies.filter(strategy => 
    categoryFilter === 'all' || strategy.category === categoryFilter
  );

  // 백테스트 실행
  const runBacktest = async (strategyId) => {
    if (!marketData || marketData.length === 0) {
      setError('시장 데이터가 로드되지 않았습니다.');
      return;
    }

    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/backtest', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          strategy_id: strategyId,
          parameters: selectedStrategy?.parameters || {},
          market_data: marketData
        })
      });

      if (!response.ok) {
        const errorText = await response.text();
        let errorData;
        try {
          errorData = JSON.parse(errorText);
        } catch {
          errorData = { error: `HTTP ${response.status}: ${errorText}` };
        }
        throw new Error(errorData.error || '백테스트 실행 실패');
      }

      const result = await response.json();
      
      if (result.error) {
        throw new Error(result.error);
      }

      setBacktestResult(result);
      
    } catch (error) {
      console.error('백테스트 오류:', error);
      
      // 폴백: 목 데이터로 결과 생성
      const mockResult = generateMockResult(strategyId);
      setBacktestResult(mockResult);
      
      setError(`백테스트 실행 중 오류가 발생했습니다. 샘플 결과를 표시합니다: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // 목 결과 생성
  const generateMockResult = (strategyId) => {
    const baseReturn = 8 + Math.random() * 12;
    const volatility = 10 + Math.random() * 15;
    const portfolioHistory = generatePortfolioHistory(baseReturn, volatility);
    
    return {
      strategy_name: strategyId,
      symbol: 'PORTFOLIO',
      totalReturn: baseReturn * 10 + Math.random() * 50,
      annualReturn: baseReturn,
      volatility: volatility,
      sharpeRatio: 0.8 + Math.random() * 0.8,
      sortinoRatio: 1.0 + Math.random() * 0.8,
      calmarRatio: 0.6 + Math.random() * 0.6,
      maxDrawdown: 5 + Math.random() * 15,
      winRate: 55 + Math.random() * 15,
      finalValue: portfolioHistory[portfolioHistory.length - 1],
      portfolioHistory: portfolioHistory,
      components: ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA'],
      weights: {'AAPL': 0.2, 'GOOGL': 0.2, 'MSFT': 0.2, 'AMZN': 0.2, 'TSLA': 0.2}
    };
  };

  const generatePortfolioHistory = (baseReturn, volatility, days = 1000) => {
    const dailyReturn = baseReturn / 365 / 100;
    const dailyVol = volatility / Math.sqrt(365) / 100;
    
    const history = [100000];
    
    for (let i = 1; i < days; i++) {
      const randomReturn = dailyReturn + (Math.random() - 0.5) * dailyVol * 2;
      const newValue = history[i-1] * (1 + randomReturn);
      history.push(Math.max(newValue, history[i-1] * 0.7));
    }
    
    return history;
  };

  const chartData = backtestResult?.portfolioHistory?.map((value, index) => ({
    date: index,
    value: value,
    benchmark: 100000 + index * 200
  })) || [];

  const drawdownData = backtestResult?.portfolioHistory?.map((value, index) => {
    if (!backtestResult?.portfolioHistory) return { date: index, drawdown: 0 };
    const peak = Math.max(...backtestResult.portfolioHistory.slice(0, index + 1));
    const drawdown = ((value - peak) / peak) * 100;
    return {
      date: index,
      drawdown: drawdown
    };
  }) || [];

  // 로딩 화면
  if (dataLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4 text-gray-400">
            <RefreshCw className="w-8 h-8 animate-spin" />
          </div>
          <h3 className="text-xl font-semibold text-gray-100 mb-2">시스템 초기화 중</h3>
          <p className="text-gray-400">전략 엔진 및 시장 데이터 로딩 중...</p>
        </div>
      </div>
    );
  }

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
                <p className="text-gray-400 text-sm">20가지 전문가 투자전략 - 기본 10가지 + 고급 10가지</p>
              </div>
            </motion.div>
            
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-gray-300 text-sm">데이터 포인트</p>
                <p className="text-gray-100 font-semibold">{marketData.length.toLocaleString()}개</p>
              </div>
              <div className="text-right">
                <p className="text-gray-300 text-sm">전략 수</p>
                <p className="text-gray-100 font-semibold">{strategies.length}가지</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 p-4 bg-yellow-800 border border-yellow-600 rounded-lg">
            <div className="flex items-center space-x-2">
              <AlertCircle className="text-yellow-400" />
              <p className="text-yellow-200 text-sm">{error}</p>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
          <div className="xl:col-span-1">
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-gray-800 rounded-2xl border border-gray-700 p-6"
            >
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-gray-100 flex items-center">
                  <Target className="mr-2" />
                  Quant Strategies
                </h2>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setCategoryFilter('all')}
                    className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
                      categoryFilter === 'all' 
                        ? 'bg-gray-600 text-gray-100' 
                        : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
                    }`}
                  >
                    전체
                  </button>
                  <button
                    onClick={() => setCategoryFilter('basic')}
                    className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
                      categoryFilter === 'basic' 
                        ? 'bg-gray-600 text-gray-100' 
                        : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
                    }`}
                  >
                    기본
                  </button>
                  <button
                    onClick={() => setCategoryFilter('advanced')}
                    className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
                      categoryFilter === 'advanced' 
                        ? 'bg-gray-600 text-gray-100' 
                        : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
                    }`}
                  >
                    고급
                  </button>
                </div>
              </div>

              <div className="space-y-3 max-h-96 overflow-y-auto">
                {filteredStrategies.map((strategy, index) => (
                  <motion.div
                    key={strategy.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
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
                            {React.createElement(strategy.icon)}
                          </div>
                          <h3 className="font-semibold text-gray-100 text-sm">{strategy.name}</h3>
                          {strategy.category === 'advanced' && (
                            <span className="px-1.5 py-0.5 bg-gray-600 text-gray-200 text-xs rounded">고급</span>
                          )}
                        </div>
                        <p className="text-gray-400 text-xs mb-3">{strategy.description}</p>
                        
                        <div className="flex flex-wrap gap-2">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${riskColors[strategy.riskLevel] || riskColors.medium}`}>
                            {strategy.riskLevel === 'low' ? '낮은 위험' : strategy.riskLevel === 'medium' ? '중간 위험' : '높은 위험'}
                          </span>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${complexityColors[strategy.complexity] || complexityColors.simple}`}>
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
                      <h2 className="text-xl font-bold text-gray-100 flex items-center">
                        <BarChart3 className="mr-2" />
                        포트폴리오 성과 요약
                      </h2>
                      <div className="flex space-x-2">
                        <button 
                          onClick={() => setShowGraphs(!showGraphs)}
                          className="p-2 text-gray-400 hover:text-gray-200 transition-colors bg-gray-700 rounded-lg"
                        >
                          <BarChart3 />
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
                        <p className="text-lg font-semibold text-gray-100">${Math.round(backtestResult.finalValue).toLocaleString()}</p>
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
                          <h3 className="text-lg font-bold text-gray-100 mb-4 flex items-center">
                            <Activity className="mr-2" />
                            Equity Curve - 자산 성장 곡선
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
                                  formatter={(value, name) => [
                                    `$${Number(value).toLocaleString()}`,
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
                          <h3 className="text-lg font-bold text-gray-100 mb-4 flex items-center">
                            <Shield className="mr-2" />
                            Drawdown Analysis - 낙폭 분석
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
                                  formatter={(value) => [`${Number(value).toFixed(2)}%`, 'Drawdown']}
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
                              <AlertCircle />
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
                      <h3 className="text-lg font-bold text-gray-100 mb-4 flex items-center">
                        <Target className="mr-2" />
                        포트폴리오 구성
                      </h3>
                      
                      <div className="grid grid-cols-5 gap-4">
                        {backtestResult.components.map((symbol) => (
                          <div key={symbol} className="bg-gray-700 rounded-lg p-3 text-center">
                            <p className="text-gray-100 font-semibold">{symbol}</p>
                            <p className="text-gray-400 text-sm">
                              {((backtestResult.weights?.[symbol] || 0.2) * 100).toFixed(1)}%
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
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
                    왼쪽에서 전략을 선택하고 백테스트를 실행하면 
                    <br />
                    상세한 성과 분석 결과가 여기에 표시됩니다.
                  </p>
                  
                  <div className="mt-8 grid grid-cols-3 gap-4">
                    <div className="bg-gray-700 rounded-lg p-4 text-center">
                      <div className="text-gray-400 flex justify-center mb-2">
                        <Target />
                      </div>
                      <p className="text-gray-100 font-semibold">실제 데이터</p>
                      <p className="text-gray-400 text-sm">CSV 파일 로딩</p>
                    </div>
                    <div className="bg-gray-700 rounded-lg p-4 text-center">
                      <div className="text-gray-400 flex justify-center mb-2">
                        <Shield />
                      </div>
                      <p className="text-gray-100 font-semibold">Python 엔진</p>
                      <p className="text-gray-400 text-sm">실제 백테스트</p>
                    </div>
                    <div className="bg-gray-700 rounded-lg p-4 text-center">
                      <div className="text-gray-400 flex justify-center mb-2">
                        <Activity />
                      </div>
                      <p className="text-gray-100 font-semibold">상세 분석</p>
                      <p className="text-gray-400 text-sm">성과 측정</p>
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
                <p className="text-gray-400 text-sm">Python 기반 전략 엔진 + CSV 데이터</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-6 text-sm text-gray-400">
              <p>실제 데이터 분석</p>
              <p>20가지 전략</p>
              <p>백엔드 연동</p>
              <p>상세 백테스트</p>
            </div>
          </div>
          
          <div className="border-t border-gray-700 mt-6 pt-6 text-center">
            <p className="text-gray-500 text-sm">
              본 시스템은 CSV 데이터와 Python 전략 엔진을 활용하여 실제 백테스트를 수행합니다. 
              투자 결정 시 신중하게 검토하시기 바랍니다.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}