"""
file: quant_mvp/data/indicators.py
기술적 지표 및 재무 지표 계산
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class TechnicalIndicators:
    """기술적 지표 계산 클래스"""
    
    @staticmethod
    def calculate_sma(prices: pd.Series, period: int) -> pd.Series:
        """단순 이동평균"""
        return prices.rolling(window=period).mean()
    
    @staticmethod
    def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
        """지수 이동평균"""
        return prices.ewm(span=period).mean()
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """RSI (Relative Strength Index)"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_bollinger_bands(prices: pd.Series, period: int = 20, 
                                 std_dev: float = 2) -> Dict[str, pd.Series]:
        """볼린저 밴드"""
        sma = TechnicalIndicators.calculate_sma(prices, period)
        std = prices.rolling(window=period).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return {
            'upper': upper_band,
            'middle': sma,
            'lower': lower_band,
            'bandwidth': (upper_band - lower_band) / sma
        }
    
    @staticmethod
    def calculate_macd(prices: pd.Series, fast_period: int = 12, 
                      slow_period: int = 26, signal_period: int = 9) -> Dict[str, pd.Series]:
        """MACD (Moving Average Convergence Divergence)"""
        ema_fast = TechnicalIndicators.calculate_ema(prices, fast_period)
        ema_slow = TechnicalIndicators.calculate_ema(prices, slow_period)
        
        macd_line = ema_fast - ema_slow
        signal_line = TechnicalIndicators.calculate_ema(macd_line, signal_period)
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series,
                           k_period: int = 14, d_period: int = 3) -> Dict[str, pd.Series]:
        """스토캐스틱 오실레이터"""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        
        k_percent = 100 * (close - lowest_low) / (highest_high - lowest_low)
        d_percent = k_percent.rolling(window=d_period).mean()
        
        return {
            'k_percent': k_percent,
            'd_percent': d_percent
        }
    
    @staticmethod
    def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series,
                     period: int = 14) -> pd.Series:
        """ATR (Average True Range)"""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        return atr
    
    @staticmethod
    def calculate_williams_r(high: pd.Series, low: pd.Series, close: pd.Series,
                           period: int = 14) -> pd.Series:
        """Williams %R"""
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()
        
        williams_r = -100 * (highest_high - close) / (highest_high - lowest_low)
        return williams_r
    
    @staticmethod
    def calculate_cci(high: pd.Series, low: pd.Series, close: pd.Series,
                     period: int = 20, constant: float = 0.015) -> pd.Series:
        """CCI (Commodity Channel Index)"""
        typical_price = (high + low + close) / 3
        sma_tp = typical_price.rolling(window=period).mean()
        mean_deviation = typical_price.rolling(window=period).apply(
            lambda x: np.mean(np.abs(x - x.mean()))
        )
        
        cci = (typical_price - sma_tp) / (constant * mean_deviation)
        return cci
    
    @staticmethod
    def calculate_momentum(prices: pd.Series, period: int = 10) -> pd.Series:
        """모멘텀"""
        return prices / prices.shift(period) - 1
    
    @staticmethod
    def calculate_roc(prices: pd.Series, period: int = 12) -> pd.Series:
        """ROC (Rate of Change)"""
        return ((prices - prices.shift(period)) / prices.shift(period)) * 100

class FundamentalIndicators:
    """재무 지표 계산 클래스"""
    
    @staticmethod
    def calculate_pe_ratio(price: float, eps: float) -> float:
        """PER (Price to Earnings Ratio)"""
        if eps <= 0:
            return float('inf')
        return price / eps
    
    @staticmethod
    def calculate_pb_ratio(price: float, book_value_per_share: float) -> float:
        """PBR (Price to Book Ratio)"""
        if book_value_per_share <= 0:
            return float('inf')
        return price / book_value_per_share
    
    @staticmethod
    def calculate_peg_ratio(pe_ratio: float, earnings_growth_rate: float) -> float:
        """PEG (Price/Earnings to Growth) Ratio"""
        if earnings_growth_rate <= 0:
            return float('inf')
        return pe_ratio / earnings_growth_rate
    
    @staticmethod
    def calculate_roe(net_income: float, shareholders_equity: float) -> float:
        """ROE (Return on Equity)"""
        if shareholders_equity <= 0:
            return 0
    
    def calculate_trend_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """추세 지표 계산"""
        try:
            result_df = data.copy()
            
            for symbol in data['symbol'].unique():
                mask = data['symbol'] == symbol
                symbol_data = data[mask].sort_values('date')
                
                if len(symbol_data) < 50:
                    continue
                
                close_prices = symbol_data['close']
                
                # 추세 강도 계산 (ADX 근사)
                result_df.loc[mask, 'trend_strength'] = self._calculate_trend_strength(close_prices)
                
                # 지지/저항 수준 계산
                support_resistance = self._calculate_support_resistance(close_prices)
                result_df.loc[mask, 'support_level'] = support_resistance['support']
                result_df.loc[mask, 'resistance_level'] = support_resistance['resistance']
                
                # 가격 위치 (지지선 대비 저항선 사이 위치)
                result_df.loc[mask, 'price_position'] = self._calculate_price_position(
                    close_prices, support_resistance
                )
            
            return result_df
            
        except Exception as e:
            logger.error(f"Error calculating trend indicators: {e}")
            return data
    
    def _calculate_trend_strength(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """추세 강도 계산 (0-100)"""
        try:
            # 방향성 움직임 계산
            price_diff = prices.diff()
            
            up_moves = price_diff.where(price_diff > 0, 0)
            down_moves = abs(price_diff.where(price_diff < 0, 0))
            
            # 평균 방향성 지수 근사
            avg_up = up_moves.rolling(window=period).mean()
            avg_down = down_moves.rolling(window=period).mean()
            
            # 추세 강도 (0-100)
            trend_strength = 100 * abs(avg_up - avg_down) / (avg_up + avg_down)
            trend_strength = trend_strength.fillna(0)
            
            return trend_strength
            
        except Exception as e:
            logger.error(f"Error calculating trend strength: {e}")
            return pd.Series(0, index=prices.index)
    
    def _calculate_support_resistance(self, prices: pd.Series, 
                                    window: int = 20) -> Dict[str, pd.Series]:
        """지지/저항선 계산"""
        try:
            # 롤링 윈도우에서 최고/최저가
            rolling_high = prices.rolling(window=window).max()
            rolling_low = prices.rolling(window=window).min()
            
            # 지지선: 최근 저점들의 평균
            support = rolling_low.rolling(window=5).mean()
            
            # 저항선: 최근 고점들의 평균  
            resistance = rolling_high.rolling(window=5).mean()
            
            return {
                'support': support,
                'resistance': resistance
            }
            
        except Exception as e:
            logger.error(f"Error calculating support/resistance: {e}")
            return {
                'support': pd.Series(0, index=prices.index),
                'resistance': pd.Series(0, index=prices.index)
            }
    
    def _calculate_price_position(self, prices: pd.Series, 
                                support_resistance: Dict[str, pd.Series]) -> pd.Series:
        """현재 가격의 지지/저항 사이 위치 (0-100)"""
        try:
            support = support_resistance['support']
            resistance = support_resistance['resistance']
            
            # 지지선과 저항선 사이에서의 위치
            position = (prices - support) / (resistance - support) * 100
            position = position.clip(0, 100)  # 0-100 범위로 제한
            
            return position.fillna(50)  # 결측값은 중간값으로
            
        except Exception as e:
            logger.error(f"Error calculating price position: {e}")
            return pd.Series(50, index=prices.index)
    
    def calculate_volatility_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """변동성 지표 계산"""
        try:
            result_df = data.copy()
            
            for symbol in data['symbol'].unique():
                mask = data['symbol'] == symbol
                symbol_data = data[mask].sort_values('date')
                
                if len(symbol_data) < 30:
                    continue
                
                close_prices = symbol_data['close']
                high_prices = symbol_data['high']
                low_prices = symbol_data['low']
                
                # 역사적 변동성 (20일)
                returns = close_prices.pct_change()
                result_df.loc[mask, 'historical_volatility'] = returns.rolling(window=20).std() * np.sqrt(252) * 100
                
                # 평균 실체 범위 (ATR)
                result_df.loc[mask, 'atr_20'] = self.technical.calculate_atr(
                    high_prices, low_prices, close_prices, 20
                )
                
                # 변동성 비율 (현재 vs 과거)
                current_vol = returns.rolling(window=10).std()
                past_vol = returns.rolling(window=30).std()
                result_df.loc[mask, 'volatility_ratio'] = (current_vol / past_vol).fillna(1.0)
            
            return result_df
            
        except Exception as e:
            logger.error(f"Error calculating volatility indicators: {e}")
            return data
    
    def get_indicator_summary(self, data: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """특정 종목의 지표 요약"""
        try:
            symbol_data = data[data['symbol'] == symbol].sort_values('date')
            
            if symbol_data.empty:
                return {}
            
            latest = symbol_data.iloc[-1]
            
            summary = {
                'symbol': symbol,
                'date': latest.get('date'),
                'price': latest.get('close', 0),
                
                # 기술적 지표
                'rsi': latest.get('rsi_14', 0),
                'macd_signal': 'buy' if latest.get('macd', 0) > latest.get('macd_signal', 0) else 'sell',
                'bb_position': self._get_bb_position(latest),
                'trend_strength': latest.get('trend_strength', 0),
                
                # 재무 지표
                'pe_ratio': latest.get('pe_ratio', 0),
                'pb_ratio': latest.get('pb_ratio', 0),
                'roe': latest.get('roe', 0),
                'debt_ratio': latest.get('debt_to_equity', 0),
                
                # 복합 점수
                'financial_health': latest.get('financial_health_score', 0),
                'value_score': latest.get('value_score', 0),
                'growth_score': latest.get('growth_score', 0),
                'dividend_score': latest.get('dividend_score', 0)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting indicator summary for {symbol}: {e}")
            return {}
    
    def _get_bb_position(self, row: pd.Series) -> str:
        """볼린저밴드 위치 판단"""
        try:
            price = row.get('close', 0)
            bb_upper = row.get('bb_upper', 0)
            bb_lower = row.get('bb_lower', 0)
            bb_middle = row.get('bb_middle', 0)
            
            if price > bb_upper:
                return 'overbought'
            elif price < bb_lower:
                return 'oversold'
            elif price > bb_middle:
                return 'above_middle'
            else:
                return 'below_middle'
                
        except Exception as e:
            logger.error(f"Error getting BB position: {e}")
            return 'unknown'
    
    def calculate_composite_scores(self, data: pd.DataFrame) -> pd.DataFrame:
        """복합 점수 계산"""
        try:
            result_df = data.copy()
            
            for symbol in data['symbol'].unique():
                mask = data['symbol'] == symbol
                symbol_data = data[mask].sort_values('date')
                
                if len(symbol_data) < 10:
                    continue
                
                # 전체 투자 매력도 점수 (기술적 + 재무적)
                tech_score = symbol_data.get('trend_strength', 0) / 100  # 0-1 스케일로 변환
                fundamental_score = (
                    symbol_data.get('financial_health_score', 0) + 
                    symbol_data.get('value_score', 0) + 
                    symbol_data.get('growth_score', 0)
                ) / 300  # 0-1 스케일로 변환
                
                # 가중 평균 (기술적 30%, 재무적 70%)
                composite_score = tech_score * 0.3 + fundamental_score * 0.7
                result_df.loc[mask, 'composite_investment_score'] = composite_score * 100
                
                # 위험 점수 계산
                volatility_score = symbol_data.get('historical_volatility', 20) / 50  # 0-1 스케일
                debt_score = np.clip(symbol_data.get('debt_to_equity', 1.0) / 2.0, 0, 1)  # 0-1 스케일
                
                risk_score = (volatility_score + debt_score) / 2 * 100
                result_df.loc[mask, 'risk_score'] = risk_score
                
                # 위험 조정 점수
                risk_adjusted_score = composite_score * 100 * (1 - risk_score / 200)  # 위험만큼 점수 차감
                result_df.loc[mask, 'risk_adjusted_score'] = np.clip(risk_adjusted_score, 0, 100)
            
            return result_df
            
        except Exception as e:
            logger.error(f"Error calculating composite scores: {e}")
            return data
    
    def get_top_stocks_by_criteria(self, data: pd.DataFrame, 
                                 criteria: str = 'composite_investment_score',
                                 top_n: int = 10) -> pd.DataFrame:
        """기준별 상위 종목 조회"""
        try:
            # 최신 데이터만 사용
            latest_data = data.groupby('symbol').last().reset_index()
            
            if criteria not in latest_data.columns:
                logger.error(f"Criteria '{criteria}' not found in data")
                return pd.DataFrame()
            
            # 기준으로 정렬하고 상위 N개 선택
            top_stocks = latest_data.nlargest(top_n, criteria)
            
            return top_stocks[['symbol', 'close', criteria, 'sector']].round(2)
            
        except Exception as e:
            logger.error(f"Error getting top stocks: {e}")
            return pd.DataFrame()
    
    def generate_market_summary(self, data: pd.DataFrame) -> Dict[str, Any]:
        """시장 전체 요약"""
        try:
            if data.empty:
                return {}
            
            # 최신 데이터
            latest_data = data.groupby('symbol').last().reset_index()
            
            summary = {
                'total_stocks': len(latest_data),
                'sectors': latest_data['sector'].nunique() if 'sector' in latest_data.columns else 0,
                'avg_pe_ratio': latest_data['pe_ratio'].mean() if 'pe_ratio' in latest_data.columns else 0,
                'avg_pb_ratio': latest_data['pb_ratio'].mean() if 'pb_ratio' in latest_data.columns else 0,
                'avg_roe': latest_data['roe'].mean() if 'roe' in latest_data.columns else 0,
                'avg_debt_ratio': latest_data['debt_to_equity'].mean() if 'debt_to_equity' in latest_data.columns else 0
            }
            
            # 섹터별 통계
            if 'sector' in latest_data.columns:
                sector_stats = latest_data.groupby('sector').agg({
                    'close': 'mean',
                    'pe_ratio': 'mean',
                    'roe': 'mean'
                }).round(2)
                summary['sector_stats'] = sector_stats.to_dict('index')
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating market summary: {e}")
            return {}
        return (net_income / shareholders_equity) * 100
    
    @staticmethod
    def calculate_roa(net_income: float, total_assets: float) -> float:
        """ROA (Return on Assets)"""
        if total_assets <= 0:
            return 0
        return (net_income / total_assets) * 100
    
    @staticmethod
    def calculate_debt_to_equity(total_debt: float, shareholders_equity: float) -> float:
        """부채비율 (Debt to Equity Ratio)"""
        if shareholders_equity <= 0:
            return float('inf')
        return total_debt / shareholders_equity
    
    @staticmethod
    def calculate_current_ratio(current_assets: float, current_liabilities: float) -> float:
        """유동비율 (Current Ratio)"""
        if current_liabilities <= 0:
            return float('inf')
        return current_assets / current_liabilities
    
    @staticmethod
    def calculate_quick_ratio(current_assets: float, inventory: float, 
                            current_liabilities: float) -> float:
        """당좌비율 (Quick Ratio)"""
        if current_liabilities <= 0:
            return float('inf')
        return (current_assets - inventory) / current_liabilities
    
    @staticmethod
    def calculate_gross_margin(gross_profit: float, revenue: float) -> float:
        """매출총이익률 (Gross Margin)"""
        if revenue <= 0:
            return 0
        return (gross_profit / revenue) * 100
    
    @staticmethod
    def calculate_operating_margin(operating_profit: float, revenue: float) -> float:
        """영업이익률 (Operating Margin)"""
        if revenue <= 0:
            return 0
        return (operating_profit / revenue) * 100
    
    @staticmethod
    def calculate_net_margin(net_income: float, revenue: float) -> float:
        """순이익률 (Net Margin)"""
        if revenue <= 0:
            return 0
        return (net_income / revenue) * 100
    
    @staticmethod
    def calculate_dividend_yield(dividend_per_share: float, price_per_share: float) -> float:
        """배당수익률 (Dividend Yield)"""
        if price_per_share <= 0:
            return 0
        return (dividend_per_share / price_per_share) * 100
    
    @staticmethod
    def calculate_payout_ratio(dividend_per_share: float, earnings_per_share: float) -> float:
        """배당성향 (Payout Ratio)"""
        if earnings_per_share <= 0:
            return 0
        return dividend_per_share / earnings_per_share
    
    @staticmethod
    def calculate_asset_turnover(revenue: float, total_assets: float) -> float:
        """자산회전율 (Asset Turnover)"""
        if total_assets <= 0:
            return 0
        return revenue / total_assets
    
    @staticmethod
    def calculate_inventory_turnover(cogs: float, avg_inventory: float) -> float:
        """재고회전율 (Inventory Turnover)"""
        if avg_inventory <= 0:
            return 0
        return cogs / avg_inventory

class IndicatorCalculator:
    """통합 지표 계산기"""
    
    def __init__(self):
        self.technical = TechnicalIndicators()
        self.fundamental = FundamentalIndicators()
    
    def calculate_all_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """모든 기술적 지표 계산"""
        try:
            result_df = data.copy()
            
            # 가격 데이터 존재 여부 확인
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            missing_cols = [col for col in required_cols if col not in data.columns]
            
            if missing_cols:
                logger.warning(f"Missing columns for technical indicators: {missing_cols}")
                return result_df
            
            # 종목별로 지표 계산
            for symbol in data['symbol'].unique():
                mask = data['symbol'] == symbol
                symbol_data = data[mask].sort_values('date')
                
                if len(symbol_data) < 30:  # 최소 30일 데이터 필요
                    continue
                
                # 기본 이동평균
                result_df.loc[mask, 'sma_20'] = self.technical.calculate_sma(symbol_data['close'], 20)
                result_df.loc[mask, 'sma_50'] = self.technical.calculate_sma(symbol_data['close'], 50)
                result_df.loc[mask, 'ema_12'] = self.technical.calculate_ema(symbol_data['close'], 12)
                result_df.loc[mask, 'ema_26'] = self.technical.calculate_ema(symbol_data['close'], 26)
                
                # RSI
                result_df.loc[mask, 'rsi_14'] = self.technical.calculate_rsi(symbol_data['close'], 14)
                
                # 볼린저 밴드
                bb = self.technical.calculate_bollinger_bands(symbol_data['close'])
                result_df.loc[mask, 'bb_upper'] = bb['upper']
                result_df.loc[mask, 'bb_middle'] = bb['middle']
                result_df.loc[mask, 'bb_lower'] = bb['lower']
                result_df.loc[mask, 'bb_bandwidth'] = bb['bandwidth']
                
                # MACD
                macd = self.technical.calculate_macd(symbol_data['close'])
                result_df.loc[mask, 'macd'] = macd['macd']
                result_df.loc[mask, 'macd_signal'] = macd['signal']
                result_df.loc[mask, 'macd_histogram'] = macd['histogram']
                
                # ATR
                result_df.loc[mask, 'atr_14'] = self.technical.calculate_atr(
                    symbol_data['high'], symbol_data['low'], symbol_data['close'], 14
                )
                
                # 모멘텀
                result_df.loc[mask, 'momentum_10'] = self.technical.calculate_momentum(symbol_data['close'], 10)
                result_df.loc[mask, 'roc_12'] = self.technical.calculate_roc(symbol_data['close'], 12)
            
            logger.info("Technical indicators calculated successfully")
            return result_df
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return data
    
    def enhance_fundamental_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """재무 데이터에 추가 지표 계산"""
        try:
            result_df = data.copy()
            
            # 재무 지표 계산을 위한 컬럼 확인
            fundamental_cols = ['pe_ratio', 'pb_ratio', 'roe', 'roa', 'debt_to_equity']
            available_cols = [col for col in fundamental_cols if col in data.columns]
            
            if not available_cols:
                logger.warning("No fundamental data columns found")
                return result_df
            
            # 종목별로 추가 지표 계산
            for symbol in data['symbol'].unique():
                mask = data['symbol'] == symbol
                symbol_data = data[mask]
                
                # PEG 비율 계산 (PE와 성장률이 있을 경우)
                if all(col in symbol_data.columns for col in ['pe_ratio', 'earnings_growth']):
                    result_df.loc[mask, 'peg_ratio'] = symbol_data.apply(
                        lambda row: self.fundamental.calculate_peg_ratio(
                            row['pe_ratio'], row['earnings_growth']
                        ), axis=1
                    )
                
                # PEG 비율 계산 (PE와 성장률이 있을 경우)
                if all(col in symbol_data.columns for col in ['pe_ratio', 'earnings_growth']):
                    result_df.loc[mask, 'peg_ratio'] = symbol_data.apply(
                        lambda row: self.fundamental.calculate_peg_ratio(
                            row['pe_ratio'], row['earnings_growth']
                        ), axis=1
                    )
                
                # 재무 건전성 점수 계산
                if all(col in symbol_data.columns for col in ['roe', 'debt_to_equity']):
                    # 유동비율이 없는 경우 기본값 사용
                    if 'current_ratio' not in symbol_data.columns:
                        symbol_data_with_ratio = symbol_data.copy()
                        symbol_data_with_ratio['current_ratio'] = 1.5  # 기본값
                    else:
                        symbol_data_with_ratio = symbol_data
                    
                    result_df.loc[mask, 'financial_health_score'] = symbol_data_with_ratio.apply(
                        lambda row: self._calculate_financial_health_score(row), axis=1
                    )
                
                # 가치 점수 계산
                if all(col in symbol_data.columns for col in ['pe_ratio', 'pb_ratio']):
                    result_df.loc[mask, 'value_score'] = symbol_data.apply(
                        lambda row: self._calculate_value_score(row), axis=1
                    )
                
                # 성장 점수 계산
                if all(col in symbol_data.columns for col in ['revenue_growth', 'earnings_growth']):
                    result_df.loc[mask, 'growth_score'] = symbol_data.apply(
                        lambda row: self._calculate_growth_score(row), axis=1
                    )
                
                # 배당 점수 계산
                if 'dividend_yield' in symbol_data.columns:
                    result_df.loc[mask, 'dividend_score'] = symbol_data.apply(
                        lambda row: self._calculate_dividend_score(row), axis=1
                    )
            
            logger.info("Fundamental indicators enhanced successfully")
            return result_df
            
        except Exception as e:
            logger.error(f"Error enhancing fundamental data: {e}")
            return data
    
    def _calculate_financial_health_score(self, row: pd.Series) -> float:
        """재무 건전성 점수 계산 (0-100)"""
        try:
            score = 0
            max_score = 100
            
            # ROE 점수 (30점)
            roe = row.get('roe', 0)
            if roe > 20:
                score += 30
            elif roe > 15:
                score += 25
            elif roe > 10:
                score += 20
            elif roe > 5:
                score += 10
            
            # 부채비율 점수 (30점)
            debt_ratio = row.get('debt_to_equity', float('inf'))
            if debt_ratio < 0.3:
                score += 30
            elif debt_ratio < 0.5:
                score += 25
            elif debt_ratio < 1.0:
                score += 15
            elif debt_ratio < 2.0:
                score += 5
            
            # 유동비율 점수 (20점)
            current_ratio = row.get('current_ratio', 1.5)
            if current_ratio > 2.0:
                score += 20
            elif current_ratio > 1.5:
                score += 15
            elif current_ratio > 1.0:
                score += 10
            elif current_ratio > 0.8:
                score += 5
            
            # ROA 점수 (20점)
            roa = row.get('roa', 0)
            if roa > 10:
                score += 20
            elif roa > 7:
                score += 15
            elif roa > 5:
                score += 10
            elif roa > 3:
                score += 5
            
            return min(score, max_score)
            
        except Exception as e:
            logger.error(f"Error calculating financial health score: {e}")
            return 0
    
    def _calculate_value_score(self, row: pd.Series) -> float:
        """가치 점수 계산 (0-100)"""
        try:
            score = 0
            
            # PER 점수 (50점)
            pe_ratio = row.get('pe_ratio', float('inf'))
            if pe_ratio < 10:
                score += 50
            elif pe_ratio < 15:
                score += 40
            elif pe_ratio < 20:
                score += 30
            elif pe_ratio < 25:
                score += 20
            elif pe_ratio < 30:
                score += 10
            
            # PBR 점수 (50점)
            pb_ratio = row.get('pb_ratio', float('inf'))
            if pb_ratio < 1.0:
                score += 50
            elif pb_ratio < 1.5:
                score += 40
            elif pb_ratio < 2.0:
                score += 30
            elif pb_ratio < 2.5:
                score += 20
            elif pb_ratio < 3.0:
                score += 10
            
            return score
            
        except Exception as e:
            logger.error(f"Error calculating value score: {e}")
            return 0
    
    def _calculate_growth_score(self, row: pd.Series) -> float:
        """성장 점수 계산 (0-100)"""
        try:
            score = 0
            
            # 매출 성장률 점수 (40점)
            revenue_growth = row.get('revenue_growth', 0)
            if revenue_growth > 25:
                score += 40
            elif revenue_growth > 20:
                score += 35
            elif revenue_growth > 15:
                score += 30
            elif revenue_growth > 10:
                score += 25
            elif revenue_growth > 5:
                score += 15
            elif revenue_growth > 0:
                score += 5
            
            # 이익 성장률 점수 (60점)
            earnings_growth = row.get('earnings_growth', 0)
            if earnings_growth > 30:
                score += 60
            elif earnings_growth > 25:
                score += 50
            elif earnings_growth > 20:
                score += 40
            elif earnings_growth > 15:
                score += 30
            elif earnings_growth > 10:
                score += 20
            elif earnings_growth > 5:
                score += 10
            elif earnings_growth > 0:
                score += 5
            
            return score
            
        except Exception as e:
            logger.error(f"Error calculating growth score: {e}")
            return 0
    
    def _calculate_dividend_score(self, row: pd.Series) -> float:
        """배당 점수 계산 (0-100)"""
        try:
            score = 0
            
            # 배당수익률 점수
            dividend_yield = row.get('dividend_yield', 0)
            if dividend_yield >= 4.0:
                score += 100
            elif dividend_yield >= 3.0:
                score += 80
            elif dividend_yield >= 2.0:
                score += 60
            elif dividend_yield >= 1.0:
                score += 40
            elif dividend_yield > 0:
                score += 20
            
            # 배당성향이 있다면 추가 고려
            payout_ratio = row.get('payout_ratio', None)
            if payout_ratio is not None:
                if 0.3 <= payout_ratio <= 0.7:  # 적절한 배당성향
                    score *= 1.2  # 20% 보너스
                elif payout_ratio > 0.9:  # 너무 높은 배당성향
                    score *= 0.8  # 20% 감점
            
            return min(score, 100)
            
        except Exception as e:
            logger.error(f"Error calculating dividend score: {e}")
            return 
                if all(col in symbol_data.columns for col in ['roe', 'debt_to_equity', 'current_ratio']):
                    result_df.loc[mask, 'financial_health_score'] = symbol_data.apply(
                        lambda row: self._calculate_financial_health_score(row), axis=1
                    )
                
                # 가치 점수 계산
                if all(col in symbol_data.columns for col in ['pe_ratio', 'pb_ratio']):
                    result_df.loc[mask, 'value_score'] = symbol_data.apply(
                        lambda row: self._calculate_value_score(row), axis=1
                    )
            
            logger.info("Fundamental indicators enhanced successfully")
            return result_df
            
        except Exception as e:
            logger.error(f"Error enhancing fundamental data: {e}")
            return data
    
    def _calculate_financial_health_score(self, row: pd.Series) -> float:
        """재무 건전성 점수 계산 (0-100)"""
        try:
            score = 0
            max_score = 100
            
            # ROE 점수 (30점)
            roe = row.get('roe', 0)
            if roe > 20:
                score += 30
            elif roe > 15:
                score += 25
            elif roe > 10:
                score += 20
            elif roe > 5:
                score += 10
            
            # 부채비율 점수 (30점)
            debt_ratio = row.get('debt_to_equity', float('inf'))
            if debt_ratio < 0.3:
                score += 30
            elif debt_ratio < 0.5:
                score += 25
            elif debt_ratio < 1.0:
                score += 15
            elif debt_ratio < 2.0:
                score += 5
            
            # 유동비율 점수 (20점)
            current_ratio = row.get('current_ratio', 0)
            if current_ratio > 2.0:
                score += 20
            elif current_ratio > 1.5:
                score += 15
            elif current_ratio > 1.0:
                score += 10
            elif current_ratio > 0.8:
                score += 5
            
            # ROA 점수 (20점)
            roa = row.get('roa', 0)
            if roa > 10:
                score += 20
            elif roa > 7:
                score += 15
            elif roa > 5:
                score += 10
            elif roa > 3:
                score += 5
            
            return min(score, max_score)
            
        except Exception as e:
            logger.error(f"Error calculating financial health score: {e}")
            return 0
    
    def _calculate_value_score(self, row: pd.Series) -> float:
        """가치 점수 계산 (0-100)"""
        try:
            score = 0
            
            # PER 점수 (50점)
            pe_ratio = row.get('pe_ratio', float('inf'))
            if pe_ratio < 10:
                score += 50
            elif pe_ratio < 15:
                score += 40
            elif pe_ratio < 20:
                score += 30
            elif pe_ratio < 25:
                score += 20
            elif pe_ratio < 30:
                score += 10
            
            # PBR 점수 (50점)
            pb_ratio = row.get('pb_ratio', float('inf'))
            if pb_ratio < 1.0:
                score += 50
            elif pb_ratio < 1.5:
                score += 40
            elif pb_ratio < 2.0:
                score += 30
            elif pb_ratio < 2.5:
                score += 20
            elif pb_ratio < 3.0:
                score += 10
            
            return score
            
        except Exception as e:
            logger.error(f"Error calculating value score: {e}")
            return 0
    
    def calculate_trend_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """추세 지표 계산"""
        try:
            result_df = data.copy()
            
            for symbol in data['symbol'].unique():
                mask = data['symbol'] == symbol
                symbol_data = data[mask].sort_values('date')
                
                if len(symbol_data) < 50:
                    continue
                
                close_prices = symbol_data['close']
                
                # 추세 강도 계산 (ADX 근사)
                result_df.loc[mask, 'trend_strength'] = self._calculate_trend_strength(close_prices)
                
                # 지지/저항 수준 계산
                support_resistance = self._calculate_support_resistance(close_prices)
                result_df.loc[mask, 'support_level'] = support_resistance['support']
                result_df.loc[mask, 'resistance_level'] = support_resistance['resistance']
                
                # 가격 위치 (지지선 대비 저항선 사이 위치)
                result_df.loc[mask, 'price_position'] = self._calculate_price_position(
                    close_prices, support_resistance
                )
            
            return result_df
            
        except Exception as e:
            logger.error(f"Error calculating trend indicators: {e}")
            return data
    
    def _calculate_trend_strength(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """추세 강도 계산 (0-100)"""
        try:
            # 방향성 움직임 계산
            price_diff = prices.diff()
            
            up_moves = price_diff.where(price_diff > 0, 0)
            down_moves = abs(price_diff.where(price_diff < 0, 0))
            
            # 평균 방향성 지수 근사
            avg_up = up_moves.rolling(window=period).mean()
            avg_down = down_moves.rolling(window=period).mean()
            
            # 추세 강도 (0-100)
            trend_strength = 100 * abs(avg_up - avg_down) / (avg_up + avg_down)
            trend_strength = trend_strength.fillna(0)
            
            return trend_strength
            
        except Exception as e:
            logger.error(f"Error calculating trend strength: {e}")
            return pd.Series(0, index=prices.index)
    
    def _calculate_support_resistance(self, prices: pd.Series, 
                                    window: int = 20) -> Dict[str, pd.Series]:
        """지지/저항선 계산"""
        try:
            # 롤링 윈도우에서 최고/최저가
            rolling_high = prices.rolling(window=window).max()
            rolling_low = prices.rolling(window=window).min()
            
            # 지지선: 최근 저점들의 평균
            support = rolling_low.rolling(window=5).mean()
            
            # 저항선: 최근 고점들의 평균  
            resistance = rolling_high.rolling(window=5).mean()
            
            return {
                'support': support,
                'resistance': resistance
            }
            
        except Exception as e:
            logger.error(f"Error calculating support/resistance: {e}")
            return {
                'support': pd.Series(0, index=prices.index),
                'resistance': pd.Series(0, index=prices.index)
            }
    
    def _calculate_price_position(self, prices: pd.Series, 
                                support_resistance: Dict[str, pd.Series]) -> pd.Series:
        """현재 가격의 지지/저항 사이 위치 (0-100)"""
        try:
            support = support_resistance['support']
            resistance = support_resistance['resistance']
            
            # 지지선과 저항선 사이에서의 위치
            position = (prices - support) / (resistance - support) * 100
            position = position.clip(0, 100)  # 0-100 범위로 제한
            
            return position.fillna(50)  # 결측값은 중간값으로
            
        except Exception as e:
            logger.error(f"Error calculating price position: {e}")
            return pd.Series(50, index=prices.index)
    
    def calculate_volatility_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """변동성 지표 계산"""
        try:
            result_df = data.copy()
            
            for symbol in data['symbol'].unique():
                mask = data['symbol'] == symbol
                symbol_data = data[mask].sort_values('date')
                
                if len(symbol_data) < 30:
                    continue
                
                close_prices = symbol_data['close']
                high_prices = symbol_data['high']
                low_prices = symbol_data['low']
                
                # 역사적 변동성 (20일)
                returns = close_prices.pct_change()
                result_df.loc[mask, 'historical_volatility'] = returns.rolling(window=20).std() * np.sqrt(252) * 100
                
                # 평균 실체 범위 (ATR)
                result_df.loc[mask, 'atr_20'] = self.technical.calculate_atr(
                    high_prices, low_prices, close_prices, 20
                )
                
                # 변동성 비율 (현재 vs 과거)
                current_vol = returns.rolling(window=10).std()
                past_vol = returns.rolling(window=30).std()
                result_df.loc[mask, 'volatility_ratio'] = (current_vol / past_vol).fillna(1.0)
            
            return result_df
            
        except Exception as e:
            logger.error(f"Error calculating volatility indicators: {e}")
            return data
    
    def get_indicator_summary(self, data: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """특정 종목의 지표 요약"""
        try:
            symbol_data = data[data['symbol'] == symbol].sort_values('date')
            
            if symbol_data.empty:
                return {}
            
            latest = symbol_data.iloc[-1]
            
            summary = {
                'symbol': symbol,
                'date': latest.get('date'),
                'price': latest.get('close', 0),
                
                # 기술적 지표
                'rsi': latest.get('rsi_14', 0),
                'macd_signal': 'buy' if latest.get('macd', 0) > latest.get('macd_signal', 0) else 'sell',
                'bb_position': self._get_bb_position(latest),
                'trend_strength': latest.get('trend_strength', 0),
                
                # 재무 지표
                'pe_ratio': latest.get('pe_ratio', 0),
                'pb_ratio': latest.get('pb_ratio', 0),
                'roe': latest.get('roe', 0),
                'debt_ratio': latest.get('debt_to_equity', 0),
                
                # 복합 점수
                'financial_health': latest.get('financial_health_score', 0),
                'value_score': latest.get('value_score', 0)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting indicator summary for {symbol}: {e}")
            return {}
    
    def _get_bb_position(self, row: pd.Series) -> str:
        """볼린저밴드 위치 판단"""
        try:
            price = row.get('close', 0)
            bb_upper = row.get('bb_upper', 0)
            bb_lower = row.get('bb_lower', 0)
            bb_middle = row.get('bb_middle', 0)
            
            if price > bb_upper:
                return 'overbought'
            elif price < bb_lower:
                return 'oversold'
            elif price > bb_middle:
                return 'above_middle'
            else:
                return 'below_middle'
                
        except Exception as e:
            logger.error(f"Error getting BB position: {e}")
            return 'unknown'