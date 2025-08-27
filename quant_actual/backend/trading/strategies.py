# file: backend/trading/strategies.py

import json
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from models import TradingSignal, OrderType, Strategy
from trading.indicators import TechnicalIndicators
from database import get_db_session

logger = logging.getLogger(__name__)

class BaseStrategy(ABC):
    """전략 베이스 클래스"""
    
    def __init__(self, strategy_config: Strategy):
        self.config = strategy_config
        self.name = strategy_config.name
        self.strategy_type = strategy_config.strategy_type
        self.target_stocks = json.loads(strategy_config.target_stocks)
        self.parameters = json.loads(strategy_config.parameters)
        self.indicators = TechnicalIndicators()
    
    @abstractmethod
    async def generate_signals(self, market_data: Dict[str, Any]) -> List[TradingSignal]:
        """매매 신호 생성 - 각 전략에서 구현"""
        pass
    
    def get_position_size(self, stock_code: str, current_price: float) -> int:
        """포지션 크기 계산"""
        try:
            investment_amount = self.config.investment_amount
            max_position_value = investment_amount * 0.3  # 전략 자금의 30%까지
            quantity = int(max_position_value / current_price / 100) * 100  # 100주 단위
            return max(100, quantity)  # 최소 100주
        except:
            return 100
    
    async def get_price_history(self, stock_code: str, days: int = 30) -> List[float]:
        """종목의 과거 가격 데이터 조회"""
        try:
            from models import Stock, PriceHistory
            
            with get_db_session() as db:
                stock = db.query(Stock).filter(Stock.code == stock_code).first()
                if not stock:
                    return []
                
                start_date = datetime.now() - timedelta(days=days)
                price_records = db.query(PriceHistory)\
                    .filter(PriceHistory.stock_id == stock.id)\
                    .filter(PriceHistory.timestamp >= start_date)\
                    .order_by(PriceHistory.timestamp)\
                    .all()
                
                return [record.price for record in price_records]
                
        except Exception as e:
            logger.error(f"가격 히스토리 조회 실패 {stock_code}: {e}")
            return []
    
    async def get_volume_history(self, stock_code: str, days: int = 5) -> List[int]:
        """종목의 과거 거래량 데이터 조회"""
        try:
            from models import Stock, PriceHistory
            
            with get_db_session() as db:
                stock = db.query(Stock).filter(Stock.code == stock_code).first()
                if not stock:
                    return []
                
                start_date = datetime.now() - timedelta(days=days)
                volume_records = db.query(PriceHistory)\
                    .filter(PriceHistory.stock_id == stock.id)\
                    .filter(PriceHistory.timestamp >= start_date)\
                    .order_by(PriceHistory.timestamp)\
                    .all()
                
                return [record.volume for record in volume_records if record.volume]
                
        except Exception as e:
            logger.error(f"거래량 히스토리 조회 실패 {stock_code}: {e}")
            return []
    
    async def get_current_position(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """현재 보유 포지션 조회"""
        try:
            from models import Position, Stock
            
            with get_db_session() as db:
                position = db.query(Position)\
                    .join(Stock)\
                    .filter(Stock.code == stock_code)\
                    .filter(Position.strategy_id == self.config.id)\
                    .filter(Position.quantity > 0)\
                    .first()
                
                if position:
                    return {
                        'quantity': position.quantity,
                        'avg_price': position.avg_price,
                        'current_price': position.current_price,
                        'unrealized_pnl': position.unrealized_pnl
                    }
                return None
                
        except Exception as e:
            logger.error(f"포지션 조회 실패 {stock_code}: {e}")
            return None
    
    def should_stop_loss(self, position: Dict[str, Any], current_price: float) -> bool:
        """손절 여부 판단"""
        try:
            stop_loss_rate = self.parameters.get('stop_loss', 0.05)  # 기본 5% 손절
            avg_price = position['avg_price']
            loss_rate = (avg_price - current_price) / avg_price
            
            return loss_rate >= stop_loss_rate
            
        except:
            return False
    
    def should_take_profit(self, position: Dict[str, Any], current_price: float) -> bool:
        """익절 여부 판단"""
        try:
            take_profit_rate = self.parameters.get('take_profit', 0.1)  # 기본 10% 익절
            avg_price = position['avg_price']
            profit_rate = (current_price - avg_price) / avg_price
            
            return profit_rate >= take_profit_rate
            
        except:
            return False

class BollingerBandStrategy(BaseStrategy):
    """볼린저밴드 평균회귀 전략"""
    
    async def generate_signals(self, market_data: Dict[str, Any]) -> List[TradingSignal]:
        signals = []
        
        for stock_code in self.target_stocks:
            try:
                if stock_code not in market_data:
                    continue
                
                current_data = market_data[stock_code]
                current_price = current_data['current_price']
                
                # 과거 가격 데이터 조회
                price_history = await self.get_price_history(stock_code, days=30)
                if len(price_history) < self.parameters.get('period', 20):
                    continue
                
                # 볼린저밴드 계산
                period = self.parameters.get('period', 20)
                std_multiplier = self.parameters.get('std_multiplier', 2.0)
                
                bb_result = self.indicators.bollinger_bands(
                    price_history, period, std_multiplier
                )
                
                if not bb_result:
                    continue
                
                upper_band = bb_result['upper'][-1]
                lower_band = bb_result['lower'][-1]
                middle_band = bb_result['middle'][-1]
                
                # 현재 포지션 확인
                current_position = await self.get_current_position(stock_code)
                
                # 매수 신호: 가격이 하단선 아래로 내려갔을 때
                if current_price <= lower_band and not current_position:
                    quantity = self.get_position_size(stock_code, current_price)
                    
                    signal = TradingSignal(
                        stock_code=stock_code,
                        strategy_name=self.name,
                        signal_type=OrderType.BUY,
                        quantity=quantity,
                        price=current_price,
                        confidence=self.calculate_confidence(current_price, lower_band, middle_band),
                        timestamp=datetime.now()
                    )
                    signals.append(signal)
                    
                    logger.info(f"볼린저밴드 매수 신호: {stock_code} @ {current_price}")
                
                # 매도 신호: 가격이 상단선 위로 올라갔을 때 또는 중간선 회귀
                elif current_position and (current_price >= upper_band or 
                    (current_price >= middle_band and self.should_take_profit(current_position, current_price))):
                    
                    signal = TradingSignal(
                        stock_code=stock_code,
                        strategy_name=self.name,
                        signal_type=OrderType.SELL,
                        quantity=current_position['quantity'],
                        price=current_price,
                        confidence=0.8,
                        timestamp=datetime.now()
                    )
                    signals.append(signal)
                    
                    logger.info(f"볼린저밴드 매도 신호: {stock_code} @ {current_price}")
                
                # 손절 체크
                elif current_position and self.should_stop_loss(current_position, current_price):
                    signal = TradingSignal(
                        stock_code=stock_code,
                        strategy_name=self.name,
                        signal_type=OrderType.SELL,
                        quantity=current_position['quantity'],
                        price=current_price,
                        confidence=0.9,  # 손절은 높은 확신도
                        timestamp=datetime.now()
                    )
                    signals.append(signal)
                    
                    logger.info(f"볼린저밴드 손절 신호: {stock_code} @ {current_price}")
                    
            except Exception as e:
                logger.error(f"볼린저밴드 전략 오류 {stock_code}: {e}")
        
        return signals
    
    def calculate_confidence(self, current_price: float, lower_band: float, middle_band: float) -> float:
        """신호의 신뢰도 계산"""
        # 하단선에서 멀수록 높은 신뢰도
        distance_ratio = (lower_band - current_price) / (middle_band - lower_band)
        return min(0.95, max(0.5, 0.7 + distance_ratio * 0.3))

class RSIReversalStrategy(BaseStrategy):
    """RSI 역추세 전략"""
    
    async def generate_signals(self, market_data: Dict[str, Any]) -> List[TradingSignal]:
        signals = []
        
        for stock_code in self.target_stocks:
            try:
                if stock_code not in market_data:
                    continue
                
                current_data = market_data[stock_code]
                current_price = current_data['current_price']
                
                # 과거 가격 데이터 조회
                price_history = await self.get_price_history(stock_code, days=30)
                rsi_period = self.parameters.get('period', 14)
                
                if len(price_history) < rsi_period + 1:
                    continue
                
                # RSI 계산
                rsi_values = self.indicators.rsi(price_history, rsi_period)
                if not rsi_values or len(rsi_values) == 0:
                    continue
                
                current_rsi = rsi_values[-1]
                oversold_level = self.parameters.get('oversold', 30)
                overbought_level = self.parameters.get('overbought', 70)
                
                # 현재 포지션 확인
                current_position = await self.get_current_position(stock_code)
                
                # 매수 신호: RSI가 과매도 영역에서 반등
                if (current_rsi <= oversold_level and 
                    len(rsi_values) >= 2 and rsi_values[-2] < rsi_values[-1] and
                    not current_position):
                    
                    quantity = self.get_position_size(stock_code, current_price)
                    
                    signal = TradingSignal(
                        stock_code=stock_code,
                        strategy_name=self.name,
                        signal_type=OrderType.BUY,
                        quantity=quantity,
                        price=current_price,
                        confidence=self.calculate_rsi_confidence(current_rsi, oversold_level),
                        timestamp=datetime.now()
                    )
                    signals.append(signal)
                    
                    logger.info(f"RSI 매수 신호: {stock_code} @ {current_price} (RSI: {current_rsi:.1f})")
                
                # 매도 신호: RSI가 과매수 영역에 진입
                elif (current_position and current_rsi >= overbought_level):
                    
                    signal = TradingSignal(
                        stock_code=stock_code,
                        strategy_name=self.name,
                        signal_type=OrderType.SELL,
                        quantity=current_position['quantity'],
                        price=current_price,
                        confidence=self.calculate_rsi_confidence(current_rsi, overbought_level, is_sell=True),
                        timestamp=datetime.now()
                    )
                    signals.append(signal)
                    
                    logger.info(f"RSI 매도 신호: {stock_code} @ {current_price} (RSI: {current_rsi:.1f})")
                
                # 손절 체크
                elif current_position and self.should_stop_loss(current_position, current_price):
                    signal = TradingSignal(
                        stock_code=stock_code,
                        strategy_name=self.name,
                        signal_type=OrderType.SELL,
                        quantity=current_position['quantity'],
                        price=current_price,
                        confidence=0.9,
                        timestamp=datetime.now()
                    )
                    signals.append(signal)
                    
                    logger.info(f"RSI 손절 신호: {stock_code} @ {current_price}")
                    
            except Exception as e:
                logger.error(f"RSI 전략 오류 {stock_code}: {e}")
        
        return signals
    
    def calculate_rsi_confidence(self, rsi_value: float, threshold: float, is_sell: bool = False) -> float:
        """RSI 기반 신뢰도 계산"""
        if is_sell:
            # 과매수 영역에서 높을수록 신뢰도 높음
            excess = max(0, rsi_value - threshold)
            return min(0.95, 0.6 + excess * 0.01)
        else:
            # 과매도 영역에서 낮을수록 신뢰도 높음
            excess = max(0, threshold - rsi_value)
            return min(0.95, 0.6 + excess * 0.01)

class MomentumStrategy(BaseStrategy):
    """모멘텀 추세추종 전략"""
    
    async def generate_signals(self, market_data: Dict[str, Any]) -> List[TradingSignal]:
        signals = []
        
        for stock_code in self.target_stocks:
            try:
                if stock_code not in market_data:
                    continue
                
                current_data = market_data[stock_code]
                current_price = current_data['current_price']
                volume = current_data.get('volume', 0)
                
                # 과거 가격 데이터 조회
                price_history = await self.get_price_history(stock_code, days=60)
                if len(price_history) < 30:
                    continue
                
                # MACD 계산
                short_period = self.parameters.get('short_period', 12)
                long_period = self.parameters.get('long_period', 26)
                signal_period = self.parameters.get('signal_period', 9)
                
                macd_result = self.indicators.macd(
                    price_history, short_period, long_period, signal_period
                )
                
                if not macd_result or len(macd_result['macd']) < 2:
                    continue
                
                current_macd = macd_result['macd'][-1]
                current_signal_line = macd_result['signal'][-1]
                prev_macd = macd_result['macd'][-2]
                prev_signal_line = macd_result['signal'][-2]
                
                # 현재 포지션 확인
                current_position = await self.get_current_position(stock_code)
                
                # 매수 신호: MACD가 시그널선을 상향돌파 + 거래량 증가
                if (current_macd > current_signal_line and 
                    prev_macd <= prev_signal_line and
                    not current_position and
                    await self.is_volume_increasing(stock_code, volume)):
                    
                    quantity = self.get_position_size(stock_code, current_price)
                    
                    signal = TradingSignal(
                        stock_code=stock_code,
                        strategy_name=self.name,
                        signal_type=OrderType.BUY,
                        quantity=quantity,
                        price=current_price,
                        confidence=self.calculate_momentum_confidence(macd_result, volume),
                        timestamp=datetime.now()
                    )
                    signals.append(signal)
                    
                    logger.info(f"모멘텀 매수 신호: {stock_code} @ {current_price}")
                
                # 매도 신호: MACD가 시그널선을 하향돌파
                elif (current_position and 
                      current_macd < current_signal_line and 
                      prev_macd >= prev_signal_line):
                    
                    signal = TradingSignal(
                        stock_code=stock_code,
                        strategy_name=self.name,
                        signal_type=OrderType.SELL,
                        quantity=current_position['quantity'],
                        price=current_price,
                        confidence=0.8,
                        timestamp=datetime.now()
                    )
                    signals.append(signal)
                    
                    logger.info(f"모멘텀 매도 신호: {stock_code} @ {current_price}")
                
                # 손절 체크
                elif current_position and self.should_stop_loss(current_position, current_price):
                    signal = TradingSignal(
                        stock_code=stock_code,
                        strategy_name=self.name,
                        signal_type=OrderType.SELL,
                        quantity=current_position['quantity'],
                        price=current_price,
                        confidence=0.9,
                        timestamp=datetime.now()
                    )
                    signals.append(signal)
                    
            except Exception as e:
                logger.error(f"모멘텀 전략 오류 {stock_code}: {e}")
        
        return signals
    
    async def is_volume_increasing(self, stock_code: str, current_volume: int) -> bool:
        """거래량 증가 확인"""
        try:
            # 최근 5일 평균 거래량과 비교
            volume_history = await self.get_volume_history(stock_code, days=5)
            if len(volume_history) < 3:
                return True  # 데이터 부족시 true
            
            avg_volume = sum(volume_history) / len(volume_history)
            return current_volume > avg_volume * 1.2  # 20% 이상 증가
            
        except:
            return True
    
    def calculate_momentum_confidence(self, macd_result: dict, volume: int) -> float:
        """모멘텀 신뢰도 계산"""
        try:
            # MACD 히스토그램의 강도와 거래량을 고려
            histogram = macd_result.get('histogram', [0])
            if len(histogram) > 0:
                current_histogram = abs(histogram[-1])
                base_confidence = 0.6
                histogram_bonus = min(0.3, current_histogram * 0.1)
                return base_confidence + histogram_bonus
            return 0.7
        except:
            return 0.7

class MovingAverageStrategy(BaseStrategy):
    """이동평균 골든크로스 전략"""
    
    async def generate_signals(self, market_data: Dict[str, Any]) -> List[TradingSignal]:
        signals = []
        
        for stock_code in self.target_stocks:
            try:
                if stock_code not in market_data:
                    continue
                
                current_data = market_data[stock_code]
                current_price = current_data['current_price']
                volume = current_data.get('volume', 0)
                
                # 과거 가격 데이터 조회
                price_history = await self.get_price_history(stock_code, days=40)
                short_ma_period = self.parameters.get('short_ma', 5)
                long_ma_period = self.parameters.get('long_ma', 20)
                
                if len(price_history) < long_ma_period + 1:
                    continue
                
                # 이동평균 계산
                short_ma = self.indicators.moving_average(price_history, short_ma_period)
                long_ma = self.indicators.moving_average(price_history, long_ma_period)
                
                if len(short_ma) < 2 or len(long_ma) < 2:
                    continue
                
                current_short_ma = short_ma[-1]
                current_long_ma = long_ma[-1]
                prev_short_ma = short_ma[-2]
                prev_long_ma = long_ma[-2]
                
                # 현재 포지션 확인
                current_position = await self.get_current_position(stock_code)
                
                # 골든크로스: 단기 이동평균이 장기 이동평균을 상향돌파
                if (current_short_ma > current_long_ma and 
                    prev_short_ma <= prev_long_ma and
                    not current_position and
                    volume > self.parameters.get('volume_threshold', 1000000)):
                    
                    quantity = self.get_position_size(stock_code, current_price)
                    
                    signal = TradingSignal(
                        stock_code=stock_code,
                        strategy_name=self.name,
                        signal_type=OrderType.BUY,
                        quantity=quantity,
                        price=current_price,
                        confidence=self.calculate_ma_confidence(current_price, current_short_ma, current_long_ma),
                        timestamp=datetime.now()
                    )
                    signals.append(signal)
                    
                    logger.info(f"골든크로스 매수 신호: {stock_code} @ {current_price}")
                
                # 데드크로스: 단기 이동평균이 장기 이동평균을 하향돌파
                elif (current_position and 
                      current_short_ma < current_long_ma and 
                      prev_short_ma >= prev_long_ma):
                    
                    signal = TradingSignal(
                        stock_code=stock_code,
                        strategy_name=self.name,
                        signal_type=OrderType.SELL,
                        quantity=current_position['quantity'],
                        price=current_price,
                        confidence=0.8,
                        timestamp=datetime.now()
                    )
                    signals.append(signal)
                    
                    logger.info(f"데드크로스 매도 신호: {stock_code} @ {current_price}")
                
                # 손절 체크
                elif current_position and self.should_stop_loss(current_position, current_price):
                    signal = TradingSignal(
                        stock_code=stock_code,
                        strategy_name=self.name,
                        signal_type=OrderType.SELL,
                        quantity=current_position['quantity'],
                        price=current_price,
                        confidence=0.9,
                        timestamp=datetime.now()
                    )
                    signals.append(signal)
                    
            except Exception as e:
                logger.error(f"이동평균 전략 오류 {stock_code}: {e}")
        
        return signals
    
    def calculate_ma_confidence(self, current_price: float, short_ma: float, long_ma: float) -> float:
        """이동평균 기반 신뢰도 계산"""
        # 현재가가 두 이동평균보다 높고, 이동평균간 간격이 클수록 신뢰도 높음
        if current_price > short_ma > long_ma:
            gap_ratio = (short_ma - long_ma) / long_ma
            return min(0.95, 0.6 + gap_ratio * 10)
        return 0.5

class StrategyManager:
    """전략 관리자"""
    
    def __init__(self):
        self.strategies = {}
        
    async def initialize(self):
        """전략 매니저 초기화"""
        try:
            # 데이터베이스에서 활성 전략 로드
            with get_db_session() as db:
                active_strategies = db.query(Strategy).filter(Strategy.is_active == True).all()
                
                for strategy_config in active_strategies:
                    strategy = self.create_strategy(strategy_config)
                    if strategy:
                        self.strategies[strategy_config.id] = strategy
                        logger.info(f"전략 초기화: {strategy_config.name}")
            
        except Exception as e:
            logger.error(f"전략 매니저 초기화 실패: {e}")
            raise
    
    def create_strategy(self, strategy_config: Strategy) -> Optional[BaseStrategy]:
        """전략 타입에 따른 전략 인스턴스 생성"""
        try:
            strategy_map = {
                "bollinger_bands": BollingerBandStrategy,
                "rsi_reversal": RSIReversalStrategy,
                "momentum": MomentumStrategy,
                "moving_average": MovingAverageStrategy
            }
            
            strategy_class = strategy_map.get(strategy_config.strategy_type)
            if strategy_class:
                return strategy_class(strategy_config)
            else:
                logger.warning(f"알 수 없는 전략 타입: {strategy_config.strategy_type}")
                return None
                
        except Exception as e:
            logger.error(f"전략 생성 실패 {strategy_config.name}: {e}")
            return None
    
    async def generate_signals(self, strategy_id: int, market_data: Dict[str, Any]) -> List[TradingSignal]:
        """특정 전략의 신호 생성"""
        try:
            if strategy_id not in self.strategies:
                return []
            
            strategy = self.strategies[strategy_id]
            signals = await strategy.generate_signals(market_data)
            
            return signals
            
        except Exception as e:
            logger.error(f"신호 생성 실패 {strategy_id}: {e}")
            return []
    
    async def add_strategy(self, strategy_config: Strategy):
        """새 전략 추가"""
        strategy = self.create_strategy(strategy_config)
        if strategy:
            self.strategies[strategy_config.id] = strategy
            logger.info(f"새 전략 추가: {strategy_config.name}")
    
    async def remove_strategy(self, strategy_id: int):
        """전략 제거"""
        if strategy_id in self.strategies:
            strategy_name = self.strategies[strategy_id].name
            del self.strategies[strategy_id]
            logger.info(f"전략 제거: {strategy_name}")
    
    async def update_strategy(self, strategy_config: Strategy):
        """전략 업데이트"""
        # 기존 전략 제거 후 새로 추가
        await self.remove_strategy(strategy_config.id)
        await self.add_strategy(strategy_config)