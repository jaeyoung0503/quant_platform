"""
file: quant_mvp/strategies/strategy_combiner.py
전략 조합 및 관리 클래스
"""

from typing import Dict, List, Any, Optional
import logging

from .base_strategy import BaseStrategy, Signal
from .technical_strategies import (
    MomentumStrategy, RSIStrategy, BollingerBandsStrategy, 
    MACDStrategy, MeanReversionStrategy
)
from .fundamental_strategies import (
    ValueStrategy, QualityStrategy, GrowthStrategy, DividendStrategy
)
from .hybrid_strategies import GARPStrategy, MomentumValueStrategy
from typing import Dict, List, Any, Tuple, Optional

logger = logging.getLogger(__name__)

class CombinedStrategy(BaseStrategy):
    """여러 전략을 조합한 전략"""
    
    def __init__(self, strategies: List[Dict[str, Any]], name: str = "Combined"):
        super().__init__(name)
        self.strategies = strategies
        self.total_weight = sum(s['weight'] for s in strategies)
        
        # 가중치 정규화
        if self.total_weight != 1.0:
            for strategy in self.strategies:
                strategy['weight'] = strategy['weight'] / self.total_weight
            self.total_weight = 1.0
    
    def get_required_data(self) -> List[str]:
        """필요한 데이터 컬럼 수집"""
        required_cols = set()
        for strategy_info in self.strategies:
            strategy = strategy_info['strategy']
            required_cols.update(strategy.get_required_data())
        return list(required_cols)
    
    def generate_signals(self, data) -> List[Signal]:
        """조합된 전략 신호 생성"""
        all_signals = []
        
        for strategy_info in self.strategies:
            strategy = strategy_info['strategy']
            weight = strategy_info['weight']
            name = strategy_info['name']
            
            try:
                # 개별 전략 신호 생성
                strategy_signals = strategy.generate_signals(data)
                
                # 가중치 적용
                for signal in strategy_signals:
                    signal.weight *= weight
                    signal.reason = f"[{name}] {signal.reason}"
                    all_signals.append(signal)
                    
            except Exception as e:
                logger.error(f"Error generating signals for {name}: {e}")
                continue
        
        # 신호 통합 및 정리
        combined_signals = self._combine_signals(all_signals)
        return combined_signals
    
    def _combine_signals(self, signals: List[Signal]) -> List[Signal]:
        """신호 통합"""
        if not signals:
            return []
        
        # 심볼별로 신호 그룹화
        symbol_signals = {}
        for signal in signals:
            if signal.symbol not in symbol_signals:
                symbol_signals[signal.symbol] = []
            symbol_signals[signal.symbol].append(signal)
        
        combined_signals = []
        
        for symbol, symbol_signal_list in symbol_signals.items():
            if not symbol_signal_list:
                continue
            
            # 같은 심볼에 대한 여러 신호를 하나로 통합
            total_weight = sum(s.weight for s in symbol_signal_list)
            avg_confidence = sum(s.confidence * s.weight for s in symbol_signal_list) / total_weight if total_weight > 0 else 0
            
            # 대표 신호 생성
            representative_signal = symbol_signal_list[0]
            reasons = [s.reason for s in symbol_signal_list]
            
            combined_signal = Signal(
                symbol=symbol,
                action='buy',  # 현재는 매수만 지원
                weight=total_weight,
                price=representative_signal.price,
                timestamp=representative_signal.timestamp,
                confidence=avg_confidence,
                reason="; ".join(reasons)
            )
            
            combined_signals.append(combined_signal)
        
        # 가중치 정규화
        total_combined_weight = sum(s.weight for s in combined_signals)
        if total_combined_weight > 0:
            for signal in combined_signals:
                signal.weight = signal.weight / total_combined_weight
        
        return combined_signals

class StrategyCombiner:
    """전략 조합기 클래스"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._strategy_registry = self._build_strategy_registry()
    
    def _build_strategy_registry(self) -> Dict[str, Dict[str, Any]]:
        """전략 레지스트리 구축"""
        return {
            "기술적 분석": {
                "Momentum": {
                    "class": MomentumStrategy,
                    "description": "과거 수익률 기반 모멘텀 전략"
                },
                "RSI": {
                    "class": RSIStrategy,
                    "description": "상대강도지수 기반 역추세 전략"
                },
                "BollingerBands": {
                    "class": BollingerBandsStrategy,
                    "description": "볼린저밴드 기반 평균회귀 전략"
                },
                "MACD": {
                    "class": MACDStrategy,
                    "description": "MACD 기반 추세추종 전략"
                },
                "MeanReversion": {
                    "class": MeanReversionStrategy,
                    "description": "통계적 평균회귀 전략"
                }
            },
            "재무 기반": {
                "Value": {
                    "class": ValueStrategy,
                    "description": "PER, PBR 기반 가치투자 전략"
                },
                "Quality": {
                    "class": QualityStrategy,
                    "description": "ROE, ROA 기반 퀄리티 전략"
                },
                "Growth": {
                    "class": GrowthStrategy,
                    "description": "매출/이익 성장률 기반 성장투자"
                },
                "Dividend": {
                    "class": DividendStrategy,
                    "description": "배당수익률 기반 배당투자"
                }
            },
            "혼합 전략": {
                "GARP": {
                    "class": GARPStrategy,
                    "description": "합리적 가격의 성장주 전략"
                },
                "MomentumValue": {
                    "class": MomentumValueStrategy,
                    "description": "모멘텀과 가치투자 결합 전략"
                }
            }
        }
    
    def get_available_strategies(self) -> Dict[str, Dict[str, Any]]:
        """사용 가능한 전략 목록 반환"""
        return self._strategy_registry
    
    def create_strategy(self, strategy_name: str, params: Dict[str, Any] = None) -> Optional[BaseStrategy]:
        """전략 인스턴스 생성"""
        try:
            # 전략 클래스 찾기
            strategy_class = None
            for category, strategies in self._strategy_registry.items():
                if strategy_name in strategies:
                    strategy_class = strategies[strategy_name]["class"]
                    break
            
            if strategy_class is None:
                logger.error(f"Strategy not found: {strategy_name}")
                return None
            
            # 전략 인스턴스 생성
            strategy_instance = strategy_class(params)
            logger.info(f"Created strategy: {strategy_name}")
            
            return strategy_instance
            
        except Exception as e:
            logger.error(f"Error creating strategy {strategy_name}: {e}")
            return None
    
    def combine_strategies(self, strategy_instances: List[Dict[str, Any]]) -> Optional[CombinedStrategy]:
        """전략들을 조합"""
        try:
            if not strategy_instances:
                logger.error("No strategies provided for combination")
                return None
            
            # 가중치 검증
            total_weight = sum(s['weight'] for s in strategy_instances)
            if abs(total_weight - 1.0) > 0.01:
                logger.warning(f"Total weight {total_weight} != 1.0, normalizing...")
            
            # 조합 전략 생성
            combined = CombinedStrategy(
                strategy_instances, 
                name=f"Combined_{len(strategy_instances)}_Strategies"
            )
            
            logger.info(f"Combined {len(strategy_instances)} strategies")
            return combined
            
        except Exception as e:
            logger.error(f"Error combining strategies: {e}")
            return None
    
    def validate_strategy_combination(self, strategies: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """전략 조합 유효성 검사"""
        try:
            if not strategies:
                return False, "전략이 선택되지 않았습니다"
            
            # 가중치 검사
            total_weight = sum(s.get('weight', 0) for s in strategies)
            if total_weight <= 0:
                return False, "총 가중치가 0보다 작거나 같습니다"
            
            # 전략 이름 중복 검사
            strategy_names = [s.get('name', '') for s in strategies]
            if len(strategy_names) != len(set(strategy_names)):
                return False, "중복된 전략이 있습니다"
            
            # 각 전략이 유효한지 검사
            for strategy in strategies:
                strategy_name = strategy.get('name', '')
                if not self._is_valid_strategy_name(strategy_name):
                    return False, f"유효하지 않은 전략: {strategy_name}"
                
                weight = strategy.get('weight', 0)
                if weight <= 0 or weight > 1:
                    return False, f"유효하지 않은 가중치: {weight}"
            
            return True, "유효한 전략 조합입니다"
            
        except Exception as e:
            return False, f"검증 중 오류: {e}"
    
    def _is_valid_strategy_name(self, strategy_name: str) -> bool:
        """전략 이름 유효성 검사"""
        for category, strategies in self._strategy_registry.items():
            if strategy_name in strategies:
                return True
        return False
    
    def get_strategy_info(self, strategy_name: str) -> Optional[Dict[str, Any]]:
        """전략 정보 조회"""
        for category, strategies in self._strategy_registry.items():
            if strategy_name in strategies:
                info = strategies[strategy_name].copy()
                info['category'] = category
                return info
        return None
    
    def suggest_strategy_combinations(self) -> List[Dict[str, Any]]:
        """추천 전략 조합"""
        suggestions = [
            {
                "name": "보수적 포트폴리오",
                "description": "안정적인 수익 추구, 낮은 변동성",
                "strategies": [
                    {"name": "Value", "weight": 0.4},
                    {"name": "Quality", "weight": 0.3},
                    {"name": "Dividend", "weight": 0.3}
                ]
            },
            {
                "name": "균형 포트폴리오",
                "description": "기술적 분석과 펀더멘털 분석의 균형",
                "strategies": [
                    {"name": "Momentum", "weight": 0.25},
                    {"name": "Value", "weight": 0.25},
                    {"name": "Quality", "weight": 0.25},
                    {"name": "Growth", "weight": 0.25} ]
            },
            {
                "name": "공격적 포트폴리오",
                "description": "높은 수익 추구, 높은 변동성 감수",
                "strategies": [
                    {"name": "Momentum", "weight": 0.3},
                    {"name": "Growth", "weight": 0.3},
                    {"name": "RSI", "weight": 0.2},
                    {"name": "MACD", "weight": 0.2}
                ]
            },
            {
                "name": "기술적 분석 중심",
                "description": "차트와 기술 지표 기반 단기 매매",
                "strategies": [
                    {"name": "RSI", "weight": 0.3},
                    {"name": "MACD", "weight": 0.25},
                    {"name": "BollingerBands", "weight": 0.25},
                    {"name": "Momentum", "weight": 0.2}
                ]
            },
            {
                "name": "가치 중심 장기투자",
                "description": "저평가된 우량주 중심 장기 보유",
                "strategies": [
                    {"name": "Value", "weight": 0.5},
                    {"name": "Quality", "weight": 0.3},
                    {"name": "Dividend", "weight": 0.2}
                ]
            }
        ]
        
        return suggestions