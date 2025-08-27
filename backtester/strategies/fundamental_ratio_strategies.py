"""
File: backtester/strategies/fundamental_ratio_strategies.py
Core Fundamental Ratio Based Strategies (Top 5 Financial Indicators)
"""

import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy

class PERStrategy(BaseStrategy):
    """P/E Ratio Based Value Strategy - 주가수익비율 전략"""
    
    def __init__(self):
        super().__init__("PER Strategy")
        self.low_pe_threshold = 12.0    # 저평가 기준
        self.high_pe_threshold = 25.0   # 고평가 기준
        self.extreme_pe_limit = 100.0   # 극단값 제외
        self.momentum_filter = True     # 모멘텀 필터 사용
        
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """PER 기반 매매신호 생성"""
        signals = pd.Series(0, index=data.index)
        
        if 'PE_Ratio' not in data.columns:
            return self._technical_pe_proxy(data)
        
        pe_ratio = data['PE_Ratio']
        close = data['Close']
        
        # PER 유효성 검증 (음수 제거, 극단값 제외)
        valid_pe = (pe_ratio > 0) & (pe_ratio < self.extreme_pe_limit)
        
        # 기본 PER 신호
        pe_signals = pd.Series(0, index=data.index)
        pe_signals[valid_pe & (pe_ratio <= self.low_pe_threshold)] = 1   # 저PER 매수
        pe_signals[valid_pe & (pe_ratio >= self.high_pe_threshold)] = -1  # 고PER 매도
        
        if self.momentum_filter:
            # 3개월 모멘텀 확인
            momentum_3m = close.pct_change(63)
            momentum_1m = close.pct_change(21)
            
            # 저PER + 긍정적 모멘텀만 매수
            buy_condition = (pe_signals == 1) & (momentum_3m > -0.1) & (momentum_1m > -0.05)
            sell_condition = (pe_signals == -1) | (momentum_1m < -0.15)
            
            signals[buy_condition] = 1
            signals[sell_condition] = -1
        else:
            signals = pe_signals
        
        return signals
    
    def _technical_pe_proxy(self, data: pd.DataFrame) -> pd.Series:
        """기술적 분석을 이용한 PER 대용 지표"""
        close = data['Close']
        signals = pd.Series(0, index=data.index)
        
        # 장기 이동평균 대비 가격 비율을 PER 대용으로 사용
        sma_200 = close.rolling(window=200).mean()
        price_ratio = close / sma_200
        
        # RSI로 과매수/과매도 확인
        rsi = self.calculate_technical_indicators(data)['RSI']
        
        # 저평가 신호: 가격이 장기평균 대비 낮고 RSI 과매도
        buy_condition = (price_ratio < 0.85) & (rsi < 35)
        sell_condition = (price_ratio > 1.20) & (rsi > 70)
        
        signals[buy_condition] = 1
        signals[sell_condition] = -1
        
        return signals
    
    def calculate_pe_quality_score(self, data: pd.DataFrame) -> pd.Series:
        """PER 품질 점수 계산 (0-1 스케일)"""
        if 'PE_Ratio' not in data.columns:
            return pd.Series(0.5, index=data.index)
        
        pe_ratio = data['PE_Ratio']
        
        # PER 점수 (낮을수록 좋음, 0-1 정규화)
        pe_score = 1 - np.clip(pe_ratio / 30.0, 0, 1)
        
        # 유효하지 않은 PER은 중간 점수
        pe_score[(pe_ratio <= 0) | (pe_ratio > 100)] = 0.5
        
        return pe_score

class PBRStrategy(BaseStrategy):
    """P/B Ratio Based Deep Value Strategy - 주가순자산비율 전략"""
    
    def __init__(self):
        super().__init__("PBR Strategy")
        self.low_pb_threshold = 1.0     # 장부가치 이하
        self.high_pb_threshold = 3.0    # 고평가 기준
        self.quality_filter = True      # 품질 필터 사용
        
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """PBR 기반 매매신호 생성"""
        signals = pd.Series(0, index=data.index)
        
        if 'PB_Ratio' not in data.columns:
            return self._technical_pb_proxy(data)
        
        pb_ratio = data['PB_Ratio']
        close = data['Close']
        
        # 기본 PBR 신호
        pb_signals = pd.Series(0, index=data.index)
        pb_signals[pb_ratio <= self.low_pb_threshold] = 1   # 장부가치 이하 매수
        pb_signals[pb_ratio >= self.high_pb_threshold] = -1  # 고PBR 매도
        
        if self.quality_filter and 'ROE' in data.columns:
            # 수익성 있는 기업만 선별 (ROE > 0)
            profitable = data['ROE'] > 0
            buy_condition = (pb_signals == 1) & profitable
            sell_condition = (pb_signals == -1) | (data['ROE'] < -10)  # 적자 기업 매도
            
            signals[buy_condition] = 1
            signals[sell_condition] = -1
        else:
            signals = pb_signals
        
        # 트렌드 확인 추가
        sma_50 = close.rolling(window=50).mean()
        downtrend = close < sma_50 * 0.95
        
        # 하락 추세에서는 매수 신호 약화
        signals[(signals == 1) & downtrend] *= 0.5
        
        return signals
    
    def _technical_pb_proxy(self, data: pd.DataFrame) -> pd.Series:
        """기술적 분석을 이용한 PBR 대용 지표"""
        close = data['Close']
        signals = pd.Series(0, index=data.index)
        
        # 52주 최저가 대비 현재가 위치를 PBR 대용으로 사용
        rolling_low = close.rolling(window=252).min()
        rolling_high = close.rolling(window=252).max()
        
        # 52주 레인지 내 위치
        position_in_range = (close - rolling_low) / (rolling_high - rolling_low + 1e-6)
        
        # 52주 최저가 근처는 장부가치 근처로 간주
        buy_condition = position_in_range < 0.15
        sell_condition = position_in_range > 0.85
        
        signals[buy_condition] = 1
        signals[sell_condition] = -1
        
        return signals

class ROEStrategy(BaseStrategy):
    """ROE Based Quality Strategy - 자기자본이익률 전략"""
    
    def __init__(self):
        super().__init__("ROE Quality Strategy")
        self.min_roe = 15.0            # 최소 ROE 기준
        self.excellent_roe = 20.0      # 우수 ROE 기준
        self.consistency_periods = 8   # ROE 일관성 검사 기간
        self.trend_periods = 4         # ROE 트렌드 검사 기간
        
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """ROE 기반 매매신호 생성"""
        signals = pd.Series(0, index=data.index)
        
        if 'ROE' not in data.columns:
            return self._technical_roe_proxy(data)
        
        roe = data['ROE']
        close = data['Close']
        
        # ROE 품질 기준
        high_roe = roe >= self.min_roe
        excellent_roe = roe >= self.excellent_roe
        
        # ROE 안정성 (변동성이 낮을수록 좋음)
        roe_volatility = roe.rolling(window=self.consistency_periods).std()
        stable_roe = roe_volatility < 3.0  # ROE 변동성 3% 이하
        
        # ROE 개선 트렌드
        roe_improving = roe > roe.shift(self.trend_periods)
        
        # 가격 모멘텀 확인
        momentum_1m = close.pct_change(21)
        momentum_3m = close.pct_change(63)
        
        # 매수 조건: 높은 ROE + 안정성 + 개선 트렌드 + 긍정적 모멘텀
        quality_criteria = high_roe & stable_roe & roe_improving
        momentum_criteria = (momentum_1m > 0.03) & (momentum_3m > 0.05)
        
        buy_condition = quality_criteria & momentum_criteria
        
        # 매도 조건: ROE 악화 또는 모멘텀 붕괴
        sell_condition = (roe < 5.0) | (momentum_1m < -0.15) | (roe < roe.shift(8) * 0.7)
        
        # 우수한 ROE는 더 강한 신호
        signals[buy_condition & excellent_roe] = 1.0
        signals[buy_condition & (~excellent_roe)] = 0.7
        signals[sell_condition] = -1
        
        return signals
    
    def _technical_roe_proxy(self, data: pd.DataFrame) -> pd.Series:
        """기술적 분석을 이용한 ROE 대용 지표"""
        close = data['Close']
        volume = data.get('Volume', pd.Series(1, index=close.index))
        
        signals = pd.Series(0, index=data.index)
        
        # 수익률의 샤프 비율을 ROE 대용으로 사용
        returns = close.pct_change()
        rolling_sharpe = (
            returns.rolling(window=63).mean() / 
            returns.rolling(window=63).std()
        ) * np.sqrt(252)
        
        # 거래량 안정성 (기업 운영의 안정성 대용)
        volume_stability = 1 / (volume.rolling(window=30).std() / volume.rolling(window=30).mean() + 0.01)
        
        # 품질 신호: 높은 샤프 비율 + 안정적 거래량
        quality_threshold = rolling_sharpe.quantile(0.7)
        volume_threshold = volume_stability.quantile(0.6)
        
        quality_signal = (rolling_sharpe > quality_threshold) & (volume_stability > volume_threshold)
        
        momentum = close.pct_change(21)
        buy_condition = quality_signal & (momentum > 0.03)
        sell_condition = (rolling_sharpe < 0) | (momentum < -0.15)
        
        signals[buy_condition] = 1
        signals[sell_condition] = -1
        
        return signals
    
    def calculate_roe_quality_metrics(self, data: pd.DataFrame) -> dict:
        """ROE 품질 지표 계산"""
        if 'ROE' not in data.columns:
            return {'error': 'ROE data not available'}
        
        roe = data['ROE']
        current_roe = roe.iloc[-1]
        
        metrics = {
            'current_roe': current_roe,
            'roe_level': 'excellent' if current_roe >= 20 else 'good' if current_roe >= 15 else 'fair' if current_roe >= 10 else 'poor',
            'roe_stability': roe.rolling(window=8).std().iloc[-1],
            'roe_trend': 'improving' if current_roe > roe.iloc[-5] else 'declining',
            'consistency_score': 1 / (roe.rolling(window=8).std().iloc[-1] + 0.1),  # 낮은 변동성 = 높은 점수
            'quality_score': min(current_roe / 25.0, 1.0)  # 25% ROE를 만점으로 정규화
        }
        
        return metrics

class DebtEquityStrategy(BaseStrategy):
    """Debt-to-Equity Ratio Based Conservative Strategy - 부채비율 전략"""
    
    def __init__(self):
        super().__init__("Debt-Equity Conservative Strategy")
        self.max_debt_equity = 0.5      # 보수적 부채비율 기준
        self.moderate_debt_equity = 1.0 # 적정 부채비율 기준
        self.debt_trend_periods = 4     # 부채 트렌드 분석 기간
        
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """부채비율 기반 매매신호 생성"""
        signals = pd.Series(0, index=data.index)
        
        if 'Debt_to_Equity' not in data.columns:
            return self._technical_debt_proxy(data)
        
        debt_equity = data['Debt_to_Equity']
        close = data['Close']
        
        # 부채비율 등급
        conservative = debt_equity <= self.max_debt_equity      # 보수적
        moderate = debt_equity <= self.moderate_debt_equity     # 적정
        high_debt = debt_equity > self.moderate_debt_equity     # 고부채
        
        # 부채 개선 트렌드
        debt_improving = debt_equity < debt_equity.shift(self.debt_trend_periods)
        debt_worsening = debt_equity > debt_equity.shift(self.debt_trend_periods) * 1.2
        
        # 수익성과 결합 (가능한 경우)
        if 'ROE' in data.columns:
            profitable = data['ROE'] > 8.0
            conservative_and_profitable = conservative & profitable & debt_improving
        else:
            conservative_and_profitable = conservative & debt_improving
        
        # 가격 트렌드 확인
        sma_20 = close.rolling(window=20).mean()
        sma_50 = close.rolling(window=50).mean()
        uptrend = (close > sma_20) & (sma_20 > sma_50)
        
        # 매수 조건: 보수적 부채 + 개선 트렌드 + 상승 추세
        buy_condition = conservative_and_profitable & uptrend
        
        # 매도 조건: 고부채 또는 부채 악화 또는 가격 하락
        sell_condition = high_debt | debt_worsening | (close < sma_50 * 0.95)
        
        # 부채비율에 따른 신호 강도 조절
        signals[buy_condition & conservative] = 1.0      # 보수적 부채: 강한 매수
        signals[buy_condition & moderate & (~conservative)] = 0.6  # 적정 부채: 약한 매수
        signals[sell_condition] = -1
        
        return signals
    
    def _technical_debt_proxy(self, data: pd.DataFrame) -> pd.Series:
        """기술적 분석을 이용한 부채 위험 대용 지표"""
        close = data['Close']
        signals = pd.Series(0, index=data.index)
        
        # 변동성을 부채 위험의 대용으로 사용
        returns = close.pct_change()
        volatility = returns.rolling(window=63).std() * np.sqrt(252)
        
        # 낮은 변동성 = 보수적 운영 (낮은 부채)
        low_risk = volatility < volatility.quantile(0.3)
        high_risk = volatility > volatility.quantile(0.7)
        
        # 추세 확인
        sma_50 = close.rolling(window=50).mean()
        uptrend = close > sma_50
        downtrend = close < sma_50 * 0.95
        
        # 매수: 낮은 변동성 + 상승 추세
        buy_condition = low_risk & uptrend
        # 매도: 높은 변동성 또는 하락 추세
        sell_condition = high_risk | downtrend
        
        signals[buy_condition] = 1
        signals[sell_condition] = -1
        
        return signals

class PEGStrategy(BaseStrategy):
    """PEG Ratio Based Growth at Reasonable Price Strategy - PEG 비율 전략"""
    
    def __init__(self):
        super().__init__("PEG Growth Strategy")
        self.max_peg = 1.0             # Peter Lynch 기준
        self.excellent_peg = 0.7       # 우수한 PEG
        self.min_growth_rate = 10.0    # 최소 성장률
        self.max_pe = 30.0             # 최대 PER 제한
        
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """PEG 기반 매매신호 생성"""
        signals = pd.Series(0, index=data.index)
        
        # PEG 계산을 위한 데이터 확인
        if not all(col in data.columns for col in ['PE_Ratio', 'ROE']):
            return self._technical_peg_proxy(data)
        
        pe_ratio = data['PE_Ratio']
        roe = data['ROE']
        close = data['Close']
        
        # 성장률 추정 (ROE 기반 간단 추정)
        estimated_growth = roe * 0.7  # 70% 유보율 가정
        
        # PEG 비율 계산
        peg_ratio = pe_ratio / (estimated_growth + 0.01)  # 0으로 나누기 방지
        
        # PEG 기반 조건
        excellent_peg_stocks = (peg_ratio <= self.excellent_peg) & (estimated_growth >= self.min_growth_rate)
        good_peg_stocks = (peg_ratio <= self.max_peg) & (estimated_growth >= self.min_growth_rate)
        
        # PE 제한 조건
        reasonable_pe = pe_ratio <= self.max_pe
        
        # 모멘텀 확인
        momentum_1m = close.pct_change(21)
        momentum_3m = close.pct_change(63)
        momentum_6m = close.pct_change(126)
        
        # 성장 모멘텀 패턴
        growth_momentum = (momentum_1m > 0.03) & (momentum_3m > 0.10) & (momentum_6m > 0.20)
        
        # 매수 조건
        excellent_buy = excellent_peg_stocks & reasonable_pe & growth_momentum
        good_buy = good_peg_stocks & reasonable_pe & (momentum_1m > 0) & (momentum_3m > 0.05)
        
        # 매도 조건
        sell_condition = (peg_ratio > 2.0) | (pe_ratio > 40) | (momentum_1m < -0.15) | (estimated_growth < 5.0)
        
        # 신호 강도에 따른 차등 적용
        signals[excellent_buy] = 1.0
        signals[good_buy & (~excellent_buy)] = 0.7
        signals[sell_condition] = -1
        
        return signals
    
    def _technical_peg_proxy(self, data: pd.DataFrame) -> pd.Series:
        """기술적 분석을 이용한 PEG 대용 지표"""
        close = data['Close']
        signals = pd.Series(0, index=data.index)
        
        # 다중 기간 모멘텀으로 성장 패턴 감지
        momentum_1m = close.pct_change(21)
        momentum_3m = close.pct_change(63)
        momentum_6m = close.pct_change(126)
        momentum_12m = close.pct_change(252)
        
        # 일관된 성장 패턴
        consistent_growth = (
            (momentum_1m > 0.02) & 
            (momentum_3m > 0.08) & 
            (momentum_6m > 0.18) & 
            (momentum_12m > 0.25)
        )
        
        # 가격 대비 과도하지 않은 수준 (PER 대용)
        sma_200 = close.rolling(window=200).mean()
        reasonable_valuation = close / sma_200 < 1.5  # 200일 평균 대비 50% 이내
        
        # 거래량 증가 (관심도 증가)
        volume = data.get('Volume', pd.Series(1, index=close.index))
        avg_volume = volume.rolling(window=50).mean()
        volume_growth = volume > avg_volume * 1.1
        
        # 성장주 패턴
        growth_pattern = consistent_growth & reasonable_valuation & volume_growth
        
        # 모멘텀 붕괴 시 매도
        momentum_break = (momentum_1m < -0.10) | (momentum_3m < -0.05)
        
        signals[growth_pattern] = 1
        signals[momentum_break] = -1
        
        return signals
    
    def calculate_peg_metrics(self, data: pd.DataFrame) -> dict:
        """PEG 관련 지표 계산"""
        metrics = {'available': False}
        
        if all(col in data.columns for col in ['PE_Ratio', 'ROE']):
            pe_ratio = data['PE_Ratio'].iloc[-1]
            roe = data['ROE'].iloc[-1]
            estimated_growth = roe * 0.7
            peg_ratio = pe_ratio / (estimated_growth + 0.01)
            
            metrics = {
                'available': True,
                'current_pe': pe_ratio,
                'current_roe': roe,
                'estimated_growth': estimated_growth,
                'peg_ratio': peg_ratio,
                'peg_rating': 'excellent' if peg_ratio <= 0.7 else 'good' if peg_ratio <= 1.0 else 'fair' if peg_ratio <= 1.5 else 'expensive',
                'lynch_criteria': peg_ratio <= 1.0 and estimated_growth >= 10.0
            }
        
        return metrics