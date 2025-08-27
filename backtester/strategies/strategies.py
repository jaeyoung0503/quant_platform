"""
File: backtester/strategies.py
Trading Strategy Algorithms
Implementation of various quantitative trading strategies including
basic strategies and strategies inspired by legendary investors
"""

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import List, Dict, Tuple
import talib as ta

class BaseStrategy(ABC):
    """Abstract base class for all trading strategies"""
    
    def __init__(self, name: str):
        self.name = name
        self.initial_capital = 100000  # $100,000 starting capital
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate buy/sell signals based on strategy logic"""
        pass
    
    def calculate_returns(self, data: pd.DataFrame, signals: pd.Series) -> List[float]:
        """Calculate portfolio returns based on signals"""
        portfolio_value = [self.initial_capital]
        position = 0
        cash = self.initial_capital
        
        for i in range(1, len(data)):
            current_price = data['Close'].iloc[i]
            signal = signals.iloc[i] if i < len(signals) else 0
            
            # Execute trades based on signals
            if signal == 1 and position == 0:  # Buy signal
                shares = cash / current_price
                position = shares
                cash = 0
            elif signal == -1 and position > 0:  # Sell signal
                cash = position * current_price
                position = 0
            
            # Calculate current portfolio value
            current_value = cash + (position * current_price)
            portfolio_value.append(current_value)
        
        return portfolio_value

class BasicMomentumStrategy(BaseStrategy):
    """Basic momentum strategy using moving averages"""
    
    def __init__(self):
        super().__init__("Basic Momentum")
        self.short_window = 20
        self.long_window = 50
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate signals based on moving average crossover"""
        prices = data['Close']
        short_ma = prices.rolling(window=self.short_window).mean()
        long_ma = prices.rolling(window=self.long_window).mean()
        
        signals = pd.Series(0, index=data.index)
        
        # Buy when short MA crosses above long MA
        signals[short_ma > long_ma] = 1
        # Sell when short MA crosses below long MA
        signals[short_ma < long_ma] = -1
        
        return signals

class BasicMeanReversionStrategy(BaseStrategy):
    """Basic mean reversion strategy using Bollinger Bands"""
    
    def __init__(self):
        super().__init__("Basic Mean Reversion")
        self.window = 20
        self.std_dev = 2
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate signals based on Bollinger Bands"""
        prices = data['Close']
        rolling_mean = prices.rolling(window=self.window).mean()
        rolling_std = prices.rolling(window=self.window).std()
        
        upper_band = rolling_mean + (rolling_std * self.std_dev)
        lower_band = rolling_mean - (rolling_std * self.std_dev)
        
        signals = pd.Series(0, index=data.index)
        
        # Buy when price touches lower band (oversold)
        signals[prices <= lower_band] = 1
        # Sell when price touches upper band (overbought)
        signals[prices >= upper_band] = -1
        
        return signals

class WarrenBuffettStrategy(BaseStrategy):
    """Value investing strategy inspired by Warren Buffett"""
    
    def __init__(self):
        super().__init__("Warren Buffett Value")
        self.min_roe = 15  # Minimum ROE threshold
        self.max_pe = 20   # Maximum P/E ratio
        self.max_pb = 3    # Maximum P/B ratio
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate signals based on value metrics"""
        signals = pd.Series(0, index=data.index)
        
        # Ensure required columns exist
        if not all(col in data.columns for col in ['PE_Ratio', 'PB_Ratio', 'ROE']):
            # Use price-based approximation if fundamental data unavailable
            prices = data['Close']
            ma_50 = prices.rolling(50).mean()
            ma_200 = prices.rolling(200).mean()
            
            # Buy when price is below long-term average (value opportunity)
            signals[(prices < ma_200 * 0.9) & (prices > ma_50)] = 1
            # Hold quality positions longer
            signals[(prices > ma_200 * 1.1)] = -1
            
            return signals
        
        # Value-based signals
        value_score = (
            (data['ROE'] > self.min_roe) & 
            (data['PE_Ratio'] < self.max_pe) & 
            (data['PB_Ratio'] < self.max_pb)
        )
        
        # Additional momentum filter
        prices = data['Close']
        price_trend = prices.rolling(20).mean() > prices.rolling(50).mean()
        
        # Buy signals for undervalued stocks with positive momentum
        signals[value_score & price_trend] = 1
        
        # Sell when valuation becomes stretched
        overvalued = (data['PE_Ratio'] > self.max_pe * 1.5) | (data['PB_Ratio'] > self.max_pb * 1.5)
        signals[overvalued] = -1
        
        return signals

class BenjaminGrahamStrategy(BaseStrategy):
    """Deep value strategy inspired by Benjamin Graham"""
    
    def __init__(self):
        super().__init__("Benjamin Graham Deep Value")
        self.max_pe = 15
        self.max_pb = 1.5
        self.min_current_ratio = 2.0
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate signals based on Graham's criteria"""
        signals = pd.Series(0, index=data.index)
        
        # Price-based Graham approximation
        prices = data['Close']
        
        # Look for stocks significantly below their highs
        rolling_high = prices.rolling(252).max()  # 1-year high
        discount_from_high = (rolling_high - prices) / rolling_high
        
        # Buy when stock is 30%+ below 52-week high and showing stability
        ma_20 = prices.rolling(20).mean()
        buy_condition = (discount_from_high > 0.3) & (prices > ma_20 * 0.95)
        signals[buy_condition] = 1
        
        # Sell when approaching 52-week highs
        sell_condition = discount_from_high < 0.1
        signals[sell_condition] = -1
        
        return signals

class PeterLynchStrategy(BaseStrategy):
    """Growth at reasonable price strategy inspired by Peter Lynch"""
    
    def __init__(self):
        super().__init__("Peter Lynch Growth")
        self.peg_threshold = 1.0  # P/E to Growth ratio
        self.min_growth = 10      # Minimum growth rate
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate signals based on growth metrics"""
        signals = pd.Series(0, index=data.index)
        
        prices = data['Close']
        
        # Calculate price momentum as growth proxy
        returns_3m = prices.pct_change(60)  # 3-month returns
        returns_1y = prices.pct_change(252)  # 1-year returns
        
        # Growth momentum filter
        growth_momentum = (returns_3m > 0.1) & (returns_1y > 0.15)
        
        # Reasonable valuation (not too expensive)
        ma_50 = prices.rolling(50).mean()
        ma_200 = prices.rolling(200).mean()
        reasonable_price = prices < ma_50 * 1.1
        
        # Uptrend confirmation
        uptrend = ma_50 > ma_200
        
        # Buy signals for growing companies at reasonable prices
        signals[growth_momentum & reasonable_price & uptrend] = 1
        
        # Sell when momentum fades
        momentum_fade = (returns_3m < -0.05) | (prices > ma_50 * 1.3)
        signals[momentum_fade] = -1
        
        return signals

class RayDalioStrategy(BaseStrategy):
    """All Weather portfolio strategy inspired by Ray Dalio"""
    
    def __init__(self):
        super().__init__("Ray Dalio All Weather")
        self.rebalance_period = 60  # Rebalance every 60 days
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate signals based on risk parity principles"""
        signals = pd.Series(0, index=data.index)
        prices = data['Close']
        
        # Calculate volatility for risk adjustment
        returns = prices.pct_change()
        volatility = returns.rolling(30).std()
        
        # Buy more when volatility is low (stable periods)
        # Reduce exposure when volatility is high
        vol_percentile = volatility.rolling(252).rank(pct=True)
        
        # Contrarian approach: buy when others are fearful (high vol)
        signals[vol_percentile > 0.8] = 1  # High volatility = opportunity
        signals[vol_percentile < 0.2] = -1  # Low volatility = reduce risk
        
        # Trend following component
        ma_20 = prices.rolling(20).mean()
        ma_60 = prices.rolling(60).mean()
        trend_signal = ma_20 > ma_60
        
        # Combine volatility and trend signals
        final_signals = signals.copy()
        final_signals[trend_signal & (vol_percentile > 0.6)] = 1
        final_signals[~trend_signal & (vol_percentile < 0.4)] = -1
        
        return final_signals

class GeorgeSorosStrategy(BaseStrategy):
    """Reflexivity-based strategy inspired by George Soros"""
    
    def __init__(self):
        super().__init__("George Soros Reflexivity")
        self.momentum_threshold = 0.05
        self.volume_threshold = 1.5
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate signals based on reflexivity theory"""
        signals = pd.Series(0, index=data.index)
        
        prices = data['Close']
        volumes = data['Volume']
        
        # Price momentum
        momentum = prices.pct_change(10)  # 10-day momentum
        
        # Volume momentum (institutional interest)
        volume_ma = volumes.rolling(20).mean()
        volume_ratio = volumes / volume_ma
        
        # Reflexivity: strong momentum + high volume = self-reinforcing trend
        strong_momentum = abs(momentum) > self.momentum_threshold
        high_volume = volume_ratio > self.volume_threshold
        
        # Positive reflexivity (buy)
        positive_reflex = (momentum > self.momentum_threshold) & high_volume
        signals[positive_reflex] = 1
        
        # Negative reflexivity (sell)
        negative_reflex = (momentum < -self.momentum_threshold) & high_volume
        signals[negative_reflex] = -1
        
        # Trend exhaustion detection
        price_acceleration = momentum.diff()
        trend_exhaustion = (
            (momentum > 0.1) & (price_acceleration < 0) & (volume_ratio < 1.0)
        )
        signals[trend_exhaustion] = -1
        
        return signals

# Strategy performance optimization utilities
class StrategyOptimizer:
    """Utility class for strategy parameter optimization"""
    
    @staticmethod
    def optimize_momentum_parameters(data: pd.DataFrame) -> Tuple[int, int]:
        """Optimize moving average parameters for momentum strategy"""
        best_sharpe = -np.inf
        best_params = (20, 50)
        
        for short in range(5, 30, 5):
            for long in range(30, 100, 10):
                if short >= long:
                    continue
                
                strategy = BasicMomentumStrategy()
                strategy.short_window = short
                strategy.long_window = long
                
                try:
                    signals = strategy.generate_signals(data)
                    returns = strategy.calculate_returns(data, signals)
                    
                    daily_returns = pd.Series(returns).pct_change().dropna()
                    if len(daily_returns) > 0 and daily_returns.std() > 0:
                        sharpe = daily_returns.mean() / daily_returns.std() * np.sqrt(252)
                        
                        if sharpe > best_sharpe:
                            best_sharpe = sharpe
                            best_params = (short, long)
                except:
                    continue
        
        return best_params
    
    @staticmethod
    def calculate_strategy_metrics(portfolio_values: List[float]) -> Dict:
        """Calculate comprehensive performance metrics"""
        if len(portfolio_values) < 2:
            return {}
        
        returns = pd.Series(portfolio_values).pct_change().dropna()
        
        if len(returns) == 0:
            return {}
        
        total_return = (portfolio_values[-1] / portfolio_values[0] - 1) * 100
        annual_return = ((portfolio_values[-1] / portfolio_values[0]) ** (252/len(returns)) - 1) * 100
        volatility = returns.std() * np.sqrt(252) * 100
        sharpe_ratio = (annual_return - 2) / volatility if volatility > 0 else 0
        
        # Calculate maximum drawdown
        cumulative = pd.Series(portfolio_values)
        rolling_max = cumulative.expanding().max()
        drawdown = ((cumulative - rolling_max) / rolling_max * 100).min()
        
        # Calculate win rate
        win_rate = (returns > 0).mean() * 100
        
        # Calculate Calmar ratio (annual return / max drawdown)
        calmar_ratio = annual_return / abs(drawdown) if drawdown < 0 else 0
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': abs(drawdown),
            'win_rate': win_rate,
            'calmar_ratio': calmar_ratio
        }

# Risk Management Utilities
class RiskManager:
    """Risk management utilities for trading strategies"""

    @staticmethod
    def rolling_volatility(prices, window=20, annualize=True):
        """
        이동 변동성(표준편차)을 계산
        Parameters:
            prices: pandas Series 또는 numpy array, 가격 데이터 (예: 종가)
            window: int, 이동 창 크기 (기본값: 20일)
            annualize: bool, 연간화 여부 (기본값: True)
        Returns:
            pandas Series, 이동 변동성
        """
        if not isinstance(prices, pd.Series):
            prices = pd.Series(prices)
        returns = np.log(prices / prices.shift(1)).dropna()
        vol = returns.rolling(window=window).std()
        if annualize:
            vol = vol * np.sqrt(252)  # 252는 주식 시장의 평균 거래일
        return vol
    
    @staticmethod
    def apply_position_sizing(signals: pd.Series, volatility: pd.Series, 
                            target_vol: float = 0.15) -> pd.Series:
        """Apply volatility-based position sizing"""
        if len(volatility) == 0:
            return signals
        
        # Calculate position size based on volatility targeting
        vol_target = target_vol / (volatility + 1e-8)  # Avoid division by zero
        position_sizes = np.clip(vol_target, 0.1, 2.0)  # Limit position sizes
        
        return signals * position_sizes
    
    @staticmethod
    def apply_stop_loss(data: pd.DataFrame, signals: pd.Series, stop_loss_pct: float = 0.05) -> pd.Series:
        """Apply stop-loss rules to trading signals"""
        prices = data['Close']
        modified_signals = signals.copy()
        
        entry_price = None
        in_position = False
        
        for i in range(len(signals)):
            if signals.iloc[i] == 1 and not in_position:  # Entry
                entry_price = prices.iloc[i]
                in_position = True
            elif in_position and entry_price:
                current_price = prices.iloc[i]
                loss = (entry_price - current_price) / entry_price
                
                # Stop loss triggered
                if loss > stop_loss_pct:
                    modified_signals.iloc[i] = -1
                    in_position = False
                    entry_price = None
                elif signals.iloc[i] == -1:  # Normal exit
                    in_position = False
                    entry_price = None  
        return modified_signals

# 테스트 코드
if __name__ == "__main__":
    # 더미 데이터 생성
    dates = pd.date_range(start="2020-01-01", periods=100, freq="D")
    data = pd.DataFrame({
        'Close': np.random.random(100) * 100,
        'Volume': np.random.random(100) * 1000
    }, index=dates)
    
    # 전략 테스트
    strategy = BasicMomentumStrategy()
    signals = strategy.generate_signals(data)
    risk_manager = RiskManager()
    adjusted_signals = risk_manager.apply_position_sizing(signals, data)
    portfolio_values = strategy.calculate_returns(data, adjusted_signals)
    
    # 성과 지표 계산
    metrics = StrategyOptimizer.calculate_strategy_metrics(portfolio_values)
    print("성과 지표:", metrics)

class PairsTradeStrategy(BaseStrategy):
    """페어 트레이딩 전략 (Statistical Arbitrage)"""
    
    def __init__(self):
        super().__init__("Pairs Trading")
        self.lookback_period = 60
        self.entry_threshold = 2.0  # Z-score threshold
        self.exit_threshold = 0.5
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """상관관계 기반 페어 트레이딩 신호"""
        prices = data['Close']
        signals = pd.Series(0, index=data.index)
        
        # 이동평균과의 차이를 페어로 가정
        ma_short = prices.rolling(20).mean()
        ma_long = prices.rolling(60).mean()
        
        # 스프레드 계산
        spread = ma_short - ma_long
        spread_mean = spread.rolling(self.lookback_period).mean()
        spread_std = spread.rolling(self.lookback_period).std()
        
        # Z-score 계산
        z_score = (spread - spread_mean) / (spread_std + 1e-8)
        
        # 매매 신호
        signals[z_score > self.entry_threshold] = -1  # Short
        signals[z_score < -self.entry_threshold] = 1   # Long
        signals[abs(z_score) < self.exit_threshold] = 0  # Exit
        
        return signals

class FactorModelStrategy(BaseStrategy):
    """팩터 모델 전략 (Fama-French 스타일)"""
    
    def __init__(self):
        super().__init__("Factor Model")
        self.momentum_period = 252
        self.value_threshold = 0.3
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """다중 팩터 기반 신호"""
        prices = data['Close']
        signals = pd.Series(0, index=data.index)
        
        # Momentum Factor
        momentum = prices.pct_change(self.momentum_period)
        momentum_rank = momentum.rolling(60).rank(pct=True)
        
        # Value Factor (Price vs Moving Average)
        ma_200 = prices.rolling(200).mean()
        value_factor = (ma_200 - prices) / ma_200
        value_rank = value_factor.rolling(60).rank(pct=True)
        
        # Combined Score
        combined_score = (momentum_rank + value_rank) / 2
        
        # 상위 30% 매수, 하위 30% 매도
        signals[combined_score > 0.7] = 1
        signals[combined_score < 0.3] = -1
        
        return signals

class VolatilityTargetingStrategy(BaseStrategy):
    """변동성 타겟팅 전략"""
    
    def __init__(self):
        super().__init__("Volatility Targeting")
        self.target_vol = 0.15  # 15% target volatility
        self.vol_window = 30
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """변동성 기반 포지션 사이징"""
        prices = data['Close']
        returns = prices.pct_change()
        
        # 변동성 계산
        rolling_vol = returns.rolling(self.vol_window).std() * np.sqrt(252)
        
        # 포지션 사이즈 (역변동성)
        position_size = self.target_vol / (rolling_vol + 1e-8)
        position_size = np.clip(position_size, 0.1, 3.0)
        
        # 트렌드 신호
        ma_fast = prices.rolling(20).mean()
        ma_slow = prices.rolling(50).mean()
        trend_signal = (ma_fast > ma_slow).astype(int)
        
        # 변동성 조정된 신호
        signals = trend_signal * position_size
        
        return signals

class CalendarAnomalyStrategy(BaseStrategy):
    """달력 이상현상 전략 (Calendar Anomaly)"""
    
    def __init__(self):
        super().__init__("Calendar Anomaly")
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """달력 효과 기반 신호 (월말, 월초 효과 등)"""
        signals = pd.Series(0, index=data.index)
        
        # 월말/월초 효과
        for date in data.index:
            day_of_month = date.day
            month_end = (date + pd.Timedelta(days=5)).month != date.month
            
            # 월말 3일, 월초 2일 매수
            if month_end or day_of_month <= 2:
                signals[date] = 1
            # 월 중순 매도
            elif 10 <= day_of_month <= 20:
                signals[date] = -1
        
        return signals

class BreakoutStrategy(BaseStrategy):
    """돌파 전략 (Breakout Strategy)"""
    
    def __init__(self):
        super().__init__("Breakout Strategy")
        self.lookback_period = 20
        self.volume_threshold = 1.5
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """가격 돌파 기반 신호"""
        prices = data['Close']
        volumes = data['Volume']
        signals = pd.Series(0, index=data.index)
        
        # 저항선/지지선
        resistance = prices.rolling(self.lookback_period).max()
        support = prices.rolling(self.lookback_period).min()
        
        # 볼륨 확인
        avg_volume = volumes.rolling(self.lookback_period).mean()
        high_volume = volumes > (avg_volume * self.volume_threshold)
        
        # 돌파 신호
        upward_breakout = (prices > resistance.shift(1)) & high_volume
        downward_breakout = (prices < support.shift(1)) & high_volume
        
        signals[upward_breakout] = 1
        signals[downward_breakout] = -1
        
        return signals

class MachineLearningStrategy(BaseStrategy):
    """머신러닝 기반 전략 (간단한 예시)"""
    
    def __init__(self):
        super().__init__("Machine Learning")
        self.feature_window = 20
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """특성 기반 예측 신호 (simplified ML approach)"""
        prices = data['Close']
        signals = pd.Series(0, index=data.index)
        
        # Feature engineering
        returns = prices.pct_change()
        
        # Technical indicators as features
        rsi = self._calculate_rsi(prices, 14)
        bb_upper, bb_lower = self._calculate_bollinger_bands(prices, 20)
        macd = self._calculate_macd(prices)
        
        # Simple rule-based "ML" (실제로는 규칙 기반)
        buy_condition = (
            (rsi < 30) &  # Oversold
            (prices < bb_lower) &  # Below lower band
            (macd > 0)  # Positive MACD
        )
        
        sell_condition = (
            (rsi > 70) &  # Overbought
            (prices > bb_upper) &  # Above upper band
            (macd < 0)  # Negative MACD
        )
        
        signals[buy_condition] = 1
        signals[sell_condition] = -1
        
        return signals
    
    def _calculate_rsi(self, prices, period=14):
        """RSI 계산"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / (loss + 1e-8)
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_bollinger_bands(self, prices, period=20, std_dev=2):
        """볼린저 밴드 계산"""
        ma = prices.rolling(period).mean()
        std = prices.rolling(period).std()
        upper = ma + (std * std_dev)
        lower = ma - (std * std_dev)
        return upper, lower
    
    def _calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """MACD 계산"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        return macd

class StatisticalArbitrageStrategy(BaseStrategy):
    """통계적 차익거래 전략"""
    
    def __init__(self):
        super().__init__("Statistical Arbitrage")
        self.cointegration_window = 60
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """통계적 차익거래 신호"""
        prices = data['Close']
        signals = pd.Series(0, index=data.index)
        
        # 두 가격 시리즈 간의 관계 (여기서는 단순화)
        ma_20 = prices.rolling(20).mean()
        ma_60 = prices.rolling(60).mean()
        
        # 스프레드
        spread = ma_20 - ma_60
        spread_ma = spread.rolling(30).mean()
        spread_std = spread.rolling(30).std()
        
        # Z-score
        z_score = (spread - spread_ma) / (spread_std + 1e-8)
        
        # 매매 신호
        signals[z_score > 2] = -1  # Mean reversion (short)
        signals[z_score < -2] = 1   # Mean reversion (long)
        signals[abs(z_score) < 0.5] = 0  # Exit
        
        return signals

class EventDrivenStrategy(BaseStrategy):
    """이벤트 드리븐 전략"""
    
    def __init__(self):
        super().__init__("Event Driven")
        self.volume_spike_threshold = 2.0
        self.price_move_threshold = 0.05
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """이벤트 기반 신호 (볼륨 스파이크, 가격 급변동)"""
        prices = data['Close']
        volumes = data['Volume']
        signals = pd.Series(0, index=data.index)
        
        # 볼륨 스파이크 감지
        avg_volume = volumes.rolling(20).mean()
        volume_spike = volumes > (avg_volume * self.volume_spike_threshold)
        
        # 가격 급변동 감지
        returns = prices.pct_change()
        price_spike = abs(returns) > self.price_move_threshold
        
        # 이벤트 발생시
        event_detected = volume_spike & price_spike
        
        # 가격 상승 + 이벤트 = 매수
        signals[(returns > 0) & event_detected] = 1
        # 가격 하락 + 이벤트 = 매도
        signals[(returns < 0) & event_detected] = -1
        
        return signals

class QuantMomentumStrategy(BaseStrategy):
    """퀀트 모멘텀 전략 (AQR 스타일)"""
    
    def __init__(self):
        super().__init__("Quant Momentum")
        self.short_momentum = 21  # 1 month
        self.medium_momentum = 63  # 3 months
        self.long_momentum = 252  # 12 months
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """다중 기간 모멘텀 신호"""
        prices = data['Close']
        signals = pd.Series(0, index=data.index)
        
        # 다양한 기간 모멘텀
        mom_1m = prices.pct_change(self.short_momentum)
        mom_3m = prices.pct_change(self.medium_momentum)
        mom_12m = prices.pct_change(self.long_momentum)
        
        # 모멘텀 점수
        momentum_score = (
            mom_1m.rolling(20).rank(pct=True) * 0.3 +
            mom_3m.rolling(20).rank(pct=True) * 0.4 +
            mom_12m.rolling(20).rank(pct=True) * 0.3
        )
        
        # 상위/하위 신호
        signals[momentum_score > 0.8] = 1
        signals[momentum_score < 0.2] = -1
        
        return signals

class CarryTradeStrategy(BaseStrategy):
    """캐리 트레이드 전략"""
    
    def __init__(self):
        super().__init__("Carry Trade")
        self.dividend_proxy_period = 252
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """캐리(수익률) 기반 신호"""
        prices = data['Close']
        signals = pd.Series(0, index=data.index)
        
        # 배당 수익률 프록시 (가격 대비 안정성)
        price_volatility = prices.pct_change().rolling(30).std()
        avg_volatility = price_volatility.rolling(60).mean()
        
        # 저변동성 = 높은 캐리
        carry_score = 1 / (price_volatility + 1e-8)
        carry_rank = carry_score.rolling(60).rank(pct=True)
        
        # 트렌드 필터
        ma_trend = prices.rolling(50).mean() > prices.rolling(100).mean()
        
        # 높은 캐리 + 상승 트렌드 = 매수
        signals[carry_rank > 0.7] = 1
        signals[carry_rank < 0.3] = -1
        
        return signals

class RiskParityStrategy(BaseStrategy):
    """리스크 패리티 전략"""
    
    def __init__(self):
        super().__init__("Risk Parity")
        self.lookback_period = 60
        self.rebalance_freq = 20
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """리스크 기반 포지션 사이징"""
        prices = data['Close']
        returns = prices.pct_change()
        signals = pd.Series(0, index=data.index)
        
        # 변동성 계산
        volatility = returns.rolling(self.lookback_period).std()
        
        # 역변동성 가중
        inv_vol_weight = 1 / (volatility + 1e-8)
        normalized_weight = inv_vol_weight / inv_vol_weight.rolling(20).mean()
        
        # 트렌드 방향
        ma_20 = prices.rolling(20).mean()
        ma_60 = prices.rolling(60).mean()
        trend_direction = (ma_20 > ma_60).astype(int) * 2 - 1  # +1 or -1
        
        # 리스크 조정된 신호
        signals = trend_direction * np.clip(normalized_weight, 0.1, 2.0)
        
        return signals

class ContrariannStrategy(BaseStrategy):
    """역발상 투자 전략"""
    
    def __init__(self):
        super().__init__("Contrarian")
        self.sentiment_window = 30
        self.extreme_threshold = 0.1
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """역발상 신호 (시장 극단에서 반대 포지션)"""
        prices = data['Close']
        volumes = data['Volume']
        signals = pd.Series(0, index=data.index)
        
        # 가격 모멘텀
        returns = prices.pct_change()
        cumulative_returns = returns.rolling(self.sentiment_window).sum()
        
        # 볼륨 트렌드
        volume_trend = volumes.rolling(20).mean() / volumes.rolling(60).mean()
        
        # 극단적 상황 감지
        extreme_up = (cumulative_returns > cumulative_returns.rolling(60).quantile(0.9))
        extreme_down = (cumulative_returns < cumulative_returns.rolling(60).quantile(0.1))
        
        # 역발상 신호
        signals[extreme_up & (volume_trend > 1.2)] = -1  # 극단적 상승시 매도
        signals[extreme_down & (volume_trend > 1.2)] = 1   # 극단적 하락시 매수
        
        return signals

# 전략 매니저 클래스 업데이트
class ExpandedStrategyManager:
    """확장된 전략 매니저"""
    
    def __init__(self):
        self.strategies = {
           
            'Basic Momentum': BasicMomentumStrategy(),
            'Basic Mean Reversion': BasicMeanReversionStrategy(),
            'Warren Buffett Value': WarrenBuffettStrategy(),
            'Benjamin Graham Deep Value': BenjaminGrahamStrategy(),
            'Peter Lynch Growth': PeterLynchStrategy(),
            'Ray Dalio All Weather': RayDalioStrategy(),
            'George Soros Reflexivity': GeorgeSorosStrategy(),
            'Pairs Trading': PairsTradeStrategy(),
            'Factor Model': FactorModelStrategy(),
            'Volatility Targeting': VolatilityTargetingStrategy(),
            'Calendar Anomaly': CalendarAnomalyStrategy(),
            'Breakout Strategy': BreakoutStrategy(),
            'Machine Learning': MachineLearningStrategy(),
            'Statistical Arbitrage': StatisticalArbitrageStrategy(),
            'Event Driven': EventDrivenStrategy(),
            'Quant Momentum': QuantMomentumStrategy(),
            'Carry Trade': CarryTradeStrategy(),
            'Risk Parity': RiskParityStrategy(),
            'Contrarian': ContrariannStrategy()
        }
    
    def get_strategy(self, name: str):
        """전략 객체 반환"""
        return self.strategies.get(name)
    
    def list_strategies(self):
        """전략 목록 반환"""
        return list(self.strategies.keys())
    
    def get_strategy_description(self, name: str):
        """전략 설명 반환"""
        descriptions = {
            'Pairs Trading': '상관관계가 높은 두 자산 간의 가격 차이를 이용한 시장중립 전략',
            'Factor Model': '모멘텀, 가치 등 다중 팩터를 조합한 체계적 투자 전략',
            'Volatility Targeting': '목표 변동성을 유지하기 위한 동적 포지션 사이징 전략',
            'Calendar Anomaly': '월말/월초 효과 등 달력상 이상현상을 이용한 전략',
            'Breakout Strategy': '지지/저항선 돌파를 포착하는 추세 추종 전략',
            'Machine Learning': '기술적 지표를 특성으로 활용한 패턴 인식 전략',
            'Statistical Arbitrage': '통계적 관계를 이용한 시장중립 차익거래 전략',
            'Event Driven': '볼륨 스파이크, 가격 급변동 등 이벤트 기반 전략',
            'Quant Momentum': '다중 기간 모멘텀을 체계적으로 포착하는 AQR 스타일 전략',
            'Carry Trade': '안정적 수익(캐리) 추구를 위한 저변동성 자산 선호 전략',
            'Risk Parity': '동일한 리스크 기여도를 목표로 하는 포트폴리오 구성 전략',
            'Contrarian': '시장 극단에서 반대 방향 포지션을 취하는 역발상 전략'
        }
        return descriptions.get(name, "설명이 없습니다.")

# 테스트 코드
if __name__ == "__main__":
    # 전략 매니저 생성
    manager = ExpandedStrategyManager()
    
    print("사용 가능한 퀀트 전략들:")
    print("=" * 50)
    
    for i, strategy_name in enumerate(manager.list_strategies(), 1):
        description = manager.get_strategy_description(strategy_name)
        print(f"{i:2d}. {strategy_name}")
        print(f"    📝 {description}")
        print()
    
    print(f"총 {len(manager.list_strategies())}개의 전략이 구현되었습니다! 🎉")   