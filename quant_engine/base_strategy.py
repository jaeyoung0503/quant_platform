"""
file: strategy_engine/base_strategy.py
Base Strategy Class and Common Interfaces
전략 기본 클래스 및 공통 인터페이스
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Union
import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum
import logging

# 설정 및 상수
class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Complexity(Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"

class StrategyCategory(Enum):
    BASIC = "basic"
    ADVANCED = "advanced"

@dataclass
class StrategyMetadata:
    """전략 메타데이터"""
    name: str
    description: str
    category: StrategyCategory
    risk_level: RiskLevel
    complexity: Complexity
    expected_return: str
    volatility: str
    min_investment_period: str
    rebalancing_frequency: str

@dataclass
class Signal:
    """매매 신호"""
    symbol: str
    timestamp: pd.Timestamp
    signal_type: str  # 'BUY', 'SELL', 'HOLD'
    strength: float  # 0.0 ~ 1.0
    confidence: float  # 0.0 ~ 1.0
    metadata: Optional[Dict] = None

@dataclass
class PortfolioWeight:
    """포트폴리오 가중치"""
    symbol: str
    weight: float
    target_weight: float
    current_weight: float
    rebalance_needed: bool = False

class BaseStrategy(ABC):
    """전략 기본 클래스"""
    
    def __init__(self, name: str, **kwargs):
        self.name = name
        self.parameters = kwargs
        self.metadata = self._get_metadata()
        self.logger = logging.getLogger(f"Strategy.{name}")
        self._validate_parameters()
    
    @abstractmethod
    def _get_metadata(self) -> StrategyMetadata:
        """전략 메타데이터 반환"""
        pass
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """매매 신호 생성"""
        pass
    
    @abstractmethod
    def calculate_weights(self, signals: List[Signal], 
                         current_portfolio: Optional[Dict[str, float]] = None) -> List[PortfolioWeight]:
        """포트폴리오 가중치 계산"""
        pass
    
    def _validate_parameters(self):
        """파라미터 검증"""
        required_params = self._get_required_parameters()
        for param in required_params:
            if param not in self.parameters:
                raise ValueError(f"Required parameter '{param}' is missing for strategy '{self.name}'")
    
    def _get_required_parameters(self) -> List[str]:
        """필수 파라미터 목록 반환"""
        return []
    
    def preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """데이터 전처리"""
        # 기본적인 데이터 정리
        data = data.copy()
        
        # 필수 컬럼 확인
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # 결측치 처리
        data = data.fillna(method='ffill').dropna()
        
        # 날짜 인덱스 설정
        if not isinstance(data.index, pd.DatetimeIndex):
            if 'date' in data.columns:
                data['date'] = pd.to_datetime(data['date'])
                data.set_index('date', inplace=True)
            else:
                self.logger.warning("No date column found, using existing index")
        
        return data
    
    def filter_universe(self, data: pd.DataFrame) -> pd.DataFrame:
        """투자 유니버스 필터링"""
        # 기본 필터링 조건
        filtered_data = data.copy()
        
        # 거래량 필터 (일평균 거래량이 너무 적은 종목 제외)
        min_volume = self.parameters.get('min_volume', 100000)
        if 'volume' in filtered_data.columns:
            avg_volume = filtered_data['volume'].rolling(20).mean()
            filtered_data = filtered_data[avg_volume > min_volume]
        
        # 가격 필터 (너무 저가주 제외)
        min_price = self.parameters.get('min_price', 1.0)
        if 'close' in filtered_data.columns:
            filtered_data = filtered_data[filtered_data['close'] > min_price]
        
        # 시가총액 필터 (설정된 경우)
        min_market_cap = self.parameters.get('min_market_cap')
        if min_market_cap and 'market_cap' in filtered_data.columns:
            filtered_data = filtered_data[filtered_data['market_cap'] > min_market_cap]
        
        return filtered_data
    
    def calculate_risk_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """리스크 지표 계산"""
        if len(returns) == 0:
            return {}
        
        # 기본 리스크 지표
        volatility = returns.std() * np.sqrt(252)  # 연율화
        max_drawdown = self._calculate_max_drawdown(returns)
        var_95 = returns.quantile(0.05)  # 5% VaR
        
        # 하방 위험 지표
        downside_returns = returns[returns < 0]
        downside_volatility = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
        
        return {
            'volatility': volatility,
            'max_drawdown': max_drawdown,
            'var_95': var_95,
            'downside_volatility': downside_volatility,
            'skewness': returns.skew(),
            'kurtosis': returns.kurtosis()
        }
    
    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """최대 낙폭 계산"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()
    
    def get_strategy_info(self) -> Dict:
        """전략 정보 반환"""
        return {
            'name': self.name,
            'metadata': self.metadata,
            'parameters': self.parameters,
            'required_data': self._get_required_data_columns(),
            'rebalancing_frequency': self.metadata.rebalancing_frequency
        }
    
    def _get_required_data_columns(self) -> List[str]:
        """필요한 데이터 컬럼 반환"""
        return ['open', 'high', 'low', 'close', 'volume']
    
    def validate_signals(self, signals: List[Signal]) -> List[Signal]:
        """신호 검증 및 필터링"""
        valid_signals = []
        
        for signal in signals:
            # 신호 강도 검증
            if not 0 <= signal.strength <= 1:
                self.logger.warning(f"Invalid signal strength for {signal.symbol}: {signal.strength}")
                continue
            
            # 신뢰도 검증
            if not 0 <= signal.confidence <= 1:
                self.logger.warning(f"Invalid signal confidence for {signal.symbol}: {signal.confidence}")
                continue
            
            # 신호 타입 검증
            if signal.signal_type not in ['BUY', 'SELL', 'HOLD']:
                self.logger.warning(f"Invalid signal type for {signal.symbol}: {signal.signal_type}")
                continue
            
            valid_signals.append(signal)
        
        return valid_signals
    
    def apply_position_sizing(self, weights: List[PortfolioWeight]) -> List[PortfolioWeight]:
        """포지션 사이징 적용"""
        # 최대 단일 종목 비중 제한
        max_single_weight = self.parameters.get('max_single_weight', 0.1)  # 10%
        
        adjusted_weights = []
        for weight in weights:
            adjusted_weight = min(weight.target_weight, max_single_weight)
            
            adjusted_weights.append(PortfolioWeight(
                symbol=weight.symbol,
                weight=adjusted_weight,
                target_weight=adjusted_weight,
                current_weight=weight.current_weight,
                rebalance_needed=abs(adjusted_weight - weight.current_weight) > 0.01
            ))
        
        # 가중치 정규화 (합계가 1.0이 되도록)
        total_weight = sum(w.weight for w in adjusted_weights)
        if total_weight > 0:
            for weight in adjusted_weights:
                weight.weight /= total_weight
                weight.target_weight /= total_weight
        
        return adjusted_weights
    
    def log_strategy_performance(self, signals: List[Signal], weights: List[PortfolioWeight]):
        """전략 성과 로깅"""
        buy_signals = len([s for s in signals if s.signal_type == 'BUY'])
        sell_signals = len([s for s in signals if s.signal_type == 'SELL'])
        total_positions = len([w for w in weights if w.weight > 0])
        
        self.logger.info(f"Strategy {self.name} - Buy: {buy_signals}, Sell: {sell_signals}, Positions: {total_positions}")

class StrategyFactory:
    """전략 팩토리 클래스"""
    
    _strategies = {}
    
    @classmethod
    def register_strategy(cls, strategy_name: str, strategy_class):
        """전략 등록"""
        cls._strategies[strategy_name] = strategy_class
    
    @classmethod
    def create_strategy(cls, strategy_name: str, **kwargs):
        """전략 생성"""
        if strategy_name not in cls._strategies:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        
        return cls._strategies[strategy_name](**kwargs)
    
    @classmethod
    def list_strategies(cls) -> List[str]:
        """등록된 전략 목록 반환"""
        return list(cls._strategies.keys())

# 유틸리티 함수들
def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
    """샤프 비율 계산"""
    if len(returns) == 0 or returns.std() == 0:
        return 0.0
    
    excess_returns = returns.mean() * 252 - risk_free_rate  # 연율화
    volatility = returns.std() * np.sqrt(252)
    
    return excess_returns / volatility

def calculate_sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
    """소르티노 비율 계산"""
    if len(returns) == 0:
        return 0.0
    
    excess_returns = returns.mean() * 252 - risk_free_rate
    downside_returns = returns[returns < 0]
    
    if len(downside_returns) == 0:
        return float('inf')
    
    downside_volatility = downside_returns.std() * np.sqrt(252)
    
    if downside_volatility == 0:
        return float('inf')
    
    return excess_returns / downside_volatility