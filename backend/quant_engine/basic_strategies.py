"""
file: strategy_engine/basic_strategies.py
Basic Investment Strategies - 10가지
개인투자자용 기본 전략들
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from base_strategy import BaseStrategy, StrategyMetadata, Signal, PortfolioWeight
from base_strategy import RiskLevel, Complexity, StrategyCategory, StrategyFactory
import technical_indicators as ti
import fundamental_metrics as fm

# 1. 저PER 전략
class LowPEStrategy(BaseStrategy):
    """저PER 전략 - PER 15배 이하 종목 선별"""
    
    def __init__(self, **kwargs):
        super().__init__("Low_PE_Strategy", **kwargs)
    
    def _get_metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            name="저PER 전략",
            description="PER 15배 이하 종목 선별하는 가치투자 전략",
            category=StrategyCategory.BASIC,
            risk_level=RiskLevel.LOW,
            complexity=Complexity.SIMPLE,
            expected_return="8-12%",
            volatility="12-18%",
            min_investment_period="1년 이상",
            rebalancing_frequency="분기별"
        )
    
    def _get_required_parameters(self) -> List[str]:
        return ['max_pe_ratio']
    
    def _get_required_data_columns(self) -> List[str]:
        return super()._get_required_data_columns() + ['pe_ratio', 'market_cap']
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        max_pe = self.parameters.get('max_pe_ratio', 15)
        signals = []
        
        # PE 데이터가 있는 종목들만 처리
        pe_data = data.dropna(subset=['pe_ratio'])
        
        for symbol in pe_data.index:
            pe_ratio = pe_data.loc[symbol, 'pe_ratio']
            
            # 저PER 조건 확인
            if 0 < pe_ratio <= max_pe:
                # 추가 필터링: 적자 기업 제외, 최소 시가총액
                market_cap = pe_data.loc[symbol, 'market_cap']
                if market_cap > 1000:  # 10억 달러 이상
                    signal_strength = min(1.0, (max_pe - pe_ratio) / max_pe)
                    
                    signals.append(Signal(
                        symbol=symbol,
                        timestamp=pd.Timestamp.now(),
                        signal_type='BUY',
                        strength=signal_strength,
                        confidence=0.7,
                        metadata={'pe_ratio': pe_ratio}
                    ))
        
        return self.validate_signals(signals)
    
    def calculate_weights(self, signals: List[Signal], 
                         current_portfolio: Optional[Dict[str, float]] = None) -> List[PortfolioWeight]:
        if not signals:
            return []
        
        # 동일 가중치 방식
        target_weight = 1.0 / len(signals)
        weights = []
        
        for signal in signals:
            current_weight = current_portfolio.get(signal.symbol, 0.0) if current_portfolio else 0.0
            
            weights.append(PortfolioWeight(
                symbol=signal.symbol,
                weight=target_weight,
                target_weight=target_weight,
                current_weight=current_weight,
                rebalance_needed=abs(target_weight - current_weight) > 0.01
            ))
        
        return self.apply_position_sizing(weights)

# 2. 배당 귀족주 전략
class DividendAristocratsStrategy(BaseStrategy):
    """배당 귀족주 전략 - 20년 이상 연속 배당 증가 기업"""
    
    def __init__(self, **kwargs):
        super().__init__("Dividend_Aristocrats_Strategy", **kwargs)
    
    def _get_metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            name="배당 귀족주 전략",
            description="20년 이상 연속 배당 증가 기업 투자",
            category=StrategyCategory.BASIC,
            risk_level=RiskLevel.LOW,
            complexity=Complexity.SIMPLE,
            expected_return="7-10%",
            volatility="10-15%",
            min_investment_period="3년 이상",
            rebalancing_frequency="연 1회"
        )
    
    def _get_required_data_columns(self) -> List[str]:
        return super()._get_required_data_columns() + ['dividend_yield', 'dividend_growth_years']
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        min_dividend_years = self.parameters.get('min_dividend_years', 20)
        min_yield = self.parameters.get('min_dividend_yield', 0.02)
        
        signals = []
        dividend_data = data.dropna(subset=['dividend_yield', 'dividend_growth_years'])
        
        for symbol in dividend_data.index:
            dividend_years = dividend_data.loc[symbol, 'dividend_growth_years']
            dividend_yield = dividend_data.loc[symbol, 'dividend_yield']
            
            if dividend_years >= min_dividend_years and dividend_yield >= min_yield:
                # 신호 강도: 배당 기간과 수익률 기준
                strength = min(1.0, (dividend_years / 30) * 0.7 + (dividend_yield / 0.06) * 0.3)
                
                signals.append(Signal(
                    symbol=symbol,
                    timestamp=pd.Timestamp.now(),
                    signal_type='BUY',
                    strength=strength,
                    confidence=0.8,
                    metadata={
                        'dividend_years': dividend_years,
                        'dividend_yield': dividend_yield
                    }
                ))
        
        return self.validate_signals(signals)
    
    def calculate_weights(self, signals: List[Signal], 
                         current_portfolio: Optional[Dict[str, float]] = None) -> List[PortfolioWeight]:
        if not signals:
            return []
        
        # 배당수익률 기준 가중치
        total_strength = sum(signal.strength for signal in signals)
        weights = []
        
        for signal in signals:
            weight = signal.strength / total_strength
            current_weight = current_portfolio.get(signal.symbol, 0.0) if current_portfolio else 0.0
            
            weights.append(PortfolioWeight(
                symbol=signal.symbol,
                weight=weight,
                target_weight=weight,
                current_weight=current_weight
            ))
        
        return self.apply_position_sizing(weights)

# 3. 단순 모멘텀 전략
class SimpleMomentumStrategy(BaseStrategy):
    """단순 모멘텀 전략 - 최근 3-12개월 수익률 상위 종목"""
    
    def __init__(self, **kwargs):
        super().__init__("Simple_Momentum_Strategy", **kwargs)
    
    def _get_metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            name="단순 모멘텀 전략",
            description="최근 성과 상위 종목 투자, 상승 추세 추종",
            category=StrategyCategory.BASIC,
            risk_level=RiskLevel.MEDIUM,
            complexity=Complexity.SIMPLE,
            expected_return="10-15%",
            volatility="16-22%",
            min_investment_period="6개월 이상",
            rebalancing_frequency="월별"
        )
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        lookback_months = self.parameters.get('lookback_months', 6)
        top_percentile = self.parameters.get('top_percentile', 0.2)  # 상위 20%
        
        signals = []
        
        # 가격 데이터에서 수익률 계산
        returns = data['close'].pct_change(lookback_months * 21)  # 약 월별 거래일
        
        # 상위 percentile 계산
        threshold = returns.quantile(1 - top_percentile)
        
        for symbol in returns.index:
            if pd.isna(returns[symbol]):
                continue
                
            if returns[symbol] >= threshold:
                # 추가 필터: 최근 변동성 확인
                recent_returns = data.loc[symbol, 'close'].pct_change().tail(21)
                volatility = recent_returns.std()
                
                # 과도한 변동성 종목 제외
                max_volatility = self.parameters.get('max_volatility', 0.05)
                if volatility <= max_volatility:
                    strength = min(1.0, returns[symbol] / (threshold * 2))
                    
                    signals.append(Signal(
                        symbol=symbol,
                        timestamp=pd.Timestamp.now(),
                        signal_type='BUY',
                        strength=strength,
                        confidence=0.6,
                        metadata={
                            'momentum_return': returns[symbol],
                            'volatility': volatility
                        }
                    ))
        
        return self.validate_signals(signals)
    
    def calculate_weights(self, signals: List[Signal], 
                         current_portfolio: Optional[Dict[str, float]] = None) -> List[PortfolioWeight]:
        if not signals:
            return []
        
        # 모멘텀 강도 기준 가중치
        total_strength = sum(signal.strength for signal in signals)
        weights = []
        
        for signal in signals:
            weight = signal.strength / total_strength
            current_weight = current_portfolio.get(signal.symbol, 0.0) if current_portfolio else 0.0
            
            weights.append(PortfolioWeight(
                symbol=signal.symbol,
                weight=weight,
                target_weight=weight,
                current_weight=current_weight
            ))
        
        return self.apply_position_sizing(weights)

# 4. 이동평균 교차 전략
class MovingAverageCrossStrategy(BaseStrategy):
    """이동평균 교차 전략 - 20일선이 60일선 돌파"""
    
    def __init__(self, **kwargs):
        super().__init__("Moving_Average_Cross_Strategy", **kwargs)
    
    def _get_metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            name="이동평균 교차 전략",
            description="단기 이동평균이 장기 이동평균 상향 돌파시 매수",
            category=StrategyCategory.BASIC,
            risk_level=RiskLevel.MEDIUM,
            complexity=Complexity.SIMPLE,
            expected_return="8-12%",
            volatility="14-20%",
            min_investment_period="6개월 이상",
            rebalancing_frequency="주별"
        )
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        short_period = self.parameters.get('short_ma', 20)
        long_period = self.parameters.get('long_ma', 60)
        
        signals = []
        
        for symbol in data.index:
            prices = data.loc[symbol, 'close']
            if len(prices) < long_period:
                continue
            
            # 이동평균 계산
            short_ma = ti.simple_moving_average(prices, short_period)
            long_ma = ti.simple_moving_average(prices, long_period)
            
            if len(short_ma) < 2 or len(long_ma) < 2:
                continue
            
            # 골든 크로스 확인 (단기선이 장기선을 상향 돌파)
            current_cross = short_ma.iloc[-1] > long_ma.iloc[-1]
            previous_cross = short_ma.iloc[-2] > long_ma.iloc[-2]
            
            if current_cross and not previous_cross:
                # 교차 강도 계산
                cross_strength = (short_ma.iloc[-1] - long_ma.iloc[-1]) / long_ma.iloc[-1]
                strength = min(1.0, abs(cross_strength) * 10)
                
                signals.append(Signal(
                    symbol=symbol,
                    timestamp=pd.Timestamp.now(),
                    signal_type='BUY',
                    strength=strength,
                    confidence=0.65,
                    metadata={
                        'short_ma': short_ma.iloc[-1],
                        'long_ma': long_ma.iloc[-1],
                        'cross_strength': cross_strength
                    }
                ))
            
            # 데드 크로스 확인 (매도 신호)
            elif not current_cross and previous_cross:
                cross_strength = (long_ma.iloc[-1] - short_ma.iloc[-1]) / long_ma.iloc[-1]
                strength = min(1.0, abs(cross_strength) * 10)
                
                signals.append(Signal(
                    symbol=symbol,
                    timestamp=pd.Timestamp.now(),
                    signal_type='SELL',
                    strength=strength,
                    confidence=0.65,
                    metadata={
                        'short_ma': short_ma.iloc[-1],
                        'long_ma': long_ma.iloc[-1],
                        'cross_strength': cross_strength
                    }
                ))
        
        return self.validate_signals(signals)
    
    def calculate_weights(self, signals: List[Signal], 
                         current_portfolio: Optional[Dict[str, float]] = None) -> List[PortfolioWeight]:
        buy_signals = [s for s in signals if s.signal_type == 'BUY']
        if not buy_signals:
            return []
        
        # 동일 가중치
        target_weight = 1.0 / len(buy_signals)
        weights = []
        
        for signal in buy_signals:
            current_weight = current_portfolio.get(signal.symbol, 0.0) if current_portfolio else 0.0
            
            weights.append(PortfolioWeight(
                symbol=signal.symbol,
                weight=target_weight,
                target_weight=target_weight,
                current_weight=current_weight
            ))
        
        return self.apply_position_sizing(weights)

# 5. RSI 과매수/과매도 전략
class RSIMeanReversionStrategy(BaseStrategy):
    """RSI 과매수/과매도 전략"""
    
    def __init__(self, **kwargs):
        super().__init__("RSI_Mean_Reversion_Strategy", **kwargs)
    
    def _get_metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            name="RSI 평균회귀 전략",
            description="RSI 30 이하 매수, 70 이상 매도",
            category=StrategyCategory.BASIC,
            risk_level=RiskLevel.MEDIUM,
            complexity=Complexity.SIMPLE,
            expected_return="10-13%",
            volatility="12-18%",
            min_investment_period="3개월 이상",
            rebalancing_frequency="주별"
        )
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        rsi_period = self.parameters.get('rsi_period', 14)
        oversold_threshold = self.parameters.get('oversold', 30)
        overbought_threshold = self.parameters.get('overbought', 70)
        
        signals = []
        
        for symbol in data.index:
            prices = data.loc[symbol, 'close']
            if len(prices) < rsi_period + 1:
                continue
            
            rsi = ti.rsi(prices, rsi_period)
            if len(rsi) == 0:
                continue
            
            current_rsi = rsi.iloc[-1]
            
            # 과매도 구간 (매수 신호)
            if current_rsi <= oversold_threshold:
                strength = (oversold_threshold - current_rsi) / oversold_threshold
                
                signals.append(Signal(
                    symbol=symbol,
                    timestamp=pd.Timestamp.now(),
                    signal_type='BUY',
                    strength=strength,
                    confidence=0.7,
                    metadata={'rsi': current_rsi}
                ))
            
            # 과매수 구간 (매도 신호)
            elif current_rsi >= overbought_threshold:
                strength = (current_rsi - overbought_threshold) / (100 - overbought_threshold)
                
                signals.append(Signal(
                    symbol=symbol,
                    timestamp=pd.Timestamp.now(),
                    signal_type='SELL',
                    strength=strength,
                    confidence=0.7,
                    metadata={'rsi': current_rsi}
                ))
        
        return self.validate_signals(signals)
    
    def calculate_weights(self, signals: List[Signal], 
                         current_portfolio: Optional[Dict[str, float]] = None) -> List[PortfolioWeight]:
        buy_signals = [s for s in signals if s.signal_type == 'BUY']
        if not buy_signals:
            return []
        
        # RSI 신호 강도 기반 가중치
        total_strength = sum(signal.strength for signal in buy_signals)
        weights = []
        
        for signal in buy_signals:
            weight = signal.strength / total_strength
            current_weight = current_portfolio.get(signal.symbol, 0.0) if current_portfolio else 0.0
            
            weights.append(PortfolioWeight(
                symbol=signal.symbol,
                weight=weight,
                target_weight=weight,
                current_weight=current_weight
            ))
        
        return self.apply_position_sizing(weights)

# 6. 볼린저 밴드 역발상 전략
class BollingerBandStrategy(BaseStrategy):
    """볼린저 밴드 역발상 전략"""
    
    def __init__(self, **kwargs):
        super().__init__("Bollinger_Band_Strategy", **kwargs)
    
    def _get_metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            name="볼린저 밴드 역발상 전략",
            description="하단선 터치시 매수, 상단선 터치시 매도",
            category=StrategyCategory.BASIC,
            risk_level=RiskLevel.MEDIUM,
            complexity=Complexity.SIMPLE,
            expected_return="9-12%",
            volatility="13-19%",
            min_investment_period="6개월 이상",
            rebalancing_frequency="주별"
        )
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        bb_period = self.parameters.get('bb_period', 20)
        bb_std = self.parameters.get('bb_std', 2)
        
        signals = []
        
        for symbol in data.index:
            prices = data.loc[symbol, 'close']
            if len(prices) < bb_period:
                continue
            
            bb_upper, bb_middle, bb_lower = ti.bollinger_bands(prices, bb_period, bb_std)
            
            if len(bb_upper) == 0:
                continue
            
            current_price = prices.iloc[-1]
            current_upper = bb_upper.iloc[-1]
            current_lower = bb_lower.iloc[-1]
            current_middle = bb_middle.iloc[-1]
            
            # 하단선 근처 (매수 신호)
            if current_price <= current_lower * 1.02:  # 2% 버퍼
                distance_ratio = (current_lower - current_price) / (current_middle - current_lower)
                strength = min(1.0, max(0, distance_ratio))
                
                signals.append(Signal(
                    symbol=symbol,
                    timestamp=pd.Timestamp.now(),
                    signal_type='BUY',
                    strength=strength,
                    confidence=0.65,
                    metadata={
                        'price': current_price,
                        'bb_lower': current_lower,
                        'bb_middle': current_middle
                    }
                ))
            
            # 상단선 근처 (매도 신호)
            elif current_price >= current_upper * 0.98:  # 2% 버퍼
                distance_ratio = (current_price - current_upper) / (current_upper - current_middle)
                strength = min(1.0, max(0, distance_ratio))
                
                signals.append(Signal(
                    symbol=symbol,
                    timestamp=pd.Timestamp.now(),
                    signal_type='SELL',
                    strength=strength,
                    confidence=0.65,
                    metadata={
                        'price': current_price,
                        'bb_upper': current_upper,
                        'bb_middle': current_middle
                    }
                ))
        
        return self.validate_signals(signals)
    
    def calculate_weights(self, signals: List[Signal], 
                         current_portfolio: Optional[Dict[str, float]] = None) -> List[PortfolioWeight]:
        buy_signals = [s for s in signals if s.signal_type == 'BUY']
        if not buy_signals:
            return []
        
        # 동일 가중치
        target_weight = 1.0 / len(buy_signals)
        weights = []
        
        for signal in buy_signals:
            current_weight = current_portfolio.get(signal.symbol, 0.0) if current_portfolio else 0.0
            
            weights.append(PortfolioWeight(
                symbol=signal.symbol,
                weight=target_weight,
                target_weight=target_weight,
                current_weight=current_weight
            ))
        
        return self.apply_position_sizing(weights)

# 7. 소형주 프리미엄 전략
class SmallCapStrategy(BaseStrategy):
    """소형주 프리미엄 전략"""
    
    def __init__(self, **kwargs):
        super().__init__("Small_Cap_Strategy", **kwargs)
    
    def _get_metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            name="소형주 프리미엄 전략",
            description="시가총액 하위 종목 투자로 초과수익 추구",
            category=StrategyCategory.BASIC,
            risk_level=RiskLevel.HIGH,
            complexity=Complexity.SIMPLE,
            expected_return="12-18%",
            volatility="20-30%",
            min_investment_period="2년 이상",
            rebalancing_frequency="분기별"
        )
    
    def _get_required_data_columns(self) -> List[str]:
        return super()._get_required_data_columns() + ['market_cap']
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        small_cap_percentile = self.parameters.get('small_cap_percentile', 0.2)  # 하위 20%
        
        signals = []
        market_cap_data = data.dropna(subset=['market_cap'])
        
        # 시가총액 하위 percentile 계산
        threshold = market_cap_data['market_cap'].quantile(small_cap_percentile)
        
        for symbol in market_cap_data.index:
            market_cap = market_cap_data.loc[symbol, 'market_cap']
            
            if market_cap <= threshold:
                # 최소 유동성 확인
                min_market_cap = self.parameters.get('min_market_cap', 100)  # 1억 달러
                if market_cap >= min_market_cap:
                    # 신호 강도는 시가총액이 작을수록 높음
                    strength = 1.0 - (market_cap / threshold)
                    
                    signals.append(Signal(
                        symbol=symbol,
                        timestamp=pd.Timestamp.now(),
                        signal_type='BUY',
                        strength=strength,
                        confidence=0.6,
                        metadata={'market_cap': market_cap}
                    ))
        
        return self.validate_signals(signals)
    
    def calculate_weights(self, signals: List[Signal], 
                         current_portfolio: Optional[Dict[str, float]] = None) -> List[PortfolioWeight]:
        if not signals:
            return []
        
        # 동일 가중치 (소형주는 집중 위험 방지)
        target_weight = 1.0 / len(signals)
        weights = []
        
        for signal in signals:
            current_weight = current_portfolio.get(signal.symbol, 0.0) if current_portfolio else 0.0
            
            weights.append(PortfolioWeight(
                symbol=signal.symbol,
                weight=target_weight,
                target_weight=target_weight,
                current_weight=current_weight
            ))
        
        return self.apply_position_sizing(weights)

# 8. 저변동성 전략
class LowVolatilityStrategy(BaseStrategy):
    """저변동성 전략"""
    
    def __init__(self, **kwargs):
        super().__init__("Low_Volatility_Strategy", **kwargs)
    
    def _get_metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            name="저변동성 전략",
            description="변동성이 낮은 종목으로 안정적 수익 추구",
            category=StrategyCategory.BASIC,
            risk_level=RiskLevel.LOW,
            complexity=Complexity.SIMPLE,
            expected_return="8-11%",
            volatility="8-12%",
            min_investment_period="1년 이상",
            rebalancing_frequency="분기별"
        )
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        volatility_period = self.parameters.get('volatility_period', 60)
        low_vol_percentile = self.parameters.get('low_vol_percentile', 0.3)  # 하위 30%
        
        signals = []
        volatilities = {}
        
        # 각 종목의 변동성 계산
        for symbol in data.index:
            prices = data.loc[symbol, 'close']
            if len(prices) < volatility_period:
                continue
            
            returns = prices.pct_change().dropna()
            volatility = returns.tail(volatility_period).std() * np.sqrt(252)  # 연율화
            volatilities[symbol] = volatility
        
        if not volatilities:
            return []
        
        # 저변동성 기준선 계산
        vol_values = list(volatilities.values())
        threshold = np.percentile(vol_values, low_vol_percentile * 100)
        
        for symbol, volatility in volatilities.items():
            if volatility <= threshold:
                # 변동성이 낮을수록 높은 강도
                strength = 1.0 - (volatility / threshold)
                
                signals.append(Signal(
                    symbol=symbol,
                    timestamp=pd.Timestamp.now(),
                    signal_type='BUY',
                    strength=strength,
                    confidence=0.75,
                    metadata={'volatility': volatility}
                ))
        
        return self.validate_signals(signals)
    
    def calculate_weights(self, signals: List[Signal], 
                         current_portfolio: Optional[Dict[str, float]] = None) -> List[PortfolioWeight]:
        if not signals:
            return []
        
        # 역변동성 가중치 (변동성이 낮을수록 높은 가중치)
        total_inv_strength = sum(1/signal.strength if signal.strength > 0 else 1 for signal in signals)
        weights = []
        
        for signal in signals:
            inv_strength = 1/signal.strength if signal.strength > 0 else 1
            weight = inv_strength / total_inv_strength
            current_weight = current_portfolio.get(signal.symbol, 0.0) if current_portfolio else 0.0
            
            weights.append(PortfolioWeight(
                symbol=signal.symbol,
                weight=weight,
                target_weight=weight,
                current_weight=current_weight
            ))
        
        return self.apply_position_sizing(weights)

# 9. 품질 팩터 전략
class QualityFactorStrategy(BaseStrategy):
    """품질 팩터 전략"""
    
    def __init__(self, **kwargs):
        super().__init__("Quality_Factor_Strategy", **kwargs)
    
    def _get_metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            name="품질 팩터 전략",
            description="ROE, 부채비율 등 재무 건전성 우수 기업",
            category=StrategyCategory.BASIC,
            risk_level=RiskLevel.LOW,
            complexity=Complexity.SIMPLE,
            expected_return="9-13%",
            volatility="12-16%",
            min_investment_period="2년 이상",
            rebalancing_frequency="분기별"
        )
    
    def _get_required_data_columns(self) -> List[str]:
        return super()._get_required_data_columns() + ['roe', 'debt_ratio', 'current_ratio']
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        min_roe = self.parameters.get('min_roe', 0.15)
        max_debt_ratio = self.parameters.get('max_debt_ratio', 0.5)
        min_current_ratio = self.parameters.get('min_current_ratio', 1.2)
        
        signals = []
        quality_data = data.dropna(subset=['roe', 'debt_ratio', 'current_ratio'])
        
        for symbol in quality_data.index:
            roe = quality_data.loc[symbol, 'roe']
            debt_ratio = quality_data.loc[symbol, 'debt_ratio']
            current_ratio = quality_data.loc[symbol, 'current_ratio']
            
            # 품질 기준 충족 확인
            if roe >= min_roe and debt_ratio <= max_debt_ratio and current_ratio >= min_current_ratio:
                # 품질 점수 계산 (각 지표의 우수성 기준)
                roe_score = min(1.0, roe / 0.3)  # ROE 30%를 만점으로
                debt_score = max(0.0, (max_debt_ratio - debt_ratio) / max_debt_ratio)
                current_score = min(1.0, (current_ratio - 1.0) / 2.0)  # 유동비율 3.0을 만점으로
                
                quality_score = (roe_score + debt_score + current_score) / 3
                
                signals.append(Signal(
                    symbol=symbol,
                    timestamp=pd.Timestamp.now(),
                    signal_type='BUY',
                    strength=quality_score,
                    confidence=0.8,
                    metadata={
                        'roe': roe,
                        'debt_ratio': debt_ratio,
                        'current_ratio': current_ratio,
                        'quality_score': quality_score
                    }
                ))
        
        return self.validate_signals(signals)
    
    def calculate_weights(self, signals: List[Signal], 
                         current_portfolio: Optional[Dict[str, float]] = None) -> List[PortfolioWeight]:
        if not signals:
            return []
        
        # 품질 점수 기반 가중치
        total_strength = sum(signal.strength for signal in signals)
        weights = []
        
        for signal in signals:
            weight = signal.strength / total_strength
            current_weight = current_portfolio.get(signal.symbol, 0.0) if current_portfolio else 0.0
            
            weights.append(PortfolioWeight(
                symbol=signal.symbol,
                weight=weight,
                target_weight=weight,
                current_weight=current_weight
            ))
        
        return self.apply_position_sizing(weights)

# 10. 정기 리밸런싱 전략
class RegularRebalancingStrategy(BaseStrategy):
    """정기 리밸런싱 전략"""
    
    def __init__(self, **kwargs):
        super().__init__("Regular_Rebalancing_Strategy", **kwargs)
    
    def _get_metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            name="정기 리밸런싱 전략",
            description="정해진 비율로 정기적 리밸런싱하여 위험 관리",
            category=StrategyCategory.BASIC,
            risk_level=RiskLevel.MEDIUM,
            complexity=Complexity.SIMPLE,
            expected_return="8-12%",
            volatility="10-16%",
            min_investment_period="1년 이상",
            rebalancing_frequency="월별"
        )
    
    def _get_required_parameters(self) -> List[str]:
        return ['target_allocation']
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        target_allocation = self.parameters.get('target_allocation', {})
        rebalance_threshold = self.parameters.get('rebalance_threshold', 0.05)  # 5% 편차
        
        signals = []
        
        if not target_allocation:
            # 기본 동일 가중치
            symbols = data.index.tolist()
            equal_weight = 1.0 / len(symbols)
            target_allocation = {symbol: equal_weight for symbol in symbols}
        
        current_portfolio = self.parameters.get('current_portfolio', {})
        
        for symbol, target_weight in target_allocation.items():
            current_weight = current_portfolio.get(symbol, 0.0)
            weight_diff = abs(target_weight - current_weight)
            
            if weight_diff > rebalance_threshold:
                if target_weight > current_weight:
                    signal_type = 'BUY'
                    strength = min(1.0, weight_diff / rebalance_threshold)
                else:
                    signal_type = 'SELL'
                    strength = min(1.0, weight_diff / rebalance_threshold)
                
                signals.append(Signal(
                    symbol=symbol,
                    timestamp=pd.Timestamp.now(),
                    signal_type=signal_type,
                    strength=strength,
                    confidence=0.9,
                    metadata={
                        'target_weight': target_weight,
                        'current_weight': current_weight,
                        'weight_diff': weight_diff
                    }
                ))
        
        return self.validate_signals(signals)
    
    def calculate_weights(self, signals: List[Signal], 
                         current_portfolio: Optional[Dict[str, float]] = None) -> List[PortfolioWeight]:
        target_allocation = self.parameters.get('target_allocation', {})
        
        if not target_allocation:
            return []
        
        weights = []
        
        for symbol, target_weight in target_allocation.items():
            current_weight = current_portfolio.get(symbol, 0.0) if current_portfolio else 0.0
            
            weights.append(PortfolioWeight(
                symbol=symbol,
                weight=target_weight,
                target_weight=target_weight,
                current_weight=current_weight,
                rebalance_needed=abs(target_weight - current_weight) > 0.01
            ))
        
        return weights

# 전략 팩토리에 등록
def register_basic_strategies():
    """기본 전략들을 팩토리에 등록"""
    StrategyFactory.register_strategy("low_pe", LowPEStrategy)
    StrategyFactory.register_strategy("dividend_aristocrats", DividendAristocratsStrategy)
    StrategyFactory.register_strategy("simple_momentum", SimpleMomentumStrategy)
    StrategyFactory.register_strategy("moving_average_cross", MovingAverageCrossStrategy)
    StrategyFactory.register_strategy("rsi_mean_reversion", RSIMeanReversionStrategy)
    StrategyFactory.register_strategy("bollinger_band", BollingerBandStrategy)
    StrategyFactory.register_strategy("small_cap", SmallCapStrategy)
    StrategyFactory.register_strategy("low_volatility", LowVolatilityStrategy)
    StrategyFactory.register_strategy("quality_factor", QualityFactorStrategy)
    StrategyFactory.register_strategy("regular_rebalancing", RegularRebalancingStrategy)

# 모듈 로드 시 자동 등록
register_basic_strategies()