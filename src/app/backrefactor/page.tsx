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
const TrendingUp = () => {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5">
      <polyline points="22,7 13.5,15.5 8.5,10.5 2,17"></polyline>
      <polyline points="16,7 22,7 22,13"></polyline>
    </svg>
  );
};

const BarChart3 = () => {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5">
      <path d="M3 3v18h18"></path>
      <path d="M18 17V9"></path>
      <path d="M13 17V5"></path>
      <path d="M8 17v-3"></path>
    </svg>
  );
};

const Shield = () => {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
    </svg>
  );
};

const Activity = () => {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5">
      <polyline points="22,12 18,12 15,21 9,3 6,12 2,12"></polyline>
    </svg>
  );
};

const Target = () => {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5">
      <circle cx="12" cy="12" r="10"></circle>
      <circle cx="12" cy="12" r="6"></circle>
      <circle cx="12" cy="12" r="2"></circle>
    </svg>
  );
};

const Play = () => {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5">
      <polygon points="5,3 19,12 5,21"></polygon>
    </svg>
  );
};

const Calendar = () => {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5">
      <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
      <line x1="16" y1="2" x2="16" y2="6"></line>
      <line x1="8" y1="2" x2="8" y2="6"></line>
      <line x1="3" y1="10" x2="21" y2="10"></line>
    </svg>
  );
};

const RefreshCw = ({ className = "w-5 h-5" }: { className?: string }) => {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
      <polyline points="23,4 23,10 17,10"></polyline>
      <polyline points="1,20 1,14 7,14"></polyline>
      <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"></path>
    </svg>
  );
};

const Info = () => {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4">
      <circle cx="12" cy="12" r="10"></circle>
      <line x1="12" y1="16" x2="12" y2="12"></line>
      <line x1="12" y1="8" x2="12.01" y2="8"></line>
    </svg>
  );
};

const AlertCircle = () => {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4">
      <circle cx="12" cy="12" r="10"></circle>
      <line x1="12" y1="8" x2="12" y2="12"></line>
      <line x1="12" y1="16" x2="12.01" y2="16"></line>
    </svg>
  );
};

const XCircle = () => {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5">
      <circle cx="12" cy="12" r="10"></circle>
      <line x1="15" y1="9" x2="9" y2="15"></line>
      <line x1="9" y1="9" x2="15" y2="15"></line>
    </svg>
  );
};

const Trophy = () => {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-5 h-5">
      <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"></path>
      <path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"></path>
      <path d="M4 22h16"></path>
      <path d="M10 14.66V17c0 .55.47.98.97 1.21C11.62 18.75 12.26 19 13 19s1.38-.25 2.03-.79c.5-.23.97-.66.97-1.21v-2.34"></path>
      <path d="M18 2H6v7a6 6 0 0 0 12 0V2z"></path>
    </svg>
  );
};

type RiskLevel = 'low' | 'medium' | 'high';
type Complexity = 'simple' | 'medium' | 'complex';

const riskColors: Record<RiskLevel, string> = {
  low: 'text-emerald-400 bg-emerald-900/30 border-emerald-700',
  medium: 'text-yellow-400 bg-yellow-900/30 border-yellow-700', 
  high: 'text-red-400 bg-red-900/30 border-red-700'
};

const complexityColors: Record<Complexity, string> = {
  simple: 'text-blue-400 bg-blue-900/30 border-blue-700',
  medium: 'text-purple-400 bg-purple-900/30 border-purple-700',
  complex: 'text-orange-400 bg-orange-900/30 border-orange-700'
};

interface Strategy {
  id: string;
  name: string;
  category: string;
  description: string;
  riskLevel: RiskLevel;
  complexity: Complexity;
  expectedReturn: string;
  volatility: string;
  details: string;
  icon?: React.ComponentType;
}

interface BacktestResult {
  strategy_id: string;
  strategy_name: string;
  totalReturn: number;
  annualReturn: number;
  sharpeRatio: number;
  sortinoRatio: number;
  maxDrawdown: number;
  winRate: number;
  volatility: number;
  finalValue: number;
  portfolioHistory?: number[];
  timestamp: string;
}

const iconMapping: Record<string, React.ComponentType> = {
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

const getAllStrategies = (): Strategy[] => [
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
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);
  const [backtestResults, setBacktestResults] = useState<BacktestResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showDetails, setShowDetails] = useState<string | null>(null);
  const [showGraphs, setShowGraphs] = useState<string | null>(null);
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [marketData, setMarketData] = useState<any[]>([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [dataLoadError, setDataLoadError] = useState<string | null>(null);
  
  const [backtestPeriod, setBacktestPeriod] = useState({
    startDate: '2024-01-01',
    endDate: '2024-12-31'
  });

  useEffect(() => {
    const loadData = async () => {
      try {
        setDataLoading(true);
        setDataLoadError(null);
        
        const loadedStrategies = getAllStrategies().map(strategy => ({
          ...strategy,
          icon: iconMapping[strategy.id] || Target
        }));
        setStrategies(loadedStrategies);

        let csvLoadSuccess = false;
        const csvPaths = ['/public/data/stock_analysis.csv', './data/stock_analysis.csv', '/data/stock_analysis.csv'];

        for (const csvPath of csvPaths) {
          try {
            const marketResponse = await fetch(csvPath);
            
            if (marketResponse.ok) {
              const marketCsvText = await marketResponse.text();
              
              if (marketCsvText.length > 100 && 
                  (marketCsvText.includes('date') || marketCsvText.includes('Date')) && 
                  (marketCsvText.includes('ticker') || marketCsvText.includes('symbol'))) {
                
                const marketParsed = Papa.parse(marketCsvText, {
                  header: true,
                  dynamicTyping: true,
                  skipEmptyLines: true,
                  delimitersToGuess: [',', ';', '\t'],
                  transformHeader: (header: string) => header.trim().toLowerCase()
                });

                if (marketParsed.data && marketParsed.data.length > 0) {
                  const loadedMarketData = marketParsed.data
                    .map((row: any) => {
                      const symbol = row.ticker || row.symbol;
                      const close = parseFloat(row.close);
                      
                      if (!symbol || !row.date || isNaN(close) || close <= 0) {
                        return null;
                      }

                      return {
                        date: row.date,
                        year: parseInt(row.year) || new Date(row.date).getFullYear(),
                        symbol: symbol,
                        ticker: symbol,
                        name: row.name || symbol,
                        market: row.market || 'UNKNOWN',
                        open: parseFloat(row.open) || close,
                        high: parseFloat(row.high) || close,
                        low: parseFloat(row.low) || close,
                        close: close,
                        volume: parseInt(row.volume) || 0,
                        market_cap: parseFloat(row.market_cap) || 0,
                        pe_ratio: parseFloat(row.pe_ratio) || 0,
                        roe: parseFloat(row.roe) || 0,
                        rsi_14: parseFloat(row.rsi_14) || 50
                      };
                    })
                    .filter((row: any) => row !== null);
                  
                  if (loadedMarketData.length > 0) {
                    setMarketData(loadedMarketData);
                    csvLoadSuccess = true;
                    break;
                  }
                }
              }
            }
          } catch (pathError) {
            console.warn(`${csvPath} 로드 실패:`, pathError);
          }
        }
        
        if (!csvLoadSuccess) {
          throw new Error('stock_analysis.csv 파일을 찾을 수 없습니다. /public/data/ 폴더에 파일이 있는지 확인하세요.');
        }

      } catch (err: any) {
        setDataLoadError(err.message);
        const fallbackStrategies = getAllStrategies().map(strategy => ({
          ...strategy,
          icon: iconMapping[strategy.id] || Target
        }));
        setStrategies(fallbackStrategies);
      } finally {
        setDataLoading(false);
      }
    };

    loadData();
  }, []);

  const filteredStrategies = strategies.filter(strategy => 
    categoryFilter === 'all' || strategy.category === categoryFilter
  );

  const runBacktest = async (strategyId: string) => {
    if (!marketData || marketData.length === 0) {
      alert('시장 데이터가 로드되지 않았습니다.');
      return;
    }

    setIsLoading(true);
    
    try {
      // 백테스트 기간에 맞는 데이터 필터링
      const filteredData = marketData.filter(row => {
        const rowDate = new Date(row.date);
        const startDate = new Date(backtestPeriod.startDate);
        const endDate = new Date(backtestPeriod.endDate);
        return rowDate >= startDate && rowDate <= endDate;
      });

      if (filteredData.length === 0) {
        alert('선택한 기간에 해당하는 데이터가 없습니다.');
        return;
      }

      // API 호출 시도
      let result: BacktestResult | null = null;
      
      try {
        console.log(`백테스트 API 호출: ${strategyId}`);
        const response = await fetch('/api/backtest', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            strategy_id: strategyId,
            start_date: backtestPeriod.startDate,
            end_date: backtestPeriod.endDate,
            market_data: filteredData.slice(0, 500) // 데이터 크기 제한
          })
        });

        if (response.ok) {
          const apiResult = await response.json();
          if (!apiResult.error) {
            result = apiResult;
            console.log('API 백테스트 성공');
          }
        } else {
          const errorText = await response.text();
          console.warn(`API 응답 오류 ${response.status}:`, errorText);
        }
      } catch (apiError: any) {
        console.warn('API 호출 실패:', apiError.message);
      }

      // API 실패 시 모의 결과 생성
      if (!result) {
        console.log('모의 백테스트 결과 생성');
        const strategy = strategies.find(s => s.id === strategyId);
        const baseReturn = 5 + Math.random() * 15; // 5-20% 연간 수익률
        const volatility = 8 + Math.random() * 20; // 8-28% 변동성
        
        result = {
          strategy_id: strategyId,
          strategy_name: strategy?.name || 'Unknown Strategy',
          totalReturn: baseReturn * ((new Date(backtestPeriod.endDate).getTime() - new Date(backtestPeriod.startDate).getTime()) / (365.25 * 24 * 60 * 60 * 1000)),
          annualReturn: baseReturn,
          volatility: volatility,
          sharpeRatio: 0.3 + Math.random() * 1.5,
          sortinoRatio: 0.5 + Math.random() * 1.5,
          maxDrawdown: 3 + Math.random() * 20,
          winRate: 45 + Math.random() * 20,
          finalValue: 100000 * (1 + (baseReturn / 100)),
          portfolioHistory: generateMockHistory(252, baseReturn, volatility),
          timestamp: new Date().toLocaleTimeString()
        };
        
        alert(`백테스트 API가 응답하지 않아 모의 결과를 생성했습니다. 실제 백엔드 연결이 필요합니다.`);
      }

      // 기존 결과에 추가
      const newResults = [...backtestResults];
      const existingIndex = newResults.findIndex(r => r.strategy_id === strategyId);
      
      if (existingIndex >= 0) {
        newResults[existingIndex] = result;
      } else {
        newResults.push(result);
      }
      
      setBacktestResults(newResults);
      
    } catch (error: any) {
      console.error('백테스트 오류:', error);
      alert(`백테스트 실행 중 오류가 발생했습니다: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // 모의 포트폴리오 히스토리 생성
  const generateMockHistory = (days: number, annualReturn: number, volatility: number): number[] => {
    const dailyReturn = annualReturn / 252 / 100;
    const dailyVol = volatility / Math.sqrt(252) / 100;
    const history = [100000];
    
    for (let i = 1; i < days; i++) {
      const randomReturn = dailyReturn + (Math.random() - 0.5) * dailyVol * 2;
      const newValue = history[i-1] * (1 + randomReturn);
      history.push(Math.max(newValue, history[i-1] * 0.8)); // 최대 20% 손실 제한
    }
    
    return history;
  };

  if (dataLoadError) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-8">
          <div className="w-16 h-16 bg-red-900/30 border border-red-700 rounded-full flex items-center justify-center mx-auto mb-4">
            <XCircle />
          </div>
          <h3 className="text-xl font-semibold text-gray-100 mb-2">데이터 로드 실패</h3>
          <p className="text-gray-400 mb-4">{dataLoadError}</p>
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 text-left">
            <p className="text-gray-300 text-sm mb-2">필요한 파일:</p>
            <code className="text-gray-400 text-xs">/public/data/stock_analysis.csv</code>
            <p className="text-gray-400 text-xs mt-2">
              CSV 형식: date,year,ticker,name,market,open,high,low,close,volume,market_cap,pe_ratio,roe,rsi_14
            </p>
          </div>
          <button 
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-gray-600 text-gray-100 rounded-lg hover:bg-gray-500 transition-colors"
          >
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  if (dataLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4 text-gray-400">
            <RefreshCw className="w-8 h-8 animate-spin" />
          </div>
          <h3 className="text-xl font-semibold text-gray-100 mb-2">데이터 로딩 중</h3>
          <p className="text-gray-400">stock_analysis.csv 파일을 읽는 중...</p>
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
                <p className="text-gray-400 text-sm">20가지 전문가 투자전략 백테스트</p>
              </div>
            </motion.div>
            
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-gray-300 text-sm">데이터 상태</p>
                <p className="text-emerald-400 text-sm font-semibold">CSV 연결됨</p>
              </div>
              <div className="text-right">
                <p className="text-gray-300 text-sm">데이터 포인트</p>
                <p className="text-gray-100 font-semibold">{marketData.length.toLocaleString()}개</p>
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
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-gray-100 flex items-center">
                  <Target />
                  <span className="ml-2">백테스트 설정</span>
                </h2>
              </div>

              <div className="mb-6 p-4 bg-gray-700 rounded-lg">
                <h3 className="text-sm font-semibold text-gray-200 mb-3 flex items-center">
                  <Calendar />
                  <span className="ml-2">백테스트 기간</span>
                </h3>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs text-gray-400 block mb-1">시작일</label>
                    <input
                      type="date"
                      value={backtestPeriod.startDate}
                      onChange={(e) => setBacktestPeriod({...backtestPeriod, startDate: e.target.value})}
                      className="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded-lg text-gray-100 text-xs"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-400 block mb-1">종료일</label>
                    <input
                      type="date"
                      value={backtestPeriod.endDate}
                      onChange={(e) => setBacktestPeriod({...backtestPeriod, endDate: e.target.value})}
                      className="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded-lg text-gray-100 text-xs"
                    />
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-gray-100">투자 전략</h3>
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
                            {React.createElement(strategy.icon || Target)}
                          </div>
                          <h3 className="font-semibold text-gray-100 text-sm">{strategy.name}</h3>
                          {strategy.category === 'advanced' && (
                            <span className="px-1.5 py-0.5 bg-gray-600 text-gray-200 text-xs rounded">고급</span>
                          )}
                        </div>
                        <p className="text-gray-400 text-xs mb-3">{strategy.description}</p>
                        
                        <div className="flex flex-wrap gap-2">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium border ${riskColors[strategy.riskLevel]}`}>
                            {strategy.riskLevel === 'low' ? '낮은 위험' : strategy.riskLevel === 'medium' ? '중간 위험' : '높은 위험'}
                          </span>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium border ${complexityColors[strategy.complexity]}`}>
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
                disabled={!selectedStrategy || isLoading || marketData.length === 0}
                className={`w-full mt-6 py-3 px-4 rounded-xl font-semibold transition-all flex items-center justify-center space-x-2 ${
                  selectedStrategy && !isLoading && marketData.length > 0
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
            {backtestResults.length > 0 ? (
              <div className="space-y-6">
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-gray-800 rounded-2xl border border-gray-700 p-6"
                >
                  <h2 className="text-xl font-bold text-gray-100 mb-6 flex items-center">
                    <Trophy />
                    <span className="ml-2">성과 종합 비교</span>
                  </h2>
                  
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-600">
                          <th className="text-left text-gray-300 pb-3">전략</th>
                          <th className="text-right text-gray-300 pb-3">연간수익률</th>
                          <th className="text-right text-gray-300 pb-3">샤프비율</th>
                          <th className="text-right text-gray-300 pb-3">최대낙폭</th>
                          <th className="text-right text-gray-300 pb-3">승률</th>
                        </tr>
                      </thead>
                      <tbody>
                        {backtestResults
                          .sort((a, b) => (b.annualReturn || 0) - (a.annualReturn || 0))
                          .map((result, index) => (
                          <tr key={result.strategy_id} className="border-b border-gray-700">
                            <td className="py-3">
                              <div className="flex items-center space-x-2">
                                {index === 0 && <Trophy className="w-4 h-4 text-yellow-400" />}
                                <span className="text-gray-100 font-medium">{result.strategy_name}</span>
                              </div>
                            </td>
                            <td className="text-right py-3">
                              <span className={`font-semibold ${
                                (result.annualReturn || 0) >= 12 ? 'text-emerald-400' : 
                                (result.annualReturn || 0) >= 8 ? 'text-yellow-400' : 'text-red-400'
                              }`}>
                                {(result.annualReturn || 0).toFixed(1)}%
                              </span>
                            </td>
                            <td className="text-right py-3">
                              <span className="text-gray-100">{(result.sharpeRatio || 0).toFixed(2)}</span>
                            </td>
                            <td className="text-right py-3">
                              <span className="text-red-400">-{(result.maxDrawdown || 0).toFixed(1)}%</span>
                            </td>
                            <td className="text-right py-3">
                              <span className="text-gray-100">{(result.winRate || 0).toFixed(1)}%</span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </motion.div>

                <div className="space-y-4">
                  {backtestResults.map((result, index) => (
                    <motion.div
                      key={result.strategy_id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="bg-gray-800 rounded-2xl border border-gray-700 p-6"
                    >
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-bold text-gray-100 flex items-center">
                          {React.createElement(iconMapping[result.strategy_id] || Target)}
                          <span className="ml-2">{result.strategy_name}</span>
                        </h3>
                        <div className="flex items-center space-x-2">
                          <span className="text-xs text-gray-400">실행: {result.timestamp}</span>
                          <button 
                            onClick={() => setShowGraphs(showGraphs === result.strategy_id ? null : result.strategy_id)}
                            className={`p-2 transition-colors rounded-lg ${
                              showGraphs === result.strategy_id
                                ? 'text-gray-200 bg-gray-600' 
                                : 'text-gray-400 hover:text-gray-200 bg-gray-700'
                            }`}
                          >
                            <BarChart3 />
                          </button>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="bg-gray-700 border border-gray-600 rounded-xl p-4">
                          <p className="text-gray-300 text-sm font-medium">총 수익률</p>
                          <p className="text-2xl font-bold text-gray-100">{(result.totalReturn || 0).toFixed(1)}%</p>
                        </div>
                        <div className="bg-gray-700 border border-gray-600 rounded-xl p-4">
                          <p className="text-gray-300 text-sm font-medium">연간 수익률</p>
                          <p className="text-2xl font-bold text-gray-100">{(result.annualReturn || 0).toFixed(1)}%</p>
                        </div>
                        <div className="bg-gray-700 border border-gray-600 rounded-xl p-4">
                          <p className="text-gray-300 text-sm font-medium">샤프 비율</p>
                          <p className="text-2xl font-bold text-gray-100">{(result.sharpeRatio || 0).toFixed(2)}</p>
                        </div>
                        <div className="bg-gray-700 border border-gray-600 rounded-xl p-4">
                          <p className="text-gray-300 text-sm font-medium">최대 낙폭</p>
                          <p className="text-2xl font-bold text-red-400">-{(result.maxDrawdown || 0).toFixed(1)}%</p>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                        <div className="bg-gray-700 rounded-xl p-4">
                          <p className="text-gray-400 text-sm">변동성</p>
                          <p className="text-lg font-semibold text-gray-100">{(result.volatility || 0).toFixed(1)}%</p>
                        </div>
                        <div className="bg-gray-700 rounded-xl p-4">
                          <p className="text-gray-400 text-sm">소르티노 비율</p>
                          <p className="text-lg font-semibold text-gray-100">{(result.sortinoRatio || 0).toFixed(2)}</p>
                        </div>
                        <div className="bg-gray-700 rounded-xl p-4">
                          <p className="text-gray-400 text-sm">승률</p>
                          <p className="text-lg font-semibold text-gray-100">{(result.winRate || 0).toFixed(1)}%</p>
                        </div>
                        <div className="bg-gray-700 rounded-xl p-4">
                          <p className="text-gray-400 text-sm">최종 가치</p>
                          <p className="text-lg font-semibold text-gray-100">${Math.round(result.finalValue || 0).toLocaleString()}</p>
                        </div>
                      </div>

                      <AnimatePresence>
                        {showGraphs === result.strategy_id && result.portfolioHistory && (
                          <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            className="mt-6 space-y-6"
                          >
                            <div className="bg-gray-700 rounded-xl p-4">
                              <h4 className="text-md font-bold text-gray-100 mb-4 flex items-center">
                                <Activity />
                                <span className="ml-2">Equity Curve</span>
                              </h4>
                              
                              <div className="h-64">
                                <ResponsiveContainer width="100%" height="100%">
                                  <LineChart data={result.portfolioHistory.map((value, idx) => ({
                                    date: idx,
                                    value: value,
                                    benchmark: 100000 * Math.pow(1.08, idx / 252)
                                  }))}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#4b5563" />
                                    <XAxis dataKey="date" stroke="#9ca3af" fontSize={12} />
                                    <YAxis stroke="#9ca3af" fontSize={12} tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`} />
                                    <Tooltip 
                                      contentStyle={{
                                        backgroundColor: '#374151',
                                        border: '1px solid #4b5563',
                                        borderRadius: '8px',
                                        color: '#f9fafb'
                                      }}
                                      formatter={(value, name) => [
                                        `$${Number(value).toLocaleString()}`,
                                        name === 'value' ? '전략' : '벤치마크'
                                      ]}
                                    />
                                    <Line type="monotone" dataKey="value" stroke="#6b7280" strokeWidth={3} dot={false} name="전략" />
                                    <Line type="monotone" dataKey="benchmark" stroke="#9ca3af" strokeWidth={2} strokeDasharray="5 5" dot={false} name="벤치마크" />
                                  </LineChart>
                                </ResponsiveContainer>
                              </div>
                            </div>

                            <div className="bg-gray-700 rounded-xl p-4">
                              <h4 className="text-md font-bold text-gray-100 mb-4 flex items-center">
                                <Shield />
                                <span className="ml-2">Drawdown Analysis</span>
                              </h4>
                              
                              <div className="h-48">
                                <ResponsiveContainer width="100%" height="100%">
                                  <AreaChart data={result.portfolioHistory.map((value, idx) => {
                                    const peak = Math.max(...result.portfolioHistory.slice(0, idx + 1));
                                    const drawdown = ((value - peak) / peak) * 100;
                                    return { date: idx, drawdown: drawdown };
                                  })}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#4b5563" />
                                    <XAxis dataKey="date" stroke="#9ca3af" fontSize={12} />
                                    <YAxis stroke="#9ca3af" fontSize={12} tickFormatter={(value) => `${value.toFixed(1)}%`} />
                                    <Tooltip 
                                      contentStyle={{
                                        backgroundColor: '#374151',
                                        border: '1px solid #4b5563',
                                        borderRadius: '8px',
                                        color: '#f9fafb'
                                      }}
                                      formatter={(value) => [`${Number(value).toFixed(2)}%`, 'Drawdown']}
                                    />
                                    <Area type="monotone" dataKey="drawdown" stroke="#ef4444" fill="#ef4444" fillOpacity={0.2} />
                                  </AreaChart>
                                </ResponsiveContainer>
                              </div>
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </motion.div>
                  ))}
                </div>
              </div>
            ) : (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="bg-gray-800 rounded-2xl border border-gray-700 p-12 text-center"
              >
                <div className="w-16 h-16 bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4 text-gray-400">
                  <BarChart3 />
                </div>
                <h3 className="text-xl font-semibold text-gray-100 mb-2">백테스트 결과 대기 중</h3>
                <p className="text-gray-400 mb-4">
                  백테스트 기간을 설정하고 전략을 선택한 후 실행하세요
                </p>
                
                <div className="bg-gray-700 rounded-lg p-4 text-left max-w-md mx-auto">
                  <h4 className="text-sm font-semibold text-gray-200 mb-2">백테스트 정보</h4>
                  <div className="space-y-1 text-xs text-gray-400">
                    <p>• 기간: {backtestPeriod.startDate} ~ {backtestPeriod.endDate}</p>
                    <p>• 사용 가능한 데이터: {marketData.length.toLocaleString()}개 포인트</p>
                    <p>• 전략: {strategies.length}가지 사용 가능</p>
                  </div>
                </div>
              </motion.div>
            )}
          </div>
        </div>
      </div>

      <footer className="bg-gray-800 border-b border-gray-700 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center space-x-3 mb-4 md:mb-0">
              <div className="w-8 h-8 bg-gray-600 rounded-lg flex items-center justify-center text-gray-200">
                <TrendingUp />
              </div>
              <div>
                <p className="text-gray-100 font-semibold">Quant Strategy Backtester</p>
                <p className="text-gray-400 text-sm">stock_analysis.csv 데이터 기반 백테스트</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-6 text-sm text-gray-400">
              <div className="text-center">
                <p className="text-gray-300 font-medium">{marketData.length.toLocaleString()}</p>
                <p>데이터 포인트</p>
              </div>
              <div className="text-center">
                <p className="text-gray-300 font-medium">20</p>
                <p>전략 수</p>
              </div>
              <div className="text-center">
                <p className="text-gray-300 font-medium">{backtestResults.length}</p>
                <p>실행된 백테스트</p>
              </div>
            </div>
          </div>
          
          <div className="border-t border-gray-700 mt-6 pt-6 text-center">
            <p className="text-gray-500 text-sm">
              백테스트 기간: {backtestPeriod.startDate} ~ {backtestPeriod.endDate} | 
              실제 투자 결정 시 신중하게 검토하시기 바랍니다.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}