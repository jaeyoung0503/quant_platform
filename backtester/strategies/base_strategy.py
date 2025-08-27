"""
File: backtester/strategies/base_strategy.py
Base Strategy Class for All Trading Strategies
"""

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import List, Dict, Tuple

class BaseStrategy(ABC):
    """Base class for all trading strategies"""
    
    def __init__(self, name: str):
        self.name = name
        self.transaction_cost = 0.001  # 0.1% transaction cost
        self.initial_capital = 10000   # $10,000 initial capital
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on the strategy logic
        
        Args:
            data: DataFrame with OHLCV and other market data
            
        Returns:
            Series with trading signals (-1: sell, 0: hold, 1: buy)
        """
        pass
    
    def calculate_returns(self, data: pd.DataFrame, signals: pd.Series) -> List[float]:
        """
        Calculate portfolio returns based on trading signals
        
        Args:
            data: Market data DataFrame
            signals: Trading signals Series
            
        Returns:
            List of portfolio values over time
        """
        prices = data['Close']
        portfolio_value = [self.initial_capital]
        position = 0  # Current position (0: no position, 1: long, -1: short)
        cash = self.initial_capital
        shares = 0
        
        for i in range(1, len(signals)):
            current_price = prices.iloc[i]
            current_signal = signals.iloc[i]
            previous_signal = signals.iloc[i-1]
            
            # Execute trades when signal changes
            if current_signal != previous_signal:
                # Close existing position
                if position != 0:
                    cash = shares * current_price * (1 - self.transaction_cost)
                    shares = 0
                    position = 0
                
                # Open new position
                if current_signal != 0:
                    shares = cash / (current_price * (1 + self.transaction_cost))
                    cash = 0
                    position = current_signal
            
            # Calculate current portfolio value
            if position != 0:
                current_value = shares * current_price
            else:
                current_value = cash
            
            portfolio_value.append(current_value)
        
        return portfolio_value
    
    def calculate_technical_indicators(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """Calculate common technical indicators"""
        close = data['Close']
        high = data['High'] if 'High' in data.columns else close
        low = data['Low'] if 'Low' in data.columns else close
        volume = data['Volume'] if 'Volume' in data.columns else pd.Series(1, index=close.index)
        
        indicators = {}
        
        # Moving averages
        indicators['SMA_20'] = close.rolling(window=20).mean()
        indicators['SMA_50'] = close.rolling(window=50).mean()
        indicators['SMA_200'] = close.rolling(window=200).mean()
        indicators['EMA_12'] = close.ewm(span=12).mean()
        indicators['EMA_26'] = close.ewm(span=26).mean()
        
        # Bollinger Bands
        sma_20 = indicators['SMA_20']
        rolling_std = close.rolling(window=20).std()
        indicators['BB_upper'] = sma_20 + (rolling_std * 2)
        indicators['BB_lower'] = sma_20 - (rolling_std * 2)
        indicators['BB_mid'] = sma_20
        
        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        indicators['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema_12 = indicators['EMA_12']
        ema_26 = indicators['EMA_26']
        indicators['MACD'] = ema_12 - ema_26
        indicators['MACD_signal'] = indicators['MACD'].ewm(span=9).mean()
        indicators['MACD_histogram'] = indicators['MACD'] - indicators['MACD_signal']
        
        # Stochastic Oscillator
        low_14 = low.rolling(window=14).min()
        high_14 = high.rolling(window=14).max()
        indicators['Stoch_K'] = 100 * (close - low_14) / (high_14 - low_14)
        indicators['Stoch_D'] = indicators['Stoch_K'].rolling(window=3).mean()
        
        # Average True Range (ATR)
        hl = high - low
        hc = abs(high - close.shift())
        lc = abs(low - close.shift())
        tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
        indicators['ATR'] = tr.rolling(window=14).mean()
        
        # Volume indicators
        indicators['Volume_SMA'] = volume.rolling(window=20).mean()
        indicators['Volume_ratio'] = volume / indicators['Volume_SMA']
        
        # Price momentum
        indicators['Returns_1d'] = close.pct_change(1)
        indicators['Returns_5d'] = close.pct_change(5)
        indicators['Returns_20d'] = close.pct_change(20)
        indicators['Returns_60d'] = close.pct_change(60)
        
        # Volatility
        indicators['Volatility_20d'] = close.rolling(window=20).std()
        indicators['Volatility_60d'] = close.rolling(window=60).std()
        
        return indicators
    
    def calculate_fundamental_signals(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """Calculate signals based on fundamental data"""
        fundamentals = {}
        
        if 'PE_Ratio' in data.columns:
            pe = data['PE_Ratio']
            fundamentals['PE_signal'] = pd.Series(0, index=pe.index)
            fundamentals['PE_signal'][pe < 15] = 1  # Buy if PE < 15
            fundamentals['PE_signal'][pe > 25] = -1  # Sell if PE > 25
        
        if 'PB_Ratio' in data.columns:
            pb = data['PB_Ratio']
            fundamentals['PB_signal'] = pd.Series(0, index=pb.index)
            fundamentals['PB_signal'][pb < 1.5] = 1  # Buy if PB < 1.5
            fundamentals['PB_signal'][pb > 3] = -1   # Sell if PB > 3
        
        if 'ROE' in data.columns:
            roe = data['ROE']
            fundamentals['ROE_signal'] = pd.Series(0, index=roe.index)
            fundamentals['ROE_signal'][roe > 15] = 1  # Buy if ROE > 15%
            fundamentals['ROE_signal'][roe < 5] = -1   # Sell if ROE < 5%
        
        if 'Debt_to_Equity' in data.columns:
            de = data['Debt_to_Equity']
            fundamentals['DE_signal'] = pd.Series(0, index=de.index)
            fundamentals['DE_signal'][de < 0.5] = 1   # Buy if low debt
            fundamentals['DE_signal'][de > 2.0] = -1  # Sell if high debt
        
        return fundamentals
    
    def normalize_signals(self, signals: pd.Series) -> pd.Series:
        """Normalize signals to -1, 0, 1 range"""
        normalized = signals.copy()
        normalized[normalized > 0] = 1
        normalized[normalized < 0] = -1
        return normalized.fillna(0)
    
    def combine_signals(self, signal_dict: Dict[str, pd.Series], weights: Dict[str, float] = None) -> pd.Series:
        """Combine multiple signals with optional weights"""
        if not signal_dict:
            return pd.Series(0, index=next(iter(signal_dict.values())).index)
        
        if weights is None:
            weights = {key: 1.0 for key in signal_dict.keys()}
        
        combined = pd.Series(0, index=next(iter(signal_dict.values())).index)
        
        for signal_name, signal_series in signal_dict.items():
            weight = weights.get(signal_name, 1.0)
            combined += signal_series * weight
        
        # Normalize combined signals
        return self.normalize_signals(combined)
    
    def apply_risk_management(self, signals: pd.Series, data: pd.DataFrame) -> pd.Series:
        """Apply risk management rules to signals"""
        managed_signals = signals.copy()
        
        # Volatility filter - reduce position size during high volatility
        if len(data) > 20:
            returns = data['Close'].pct_change()
            volatility = returns.rolling(window=20).std()
            high_vol_threshold = volatility.quantile(0.8)
            
            # Reduce signals during high volatility periods
            high_vol_mask = volatility > high_vol_threshold
            managed_signals[high_vol_mask] = managed_signals[high_vol_mask] * 0.5
        
        # Trend filter - avoid counter-trend trades
        if len(data) > 50:
            sma_20 = data['Close'].rolling(window=20).mean()
            sma_50 = data['Close'].rolling(window=50).mean()
            
            # Only allow long signals when price is above SMA_20 and SMA_20 > SMA_50
            uptrend = (data['Close'] > sma_20) & (sma_20 > sma_50)
            downtrend = (data['Close'] < sma_20) & (sma_20 < sma_50)
            
            # Filter signals based on trend
            managed_signals[(managed_signals > 0) & (~uptrend)] = 0
            managed_signals[(managed_signals < 0) & (~downtrend)] = 0
        
        return managed_signals
    
    def calculate_position_size(self, signal: float, volatility: float, max_risk: float = 0.02) -> float:
        """Calculate position size based on volatility and risk management"""
        if signal == 0 or volatility == 0:
            return 0
        
        # Kelly criterion approximation
        base_size = abs(signal)
        
        # Adjust for volatility (higher volatility = smaller position)
        vol_adjustment = min(1.0, 0.15 / volatility)  # Target 15% volatility
        
        # Apply maximum risk limit
        position_size = base_size * vol_adjustment
        position_size = min(position_size, max_risk / volatility)
        
        return position_size * np.sign(signal)
    
    def backtest_strategy(self, data: pd.DataFrame) -> Dict:
        """Complete backtest of the strategy"""
        # Generate signals
        signals = self.generate_signals(data)
        
        # Apply risk management
        managed_signals = self.apply_risk_management(signals, data)
        
        # Calculate returns
        portfolio_value = self.calculate_returns(data, managed_signals)
        
        # Calculate metrics
        returns = pd.Series(portfolio_value).pct_change().dropna()
        
        total_return = (portfolio_value[-1] / portfolio_value[0] - 1) * 100
        annual_return = ((portfolio_value[-1] / portfolio_value[0]) ** (252 / len(portfolio_value)) - 1) * 100
        volatility = returns.std() * np.sqrt(252) * 100
        sharpe_ratio = (annual_return - 2) / volatility if volatility > 0 else 0
        
        # Maximum drawdown
        portfolio_series = pd.Series(portfolio_value)
        rolling_max = portfolio_series.expanding().max()
        drawdown = ((portfolio_series - rolling_max) / rolling_max * 100)
        max_drawdown = drawdown.min()
        
        return {
            'portfolio_value': portfolio_value,
            'signals': managed_signals,
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': (returns > 0).mean() * 100
        }
    
    def optimize_parameters(self, data: pd.DataFrame, param_ranges: Dict) -> Dict:
        """Optimize strategy parameters using grid search"""
        best_params = {}
        best_sharpe = -999
        
        # This is a simplified version - in practice you'd use more sophisticated optimization
        print(f"Optimizing parameters for {self.name}...")
        
        # For demonstration, we'll just return the current parameters
        # In a real implementation, you'd iterate through param_ranges
        
        return {
            'best_params': best_params,
            'best_sharpe': best_sharpe,
            'optimization_results': []
        }
    
    def generate_report(self, backtest_results: Dict) -> str:
        """Generate a text report of strategy performance"""
        report = f"""
Strategy Performance Report: {self.name}
{'='*50}

Performance Metrics:
- Total Return: {backtest_results['total_return']:.2f}%
- Annual Return: {backtest_results['annual_return']:.2f}%
- Volatility: {backtest_results['volatility']:.2f}%
- Sharpe Ratio: {backtest_results['sharpe_ratio']:.2f}
- Maximum Drawdown: {backtest_results['max_drawdown']:.2f}%
- Win Rate: {backtest_results['win_rate']:.2f}%

Risk Assessment:
- {'Low Risk' if backtest_results['volatility'] < 15 else 'Medium Risk' if backtest_results['volatility'] < 25 else 'High Risk'}
- {'Excellent' if backtest_results['sharpe_ratio'] > 1.5 else 'Good' if backtest_results['sharpe_ratio'] > 1.0 else 'Average' if backtest_results['sharpe_ratio'] > 0.5 else 'Poor'} Risk-Adjusted Returns

Strategy Characteristics:
- Transaction Cost: {self.transaction_cost*100:.2f}%
- Initial Capital: ${self.initial_capital:,}
- Final Portfolio Value: ${backtest_results['portfolio_value'][-1]:,.2f}
        """
        
        return report
    
    def __str__(self):
        return f"Strategy: {self.name}"
    
    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}')"