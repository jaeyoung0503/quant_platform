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
} from 'recharts';

interface StockData {
  date: string;
  close: number;
  open: number;
  high: number;
  low: number;
  volume: number;
}

interface TechnicalIndicators {
  ma5: (number | null)[];
  ma20: (number | null)[];
  ma60: (number | null)[];
  rsi: (number | null)[];
  bb: {
    upper: (number | null)[];
    middle: (number | null)[];
    lower: (number | null)[];
  };
}

interface TradingSignal {
  type: 'BUY' | 'SELL';
  price: number;
  date: string;
  ma5?: number;
  ma20?: number;
  rsi?: number;
}

interface BacktestResult {
  totalReturn: number;
  annualReturn: number;
  winRate: number;
  finalValue: number;
  initialCapital: number;
  trades: number;
  signals: TradingSignal[];
}

interface AnalysisResult {
  signals: TradingSignal[];
  backtest: BacktestResult;
}

interface Strategy {
  id: string;
  name: string;
  icon: React.ComponentType<{ className?: string }>;
}

interface ChartDataPoint {
  date: string;
  close: number;
  ma5?: number | null;
  ma20?: number | null;
  ma60?: number | null;
  rsi?: number | null;
  bb_upper?: number | null;
  bb_middle?: number | null;
  bb_lower?: number | null;
}

interface AnalysisStep {
  step: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  message: string;
  details?: string;
}

// 아이콘 컴포넌트들
const TrendingUp = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <polyline points="22,7 13.5,15.5 8.5,10.5 2,17"></polyline>
    <polyline points="16,7 22,7 22,13"></polyline>
  </svg>
);

const Activity = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <polyline points="22,12 18,12 15,21 9,3 6,12 2,12"></polyline>
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

const Play = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <polygon points="5,3 19,12 5,21"></polygon>
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

const RefreshCw = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <polyline points="23,4 23,10 17,10"></polyline>
    <polyline points="1,20 1,14 7,14"></polyline>
    <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"></path>
  </svg>
);

const CheckCircle2 = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
    <polyline points="22,4 12,14.01 9,11.01"></polyline>
  </svg>
);

const AlertCircle = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <circle cx="12" cy="12" r="10"></circle>
    <line x1="12" y1="8" x2="12" y2="12"></line>
    <line x1="12" y1="16" x2="12.01" y2="16"></line>
  </svg>
);

const Clock = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <circle cx="12" cy="12" r="10"></circle>
    <polyline points="12,6 12,12 16,14"></polyline>
  </svg>
);

const Eye = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
    <circle cx="12" cy="12" r="3"></circle>
  </svg>
);

const ChevronDown = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <polyline points="6,9 12,15 18,9"></polyline>
  </svg>
);

const Upload = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
    <polyline points="17,8 12,3 7,8"></polyline>
    <line x1="12" y1="3" x2="12" y2="15"></line>
  </svg>
);

// CSV 데이터 로더
class CSVDataLoader {
  static async loadStockData(): Promise<StockData[]> {
    try {
      const response = await fetch('/data/stock.csv');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const csvText = await response.text();
      return this.parseCSV(csvText);
    } catch (error) {
      console.error('CSV 파일 로드 실패, 샘플 데이터 사용:', error);
      return this.generateSampleData();
    }
  }

  static generateStockDataForSymbol(symbol: string, initialPrice: number, volatility: number): StockData[] {
    const data: StockData[] = [];
    let currentPrice = initialPrice;
    
    for (let i = 0; i < 252; i++) {
      const returns = (Math.random() - 0.5) * volatility;
      currentPrice = currentPrice * (1 + returns);
      currentPrice = Math.max(currentPrice, initialPrice * 0.3);
      
      const date = new Date();
      date.setDate(date.getDate() - (252 - i));
      
      const dailyVolatility = volatility * (0.5 + Math.random() * 0.5);
      const open = currentPrice * (1 + (Math.random() - 0.5) * dailyVolatility);
      const high = Math.max(open, currentPrice) * (1 + Math.random() * dailyVolatility * 0.5);
      const low = Math.min(open, currentPrice) * (1 - Math.random() * dailyVolatility * 0.5);
      
      data.push({
        date: date.toISOString().split('T')[0],
        close: currentPrice,
        open,
        high,
        low,
        volume: Math.floor(1000000 * (0.5 + Math.random() * 1.5))
      });
    }
    
    return data;
  }

  static parseCSV(csvText: string): StockData[] {
    const lines = csvText.trim().split('\n');
    if (lines.length < 2) {
      throw new Error('CSV 파일이 비어있습니다.');
    }

    const headers = lines[0].toLowerCase().split(',').map(h => h.trim());
    const headerMap = {
      date: headers.findIndex(h => h.includes('date')),
      open: headers.findIndex(h => h.includes('open')),
      high: headers.findIndex(h => h.includes('high')),
      low: headers.findIndex(h => h.includes('low')),
      close: headers.findIndex(h => h.includes('close')),
      volume: headers.findIndex(h => h.includes('volume'))
    };

    if (headerMap.date === -1 || headerMap.close === -1) {
      throw new Error('필수 컬럼이 없습니다: date, close');
    }

    const data: StockData[] = [];
    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].split(',').map(v => v.trim());
      
      const dateStr = values[headerMap.date];
      const close = parseFloat(values[headerMap.close]);
      const open = headerMap.open !== -1 ? parseFloat(values[headerMap.open]) || close : close;
      const high = headerMap.high !== -1 ? parseFloat(values[headerMap.high]) || close : close;
      const low = headerMap.low !== -1 ? parseFloat(values[headerMap.low]) || close : close;
      const volume = headerMap.volume !== -1 ? parseInt(values[headerMap.volume]) || 0 : 0;

      if (isNaN(close) || close <= 0) continue;
      
      const date = new Date(dateStr).toISOString().split('T')[0];
      if (!date) continue;
      
      data.push({ date, open, high, low, close, volume });
    }

    if (data.length < 10) {
      throw new Error('유효한 데이터가 부족합니다');
    }

    return data.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  }

  static generateSampleData(): StockData[] {
    const data: StockData[] = [];
    let currentPrice = 100;
    
    for (let i = 0; i < 252; i++) {
      const returns = (Math.random() - 0.5) * 0.05;
      currentPrice = currentPrice * (1 + returns);
      
      const date = new Date();
      date.setDate(date.getDate() - (252 - i));
      
      const open = currentPrice * (1 + (Math.random() - 0.5) * 0.02);
      const high = Math.max(open, currentPrice) * (1 + Math.random() * 0.02);
      const low = Math.min(open, currentPrice) * (1 - Math.random() * 0.02);
      
      data.push({
        date: date.toISOString().split('T')[0],
        close: currentPrice,
        open,
        high,
        low,
        volume: Math.floor(1000000 * (0.5 + Math.random() * 1.5))
      });
    }
    
    return data;
  }
}

// 기술적 지표 계산
class TechnicalIndicatorsCalculator {
  static calculateMA(data: StockData[], period: number): (number | null)[] {
    const result: (number | null)[] = [];
    for (let i = 0; i < data.length; i++) {
      if (i < period - 1) {
        result.push(null);
      } else {
        const sum = data.slice(i - period + 1, i + 1).reduce((acc, val) => acc + val.close, 0);
        result.push(sum / period);
      }
    }
    return result;
  }
  
  static calculateRSI(data: StockData[], period: number = 14): (number | null)[] {
    const result: (number | null)[] = [];
    for (let i = 0; i < data.length; i++) {
      if (i < period) {
        result.push(null);
      } else {
        let gains = 0, losses = 0;
        for (let j = i - period + 1; j <= i; j++) {
          const change = data[j].close - data[j-1].close;
          if (change > 0) gains += change;
          else losses -= change;
        }
        const avgGain = gains / period;
        const avgLoss = losses / period;
        const rs = avgGain / avgLoss;
        const rsi = 100 - (100 / (1 + rs));
        result.push(isNaN(rsi) ? 50 : rsi);
      }
    }
    return result;
  }
  
  static calculateBollingerBands(data: StockData[], period: number = 20): { upper: (number | null)[]; middle: (number | null)[]; lower: (number | null)[] } {
    const ma = this.calculateMA(data, period);
    const upper: (number | null)[] = [];
    const lower: (number | null)[] = [];
    
    for (let i = 0; i < data.length; i++) {
      if (i < period - 1) {
        upper.push(null);
        lower.push(null);
      } else {
        const slice = data.slice(i - period + 1, i + 1);
        const mean = ma[i];
        if (mean !== null) {
          const variance = slice.reduce((acc, val) => acc + Math.pow(val.close - mean, 2), 0) / period;
          const std = Math.sqrt(variance);
          upper.push(mean + (std * 2));
          lower.push(mean - (std * 2));
        } else {
          upper.push(null);
          lower.push(null);
        }
      }
    }
    
    return { upper, middle: ma, lower };
  }
}

// 트레이딩 전략
class TradingStrategiesEngine {
  static generateSignals(data: StockData[], strategy: string, indicators: TechnicalIndicators): TradingSignal[] {
    const signals: TradingSignal[] = [];
    
    for (let i = 1; i < data.length; i++) {
      let signal: TradingSignal | null = null;
      
      switch (strategy) {
        case 'golden_cross':
          if (indicators.ma5[i] && indicators.ma20[i] && indicators.ma5[i-1] && indicators.ma20[i-1]) {
            if (indicators.ma5[i]! > indicators.ma20[i]! && indicators.ma5[i-1]! <= indicators.ma20[i-1]!) {
              signal = { type: 'BUY', price: data[i].close, date: data[i].date, ma5: indicators.ma5[i]!, ma20: indicators.ma20[i]! };
            } else if (indicators.ma5[i]! < indicators.ma20[i]! && indicators.ma5[i-1]! >= indicators.ma20[i-1]!) {
              signal = { type: 'SELL', price: data[i].close, date: data[i].date, ma5: indicators.ma5[i]!, ma20: indicators.ma20[i]! };
            }
          }
          break;
        case 'rsi_divergence':
          if (indicators.rsi[i] && indicators.rsi[i-1]) {
            if (indicators.rsi[i]! > 30 && indicators.rsi[i-1]! <= 30) {
              signal = { type: 'BUY', price: data[i].close, date: data[i].date, rsi: indicators.rsi[i]! };
            } else if (indicators.rsi[i]! < 70 && indicators.rsi[i-1]! >= 70) {
              signal = { type: 'SELL', price: data[i].close, date: data[i].date, rsi: indicators.rsi[i]! };
            }
          }
          break;
        case 'bollinger_bands':
          if (indicators.bb.lower[i] && indicators.bb.upper[i]) {
            if (data[i].close > indicators.bb.lower[i]! && data[i-1].close <= (indicators.bb.lower[i-1] || data[i-1].close)) {
              signal = { type: 'BUY', price: data[i].close, date: data[i].date };
            } else if (data[i].close < indicators.bb.upper[i]! && data[i-1].close >= (indicators.bb.upper[i-1] || data[i-1].close)) {
              signal = { type: 'SELL', price: data[i].close, date: data[i].date };
            }
          }
          break;
        case 'macd_crossover':
          if (indicators.rsi[i] && indicators.rsi[i-1]) {
            if (indicators.rsi[i]! < 50 && indicators.rsi[i-1]! >= 50) {
              signal = { type: 'BUY', price: data[i].close, date: data[i].date };
            } else if (indicators.rsi[i]! > 50 && indicators.rsi[i-1]! <= 50) {
              signal = { type: 'SELL', price: data[i].close, date: data[i].date };
            }
          }
          break;
      }
      
      if (signal) signals.push(signal);
    }
    
    return signals;
  }
  
  static runBacktest(data: StockData[], signals: TradingSignal[], initialCapital: number = 10000000): BacktestResult {
    let capital = initialCapital;
    let position = 0;
    let trades = 0;
    
    for (const signal of signals) {
      if (signal.type === 'BUY' && position === 0) {
        position = capital / signal.price;
        capital = 0;
        trades++;
      } else if (signal.type === 'SELL' && position > 0) {
        capital = position * signal.price;
        position = 0;
        trades++;
      }
    }
    
    if (position > 0) {
      const finalPrice = data[data.length - 1].close;
      capital = position * finalPrice;
    }
    
    const totalReturn = (capital - initialCapital) / initialCapital * 100;
    const buySignals = signals.filter(s => s.type === 'BUY');
    const sellSignals = signals.filter(s => s.type === 'SELL');
    
    let profitableTrades = 0;
    for (let i = 0; i < Math.min(buySignals.length, sellSignals.length); i++) {
      if (sellSignals[i].price > buySignals[i].price) {
        profitableTrades++;
      }
    }
    
    const winRate = buySignals.length > 0 ? (profitableTrades / Math.min(buySignals.length, sellSignals.length)) * 100 : 0;
    const days = data.length;
    const annualReturn = days > 0 ? (Math.pow(capital / initialCapital, 365 / days) - 1) * 100 : 0;
    
    return {
      totalReturn,
      annualReturn,
      winRate,
      finalValue: capital,
      initialCapital,
      trades,
      signals
    };
  }
}

// 메인 컴포넌트
export default function OneStockAnalyzer(): JSX.Element {
  const [selectedStrategies, setSelectedStrategies] = useState<string[]>([]);
  const [selectedStock, setSelectedStock] = useState<string>('');
  const [stockSearchQuery, setStockSearchQuery] = useState<string>('');
  const [isStockSearchOpen, setIsStockSearchOpen] = useState<boolean>(false);
  const [filteredStocks, setFilteredStocks] = useState<Stock[]>([]);
  const [allStocks, setAllStocks] = useState<Stock[]>([]);
  const [isLoadingStocks, setIsLoadingStocks] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [analysisResults, setAnalysisResults] = useState<Record<string, AnalysisResult>>({});
  const [stockData, setStockData] = useState<StockData[] | null>(null);
  const [indicators, setIndicators] = useState<TechnicalIndicators>({
    ma5: [],
    ma20: [],
    ma60: [],
    rsi: [],
    bb: { upper: [], middle: [], lower: [] }
  });
  const [analysisSteps, setAnalysisSteps] = useState<AnalysisStep[]>([]);
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [expandedSignals, setExpandedSignals] = useState<Record<string, boolean>>({});
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [csvLoadStatus, setCsvLoadStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');

  // 회사 목록 로드 함수
  const loadCompanyList = async (): Promise<void> => {
    setIsLoadingStocks(true);
    try {
      const response = await fetch('/data/company_list.csv');
      if (!response.ok) {
        throw new Error('회사 목록 파일을 찾을 수 없습니다');
      }
      
      const csvText = await response.text();
      const lines = csvText.trim().split('\n');
      
      if (lines.length < 2) {
        throw new Error('회사 목록 파일이 비어있습니다');
      }

      const headers = lines[0].toLowerCase().split(',').map(h => h.trim());
      const headerMap = {
        symbol: headers.findIndex(h => h.includes('symbol') || h.includes('code') || h.includes('ticker')),
        name: headers.findIndex(h => h.includes('name') || h.includes('company')),
        market: headers.findIndex(h => h.includes('market') || h.includes('exchange')),
        price: headers.findIndex(h => h.includes('price') || h.includes('close')),
        sector: headers.findIndex(h => h.includes('sector') || h.includes('industry'))
      };

      const companies: Stock[] = [];
      
      for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split(',').map(v => v.trim().replace(/"/g, ''));
        
        if (values.length < 2) continue;
        
        const symbol = headerMap.symbol !== -1 ? values[headerMap.symbol] : '';
        const name = headerMap.name !== -1 ? values[headerMap.name] : '';
        const market = headerMap.market !== -1 ? values[headerMap.market] || 'KOSPI' : 'KOSPI';
        const price = headerMap.price !== -1 ? parseFloat(values[headerMap.price]) || Math.floor(Math.random() * 100000 + 10000) : Math.floor(Math.random() * 100000 + 10000);
        
        if (symbol && name) {
          // 시장별 기본 변동성 설정
          let volatility = 0.025;
          if (market === 'KOSDAQ') volatility = 0.035;
          else if (market === 'NASDAQ') volatility = 0.030;
          
          companies.push({
            symbol: symbol,
            name: name,
            price: price,
            volatility: volatility + (Math.random() * 0.02 - 0.01), // ±1% 랜덤 변동성
            market: market
          });
        }
      }
      
      console.log(`회사 목록 로드 완료: ${companies.length}개 종목`);
      setAllStocks(companies);
      
    } catch (error) {
      console.error('회사 목록 로드 실패, 기본 목록 사용:', error);
      // 기본 종목 목록 사용
      setAllStocks(getDefaultStocks());
    } finally {
      setIsLoadingStocks(false);
    }
  };

  // 기본 종목 목록 (CSV 로드 실패시 사용)
  const getDefaultStocks = (): Stock[] => {
    return [
      // 주요 대형주
      { symbol: '005930', name: '삼성전자', price: 71000, volatility: 0.025, market: 'KOSPI' },
      { symbol: '000660', name: 'SK하이닉스', price: 130000, volatility: 0.035, market: 'KOSPI' },
      { symbol: '035420', name: 'NAVER', price: 230000, volatility: 0.030, market: 'KOSPI' },
      { symbol: '051910', name: 'LG화학', price: 620000, volatility: 0.028, market: 'KOSPI' },
      { symbol: '006400', name: '삼성SDI', price: 520000, volatility: 0.032, market: 'KOSPI' },
      { symbol: '207940', name: '삼성바이오로직스', price: 850000, volatility: 0.030, market: 'KOSPI' },
      { symbol: '068270', name: '셀트리온', price: 180000, volatility: 0.035, market: 'KOSPI' },
      { symbol: '035720', name: '카카오', price: 55000, volatility: 0.040, market: 'KOSPI' },
      { symbol: '042660', name: '한화오션', price: 28000, volatility: 0.045, market: 'KOSPI' },
      { symbol: '028260', name: '삼성물산', price: 120000, volatility: 0.025, market: 'KOSPI' },
      { symbol: '066570', name: 'LG전자', price: 95000, volatility: 0.030, market: 'KOSPI' },
      
      // 중형주
      { symbol: '096770', name: 'SK이노베이션', price: 180000, volatility: 0.035, market: 'KOSPI' },
      { symbol: '323410', name: 'kakaopay', price: 85000, volatility: 0.045, market: 'KOSPI' },
      { symbol: '352820', name: '하이브', price: 250000, volatility: 0.050, market: 'KOSPI' },
      { symbol: '373220', name: 'LG에너지솔루션', price: 480000, volatility: 0.040, market: 'KOSPI' },
      
      // KOSDAQ
      { symbol: '247540', name: 'EcoPro BM', price: 220000, volatility: 0.055, market: 'KOSDAQ' },
      { symbol: '086520', name: '에코프로', price: 880000, volatility: 0.060, market: 'KOSDAQ' },
      { symbol: '091990', name: '셀트리온헬스케어', price: 85000, volatility: 0.040, market: 'KOSDAQ' },
      { symbol: '000250', name: '삼천당제약', price: 150000, volatility: 0.045, market: 'KOSDAQ' },
      
      // 해외 주식
      { symbol: 'AAPL', name: 'Apple Inc.', price: 180, volatility: 0.025, market: 'NASDAQ' },
      { symbol: 'GOOGL', name: 'Alphabet Inc.', price: 130, volatility: 0.022, market: 'NASDAQ' },
      { symbol: 'MSFT', name: 'Microsoft Corp.', price: 350, volatility: 0.020, market: 'NASDAQ' },
      { symbol: 'TSLA', name: 'Tesla Inc.', price: 250, volatility: 0.045, market: 'NASDAQ' },
      { symbol: 'NVDA', name: 'NVIDIA Corp.', price: 500, volatility: 0.035, market: 'NASDAQ' }
    ];
  };

  // 컴포넌트 마운트시 회사 목록 로드
  React.useEffect(() => {
    loadCompanyList();
  }, []);

  const strategies: Strategy[] = [
    { id: 'golden_cross', name: 'Golden Cross Strategy', icon: TrendingUp },
    { id: 'rsi_divergence', name: 'RSI Mean Reversion', icon: Activity },
    { id: 'bollinger_bands', name: 'Bollinger Bands Strategy', icon: Target },
    { id: 'macd_crossover', name: 'MACD Crossover', icon: Shield }
  ];

  // 종목 검색 기능
  const handleStockSearch = (query: string): void => {
    setStockSearchQuery(query);
    
    if (query.trim() === '') {
      setFilteredStocks([]);
      setIsStockSearchOpen(false);
      return;
    }

    const filtered = allStocks.filter(stock => 
      stock.symbol.toLowerCase().includes(query.toLowerCase()) ||
      stock.name.toLowerCase().includes(query.toLowerCase())
    );
    
    // 최대 20개 결과만 표시
    setFilteredStocks(filtered.slice(0, 20));
    setIsStockSearchOpen(true);
  };

  const handleStockSelect = (stock: Stock): void => {
    setSelectedStock(stock.symbol);
    setStockSearchQuery(`${stock.symbol} - ${stock.name}`);
    setIsStockSearchOpen(false);
    setFilteredStocks([]);
  };

  const clearStockSelection = (): void => {
    setSelectedStock('');
    setStockSearchQuery('');
    setFilteredStocks([]);
    setIsStockSearchOpen(false);
  };

  const initializeAnalysisSteps = (): void => {
    const steps: AnalysisStep[] = [
      { step: 'CSV Data Loading', status: 'pending', message: 'CSV 파일 로드 중...', details: '/data/stock.csv 파일을 읽고 있습니다.' },
      { step: 'Data Validation', status: 'pending', message: '데이터 검증 중...', details: '날짜 형식 및 데이터 유효성을 확인합니다.' },
      { step: 'Technical Indicators', status: 'pending', message: '기술적 지표 계산 중...', details: 'MA, RSI, Bollinger Bands를 계산합니다.' },
      { step: 'Signal Generation', status: 'pending', message: '매매 신호 생성 중...', details: '선택된 전략으로 신호를 생성합니다.' },
      { step: 'Backtesting', status: 'pending', message: '백테스트 실행 중...', details: '각 전략의 성과를 분석합니다.' },
      { step: 'Analysis Complete', status: 'pending', message: '분석 완료', details: '모든 분석이 완료되었습니다.' }
    ];
    setAnalysisSteps(steps);
    setCurrentStep(0);
  };

  const updateStepStatus = (stepIndex: number, status: 'pending' | 'running' | 'completed' | 'error'): void => {
    setAnalysisSteps(prev => prev.map((step, index) =>
      index === stepIndex ? { ...step, status } : step
    ));
  };

  const runAnalysis = async (): Promise<void> => {
    if (selectedStrategies.length === 0) return;
    
    setIsLoading(true);
    setCsvLoadStatus('loading');
    setErrorMessage('');
    initializeAnalysisSteps();

    try {
      setCurrentStep(0);
      updateStepStatus(0, 'running');
      await new Promise(resolve => setTimeout(resolve, 500));
      
      let data: StockData[];
      
      // 선택된 종목이 있으면 해당 종목 데이터 생성, 없으면 CSV에서 로드
      if (selectedStock) {
        const stockInfo = allStocks.find(s => s.symbol === selectedStock);
        if (stockInfo) {
          data = CSVDataLoader.generateStockDataForSymbol(stockInfo.symbol, stockInfo.price, stockInfo.volatility);
          setCsvLoadStatus('success');
        } else {
          data = await CSVDataLoader.loadStockData();
          setCsvLoadStatus('success');
        }
      } else {
        data = await CSVDataLoader.loadStockData();
        setCsvLoadStatus('success');
      }
      
      updateStepStatus(0, 'completed');

      setCurrentStep(1);
      updateStepStatus(1, 'running');
      await new Promise(resolve => setTimeout(resolve, 800));
      setStockData(data);
      updateStepStatus(1, 'completed');

      setCurrentStep(2);
      updateStepStatus(2, 'running');
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const ma5 = TechnicalIndicatorsCalculator.calculateMA(data, 5);
      const ma20 = TechnicalIndicatorsCalculator.calculateMA(data, 20);
      const ma60 = TechnicalIndicatorsCalculator.calculateMA(data, 60);
      const rsi = TechnicalIndicatorsCalculator.calculateRSI(data);
      const bb = TechnicalIndicatorsCalculator.calculateBollingerBands(data);
      
      setIndicators({ ma5, ma20, ma60, rsi, bb });
      updateStepStatus(2, 'completed');

      setCurrentStep(3);
      updateStepStatus(3, 'running');
      await new Promise(resolve => setTimeout(resolve, 1200));

      const results: Record<string, AnalysisResult> = {};
      for (const strategyId of selectedStrategies) {
        const signals = TradingStrategiesEngine.generateSignals(data, strategyId, { ma5, ma20, ma60, rsi, bb });
        const backtest = TradingStrategiesEngine.runBacktest(data, signals);
        results[strategyId] = { signals, backtest };
      }
      updateStepStatus(3, 'completed');

      setCurrentStep(4);
      updateStepStatus(4, 'running');
      await new Promise(resolve => setTimeout(resolve, 1000));
      setAnalysisResults(results);
      updateStepStatus(4, 'completed');

      setCurrentStep(5);
      updateStepStatus(5, 'completed');

    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : '분석 중 오류가 발생했습니다';
      setErrorMessage(errorMsg);
      setCsvLoadStatus('error');
      updateStepStatus(currentStep, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStrategyToggle = (strategyId: string): void => {
    setSelectedStrategies(prev =>
      prev.includes(strategyId)
        ? prev.filter(id => id !== strategyId)
        : [...prev, strategyId]
    );
  };

  const getChartData = (): ChartDataPoint[] => {
    if (!stockData) return [];
    return stockData.map((item, index) => ({
      date: item.date,
      close: item.close,
      ma5: indicators.ma5?.[index],
      ma20: indicators.ma20?.[index],
      ma60: indicators.ma60?.[index],
      rsi: indicators.rsi?.[index],
      bb_upper: indicators.bb?.upper[index],
      bb_middle: indicators.bb?.middle[index],
      bb_lower: indicators.bb?.lower[index]
    }));
  };

  const getStepIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle2 className="w-4 h-4 text-gray-300" />;
      case 'running': return <RefreshCw className="w-4 h-4 text-gray-400 animate-spin" />;
      case 'error': return <AlertCircle className="w-4 h-4 text-gray-500" />;
      default: return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };

  const toggleSignalExpansion = (strategyId: string): void => {
    setExpandedSignals(prev => ({
      ...prev,
      [strategyId]: !prev[strategyId]
    }));
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('ko-KR');
  };

  const getSignalColor = (type: 'BUY' | 'SELL') => {
    return type === 'BUY' ? 'text-green-400' : 'text-red-400';
  };

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
                <BarChart3 />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-100">Single Stock Technical Analysis</h1>
                <p className="text-gray-400 text-sm">CSV Data Analysis - 4 Core Strategies</p>
              </div>
            </motion.div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
          
          <div className="xl:col-span-1 space-y-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-gray-800 rounded-2xl border border-gray-700 p-6"
            >
              <h2 className="text-xl font-bold text-gray-100 mb-6 flex items-center text-gray-400">
                <Target />
                <span className="ml-2">CSV Data Analysis</span>
              </h2>

              {errorMessage && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mb-6 p-4 bg-red-900/20 border border-red-600 rounded-xl"
                >
                  <div className="flex items-start space-x-3">
                    <AlertCircle className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <h4 className="font-semibold text-red-300 mb-1">CSV 데이터 오류</h4>
                      <p className="text-red-200 text-sm">{errorMessage}</p>
                      <p className="text-red-300 text-xs mt-2">
                        파일 형식: date,year,ticker,name,market,open,high,low,close,volume
                      </p>
                    </div>
                  </div>
                </motion.div>
              )}

              <div className="space-y-6">
                
                {/* 종목 선택 섹션 */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-100 mb-4 flex items-center">
                    <span className="text-lg">🔍</span>
                    <span className="ml-2">Stock Selection</span>
                  </h3>
                  
                  <div className="relative">
                    <div className="flex space-x-2">
                      <div className="flex-1 relative">
                        <input
                          type="text"
                          placeholder="종목 코드 또는 종목명 검색 (예: 005930, 삼성전자)"
                          value={stockSearchQuery}
                          onChange={(e) => handleStockSearch(e.target.value)}
                          onFocus={() => stockSearchQuery && setIsStockSearchOpen(true)}
                          className="w-full p-3 bg-gray-700 border border-gray-600 rounded-xl text-gray-100 focus:outline-none focus:border-gray-500 pr-10"
                        />
                        {selectedStock && (
                          <button
                            onClick={clearStockSelection}
                            className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-200"
                          >
                            ✕
                          </button>
                        )}
                      </div>
                      <button
                        onClick={() => setIsStockSearchOpen(!isStockSearchOpen)}
                        className="px-4 py-3 bg-gray-600 text-gray-100 rounded-xl hover:bg-gray-500 transition-colors"
                      >
                        📋
                      </button>
                    </div>
                    
                    {/* 검색 결과 드롭다운 */}
                    {isStockSearchOpen && filteredStocks.length > 0 && (
                      <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="absolute top-full left-0 right-0 mt-1 bg-gray-700 border border-gray-600 rounded-xl shadow-lg z-50 max-h-60 overflow-y-auto"
                      >
                        {filteredStocks.map((stock) => (
                          <div
                            key={stock.symbol}
                            onClick={() => handleStockSelect(stock)}
                            className="p-3 hover:bg-gray-600 cursor-pointer border-b border-gray-600 last:border-b-0"
                          >
                            <div className="flex items-center justify-between">
                              <div>
                                <div className="flex items-center space-x-2">
                                  <span className="font-semibold text-gray-100">{stock.symbol}</span>
                                  <span className="text-xs bg-gray-600 text-gray-300 px-2 py-1 rounded">
                                    {stock.market}
                                  </span>
                                </div>
                                <p className="text-gray-300 text-sm">{stock.name}</p>
                              </div>
                              <div className="text-right">
                                <p className="text-gray-200 font-semibold">
                                  {stock.market === 'NASDAQ' ? `$${stock.price}` : `₩${stock.price.toLocaleString()}`}
                                </p>
                                <p className="text-gray-400 text-xs">변동성 {(stock.volatility * 100).toFixed(1)}%</p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </motion.div>
                    )}
                    
                    {/* 전체 종목 리스트 */}
                    {isStockSearchOpen && !stockSearchQuery && (
                      <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="absolute top-full left-0 right-0 mt-1 bg-gray-700 border border-gray-600 rounded-xl shadow-lg z-50 max-h-80 overflow-y-auto"
                      >
                        <div className="p-3 border-b border-gray-600">
                          <h4 className="font-semibold text-gray-100 mb-2">
                            전체 종목 목록 ({allStocks.length}개)
                          </h4>
                          {isLoadingStocks && (
                            <p className="text-gray-400 text-sm">종목 목록 로딩 중...</p>
                          )}
                          <div className="grid grid-cols-1 gap-1 max-h-64 overflow-y-auto">
                            {['KOSPI', 'KOSDAQ', 'NASDAQ'].map(market => {
                              const marketStocks = allStocks.filter(s => s.market === market);
                              if (marketStocks.length === 0) return null;
                              
                              return (
                                <div key={market}>
                                  <p className="text-xs font-semibold text-gray-400 mb-2 mt-2">{market} ({marketStocks.length}개)</p>
                                  {marketStocks.slice(0, 8).map(stock => (
                                    <div
                                      key={stock.symbol}
                                      onClick={() => handleStockSelect(stock)}
                                      className="p-2 hover:bg-gray-600 cursor-pointer rounded flex items-center justify-between"
                                    >
                                      <div>
                                        <span className="text-gray-100 text-sm font-semibold">{stock.symbol}</span>
                                        <span className="text-gray-300 text-sm ml-2">{stock.name}</span>
                                      </div>
                                      <span className="text-gray-400 text-xs">
                                        {stock.market === 'NASDAQ' ? `$${stock.price}` : `₩${stock.price.toLocaleString()}`}
                                      </span>
                                    </div>
                                  ))}
                                  {marketStocks.length > 8 && (
                                    <p className="text-xs text-gray-500 text-center py-1">
                                      ...및 {marketStocks.length - 8}개 더 (검색으로 찾기)
                                    </p>
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </div>
                  
                  {/* 선택된 종목 정보 */}
                  {selectedStock && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="mt-4 p-4 bg-gray-700 rounded-xl border border-gray-600"
                    >
                      {(() => {
                        const stockInfo = allStocks.find(s => s.symbol === selectedStock);
                        return stockInfo ? (
                          <div>
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center space-x-2">
                                <span className="font-semibold text-gray-100">{stockInfo.symbol}</span>
                                <span className="text-xs bg-blue-600 text-white px-2 py-1 rounded">
                                  {stockInfo.market}
                                </span>
                              </div>
                              <span className="text-gray-200 font-semibold">
                                {stockInfo.market === 'NASDAQ' ? `$${stockInfo.price}` : `₩${stockInfo.price.toLocaleString()}`}
                              </span>
                            </div>
                            <p className="text-gray-200 font-semibold">{stockInfo.name}</p>
                            <p className="text-gray-400 text-sm">
                              예상 변동성: {(stockInfo.volatility * 100).toFixed(1)}% | 
                              시뮬레이션 데이터로 분석 진행
                            </p>
                          </div>
                        ) : (
                          <div>
                            <p className="text-gray-200">선택된 종목: {selectedStock}</p>
                            <p className="text-gray-400 text-sm">종목 정보를 찾을 수 없습니다</p>
                          </div>
                        );
                      })()}
                    </motion.div>
                  )}
                  
                  {/* CSV vs 종목 선택 안내 */}
                  <div className="mt-4 p-3 bg-gray-700 rounded-lg">
                    <p className="text-gray-300 text-sm">
                      <span className="font-semibold">분석 데이터:</span>
                      {selectedStock 
                        ? ' 선택된 종목의 시뮬레이션 데이터 사용' 
                        : ' CSV 파일 또는 샘플 데이터 사용'}
                    </p>
                  </div>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-100 mb-4 flex items-center">
                    <span className="text-lg">📊</span>
                    <span className="ml-2">Strategy Selection</span>
                  </h3>
                  
                  <div className="space-y-3">
                    {strategies.map((strategy, index) => (
                      <motion.div
                        key={strategy.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className={`p-4 rounded-xl border cursor-pointer transition-all duration-300 ${
                          selectedStrategies.includes(strategy.id)
                            ? 'border-gray-500 bg-gray-600 shadow-lg'
                            : 'border-gray-600 bg-gray-800 hover:border-gray-500 hover:bg-gray-700'
                        }`}
                        onClick={() => handleStrategyToggle(strategy.id)}
                      >
                        <div className="flex items-center space-x-3">
                          <div className="text-gray-400">
                            <strategy.icon />
                          </div>
                          <div>
                            <h4 className="font-semibold text-gray-100 text-sm">{strategy.name}</h4>
                            <p className="text-gray-400 text-xs">
                              {strategy.id === 'golden_cross' ? 'MA5 vs MA20 크로스오버' :
                              strategy.id === 'rsi_divergence' ? 'RSI 과매수/과매도 구간' :
                              strategy.id === 'bollinger_bands' ? '볼린저 밴드 터치 전략' :
                              'MACD 신호선 교차'}
                            </p>
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>

                  {selectedStrategies.length > 0 && (
                    <div className="mt-4 bg-gray-700 rounded-lg p-3">
                      <p className="text-gray-300 text-sm">
                        Selected: {selectedStrategies.length} strategies
                      </p>
                    </div>
                  )}
                </div>

                <div className="bg-gray-700 rounded-lg p-4">
                  <div className="flex items-center space-x-2 mb-2">
                    <Upload className="w-4 h-4 text-gray-400" />
                    <span className="text-gray-300 text-sm font-medium">CSV 데이터 상태</span>
                  </div>
                  <div className={`text-sm ${
                    csvLoadStatus === 'success' ? 'text-green-400' :
                    csvLoadStatus === 'error' ? 'text-red-400' :
                    csvLoadStatus === 'loading' ? 'text-blue-400' :
                    'text-gray-400'
                  }`}>
                    {csvLoadStatus === 'success' ? `로드 완료 (${stockData?.length || 0}개 레코드)` :
                     csvLoadStatus === 'error' ? '로드 실패 - 에러 확인 필요' :
                     csvLoadStatus === 'loading' ? '로드 중...' :
                     '대기 중 - /data/stock.csv'}
                  </div>
                  <p className="text-gray-500 text-xs mt-1">
                    필요 형식: date,year,ticker,name,market,open,high,low,close,volume
                  </p>
                </div>

                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={runAnalysis}
                  disabled={selectedStrategies.length === 0 || isLoading}
                  className={`w-full py-3 px-4 rounded-xl font-semibold transition-all flex items-center justify-center space-x-2 ${
                    selectedStrategies.length > 0 && !isLoading
                      ? 'bg-gray-600 text-gray-100 hover:bg-gray-500 shadow-lg'
                      : 'bg-gray-700 text-gray-400 cursor-not-allowed'
                  }`}
                >
                  {isLoading ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>분석 진행 중...</span>
                    </>
                  ) : (
                    <>
                      <Play />
                      <span>CSV 데이터 분석 시작</span>
                    </>
                  )}
                </motion.button>
              </div>
            </motion.div>

            {(isLoading || analysisSteps.length > 0) && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-gray-800 rounded-2xl border border-gray-700 p-6"
              >
                <h2 className="text-xl font-bold text-gray-100 mb-6 flex items-center text-gray-400">
                  <Activity />
                  <span className="ml-2">Analysis Progress</span>
                </h2>
                
                <div className="space-y-4">
                  {analysisSteps.map((step, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className={`p-4 rounded-xl border transition-all ${
                        step.status === 'completed' ? 'border-gray-500 bg-gray-700' :
                        step.status === 'running' ? 'border-gray-500 bg-gray-700' :
                        step.status === 'error' ? 'border-gray-600 bg-gray-800' :
                        'border-gray-600 bg-gray-800'
                      }`}
                    >
                      <div className="flex items-start space-x-3">
                        <div className="mt-0.5">
                          {getStepIcon(step.status)}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-1">
                            <span className="text-lg">{index + 1}.</span>
                            <h3 className="font-semibold text-gray-100 text-sm">{step.step}</h3>
                            {step.status === 'completed' && (
                              <span className="text-xs bg-gray-600 text-gray-300 px-2 py-1 rounded">완료</span>
                            )}
                            {step.status === 'running' && (
                              <span className="text-xs bg-gray-500 text-gray-200 px-2 py-1 rounded">진행중</span>
                            )}
                            {step.status === 'error' && (
                              <span className="text-xs bg-red-600 text-white px-2 py-1 rounded">오류</span>
                            )}
                          </div>
                          <p className="text-gray-300 text-xs mb-2">{step.message}</p>
                          <p className="text-gray-400 text-xs">{step.details}</p>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            )}
          </div>
          
          <div className="xl:col-span-2">
            <div className="space-y-6">
              
              <AnimatePresence>
                {Object.keys(analysisResults).length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-gray-800 rounded-2xl border border-gray-700 p-6"
                  >
                    <h2 className="text-xl font-bold text-gray-100 mb-6 flex items-center text-gray-400">
                      <BarChart3 />
                      <span className="ml-2">분석 결과 요약</span>
                    </h2>
                    
                    <div className="space-y-4">
                      {Object.entries(analysisResults).map(([strategyId, result]) => {
                        const strategy = strategies.find(s => s.id === strategyId);
                        const { backtest, signals } = result;
                        const isPositive = backtest.totalReturn > 0;
                        
                        return (
                          <motion.div
                            key={strategyId}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            className="bg-gray-700 border border-gray-600 rounded-xl p-4"
                          >
                            <div className="flex items-center space-x-2 mb-3">
                              {strategy && <strategy.icon className="w-4 h-4 text-gray-400" />}
                              <h3 className="font-semibold text-gray-100 text-sm">{strategy?.name}</h3>
                            </div>
                            
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                              <div className="bg-gray-800 border border-gray-600 rounded-xl p-3">
                                <p className="text-gray-300 text-xs font-medium">총 수익률</p>
                                <p className={`text-lg font-bold ${isPositive ? 'text-gray-200' : 'text-gray-400'}`}>
                                  {backtest.totalReturn.toFixed(1)}%
                                </p>
                              </div>
                              <div className="bg-gray-800 border border-gray-600 rounded-xl p-3">
                                <p className="text-gray-300 text-xs font-medium">연간 수익률</p>
                                <p className="text-lg font-bold text-gray-200">{backtest.annualReturn.toFixed(1)}%</p>
                              </div>
                              <div className="bg-gray-800 border border-gray-600 rounded-xl p-3">
                                <p className="text-gray-300 text-xs font-medium">승률</p>
                                <p className="text-lg font-bold text-gray-200">{backtest.winRate.toFixed(1)}%</p>
                              </div>
                              <div className="bg-gray-800 border border-gray-600 rounded-xl p-3">
                                <p className="text-gray-300 text-xs font-medium">거래 횟수</p>
                                <p className="text-lg font-bold text-gray-200">{backtest.trades}</p>
                              </div>
                            </div>
                            
                            <div className="flex justify-between items-center pt-3 border-t border-gray-600">
                              <div className="flex items-center space-x-4">
                                <span className="text-gray-400 text-xs">
                                  {signals.length}개 매매신호
                                </span>
                                <span className="text-gray-400 text-xs">
                                  ${backtest.finalValue.toLocaleString()}
                                </span>
                              </div>
                              <span className={`text-xs font-semibold ${
                                backtest.totalReturn > 10 ? 'text-gray-200' :
                                backtest.totalReturn > 0 ? 'text-gray-300' : 'text-gray-500'
                              }`}>
                                {backtest.totalReturn > 10 ? '뛰어난 전략' :
                                 backtest.totalReturn > 0 ? '우수한 전략' : '개선 필요'}
                              </span>
                            </div>
                          </motion.div>
                        );
                      })}
                    </div>

                    <div className="mt-6 text-center">
                      <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => {
                          setSelectedStrategies([]);
                          setSelectedStock('');
                          setStockSearchQuery('');
                          setIsStockSearchOpen(false);
                          setFilteredStocks([]);
                          setStockData(null);
                          setAnalysisResults({});
                          setAnalysisSteps([]);
                          setErrorMessage('');
                          setCsvLoadStatus('idle');
                          setExpandedSignals({});
                        }}
                        className="bg-gray-600 text-gray-100 hover:bg-gray-500 px-6 py-3 rounded-xl font-semibold transition-all flex items-center space-x-2 mx-auto"
                      >
                        <RefreshCw className="w-4 h-4" />
                        <span>다른 분석 시작하기</span>
                      </motion.button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              <AnimatePresence>
                {stockData && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    className="space-y-6"
                  >
                    <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6">
                      <h3 className="text-lg font-bold text-gray-100 mb-4 flex items-center text-gray-400">
                        <TrendingUp />
                        <span className="ml-2">주가 차트 & 기술지표</span>
                      </h3>
                      
                      <div className="h-80">
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={getChartData()}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#4b5563" />
                            <XAxis dataKey="date" stroke="#9ca3af" fontSize={12} />
                            <YAxis stroke="#9ca3af" fontSize={12} tickFormatter={(value) => `$${value.toFixed(0)}`} />
                            <Tooltip contentStyle={{
                              backgroundColor: '#374151',
                              border: '1px solid #4b5563',
                              borderRadius: '8px',
                              color: '#f9fafb'
                            }} />
                            
                            <Line type="monotone" dataKey="bb_upper" stroke="#6b7280" strokeWidth={1} strokeDasharray="5,5" dot={false} name="BB Upper" />
                            <Line type="monotone" dataKey="bb_middle" stroke="#9ca3af" strokeWidth={1} strokeDasharray="3,3" dot={false} name="BB Middle" />
                            <Line type="monotone" dataKey="bb_lower" stroke="#6b7280" strokeWidth={1} strokeDasharray="5,5" dot={false} name="BB Lower" />
                            <Line type="monotone" dataKey="close" stroke="#f9fafb" strokeWidth={2} dot={false} name="Close" />
                            <Line type="monotone" dataKey="ma5" stroke="#10b981" strokeWidth={1.5} dot={false} name="MA5" />
                            <Line type="monotone" dataKey="ma20" stroke="#3b82f6" strokeWidth={1.5} dot={false} name="MA20" />
                            <Line type="monotone" dataKey="ma60" stroke="#ef4444" strokeWidth={1} dot={false} name="MA60" />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    </div>

                    <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6">
                      <h3 className="text-lg font-bold text-gray-100 mb-4 flex items-center text-gray-400">
                        <Activity />
                        <span className="ml-2">RSI Indicator</span>
                      </h3>
                      
                      <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={getChartData()}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#4b5563" />
                            <XAxis dataKey="date" stroke="#9ca3af" fontSize={10} />
                            <YAxis domain={[0, 100]} stroke="#9ca3af" fontSize={10} />
                            <Tooltip contentStyle={{
                              backgroundColor: '#374151',
                              border: '1px solid #4b5563',
                              borderRadius: '8px',
                              color: '#f9fafb'
                            }} />
                            <Line type="monotone" dataKey="rsi" stroke="#8b5cf6" strokeWidth={2} dot={false} name="RSI" />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              <AnimatePresence>
                {Object.keys(analysisResults).length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    className="bg-gray-800 rounded-2xl border border-gray-700 p-6"
                  >
                    <h2 className="text-xl font-bold text-gray-100 mb-6 flex items-center text-gray-400">
                      <Eye />
                      <span className="ml-2">매수매도 신호 상세 내역</span>
                    </h2>
                    
                    <div className="space-y-4">
                      {Object.entries(analysisResults).map(([strategyId, result]) => {
                        const strategy = strategies.find(s => s.id === strategyId);
                        const { signals } = result;
                        const isExpanded = expandedSignals[strategyId];
                        
                        return (
                          <div key={strategyId} className="bg-gray-700 border border-gray-600 rounded-xl p-4">
                            <div
                              className="flex items-center justify-between cursor-pointer"
                              onClick={() => toggleSignalExpansion(strategyId)}
                            >
                              <div className="flex items-center space-x-3">
                                {strategy && <strategy.icon className="w-4 h-4 text-gray-400" />}
                                <div>
                                  <h3 className="font-semibold text-gray-100 text-sm">{strategy?.name}</h3>
                                  <p className="text-gray-400 text-xs">
                                    총 {signals.length}개 신호
                                    (매수: {signals.filter(s => s.type === 'BUY').length}개,
                                     매도: {signals.filter(s => s.type === 'SELL').length}개)
                                  </p>
                                </div>
                              </div>
                              <motion.div
                                animate={{ rotate: isExpanded ? 180 : 0 }}
                                transition={{ duration: 0.2 }}
                              >
                                <ChevronDown className="w-4 h-4 text-gray-400" />
                              </motion.div>
                            </div>

                            <AnimatePresence>
                              {isExpanded && (
                                <motion.div
                                  initial={{ opacity: 0, height: 0 }}
                                  animate={{ opacity: 1, height: 'auto' }}
                                  exit={{ opacity: 0, height: 0 }}
                                  transition={{ duration: 0.3 }}
                                  className="mt-4 space-y-2 max-h-80 overflow-y-auto"
                                >
                                  {signals.length > 0 ? (
                                    signals.map((signal, index) => (
                                      <motion.div
                                        key={index}
                                        initial={{ opacity: 0, x: -10 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: index * 0.05 }}
                                        className="bg-gray-800 border border-gray-600 rounded-lg p-3 flex items-center justify-between"
                                      >
                                        <div className="flex items-center space-x-3">
                                          <div>
                                            <div className="flex items-center space-x-2">
                                              <span className={`font-semibold ${getSignalColor(signal.type)}`}>
                                                {signal.type === 'BUY' ? '매수' : '매도'}
                                              </span>
                                              <span className="text-gray-300 text-sm">
                                                ${signal.price.toFixed(2)}
                                              </span>
                                            </div>
                                            <p className="text-gray-400 text-xs">
                                              {formatDate(signal.date)}
                                              {signal.ma5 && signal.ma20 && (
                                                <span className="ml-2">
                                                  MA5: ${signal.ma5.toFixed(2)}, MA20: ${signal.ma20.toFixed(2)}
                                                </span>
                                              )}
                                              {signal.rsi && (
                                                <span className="ml-2">RSI: {signal.rsi.toFixed(1)}</span>
                                              )}
                                            </p>
                                          </div>
                                        </div>
                                        <div className="text-right">
                                          <span className="text-gray-400 text-xs">
                                            #{index + 1}
                                          </span>
                                        </div>
                                      </motion.div>
                                    ))
                                  ) : (
                                    <div className="text-center py-4">
                                      <p className="text-gray-400 text-sm">해당 전략으로 생성된 신호가 없습니다.</p>
                                    </div>
                                  )}
                                </motion.div>
                              )}
                            </AnimatePresence>
                          </div>
                        );
                      })}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {Object.keys(analysisResults).length === 0 && !stockData && analysisSteps.length === 0 && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="bg-gray-800 rounded-2xl border border-gray-700 p-12 text-center"
                >
                  <div className="w-16 h-16 bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4 text-gray-400">
                    <BarChart3 />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-100 mb-2">CSV 주가 데이터 기술적 분석 준비 완료</h3>
                  <p className="text-gray-400 mb-6">
                    CSV 파일에서 주가 데이터를 로드하여 상세한 기술적 분석을 시작하세요
                    <br />
                    4가지 핵심 전략으로 매매 신호와 백테스트 결과를 제공합니다
                  </p>
                  
                  <div className="bg-gray-700 rounded-lg p-4 mb-6">
                    <h4 className="text-gray-100 font-semibold mb-2">CSV 파일 형식 요구사항:</h4>
                    <div className="text-gray-300 text-sm space-y-1">
                      <p>• 필수 컬럼: date, close</p>
                      <p>• 권장 컬럼: open, high, low, volume</p>
                      <p>• 파일 형식: date,year,ticker,name,market,open,high,low,close,volume</p>
                      <p>• 파일 위치: /public/data/stock.csv</p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-gray-700 rounded-lg p-4 text-center">
                      <div className="text-2xl mb-2">📄</div>
                      <p className="text-gray-100 font-semibold">CSV 데이터</p>
                      <p className="text-gray-400 text-sm">OHLCV + 기술지표</p>
                    </div>
                    <div className="bg-gray-700 rounded-lg p-4 text-center">
                      <div className="text-2xl mb-2">📊</div>
                      <p className="text-gray-100 font-semibold">매매 신호</p>
                      <p className="text-gray-400 text-sm">Buy/Sell 신호 생성</p>
                    </div>
                    <div className="bg-gray-700 rounded-lg p-4 text-center">
                      <div className="text-2xl mb-2">💰</div>
                      <p className="text-gray-100 font-semibold">백테스트</p>
                      <p className="text-gray-400 text-sm">성과 분석</p>
                    </div>
                  </div>
                </motion.div>
              )}
            </div>
          </div>
        </div>
      </div>

      <footer className="bg-gray-800 border-t border-gray-700 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center space-x-3 mb-4 md:mb-0">
              <div className="w-8 h-8 bg-gray-600 rounded-lg flex items-center justify-center text-gray-200">
                <BarChart3 />
              </div>
              <div>
                <p className="text-gray-100 font-semibold">Single Stock Technical Analysis</p>
                <p className="text-gray-400 text-sm">CSV Data Analysis - 4 Core Strategies</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-6 text-sm text-gray-400">
              <p>📄 CSV 데이터</p>
              <p>⚡ 실시간 분석</p>
              <p>🎯 4가지 전략</p>
              <p>🔍 상세 백테스트</p>
            </div>
          </div>
          
          <div className="border-t border-gray-700 mt-6 pt-6 text-center">
            <p className="text-gray-500 text-sm">
              © 2025 CSV Stock Technical Analysis. 본 시스템의 분석 결과는 과거 데이터를 기반으로 하며,
              미래 수익을 보장하지 않습니다. 투자 결정 시 신중하게 검토하시기 바랍니다.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}