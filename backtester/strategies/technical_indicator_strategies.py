"""
File: backtester/strategies/technical_indicator_strategies.py
Core Technical Analysis Based Strategies (Top 5 Technical Indicators)
"""

import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy

class MovingAverageStrategy(BaseStrategy):
    """Moving Average Based Trend Following Strategy - 이동평균 전략"""
    
    def __init__(self):
        super().__init__("Moving Average Strategy")
        self.short_window = 20         # 단기 이동평균
        self.medium_window = 50        # 중기 이동평균
        self.long_window = 200         # 장기 이동평균
        self.use_exponential = True    # 지수이동평균 사용 여부
        
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """이동평균 기반 매매신호 생성"""
        close = data['Close']
        signals = pd.Series(0, index=data.index)
        
        if self.use_exponential:
            # 지수이동평균 (EMA)
            ema_short = close.ewm(span=self.short_window).mean()
            ema_medium = close.ewm(span=self.medium_window).mean()
            ema_long = close.ewm(span=self.long_window).mean()
            
            # 골든크로스/데드크로스 신호
            golden_cross = (ema_short > ema_medium) & (ema_short.shift(1) <= ema_medium.shift(1))
            death_cross = (ema_short < ema_medium) & (ema_short.shift(1) >= ema_medium.shift(1))
            
            # 장기 트렌드 확인
            long_term_uptrend = ema_medium > ema_long
            long_term_downtrend = ema_medium < ema_long
            
        else:
            # 단순이동평균 (SMA)
            sma_short = close.rolling(window=self.short_window).mean()
            sma_medium = close.rolling(window=self.medium_window).mean()
            sma_long = close.rolling(window=self.long_window).mean()
            
            golden_cross = (sma_short > sma_medium) & (sma_short.shift(1) <= sma_medium.shift(1))
            death_cross = (sma_short < sma_medium) & (sma_short.shift(1) >= sma_medium.shift(1))
            
            long_term_uptrend = sma_medium > sma_long
            long_term_downtrend = sma_medium < sma_long
        
        # 거래량 확인 (신호 강도 조절)
        volume = data.get('Volume', pd.Series(1, index=close.index))
        avg_volume = volume.rolling(window=20).mean()
        volume_confirmation = volume > avg_volume * 1.1
        
        # 매수 신호: 골든크로스 + 장기 상승추세
        strong_buy = golden_cross & long_term_uptrend & volume_confirmation
        weak_buy = golden_cross & long_term_uptrend & (~volume_confirmation)
        
        # 매도 신호: 데드크로스 또는 장기 하락추세 진입
        sell_signal = death_cross | (long_term_downtrend & (close < ema_short if self.use_exponential else close < sma_short))
        
        signals[strong_buy] = 1.0
        signals[weak_buy] = 0.6
        signals[sell_signal] = -1
        
        return signals
    
    def calculate_ma_strength(self, data: pd.DataFrame) -> pd.Series:
        """이동평균 신호 강도 계산"""
        close = data['Close']
        
        if self.use_exponential:
            ema_short = close.ewm(span=self.short_window).mean()
            ema_medium = close.ewm(span=self.medium_window).mean()
            ema_long = close.ewm(span=self.long_window).mean()
            
            # 이동평균 배열 강도
            ma_alignment = (
                (close > ema_short).astype(int) +
                (ema_short > ema_medium).astype(int) +
                (ema_medium > ema_long).astype(int)
            ) / 3.0
            
        else:
            sma_short = close.rolling(window=self.short_window).mean()
            sma_medium = close.rolling(window=self.medium_window).mean()
            sma_long = close.rolling(window=self.long_window).mean()
            
            ma_alignment = (
                (close > sma_short).astype(int) +
                (sma_short > sma_medium).astype(int) +
                (sma_medium > sma_long).astype(int)
            ) / 3.0
        
        return ma_alignment

class RSIStrategy(BaseStrategy):
    """RSI Based Mean Reversion Strategy - RSI 전략"""
    
    def __init__(self):
        super().__init__("RSI Strategy")
        self.rsi_period = 14           # RSI 계산 기간
        self.oversold_threshold = 30   # 과매도 기준
        self.overbought_threshold = 70 # 과매수 기준
        self.extreme_oversold = 20     # 극도 과매도
        self.extreme_overbought = 80   # 극도 과매수
        
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """RSI 기반 매매신호 생성"""
        close = data['Close']
        signals = pd.Series(0, index=data.index)