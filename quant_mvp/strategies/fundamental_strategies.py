"""
file: quant_mvp/strategies/fundamental_strategies.py
재무 기반 투자 전략들
가치투자, 성장투자, 퀄리티투자, 배당투자 전략 포함
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from datetime import datetime
import logging

from .base_strategy import BaseStrategy, Signal

logger = logging.getLogger(__name__)

class ValueStrategy(BaseStrategy):
    """가치 투자 전략 - PER, PBR 기반"""
    
    def __init__(self, params: Dict[str, Any] = None):
        default_params = {
            'max_pe_ratio': 15,
            'max_pb_ratio': 1.5,
            'min_market_cap': 1_000_000_000,  # 10억 달러
            'pe_weight': 0.5,
            'pb_weight': 0.5,
            'top_n': 10
        }
        if params:
            default_params.update(params)
        
        super().__init__("Value", default_params)
    
    def get_required_data(self) -> List[str]:
        return ['close', 'pe_ratio', 'pb_ratio', 'market_cap']
    
    def calculate_value_score(self, pe_ratio: float, pb_ratio: float) -> float:
        """가치 점수 계산 (낮은 비율일수록 높은 점수)"""
        pe_weight = self.params['pe_weight']
        pb_weight = self.params['pb_weight']
        max_pe = self.params['max_pe_ratio']
        max_pb = self.params['max_pb_ratio']
        
        # PE 점수 (낮을수록 좋음)
        pe_score = max(0, (max_pe - pe_ratio) / max_pe) if pe_ratio > 0 else 0
        
        # PB 점수 (낮을수록 좋음)
        pb_score = max(0, (max_pb - pb_ratio) / max_pb) if pb_ratio > 0 else 0
        
        return pe_score * pe_weight + pb_score * pb_weight
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """가치 투자 신호 생성"""
        if not self.validate_data(data):
            return []
        
        signals = []
        max_pe = self.params['max_pe_ratio']
        max_pb = self.params['max_pb_ratio']
        min_mcap = self.params['min_market_cap']
        top_n = self.params['top_n']
        
        candidates = []
        
        # 최신 데이터만 사용 (각 종목별로)
        latest_data = data.groupby('symbol').last().reset_index()
        
        for _, row in latest_data.iterrows():
            symbol = row['symbol']
            pe_ratio = row.get('pe_ratio', np.nan)
            pb_ratio = row.get('pb_ratio', np.nan)
            market_cap = row.get('market_cap', 0)
            price = row['close']
            
            # 필터링 조건
            if (pd.isna(pe_ratio) or pd.isna(pb_ratio) or 
                pe_ratio <= 0 or pb_ratio <= 0 or
                pe_ratio > max_pe or pb_ratio > max_pb or
                market_cap < min_mcap):
                continue
            
            value_score = self.calculate_value_score(pe_ratio, pb_ratio)
            
            candidates.append({
                'symbol': symbol,
                'price': price,
                'pe_ratio': pe_ratio,
                'pb_ratio': pb_ratio,
                'market_cap': market_cap,
                'value_score': value_score,
                'date': row.get('date', datetime.now())
            })
        
        # 가치 점수 기준으로 정렬
        if candidates:
            candidates.sort(key=lambda x: x['value_score'], reverse=True)
            selected = candidates[:top_n]
            
            if selected:
                weight_per_stock = 1.0 / len(selected)
                
                for candidate in selected:
                    signals.append(Signal(
                        symbol=candidate['symbol'],
                        action='buy',
                        weight=weight_per_stock,
                        price=candidate['price'],
                        timestamp=candidate['date'],
                        confidence=candidate['value_score'],
                        reason=f"PE: {candidate['pe_ratio']:.1f}, PB: {candidate['pb_ratio']:.1f}"
                    ))
        
        return signals
    
    def get_parameter_bounds(self) -> Dict[str, Tuple[float, float]]:
        return {
            'max_pe_ratio': (8, 25),
            'max_pb_ratio': (0.5, 3.0),
            'min_market_cap': (500_000_000, 10_000_000_000),
            'pe_weight': (0.3, 0.7),
            'pb_weight': (0.3, 0.7),
            'top_n': (5, 20)
        }

class QualityStrategy(BaseStrategy):
    """퀄리티 투자 전략 - ROE, ROA 기반"""
    
    def __init__(self, params: Dict[str, Any] = None):
        default_params = {
            'min_roe': 15,
            'min_roa': 8,
            'max_debt_equity': 0.5,
            'roe_weight': 0.4,
            'roa_weight': 0.4,
            'debt_weight': 0.2,
            'top_n': 10
        }
        if params:
            default_params.update(params)
        
        super().__init__("Quality", default_params)
    
    def get_required_data(self) -> List[str]:
        return ['close', 'roe', 'roa', 'debt_to_equity']
    
    def calculate_quality_score(self, roe: float, roa: float, debt_equity: float) -> float:
        """퀄리티 점수 계산"""
        roe_weight = self.params['roe_weight']
        roa_weight = self.params['roa_weight']
        debt_weight = self.params['debt_weight']
        min_roe = self.params['min_roe']
        min_roa = self.params['min_roa']
        max_debt = self.params['max_debt_equity']
        
        # ROE 점수 (높을수록 좋음)
        roe_score = min(1.0, max(0, roe / 30)) if roe > 0 else 0
        
        # ROA 점수 (높을수록 좋음)
        roa_score = min(1.0, max(0, roa / 20)) if roa > 0 else 0
        
        # 부채 점수 (낮을수록 좋음)
        debt_score = max(0, (max_debt - debt_equity) / max_debt) if debt_equity >= 0 else 0
        
        return roe_score * roe_weight + roa_score * roa_weight + debt_score * debt_weight
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """퀄리티 투자 신호 생성"""
        if not self.validate_data(data):
            return []
        
        signals = []
        min_roe = self.params['min_roe']
        min_roa = self.params['min_roa']
        max_debt = self.params['max_debt_equity']
        top_n = self.params['top_n']
        
        candidates = []
        latest_data = data.groupby('symbol').last().reset_index()
        
        for _, row in latest_data.iterrows():
            symbol = row['symbol']
            roe = row.get('roe', np.nan)
            roa = row.get('roa', np.nan)
            debt_equity = row.get('debt_to_equity', np.nan)
            price = row['close']
            
            # 필터링 조건
            if (pd.isna(roe) or pd.isna(roa) or pd.isna(debt_equity) or
                roe < min_roe or roa < min_roa or debt_equity > max_debt):
                continue
            
            quality_score = self.calculate_quality_score(roe, roa, debt_equity)
            
            candidates.append({
                'symbol': symbol,
                'price': price,
                'roe': roe,
                'roa': roa,
                'debt_equity': debt_equity,
                'quality_score': quality_score,
                'date': row.get('date', datetime.now())
            })
        
        # 퀄리티 점수 기준으로 정렬
        if candidates:
            candidates.sort(key=lambda x: x['quality_score'], reverse=True)
            selected = candidates[:top_n]
            
            if selected:
                weight_per_stock = 1.0 / len(selected)
                
                for candidate in selected:
                    signals.append(Signal(
                        symbol=candidate['symbol'],
                        action='buy',
                        weight=weight_per_stock,
                        price=candidate['price'],
                        timestamp=candidate['date'],
                        confidence=candidate['quality_score'],
                        reason=f"ROE: {candidate['roe']:.1f}%, ROA: {candidate['roa']:.1f}%"
                    ))
        
        return signals
    
    def get_parameter_bounds(self) -> Dict[str, Tuple[float, float]]:
        return {
            'min_roe': (10, 25),
            'min_roa': (5, 15),
            'max_debt_equity': (0.2, 1.0),
            'roe_weight': (0.2, 0.6),
            'roa_weight': (0.2, 0.6),
            'debt_weight': (0.1, 0.4),
            'top_n': (5, 20)
        }

class GrowthStrategy(BaseStrategy):
    """성장 투자 전략 - 매출/이익 성장률 기반"""
    
    def __init__(self, params: Dict[str, Any] = None):
        default_params = {
            'min_revenue_growth': 10,
            'min_earnings_growth': 15,
            'revenue_weight': 0.4,
            'earnings_weight': 0.6,
            'top_n': 10
        }
        if params:
            default_params.update(params)
        
        super().__init__("Growth", default_params)
    
    def get_required_data(self) -> List[str]:
        return ['close', 'revenue_growth', 'earnings_growth']
    
    def calculate_growth_score(self, revenue_growth: float, earnings_growth: float) -> float:
        """성장 점수 계산"""
        revenue_weight = self.params['revenue_weight']
        earnings_weight = self.params['earnings_weight']
        
        # 성장률을 0-1 스케일로 변환 (30% 성장을 1.0으로 가정)
        revenue_score = min(1.0, max(0, revenue_growth / 30)) if revenue_growth > 0 else 0
        earnings_score = min(1.0, max(0, earnings_growth / 30)) if earnings_growth > 0 else 0
        
        return revenue_score * revenue_weight + earnings_score * earnings_weight
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """성장 투자 신호 생성"""
        if not self.validate_data(data):
            return []
        
        signals = []
        min_rev_growth = self.params['min_revenue_growth']
        min_earn_growth = self.params['min_earnings_growth']
        top_n = self.params['top_n']
        
        candidates = []
        latest_data = data.groupby('symbol').last().reset_index()
        
        for _, row in latest_data.iterrows():
            symbol = row['symbol']
            revenue_growth = row.get('revenue_growth', np.nan)
            earnings_growth = row.get('earnings_growth', np.nan)
            price = row['close']
            
            # 필터링 조건
            if (pd.isna(revenue_growth) or pd.isna(earnings_growth) or
                revenue_growth < min_rev_growth or earnings_growth < min_earn_growth):
                continue
            
            growth_score = self.calculate_growth_score(revenue_growth, earnings_growth)
            
            candidates.append({
                'symbol': symbol,
                'price': price,
                'revenue_growth': revenue_growth,
                'earnings_growth': earnings_growth,
                'growth_score': growth_score,
                'date': row.get('date', datetime.now())
            })
        
        # 성장 점수 기준으로 정렬
        if candidates:
            candidates.sort(key=lambda x: x['growth_score'], reverse=True)
            selected = candidates[:top_n]
            
            if selected:
                weight_per_stock = 1.0 / len(selected)
                
                for candidate in selected:
                    signals.append(Signal(
                        symbol=candidate['symbol'],
                        action='buy',
                        weight=weight_per_stock,
                        price=candidate['price'],
                        timestamp=candidate['date'],
                        confidence=candidate['growth_score'],
                        reason=f"Rev: {candidate['revenue_growth']:.1f}%, Earn: {candidate['earnings_growth']:.1f}%"
                    ))
        
        return signals
    
    def get_parameter_bounds(self) -> Dict[str, Tuple[float, float]]:
        return {
            'min_revenue_growth': (5, 20),
            'min_earnings_growth': (10, 30),
            'revenue_weight': (0.2, 0.6),
            'earnings_weight': (0.4, 0.8),
            'top_n': (5, 20)
        }

class DividendStrategy(BaseStrategy):
    """배당 투자 전략"""
    
    def __init__(self, params: Dict[str, Any] = None):
        default_params = {
            'min_dividend_yield': 2.0,
            'min_payout_ratio': 0.3,
            'max_payout_ratio': 0.8,
            'yield_weight': 0.6,
            'payout_weight': 0.4,
            'top_n': 10
        }
        if params:
            default_params.update(params)
        
        super().__init__("Dividend", default_params)
    
    def get_required_data(self) -> List[str]:
        return ['close', 'dividend_yield']
    
    def calculate_dividend_score(self, dividend_yield: float, payout_ratio: float = None) -> float:
        """배당 점수 계산"""
        yield_weight = self.params['yield_weight']
        payout_weight = self.params['payout_weight']
        
        # 배당 수익률 점수 (높을수록 좋지만 너무 높으면 위험)
        optimal_yield = 4.0  # 최적 배당수익률
        if dividend_yield <= optimal_yield:
            yield_score = dividend_yield / optimal_yield
        else:
            # 너무 높은 배당수익률은 점수 감점
            yield_score = max(0, 2 - dividend_yield / optimal_yield)
        
        # 배당성향 점수 (적절한 범위가 좋음)
        if payout_ratio is not None:
            min_payout = self.params['min_payout_ratio']
            max_payout = self.params['max_payout_ratio']
            
            if min_payout <= payout_ratio <= max_payout:
                # 적절한 범위 내에서는 중간값이 최고 점수
                mid_payout = (min_payout + max_payout) / 2
                payout_score = 1 - abs(payout_ratio - mid_payout) / (max_payout - min_payout) * 2
            else:
                payout_score = 0
                
            return yield_score * yield_weight + payout_score * payout_weight
        else:
            return yield_score  # 배당성향 데이터가 없으면 수익률만 사용
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """배당 투자 신호 생성"""
        if not self.validate_data(data):
            return []
        
        signals = []
        min_yield = self.params['min_dividend_yield']
        top_n = self.params['top_n']
        
        candidates = []
        latest_data = data.groupby('symbol').last().reset_index()
        
        for _, row in latest_data.iterrows():
            symbol = row['symbol']
            dividend_yield = row.get('dividend_yield', np.nan)
            price = row['close']
            
            # 필터링 조건
            if pd.isna(dividend_yield) or dividend_yield < min_yield:
                continue
            
            # 배당성향 데이터가 있으면 사용
            payout_ratio = row.get('payout_ratio', None)
            if payout_ratio is not None:
                min_payout = self.params['min_payout_ratio']
                max_payout = self.params['max_payout_ratio']
                if payout_ratio < min_payout or payout_ratio > max_payout:
                    continue
            
            dividend_score = self.calculate_dividend_score(dividend_yield, payout_ratio)
            
            candidates.append({
                'symbol': symbol,
                'price': price,
                'dividend_yield': dividend_yield,
                'payout_ratio': payout_ratio,
                'dividend_score': dividend_score,
                'date': row.get('date', datetime.now())
            })
        
        # 배당 점수 기준으로 정렬
        if candidates:
            candidates.sort(key=lambda x: x['dividend_score'], reverse=True)
            selected = candidates[:top_n]
            
            if selected:
                weight_per_stock = 1.0 / len(selected)
                
                for candidate in selected:
                    payout_info = f", Payout: {candidate['payout_ratio']:.1%}" if candidate['payout_ratio'] else ""
                    
                    signals.append(Signal(
                        symbol=candidate['symbol'],
                        action='buy',
                        weight=weight_per_stock,
                        price=candidate['price'],
                        timestamp=candidate['date'],
                        confidence=candidate['dividend_score'],
                        reason=f"Div Yield: {candidate['dividend_yield']:.1f}%{payout_info}"
                    ))
        
        return signals
    
    def get_parameter_bounds(self) -> Dict[str, Tuple[float, float]]:
        return {
            'min_dividend_yield': (1.0, 4.0),
            'min_payout_ratio': (0.2, 0.5),
            'max_payout_ratio': (0.6, 0.9),
            'yield_weight': (0.4, 0.8),
            'payout_weight': (0.2, 0.6),
            'top_n': (5, 20)
        }