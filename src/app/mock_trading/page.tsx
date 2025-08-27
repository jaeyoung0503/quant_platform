'use client';

import React, { useState, useEffect } from 'react';
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
  Cell
} from 'recharts';

// 타입 정의들
interface AccountInfo {
  balance: number;
  totalAsset: number;
  buyingPower: number;
  profitLoss: number;
  profitRate: number;
}

interface PortfolioItem {
  stockCode: string;
  stockName: string;
  quantity: number;
  avgPrice: number;
  currentPrice: number;
  marketValue: number;
  profitLoss: number;
  profitRate: number;
}

interface OrderInfo {
  id: string;
  stockCode: string;
  stockName: string;
  orderType: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  status: 'PENDING' | 'COMPLETED' | 'CANCELLED';
  orderTime: string;
}

interface Transaction {
  id: string;
  stockCode: string;
  stockName: string;
  type: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  amount: number;
  fee: number;
  time: string;
}

interface StockInfo {
  code: string;
  name: string;
  price: number;
  change: number;
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

const DollarSign = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <line x1="12" y1="1" x2="12" y2="23"></line>
    <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
  </svg>
);

const Activity = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <polyline points="22,12 18,12 15,21 9,3 6,12 2,12"></polyline>
  </svg>
);

const ShoppingCart = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <circle cx="9" cy="21" r="1"></circle>
    <circle cx="20" cy="21" r="1"></circle>
    <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path>
  </svg>
);

const Wallet = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <path d="M21 12V7H5a2 2 0 0 1 0-4h14v4"></path>
    <path d="M3 5v14a2 2 0 0 0 2 2h16v-5"></path>
    <path d="M18 12a2 2 0 0 0 0 4h4v-4Z"></path>
  </svg>
);

const RefreshCw = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <polyline points="23,4 23,10 17,10"></polyline>
    <polyline points="1,20 1,14 7,14"></polyline>
    <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"></path>
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
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1 1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
  </svg>
);

const Clock = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <circle cx="12" cy="12" r="10"></circle>
    <polyline points="12,6 12,12 16,14"></polyline>
  </svg>
);

const CheckCircle = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
    <polyline points="22,4 12,14.01 9,11.01"></polyline>
  </svg>
);

const AlertTriangle = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
    <line x1="12" y1="9" x2="12" y2="13"></line>
    <line x1="12" y1="17" x2="12.01" y2="17"></line>
  </svg>
);

const Target = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <circle cx="12" cy="12" r="10"></circle>
    <circle cx="12" cy="12" r="6"></circle>
    <circle cx="12" cy="12" r="2"></circle>
  </svg>
);

const Search = ({ className = "w-4 h-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={className}>
    <circle cx="11" cy="11" r="8"></circle>
    <path d="M21 21l-4.35-4.35"></path>
  </svg>
);

// 모의 데이터 생성 함수들
const generateMockAccountInfo = (): AccountInfo => ({
  balance: 8250000,
  totalAsset: 10500000,
  buyingPower: 8250000,
  profitLoss: 500000,
  profitRate: 5.0
});

const generateMockPortfolio = (): PortfolioItem[] => [
  {
    stockCode: '005930',
    stockName: '삼성전자',
    quantity: 15,
    avgPrice: 68000,
    currentPrice: 70000,
    marketValue: 1050000,
    profitLoss: 30000,
    profitRate: 2.94
  },
  {
    stockCode: '000660',
    stockName: 'SK하이닉스',
    quantity: 8,
    avgPrice: 120000,
    currentPrice: 125000,
    marketValue: 1000000,
    profitLoss: 40000,
    profitRate: 4.17
  },
  {
    stockCode: '035420',
    stockName: 'NAVER',
    quantity: 3,
    avgPrice: 180000,
    currentPrice: 185000,
    marketValue: 555000,
    profitLoss: 15000,
    profitRate: 2.78
  }
];

const generateMockOrders = (): OrderInfo[] => [
  {
    id: '1',
    stockCode: '005930',
    stockName: '삼성전자',
    orderType: 'BUY',
    quantity: 10,
    price: 69000,
    status: 'COMPLETED',
    orderTime: '2025-01-15 09:15:30'
  },
  {
    id: '2',
    stockCode: '000660',
    stockName: 'SK하이닉스',
    orderType: 'SELL',
    quantity: 5,
    price: 125000,
    status: 'PENDING',
    orderTime: '2025-01-15 14:22:15'
  },
  {
    id: '3',
    stockCode: '035420',
    stockName: 'NAVER',
    orderType: 'BUY',
    quantity: 2,
    price: 185000,
    status: 'COMPLETED',
    orderTime: '2025-01-15 13:45:12'
  }
];

const generateMockTransactions = (): Transaction[] => [
  {
    id: '1',
    stockCode: '005930',
    stockName: '삼성전자',
    type: 'BUY',
    quantity: 15,
    price: 68000,
    amount: 1020000,
    fee: 153,
    time: '2025-01-15 09:15:30'
  },
  {
    id: '2',
    stockCode: '000660',
    stockName: 'SK하이닉스',
    type: 'BUY',
    quantity: 8,
    price: 120000,
    amount: 960000,
    fee: 144,
    time: '2025-01-14 14:20:15'
  },
  {
    id: '3',
    stockCode: '035420',
    stockName: 'NAVER',
    type: 'BUY',
    quantity: 3,
    price: 180000,
    amount: 540000,
    fee: 81,
    time: '2025-01-13 11:30:45'
  }
];

const generatePriceHistory = (days: number = 30) => {
  const data = [];
  let price = 70000;
  let ma5 = 70000;
  let ma20 = 70000;
  const today = new Date();
  
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);
    
    price += (Math.random() - 0.5) * 2000;
    price = Math.max(60000, Math.min(80000, price));
    
    // 이동평균선 계산 (단순화)
    ma5 = ma5 * 0.8 + price * 0.2;
    ma20 = ma20 * 0.95 + price * 0.05;
    
    data.push({
      date: date.toISOString().split('T')[0],
      price: Math.round(price),
      ma5: Math.round(ma5),
      ma20: Math.round(ma20),
      volume: Math.floor(Math.random() * 1000000) + 500000
    });
  }
  return data;
};

// KOSPI 지수 데이터 생성
const generateKospiHistory = (days: number = 30) => {
  const data = [];
  let index = 2500;
  const today = new Date();
  
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);
    
    index += (Math.random() - 0.5) * 30;
    index = Math.max(2300, Math.min(2700, index));
    
    data.push({
      date: date.toISOString().split('T')[0],
      kospi: Math.round(index * 100) / 100
    });
  }
  return data;
};

// 주요 종목 리스트
const stockDatabase = [
  { code: '005930', name: '삼성전자', price: 70000, change: 2.94 },
  { code: '000660', name: 'SK하이닉스', price: 125000, change: -1.2 },
  { code: '035420', name: 'NAVER', price: 185000, change: 0.8 },
  { code: '051910', name: 'LG화학', price: 400000, change: 1.5 },
  { code: '006400', name: '삼성SDI', price: 150000, change: -0.5 },
  { code: '035720', name: '카카오', price: 50000, change: 3.2 },
  { code: '207940', name: '삼성바이오로직스', price: 800000, change: 0.9 },
  { code: '373220', name: 'LG에너지솔루션', price: 400000, change: -0.3 }
];

export default function KiwoomTradingPlatform(): JSX.Element {
  const [selectedTab, setSelectedTab] = useState<'portfolio' | 'trading' | 'orders' | 'analysis'>('portfolio');
  const [selectedStock, setSelectedStock] = useState<string>('005930');
  const [orderType, setOrderType] = useState<'BUY' | 'SELL'>('BUY');
  const [orderQuantity, setOrderQuantity] = useState<string>('10');
  const [orderPrice, setOrderPrice] = useState<string>('70000');
  const [stockSearchQuery, setStockSearchQuery] = useState<string>('');
  const [searchResults, setSearchResults] = useState<StockInfo[]>([]);
  const [showSearchResults, setShowSearchResults] = useState<boolean>(false);
  const [selectedStockInfo, setSelectedStockInfo] = useState<StockInfo | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [marketStatus, setMarketStatus] = useState<'OPEN' | 'CLOSED'>('OPEN');
  const [autoRefresh, setAutoRefresh] = useState<boolean>(true);
  const [showOrderConfirm, setShowOrderConfirm] = useState<boolean>(false);
  const [lastUpdate, setLastUpdate] = useState<string>(new Date().toLocaleTimeString());
  
  const accountInfo = generateMockAccountInfo();
  const portfolio = generateMockPortfolio();
  const orders = generateMockOrders();
  const transactions = generateMockTransactions();
  const priceHistory = generatePriceHistory();
  const kospiHistory = generateKospiHistory();

  // 종목 검색
  const handleStockSearch = (query: string) => {
    setStockSearchQuery(query);
    if (query.length > 0) {
      const filtered = stockDatabase.filter(stock =>
        stock.code.includes(query) || 
        stock.name.toLowerCase().includes(query.toLowerCase())
      );
      setSearchResults(filtered);
      setShowSearchResults(true);
    } else {
      setSearchResults([]);
      setShowSearchResults(false);
    }
  };

  // 종목 선택
  const handleStockSelect = (stock: StockInfo) => {
    setSelectedStock(stock.code);
    setSelectedStockInfo(stock);
    setOrderPrice(stock.price.toString());
    setStockSearchQuery(`${stock.code} - ${stock.name}`);
    setShowSearchResults(false);
  };

  // 자동 새로고침 효과
  useEffect(() => {
    if (!autoRefresh) return;
    
    const interval = setInterval(() => {
      setLastUpdate(new Date().toLocaleTimeString());
      setIsLoading(true);
      setTimeout(() => setIsLoading(false), 500);
    }, 5000);

    return () => clearInterval(interval);
  }, [autoRefresh]);

  // 초기 종목 정보 설정
  useEffect(() => {
    const initialStock = stockDatabase.find(s => s.code === selectedStock);
    if (initialStock) {
      setSelectedStockInfo(initialStock);
      setStockSearchQuery(`${initialStock.code} - ${initialStock.name}`);
    }
  }, [selectedStock]);

  const handleOrder = async () => {
    setIsLoading(true);
    
    try {
      const quantity = parseInt(orderQuantity);
      const price = parseInt(orderPrice);
      
      if (quantity <= 0 || price <= 0) {
        alert('수량과 가격은 양수여야 합니다.');
        return;
      }
      
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      alert(`${orderType === 'BUY' ? '매수' : '매도'} 주문이 완료되었습니다.\n` +
            `종목: ${selectedStockInfo?.name} (${selectedStock})\n` +
            `수량: ${quantity.toLocaleString()}주\n` +
            `가격: ₩${price.toLocaleString()}`);
      
      setOrderQuantity('10');
      setShowOrderConfirm(false);
      
    } catch (error) {
      alert('주문 처리 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const formatCurrency = (amount: number): string => {
    return `₩${amount.toLocaleString()}`;
  };

  const formatPercent = (rate: number): string => {
    return `${rate > 0 ? '+' : ''}${rate.toFixed(2)}%`;
  };

  const getChangeColor = (change: number): string => {
    if (change > 0) return 'text-red-400';
    if (change < 0) return 'text-blue-400';
    return 'text-gray-300';
  };

  const getStatusText = (status: string): string => {
    switch (status) {
      case 'COMPLETED': return '체결완료';
      case 'PENDING': return '주문접수';
      case 'CANCELLED': return '주문취소';
      default: return '알 수 없음';
    }
  };

  return (
    <div className="min-h-screen bg-gray-900">
      {/* 헤더 */}
      <header className="bg-gray-800 border-b border-gray-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <motion.div 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center space-x-3"
            >
              <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white">
                <BarChart3 />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-100">키움 모의투자 시스템</h1>
                <p className="text-gray-400 text-sm">Kiwoom Mock Trading Platform</p>
              </div>
            </motion.div>
            
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-gray-300 text-sm">시장 상태</p>
                <div className="flex items-center space-x-2">
                  <div className={`w-2 h-2 rounded-full ${marketStatus === 'OPEN' ? 'bg-green-400' : 'bg-red-400'}`}></div>
                  <p className="text-gray-100 font-semibold">
                    {marketStatus === 'OPEN' ? '개장' : '폐장'}
                  </p>
                </div>
              </div>
              
              <div className="text-right">
                <p className="text-gray-300 text-sm">마지막 업데이트</p>
                <p className="text-gray-100 font-mono text-sm">{lastUpdate}</p>
              </div>
              
              <div className="text-right">
                <p className="text-gray-300 text-sm">자동새로고침</p>
                <button
                  onClick={() => setAutoRefresh(!autoRefresh)}
                  className={`text-sm px-3 py-1 rounded-lg transition-all ${
                    autoRefresh ? 'bg-green-600 text-white' : 'bg-gray-600 text-gray-300'
                  }`}
                >
                  {autoRefresh ? 'ON' : 'OFF'}
                </button>
              </div>
              
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => {
                  setIsLoading(true);
                  setLastUpdate(new Date().toLocaleTimeString());
                  setTimeout(() => setIsLoading(false), 1000);
                }}
                className="p-2 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 transition-all"
              >
                <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
              </motion.button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 xl:grid-cols-4 gap-8">
          
          {/* 왼쪽 사이드바 */}
          <div className="xl:col-span-1">
            <div className="space-y-6">
              
              {/* 계좌 요약 */}
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-gray-800 rounded-2xl border border-gray-700 p-6"
              >
                <h2 className="text-lg font-bold text-gray-100 mb-4 flex items-center">
                  <Wallet className="w-5 h-5 mr-2 text-blue-400" />
                  계좌 정보
                </h2>
                
                <div className="space-y-4">
                  <div className="space-y-3">
                    <div className="bg-gray-700 border border-gray-600 rounded-xl p-4">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-gray-300 text-sm font-medium">총 자산</p>
                        <DollarSign className="w-4 h-4 text-gray-400" />
                      </div>
                      <p className="text-gray-100 font-bold text-lg">
                        {formatCurrency(accountInfo.totalAsset)}
                      </p>
                    </div>
                    
                    <div className="bg-gray-700 border border-gray-600 rounded-xl p-4">
                      <p className="text-gray-300 text-sm font-medium mb-2">현금 잔고</p>
                      <p className="text-gray-100 font-bold text-lg">
                        {formatCurrency(accountInfo.balance)}
                      </p>
                    </div>
                    
                    <div className="bg-gray-700 border border-gray-600 rounded-xl p-4">
                      <p className="text-gray-300 text-sm font-medium mb-2">평가손익</p>
                      <div className="flex items-center justify-between">
                        <p className={`font-bold text-lg ${getChangeColor(accountInfo.profitLoss)}`}>
                          {formatCurrency(accountInfo.profitLoss)}
                        </p>
                        <p className={`font-semibold ${getChangeColor(accountInfo.profitRate)}`}>
                          {formatPercent(accountInfo.profitRate)}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>

              {/* 주문 입력 */}
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="bg-gray-800 rounded-2xl border border-gray-700 p-6"
              >
                <h2 className="text-lg font-bold text-gray-100 mb-4 flex items-center">
                  <ShoppingCart className="w-5 h-5 mr-2 text-green-400" />
                  주문 입력
                </h2>
                
                <div className="space-y-3">
                  {/* 매수/매도 선택 */}
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setOrderType('BUY')}
                      className={`flex-1 py-2 px-3 rounded-xl font-semibold transition-all ${
                        orderType === 'BUY'
                          ? 'bg-red-600 text-white shadow-lg border border-red-500'
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600 border border-gray-600'
                      }`}
                    >
                      매수
                    </button>
                    <button
                      onClick={() => setOrderType('SELL')}
                      className={`flex-1 py-2 px-3 rounded-xl font-semibold transition-all ${
                        orderType === 'SELL'
                          ? 'bg-blue-600 text-white shadow-lg border border-blue-500'
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600 border border-gray-600'
                      }`}
                    >
                      매도
                    </button>
                  </div>

                  {/* 종목 검색 */}
                  <div className="relative">
                    <label className="block text-gray-300 text-sm font-medium mb-2">종목 검색</label>
                    <div className="relative">
                      <input
                        type="text"
                        value={stockSearchQuery}
                        onChange={(e) => handleStockSearch(e.target.value)}
                        className="w-full p-2 bg-gray-700 border border-gray-600 rounded-xl text-gray-100 focus:outline-none focus:border-blue-500 transition-all pr-10"
                        placeholder="종목코드 또는 종목명 입력"
                      />
                      <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    </div>
                    
                    {/* 검색 결과 드롭다운 */}
                    <AnimatePresence>
                      {showSearchResults && searchResults.length > 0 && (
                        <motion.div
                          initial={{ opacity: 0, y: -10 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -10 }}
                          className="absolute z-10 w-full mt-1 bg-gray-700 border border-gray-600 rounded-xl shadow-lg max-h-40 overflow-y-auto"
                        >
                          {searchResults.map((stock) => (
                            <button
                              key={stock.code}
                              onClick={() => handleStockSelect(stock)}
                              className="w-full text-left p-2 hover:bg-gray-600 transition-colors border-b border-gray-600 last:border-b-0"
                            >
                              <div className="flex items-center justify-between">
                                <div>
                                  <p className="text-gray-100 font-semibold text-sm">{stock.name}</p>
                                  <p className="text-gray-400 text-xs">{stock.code}</p>
                                </div>
                                <div className="text-right">
                                  <p className="text-gray-100 font-mono text-xs">
                                    {formatCurrency(stock.price)}
                                  </p>
                                  <p className={`text-xs font-semibold ${getChangeColor(stock.change)}`}>
                                    {formatPercent(stock.change)}
                                  </p>
                                </div>
                              </div>
                            </button>
                          ))}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                      
                  {/* 수량 입력 */}
                  <div>
                    <label className="block text-gray-300 text-sm font-medium mb-2">수량</label>
                    <input
                      type="number"
                      value={orderQuantity}
                      onChange={(e) => setOrderQuantity(e.target.value)}
                      className="w-full p-2 bg-gray-700 border border-gray-600 rounded-xl text-gray-100 focus:outline-none focus:border-blue-500 transition-all"
                      placeholder="수량을 입력하세요"
                      min="1"
                    />
                  </div>

                  {/* 가격 입력 */}
                  <div>
                    <label className="block text-gray-300 text-sm font-medium mb-2">가격</label>
                    <input
                      type="text"
                      value={orderPrice}
                      onChange={(e) => setOrderPrice(e.target.value.replace(/[^0-9]/g, ''))}
                      className="w-full p-2 bg-gray-700 border border-gray-600 rounded-xl text-gray-100 focus:outline-none focus:border-blue-500 transition-all"
                      placeholder="가격을 입력하세요"
                    />
                  </div>

                  {/* 주문 금액 표시 */}
                  <div className="bg-gray-700 border border-gray-600 rounded-xl p-3">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-400 text-sm">주문금액</span>
                      <span className="text-gray-100 font-bold">
                        {formatCurrency((parseInt(orderQuantity) || 0) * (parseInt(orderPrice) || 0))}
                      </span>
                    </div>
                  </div>

                  {/* 주문 버튼 */}
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setShowOrderConfirm(true)}
                    disabled={isLoading || !orderQuantity || !orderPrice}
                    className={`w-full py-2 px-3 rounded-xl font-semibold transition-all flex items-center justify-center space-x-2 ${
                      orderType === 'BUY'
                        ? 'bg-red-600 hover:bg-red-700 text-white shadow-lg border border-red-500'
                        : 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg border border-blue-500'
                    } ${isLoading || !orderQuantity || !orderPrice ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    {isLoading ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        <span>처리중...</span>
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4" />
                        <span>{orderType === 'BUY' ? '매수' : '매도'} 주문</span>
                      </>
                    )}
                  </motion.button>
                </div>
              </motion.div>
            </div>
          </div>

          {/* 메인 컨텐츠 영역 */}
          <div className="xl:col-span-3">
            {/* 탭 네비게이션 */}
            <div className="flex space-x-1 bg-gray-800 rounded-xl p-1 mb-6 border border-gray-700">
              {[
                { id: 'portfolio', label: '포트폴리오', icon: Wallet },
                { id: 'trading', label: '차트분석', icon: BarChart3 },
                { id: 'orders', label: '거래내역', icon: ShoppingCart },
                { id: 'analysis', label: '종목분석', icon: Activity }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setSelectedTab(tab.id as any)}
                  className={`flex items-center space-x-2 px-6 py-3 rounded-lg font-semibold transition-all flex-1 justify-center ${
                    selectedTab === tab.id
                      ? 'bg-gray-600 text-gray-100 shadow-lg border border-gray-500'
                      : 'text-gray-400 hover:text-gray-300 hover:bg-gray-700'
                  }`}
                >
                  <tab.icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              ))}
            </div>

            {/* 탭 컨텐츠 */}
            <AnimatePresence mode="wait">
              {/* 포트폴리오 탭 */}
              {selectedTab === 'portfolio' && (
                <motion.div
                  key="portfolio"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="space-y-6"
                >
                  {/* 포트폴리오 요약 카드들 */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6">
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="text-lg font-semibold text-gray-100">주식평가액</h3>
                        <DollarSign className="w-5 h-5 text-green-400" />
                      </div>
                      <p className="text-2xl font-bold text-gray-100 mb-1">
                        {formatCurrency(portfolio.reduce((sum, item) => sum + item.marketValue, 0))}
                      </p>
                      <p className="text-gray-400 text-sm">현재 보유 주식 가치</p>
                    </div>

                    <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6">
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="text-lg font-semibold text-gray-100">평가손익</h3>
                        <TrendingUp className="w-5 h-5 text-blue-400" />
                      </div>
                      <p className={`text-2xl font-bold mb-1 ${getChangeColor(portfolio.reduce((sum, item) => sum + item.profitLoss, 0))}`}>
                        {formatCurrency(portfolio.reduce((sum, item) => sum + item.profitLoss, 0))}
                      </p>
                      <p className={`text-sm font-semibold ${getChangeColor(portfolio.reduce((sum, item) => sum + item.profitRate * item.marketValue, 0) / portfolio.reduce((sum, item) => sum + item.marketValue, 0) || 0)}`}>
                        {formatPercent(portfolio.reduce((sum, item) => sum + item.profitRate * item.marketValue, 0) / portfolio.reduce((sum, item) => sum + item.marketValue, 0) || 0)}
                      </p>
                    </div>

                    <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6">
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="text-lg font-semibold text-gray-100">보유종목</h3>
                        <BarChart3 className="w-5 h-5 text-purple-400" />
                      </div>
                      <p className="text-2xl font-bold text-gray-100 mb-1">{portfolio.length}</p>
                      <p className="text-gray-400 text-sm">개 종목 보유중</p>
                    </div>
                  </div>

                  {/* 포트폴리오 상세 테이블 */}
                  <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6">
                    <h3 className="text-lg font-semibold text-gray-100 mb-6 flex items-center">
                      <Target className="w-5 h-5 mr-2 text-yellow-400" />
                      보유 종목 상세
                    </h3>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="text-gray-400 text-sm border-b border-gray-700">
                            <th className="text-left py-3 px-2">종목정보</th>
                            <th className="text-right py-3 px-2">수량</th>
                            <th className="text-right py-3 px-2">평균단가</th>
                            <th className="text-right py-3 px-2">현재가</th>
                            <th className="text-right py-3 px-2">평가액</th>
                            <th className="text-right py-3 px-2">손익률</th>
                          </tr>
                        </thead>
                        <tbody>
                          {portfolio.map((item, index) => (
                            <motion.tr
                              key={item.stockCode}
                              initial={{ opacity: 0, x: -20 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: index * 0.1 }}
                              className="border-b border-gray-700 hover:bg-gray-750 transition-colors"
                            >
                              <td className="py-4 px-2">
                                <div>
                                  <p className="text-gray-100 font-semibold text-sm">{item.stockName}</p>
                                  <p className="text-gray-400 text-xs">{item.stockCode}</p>
                                </div>
                              </td>
                              <td className="text-right py-4 px-2 text-gray-100 font-mono text-sm">
                                {item.quantity.toLocaleString()}
                              </td>
                              <td className="text-right py-4 px-2 text-gray-100 font-mono text-sm">
                                {formatCurrency(item.avgPrice)}
                              </td>
                              <td className="text-right py-4 px-2 text-gray-100 font-mono text-sm font-semibold">
                                {formatCurrency(item.currentPrice)}
                              </td>
                              <td className="text-right py-4 px-2 text-gray-100 font-mono text-sm font-bold">
                                {formatCurrency(item.marketValue)}
                              </td>
                              <td className={`text-right py-4 px-2 font-semibold text-sm ${getChangeColor(item.profitRate)}`}>
                                {formatPercent(item.profitRate)}
                              </td>
                            </motion.tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </motion.div>
              )}

              {/* 차트분석 탭 */}
              {selectedTab === 'trading' && (
                <motion.div
                  key="trading"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="space-y-6"
                >
                  {/* 선택된 종목 정보 헤더 */}
                  <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6">
                    <div className="flex items-center justify-between mb-6">
                      <div className="flex items-center space-x-3">
                        <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                          <BarChart3 className="w-6 h-6 text-white" />
                        </div>
                        <div>
                          <h3 className="text-xl font-bold text-gray-100">
                            {selectedStockInfo?.name || stockDatabase.find(s => s.code === selectedStock)?.name}
                          </h3>
                          <p className="text-gray-400 text-sm">{selectedStock}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold text-gray-100 mb-1">
                          {formatCurrency(selectedStockInfo?.price || stockDatabase.find(s => s.code === selectedStock)?.price || 0)}
                        </p>
                        <p className={`text-sm font-semibold ${getChangeColor(selectedStockInfo?.change || stockDatabase.find(s => s.code === selectedStock)?.change || 0)}`}>
                          {formatPercent(selectedStockInfo?.change || stockDatabase.find(s => s.code === selectedStock)?.change || 0)}
                        </p>
                      </div>
                    </div>

                    {/* 가격 차트 */}
                    <div className="h-96">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={priceHistory}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#4b5563" />
                          <XAxis 
                            dataKey="date" 
                            stroke="#9ca3af" 
                            fontSize={12}
                            tickFormatter={(value) => new Date(value).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' })}
                          />
                          <YAxis 
                            stroke="#9ca3af" 
                            fontSize={12} 
                            tickFormatter={(value) => `₩${(value / 1000).toFixed(0)}K`}
                          />
                          <Tooltip 
                            contentStyle={{
                              backgroundColor: '#374151',
                              border: '1px solid #4b5563',
                              borderRadius: '12px',
                              color: '#f9fafb'
                            }}
                            formatter={(value: any, name: string) => {
                              switch(name) {
                                case '종가': return [formatCurrency(value), '종가'];
                                case '5일평균': return [formatCurrency(value), '5일 이평선'];
                                case '20일평균': return [formatCurrency(value), '20일 이평선'];
                                default: return [formatCurrency(value), name];
                              }
                            }}
                            labelFormatter={(label) => new Date(label).toLocaleDateString('ko-KR')}
                          />
                          <Line 
                            type="monotone" 
                            dataKey="price" 
                            stroke="#3b82f6" 
                            strokeWidth={2}
                            dot={false}
                            name="종가"
                          />
                          <Line 
                            type="monotone" 
                            dataKey="ma5" 
                            stroke="#10b981" 
                            strokeWidth={1.5}
                            dot={false}
                            name="5일평균"
                            strokeDasharray="5 5"
                          />
                          <Line 
                            type="monotone" 
                            dataKey="ma20" 
                            stroke="#f59e0b" 
                            strokeWidth={1.5}
                            dot={false}
                            name="20일평균"
                            strokeDasharray="10 5"
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  {/* KOSPI 지수 차트 */}
                  <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6">
                    <h3 className="text-lg font-semibold text-gray-100 mb-4 flex items-center">
                      <Activity className="w-5 h-5 mr-2 text-green-400" />
                      종합주가지수 (KOSPI)
                    </h3>
                    
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={kospiHistory}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#4b5563" />
                          <XAxis 
                            dataKey="date" 
                            stroke="#9ca3af" 
                            fontSize={10}
                            tickFormatter={(value) => new Date(value).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' })}
                          />
                          <YAxis 
                            stroke="#9ca3af" 
                            fontSize={10}
                            tickFormatter={(value) => value.toFixed(0)}
                          />
                          <Tooltip 
                            contentStyle={{
                              backgroundColor: '#374151',
                              border: '1px solid #4b5563',
                              borderRadius: '8px',
                              color: '#f9fafb'
                            }}
                            formatter={(value: any) => [value.toFixed(2), 'KOSPI']}
                            labelFormatter={(label) => new Date(label).toLocaleDateString('ko-KR')}
                          />
                          <Line 
                            type="monotone" 
                            dataKey="kospi" 
                            stroke="#ef4444" 
                            strokeWidth={2}
                            dot={false}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </motion.div>
              )}

              {/* 거래내역 탭 */}
              {selectedTab === 'orders' && (
                <motion.div
                  key="orders"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="space-y-6"
                >
                  {/* 주문 필터 */}
                  <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6">
                    <h3 className="text-lg font-semibold text-gray-100 mb-4 flex items-center">
                      <ShoppingCart className="w-5 h-5 mr-2 text-orange-400" />
                      거래 내역
                    </h3>
                    
                    <div className="flex space-x-2 mb-6">
                      {['전체', '체결완료', '주문접수', '주문취소'].map((status, index) => (
                        <button
                          key={status}
                          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                            index === 0 
                              ? 'bg-blue-600 text-white border border-blue-500' 
                              : 'bg-gray-700 text-gray-300 border border-gray-600 hover:bg-gray-600'
                          }`}
                        >
                          {status}
                        </button>
                      ))}
                    </div>

                    {/* 주문 테이블 */}
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="text-gray-400 text-sm border-b border-gray-700">
                            <th className="text-left py-3 px-2">주문시간</th>
                            <th className="text-left py-3 px-2">종목정보</th>
                            <th className="text-center py-3 px-2">구분</th>
                            <th className="text-right py-3 px-2">수량</th>
                            <th className="text-right py-3 px-2">가격</th>
                            <th className="text-center py-3 px-2">상태</th>
                          </tr>
                        </thead>
                        <tbody>
                          {orders.map((order, index) => (
                            <motion.tr
                              key={order.id}
                              initial={{ opacity: 0, x: -20 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: index * 0.1 }}
                              className="border-b border-gray-700 hover:bg-gray-750 transition-colors"
                            >
                              <td className="py-4 px-2 text-gray-300 text-sm font-mono">
                                {new Date(order.orderTime).toLocaleDateString('ko-KR', { 
                                  month: 'short', 
                                  day: 'numeric',
                                  hour: '2-digit',
                                  minute: '2-digit'
                                })}
                              </td>
                              <td className="py-4 px-2">
                                <div>
                                  <p className="text-gray-100 font-semibold text-sm">{order.stockName}</p>
                                  <p className="text-gray-400 text-xs">{order.stockCode}</p>
                                </div>
                              </td>
                              <td className="text-center py-4 px-2">
                                <span className={`px-3 py-1 rounded-lg text-xs font-semibold ${
                                  order.orderType === 'BUY' 
                                    ? 'bg-red-600 text-white' 
                                    : 'bg-blue-600 text-white'
                                }`}>
                                  {order.orderType === 'BUY' ? '매수' : '매도'}
                                </span>
                              </td>
                              <td className="text-right py-4 px-2 text-gray-100 font-mono text-sm">
                                {order.quantity.toLocaleString()}
                              </td>
                              <td className="text-right py-4 px-2 text-gray-100 font-mono text-sm">
                                {formatCurrency(order.price)}
                              </td>
                              <td className="text-center py-4 px-2">
                                <span className={`px-3 py-1 rounded-lg text-xs font-semibold ${
                                  order.status === 'COMPLETED' ? 'bg-green-600 text-white' :
                                  order.status === 'PENDING' ? 'bg-yellow-600 text-white' :
                                  'bg-gray-600 text-white'
                                }`}>
                                  {getStatusText(order.status)}
                                </span>
                              </td>
                            </motion.tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </motion.div>
              )}

              {/* 종목분석 탭 */}
              {selectedTab === 'analysis' && (
                <motion.div
                  key="analysis"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="space-y-6"
                >
                  {/* 거래내역 */}
                  <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6">
                    <h3 className="text-lg font-semibold text-gray-100 mb-6 flex items-center">
                      <Clock className="w-5 h-5 mr-2 text-indigo-400" />
                      최근 거래내역
                    </h3>
                    
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="text-gray-400 text-sm border-b border-gray-700">
                            <th className="text-left py-3 px-2">거래시간</th>
                            <th className="text-left py-3 px-2">종목정보</th>
                            <th className="text-center py-3 px-2">구분</th>
                            <th className="text-right py-3 px-2">수량</th>
                            <th className="text-right py-3 px-2">단가</th>
                            <th className="text-right py-3 px-2">거래금액</th>
                          </tr>
                        </thead>
                        <tbody>
                          {transactions.map((transaction, index) => (
                            <motion.tr
                              key={transaction.id}
                              initial={{ opacity: 0, x: -20 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: index * 0.1 }}
                              className="border-b border-gray-700 hover:bg-gray-750 transition-colors"
                            >
                              <td className="py-4 px-2 text-gray-300 text-sm font-mono">
                                {new Date(transaction.time).toLocaleDateString('ko-KR', { 
                                  month: 'short', 
                                  day: 'numeric',
                                  hour: '2-digit',
                                  minute: '2-digit'
                                })}
                              </td>
                              <td className="py-4 px-2">
                                <div>
                                  <p className="text-gray-100 font-semibold text-sm">{transaction.stockName}</p>
                                  <p className="text-gray-400 text-xs">{transaction.stockCode}</p>
                                </div>
                              </td>
                              <td className="text-center py-4 px-2">
                                <span className={`px-3 py-1 rounded-lg text-xs font-semibold ${
                                  transaction.type === 'BUY' 
                                    ? 'bg-red-600 text-white' 
                                    : 'bg-blue-600 text-white'
                                }`}>
                                  {transaction.type === 'BUY' ? '매수' : '매도'}
                                </span>
                              </td>
                              <td className="text-right py-4 px-2 text-gray-100 font-mono text-sm">
                                {transaction.quantity.toLocaleString()}
                              </td>
                              <td className="text-right py-4 px-2 text-gray-100 font-mono text-sm">
                                {formatCurrency(transaction.price)}
                              </td>
                              <td className="text-right py-4 px-2 text-gray-100 font-mono text-sm font-bold">
                                {formatCurrency(transaction.amount)}
                              </td>
                            </motion.tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* 거래 통계 */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6">
                      <h3 className="text-lg font-semibold text-gray-100 mb-4 flex items-center">
                        <BarChart3 className="w-5 h-5 mr-2 text-cyan-400" />
                        일일 거래 통계
                      </h3>
                      
                      <div className="space-y-4">
                        <div className="flex justify-between items-center">
                          <span className="text-gray-400">총 거래건수</span>
                          <span className="text-gray-100 font-bold">{transactions.length}건</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-gray-400">매수 거래</span>
                          <span className="text-gray-100 font-bold">
                            {transactions.filter(t => t.type === 'BUY').length}건
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-gray-400">매도 거래</span>
                          <span className="text-gray-100 font-bold">
                            {transactions.filter(t => t.type === 'SELL').length}건
                          </span>
                        </div>
                        <div className="flex justify-between items-center border-t border-gray-700 pt-3">
                          <span className="text-gray-400">총 거래금액</span>
                          <span className="text-gray-100 font-bold">
                            {formatCurrency(transactions.reduce((sum, t) => sum + t.amount, 0))}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6">
                      <h3 className="text-lg font-semibold text-gray-100 mb-4 flex items-center">
                        <Target className="w-5 h-5 mr-2 text-pink-400" />
                        포트폴리오 구성
                      </h3>
                      
                      <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie
                              data={portfolio.map(item => ({
                                name: item.stockName,
                                value: item.marketValue,
                                fill: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'][portfolio.indexOf(item) % 5]
                              }))}
                              cx="50%"
                              cy="50%"
                              innerRadius={40}
                              outerRadius={80}
                              dataKey="value"
                            >
                              {portfolio.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'][index % 5]} />
                              ))}
                            </Pie>
                            <Tooltip 
                              contentStyle={{
                                backgroundColor: '#374151',
                                border: '1px solid #4b5563',
                                borderRadius: '8px',
                                color: '#f9fafb'
                              }}
                              formatter={(value: any) => [formatCurrency(value), '평가액']}
                            />
                          </PieChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  </div>

                  {/* 자동매매 전략 설정 */}
                  <div className="bg-gray-800 rounded-2xl border border-gray-700 p-6">
                    <h3 className="text-lg font-semibold text-gray-100 mb-6 flex items-center">
                      <Settings className="w-5 h-5 mr-2 text-violet-400" />
                      자동매매 전략 설정
                    </h3>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* 전략 선택 */}
                      <div>
                        <h4 className="text-gray-200 font-medium mb-3">전략 선택</h4>
                        <div className="space-y-2">
                          {[
                            { id: 'momentum', name: '모멘텀 전략', desc: '추세 추종 매매' },
                            { id: 'mean_reversion', name: '평균회귀 전략', desc: '과매수/과매도 구간 매매' },
                            { id: 'breakout', name: '돌파 전략', desc: '저항선/지지선 돌파 매매' }
                          ].map((strategy, index) => (
                            <div
                              key={strategy.id}
                              className={`p-3 rounded-lg border cursor-pointer transition-all ${
                                index === 0 
                                  ? 'border-blue-500 bg-blue-600/20' 
                                  : 'border-gray-600 bg-gray-700 hover:border-gray-500'
                              }`}
                            >
                              <div className="flex items-center space-x-3">
                                <div className={`w-3 h-3 rounded-full ${
                                  index === 0 ? 'bg-blue-400' : 'bg-gray-500'
                                }`}></div>
                                <div>
                                  <p className="text-gray-100 font-medium text-sm">{strategy.name}</p>
                                  <p className="text-gray-400 text-xs">{strategy.desc}</p>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* 리스크 관리 */}
                      <div>
                        <h4 className="text-gray-200 font-medium mb-3">리스크 관리</h4>
                        <div className="space-y-3">
                          <div>
                            <label className="block text-gray-400 text-sm mb-1">손절매 비율</label>
                            <div className="flex items-center space-x-2">
                              <input
                                type="range"
                                min="1"
                                max="10"
                                defaultValue="5"
                                className="flex-1"
                              />
                              <span className="text-gray-100 text-sm font-mono w-12">5%</span>
                            </div>
                          </div>
                          
                          <div>
                            <label className="block text-gray-400 text-sm mb-1">익절매 비율</label>
                            <div className="flex items-center space-x-2">
                              <input
                                type="range"
                                min="5"
                                max="20"
                                defaultValue="10"
                                className="flex-1"
                              />
                              <span className="text-gray-100 text-sm font-mono w-12">10%</span>
                            </div>
                          </div>
                          
                          <div>
                            <label className="block text-gray-400 text-sm mb-1">최대 포지션 크기</label>
                            <div className="flex items-center space-x-2">
                              <input
                                type="range"
                                min="5"
                                max="30"
                                defaultValue="10"
                                className="flex-1"
                              />
                              <span className="text-gray-100 text-sm font-mono w-12">10%</span>
                            </div>
                          </div>
                        </div>
                        
                        <div className="mt-4 pt-4 border-t border-gray-700">
                          <button className="w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white py-3 px-4 rounded-xl font-semibold hover:from-purple-700 hover:to-blue-700 transition-all">
                            전략 활성화
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>

      {/* 주문 확인 모달 */}
      <AnimatePresence>
        {showOrderConfirm && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
            onClick={() => setShowOrderConfirm(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-gray-800 rounded-2xl border border-gray-700 p-6 max-w-md w-full"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-xl font-bold text-gray-100 mb-4 flex items-center">
                <AlertTriangle className="w-6 h-6 mr-2 text-yellow-400" />
                주문 확인
              </h3>
              
              <div className="space-y-4 mb-6">
                <div className="bg-gray-700 rounded-lg p-4">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-gray-400">종목</p>
                      <p className="text-gray-100 font-semibold">
                        {selectedStockInfo?.name || stockDatabase.find(s => s.code === selectedStock)?.name}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-400">구분</p>
                      <p className={`font-semibold ${orderType === 'BUY' ? 'text-red-400' : 'text-blue-400'}`}>
                        {orderType === 'BUY' ? '매수' : '매도'}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-400">수량</p>
                      <p className="text-gray-100 font-mono">{parseInt(orderQuantity || '0').toLocaleString()}주</p>
                    </div>
                    <div>
                      <p className="text-gray-400">가격</p>
                      <p className="text-gray-100 font-mono">{formatCurrency(parseInt(orderPrice || '0'))}</p>
                    </div>
                  </div>
                  
                  <div className="border-t border-gray-600 mt-4 pt-4">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-400">총 주문금액</span>
                      <span className="text-gray-100 font-bold text-lg">
                        {formatCurrency((parseInt(orderQuantity) || 0) * (parseInt(orderPrice) || 0))}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="flex space-x-3">
                <button
                  onClick={() => setShowOrderConfirm(false)}
                  className="flex-1 py-3 px-4 bg-gray-700 text-gray-300 rounded-xl font-semibold hover:bg-gray-600 transition-all"
                >
                  취소
                </button>
                <button
                  onClick={handleOrder}
                  disabled={isLoading}
                  className={`flex-1 py-3 px-4 rounded-xl font-semibold transition-all ${
                    orderType === 'BUY'
                      ? 'bg-red-600 hover:bg-red-700 text-white'
                      : 'bg-blue-600 hover:bg-blue-700 text-white'
                  } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  {isLoading ? '처리중...' : '주문 확정'}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 푸터 */}
      <footer className="bg-gray-800 border-t border-gray-700 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center space-x-3 mb-4 md:mb-0">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white">
                <BarChart3 />
              </div>
              <div>
                <p className="text-gray-100 font-semibold">키움 모의투자 시스템</p>
                <p className="text-gray-400 text-sm">Professional Mock Trading Platform</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-6 text-sm text-gray-400">
              <div className="flex items-center space-x-2">
                <CheckCircle className="w-4 h-4 text-green-400" />
                <span>실시간 데이터</span>
              </div>
              <div className="flex items-center space-x-2">
                <CheckCircle className="w-4 h-4 text-green-400" />
                <span>자동매매 지원</span>
              </div>
              <div className="flex items-center space-x-2">
                <CheckCircle className="w-4 h-4 text-green-400" />
                <span>리스크 관리</span>
              </div>
              <div className="flex items-center space-x-2">
                <CheckCircle className="w-4 h-4 text-green-400" />
                <span>포트폴리오 분석</span>
              </div>
            </div>
          </div>
          
          <div className="border-t border-gray-700 mt-6 pt-6 text-center">
            <p className="text-gray-500 text-sm">
              © 2025 키움 모의투자 시스템. 본 시스템은 모의투자 목적으로 제작되었으며, 
              실제 투자 결과와 다를 수 있습니다. 투자 결정 시 신중하게 검토하시기 바랍니다.
            </p>
          </div>
        </div>
      </footer>

      {/* 실시간 알림 (하단 우측) */}
      <div className="fixed bottom-4 right-4 space-y-2 z-40">
        <AnimatePresence>
          {isLoading && (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="bg-gray-800 border border-gray-600 rounded-xl p-4 shadow-lg flex items-center space-x-3"
            >
              <RefreshCw className="w-4 h-4 text-blue-400 animate-spin" />
              <span className="text-gray-100 text-sm">데이터 업데이트 중...</span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}