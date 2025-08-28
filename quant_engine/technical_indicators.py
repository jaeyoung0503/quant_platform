"""
Technical Indicators Module - 기술적 지표 계산 함수들
RSI, MACD, 볼린저밴드, 이동평균 등 200여 라인
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional, Union
import warnings

# 이동평균 관련 함수들
def simple_moving_average(prices: pd.Series, window: int) -> pd.Series:
    """단순 이동평균 (SMA)"""
    if len(prices) < window:
        return pd.Series(dtype=float)
    return prices.rolling(window=window).mean()

def exponential_moving_average(prices: pd.Series, window: int) -> pd.Series:
    """지수 이동평균 (EMA)"""
    if len(prices) < window:
        return pd.Series(dtype=float)
    return prices.ewm(span=window).mean()

def weighted_moving_average(prices: pd.Series, window: int) -> pd.Series:
    """가중 이동평균 (WMA)"""
    if len(prices) < window:
        return pd.Series(dtype=float)
    
    weights = np.arange(1, window + 1)
    wma_values = []
    
    for i in range(window - 1, len(prices)):
        period_prices = prices.iloc[i - window + 1:i + 1]
        wma_value = np.dot(period_prices, weights) / weights.sum()
        wma_values.append(wma_value)
    
    # 인덱스 맞추기
    wma_series = pd.Series(index=prices.index[window-1:], data=wma_values)
    return wma_series

def volume_weighted_average_price(prices: pd.Series, volumes: pd.Series, window: int) -> pd.Series:
    """거래량 가중 평균가격 (VWAP)"""
    if len(prices) != len(volumes) or len(prices) < window:
        return pd.Series(dtype=float)
    
    typical_price = prices
    pv = typical_price * volumes
    
    vwap = pv.rolling(window=window).sum() / volumes.rolling(window=window).sum()
    return vwap

# RSI 관련 함수들
def rsi(prices: pd.Series, window: int = 14) -> pd.Series:
    """상대강도지수 (RSI)"""
    if len(prices) < window + 1:
        return pd.Series(dtype=float)
    
    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    
    rs = avg_gain / avg_loss
    rsi_values = 100 - (100 / (1 + rs))
    
    return rsi_values

def stochastic_rsi(prices: pd.Series, window: int = 14, k_period: int = 3, d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
    """스토캐스틱 RSI"""
    rsi_values = rsi(prices, window)
    
    if len(rsi_values) < window:
        return pd.Series(dtype=float), pd.Series(dtype=float)
    
    rsi_low = rsi_values.rolling(window=window).min()
    rsi_high = rsi_values.rolling(window=window).max()
    
    stoch_rsi = (rsi_values - rsi_low) / (rsi_high - rsi_low) * 100
    k_percent = stoch_rsi.rolling(window=k_period).mean()
    d_percent = k_percent.rolling(window=d_period).mean()
    
    return k_percent, d_percent

# MACD 관련 함수들
def macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """MACD (Moving Average Convergence Divergence)"""
    if len(prices) < slow:
        return pd.Series(dtype=float), pd.Series(dtype=float), pd.Series(dtype=float)
    
    ema_fast = exponential_moving_average(prices, fast)
    ema_slow = exponential_moving_average(prices, slow)
    
    macd_line = ema_fast - ema_slow
    signal_line = exponential_moving_average(macd_line, signal)
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram

def ppo(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series]:
    """Percentage Price Oscillator"""
    if len(prices) < slow:
        return pd.Series(dtype=float), pd.Series(dtype=float)
    
    ema_fast = exponential_moving_average(prices, fast)
    ema_slow = exponential_moving_average(prices, slow)
    
    ppo_line = ((ema_fast - ema_slow) / ema_slow) * 100
    signal_line = exponential_moving_average(ppo_line, signal)
    
    return ppo_line, signal_line

# 볼린저 밴드
def bollinger_bands(prices: pd.Series, window: int = 20, num_std: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """볼린저 밴드"""
    if len(prices) < window:
        return pd.Series(dtype=float), pd.Series(dtype=float), pd.Series(dtype=float)
    
    sma = simple_moving_average(prices, window)
    std = prices.rolling(window=window).std()
    
    upper_band = sma + (std * num_std)
    lower_band = sma - (std * num_std)
    
    return upper_band, sma, lower_band

def bollinger_bands_percent_b(prices: pd.Series, window: int = 20, num_std: float = 2) -> pd.Series:
    """볼린저 밴드 %B"""
    upper, middle, lower = bollinger_bands(prices, window, num_std)
    
    if len(upper) == 0:
        return pd.Series(dtype=float)
    
    percent_b = (prices - lower) / (upper - lower)
    return percent_b

def bollinger_bands_width(prices: pd.Series, window: int = 20, num_std: float = 2) -> pd.Series:
    """볼린저 밴드 폭"""
    upper, middle, lower = bollinger_bands(prices, window, num_std)
    
    if len(upper) == 0:
        return pd.Series(dtype=float)
    
    band_width = (upper - lower) / middle
    return band_width

# 스토캐스틱
def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, 
               k_period: int = 14, k_smooth: int = 3, d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
    """스토캐스틱 오실레이터"""
    if len(high) < k_period:
        return pd.Series(dtype=float), pd.Series(dtype=float)
    
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    
    k_percent_raw = (close - lowest_low) / (highest_high - lowest_low) * 100
    k_percent = k_percent_raw.rolling(window=k_smooth).mean()
    d_percent = k_percent.rolling(window=d_period).mean()
    
    return k_percent, d_percent

# 윌리엄스 %R
def williams_r(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
    """윌리엄스 %R"""
    if len(high) < window:
        return pd.Series(dtype=float)
    
    highest_high = high.rolling(window=window).max()
    lowest_low = low.rolling(window=window).min()
    
    williams_r_values = (highest_high - close) / (highest_high - lowest_low) * -100
    return williams_r_values

# CCI (Commodity Channel Index)
def cci(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 20) -> pd.Series:
    """Commodity Channel Index"""
    if len(high) < window:
        return pd.Series(dtype=float)
    
    typical_price = (high + low + close) / 3
    sma_tp = typical_price.rolling(window=window).mean()
    
    # Mean Absolute Deviation 계산
    mad = typical_price.rolling(window=window).apply(lambda x: np.mean(np.abs(x - x.mean())))
    
    cci_values = (typical_price - sma_tp) / (0.015 * mad)
    return cci_values

# ATR (Average True Range)
def average_true_range(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
    """평균 실제 범위 (ATR)"""
    if len(high) < 2:
        return pd.Series(dtype=float)
    
    # True Range 계산
    tr1 = high - low
    tr2 = np.abs(high - close.shift(1))
    tr3 = np.abs(low - close.shift(1))
    
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = true_range.rolling(window=window).mean()
    
    return atr

# ADX (Average Directional Index)
def adx(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Average Directional Index"""
    if len(high) < window + 1:
        return pd.Series(dtype=float), pd.Series(dtype=float), pd.Series(dtype=float)
    
    # Calculate True Range and Directional Movement
    tr = average_true_range(high, low, close, 1)
    
    high_diff = high.diff()
    low_diff = low.diff()
    
    plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)
    minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)
    
    plus_dm = pd.Series(plus_dm, index=high.index)
    minus_dm = pd.Series(minus_dm, index=low.index)
    
    # Smooth the values
    plus_di = 100 * (plus_dm.rolling(window=window).mean() / tr.rolling(window=window).mean())
    minus_di = 100 * (minus_dm.rolling(window=window).mean() / tr.rolling(window=window).mean())
    
    # Calculate ADX
    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
    adx_values = dx.rolling(window=window).mean()
    
    return adx_values, plus_di, minus_di

# 거래량 지표들
def on_balance_volume(close: pd.Series, volume: pd.Series) -> pd.Series:
    """On-Balance Volume"""
    if len(close) != len(volume) or len(close) < 2:
        return pd.Series(dtype=float)
    
    price_change = close.diff()
    obv = np.where(price_change > 0, volume, 
                   np.where(price_change < 0, -volume, 0)).cumsum()
    
    return pd.Series(obv, index=close.index)

def accumulation_distribution_line(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    """Accumulation/Distribution Line"""
    if len(high) != len(volume):
        return pd.Series(dtype=float)
    
    clv = ((close - low) - (high - close)) / (high - low)
    clv = clv.fillna(0)  # high == low인 경우 처리
    
    money_flow_volume = clv * volume
    ad_line = money_flow_volume.cumsum()
    
    return ad_line

def money_flow_index(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, window: int = 14) -> pd.Series:
    """Money Flow Index"""
    if len(high) != len(volume) or len(high) < window + 1:
        return pd.Series(dtype=float)
    
    typical_price = (high + low + close) / 3
    money_flow = typical_price * volume
    
    price_change = typical_price.diff()
    
    positive_flow = np.where(price_change > 0, money_flow, 0)
    negative_flow = np.where(price_change < 0, money_flow, 0)
    
    positive_flow_sum = pd.Series(positive_flow, index=high.index).rolling(window=window).sum()
    negative_flow_sum = pd.Series(negative_flow, index=high.index).rolling(window=window).sum()
    
    money_ratio = positive_flow_sum / negative_flow_sum
    mfi = 100 - (100 / (1 + money_ratio))
    
    return mfi

# 모멘텀 지표들
def momentum(prices: pd.Series, window: int = 10) -> pd.Series:
    """모멘텀 지표"""
    if len(prices) < window:
        return pd.Series(dtype=float)
    
    return prices - prices.shift(window)

def rate_of_change(prices: pd.Series, window: int = 10) -> pd.Series:
    """변화율 (ROC)"""
    if len(prices) < window:
        return pd.Series(dtype=float)
    
    return ((prices - prices.shift(window)) / prices.shift(window)) * 100

def relative_strength(prices: pd.Series, benchmark: pd.Series, window: int = 252) -> pd.Series:
    """상대강도 (vs 벤치마크)"""
    if len(prices) != len(benchmark) or len(prices) < window:
        return pd.Series(dtype=float)
    
    stock_return = prices.pct_change(window)
    benchmark_return = benchmark.pct_change(window)
    
    relative_strength_values = (1 + stock_return) / (1 + benchmark_return) - 1
    return relative_strength_values * 100

# 변동성 지표들
def standard_deviation(prices: pd.Series, window: int = 20) -> pd.Series:
    """표준편차"""
    if len(prices) < window:
        return pd.Series(dtype=float)
    
    return prices.rolling(window=window).std()

def historical_volatility(prices: pd.Series, window: int = 30) -> pd.Series:
    """역사적 변동성 (연율화)"""
    if len(prices) < window:
        return pd.Series(dtype=float)
    
    returns = prices.pct_change()
    volatility = returns.rolling(window=window).std() * np.sqrt(252)
    return volatility * 100

# 추세 지표들
def parabolic_sar(high: pd.Series, low: pd.Series, af_start: float = 0.02, af_increment: float = 0.02, af_max: float = 0.2) -> pd.Series:
    """Parabolic SAR"""
    if len(high) < 2:
        return pd.Series(dtype=float)
    
    sar = np.zeros(len(high))
    trend = np.zeros(len(high))  # 1 for uptrend, -1 for downtrend
    af = np.zeros(len(high))
    ep = np.zeros(len(high))  # Extreme Point
    
    # 초기값 설정
    sar[0] = low.iloc[0]
    trend[0] = 1
    af[0] = af_start
    ep[0] = high.iloc[0]
    
    for i in range(1, len(high)):
        if trend[i-1] == 1:  # Uptrend
            sar[i] = sar[i-1] + af[i-1] * (ep[i-1] - sar[i-1])
            
            if low.iloc[i] <= sar[i]:  # Trend reversal
                trend[i] = -1
                sar[i] = ep[i-1]
                af[i] = af_start
                ep[i] = low.iloc[i]
            else:
                trend[i] = 1
                if high.iloc[i] > ep[i-1]:
                    ep[i] = high.iloc[i]
                    af[i] = min(af_max, af[i-1] + af_increment)
                else:
                    ep[i] = ep[i-1]
                    af[i] = af[i-1]
        else:  # Downtrend
            sar[i] = sar[i-1] + af[i-1] * (ep[i-1] - sar[i-1])
            
            if high.iloc[i] >= sar[i]:  # Trend reversal
                trend[i] = 1
                sar[i] = ep[i-1]
                af[i] = af_start
                ep[i] = high.iloc[i]
            else:
                trend[i] = -1
                if low.iloc[i] < ep[i-1]:
                    ep[i] = low.iloc[i]
                    af[i] = min(af_max, af[i-1] + af_increment)
                else:
                    ep[i] = ep[i-1]
                    af[i] = af[i-1]
    
    return pd.Series(sar, index=high.index)

# 유틸리티 함수들
def crossover(series1: pd.Series, series2: pd.Series) -> pd.Series:
    """상향 교차 확인"""
    return (series1 > series2) & (series1.shift(1) <= series2.shift(1))

def crossunder(series1: pd.Series, series2: pd.Series) -> pd.Series:
    """하향 교차 확인"""
    return (series1 < series2) & (series1.shift(1) >= series2.shift(1))

def highest(series: pd.Series, window: int) -> pd.Series:
    """지정 기간 내 최고값"""
    return series.rolling(window=window).max()

def lowest(series: pd.Series, window: int) -> pd.Series:
    """지정 기간 내 최저값"""
    return series.rolling(window=window).min()

def normalize_indicator(indicator: pd.Series, window: int = 252) -> pd.Series:
    """지표 정규화 (0-1 범위)"""
    if len(indicator) < window:
        return pd.Series(dtype=float)
    
    rolling_min = indicator.rolling(window=window).min()
    rolling_max = indicator.rolling(window=window).max()
    
    normalized = (indicator - rolling_min) / (rolling_max - rolling_min)
    return normalized

