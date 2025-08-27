"""
File: backtester/strategies/composite_top10_strategy.py
Composite Strategy Using Top 10 Quant Indicators - Fixed Version
"""

import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy

# Safe imports - 구현된 전략들만 import
try:
    from .fundamental_ratio_strategies import (
        PERStrategy, PBRStrategy, ROEStrategy, DebtEquityStrategy, PEGStrategy
    )
    FUNDAMENTAL_STRATEGIES_AVAILABLE = True
except ImportError:
    print("Warning: Fundamental strategies not available")
    FUNDAMENTAL_STRATEGIES_AVAILABLE = False

try:
    from .technical_indicator_strategies import (
        MovingAverageStrategy, RSIStrategy
    )
    TECHNICAL_STRATEGIES_AVAILABLE = True
except ImportError:
    print("Warning: Technical strategies not available")
    TECHNICAL_STRATEGIES_AVAILABLE = False

class Top10CompositeStrategy(BaseStrategy):
    """TOP 10 지표를 통합한 종합 전략 (안전한 버전)"""
    
    def __init__(self):
        super().__init__("TOP 10 Composite Strategy")
        
        # 개별 전략 인스턴스 (사용 가능한 것만)
        self.fundamental_strategies = {}
        self.technical_strategies = {}
        
        if FUNDAMENTAL_STRATEGIES_AVAILABLE:
            try:
                self.fundamental_strategies = {
                    'PER': PERStrategy(),
                    'PBR': PBRStrategy(),
                    'ROE': ROEStrategy(),
                    'Debt': DebtEquityStrategy(),
                    'PEG': PEGStrategy()
                }
            except Exception as e:
                print(f"Warning: Could not initialize fundamental strategies: {e}")
                self.fundamental_strategies = {}
        
        if TECHNICAL_STRATEGIES_AVAILABLE:
            try:
                self.technical_strategies = {
                    'MA': MovingAverageStrategy(),
                    'RSI': RSIStrategy()
                }
            except Exception as e:
                print(f"Warning: Could not initialize technical strategies: {e}")
                self.technical_strategies = {}
        
        # 가중치 설정
        self.weights = {
            'fundamental': 0.6,  # 재무지표 60%
            'technical': 0.4     # 기술지표 40%
        }
        
        # 재무지표 가중치 (5개 전략)
        self.fundamental_weights = {
            'PER': 0.25,    # 25%
            'PBR': 0.20,    # 20%
            'ROE': 0.25,    # 25%
            'Debt': 0.15,   # 15%
            'PEG': 0.15     # 15%
        }
        
        # 기술지표 가중치 (구현된 것만)
        self.technical_weights = {
            'MA': 0.60,     # 60% (이동평균)
            'RSI': 0.40,    # 40% (RSI)
        }
        
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """TOP 10 지표를 통합한 매매신호 생성"""
        signals = pd.Series(0, index=data.index)
        
        try:
            # 1. 재무지표 점수 계산
            fundamental_score = self._calculate_fundamental_score(data)
            
            # 2. 기술지표 점수 계산
            technical_score = self._calculate_technical_score(data)
            
            # 3. 종합 점수 계산
            composite_score = (
                fundamental_score * self.weights['fundamental'] +
                technical_score * self.weights['technical']
            )
            
            # 4. 신호 생성 (임계값 기반)
            signals[composite_score >= 0.7] = 1.0   # 강한 매수
            signals[composite_score >= 0.5] = 0.7   # 중간 매수
            signals[composite_score <= -0.7] = -1.0 # 강한 매도
            signals[composite_score <= -0.5] = -0.7 # 중간 매도
            
            # 5. 추가 필터링 (리스크 관리)
            filtered_signals = self._apply_risk_filters(signals, data)
            
            return filtered_signals
            
        except Exception as e:
            print(f"Error in Top10CompositeStrategy.generate_signals: {e}")
            return pd.Series(0, index=data.index)
    
    def _calculate_fundamental_score(self, data: pd.DataFrame) -> pd.Series:
        """재무지표 종합 점수 계산"""
        fund_scores = {}
        
        if not self.fundamental_strategies:
            # 재무 전략이 없으면 기본 점수 반환
            return pd.Series(0, index=data.index)
        
        for name, strategy in self.fundamental_strategies.items():
            try:
                strategy_signals = strategy.generate_signals(data)
                # 신호를 -1~1에서 0~1 점수로 변환
                strategy_score = (strategy_signals + 1) / 2
                fund_scores[name] = strategy_score * self.fundamental_weights[name]
            except Exception as e:
                print(f"Error in fundamental strategy {name}: {e}")
                # 오류 시 중립 점수
                fund_scores[name] = pd.Series(0.5, index=data.index) * self.fundamental_weights[name]
        
        # 가중 평균 계산
        fundamental_score = pd.Series(0, index=data.index)
        for score in fund_scores.values():
            fundamental_score += score
        
        return (fundamental_score - 0.5) * 2  # -1~1 범위로 재조정
    
    def _calculate_technical_score(self, data: pd.DataFrame) -> pd.Series:
        """기술지표 종합 점수 계산"""
        tech_scores = {}
        
        if not self.technical_strategies:
            # 기술 전략이 없으면 기본 점수 반환
            return pd.Series(0, index=data.index)
        
        for name, strategy in self.technical_strategies.items():
            try:
                strategy_signals = strategy.generate_signals(data)
                # 신호를 -1~1에서 0~1 점수로 변환
                strategy_score = (strategy_signals + 1) / 2
                tech_scores[name] = strategy_score * self.technical_weights[name]
            except Exception as e:
                print(f"Error in technical strategy {name}: {e}")
                # 오류 시 중립 점수
                tech_scores[name] = pd.Series(0.5, index=data.index) * self.technical_weights[name]
        
        # 가중 평균 계산
        technical_score = pd.Series(0, index=data.index)
        for score in tech_scores.values():
            technical_score += score
        
        return (technical_score - 0.5) * 2  # -1~1 범위로 재조정
    
    def _apply_risk_filters(self, signals: pd.Series, data: pd.DataFrame) -> pd.Series:
        """리스크 관리 필터 적용"""
        filtered_signals = signals.copy()
        
        try:
            close = data['Close']
            
            # 1. 변동성 필터
            returns = close.pct_change()
            volatility = returns.rolling(window=20).std() * np.sqrt(252)
            high_vol_mask = volatility > 0.40  # 40% 이상 고변동성
            
            # 고변동성 시 신호 강도 감소
            filtered_signals[high_vol_mask] *= 0.5
            
            # 2. 트렌드 필터
            if len(data) > 200:
                sma_200 = close.rolling(window=200).mean()
                strong_downtrend = close < sma_200 * 0.9
                
                # 강한 하락추세에서는 매수 신호 제거
                filtered_signals[strong_downtrend & (filtered_signals > 0)] = 0
            
            # 3. 모멘텀 필터
            if len(data) > 21:
                momentum_1m = close.pct_change(21)
                negative_momentum = momentum_1m < -0.20
                
                # 강한 부정적 모멘텀에서는 매수 신호 제거
                filtered_signals[negative_momentum & (filtered_signals > 0)] = 0
                
        except Exception as e:
            print(f"Error in risk filters: {e}")
            # 오류 시 원본 신호 반환
            pass
        
        return filtered_signals
    
    def analyze_individual_indicators(self, data: pd.DataFrame) -> dict:
        """개별 지표 분석 결과"""
        analysis = {
            'fundamental_analysis': {},
            'technical_analysis': {},
            'composite_score': 0,
            'signal_strength': 'neutral'
        }
        
        try:
            # 재무지표 분석
            for name, strategy in self.fundamental_strategies.items():
                try:
                    signals = strategy.generate_signals(data)
                    current_signal = signals.iloc[-1] if len(signals) > 0 else 0
                    analysis['fundamental_analysis'][name] = {
                        'signal': current_signal,
                        'interpretation': self._interpret_signal(current_signal),
                        'weight': self.fundamental_weights[name]
                    }
                except Exception as e:
                    analysis['fundamental_analysis'][name] = {
                        'signal': 0,
                        'interpretation': 'neutral',
                        'weight': self.fundamental_weights[name],
                        'error': str(e)
                    }
            
            # 기술지표 분석
            for name, strategy in self.technical_strategies.items():
                try:
                    signals = strategy.generate_signals(data)
                    current_signal = signals.iloc[-1] if len(signals) > 0 else 0
                    analysis['technical_analysis'][name] = {
                        'signal': current_signal,
                        'interpretation': self._interpret_signal(current_signal),
                        'weight': self.technical_weights[name]
                    }
                except Exception as e:
                    analysis['technical_analysis'][name] = {
                        'signal': 0,
                        'interpretation': 'neutral',
                        'weight': self.technical_weights[name],
                        'error': str(e)
                    }
            
            # 종합 점수 계산
            fundamental_score = self._calculate_fundamental_score(data).iloc[-1] if len(data) > 0 else 0
            technical_score = self._calculate_technical_score(data).iloc[-1] if len(data) > 0 else 0
            composite_score = (
                fundamental_score * self.weights['fundamental'] +
                technical_score * self.weights['technical']
            )
            
            analysis['composite_score'] = composite_score
            analysis['signal_strength'] = self._interpret_signal(composite_score)
            analysis['fundamental_score'] = fundamental_score
            analysis['technical_score'] = technical_score
            
        except Exception as e:
            print(f"Error in analyze_individual_indicators: {e}")
            
        return analysis
    
    def _interpret_signal(self, signal_value: float) -> str:
        """신호 값 해석"""
        if signal_value >= 0.7:
            return 'strong_buy'
        elif signal_value >= 0.3:
            return 'buy'
        elif signal_value >= -0.3:
            return 'neutral'
        elif signal_value >= -0.7:
            return 'sell'
        else:
            return 'strong_sell'
    
    def generate_trading_report(self, data: pd.DataFrame) -> str:
        """거래 보고서 생성"""
        try:
            analysis = self.analyze_individual_indicators(data)
            
            report = f"""
📊 TOP 10 지표 종합 분석 보고서
{'='*50}

🎯 종합 판단: {analysis['signal_strength'].upper()}
📈 종합 점수: {analysis['composite_score']:.3f}

💰 재무지표 분석 (가중치 60%):
점수: {analysis.get('fundamental_score', 0):.3f}
"""
            
            for name, result in analysis['fundamental_analysis'].items():
                signal_emoji = "🟢" if result['signal'] > 0.3 else "🔴" if result['signal'] < -0.3 else "🟡"
                report += f"  {signal_emoji} {name}: {result['interpretation']} ({result['signal']:.2f})\n"
            
            report += f"""
📈 기술지표 분석 (가중치 40%):
점수: {analysis.get('technical_score', 0):.3f}
"""
            
            for name, result in analysis['technical_analysis'].items():
                signal_emoji = "🟢" if result['signal'] > 0.3 else "🔴" if result['signal'] < -0.3 else "🟡"
                report += f"  {signal_emoji} {name}: {result['interpretation']} ({result['signal']:.2f})\n"
            
            report += f"""
💡 투자 권고:
{self._generate_recommendation(analysis['composite_score'])}

⚠️ 주의사항:
- 이 분석은 과거 데이터 기반 참고용입니다
- 실제 투자 시 추가적인 리스크 관리가 필요합니다
- 시장 상황과 개별 기업 뉴스를 종합적으로 고려하세요
"""
            
            return report
            
        except Exception as e:
            return f"보고서 생성 중 오류 발생: {str(e)}"
    
    def _generate_recommendation(self, score: float) -> str:
        """점수 기반 투자 권고 생성"""
        if score >= 0.7:
            return """🚀 강력 매수 추천
- 재무지표와 기술지표가 모두 긍정적
- 적극적인 매수 포지션 고려
- 목표 수익률: 15-25%"""
        elif score >= 0.3:
            return """📈 매수 추천  
- 대부분의 지표가 긍정적
- 점진적 매수 포지션 고려
- 목표 수익률: 8-15%"""
        elif score >= -0.3:
            return """⚖️ 중립/관망
- 지표들이 혼재된 신호
- 추가 정보 수집 후 판단
- 기존 포지션 유지"""
        elif score >= -0.7:
            return """📉 매도 고려
- 부정적 신호가 우세
- 포지션 축소 고려
- 손절선 설정 필요"""
        else:
            return """⛔ 강력 매도 추천
- 대부분의 지표가 부정적
- 즉시 포지션 정리 고려  
- 재진입 시점 대기"""

class AdaptiveTop10Strategy(BaseStrategy):
    """시장 상황에 따라 적응하는 TOP 10 전략 (간소화 버전)"""
    
    def __init__(self):
        super().__init__("Adaptive TOP 10 Strategy")
        self.base_strategy = Top10CompositeStrategy()
        self.market_regime_period = 60  # 시장 체제 분석 기간
        
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """시장 상황 적응형 매매신호 생성"""
        try:
            # 1. 시장 체제 분석
            market_regime = self._analyze_market_regime(data)
            
            # 2. 기본 신호 생성
            base_signals = self.base_strategy.generate_signals(data)
            
            # 3. 시장 체제에 따른 신호 조정
            adapted_signals = self._adapt_signals_to_regime(base_signals, market_regime, data)
            
            return adapted_signals
            
        except Exception as e:
            print(f"Error in AdaptiveTop10Strategy: {e}")
            return pd.Series(0, index=data.index)
    
    def _analyze_market_regime(self, data: pd.DataFrame) -> pd.Series:
        """시장 체제 분석 (상승/하락/횡보)"""
        try:
            close = data['Close']
            returns = close.pct_change()
            
            # 트렌드 강도
            sma_20 = close.rolling(window=20).mean()
            sma_50 = close.rolling(window=50).mean()
            sma_200 = close.rolling(window=200).mean()
            
            # 변동성
            volatility = returns.rolling(window=self.market_regime_period).std() * np.sqrt(252)
            
            # 모멘텀
            momentum = close.pct_change(self.market_regime_period)
            
            regime = pd.Series('sideways', index=data.index)
            
            # 상승장: 강한 상승 모멘텀 + 이동평균 정배열
            bull_market = (
                (momentum > 0.15) & 
                (close > sma_20) & 
                (sma_20 > sma_50) & 
                (sma_50 > sma_200)
            )
            
            # 하락장: 강한 하락 모멘텀 + 이동평균 역배열
            bear_market = (
                (momentum < -0.15) & 
                (close < sma_20) & 
                (sma_20 < sma_50) & 
                (sma_50 < sma_200)
            )
            
            # 변동성장: 높은 변동성
            if len(volatility) > 252:
                volatile_market = volatility > volatility.rolling(window=252).quantile(0.8)
                regime[volatile_market] = 'volatile'
            
            regime[bull_market] = 'bull'
            regime[bear_market] = 'bear'
            
            return regime
            
        except Exception as e:
            print(f"Error in market regime analysis: {e}")
            return pd.Series('sideways', index=data.index)
    
    def _adapt_signals_to_regime(self, signals: pd.Series, regime: pd.Series, data: pd.DataFrame) -> pd.Series:
        """시장 체제에 따른 신호 조정"""
        try:
            adapted_signals = signals.copy()
            
            # 상승장: 매수 신호 강화
            bull_mask = regime == 'bull'
            adapted_signals[bull_mask & (signals > 0)] *= 1.2
            
            # 하락장: 매수 신호 약화, 매도 신호 강화
            bear_mask = regime == 'bear'
            adapted_signals[bear_mask & (signals > 0)] *= 0.5
            adapted_signals[bear_mask & (signals < 0)] *= 1.3
            
            # 변동성장: 모든 신호 약화 (관망)
            volatile_mask = regime == 'volatile'
            adapted_signals[volatile_mask] *= 0.3
            
            return np.clip(adapted_signals, -1, 1)
            
        except Exception as e:
            print(f"Error in signal adaptation: {e}")
            return signals

class Top10SectorRotationStrategy(BaseStrategy):
    """TOP 10 지표 기반 섹터 로테이션 전략 (간소화 버전)"""
    
    def __init__(self):
        super().__init__("TOP 10 Sector Rotation Strategy")
        self.base_strategy = Top10CompositeStrategy()
        
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """섹터별 강도 조정 신호 생성"""
        try:
            # 기본 신호
            base_signals = self.base_strategy.generate_signals(data)
            
            # 섹터 특성 반영 (간단한 예시)
            sector_adjusted_signals = self._adjust_for_sector_characteristics(base_signals, data)
            
            return sector_adjusted_signals
            
        except Exception as e:
            print(f"Error in Top10SectorRotationStrategy: {e}")
            return pd.Series(0, index=data.index)
    
    def _adjust_for_sector_characteristics(self, signals: pd.Series, data: pd.DataFrame) -> pd.Series:
        """섹터 특성에 따른 신호 조정 (예시)"""
        try:
            close = data['Close']
            returns = close.pct_change()
            volatility = returns.rolling(window=60).std() * np.sqrt(252)
            
            adjusted_signals = signals.copy()
            
            # 고변동성 종목 (기술주 추정): 모멘텀 신호 강화
            if len(volatility) > 0:
                high_vol_mask = volatility > volatility.quantile(0.7)
                adjusted_signals[high_vol_mask & (signals > 0)] *= 1.2
                
                # 저변동성 종목 (유틸리티 추정): 안정성 중시
                low_vol_mask = volatility < volatility.quantile(0.3)
                adjusted_signals[low_vol_mask] *= 0.8
            
            return adjusted_signals
            
        except Exception as e:
            print(f"Error in sector adjustment: {e}")
            return signals