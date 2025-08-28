"""
Investment Strategies Package - 개인투자자용 투자전략 20가지
패키지 초기화 및 주요 클래스/함수 export
"""

import logging
from typing import Dict, List, Optional, Any

# 패키지 정보
__version__ = "1.0.0"
__author__ = "Investment Strategy Engine"
__description__ = "20가지 개인투자자용 투자전략 백테스팅 엔진"

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 코어 모듈들 import
try:
    # 기본 전략 클래스
    from .base_strategy import (
        BaseStrategy, 
        StrategyMetadata, 
        Signal, 
        PortfolioWeight,
        RiskLevel,
        Complexity,
        StrategyCategory,
        calculate_sharpe_ratio,
        calculate_sortino_ratio
    )
    
    # 팩토리 및 매니저
    from .strategy_factory import (
        StrategyFactory,
        StrategyRegistry,
        StrategyManager,
        StrategyLoader,
        strategy_registry,
        create_strategy_combination,
        get_recommended_strategies,
        initialize_strategy_system
    )
    
    # 기술적 지표
    from .technical_indicators import (
        simple_moving_average,
        exponential_moving_average,
        rsi,
        macd,
        bollinger_bands,
        stochastic,
        atr as average_true_range,
        on_balance_volume,
        momentum,
        relative_strength
    )
    
    # 펀더멘털 지표
    from .fundamental_metrics import (
        price_to_earnings_ratio,
        price_to_book_ratio,
        return_on_equity,
        debt_to_equity_ratio,
        current_ratio,
        dividend_yield,
        piotroski_f_score,
        altman_z_score,
        calculate_quality_score
    )
    
    # 포트폴리오 유틸리티
    from .portfolio_utils import (
        equal_weight_portfolio,
        market_cap_weighted_portfolio,
        risk_parity_portfolio,
        minimum_variance_portfolio,
        calculate_rebalancing_trades,
        calculate_portfolio_metrics,
        efficient_frontier,
        kelly_criterion_weights
    )

except ImportError as e:
    logging.warning(f"Some modules could not be imported: {e}")

# 전략 모듈들 import (선택적)
try:
    from . import basic_strategies
    from . import value_strategies  
    from . import growth_momentum_strategies
    from . import cycle_contrarian_strategies
    
    # 전략 시스템 초기화
    initialize_strategy_system()
    
except ImportError as e:
    logging.warning(f"Strategy modules could not be loaded: {e}")

# 공개 API 정의
__all__ = [
    # 버전 정보
    "__version__",
    "__author__", 
    "__description__",
    
    # 코어 클래스들
    "BaseStrategy",
    "StrategyMetadata", 
    "Signal",
    "PortfolioWeight",
    "RiskLevel",
    "Complexity", 
    "StrategyCategory",
    
    # 팩토리 및 매니저
    "StrategyFactory",
    "StrategyRegistry",
    "StrategyManager", 
    "StrategyLoader",
    "strategy_registry",
    
    # 헬퍼 함수들
    "create_strategy_combination",
    "get_recommended_strategies",
    "initialize_strategy_system",
    
    # 기술적 지표 (주요)
    "simple_moving_average",
    "exponential_moving_average", 
    "rsi",
    "macd",
    "bollinger_bands",
    
    # 펀더멘털 지표 (주요)
    "price_to_earnings_ratio",
    "return_on_equity",
    "debt_to_equity_ratio",
    "calculate_quality_score",
    
    # 포트폴리오 함수 (주요)
    "equal_weight_portfolio",
    "risk_parity_portfolio",
    "calculate_portfolio_metrics",
    "kelly_criterion_weights",
    
    # 성과 측정 함수들
    "calculate_sharpe_ratio",
    "calculate_sortino_ratio"
]

# 패키지 레벨 편의 함수들
def get_strategy_list() -> List[str]:
    """사용 가능한 모든 전략 목록 반환"""
    try:
        return strategy_registry.list_strategies()
    except:
        return []

def create_strategy(strategy_name: str, **kwargs) -> Optional[BaseStrategy]:
    """전략 생성 편의 함수"""
    try:
        return strategy_registry.create_strategy(strategy_name, **kwargs)
    except Exception as e:
        logging.error(f"Failed to create strategy {strategy_name}: {e}")
        return None

def get_basic_strategies() -> List[str]:
    """기본 전략 10가지 목록"""
    basic_list = [
        "low_pe",
        "dividend_aristocrats", 
        "simple_momentum",
        "moving_average_cross",
        "rsi_mean_reversion",
        "bollinger_band",
        "small_cap",
        "low_volatility", 
        "quality_factor",
        "regular_rebalancing"
    ]
    available = get_strategy_list()
    return [s for s in basic_list if s in available]

def get_advanced_strategies() -> List[str]:
    """고급 전략 10가지 목록"""
    advanced_list = [
        "buffett_moat",
        "peter_lynch_peg", 
        "benjamin_graham_defensive",
        "joel_greenblatt_magic",
        "william_oneil_canslim",
        "howard_marks_cycle",
        "james_oshaughnessy",
        "ray_dalio_all_weather",
        "david_dreman_contrarian",
        "john_neff_low_pe_dividend"
    ]
    available = get_strategy_list()
    return [s for s in advanced_list if s in available]

def get_strategy_by_risk_level(risk_level: str) -> List[str]:
    """위험도별 전략 필터링"""
    try:
        return strategy_registry.search_strategies(risk_level=risk_level)
    except:
        return []

def get_strategy_by_complexity(complexity: str) -> List[str]:
    """복잡도별 전략 필터링"""
    try:
        return strategy_registry.search_strategies(complexity=complexity)
    except:
        return []

def print_package_info():
    """패키지 정보 출력"""
    total_strategies = len(get_strategy_list())
    basic_count = len(get_basic_strategies())  
    advanced_count = len(get_advanced_strategies())
    
    print(f"""
    ╔════════════════════════════════════════════════════════════╗
    ║           Investment Strategies Package v{__version__}           ║
    ║                                                            ║
    ║  개인투자자를 위한 20가지 투자전략 백테스팅 엔진                   ║
    ║                                                            ║
    ║  📊 전체 전략: {total_strategies}개                                      ║
    ║  📈 기본 전략: {basic_count}개                                      ║  
    ║  🎯 고급 전략: {advanced_count}개                                      ║
    ║                                                            ║
    ║  주요 기능:                                                  ║
    ║  • 기술적 지표 계산                                           ║
    ║  • 펀더멘털 분석                                             ║
    ║  • 포트폴리오 최적화                                          ║
    ║  • 백테스팅 & 성과 측정                                       ║
    ║                                                            ║
    ╚════════════════════════════════════════════════════════════╝
    """)

def quick_start_guide():
    """빠른 시작 가이드"""
    print("""
    🚀 Quick Start Guide:
    
    1. 전략 목록 확인:
       >>> import strategies
       >>> strategies.get_strategy_list()
    
    2. 전략 생성:
       >>> strategy = strategies.create_strategy('low_pe')
    
    3. 신호 생성:
       >>> signals = strategy.generate_signals(data)
    
    4. 포트폴리오 가중치:
       >>> weights = strategy.calculate_weights(signals)
    
    5. 추천 전략:
       >>> user_profile = {'risk_tolerance': 'medium', 'experience_level': 'beginner'}
       >>> recommended = strategies.get_recommended_strategies(user_profile)
    
    자세한 사용법은 각 전략의 메타데이터를 확인하세요.
    """)

# 패키지 로딩 완료 메시지
def _on_import():
    """패키지 import 시 실행"""
    total_strategies = len(get_strategy_list())
    if total_strategies > 0:
        logging.info(f"Investment Strategies Package v{__version__} loaded successfully with {total_strategies} strategies")
    else:
        logging.warning("Investment Strategies Package loaded but no strategies found")

# 패키지 import시 자동 실행
_on_import()

# 사용자 편의를 위한 별칭들
create = create_strategy
list_all = get_strategy_list
list_basic = get_basic_strategies
list_advanced = get_advanced_strategies
info = print_package_info
help = quick_start_guide

# 디버그 모드 설정
DEBUG = False

def set_debug_mode(enabled: bool = True):
    """디버그 모드 설정"""
    global DEBUG
    DEBUG = enabled
    log_level = logging.DEBUG if enabled else logging.INFO
    logging.getLogger().setLevel(log_level)
    
    if enabled:
        logging.info("Debug mode enabled")
    else:
        logging.info("Debug mode disabled") 
