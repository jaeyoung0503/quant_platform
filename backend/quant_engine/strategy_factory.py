"""
file: strategy_engine/strategy_factory.py
Strategy Factory Module - 전략 객체 생성 팩토리 패턴
전략 이름으로 해당 클래스 반환, 전략 관리 및 유틸리티 함수들
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Type, Any, Callable
import logging
import importlib
from base_strategy import BaseStrategy, StrategyCategory
from collections import defaultdict

class StrategyRegistry:
    """전략 레지스트리 - 모든 전략을 중앙 관리"""
    
    def __init__(self):
        self._strategies: Dict[str, Type[BaseStrategy]] = {}
        self._strategy_metadata: Dict[str, Dict] = {}
        self._categories: Dict[StrategyCategory, List[str]] = defaultdict(list)
        self.logger = logging.getLogger("StrategyRegistry")
    
    def register(self, strategy_name: str, strategy_class: Type[BaseStrategy]):
        """전략 등록"""
        if not issubclass(strategy_class, BaseStrategy):
            raise ValueError(f"Strategy class must inherit from BaseStrategy")
        
        self._strategies[strategy_name] = strategy_class
        
        # 메타데이터 저장 (인스턴스 생성 없이)
        try:
            temp_instance = strategy_class()
            metadata = temp_instance.get_strategy_info()
            self._strategy_metadata[strategy_name] = metadata
            
            # 카테고리별 분류
            category = metadata['metadata'].category
            if strategy_name not in self._categories[category]:
                self._categories[category].append(strategy_name)
            
        except Exception as e:
            self.logger.warning(f"Could not get metadata for {strategy_name}: {e}")
    
    def get_strategy_class(self, strategy_name: str) -> Type[BaseStrategy]:
        """전략 클래스 반환"""
        if strategy_name not in self._strategies:
            raise ValueError(f"Strategy '{strategy_name}' not found. Available strategies: {list(self._strategies.keys())}")
        
        return self._strategies[strategy_name]
    
    def create_strategy(self, strategy_name: str, **kwargs) -> BaseStrategy:
        """전략 인스턴스 생성"""
        strategy_class = self.get_strategy_class(strategy_name)
        return strategy_class(**kwargs)
    
    def list_strategies(self) -> List[str]:
        """등록된 전략 목록"""
        return list(self._strategies.keys())
    
    def list_strategies_by_category(self, category: StrategyCategory) -> List[str]:
        """카테고리별 전략 목록"""
        return self._categories.get(category, [])
    
    def get_strategy_metadata(self, strategy_name: str) -> Dict:
        """전략 메타데이터 반환"""
        if strategy_name not in self._strategy_metadata:
            # 메타데이터가 없으면 실시간 생성
            try:
                strategy = self.create_strategy(strategy_name)
                return strategy.get_strategy_info()
            except Exception as e:
                return {"error": str(e)}
        
        return self._strategy_metadata[strategy_name]
    
    def search_strategies(self, 
                         risk_level: Optional[str] = None,
                         complexity: Optional[str] = None,
                         category: Optional[StrategyCategory] = None,
                         min_expected_return: Optional[float] = None) -> List[str]:
        """조건별 전략 검색"""
        matching_strategies = []
        
        for strategy_name, metadata in self._strategy_metadata.items():
            strategy_meta = metadata.get('metadata')
            if not strategy_meta:
                continue
            
            # 조건 확인
            if risk_level and strategy_meta.risk_level.value != risk_level:
                continue
            
            if complexity and strategy_meta.complexity.value != complexity:
                continue
            
            if category and strategy_meta.category != category:
                continue
            
            # 예상 수익률 파싱 및 비교 (간단한 구현)
            if min_expected_return:
                expected_return_str = strategy_meta.expected_return
                try:
                    # "10-12%" 형태에서 하한값 추출
                    return_value = float(expected_return_str.split('-')[0].rstrip('%'))
                    if return_value < min_expected_return:
                        continue
                except:
                    continue
            
            matching_strategies.append(strategy_name)
        
        return matching_strategies

# 글로벌 레지스트리 인스턴스
strategy_registry = StrategyRegistry()

class StrategyFactory:
    """전략 팩토리 - 백워드 호환성을 위한 래퍼"""
    
    @staticmethod
    def register_strategy(strategy_name: str, strategy_class: Type[BaseStrategy]):
        """전략 등록"""
        strategy_registry.register(strategy_name, strategy_class)
    
    @staticmethod
    def create_strategy(strategy_name: str, **kwargs) -> BaseStrategy:
        """전략 생성"""
        return strategy_registry.create_strategy(strategy_name, **kwargs)
    
    @staticmethod
    def list_strategies() -> List[str]:
        """전략 목록"""
        return strategy_registry.list_strategies()

class StrategyManager:
    """전략 매니저 - 복수 전략 관리 및 포트폴리오 운영"""
    
    def __init__(self):
        self.strategies: Dict[str, BaseStrategy] = {}
        self.strategy_weights: Dict[str, float] = {}
        self.logger = logging.getLogger("StrategyManager")
    
    def add_strategy(self, name: str, strategy: BaseStrategy, weight: float = 1.0):
        """전략 추가"""
        if not isinstance(strategy, BaseStrategy):
            raise ValueError("Strategy must be an instance of BaseStrategy")
        
        self.strategies[name] = strategy
        self.strategy_weights[name] = weight
        
        # 가중치 정규화
        self._normalize_weights()
    
    def remove_strategy(self, name: str):
        """전략 제거"""
        if name in self.strategies:
            del self.strategies[name]
            del self.strategy_weights[name]
            self._normalize_weights()
    
    def _normalize_weights(self):
        """가중치 정규화"""
        total_weight = sum(self.strategy_weights.values())
        if total_weight > 0:
            for name in self.strategy_weights:
                self.strategy_weights[name] /= total_weight
    
    def generate_combined_signals(self, data: pd.DataFrame) -> List:
        """복수 전략의 신호 결합"""
        all_signals = []
        
        for name, strategy in self.strategies.items():
            try:
                signals = strategy.generate_signals(data)
                weight = self.strategy_weights[name]
                
                # 신호에 전략 가중치 적용
                for signal in signals:
                    signal.strength *= weight
                    signal.metadata = signal.metadata or {}
                    signal.metadata['strategy_name'] = name
                    signal.metadata['strategy_weight'] = weight
                
                all_signals.extend(signals)
                
            except Exception as e:
                self.logger.error(f"Error generating signals for strategy {name}: {e}")
        
        return all_signals
    
    def calculate_ensemble_weights(self, signals: List, 
                                  current_portfolio: Optional[Dict[str, float]] = None) -> List:
        """앙상블 가중치 계산"""
        # 종목별로 신호 그룹화
        symbol_signals = defaultdict(list)
        for signal in signals:
            symbol_signals[signal.symbol].append(signal)
        
        ensemble_weights = []
        
        for symbol, symbol_signal_list in symbol_signals.items():
            # 동일 종목에 대한 여러 전략 신호 결합
            combined_strength = sum(s.strength for s in symbol_signal_list)
            combined_confidence = np.mean([s.confidence for s in symbol_signal_list])
            
            # 가장 강한 신호의 타입 사용
            signal_type = max(symbol_signal_list, key=lambda x: x.strength).signal_type
            
            if combined_strength > 0:
                from base_strategy import PortfolioWeight
                current_weight = current_portfolio.get(symbol, 0.0) if current_portfolio else 0.0
                
                ensemble_weights.append(PortfolioWeight(
                    symbol=symbol,
                    weight=combined_strength,  # 임시값, 나중에 정규화
                    target_weight=combined_strength,
                    current_weight=current_weight
                ))
        
        # 가중치 정규화
        total_weight = sum(w.weight for w in ensemble_weights)
        if total_weight > 0:
            for weight in ensemble_weights:
                weight.weight /= total_weight
                weight.target_weight /= total_weight
        
        return ensemble_weights
    
    def get_strategy_performance(self, returns: pd.DataFrame) -> Dict[str, Dict]:
        """각 전략별 성과 평가"""
        performance = {}
        
        for name, strategy in self.strategies.items():
            try:
                signals = strategy.generate_signals(returns)
                weights = strategy.calculate_weights(signals)
                
                if weights:
                    # 간단한 백테스트
                    strategy_returns = self._calculate_strategy_returns(returns, weights)
                    
                    from portfolio_utils import calculate_portfolio_metrics
                    metrics = calculate_portfolio_metrics(strategy_returns)
                    
                    performance[name] = {
                        'metrics': metrics,
                        'weight': self.strategy_weights[name],
                        'signal_count': len(signals),
                        'position_count': len(weights)
                    }
                    
            except Exception as e:
                self.logger.error(f"Error evaluating strategy {name}: {e}")
                performance[name] = {'error': str(e)}
        
        return performance
    
    def _calculate_strategy_returns(self, returns: pd.DataFrame, weights: List) -> pd.Series:
        """전략별 수익률 계산 (간단 버전)"""
        if not weights:
            return pd.Series(dtype=float)
        
        # 가중치를 시리즈로 변환
        weight_dict = {w.symbol: w.weight for w in weights if w.symbol in returns.columns}
        weight_series = pd.Series(weight_dict)
        
        # 포트폴리오 수익률
        strategy_returns = (returns[weight_series.index] * weight_series).sum(axis=1)
        
        return strategy_returns

class StrategyLoader:
    """전략 동적 로딩"""
    
    @staticmethod
    def load_strategies_from_modules():
        """모든 전략 모듈에서 전략들을 자동 로드"""
        strategy_modules = [
            'basic_strategies',
            'value_strategies', 
            'growth_momentum_strategies',
            'cycle_contrarian_strategies'
        ]
        
        for module_name in strategy_modules:
            try:
                module = importlib.import_module(module_name)
                # 각 모듈의 register 함수 호출 (있다면)
                if hasattr(module, f'register_{module_name}'):
                    register_func = getattr(module, f'register_{module_name}')
                    register_func()
                    logging.info(f"Loaded strategies from {module_name}")
            except ImportError as e:
                logging.warning(f"Could not load strategy module {module_name}: {e}")
    
    @staticmethod
    def get_all_available_strategies() -> Dict[str, Dict]:
        """사용 가능한 모든 전략 정보"""
        strategies_info = {}
        
        for strategy_name in strategy_registry.list_strategies():
            metadata = strategy_registry.get_strategy_metadata(strategy_name)
            strategies_info[strategy_name] = metadata
        
        return strategies_info

def create_strategy_combination(strategy_configs: List[Dict[str, Any]]) -> StrategyManager:
    """전략 조합 생성 헬퍼 함수"""
    manager = StrategyManager()
    
    for config in strategy_configs:
        strategy_name = config['strategy']
        weight = config.get('weight', 1.0)
        params = config.get('parameters', {})
        
        try:
            strategy = strategy_registry.create_strategy(strategy_name, **params)
            manager.add_strategy(f"{strategy_name}_{len(manager.strategies)}", strategy, weight)
        except Exception as e:
            logging.error(f"Failed to create strategy {strategy_name}: {e}")
    
    return manager

def get_recommended_strategies(user_profile: Dict[str, Any]) -> List[str]:
    """사용자 프로필 기반 추천 전략"""
    risk_tolerance = user_profile.get('risk_tolerance', 'medium')  # low, medium, high
    experience_level = user_profile.get('experience_level', 'beginner')  # beginner, intermediate, advanced
    investment_horizon = user_profile.get('investment_horizon', 'medium')  # short, medium, long
    
    recommended = []
    
    # 초보자용 전략
    if experience_level == 'beginner':
        recommended.extend([
            'low_pe', 'dividend_aristocrats', 'regular_rebalancing',
            'benjamin_graham_defensive'
        ])
    
    # 중급자용 전략  
    elif experience_level == 'intermediate':
        recommended.extend([
            'rsi_mean_reversion', 'moving_average_cross', 'quality_factor',
            'joel_greenblatt_magic', 'john_neff_low_pe_dividend'
        ])
    
    # 고급자용 전략
    else:
        recommended.extend([
            'william_oneil_canslim', 'howard_marks_cycle', 'james_oshaughnessy',
            'buffett_moat', 'peter_lynch_peg'
        ])
    
    # 위험 선호도에 따른 필터링
    if risk_tolerance == 'low':
        safe_strategies = strategy_registry.search_strategies(risk_level='low')
        recommended = [s for s in recommended if s in safe_strategies]
    elif risk_tolerance == 'high':
        aggressive_strategies = strategy_registry.search_strategies(risk_level='high')
        recommended.extend(aggressive_strategies)
    
    # 중복 제거 및 존재하는 전략만 반환
    available_strategies = strategy_registry.list_strategies()
    recommended = list(set(recommended))
    recommended = [s for s in recommended if s in available_strategies]
    
    return recommended[:5]  # 최대 5개 전략 추천

# 모듈 로드시 자동 실행
def initialize_strategy_system():
    """전략 시스템 초기화"""
    StrategyLoader.load_strategies_from_modules()
    logging.info(f"Strategy system initialized with {len(strategy_registry.list_strategies())} strategies")

# 백워드 호환성을 위한 별칭
register_strategy = StrategyFactory.register_strategy
create_strategy = StrategyFactory.create_strategy
list_strategies = StrategyFactory.list_strategies 
