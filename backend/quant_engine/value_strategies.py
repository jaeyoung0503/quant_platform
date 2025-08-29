"""
file: strategy_engine/value_strategies.py
Value Investment Strategies - 가치투자 관련 고급 전략 4가지
워렌 버핏, 벤저민 그레이엄, 존 네프, 조엘 그린블라트의 전략들
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from base_strategy import BaseStrategy, StrategyMetadata, Signal, PortfolioWeight
from base_strategy import RiskLevel, Complexity, StrategyCategory, StrategyFactory
import fundamental_metrics as fm

# 11. 워렌 버핏의 해자 전략
class BuffettMoatStrategy(BaseStrategy):
    """워렌 버핏의 경제적 해자 전략"""
    
    def __init__(self, **kwargs):
        super().__init__("Buffett_Moat_Strategy", **kwargs)
    
    def _get_metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            name="워렌 버핏의 해자 전략",
            description="경쟁우위가 있는 기업을 합리적 가격에 장기 보유",
            category=StrategyCategory.ADVANCED,
            risk_level=RiskLevel.LOW,
            complexity=Complexity.MEDIUM,
            expected_return="12-16%",
            volatility="10-15%",
            min_investment_period="10년 이상",
            rebalancing_frequency="연 1회"
        )
    
    def _get_required_data_columns(self) -> List[str]:
        return super()._get_required_data_columns() + [
            'pe_ratio', 'roe', 'roic', 'debt_to_equity', 'profit_margin', 
            'revenue_growth_5y', 'earnings_growth_5y', 'brand_strength', 
            'market_share', 'switching_cost'
        ]
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        signals = []
        
        # 버핏 기준 파라미터
        max_pe = self.parameters.get('max_pe', 20)
        min_roe = self.parameters.get('min_roe', 0.15)
        min_roic = self.parameters.get('min_roic', 0.12)
        max_debt_equity = self.parameters.get('max_debt_equity', 0.5)
        min_profit_margin = self.parameters.get('min_profit_margin', 0.1)
        min_revenue_growth = self.parameters.get('min_revenue_growth', 0.05)
        
        moat_data = data.dropna(subset=['pe_ratio', 'roe', 'roic'])
        
        for symbol in moat_data.index:
            # 기본 재무 지표 확인
            pe_ratio = moat_data.loc[symbol, 'pe_ratio']
            roe = moat_data.loc[symbol, 'roe']
            roic = moat_data.loc[symbol, 'roic']
            debt_equity = moat_data.loc[symbol, 'debt_to_equity']
            profit_margin = moat_data.loc[symbol, 'profit_margin']
            
            # 버핏의 기본 조건 검증
            basic_conditions = [
                0 < pe_ratio <= max_pe,
                roe >= min_roe,
                roic >= min_roic,
                debt_equity <= max_debt_equity,
                profit_margin >= min_profit_margin
            ]
            
            if not all(basic_conditions):
                continue
            
            # 경제적 해자 평가
            moat_score = self._evaluate_economic_moat(moat_data.loc[symbol])
            
            if moat_score >= 0.6:  # 해자 점수 60% 이상
                # 내재가치 대비 할인 정도 계산
                intrinsic_value = self._calculate_intrinsic_value(moat_data.loc[symbol])
                current_price = moat_data.loc[symbol, 'close']
                discount = (intrinsic_value - current_price) / intrinsic_value
                
                # 안전마진 20% 이상일 때만 매수
                if discount >= 0.2:
                    strength = min(1.0, moat_score * discount * 2)
                    
                    signals.append(Signal(
                        symbol=symbol,
                        timestamp=pd.Timestamp.now(),
                        signal_type='BUY',
                        strength=strength,
                        confidence=0.85,
                        metadata={
                            'moat_score': moat_score,
                            'intrinsic_value': intrinsic_value,
                            'current_price': current_price,
                            'discount': discount,
                            'pe_ratio': pe_ratio,
                            'roe': roe,
                            'roic': roic
                        }
                    ))
        
        return self.validate_signals(signals)
    
    def _evaluate_economic_moat(self, company_data: pd.Series) -> float:
        """경제적 해자 평가"""
        moat_score = 0.0
        
        # 브랜드 파워 (25%)
        brand_strength = company_data.get('brand_strength', 0.5)
        moat_score += brand_strength * 0.25
        
        # 시장 지배력 (25%)
        market_share = company_data.get('market_share', 0.3)
        if market_share > 0.3:  # 시장 점유율 30% 이상
            moat_score += min(1.0, market_share) * 0.25
        
        # 전환 비용 (20%)
        switching_cost = company_data.get('switching_cost', 0.5)
        moat_score += switching_cost * 0.2
        
        # 지속적 수익성 (15%)
        roe_consistency = self._calculate_roe_consistency(company_data)
        moat_score += roe_consistency * 0.15
        
        # 재투자 효율성 (15%)
        roic = company_data.get('roic', 0.1)
        if roic > 0.15:
            reinvestment_score = min(1.0, roic / 0.3)
            moat_score += reinvestment_score * 0.15
        
        return min(1.0, moat_score)
    
    def _calculate_roe_consistency(self, company_data: pd.Series) -> float:
        """ROE 일관성 평가"""
        # 간단화: ROE가 15% 이상이고 안정적이면 높은 점수
        roe = company_data.get('roe', 0)
        if roe >= 0.15:
            return 1.0
        elif roe >= 0.1:
            return 0.6
        else:
            return 0.2
    
    def _calculate_intrinsic_value(self, company_data: pd.Series) -> float:
        """간단한 내재가치 계산 (DCF 모형 단순화)"""
        # 현재 수익을 기반으로 한 추정
        current_price = company_data.get('close', 100)
        pe_ratio = company_data.get('pe_ratio', 15)
        earnings_per_share = current_price / pe_ratio
        
        # 성장률 추정
        earnings_growth = company_data.get('earnings_growth_5y', 0.08)
        discount_rate = 0.1  # 10% 할인율
        
        # 10년 DCF 단순 계산
        intrinsic_value = 0
        for year in range(1, 11):
            future_earnings = earnings_per_share * (1 + earnings_growth) ** year
            present_value = future_earnings / (1 + discount_rate) ** year
            intrinsic_value += present_value
        
        # 터미널 가치 (단순화)
        terminal_value = (earnings_per_share * (1 + earnings_growth) ** 10 * 15) / (1 + discount_rate) ** 10
        intrinsic_value += terminal_value
        
        return intrinsic_value
    
    def calculate_weights(self, signals: List[Signal], 
                         current_portfolio: Optional[Dict[str, float]] = None) -> List[PortfolioWeight]:
        if not signals:
            return []
        
        # 집중 투자 (버핏 스타일)
        # 상위 종목에 더 높은 가중치
        signals_sorted = sorted(signals, key=lambda x: x.strength, reverse=True)
        top_signals = signals_sorted[:min(10, len(signals_sorted))]  # 최대 10개 종목
        
        weights = []
        total_strength = sum(signal.strength for signal in top_signals)
        
        for i, signal in enumerate(top_signals):
            # 상위 종목일수록 더 높은 가중치 (집중도 증가)
            position_multiplier = 1.5 if i < 3 else 1.0  # 상위 3개 종목 가중치 증가
            adjusted_strength = signal.strength * position_multiplier
            weight = adjusted_strength / (total_strength * 1.2)  # 조정된 총합으로 나눔
            
            current_weight = current_portfolio.get(signal.symbol, 0.0) if current_portfolio else 0.0
            
            weights.append(PortfolioWeight(
                symbol=signal.symbol,
                weight=weight,
                target_weight=weight,
                current_weight=current_weight
            ))
        
        return self.apply_position_sizing(weights)

# 12. 피터 린치의 PEG 전략
class PeterLynchPEGStrategy(BaseStrategy):
    """피터 린치의 PEG 전략"""
    
    def __init__(self, **kwargs):
        super().__init__("Peter_Lynch_PEG_Strategy", **kwargs)
    
    def _get_metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            name="피터 린치의 PEG 전략",
            description="PEG 비율 1.0 이하 성장주 발굴, 10배 주식 추구",
            category=StrategyCategory.ADVANCED,
            risk_level=RiskLevel.MEDIUM,
            complexity=Complexity.MEDIUM,
            expected_return="13-18%",
            volatility="16-22%",
            min_investment_period="2년 이상",
            rebalancing_frequency="분기별"
        )
    
    def _get_required_data_columns(self) -> List[str]:
        return super()._get_required_data_columns() + [
            'pe_ratio', 'earnings_growth_rate', 'revenue_growth_rate', 
            'market_cap', 'industry_type', 'consumer_exposure'
        ]
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        signals = []
        
        max_peg = self.parameters.get('max_peg', 1.0)
        min_growth_rate = self.parameters.get('min_growth_rate', 0.1)  # 10%
        max_pe = self.parameters.get('max_pe', 30)
        
        peg_data = data.dropna(subset=['pe_ratio', 'earnings_growth_rate'])
        
        for symbol in peg_data.index:
            pe_ratio = peg_data.loc[symbol, 'pe_ratio']
            growth_rate = peg_data.loc[symbol, 'earnings_growth_rate']
            
            # PEG 계산
            if growth_rate <= 0:
                continue
            
            peg_ratio = pe_ratio / (growth_rate * 100)
            
            # 린치의 기본 조건
            conditions = [
                peg_ratio <= max_peg,
                growth_rate >= min_growth_rate,
                pe_ratio <= max_pe,
                pe_ratio > 0
            ]
            
            if not all(conditions):
                continue
            
            # 추가 린치 스타일 평가
            lynch_score = self._evaluate_lynch_criteria(peg_data.loc[symbol], peg_ratio)
            
            if lynch_score >= 0.5:
                # PEG가 낮을수록, 성장률이 높을수록 높은 강도
                growth_bonus = min(1.0, growth_rate / 0.3)  # 30% 성장을 최대로
                peg_bonus = max(0.1, (1.0 - peg_ratio))  # PEG가 낮을수록 높은 점수
                strength = min(1.0, lynch_score * growth_bonus * peg_bonus)
                
                signals.append(Signal(
                    symbol=symbol,
                    timestamp=pd.Timestamp.now(),
                    signal_type='BUY',
                    strength=strength,
                    confidence=0.75,
                    metadata={
                        'peg_ratio': peg_ratio,
                        'growth_rate': growth_rate,
                        'pe_ratio': pe_ratio,
                        'lynch_score': lynch_score
                    }
                ))
        
        return self.validate_signals(signals)
    
    def _evaluate_lynch_criteria(self, company_data: pd.Series, peg_ratio: float) -> float:
        """린치의 추가 평가 기준"""
        score = 0.0
        
        # 1. 이해하기 쉬운 사업 (소비자 노출도)
        consumer_exposure = company_data.get('consumer_exposure', 0.5)
        score += consumer_exposure * 0.3
        
        # 2. 적당한 크기 (너무 크지 않은 기업 선호)
        market_cap = company_data.get('market_cap', 5000)
        if 1000 <= market_cap <= 50000:  # 10억-500억 달러
            size_score = 1.0
        elif market_cap <= 100000:  # 1000억 달러 이하
            size_score = 0.7
        else:
            size_score = 0.3
        score += size_score * 0.2
        
        # 3. 매출 성장률 일관성
        revenue_growth = company_data.get('revenue_growth_rate', 0.05)
        if revenue_growth > 0.1:  # 10% 이상
            score += 0.3
        elif revenue_growth > 0.05:  # 5% 이상
            score += 0.2
        
        # 4. PEG 우수성 (0.5 이하면 보너스)
        if peg_ratio <= 0.5:
            score += 0.2
        
        return min(1.0, score)
    
    def calculate_weights(self, signals: List[Signal], 
                         current_portfolio: Optional[Dict[str, float]] = None) -> List[PortfolioWeight]:
        if not signals:
            return []
        
        # PEG와 성장률 기반 가중치 (성장주 스타일)
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

# 13. 벤저민 그레이엄의 방어적 투자
class BenjaminGrahamDefensiveStrategy(BaseStrategy):
    """벤저민 그레이엄의 방어적 투자자 전략"""
    
    def __init__(self, **kwargs):
        super().__init__("Benjamin_Graham_Defensive_Strategy", **kwargs)
    
    def _get_metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            name="벤저민 그레이엄의 방어적 투자",
            description="안전성과 수익성을 겸비한 보수적 가치투자",
            category=StrategyCategory.ADVANCED,
            risk_level=RiskLevel.LOW,
            complexity=Complexity.MEDIUM,
            expected_return="9-13%",
            volatility="10-16%",
            min_investment_period="3년 이상",
            rebalancing_frequency="연 1회"
        )
    
    def _get_required_data_columns(self) -> List[str]:
        return super()._get_required_data_columns() + [
            'pe_ratio', 'pb_ratio', 'current_ratio', 'debt_to_equity', 
            'dividend_yield', 'earnings_stability', 'dividend_years', 'market_cap'
        ]
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        signals = []
        
        # 그레이엄의 방어적 투자자 기준
        max_pe = self.parameters.get('max_pe', 15)
        max_pb = self.parameters.get('max_pb', 1.5)
        min_current_ratio = self.parameters.get('min_current_ratio', 2.0)
        max_debt_equity = self.parameters.get('max_debt_equity', 0.5)
        min_dividend_years = self.parameters.get('min_dividend_years', 3)
        min_market_cap_rank = self.parameters.get('min_market_cap_percentile', 0.7)  # 상위 30%
        
        graham_data = data.dropna(subset=['pe_ratio', 'pb_ratio', 'current_ratio'])
        
        # 시가총액 기준선 계산
        market_cap_threshold = graham_data['market_cap'].quantile(min_market_cap_rank)
        
        for symbol in graham_data.index:
            company_data = graham_data.loc[symbol]
            
            # 그레이엄의 7가지 기준 검증
            graham_criteria = [
                0 < company_data['pe_ratio'] <= max_pe,
                0 < company_data['pb_ratio'] <= max_pb,
                company_data['current_ratio'] >= min_current_ratio,
                company_data['debt_to_equity'] <= max_debt_equity,
                company_data.get('dividend_years', 0) >= min_dividend_years,
                company_data['market_cap'] >= market_cap_threshold,
                company_data.get('earnings_stability', 0) >= 0.7  # 수익 안정성
            ]
            
            passed_criteria = sum(graham_criteria)
            
            # 최소 5개 기준 이상 충족
            if passed_criteria >= 5:
                # 추가 안전성 검증
                safety_score = self._calculate_safety_margin(company_data)
                
                if safety_score >= 0.6:
                    # 충족 기준 수와 안전성을 기반으로 강도 계산
                    criteria_score = passed_criteria / 7
                    strength = min(1.0, criteria_score * safety_score * 1.2)
                    
                    signals.append(Signal(
                        symbol=symbol,
                        timestamp=pd.Timestamp.now(),
                        signal_type='BUY',
                        strength=strength,
                        confidence=0.9,
                        metadata={
                            'passed_criteria': passed_criteria,
                            'safety_score': safety_score,
                            'pe_ratio': company_data['pe_ratio'],
                            'pb_ratio': company_data['pb_ratio'],
                            'current_ratio': company_data['current_ratio']
                        }
                    ))
        
        return self.validate_signals(signals)
    
    def _calculate_safety_margin(self, company_data: pd.Series) -> float:
        """안전마진 계산"""
        safety_score = 0.0
        
        # 유동성 안전성 (30%)
        current_ratio = company_data['current_ratio']
        if current_ratio >= 3.0:
            liquidity_score = 1.0
        elif current_ratio >= 2.0:
            liquidity_score = 0.8
        else:
            liquidity_score = max(0, (current_ratio - 1.0) / 1.0)
        safety_score += liquidity_score * 0.3
        
        # 부채 안전성 (25%)
        debt_equity = company_data['debt_to_equity']
        debt_score = max(0, (0.5 - debt_equity) / 0.5)
        safety_score += debt_score * 0.25
        
        # 밸류에이션 안전성 (25%)
        pe_ratio = company_data['pe_ratio']
        pb_ratio = company_data['pb_ratio']
        if pe_ratio > 0 and pb_ratio > 0:
            pe_score = max(0, (15 - pe_ratio) / 15)
            pb_score = max(0, (1.5 - pb_ratio) / 1.5)
            valuation_score = (pe_score + pb_score) / 2
            safety_score += valuation_score * 0.25
        
        # 배당 안전성 (20%)
        dividend_yield = company_data.get('dividend_yield', 0)
        dividend_years = company_data.get('dividend_years', 0)
        if dividend_yield > 0.02 and dividend_years >= 5:
            dividend_score = min(1.0, (dividend_yield / 0.06) * 0.5 + (dividend_years / 20) * 0.5)
            safety_score += dividend_score * 0.2
        
        return min(1.0, safety_score)
    
    def calculate_weights(self, signals: List[Signal], 
                         current_portfolio: Optional[Dict[str, float]] = None) -> List[PortfolioWeight]:
        if not signals:
            return []
        
        # 보수적 균등 분산 (그레이엄 스타일)
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

# 14. 조엘 그린블라트의 마법공식
class JoelGreenblattMagicFormulaStrategy(BaseStrategy):
    """조엘 그린블라트의 마법공식 전략"""
    
    def __init__(self, **kwargs):
        super().__init__("Joel_Greenblatt_Magic_Formula_Strategy", **kwargs)
    
    def _get_metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            name="조엘 그린블라트의 마법공식",
            description="ROE + 수익수익률(E/P) 결합한 체계적 가치투자",
            category=StrategyCategory.ADVANCED,
            risk_level=RiskLevel.MEDIUM,
            complexity=Complexity.MEDIUM,
            expected_return="12-17%",
            volatility="14-20%",
            min_investment_period="3년 이상",
            rebalancing_frequency="연 1회"
        )
    
    def _get_required_data_columns(self) -> List[str]:
        return super()._get_required_data_columns() + [
            'roe', 'pe_ratio', 'roic', 'market_cap'
        ]
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        signals = []
        
        min_market_cap = self.parameters.get('min_market_cap', 1000)  # 10억 달러
        top_stocks = self.parameters.get('top_stocks', 30)
        
        magic_data = data.dropna(subset=['roe', 'pe_ratio'])
        
        # 시가총액 필터링
        magic_data = magic_data[magic_data['market_cap'] >= min_market_cap]
        
        if len(magic_data) == 0:
            return []
        
        # 마법공식 랭킹 계산
        magic_scores = []
        
        for symbol in magic_data.index:
            company_data = magic_data.loc[symbol]
            
            # 수익수익률 계산 (E/P = 1/PE)
            pe_ratio = company_data['pe_ratio']
            if pe_ratio <= 0:
                continue
            
            earnings_yield = 1 / pe_ratio
            roe = company_data['roe']
            
            # ROIC 사용 가능하면 ROE 대신 사용
            if 'roic' in company_data and pd.notna(company_data['roic']):
                return_on_capital = company_data['roic']
            else:
                return_on_capital = roe
            
            magic_scores.append({
                'symbol': symbol,
                'earnings_yield': earnings_yield,
                'return_on_capital': return_on_capital,
                'company_data': company_data
            })
        
        if not magic_scores:
            return []
        
        # 각 지표별 순위 계산
        df_scores = pd.DataFrame(magic_scores)
        df_scores['ey_rank'] = df_scores['earnings_yield'].rank(ascending=False)
        df_scores['roc_rank'] = df_scores['return_on_capital'].rank(ascending=False)
        df_scores['combined_rank'] = df_scores['ey_rank'] + df_scores['roc_rank']
        
        # 상위 종목 선별
        df_scores = df_scores.sort_values('combined_rank')
        top_selections = df_scores.head(top_stocks)
        
        for _, row in top_selections.iterrows():
            # 순위가 높을수록 높은 강도
            max_rank = len(df_scores) * 2  # 두 순위 합의 최대값
            strength = 1.0 - (row['combined_rank'] / max_rank)
            
            signals.append(Signal(
                symbol=row['symbol'],
                timestamp=pd.Timestamp.now(),
                signal_type='BUY',
                strength=strength,
                confidence=0.8,
                metadata={
                    'earnings_yield': row['earnings_yield'],
                    'return_on_capital': row['return_on_capital'],
                    'ey_rank': row['ey_rank'],
                    'roc_rank': row['roc_rank'],
                    'combined_rank': row['combined_rank']
                }
            ))
        
        return self.validate_signals(signals)
    
    def calculate_weights(self, signals: List[Signal], 
                         current_portfolio: Optional[Dict[str, float]] = None) -> List[PortfolioWeight]:
        if not signals:
            return []
        
        # 마법공식은 동일 가중치 권장
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

# 전략 팩토리에 등록
def register_value_strategies():
    """가치투자 전략들을 팩토리에 등록"""
    StrategyFactory.register_strategy("buffett_moat", BuffettMoatStrategy)
    StrategyFactory.register_strategy("peter_lynch_peg", PeterLynchPEGStrategy)
    StrategyFactory.register_strategy("benjamin_graham_defensive", BenjaminGrahamDefensiveStrategy)
    StrategyFactory.register_strategy("joel_greenblatt_magic", JoelGreenblattMagicFormulaStrategy)

# 모듈 로드 시 자동 등록
register_value_strategies()