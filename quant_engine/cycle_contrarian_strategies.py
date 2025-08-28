"""
file: strategy_engine/cycle_contrarian_strategies.py
Cycle & Contrarian Strategies - 사이클/역발상 관련 고급 전략 3가지
레이 달리오의 올웨더, 데이비드 드레먼의 역발상, 존 네프의 저PER+배당 전략
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from base_strategy import BaseStrategy, StrategyMetadata, Signal, PortfolioWeight
from base_strategy import RiskLevel, Complexity, StrategyCategory, StrategyFactory
import technical_indicators as ti
import fundamental_metrics as fm

# 18. 레이 달리오의 올웨더 포트폴리오
class RayDalioAllWeatherStrategy(BaseStrategy):
    """레이 달리오의 올웨더 포트폴리오 전략"""
    
    def __init__(self, **kwargs):
        super().__init__("Ray_Dalio_All_Weather_Strategy", **kwargs)
    
    def _get_metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            name="레이 달리오의 올웨더 포트폴리오",
            description="경제 환경 변화에 관계없이 안정적 수익 추구",
            category=StrategyCategory.ADVANCED,
            risk_level=RiskLevel.LOW,
            complexity=Complexity.MEDIUM,
            expected_return="8-12%",
            volatility="8-12%",
            min_investment_period="5년 이상",
            rebalancing_frequency="분기별"
        )
    
    def _get_required_data_columns(self) -> List[str]:
        return super()._get_required_data_columns() + [
            'asset_class', 'duration', 'correlation_matrix', 'volatility', 
            'inflation_sensitivity', 'growth_sensitivity'
        ]
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """올웨더는 고정 배분이므로 리밸런싱 신호만 생성"""
        signals = []
        
        # 기본 올웨더 배분
        target_allocation = self.parameters.get('target_allocation', {
            'stocks': 0.30,
            'long_term_bonds': 0.40,
            'intermediate_bonds': 0.15,
            'commodities': 0.075,
            'tips': 0.075  # Treasury Inflation-Protected Securities
        })
        
        current_allocation = self.parameters.get('current_allocation', {})
        rebalance_threshold = self.parameters.get('rebalance_threshold', 0.05)
        
        # 각 자산군별 리밸런싱 필요성 확인
        for asset_class, target_weight in target_allocation.items():
            current_weight = current_allocation.get(asset_class, 0.0)
            weight_diff = target_weight - current_weight
            
            if abs(weight_diff) > rebalance_threshold:
                # 리밸런싱 강도는 편차 크기에 비례
                strength = min(1.0, abs(weight_diff) / rebalance_threshold)
                
                signal_type = 'BUY' if weight_diff > 0 else 'SELL'
                
                # 자산군별 대표 종목들 찾기
                asset_symbols = self._get_asset_class_symbols(data, asset_class)
                
                for symbol in asset_symbols:
                    signals.append(Signal(
                        symbol=symbol,
                        timestamp=pd.Timestamp.now(),
                        signal_type=signal_type,
                        strength=strength,
                        confidence=0.95,  # 올웨더는 확신도 높음
                        metadata={
                            'asset_class': asset_class,
                            'target_weight': target_weight,
                            'current_weight': current_weight,
                            'weight_diff': weight_diff,
                            'rebalancing_reason': 'all_weather_allocation'
                        }
                    ))
        
        return self.validate_signals(signals)
    
    def _get_asset_class_symbols(self, data: pd.DataFrame, asset_class: str) -> List[str]:
        """자산군별 해당 종목들 반환"""
        if 'asset_class' not in data.columns:
            # 기본 매핑 사용
            asset_mapping = {
                'stocks': ['SPY', 'VTI', 'ITOT'],
                'long_term_bonds': ['TLT', 'VGLT'],
                'intermediate_bonds': ['IEF', 'VGIT'],
                'commodities': ['DJP', 'PDBC', 'BCI'],
                'tips': ['TIPS', 'VTIP', 'SCHP']
            }
            return asset_mapping.get(asset_class, [])
        
        # 데이터에서 해당 자산군 종목들 찾기
        asset_symbols = data[data['asset_class'] == asset_class].index.tolist()
        return asset_symbols[:3]  # 최대 3개까지
    
    def calculate_weights(self, signals: List[Signal], 
                         current_portfolio: Optional[Dict[str, float]] = None) -> List[PortfolioWeight]:
        
        target_allocation = self.parameters.get('target_allocation', {
            'stocks': 0.30,
            'long_term_bonds': 0.40,
            'intermediate_bonds': 0.15,
            'commodities': 0.075,
            'tips': 0.075
        })
        
        weights = []
        
        # 각 자산군 내에서 동일 가중치 배분
        asset_weights = {}
        for signal in signals:
            asset_class = signal.metadata.get('asset_class')
            if asset_class not in asset_weights:
                asset_weights[asset_class] = []
            asset_weights[asset_class].append(signal.symbol)
        
        for asset_class, symbols in asset_weights.items():
            target_asset_weight = target_allocation.get(asset_class, 0.0)
            weight_per_symbol = target_asset_weight / len(symbols)
            
            for symbol in symbols:
                current_weight = current_portfolio.get(symbol, 0.0) if current_portfolio else 0.0
                
                weights.append(PortfolioWeight(
                    symbol=symbol,
                    weight=weight_per_symbol,
                    target_weight=weight_per_symbol,
                    current_weight=current_weight,
                    rebalance_needed=abs(weight_per_symbol - current_weight) > 0.01
                ))
        
        return weights

# 19. 데이비드 드레먼의 역발상 투자
class DavidDremanContrarianStrategy(BaseStrategy):
    """데이비드 드레먼의 역발상 투자 전략"""
    
    def __init__(self, **kwargs):
        super().__init__("David_Dreman_Contrarian_Strategy", **kwargs)
    
    def _get_metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            name="데이비드 드레먼의 역발상 투자",
            description="시장 공포와 비관론 속에서 저평가 기회 발굴",
            category=StrategyCategory.ADVANCED,
            risk_level=RiskLevel.MEDIUM,
            complexity=Complexity.MEDIUM,
            expected_return="12-16%",
            volatility="16-22%",
            min_investment_period="2년 이상",
            rebalancing_frequency="분기별"
        )
    
    def _get_required_data_columns(self) -> List[str]:
        return super()._get_required_data_columns() + [
            'pe_ratio', 'pb_ratio', 'sentiment_score', 'analyst_coverage',
            'news_sentiment', 'price_momentum_3m', 'earnings_surprise',
            'analyst_revisions', 'short_interest'
        ]
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        signals = []
        
        # 드레먼의 역발상 기준
        max_pe_percentile = self.parameters.get('max_pe_percentile', 0.2)  # 하위 20%
        fear_threshold = self.parameters.get('fear_threshold', -0.6)  # 부정적 감정
        min_market_cap = self.parameters.get('min_market_cap', 1000)  # 10억 달러
        
        contrarian_data = data.dropna(subset=['pe_ratio', 'pb_ratio'])
        
        # 시장 전체 공포 수준 확인
        market_fear_score = self._calculate_market_fear_level(contrarian_data)
        
        # 시장이 충분히 비관적이지 않으면 대기
        if market_fear_score > -0.5:
            return []
        
        # PE 기준선 계산 (하위 percentile)
        pe_threshold = contrarian_data['pe_ratio'].quantile(max_pe_percentile)
        
        for symbol in contrarian_data.index:
            company_data = contrarian_data.loc[symbol]
            
            # 기본 저평가 조건
            pe_ratio = company_data['pe_ratio']
            pb_ratio = company_data['pb_ratio']
            market_cap = company_data.get('market_cap', 0)
            
            basic_value_conditions = [
                0 < pe_ratio <= pe_threshold,
                0 < pb_ratio <= 2.0,
                market_cap >= min_market_cap
            ]
            
            if not all(basic_value_conditions):
                continue
            
            # 역발상 신호 평가
            contrarian_score = self._evaluate_contrarian_signals(company_data)
            
            if contrarian_score >= 0.6:  # 충분한 역발상 신호
                # 가치 + 역발상 종합 점수
                value_score = self._calculate_value_score(company_data, contrarian_data)
                final_strength = min(1.0, contrarian_score * value_score * 1.2)
                
                confidence = min(0.9, 0.6 + abs(market_fear_score) * 0.3)
                
                signals.append(Signal(
                    symbol=symbol,
                    timestamp=pd.Timestamp.now(),
                    signal_type='BUY',
                    strength=final_strength,
                    confidence=confidence,
                    metadata={
                        'contrarian_score': contrarian_score,
                        'value_score': value_score,
                        'market_fear_score': market_fear_score,
                        'pe_ratio': pe_ratio,
                        'pb_ratio': pb_ratio
                    }
                ))
        
        return self.validate_signals(signals)
    
    def _calculate_market_fear_level(self, data: pd.DataFrame) -> float:
        """시장 전체 공포 수준 계산"""
        fear_indicators = []
        
        # VIX 수준 (있다면)
        if 'vix' in data.columns:
            avg_vix = data['vix'].mean()
            if avg_vix > 30:
                fear_indicators.append(-0.8)
            elif avg_vix > 25:
                fear_indicators.append(-0.5)
            else:
                fear_indicators.append(0.2)
        
        # 전체 시장 심리
        if 'sentiment_score' in data.columns:
            avg_sentiment = data['sentiment_score'].mean()
            fear_indicators.append(avg_sentiment)
        
        # 뉴스 심리
        if 'news_sentiment' in data.columns:
            avg_news_sentiment = data['news_sentiment'].mean()
            fear_indicators.append(avg_news_sentiment)
        
        # 단기 모멘텀 (하락이 클수록 공포)
        if 'price_momentum_3m' in data.columns:
            avg_momentum = data['price_momentum_3m'].mean()
            if avg_momentum < -0.2:  # 20% 하락
                fear_indicators.append(-0.9)
            elif avg_momentum < -0.1:  # 10% 하락
                fear_indicators.append(-0.6)
            else:
                fear_indicators.append(0.0)
        
        return np.mean(fear_indicators) if fear_indicators else 0.0
    
    def _evaluate_contrarian_signals(self, company_data: pd.Series) -> float:
        """개별 종목의 역발상 신호 평가"""
        contrarian_score = 0.0
        
        # 부정적 감정
        sentiment = company_data.get('sentiment_score', 0.0)
        if sentiment <= -0.7:
            contrarian_score += 0.3
        elif sentiment <= -0.4:
            contrarian_score += 0.2
        
        # 애널리스트 커버리지 감소 (관심 저하)
        analyst_coverage = company_data.get('analyst_coverage', 10)
        if analyst_coverage <= 5:
            contrarian_score += 0.2
        
        # 애널리스트 하향 조정
        analyst_revisions = company_data.get('analyst_revisions', 0.0)
        if analyst_revisions < -0.3:  # 30% 하향
            contrarian_score += 0.25
        
        # 공매도 비율 높음 (비관론)
        short_interest = company_data.get('short_interest', 0.05)
        if short_interest > 0.15:  # 15% 이상
            contrarian_score += 0.25
        
        return min(1.0, contrarian_score)
    
    def _calculate_value_score(self, company_data: pd.Series, universe_data: pd.DataFrame) -> float:
        """가치 평가 점수"""
        value_score = 0.0
        
        # PE 상대 순위 (낮을수록 좋음)
        pe_ratio = company_data['pe_ratio']
        pe_rank = 1 - (universe_data['pe_ratio'] <= pe_ratio).mean()
        value_score += pe_rank * 0.5
        
        # PB 상대 순위
        pb_ratio = company_data['pb_ratio']
        pb_rank = 1 - (universe_data['pb_ratio'] <= pb_ratio).mean()
        value_score += pb_rank * 0.3
        
        # 어닝 서프라이즈 보너스
        earnings_surprise = company_data.get('earnings_surprise', 0.0)
        if earnings_surprise > 0.1:  # 10% 서프라이즈
            value_score += 0.2
        
        return min(1.0, value_score)
    
    def calculate_weights(self, signals: List[Signal], 
                         current_portfolio: Optional[Dict[str, float]] = None) -> List[PortfolioWeight]:
        if not signals:
            return []
        
        # 역발상 강도 기반 가중치
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

# 20. 존 네프의 저PER + 배당 전략
class JohnNeffLowPEDividendStrategy(BaseStrategy):
    """존 네프의 저PER + 배당 전략"""
    
    def __init__(self, **kwargs):
        super().__init__("John_Neff_Low_PE_Dividend_Strategy", **kwargs)
    
    def _get_metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            name="존 네프의 저PER + 배당 전략",
            description="소외받는 업종에서 저PER + 고배당 보석 발굴",
            category=StrategyCategory.ADVANCED,
            risk_level=RiskLevel.MEDIUM,
            complexity=Complexity.MEDIUM,
            expected_return="11-15%",
            volatility="14-18%",
            min_investment_period="3년 이상",
            rebalancing_frequency="반기별"
        )
    
    def _get_required_data_columns(self) -> List[str]:
        return super()._get_required_data_columns() + [
            'pe_ratio', 'dividend_yield', 'earnings_growth_rate', 
            'total_return_potential', 'industry_popularity', 'peg_ratio'
        ]
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        signals = []
        
        # 네프의 기본 기준
        market_pe_discount = self.parameters.get('market_pe_discount', 0.6)  # 시장 PE의 60%
        min_dividend_yield = self.parameters.get('min_dividend_yield', 0.03)  # 3%
        target_total_return = self.parameters.get('target_total_return', 0.12)  # 12%
        max_peg = self.parameters.get('max_peg', 0.5)  # PEG 0.5 이하
        
        neff_data = data.dropna(subset=['pe_ratio', 'dividend_yield'])
        
        if len(neff_data) == 0:
            return []
        
        # 시장 평균 PE 계산
        market_pe = neff_data['pe_ratio'].median()
        target_pe_threshold = market_pe * market_pe_discount
        
        for symbol in neff_data.index:
            company_data = neff_data.loc[symbol]
            
            pe_ratio = company_data['pe_ratio']
            dividend_yield = company_data['dividend_yield']
            
            # 기본 조건 확인
            basic_conditions = [
                0 < pe_ratio <= target_pe_threshold,
                dividend_yield >= min_dividend_yield
            ]
            
            if not all(basic_conditions):
                continue
            
            # 네프의 총수익률 공식 평가
            total_return_score = self._calculate_neff_total_return(company_data)
            
            if total_return_score >= target_total_return:
                # 소외 업종 보너스
                neglected_bonus = self._evaluate_neglected_sector(company_data)
                
                # PEG 비율 확인
                peg_ratio = company_data.get('peg_ratio', 1.0)
                peg_bonus = 1.0 if peg_ratio <= max_peg else 0.7
                
                # 최종 강도 계산
                base_strength = min(1.0, total_return_score / target_total_return)
                final_strength = base_strength * neglected_bonus * peg_bonus
                
                signals.append(Signal(
                    symbol=symbol,
                    timestamp=pd.Timestamp.now(),
                    signal_type='BUY',
                    strength=final_strength,
                    confidence=0.8,
                    metadata={
                        'total_return_score': total_return_score,
                        'neglected_bonus': neglected_bonus,
                        'peg_bonus': peg_bonus,
                        'pe_ratio': pe_ratio,
                        'dividend_yield': dividend_yield,
                        'peg_ratio': peg_ratio,
                        'market_pe': market_pe
                    }
                ))
        
        return self.validate_signals(signals)
    
    def _calculate_neff_total_return(self, company_data: pd.Series) -> float:
        """네프의 총수익률 계산법"""
        # 총수익률 = 배당수익률 + 예상 주가상승률
        dividend_yield = company_data['dividend_yield']
        
        # 예상 주가상승률 추정
        earnings_growth = company_data.get('earnings_growth_rate', 0.05)
        pe_ratio = company_data['pe_ratio']
        
        # 간단한 주가상승률 추정: 수익 성장률 + PE 정상화 기대
        # PE가 낮으면 PE 확장 가능성
        normal_pe = 15  # 정상 PE 가정
        pe_expansion_potential = max(0, (normal_pe - pe_ratio) / pe_ratio * 0.3)  # 30% 반영
        
        expected_price_appreciation = earnings_growth + pe_expansion_potential
        total_return = dividend_yield + expected_price_appreciation
        
        return total_return
    
    def _evaluate_neglected_sector(self, company_data: pd.Series) -> float:
        """소외받는 업종/종목 평가"""
        neglected_score = 1.0  # 기본값
        
        # 업종 인기도 (낮을수록 좋음)
        industry_popularity = company_data.get('industry_popularity', 0.5)
        if industry_popularity <= 0.3:  # 하위 30%
            neglected_score *= 1.2
        elif industry_popularity <= 0.5:  # 하위 50%
            neglected_score *= 1.1
        
        return min(1.3, neglected_score)  # 최대 30% 보너스
    
    def calculate_weights(self, signals: List[Signal], 
                         current_portfolio: Optional[Dict[str, float]] = None) -> List[PortfolioWeight]:
        if not signals:
            return []
        
        # 총수익률 기대치 기반 가중치
        weights = []
        total_return_sum = sum(signal.metadata.get('total_return_score', 0.12) for signal in signals)
        
        for signal in signals:
            expected_return = signal.metadata.get('total_return_score', 0.12)
            weight = expected_return / total_return_sum
            current_weight = current_portfolio.get(signal.symbol, 0.0) if current_portfolio else 0.0
            
            weights.append(PortfolioWeight(
                symbol=signal.symbol,
                weight=weight,
                target_weight=weight,
                current_weight=current_weight
            ))
        
        return self.apply_position_sizing(weights)

# 전략 팩토리에 등록
def register_cycle_contrarian_strategies():
    """사이클/역발상 전략들을 팩토리에 등록"""
    StrategyFactory.register_strategy("ray_dalio_all_weather", RayDalioAllWeatherStrategy)
    StrategyFactory.register_strategy("david_dreman_contrarian", DavidDremanContrarianStrategy)
    StrategyFactory.register_strategy("john_neff_low_pe_dividend", JohnNeffLowPEDividendStrategy)

# 모듈 로드 시 자동 등록
register_cycle_contrarian_strategies()
