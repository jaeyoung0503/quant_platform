"""
Growth & Momentum Strategies - 성장/모멘텀 관련 고급 전략 3가지
윌리엄 오닐의 CAN SLIM, 제임스 오쇼네시 전략 포함
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from base_strategy import BaseStrategy, StrategyMetadata, Signal, PortfolioWeight
from base_strategy import RiskLevel, Complexity, StrategyCategory, StrategyFactory
import technical_indicators as ti
import fundamental_metrics as fm

# 15. 윌리엄 오닐의 CAN SLIM 전략
class WilliamONeilCANSLIMStrategy(BaseStrategy):
    """윌리엄 오닐의 CAN SLIM 전략"""
    
    def __init__(self, **kwargs):
        super().__init__("William_ONeil_CANSLIM_Strategy", **kwargs)
    
    def _get_metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            name="윌리엄 오닐의 CAN SLIM",
            description="7가지 기준으로 고성장주 발굴, 모멘텀과 펀더멘털 결합",
            category=StrategyCategory.ADVANCED,
            risk_level=RiskLevel.HIGH,
            complexity=Complexity.COMPLEX,
            expected_return="15-25%",
            volatility="20-30%",
            min_investment_period="6개월-2년",
            rebalancing_frequency="월별"
        )
    
    def _get_required_data_columns(self) -> List[str]:
        return super()._get_required_data_columns() + [
            'eps_growth_current', 'eps_growth_annual', 'new_products', 'new_management',
            'supply_demand', 'leading_stock', 'institutional_ownership', 'market_direction',
            'price_52w_high', 'relative_strength', 'industry_rank'
        ]
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        signals = []
        
        # CAN SLIM 각 요소별 최소 기준
        min_current_earnings = self.parameters.get('min_current_earnings', 0.25)  # 25%
        min_annual_earnings = self.parameters.get('min_annual_earnings', 0.25)   # 25%
        min_relative_strength = self.parameters.get('min_relative_strength', 80)  # 80 이상
        min_institutional_ownership = self.parameters.get('min_institutional_ownership', 0.1)
        price_near_high_threshold = self.parameters.get('price_near_high', 0.85)  # 52주 고점의 85%
        
        canslim_data = data.dropna(subset=['eps_growth_current', 'eps_growth_annual'])
        
        for symbol in canslim_data.index:
            company_data = canslim_data.loc[symbol]
            
            # CAN SLIM 7가지 기준 평가
            canslim_scores = self._evaluate_canslim_criteria(company_data)
            
            # 각 기준별 점수
            c_score = canslim_scores['current_earnings']
            a_score = canslim_scores['annual_earnings']
            n_score = canslim_scores['new_factors']
            s_score = canslim_scores['supply_demand']
            l_score = canslim_scores['leader']
            i_score = canslim_scores['institutional']
            m_score = canslim_scores['market_direction']
            
            # 종합 CAN SLIM 점수
            total_score = (c_score + a_score + n_score + s_score + l_score + i_score + m_score) / 7
            
            # 최소 기준 충족 확인
            basic_requirements = [
                c_score >= 0.6,  # C: 현재 분기 수익 25% 이상 증가
                a_score >= 0.6,  # A: 연간 수익 증가 지속
                l_score >= 0.6,  # L: 업종 선도주
                m_score >= 0.5   # M: 시장 방향 확인
            ]
            
            if sum(basic_requirements) >= 3 and total_score >= 0.65:
                # 추가 기술적 확인
                technical_score = self._evaluate_technical_breakout(company_data)
                
                if technical_score >= 0.6:
                    final_strength = min(1.0, total_score * technical_score * 1.2)
                    
                    signals.append(Signal(
                        symbol=symbol,
                        timestamp=pd.Timestamp.now(),
                        signal_type='BUY',
                        strength=final_strength,
                        confidence=0.75,
                        metadata={
                            'canslim_total_score': total_score,
                            'technical_score': technical_score,
                            'c_score': c_score,
                            'a_score': a_score,
                            'n_score': n_score,
                            's_score': s_score,
                            'l_score': l_score,
                            'i_score': i_score,
                            'm_score': m_score
                        }
                    ))
        
        return self.validate_signals(signals)
    
    def _evaluate_canslim_criteria(self, company_data: pd.Series) -> Dict[str, float]:
        """CAN SLIM 7가지 기준 평가"""
        scores = {}
        
        # C - Current Earnings (현재 분기 수익)
        current_eps_growth = company_data.get('eps_growth_current', 0)
        if current_eps_growth >= 0.5:  # 50% 이상
            scores['current_earnings'] = 1.0
        elif current_eps_growth >= 0.25:  # 25% 이상
            scores['current_earnings'] = 0.8
        elif current_eps_growth >= 0.1:   # 10% 이상
            scores['current_earnings'] = 0.6
        else:
            scores['current_earnings'] = 0.2
        
        # A - Annual Earnings (연간 수익 증가)
        annual_eps_growth = company_data.get('eps_growth_annual', 0)
        if annual_eps_growth >= 0.25:  # 25% 이상
            scores['annual_earnings'] = 1.0
        elif annual_eps_growth >= 0.15:  # 15% 이상
            scores['annual_earnings'] = 0.8
        else:
            scores['annual_earnings'] = 0.4
        
        # N - New (신제품, 신경영, 신고점)
        new_score = 0
        if company_data.get('new_products', False):
            new_score += 0.4
        if company_data.get('new_management', False):
            new_score += 0.3
        # 52주 신고점 근처
        price_vs_high = company_data.get('price_52w_high', 0)
        if price_vs_high >= 0.85:  # 52주 고점의 85% 이상
            new_score += 0.3
        scores['new_factors'] = min(1.0, new_score)
        
        # S - Supply and Demand (수급)
        supply_demand = company_data.get('supply_demand', 0.5)
        scores['supply_demand'] = supply_demand
        
        # L - Leader (업종 선도주)
        leading_stock = company_data.get('leading_stock', False)
        industry_rank = company_data.get('industry_rank', 50)
        if leading_stock and industry_rank <= 10:
            scores['leader'] = 1.0
        elif industry_rank <= 20:
            scores['leader'] = 0.8
        elif industry_rank <= 40:
            scores['leader'] = 0.6
        else:
            scores['leader'] = 0.3
        
        # I - Institutional Sponsorship (기관 후원)
        institutional_ownership = company_data.get('institutional_ownership', 0)
        if institutional_ownership >= 0.2:  # 20% 이상
            scores['institutional'] = 1.0
        elif institutional_ownership >= 0.1:  # 10% 이상
            scores['institutional'] = 0.7
        else:
            scores['institutional'] = 0.4
        
        # M - Market Direction (시장 방향)
        market_direction = company_data.get('market_direction', 0.5)
        scores['market_direction'] = market_direction
        
        return scores
    
    def _evaluate_technical_breakout(self, company_data: pd.Series) -> float:
        """기술적 돌파 패턴 평가"""
        technical_score = 0.0
        
        # 상대강도 (RS Rating)
        relative_strength = company_data.get('relative_strength', 50)
        if relative_strength >= 90:
            technical_score += 0.4
        elif relative_strength >= 80:
            technical_score += 0.3
        elif relative_strength >= 70:
            technical_score += 0.2
        
        # 52주 고점 근처
        price_vs_high = company_data.get('price_52w_high', 0)
        if price_vs_high >= 0.95:  # 95% 이상
            technical_score += 0.3
        elif price_vs_high >= 0.85:  # 85% 이상
            technical_score += 0.2
        
        # 거래량 증가 (간접 지표)
        volume_score = company_data.get('volume_increase', 0.5)
        technical_score += volume_score * 0.3
        
        return min(1.0, technical_score)
    
    def calculate_weights(self, signals: List[Signal], 
                         current_portfolio: Optional[Dict[str, float]] = None) -> List[PortfolioWeight]:
        if not signals:
            return []
        
        # 성장주 집중 투자 스타일
        # 상위 성과 종목에 더 높은 가중치
        signals_sorted = sorted(signals, key=lambda x: x.strength, reverse=True)
        top_signals = signals_sorted[:min(8, len(signals_sorted))]  # 최대 8개 종목 집중
        
        weights = []
        total_strength = sum(signal.strength for signal in top_signals)
        
        for i, signal in enumerate(top_signals):
            # 상위 종목일수록 높은 가중치
            position_bonus = 1.3 if i < 3 else 1.0
            adjusted_strength = signal.strength * position_bonus
            weight = adjusted_strength / (total_strength * 1.1)
            
            current_weight = current_portfolio.get(signal.symbol, 0.0) if current_portfolio else 0.0
            
            weights.append(PortfolioWeight(
                symbol=signal.symbol,
                weight=weight,
                target_weight=weight,
                current_weight=current_weight
            ))
        
        return self.apply_position_sizing(weights)

# 16. 하워드 막스의 사이클 투자 전략 (성장/모멘텀 버전)
class HowardMarksCycleStrategy(BaseStrategy):
    """하워드 막스의 사이클 투자 전략"""
    
    def __init__(self, **kwargs):
        super().__init__("Howard_Marks_Cycle_Strategy", **kwargs)
    
    def _get_metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            name="하워드 막스의 사이클 투자",
            description="경기사이클 극단점에서 역발상 기회 포착",
            category=StrategyCategory.ADVANCED,
            risk_level=RiskLevel.MEDIUM,
            complexity=Complexity.COMPLEX,
            expected_return="13-18%",
            volatility="16-24%",
            min_investment_period="2년 이상",
            rebalancing_frequency="분기별"
        )
    
    def _get_required_data_columns(self) -> List[str]:
        return super()._get_required_data_columns() + [
            'credit_spread', 'vix', 'yield_curve', 'sentiment_index', 
            'valuation_percentile', 'cycle_position', 'fear_greed_index'
        ]
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        signals = []
        
        # 시장 사이클 분석
        market_cycle_score = self._analyze_market_cycle(data)
        
        # 극단적 상황에서만 매매 (막스의 철학)
        if abs(market_cycle_score) < 0.7:  # 중립 구간에서는 거래하지 않음
            return []
        
        cycle_data = data.dropna(subset=['valuation_percentile'])
        
        for symbol in cycle_data.index:
            company_data = cycle_data.loc[symbol]
            
            # 개별 종목의 사이클 위치 분석
            stock_cycle_score = self._analyze_stock_cycle(company_data)
            
            # 시장 사이클과 개별 종목 사이클의 조합
            combined_score = (market_cycle_score + stock_cycle_score) / 2
            
            # 극단적 저평가 상황 (매수 기회)
            if combined_score <= -0.7:
                strength = abs(combined_score)
                confidence = min(0.9, abs(combined_score) + 0.1)
                
                signals.append(Signal(
                    symbol=symbol,
                    timestamp=pd.Timestamp.now(),
                    signal_type='BUY',
                    strength=strength,
                    confidence=confidence,
                    metadata={
                        'market_cycle_score': market_cycle_score,
                        'stock_cycle_score': stock_cycle_score,
                        'combined_score': combined_score,
                        'valuation_percentile': company_data['valuation_percentile']
                    }
                ))
            
            # 극단적 고평가 상황 (매도 신호)
            elif combined_score >= 0.7:
                strength = combined_score
                
                signals.append(Signal(
                    symbol=symbol,
                    timestamp=pd.Timestamp.now(),
                    signal_type='SELL',
                    strength=strength,
                    confidence=0.8,
                    metadata={
                        'market_cycle_score': market_cycle_score,
                        'stock_cycle_score': stock_cycle_score,
                        'combined_score': combined_score
                    }
                ))
        
        return self.validate_signals(signals)
    
    def _analyze_market_cycle(self, data: pd.DataFrame) -> float:
        """전체 시장 사이클 분석"""
        cycle_indicators = []
        
        # 신용 스프레드 (위험 지표)
        avg_credit_spread = data['credit_spread'].mean()
        if avg_credit_spread > 300:  # 3% 이상
            cycle_indicators.append(-0.8)  # 매우 부정적
        elif avg_credit_spread > 200:  # 2% 이상
            cycle_indicators.append(-0.5)
        elif avg_credit_spread < 100:  # 1% 이하
            cycle_indicators.append(0.6)   # 과도한 낙관
        else:
            cycle_indicators.append(0.0)
        
        # VIX (공포 지수)
        avg_vix = data['vix'].mean()
        if avg_vix > 30:
            cycle_indicators.append(-0.7)  # 극단적 공포
        elif avg_vix > 20:
            cycle_indicators.append(-0.3)
        elif avg_vix < 15:
            cycle_indicators.append(0.5)   # 과도한 안정감
        else:
            cycle_indicators.append(0.0)
        
        # 투자 심리
        avg_sentiment = data['sentiment_index'].mean()
        if avg_sentiment < 20:
            cycle_indicators.append(-0.8)  # 극단적 비관
        elif avg_sentiment < 40:
            cycle_indicators.append(-0.4)
        elif avg_sentiment > 80:
            cycle_indicators.append(0.7)   # 극단적 낙관
        else:
            cycle_indicators.append(0.0)
        
        return np.mean(cycle_indicators)
    
    def _analyze_stock_cycle(self, company_data: pd.Series) -> float:
        """개별 종목 사이클 분석"""
        stock_score = 0.0
        
        # 밸류에이션 백분위
        val_percentile = company_data['valuation_percentile']
        if val_percentile < 10:  # 하위 10%
            stock_score -= 0.8
        elif val_percentile < 25:  # 하위 25%
            stock_score -= 0.5
        elif val_percentile > 90:  # 상위 10%
            stock_score += 0.7
        elif val_percentile > 75:  # 상위 25%
            stock_score += 0.4
        
        # 사이클 위치
        cycle_position = company_data.get('cycle_position', 0.5)
        if cycle_position < 0.2:  # 사이클 바닥
            stock_score -= 0.6
        elif cycle_position > 0.8:  # 사이클 고점
            stock_score += 0.6
        
        return np.clip(stock_score, -1.0, 1.0)
    
    def calculate_weights(self, signals: List[Signal], 
                         current_portfolio: Optional[Dict[str, float]] = None) -> List[PortfolioWeight]:
        buy_signals = [s for s in signals if s.signal_type == 'BUY']
        if not buy_signals:
            return []
        
        # 사이클 투자는 기회주의적 집중
        weights = []
        total_strength = sum(signal.strength for signal in buy_signals)
        
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

# 17. 제임스 오쇼네시의 What Works on Wall Street 전략
class JamesOShaughnessyStrategy(BaseStrategy):
    """제임스 오쇼네시의 What Works on Wall Street 전략"""
    
    def __init__(self, **kwargs):
        super().__init__("James_OShaughnessy_Strategy", **kwargs)
    
    def _get_metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            name="제임스 오쇼네시의 What Works",
            description="50년 데이터 검증, 시총+PBR+모멘텀 멀티팩터",
            category=StrategyCategory.ADVANCED,
            risk_level=RiskLevel.MEDIUM,
            complexity=Complexity.MEDIUM,
            expected_return="14-19%",
            volatility="17-23%",
            min_investment_period="1년 이상",
            rebalancing_frequency="연 1회"
        )
    
    def _get_required_data_columns(self) -> List[str]:
        return super()._get_required_data_columns() + [
            'market_cap', 'pb_ratio', 'momentum_1year', 'price_sales', 
            'shareholder_yield', 'roe', 'earnings_quality'
        ]
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        signals = []
        
        # 오쇼네시의 최적 조합: 대형주 + 저PBR + 모멘텀
        market_cap_threshold = self.parameters.get('market_cap_percentile', 0.5)  # 상위 50%
        pbr_threshold = self.parameters.get('pbr_percentile', 0.25)  # 하위 25%
        momentum_threshold = self.parameters.get('momentum_percentile', 0.75)  # 상위 25%
        
        oshaughnessy_data = data.dropna(subset=['market_cap', 'pb_ratio', 'momentum_1year'])
        
        # 각 팩터별 기준선 계산
        market_cap_cutoff = oshaughnessy_data['market_cap'].quantile(market_cap_threshold)
        pbr_cutoff = oshaughnessy_data['pb_ratio'].quantile(pbr_threshold)
        momentum_cutoff = oshaughnessy_data['momentum_1year'].quantile(momentum_threshold)
        
        for symbol in oshaughnessy_data.index:
            company_data = oshaughnessy_data.loc[symbol]
            
            # 3가지 핵심 조건
            large_cap = company_data['market_cap'] >= market_cap_cutoff
            low_pbr = company_data['pb_ratio'] <= pbr_cutoff
            high_momentum = company_data['momentum_1year'] >= momentum_cutoff
            
            # 모든 조건 충족 시 기본 선별
            if large_cap and low_pbr and high_momentum:
                # 추가 품질 지표 평가
                quality_score = self._evaluate_quality_factors(company_data)
                
                if quality_score >= 0.5:
                    # 각 팩터의 상대적 순위 계산
                    factor_scores = self._calculate_factor_scores(company_data, oshaughnessy_data)
                    
                    # 종합 점수
                    composite_score = (
                        factor_scores['size_score'] * 0.3 +
                        factor_scores['value_score'] * 0.4 +
                        factor_scores['momentum_score'] * 0.3
                    )
                    
                    final_strength = min(1.0, composite_score * quality_score * 1.1)
                    
                    signals.append(Signal(
                        symbol=symbol,
                        timestamp=pd.Timestamp.now(),
                        signal_type='BUY',
                        strength=final_strength,
                        confidence=0.8,
                        metadata={
                            'composite_score': composite_score,
                            'quality_score': quality_score,
                            'size_score': factor_scores['size_score'],
                            'value_score': factor_scores['value_score'],
                            'momentum_score': factor_scores['momentum_score'],
                            'market_cap': company_data['market_cap'],
                            'pb_ratio': company_data['pb_ratio'],
                            'momentum_1year': company_data['momentum_1year']
                        }
                    ))
        
        return self.validate_signals(signals)
    
    def _evaluate_quality_factors(self, company_data: pd.Series) -> float:
        """품질 팩터 평가"""
        quality_score = 0.0
        
        # ROE
        roe = company_data.get('roe', 0.1)
        if roe > 0.15:
            quality_score += 0.3
        elif roe > 0.1:
            quality_score += 0.2
        
        # 주주수익률 (배당 + 자사주 매입)
        shareholder_yield = company_data.get('shareholder_yield', 0.02)
        if shareholder_yield > 0.05:
            quality_score += 0.3
        elif shareholder_yield > 0.02:
            quality_score += 0.2
        
        # 수익 품질
        earnings_quality = company_data.get('earnings_quality', 0.7)
        quality_score += earnings_quality * 0.4
        
        return min(1.0, quality_score)
    
    def _calculate_factor_scores(self, company_data: pd.Series, universe_data: pd.DataFrame) -> Dict[str, float]:
        """팩터별 상대 점수 계산"""
        scores = {}
        
        # 시가총액 점수 (클수록 높은 점수)
        market_cap = company_data['market_cap']
        market_cap_rank = (universe_data['market_cap'] <= market_cap).mean()
        scores['size_score'] = market_cap_rank
        
        # 가치 점수 (PBR 낮을수록 높은 점수)
        pb_ratio = company_data['pb_ratio']
        pbr_rank = 1 - (universe_data['pb_ratio'] <= pb_ratio).mean()
        scores['value_score'] = pbr_rank
        
        # 모멘텀 점수 (높을수록 높은 점수)
        momentum = company_data['momentum_1year']
        momentum_rank = (universe_data['momentum_1year'] <= momentum).mean()
        scores['momentum_score'] = momentum_rank
        
        return scores
    
    def calculate_weights(self, signals: List[Signal], 
                         current_portfolio: Optional[Dict[str, float]] = None) -> List[PortfolioWeight]:
        if not signals:
            return []
        
        # 팩터 점수 기반 가중치
        weights = []
        total_strength = sum(signal.strength for signal in signals)
        
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

# 전략 팩토리에 등록
def register_growth_momentum_strategies():
    """성장/모멘텀 전략들을 팩토리에 등록"""
    StrategyFactory.register_strategy("william_oneil_canslim", WilliamONeilCANSLIMStrategy)
    StrategyFactory.register_strategy("howard_marks_cycle", HowardMarksCycleStrategy)
    StrategyFactory.register_strategy("james_oshaughnessy", JamesOShaughnessyStrategy)

# 모듈 로드 시 자동 등록
register_growth_momentum_strategies()