"""
File: backtester/strategies/__init__.py
Strategy Module Initialization - Fixed Version
"""

# Base strategy
from .base_strategy import BaseStrategy

# Fundamental ratio strategies (실제 구현된 파일)
from .fundamental_ratio_strategies import (
    PERStrategy, PBRStrategy, ROEStrategy, 
    DebtEquityStrategy, PEGStrategy
)

# Technical indicator strategies (실제 구현된 파일)
try:
    from .technical_indicator_strategies import (
        MovingAverageStrategy, RSIStrategy
    )
    # Optional imports - 구현되지 않은 경우 None으로 설정
    try:
        from .technical_indicator_strategies import BollingerBandStrategy
    except ImportError:
        BollingerBandStrategy = None
    
    try:
        from .technical_indicator_strategies import MACDStrategy
    except ImportError:
        MACDStrategy = None
        
    try:
        from .technical_indicator_strategies import VolatilityStrategy
    except ImportError:
        VolatilityStrategy = None
        
except ImportError as e:
    print(f"Warning: Could not import technical strategies: {e}")
    MovingAverageStrategy = None
    RSIStrategy = None
    BollingerBandStrategy = None
    MACDStrategy = None
    VolatilityStrategy = None

# Composite strategies (실제 구현된 파일)
from .composite_top10_strategy import (
    Top10CompositeStrategy, AdaptiveTop10Strategy, 
    Top10SectorRotationStrategy
)

# 향후 구현 예정인 전략들은 주석 처리
# from .momentum_strategies import BasicMomentumStrategy, QuantMomentumStrategy
# from .mean_reversion_strategies import BasicMeanReversionStrategy, StatisticalArbitrageStrategy
# from .value_strategies import WarrenBuffettStrategy, BenjaminGrahamStrategy
# from .growth_strategies import PeterLynchStrategy
# from .macro_strategies import RayDalioStrategy, GeorgeSorosStrategy
# from .pairs_strategies import PairsTradeStrategy
# from .remaining_strategies import (
#     FactorModelStrategy, VolatilityTargetingStrategy, CalendarAnomalyStrategy,
#     BreakoutStrategy, MachineLearningStrategy, EventDrivenStrategy,
#     CarryTradeStrategy, RiskParityStrategy, ContrariannStrategy
# )

__all__ = [
    # Base strategy
    'BaseStrategy',
    
    # Fundamental strategies (실제 구현됨)
    'PERStrategy',
    'PBRStrategy', 
    'ROEStrategy',
    'DebtEquityStrategy',
    'PEGStrategy',
    
    # Technical strategies (구현된 것만)
    'MovingAverageStrategy',
    'RSIStrategy',
    
    # Composite strategies (실제 구현됨)
    'Top10CompositeStrategy',
    'AdaptiveTop10Strategy',
    'Top10SectorRotationStrategy',
    
    # 향후 구현 예정 (주석 처리)
    # 'BollingerBandStrategy',
    # 'MACDStrategy', 
    # 'VolatilityStrategy',
    # 'BasicMomentumStrategy',
    # 'BasicMeanReversionStrategy', 
    # 'WarrenBuffettStrategy',
    # 'BenjaminGrahamStrategy',
    # 'PeterLynchStrategy',
    # 'RayDalioStrategy',
    # 'GeorgeSorosStrategy',
    # 'PairsTradeStrategy',
    # 'FactorModelStrategy',
    # 'VolatilityTargetingStrategy',
    # 'CalendarAnomalyStrategy',
    # 'BreakoutStrategy',
    # 'MachineLearningStrategy',
    # 'StatisticalArbitrageStrategy',
    # 'EventDrivenStrategy',
    # 'QuantMomentumStrategy',
    # 'CarryTradeStrategy',
    # 'RiskParityStrategy',
    # 'ContrariannStrategy',
    # 'CompositeValueStrategy'
]

# 전략 카테고리별 그룹화
FUNDAMENTAL_STRATEGIES = [
    'PERStrategy', 'PBRStrategy', 'ROEStrategy', 
    'DebtEquityStrategy', 'PEGStrategy'
]

TECHNICAL_STRATEGIES = [
    'MovingAverageStrategy', 'RSIStrategy'
    # 향후 추가 예정: 'BollingerBandStrategy', 'MACDStrategy', 'VolatilityStrategy'
]

COMPOSITE_STRATEGIES = [
    'Top10CompositeStrategy', 'AdaptiveTop10Strategy', 
    'Top10SectorRotationStrategy'
]

# 전략 팩토리 함수
def get_strategy_by_name(strategy_name: str):
    """전략 이름으로 전략 인스턴스 생성"""
    strategy_map = {
        # Fundamental strategies
        'PER': PERStrategy,
        'PBR': PBRStrategy,
        'ROE': ROEStrategy,
        'Debt': DebtEquityStrategy,
        'PEG': PEGStrategy,
        
        # Technical strategies  
        'MA': MovingAverageStrategy,
        'RSI': RSIStrategy,
        'BB': BollingerBandStrategy,
        'MACD': MACDStrategy,
        'VOL': VolatilityStrategy,
        
        # Composite strategies
        'TOP10': Top10CompositeStrategy,
        'ADAPTIVE_TOP10': AdaptiveTop10Strategy,
        'SECTOR_TOP10': Top10SectorRotationStrategy,
    }
    
    if strategy_name.upper() in strategy_map:
        return strategy_map[strategy_name.upper()]()
    else:
        raise ValueError(f"Strategy '{strategy_name}' not found. Available strategies: {list(strategy_map.keys())}")

def list_available_strategies():
    """사용 가능한 전략 목록 반환"""
    return {
        'fundamental': FUNDAMENTAL_STRATEGIES,
        'technical': TECHNICAL_STRATEGIES,
        'composite': COMPOSITE_STRATEGIES
    }

def get_all_strategies():
    """모든 구현된 전략 인스턴스 리스트 반환"""
    strategies = []
    
    # Fundamental strategies
    strategies.extend([
        PERStrategy(), PBRStrategy(), ROEStrategy(),
        DebtEquityStrategy(), PEGStrategy()
    ])
    
    # Technical strategies (구현된 것만)
    strategies.extend([
        MovingAverageStrategy(), RSIStrategy()
    ])
    
    # 구현된 경우만 추가
    if BollingerBandStrategy:
        strategies.append(BollingerBandStrategy())
    if MACDStrategy:
        strategies.append(MACDStrategy())
    if VolatilityStrategy:
        strategies.append(VolatilityStrategy())
    
    # Composite strategies
    strategies.extend([
        Top10CompositeStrategy(), AdaptiveTop10Strategy(),
        Top10SectorRotationStrategy()
    ])
    
    return strategies