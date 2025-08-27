"""
file: quant_mvp/strategies/base_strategy.py
기본 전략 클래스 및 공통 유틸리티
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class Signal:
    """거래 신호"""
    symbol: str
    action: str  # 'buy', 'sell', 'hold'
    weight: float  # 포트폴리오 내 가중치
    price: float
    timestamp: datetime
    confidence: float = 1.0
    reason: str = ""

@dataclass
class StrategyResult:
    """전략 실행 결과"""
    signals: List[Signal]
    metadata: Dict[str, Any]
    performance_metrics: Dict[str, float]

class BaseStrategy(ABC):
    """모든 전략의 기본 클래스"""
    
    def __init__(self, name: str, params: Dict[str, Any] = None):
        self.name = name
        self.params = params or {}
        self.is_fitted = False
        self.logger = logging.getLogger(f"{__name__}.{name}")
        
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """거래 신호 생성"""
        pass
    
    @abstractmethod
    def get_required_data(self) -> List[str]:
        """필요한 데이터 컬럼 반환"""
        pass
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """데이터 유효성 검사"""
        required_cols = self.get_required_data()
        missing_cols = [col for col in required_cols if col not in data.columns]
        
        if missing_cols:
            self.logger.error(f"Missing required columns: {missing_cols}")
            return False
            
        if data.empty:
            self.logger.error("Empty data provided")
            return False
            
        return True
    
    def preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """데이터 전처리"""
        # 결측값 처리
        data = data.fillna(method='ffill').fillna(method='bfill')
        
        # 날짜 인덱스 설정
        if 'date' in data.columns and not isinstance(data.index, pd.DatetimeIndex):
            data['date'] = pd.to_datetime(data['date'])
            data = data.set_index('date')
        
        return data
    
    def calculate_returns(self, prices: pd.Series, period: int = 1) -> pd.Series:
        """수익률 계산"""
        return prices.pct_change(period)
    
    def calculate_rolling_stats(self, data: pd.Series, window: int) -> Dict[str, pd.Series]:
        """롤링 통계 계산"""
        return {
            'mean': data.rolling(window).mean(),
            'std': data.rolling(window).std(),
            'min': data.rolling(window).min(),
            'max': data.rolling(window).max()
        }
    
    def normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """가중치 정규화"""
        total = sum(abs(w) for w in weights.values())
        if total == 0:
            return weights
        return {k: v/total for k, v in weights.items()}
    
    def get_parameter_bounds(self) -> Dict[str, Tuple[float, float]]:
        """파라미터 최적화 범위 반환"""
        return {}
    
    def set_parameters(self, params: Dict[str, Any]):
        """파라미터 설정"""
        self.params.update(params)
        self.is_fitted = False
    
    def __str__(self):
        return f"{self.name}({self.params})"
    
    def __repr__(self):
        return self.__str__()

class StrategyValidator:
    """전략 검증 유틸리티"""
    
    @staticmethod
    def validate_signals(signals: List[Signal]) -> bool:
        """신호 유효성 검사"""
        if not signals:
            return True
            
        for signal in signals:
            if signal.weight < 0 or signal.weight > 1:
                logger.error(f"Invalid weight {signal.weight} for {signal.symbol}")
                return False
                
            if signal.action not in ['buy', 'sell', 'hold']:
                logger.error(f"Invalid action {signal.action} for {signal.symbol}")
                return False
                
        return True
    
    @staticmethod
    def validate_parameters(strategy: BaseStrategy, params: Dict[str, Any]) -> bool:
        """파라미터 유효성 검사"""
        bounds = strategy.get_parameter_bounds()
        
        for param_name, value in params.items():
            if param_name in bounds:
                min_val, max_val = bounds[param_name]
                if not (min_val <= value <= max_val):
                    logger.error(f"Parameter {param_name}={value} out of bounds [{min_val}, {max_val}]")
                    return False
        
        return True

class StrategyMetrics:
    """전략 성과 지표 계산"""
    
    @staticmethod
    def calculate_basic_metrics(returns: pd.Series) -> Dict[str, float]:
        """기본 성과 지표"""
        if returns.empty or returns.isna().all():
            return {}
            
        total_return = (1 + returns).cumprod().iloc[-1] - 1
        annual_return = (1 + total_return) ** (252 / len(returns)) - 1
        volatility = returns.std() * np.sqrt(252)
        sharpe_ratio = annual_return / volatility if volatility != 0 else 0
        
        # 최대 낙폭 계산
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': (returns > 0).mean()
        }