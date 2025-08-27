"""
file: quant_mvp/data/data_loader.py
데이터 로딩 및 샘플 데이터 생성
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class DataLoader:
    """데이터 로더 클래스"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.data_dir = Path("data/sample_data")
        self.price_file = self.data_dir / "market_prices.csv"
        self.financial_file = self.data_dir / "financials.csv"
        self.market_file = self.data_dir / "market_data.csv"
    
    def load_all_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """모든 데이터 로드"""
        try:
            prices = self.load_price_data()
            financials = self.load_financial_data()
            market = self.load_market_data()
            
            logger.info(f"Loaded data - Prices: {len(prices)}, Financials: {len(financials)}, Market: {len(market)}")
            return prices, financials, market
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    def load_price_data(self) -> pd.DataFrame:
        """가격 데이터 로드"""
        if not self.price_file.exists():
            logger.warning("Price data not found, generating sample data")
            generate_sample_data()
        
        df = pd.read_csv(self.price_file, parse_dates=['date'])
        df = df.sort_values(['symbol', 'date'])
        return df
    
    def load_financial_data(self) -> pd.DataFrame:
        """재무 데이터 로드"""
        if not self.financial_file.exists():
            logger.warning("Financial data not found, generating sample data")
            generate_sample_data()
        
        df = pd.read_csv(self.financial_file, parse_dates=['date'])
        return df
    
    def load_market_data(self) -> pd.DataFrame:
        """시장 데이터 로드"""
        if not self.market_file.exists():
            logger.warning("Market data not found, generating sample data")
            generate_sample_data()
        
        df = pd.read_csv(self.market_file, parse_dates=['date'])
        df = df.set_index('date')
        return df
    
    def get_symbol_data(self, symbol: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """특정 종목 데이터 조회"""
        prices = self.load_price_data()
        symbol_data = prices[prices['symbol'] == symbol].copy()
        
        if start_date:
            symbol_data = symbol_data[symbol_data['date'] >= start_date]
        if end_date:
            symbol_data = symbol_data[symbol_data['date'] <= end_date]
        
        symbol_data = symbol_data.set_index('date')
        return symbol_data
    
    def get_symbols_list(self) -> List[str]:
        """사용 가능한 종목 리스트"""
        try:
            prices = self.load_price_data()
            return sorted(prices['symbol'].unique().tolist())
        except:
            return []
    
    def merge_price_financial_data(self, symbols: List[str] = None) -> pd.DataFrame:
        """가격 데이터와 재무 데이터 병합"""
        prices = self.load_price_data()
        financials = self.load_financial_data()
        
        if symbols:
            prices = prices[prices['symbol'].isin(symbols)]
            financials = financials[financials['symbol'].isin(symbols)]
        
        # 분기별 재무 데이터를 일별로 확장
        financials_expanded = []
        for _, row in financials.iterrows():
            quarter_dates = pd.date_range(
                start=row['date'], 
                periods=90,  # 분기 약 90일
                freq='D'
            )
            for date in quarter_dates:
                new_row = row.copy()
                new_row['date'] = date
                financials_expanded.append(new_row)
        
        financials_df = pd.DataFrame(financials_expanded)
        
        # 가격 데이터와 재무 데이터 병합
        merged = pd.merge(prices, financials_df, on=['symbol', 'date'], how='left')
        merged = merged.fillna(method='ffill')  # 재무 데이터 forward fill
        
        return merged

def generate_sample_data():
    """샘플 데이터 생성"""
    logger.info("Generating sample data...")
    
    # 데이터 디렉토리 생성
    data_dir = Path("data/sample_data")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # 날짜 범위 설정
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2024, 12, 31)
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    business_days = pd.bdate_range(start=start_date, end=end_date)
    
    # 종목 리스트
    symbols = {
        'AAPL': {'name': 'Apple Inc.', 'sector': 'Technology', 'base_price': 150},
        'TSLA': {'name': 'Tesla Inc.', 'sector': 'Consumer Discretionary', 'base_price': 200},
        'MSFT': {'name': 'Microsoft Corp.', 'sector': 'Technology', 'base_price': 300},
        'AMZN': {'name': 'Amazon.com Inc.', 'sector': 'Consumer Discretionary', 'base_price': 100},
        'GOOGL': {'name': 'Alphabet Inc.', 'sector': 'Technology', 'base_price': 120},
        'NVDA': {'name': 'NVIDIA Corp.', 'sector': 'Technology', 'base_price': 400},
        'META': {'name': 'Meta Platforms Inc.', 'sector': 'Technology', 'base_price': 250},
        'BRK.B': {'name': 'Berkshire Hathaway', 'sector': 'Financial Services', 'base_price': 300},
        'JPM': {'name': 'JPMorgan Chase', 'sector': 'Financial Services', 'base_price': 140},
        'JNJ': {'name': 'Johnson & Johnson', 'sector': 'Healthcare', 'base_price': 160},
        'PG': {'name': 'Procter & Gamble', 'sector': 'Consumer Staples', 'base_price': 140},
        'KO': {'name': 'Coca-Cola', 'sector': 'Consumer Staples', 'base_price': 55},
        'WMT': {'name': 'Walmart Inc.', 'sector': 'Consumer Staples', 'base_price': 140},
        'SPY': {'name': 'SPDR S&P 500 ETF', 'sector': 'Index', 'base_price': 350}
    }
    
    # 1. 가격 데이터 생성
    price_data = []
    np.random.seed(42)  # 재현 가능한 결과
    
    for symbol, info in symbols.items():
        prices = generate_price_series(info['base_price'], len(business_days))
        volumes = generate_volume_series(len(business_days))
        
        for i, date in enumerate(business_days):
            price_data.append({
                'date': date,
                'symbol': symbol,
                'open': prices[i] * (0.995 + np.random.random() * 0.01),
                'high': prices[i] * (1.0 + np.random.random() * 0.02),
                'low': prices[i] * (0.98 + np.random.random() * 0.01),
                'close': prices[i],
                'volume': volumes[i],
                'sector': info['sector']
            })
    
    price_df = pd.DataFrame(price_data)
    price_df.to_csv(data_dir / "market_prices.csv", index=False)
    
    # 2. 재무 데이터 생성
    financial_data = []
    quarters = pd.date_range(start=start_date, end=end_date, freq='Q')
    
    for symbol, info in symbols.items():
        if symbol == 'SPY':  # ETF는 재무 데이터 제외
            continue
            
        base_market_cap = np.random.uniform(500_000, 2_000_000)  # 백만 달러
        base_revenue = np.random.uniform(50_000, 500_000)  # 백만 달러
        
        for quarter in quarters:
            # 성장률 시뮬레이션
            growth_factor = 1 + np.random.normal(0.02, 0.1)  # 평균 2% 성장
            market_cap = base_market_cap * growth_factor
            revenue = base_revenue * growth_factor
            
            financial_data.append({
                'symbol': symbol,
                'date': quarter,
                'market_cap': market_cap * 1_000_000,  # 달러로 변환
                'pe_ratio': np.random.uniform(8, 35),
                'pb_ratio': np.random.uniform(0.5, 5),
                'roe': np.random.uniform(5, 30),
                'roa': np.random.uniform(2, 20),
                'debt_to_equity': np.random.uniform(0.1, 2.0),
                'dividend_yield': np.random.uniform(0, 5) if info['sector'] != 'Technology' else np.random.uniform(0, 2),
                'revenue_growth': np.random.uniform(-5, 25),
                'earnings_growth': np.random.uniform(-10, 30),
                'sector': info['sector']
            })
            
            # 다음 분기를 위해 베이스 값 업데이트
            base_market_cap = market_cap
            base_revenue = revenue
    
    financial_df = pd.DataFrame(financial_data)
    financial_df.to_csv(data_dir / "financials.csv", index=False)
    
    # 3. 시장 데이터 생성
    market_data = []
    spy_prices = [d for d in price_data if d['symbol'] == 'SPY']
    
    for i, date in enumerate(business_days):
        spy_close = spy_prices[i]['close'] if i < len(spy_prices) else 350
        
        market_data.append({
            'date': date,
            'spy_close': spy_close,
            'nasdaq_close': spy_close * 12 + np.random.normal(0, 50),  # 대략적인 나스닥 지수
            'vix_close': max(10, 20 + np.random.normal(0, 5)),  # VIX는 10 이상
            'treasury_10y': max(0.5, 2.0 + np.random.normal(0, 0.5)),  # 10년 국채
            'inflation_rate': max(0, 2.5 + np.random.normal(0, 1)),  # 인플레이션
            'gdp_growth': 2.0 + np.random.normal(0, 2)  # GDP 성장률
        })
    
    market_df = pd.DataFrame(market_data)
    market_df.to_csv(data_dir / "market_data.csv", index=False)
    
    logger.info("Sample data generation completed")

def generate_price_series(base_price: float, length: int) -> np.ndarray:
    """주가 시계열 생성 (기하 브라운 운동)"""
    returns = np.random.normal(0.0005, 0.02, length)  # 일일 수익률
    prices = [base_price]
    
    for i in range(1, length):
        new_price = prices[-1] * (1 + returns[i])
        prices.append(max(new_price, 1.0))  # 최소 1달러
    
    return np.array(prices)

def generate_volume_series(length: int) -> np.ndarray:
    """거래량 시계열 생성"""
    base_volume = np.random.uniform(1_000_000, 50_000_000)
    volumes = []
    
    for i in range(length):
        # 거래량은 로그 정규분포를 따름
        volume = base_volume * np.random.lognormal(0, 0.5)
        volumes.append(int(volume))
    
    return np.array(volumes)