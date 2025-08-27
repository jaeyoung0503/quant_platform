"""
file: quant_mvp/strategies/hybrid_strategies.py
혼합 전략들 - 기술적 분석과 재무 분석을 결합한 전략
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from datetime import datetime
import logging

from .base_strategy import BaseStrategy, Signal

logger = logging.getLogger(__name__)

class GARPStrategy(BaseStrategy):
    """GARP (Growth at Reasonable Price) 전략"""
    
    def __init__(self, params: Dict[str, Any] = None):
        default_params = {
            'max_peg_ratio': 1.5,
            'min_roe': 15,
            'max_pe_ratio': 20,
            'min_earnings_growth': 10,
            'growth_weight': 0.4,
            'value_weight': 0.6,
            'top_n': 10
        }
        if params:
            default_params.update(params)
        
        super().__init__("GARP", default_params)
    
    def get_required_data(self) -> List[str]:
        return ['close', 'pe_ratio', 'roe', 'earnings_growth']
    
    def calculate_peg_ratio(self, pe_ratio: float, earnings_growth: float) -> float:
        """PEG 비율 계산"""
        if earnings_growth <= 0:
            return float('inf')
        return pe_ratio / earnings_growth
    
    def calculate_garp_score(self, pe_ratio: float, earnings_growth: float, roe: float) -> float:
        """GARP 점수 계산"""
        growth_weight = self.params['growth_weight']
        value_weight = self.params['value_weight']
        
        # 성장 점수 (높을수록 좋음)
        growth_score = min(1.0, max(0, earnings_growth / 25)) if earnings_growth > 0 else 0
        
        # 가치 점수 (낮은 PEG 비율이 좋음)
        peg_ratio = self.calculate_peg_ratio(pe_ratio, earnings_growth)
        if peg_ratio == float('inf'):
            value_score = 0
        else:
            value_score = max(0, (2.0 - peg_ratio) / 2.0)  # PEG 2.0 이하가 좋음
        
        # ROE 보너스
        roe_bonus = min(0.2, roe / 100) if roe > 0 else 0
        
        return (growth_score * growth_weight + value_score * value_weight) * (1 + roe_bonus)
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """GARP 신호 생성"""
        if not self.validate_data(data):
            return []
        
        signals = []
        max_peg = self.params['max_peg_ratio']
        min_roe = self.params['min_roe']
        max_pe = self.params['max_pe_ratio']
        min_growth = self.params['min_earnings_growth']
        top_n = self.params['top_n']
        
        candidates = []
        latest_data = data.groupby('symbol').last().reset_index()
        
        for _, row in latest_data.iterrows():
            symbol = row['symbol']
            pe_ratio = row.get('pe_ratio', np.nan)
            earnings_growth = row.get('earnings_growth', np.nan)
            roe = row.get('roe', np.nan)
            price = row['close']
            
            # 필터링 조건
            if (pd.isna(pe_ratio) or pd.isna(earnings_growth) or pd.isna(roe) or
                pe_ratio <= 0 or earnings_growth <= 0 or roe <= 0 or
                pe_ratio > max_pe or roe < min_roe or earnings_growth < min_growth):
                continue
            
            peg_ratio = self.calculate_peg_ratio(pe_ratio, earnings_growth)
            if peg_ratio > max_peg:
                continue
            
            garp_score = self.calculate_garp_score(pe_ratio, earnings_growth, roe)
            
            candidates.append({
                'symbol': symbol,
                'price': price,
                'pe_ratio': pe_ratio,
                'earnings_growth': earnings_growth,
                'roe': roe,
                'peg_ratio': peg_ratio,
                'garp_score': garp_score,
                'date': row.get('date', datetime.now())
            })
        
        # GARP 점수 기준으로 정렬
        if candidates:
            candidates.sort(key=lambda x: x['garp_score'], reverse=True)
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
                        confidence=candidate['garp_score'],
                        reason=f"PEG: {candidate['peg_ratio']:.2f}, ROE: {candidate['roe']:.1f}%"
                    ))
        
        return signals
    
    def get_parameter_bounds(self) -> Dict[str, Tuple[float, float]]:
        return {
            'max_peg_ratio': (1.0, 2.5),
            'min_roe': (10, 25),
            'max_pe_ratio': (15, 30),
            'min_earnings_growth': (5, 20),
            'growth_weight': (0.2, 0.8),
            'value_weight': (0.2, 0.8),
            'top_n': (5, 20)
        }

class MomentumValueStrategy(BaseStrategy):
    """모멘텀과 가치투자 결합 전략"""
    
    def __init__(self, params: Dict[str, Any] = None):
        default_params = {
            'momentum_weight': 0.6,
            'value_weight': 0.4,
            'lookback_period': 60,
            'min_momentum_return': 0.05,
            'max_pe_ratio': 20,
            'max_pb_ratio': 2.0,
            'top_n': 15
        }
        if params:
            default_params.update(params)
        
        super().__init__("MomentumValue", default_params)
    
    def get_required_data(self) -> List[str]:
        return ['close', 'pe_ratio', 'pb_ratio', 'volume']
    
    def calculate_momentum_score(self, prices: pd.Series, lookback: int) -> float:
        """모멘텀 점수 계산"""
        if len(prices) < lookback + 1:
            return 0
        
        current_price = prices.iloc[-1]
        past_price = prices.iloc[-(lookback + 1)]
        
        if past_price <= 0:
            return 0
        
        momentum_return = (current_price / past_price) - 1
        
        # 0-1 스케일로 변환 (20% 상승을 1.0으로)
        return min(1.0, max(0, momentum_return / 0.2))
    
    def calculate_value_score(self, pe_ratio: float, pb_ratio: float) -> float:
        """가치 점수 계산"""
        max_pe = self.params['max_pe_ratio']
        max_pb = self.params['max_pb_ratio']
        
        # PE 점수 (낮을수록 좋음)
        pe_score = max(0, (max_pe - pe_ratio) / max_pe) if pe_ratio > 0 else 0
        
        # PB 점수 (낮을수록 좋음)
        pb_score = max(0, (max_pb - pb_ratio) / max_pb) if pb_ratio > 0 else 0
        
        return (pe_score + pb_score) / 2
    
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """모멘텀+가치 신호 생성"""
        if not self.validate_data(data):
            return []
        
        signals = []
        momentum_weight = self.params['momentum_weight']
        value_weight = self.params['value_weight']
        lookback = self.params['lookback_period']
        min_momentum = self.params['min_momentum_return']
        max_pe = self.params['max_pe_ratio']
        max_pb = self.params['max_pb_ratio']
        top_n = self.params['top_n']
        
        candidates = []
        
        for symbol in data['symbol'].unique():
            symbol_data = data[data['symbol'] == symbol].copy()
            symbol_data = symbol_data.sort_values('date')
            
            if len(symbol_data) < lookback + 1:
                continue
            
            # 최신 재무 데이터
            latest_row = symbol_data.iloc[-1]
            pe_ratio = latest_row.get('pe_ratio', np.nan)
            pb_ratio = latest_row.get('pb_ratio', np.nan)
            price = latest_row['close']
            
            # 필터링 조건
            if (pd.isna(pe_ratio) or pd.isna(pb_ratio) or
                pe_ratio <= 0 or pb_ratio <= 0 or
                pe_ratio > max_pe or pb_ratio > max_pb):
                continue
            
            # 모멘텀 계산
            prices = symbol_data['close']
            momentum_score = self.calculate_momentum_score(prices, lookback)
            
            # 최소 모멘텀 요구
            recent_return = (prices.iloc[-1] / prices.iloc[-(lookback + 1)]) - 1 if len(prices) >= lookback + 1 else 0
            if recent_return < min_momentum:
                continue
            
            # 가치 점수 계산
            value_score = self.calculate_value_score(pe_ratio, pb_ratio)
            
            # 통합 점수
            combined_score = momentum_score * momentum_weight + value_score * value_weight
            
            candidates.append({
                'symbol': symbol,
                'price': price,
                'momentum_score': momentum_score,
                'value_score': value_score,
                'combined_score': combined_score,
                'momentum_return': recent_return,
                'pe_ratio': pe_ratio,
                'pb_ratio': pb_ratio,
                'date': latest_row.get('date', datetime.now())
            })
        
        # 통합 점수 기준으로 정렬
        if candidates:
            candidates.sort(key=lambda x: x['combined_score'], reverse=True)
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
                        confidence=candidate['combined_score'],
                        reason=f"Mom: {candidate['momentum_return']:.1%}, PE: {candidate['pe_ratio']:.1f}"
                    ))
        
        return signals
    
    def get_parameter_bounds(self) -> Dict[str, Tuple[float, float]]:
        return {
            'momentum_weight': (0.3, 0.8),
            'value_weight': (0.2, 0.7),
            'lookback_period': (30, 120),
            'min_momentum_return': (0.02, 0.15),
            'max_pe_ratio': (15, 30),
            'max_pb_ratio': (1.0, 3.0),
            'top_n': (10, 25)
        }