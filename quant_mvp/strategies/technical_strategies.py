"""
file: quant_mvp/strategies/technical_strategies.py
기술적 분석 전략들 모멘텀, RSI, 볼린저밴드, MACD, 평균회귀 전략 포함
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from datetime import datetime
import logging

from .base_strategy import BaseStrategy, Signal

logger = logging.getLogger(__name__)

class MomentumStrategy(BaseStrategy):
    """모멘텀 전략 - 과거 수익률 기반"""
    
    def __init__(self, params: Dict[str, Any] = None):
        default_params = {
            'lookback_period': 20,
            'min_return_threshold': 0.02,
            'top_n': 10
        }
        if params:
            default_params.update(params)
        
        super().__init__("Momentum", default_params)
    
    def get_required_data(self) -> List[str]:
        return ['close', 'volume']
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """모멘텀 신호 생성"""
        if not self.validate_data(data):
            return []
        
        signals = []
        lookback = self.params['lookback_period']
        min_threshold = self.params['min_return_threshold']
        top_n = self.params['top_n']
        
        # 종목별로 모멘텀 계산
        momentum_scores = {}
        
        for symbol in data['symbol'].unique():
            symbol_data = data[data['symbol'] == symbol].copy()
            symbol_data = symbol_data.sort_values('date')
            
            if len(symbol_data) < lookback + 1:
                continue
            
            # 최근 수익률 계산
            latest_price = symbol_data['close'].iloc[-1]
            past_price = symbol_data['close'].iloc[-(lookback + 1)]
            
            if past_price > 0:
                momentum = (latest_price / past_price) - 1
                
                if momentum > min_threshold:
                    momentum_scores[symbol] = {
                        'momentum': momentum,
                        'price': latest_price,
                        'volume': symbol_data['volume'].iloc[-1],
                        'date': symbol_data['date'].iloc[-1]
                    }
        
        # 상위 종목 선택
        if momentum_scores:
            sorted_symbols = sorted(momentum_scores.items(), 
                                  key=lambda x: x[1]['momentum'], 
                                  reverse=True)[:top_n]
            
            # 동일 가중치 할당
            weight_per_stock = 1.0 / len(sorted_symbols)
            
            for symbol, data_dict in sorted_symbols:
                signals.append(Signal(
                    symbol=symbol,
                    action='buy',
                    weight=weight_per_stock,
                    price=data_dict['price'],
                    timestamp=data_dict['date'],
                    confidence=min(data_dict['momentum'] / 0.1, 1.0),  # 정규화
                    reason=f"Momentum: {data_dict['momentum']:.2%}"
                ))
        
        return signals
    
    def get_parameter_bounds(self) -> Dict[str, Tuple[float, float]]:
        return {
            'lookback_period': (5, 60),
            'min_return_threshold': (0.01, 0.1),
            'top_n': (5, 20)
        }

class RSIStrategy(BaseStrategy):
    """RSI 역추세 전략"""
    
    def __init__(self, params: Dict[str, Any] = None):
        default_params = {
            'period': 14,
            'overbought': 70,
            'oversold': 30,
            'top_n': 10
        }
        if params:
            default_params.update(params)
        
        super().__init__("RSI", default_params)
    
    def get_required_data(self) -> List[str]:
        return ['close', 'volume']
    
    def calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """RSI 계산"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """RSI 신호 생성"""
        if not self.validate_data(data):
            return []
        
        signals = []
        period = self.params['period']
        overbought = self.params['overbought']
        oversold = self.params['oversold']
        top_n = self.params['top_n']
        
        buy_candidates = []
        sell_candidates = []
        
        for symbol in data['symbol'].unique():
            symbol_data = data[data['symbol'] == symbol].copy()
            symbol_data = symbol_data.sort_values('date')
            
            if len(symbol_data) < period + 1:
                continue
            
            # RSI 계산
            rsi = self.calculate_rsi(symbol_data['close'], period)
            latest_rsi = rsi.iloc[-1]
            
            if pd.isna(latest_rsi):
                continue
            
            latest_price = symbol_data['close'].iloc[-1]
            latest_date = symbol_data['date'].iloc[-1]
            
            # 매수 신호 (과매도)
            if latest_rsi <= oversold:
                buy_candidates.append({
                    'symbol': symbol,
                    'rsi': latest_rsi,
                    'price': latest_price,
                    'date': latest_date,
                    'score': oversold - latest_rsi  # 더 낮은 RSI일수록 높은 점수
                })
            
            # 매도 신호 (과매수)
            elif latest_rsi >= overbought:
                sell_candidates.append({
                    'symbol': symbol,
                    'rsi': latest_rsi,
                    'price': latest_price,
                    'date': latest_date,
                    'score': latest_rsi - overbought
                })
        
        # 상위 매수 후보 선택
        if buy_candidates:
            buy_candidates.sort(key=lambda x: x['score'], reverse=True)
            selected_buys = buy_candidates[:top_n//2]
            
            if selected_buys:
                weight_per_stock = 1.0 / len(selected_buys)
                
                for candidate in selected_buys:
                    signals.append(Signal(
                        symbol=candidate['symbol'],
                        action='buy',
                        weight=weight_per_stock,
                        price=candidate['price'],
                        timestamp=candidate['date'],
                        confidence=(oversold - candidate['rsi']) / oversold,
                        reason=f"RSI oversold: {candidate['rsi']:.1f}"
                    ))
        
        return signals
    
    def get_parameter_bounds(self) -> Dict[str, Tuple[float, float]]:
        return {
            'period': (7, 30),
            'overbought': (65, 85),
            'oversold': (15, 35),
            'top_n': (5, 20)
        }

class BollingerBandsStrategy(BaseStrategy):
    """볼린저밴드 평균회귀 전략"""
    
    def __init__(self, params: Dict[str, Any] = None):
        default_params = {
            'period': 20,
            'std_dev': 2.0,
            'top_n': 10
        }
        if params:
            default_params.update(params)
        
        super().__init__("BollingerBands", default_params)
    
    def get_required_data(self) -> List[str]:
        return ['close', 'volume']
    
    def calculate_bollinger_bands(self, prices: pd.Series, period: int, std_dev: float) -> Dict[str, pd.Series]:
        """볼린저밴드 계산"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return {
            'middle': sma,
            'upper': upper_band,
            'lower': lower_band,
            'width': (upper_band - lower_band) / sma
        }
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """볼린저밴드 신호 생성"""
        if not self.validate_data(data):
            return []
        
        signals = []
        period = self.params['period']
        std_dev = self.params['std_dev']
        top_n = self.params['top_n']
        
        buy_candidates = []
        
        for symbol in data['symbol'].unique():
            symbol_data = data[data['symbol'] == symbol].copy()
            symbol_data = symbol_data.sort_values('date')
            
            if len(symbol_data) < period + 1:
                continue
            
            # 볼린저밴드 계산
            bb = self.calculate_bollinger_bands(symbol_data['close'], period, std_dev)
            
            latest_price = symbol_data['close'].iloc[-1]
            latest_date = symbol_data['date'].iloc[-1]
            latest_lower = bb['lower'].iloc[-1]
            latest_upper = bb['upper'].iloc[-1]
            latest_middle = bb['middle'].iloc[-1]
            
            if pd.isna(latest_lower) or pd.isna(latest_upper):
                continue
            
            # 하단 밴드 근처에서 매수 (평균회귀 기대)
            if latest_price <= latest_lower * 1.02:  # 2% 버퍼
                distance_from_lower = (latest_price - latest_lower) / latest_lower
                buy_candidates.append({
                    'symbol': symbol,
                    'price': latest_price,
                    'date': latest_date,
                    'distance': abs(distance_from_lower),
                    'bb_position': (latest_price - latest_lower) / (latest_upper - latest_lower)
                })
        
        # 상위 후보 선택 (하단에 더 가까운 종목 우선)
        if buy_candidates:
            buy_candidates.sort(key=lambda x: x['distance'])
            selected = buy_candidates[:top_n]
            
            if selected:
                weight_per_stock = 1.0 / len(selected)
                
                for candidate in selected:
                    signals.append(Signal(
                        symbol=candidate['symbol'],
                        action='buy',
                        weight=weight_per_stock,
                        price=candidate['price'],
                        timestamp=candidate['date'],
                        confidence=1.0 - candidate['distance'],
                        reason=f"BB position: {candidate['bb_position']:.2f}"
                    ))
        
        return signals
    
    def get_parameter_bounds(self) -> Dict[str, Tuple[float, float]]:
        return {
            'period': (10, 50),
            'std_dev': (1.5, 3.0),
            'top_n': (5, 20)
        }

class MACDStrategy(BaseStrategy):
    """MACD 추세추종 전략"""
    
    def __init__(self, params: Dict[str, Any] = None):
        default_params = {
            'fast_period': 12,
            'slow_period': 26,
            'signal_period': 9,
            'top_n': 10
        }
        if params:
            default_params.update(params)
        
        super().__init__("MACD", default_params)
    
    def get_required_data(self) -> List[str]:
        return ['close', 'volume']
    
    def calculate_macd(self, prices: pd.Series, fast: int, slow: int, signal: int) -> Dict[str, pd.Series]:
        """MACD 계산"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        
        return {
            'macd': macd,
            'signal': signal_line,
            'histogram': histogram
        }
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """MACD 신호 생성"""
        if not self.validate_data(data):
            return []
        
        signals = []
        fast = self.params['fast_period']
        slow = self.params['slow_period']
        signal_period = self.params['signal_period']
        top_n = self.params['top_n']
        
        buy_candidates = []
        
        for symbol in data['symbol'].unique():
            symbol_data = data[data['symbol'] == symbol].copy()
            symbol_data = symbol_data.sort_values('date')
            
            if len(symbol_data) < slow + signal_period:
                continue
            
            # MACD 계산
            macd_data = self.calculate_macd(symbol_data['close'], fast, slow, signal_period)
            
            if len(macd_data['macd']) < 2:
                continue
            
            # 골든크로스 확인 (MACD > Signal)
            current_macd = macd_data['macd'].iloc[-1]
            current_signal = macd_data['signal'].iloc[-1]
            prev_macd = macd_data['macd'].iloc[-2]
            prev_signal = macd_data['signal'].iloc[-2]
            
            if (pd.isna(current_macd) or pd.isna(current_signal) or 
                pd.isna(prev_macd) or pd.isna(prev_signal)):
                continue
            
            # 골든크로스 발생 (이전에는 MACD < Signal, 현재는 MACD > Signal)
            if prev_macd <= prev_signal and current_macd > current_signal:
                latest_price = symbol_data['close'].iloc[-1]
                latest_date = symbol_data['date'].iloc[-1]
                
                # 히스토그램 강도로 신호 품질 평가
                histogram_strength = macd_data['histogram'].iloc[-1]
                
                buy_candidates.append({
                    'symbol': symbol,
                    'price': latest_price,
                    'date': latest_date,
                    'macd_diff': current_macd - current_signal,
                    'histogram': histogram_strength
                })
        
        # 상위 후보 선택
        if buy_candidates:
            buy_candidates.sort(key=lambda x: x['macd_diff'], reverse=True)
            selected = buy_candidates[:top_n]
            
            if selected:
                weight_per_stock = 1.0 / len(selected)
                
                for candidate in selected:
                    signals.append(Signal(
                        symbol=candidate['symbol'],
                        action='buy',
                        weight=weight_per_stock,
                        price=candidate['price'],
                        timestamp=candidate['date'],
                        confidence=min(candidate['macd_diff'] / 10, 1.0),
                        reason=f"MACD Golden Cross: {candidate['macd_diff']:.3f}"
                    ))
        
        return signals
    
    def get_parameter_bounds(self) -> Dict[str, Tuple[float, float]]:
        return {
            'fast_period': (8, 20),
            'slow_period': (20, 35),
            'signal_period': (5, 15),
            'top_n': (5, 20)
        }

class MeanReversionStrategy(BaseStrategy):
    """평균회귀 전략"""
    
    def __init__(self, params: Dict[str, Any] = None):
        default_params = {
            'lookback_period': 20,
            'zscore_threshold': 2.0,
            'top_n': 10
        }
        if params:
            default_params.update(params)
        
        super().__init__("MeanReversion", default_params)
    
    def get_required_data(self) -> List[str]:
        return ['close', 'volume']
    
    def calculate_zscore(self, prices: pd.Series, period: int) -> pd.Series:
        """Z-Score 계산"""
        rolling_mean = prices.rolling(window=period).mean()
        rolling_std = prices.rolling(window=period).std()
        zscore = (prices - rolling_mean) / rolling_std
        return zscore
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """평균회귀 신호 생성"""
        if not self.validate_data(data):
            return []
        
        signals = []
        lookback = self.params['lookback_period']
        threshold = self.params['zscore_threshold']
        top_n = self.params['top_n']
        
        buy_candidates = []
        
        for symbol in data['symbol'].unique():
            symbol_data = data[data['symbol'] == symbol].copy()
            symbol_data = symbol_data.sort_values('date')
            
            if len(symbol_data) < lookback + 1:
                continue
            
            # Z-Score 계산
            zscore = self.calculate_zscore(symbol_data['close'], lookback)
            latest_zscore = zscore.iloc[-1]
            
            if pd.isna(latest_zscore):
                continue
            
            # 과매도 구간에서 매수 (Z-Score < -threshold)
            if latest_zscore <= -threshold:
                latest_price = symbol_data['close'].iloc[-1]
                latest_date = symbol_data['date'].iloc[-1]
                
                buy_candidates.append({
                    'symbol': symbol,
                    'price': latest_price,
                    'date': latest_date,
                    'zscore': latest_zscore,
                    'score': abs(latest_zscore)  # 더 극단적일수록 높은 점수
                })
        
        # 상위 후보 선택
        if buy_candidates:
            buy_candidates.sort(key=lambda x: x['score'], reverse=True)
            selected = buy_candidates[:top_n]
            
            if selected:
                weight_per_stock = 1.0 / len(selected)
                
                for candidate in selected:
                    signals.append(Signal(
                        symbol=candidate['symbol'],
                        action='buy',
                        weight=weight_per_stock,
                        price=candidate['price'],
                        timestamp=candidate['date'],
                        confidence=min(abs(candidate['zscore']) / 3.0, 1.0),
                        reason=f"Z-Score: {candidate['zscore']:.2f}"
                    ))
        
        return signals
    
    def get_parameter_bounds(self) -> Dict[str, Tuple[float, float]]:
        return {
            'lookback_period': (10, 50),
            'zscore_threshold': (1.5, 3.0),
            'top_n': (5, 20)
        }