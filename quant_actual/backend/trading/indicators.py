# file: backend/trading/indicators.py

import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Union
import logging

logger = logging.getLogger(__name__)

class TechnicalIndicators:
    """기술적 지표 계산 클래스"""
    
    @staticmethod
    def moving_average(prices: List[float], period: int) -> List[float]:
        """단순 이동평균 (SMA) 계산"""
        if len(prices) < period:
            return []
        
        try:
            df = pd.Series(prices)
            ma = df.rolling(window=period).mean()
            return ma.dropna().tolist()
        except Exception as e:
            logger.error(f"이동평균 계산 오류: {e}")
            return []
    
    @staticmethod
    def exponential_moving_average(prices: List[float], period: int) -> List[float]:
        """지수 이동평균 (EMA) 계산"""
        if len(prices) < period:
            return []
        
        try:
            df = pd.Series(prices)
            ema = df.ewm(span=period, adjust=False).mean()
            return ema.tolist()
        except Exception as e:
            logger.error(f"지수이동평균 계산 오류: {e}")
            return []
    
    @staticmethod
    def bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2.0) -> Optional[Dict[str, List[float]]]:
        """볼린저 밴드 계산"""
        if len(prices) < period:
            return None
        
        try:
            df = pd.Series(prices)
            
            # 중간선 (이동평균)
            middle = df.rolling(window=period).mean()
            
            # 표준편차
            std = df.rolling(window=period).std()
            
            # 상단선, 하단선
            upper = middle + (std * std_dev)
            lower = middle - (std * std_dev)
            
            return {
                'upper': upper.dropna().tolist(),
                'middle': middle.dropna().tolist(),
                'lower': lower.dropna().tolist()
            }
        except Exception as e:
            logger.error(f"볼린저밴드 계산 오류: {e}")
            return None
    
    @staticmethod
    def rsi(prices: List[float], period: int = 14) -> List[float]:
        """RSI (Relative Strength Index) 계산"""
        if len(prices) < period + 1:
            return []
        
        try:
            df = pd.Series(prices)
            
            # 가격 변화 계산
            delta = df.diff()
            
            # 상승분과 하락분 분리
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            # RS 계산
            rs = gain / loss
            
            # RSI 계산
            rsi = 100 - (100 / (1 + rs))
            
            return rsi.dropna().tolist()
        except Exception as e:
            logger.error(f"RSI 계산 오류: {e}")
            return []
    
    @staticmethod
    def macd(prices: List[float], fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Optional[Dict[str, List[float]]]:
        """MACD (Moving Average Convergence Divergence) 계산"""
        if len(prices) < slow_period:
            return None
        
        try:
            df = pd.Series(prices)
            
            # 빠른 EMA와 느린 EMA 계산
            ema_fast = df.ewm(span=fast_period).mean()
            ema_slow = df.ewm(span=slow_period).mean()
            
            # MACD 라인
            macd_line = ema_fast - ema_slow
            
            # 신호선 (MACD의 EMA)
            signal_line = macd_line.ewm(span=signal_period).mean()
            
            # 히스토그램
            histogram = macd_line - signal_line
            
            return {
                'macd': macd_line.dropna().tolist(),
                'signal': signal_line.dropna().tolist(),
                'histogram': histogram.dropna().tolist()
            }
        except Exception as e:
            logger.error(f"MACD 계산 오류: {e}")
            return None
    
    @staticmethod
    def calculate_volatility(prices: List[float], period: int = 20) -> float:
        """변동성 계산 (표준편차 기반)"""
        if len(prices) < period:
            return 0.0
        
        try:
            df = pd.Series(prices)
            returns = df.pct_change().dropna()
            volatility = returns.rolling(window=period).std().iloc[-1]
            
            # 연율화 (일간 변동성을 연간으로 변환)
            return volatility * np.sqrt(252)  # 252 = 연간 거래일수
        except Exception as e:
            logger.error(f"변동성 계산 오류: {e}")
            return 0.0
    
    @staticmethod
    def calculate_correlation(prices1: List[float], prices2: List[float], period: int = 20) -> float:
        """두 자산간 상관계수 계산"""
        if len(prices1) < period or len(prices2) < period or len(prices1) != len(prices2):
            return 0.0
        
        try:
            df1 = pd.Series(prices1)
            df2 = pd.Series(prices2)
            
            returns1 = df1.pct_change().dropna()
            returns2 = df2.pct_change().dropna()
            
            correlation = returns1.rolling(window=period).corr(returns2).iloc[-1]
            
            return correlation if not np.isnan(correlation) else 0.0
        except Exception as e:
            logger.error(f"상관계수 계산 오류: {e}")
            return 0.0
    
    @staticmethod
    def ichimoku_cloud(high_prices: List[float], low_prices: List[float], close_prices: List[float], 
                      tenkan_period: int = 9, kijun_period: int = 26, senkou_span_b_period: int = 52) -> Optional[Dict[str, List[float]]]:
        """일목균형표 계산"""
        if len(high_prices) < senkou_span_b_period:
            return None
        
        try:
            high_df = pd.Series(high_prices)
            low_df = pd.Series(low_prices)
            close_df = pd.Series(close_prices)
            
            # 전환선 (Tenkan-sen)
            tenkan_high = high_df.rolling(window=tenkan_period).max()
            tenkan_low = low_df.rolling(window=tenkan_period).min()
            tenkan_sen = (tenkan_high + tenkan_low) / 2
            
            # 기준선 (Kijun-sen)
            kijun_high = high_df.rolling(window=kijun_period).max()
            kijun_low = low_df.rolling(window=kijun_period).min()
            kijun_sen = (kijun_high + kijun_low) / 2
            
            # 선행스팬 A (Senkou Span A)
            senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(kijun_period)
            
            # 선행스팬 B (Senkou Span B)
            senkou_high = high_df.rolling(window=senkou_span_b_period).max()
            senkou_low = low_df.rolling(window=senkou_span_b_period).min()
            senkou_span_b = ((senkou_high + senkou_low) / 2).shift(kijun_period)
            
            # 후행스팬 (Chikou Span)
            chikou_span = close_df.shift(-kijun_period)
            
            return {
                'tenkan_sen': tenkan_sen.dropna().tolist(),
                'kijun_sen': kijun_sen.dropna().tolist(),
                'senkou_span_a': senkou_span_a.dropna().tolist(),
                'senkou_span_b': senkou_span_b.dropna().tolist(),
                'chikou_span': chikou_span.dropna().tolist()
            }
        except Exception as e:
            logger.error(f"일목균형표 계산 오류: {e}")
            return None

class RiskMetrics:
    """리스크 지표 계산 클래스"""
    
    @staticmethod
    def calculate_max_drawdown(prices: List[float]) -> Dict[str, float]:
        """최대 낙폭 계산"""
        if not prices:
            return {'max_drawdown': 0.0, 'max_drawdown_pct': 0.0}
        
        try:
            peak = prices[0]
            max_drawdown = 0.0
            max_drawdown_pct = 0.0
            
            for price in prices:
                if price > peak:
                    peak = price
                else:
                    drawdown = peak - price
                    drawdown_pct = drawdown / peak
                    
                    if drawdown > max_drawdown:
                        max_drawdown = drawdown
                        max_drawdown_pct = drawdown_pct
            
            return {
                'max_drawdown': max_drawdown,
                'max_drawdown_pct': max_drawdown_pct
            }
        except:
            return {'max_drawdown': 0.0, 'max_drawdown_pct': 0.0}

# 나머지 클래스들은 기존과 동일하게 유지...