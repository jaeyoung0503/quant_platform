"""
File: backtester/data_generator.py
Stock Data Generator for Backtesting
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict

class DataGenerator:
    """Generate realistic sample stock data for backtesting"""
    
    def __init__(self):
        self.symbols = [
            'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'META', 'BRK.B', 
            'V', 'JNJ', 'WMT', 'JPM', 'UNH', 'PG', 'MA', 'HD', 'CVX', 'ABBV', 
            'PFE', 'KO', 'PEP', 'AVGO', 'TMO', 'COST', 'DIS', 'ABT', 'ADBE',
            'CRM', 'NFLX', 'XOM', 'ORCL', 'ACN', 'VZ', 'CMCSA', 'DHR', 'NKE',
            'LIN', 'NEE', 'RTX', 'UPS', 'PM', 'HON', 'QCOM', 'T', 'IBM', 'GE',
            'AMD', 'INTC', 'CAT'
        ]
        
        # Stock characteristics for realistic data generation
        self.stock_profiles = {
            'high_vol': ['TSLA', 'NVDA', 'AMD', 'NFLX', 'CRM'],
            'low_vol': ['JNJ', 'PG', 'KO', 'WMT', 'UNH'],
            'tech_growth': ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META'],
            'defensive': ['JNJ', 'PG', 'KO', 'PFE', 'ABT'],
            'cyclical': ['CAT', 'GE', 'CVX', 'XOM', 'RTX']
        }
    
    def generate_sample_data(self, days: int = 3650) -> Dict:
        """Generate realistic sample stock data"""
        print("📊 샘플 데이터 생성 중...")
        
        data = {}
        base_date = datetime.now() - timedelta(days=days)
        
        for symbol in self.symbols:
            data[symbol] = self._generate_stock_data(symbol, base_date, days)
        
        print(f"✅ {len(self.symbols)}개 종목 데이터 생성 완료")
        return data
    
    def _generate_stock_data(self, symbol: str, start_date: datetime, days: int) -> pd.DataFrame:
        """Generate individual stock data with realistic characteristics"""
        dates = pd.date_range(start=start_date, end=datetime.now(), freq='D')
        
        # Determine stock characteristics
        returns_params = self._get_returns_parameters(symbol)
        
        # Generate price series
        returns = np.random.normal(
            returns_params['mean'], 
            returns_params['volatility'], 
            len(dates)
        )
        
        # Add market regime effects
        returns = self._add_market_regimes(returns, dates)
        
        # Generate prices from returns
        prices = self._generate_price_series(returns, start_price=100)
        
        # Generate volume data
        volumes = self._generate_volume_data(symbol, len(dates), returns)
        
        # Generate fundamental data
        fundamentals = self._generate_fundamental_data(symbol, len(dates))
        
        # Create DataFrame
        df = pd.DataFrame({
            'Date': dates,
            'Close': prices[:len(dates)],
            'Volume': volumes,
            'Market_Cap': fundamentals['market_cap'],
            'PE_Ratio': fundamentals['pe_ratio'],
            'PB_Ratio': fundamentals['pb_ratio'],
            'ROE': fundamentals['roe'],
            'Debt_to_Equity': fundamentals['debt_equity']
        })
        
        df.set_index('Date', inplace=True)
        return df
    
    def _get_returns_parameters(self, symbol: str) -> Dict:
        """Get return distribution parameters based on stock type"""
        if symbol in self.stock_profiles['high_vol']:
            return {'mean': 0.001, 'volatility': 0.035}
        elif symbol in self.stock_profiles['low_vol']:
            return {'mean': 0.0005, 'volatility': 0.012}
        elif symbol in self.stock_profiles['tech_growth']:
            return {'mean': 0.0012, 'volatility': 0.025}
        elif symbol in self.stock_profiles['defensive']:
            return {'mean': 0.0006, 'volatility': 0.015}
        elif symbol in self.stock_profiles['cyclical']:
            return {'mean': 0.0008, 'volatility': 0.028}
        else:
            return {'mean': 0.0008, 'volatility': 0.02}  # Default
    
    def _add_market_regimes(self, returns: np.array, dates: pd.DatetimeIndex) -> np.array:
        """Add market regime effects to returns"""
        modified_returns = returns.copy()
        
        # Add some market crash periods
        crash_periods = [
            ('2020-03-01', '2020-04-15'),  # COVID crash
            ('2022-01-01', '2022-06-30'),  # 2022 correction
            ('2018-10-01', '2018-12-31'),  # 2018 correction
        ]
        
        for start_crash, end_crash in crash_periods:
            crash_start = pd.to_datetime(start_crash)
            crash_end = pd.to_datetime(end_crash)
            
            crash_mask = (dates >= crash_start) & (dates <= crash_end)
            if crash_mask.any():
                # Increase volatility and add negative bias during crashes
                modified_returns[crash_mask] += np.random.normal(-0.002, 0.02, crash_mask.sum())
        
        # Add bull market periods
        bull_periods = [
            ('2016-01-01', '2018-01-31'),
            ('2020-04-01', '2021-12-31'),
        ]
        
        for start_bull, end_bull in bull_periods:
            bull_start = pd.to_datetime(start_bull)
            bull_end = pd.to_datetime(end_bull)
            
            bull_mask = (dates >= bull_start) & (dates <= bull_end)
            if bull_mask.any():
                # Add positive bias during bull markets
                modified_returns[bull_mask] += np.random.normal(0.001, 0.005, bull_mask.sum())
        
        return modified_returns
    
    def _generate_price_series(self, returns: np.array, start_price: float = 100) -> list:
        """Generate price series from returns"""
        prices = [start_price]
        
        for ret in returns[1:]:
            new_price = prices[-1] * (1 + ret)
            prices.append(max(new_price, 1))  # Prevent negative prices
        
        return prices
    
    def _generate_volume_data(self, symbol: str, length: int, returns: np.array) -> np.array:
        """Generate volume data correlated with price movements"""
        base_volume = np.random.lognormal(15, 0.5, length)
        
        # Volume tends to increase with price volatility
        volatility_factor = np.abs(returns) * 2
        volume_multiplier = 1 + volatility_factor
        
        # High volume stocks have higher base volume
        if symbol in self.stock_profiles['high_vol']:
            base_volume *= 2
        elif symbol in self.stock_profiles['low_vol']:
            base_volume *= 0.5
        
        return base_volume * volume_multiplier[:length]
    
    def _generate_fundamental_data(self, symbol: str, length: int) -> Dict:
        """Generate fundamental data for stocks"""
        fundamentals = {}
        
        # Market Cap - varies by company size
        if symbol in ['AAPL', 'MSFT', 'GOOGL', 'AMZN']:
            base_mc = np.random.uniform(1e12, 3e12, length)  # Large cap
        elif symbol in ['TSLA', 'NVDA', 'META']:
            base_mc = np.random.uniform(500e9, 1.5e12, length)  # Large cap growth
        else:
            base_mc = np.random.uniform(50e9, 500e9, length)  # Mid to large cap
        
        fundamentals['market_cap'] = base_mc
        
        # PE Ratio - varies by sector and growth profile
        if symbol in self.stock_profiles['tech_growth']:
            fundamentals['pe_ratio'] = np.random.uniform(20, 40, length)
        elif symbol in self.stock_profiles['defensive']:
            fundamentals['pe_ratio'] = np.random.uniform(15, 25, length)
        else:
            fundamentals['pe_ratio'] = np.random.uniform(12, 30, length)
        
        # PB Ratio
        fundamentals['pb_ratio'] = np.random.uniform(1, 5, length)
        
        # ROE
        if symbol in self.stock_profiles['tech_growth']:
            fundamentals['roe'] = np.random.uniform(15, 35, length)
        elif symbol in self.stock_profiles['defensive']:
            fundamentals['roe'] = np.random.uniform(12, 25, length)
        else:
            fundamentals['roe'] = np.random.uniform(8, 20, length)
        
        # Debt to Equity
        if symbol in self.stock_profiles['tech_growth']:
            fundamentals['debt_equity'] = np.random.uniform(0.1, 1.0, length)
        else:
            fundamentals['debt_equity'] = np.random.uniform(0.3, 2.0, length)
        
        return fundamentals
    
    def generate_correlation_matrix(self) -> pd.DataFrame:
        """Generate correlation matrix for stocks"""
        n_stocks = len(self.symbols)
        
        # Start with random correlation matrix
        random_corr = np.random.uniform(-0.3, 0.8, (n_stocks, n_stocks))
        
        # Make symmetric
        correlation_matrix = (random_corr + random_corr.T) / 2
        
        # Set diagonal to 1
        np.fill_diagonal(correlation_matrix, 1)
        
        # Ensure positive semi-definite
        eigenvals, eigenvecs = np.linalg.eigh(correlation_matrix)
        eigenvals = np.maximum(eigenvals, 0.01)  # Ensure positive eigenvalues
        correlation_matrix = eigenvecs @ np.diag(eigenvals) @ eigenvecs.T
        
        # Normalize to correlation matrix
        d = np.sqrt(np.diag(correlation_matrix))
        correlation_matrix = correlation_matrix / np.outer(d, d)
        
        return pd.DataFrame(correlation_matrix, index=self.symbols, columns=self.symbols)
    
    def add_economic_indicators(self, stock_data: Dict) -> Dict:
        """Add economic indicators to stock data"""
        # Generate some simple economic indicators
        dates = list(stock_data.values())[0].index
        
        economic_data = pd.DataFrame(index=dates)
        
        # Interest rates (simplified)
        economic_data['Interest_Rate'] = 2 + np.random.normal(0, 0.5, len(dates)).cumsum() * 0.01
        economic_data['Interest_Rate'] = np.clip(economic_data['Interest_Rate'], 0, 10)
        
        # VIX-like volatility index
        economic_data['VIX'] = 20 + np.random.normal(0, 5, len(dates))
        economic_data['VIX'] = np.clip(economic_data['VIX'], 10, 80)
        
        # GDP growth rate (quarterly)
        quarterly_growth = np.random.normal(2.5, 1.0, len(dates) // 90)
        economic_data['GDP_Growth'] = np.repeat(quarterly_growth, 90)[:len(dates)]
        
        # Add to each stock's data
        for symbol in stock_data:
            for col in economic_data.columns:
                stock_data[symbol][col] = economic_data[col]
        
        return stock_data