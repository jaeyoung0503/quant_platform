"""
file: quant_mvp/backtesting/portfolip.py
포트폴리오 관리 클래스
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

@dataclass
class Trade:
    """거래 기록"""
    date: datetime
    symbol: str
    action: str  # 'buy', 'sell'
    shares: int
    price: float
    total_value: float
    commission: float
    reason: str = ""

@dataclass
class Position:
    """포지션 정보"""
    symbol: str
    shares: int
    avg_cost: float
    current_price: float = 0.0
    market_value: float = 0.0
    unrealized_pnl: float = 0.0
    weight: float = 0.0

class Portfolio:
    """포트폴리오 관리 클래스"""
    
    def __init__(self, initial_cash: float, config: Dict[str, Any]):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.config = config
        
        # 포지션 관리
        self.positions: Dict[str, Position] = {}
        
        # 거래 기록
        self.trade_history: List[Trade] = []
        
        # 포트폴리오 히스토리
        self.value_history: List[Dict[str, Any]] = []
        
        # 설정
        self.transaction_cost = config.get('portfolio', {}).get('transaction_cost', 0.001)
        self.max_positions = config.get('portfolio', {}).get('max_positions', 20)
        self.max_position_size = config.get('portfolio', {}).get('max_position_size', 0.1)
        self.min_position_size = config.get('portfolio', {}).get('min_position_size', 0.02)
    
    def get_total_value(self, current_prices: Dict[str, float]) -> float:
        """총 포트폴리오 가치 계산"""
        total_value = self.cash
        
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                market_value = position.shares * current_prices[symbol]
                total_value += market_value
        
        return total_value
    
    def update_positions(self, current_prices: Dict[str, float]):
        """포지션 정보 업데이트"""
        total_value = self.get_total_value(current_prices)
        
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                position.current_price = current_prices[symbol]
                position.market_value = position.shares * position.current_price
                position.unrealized_pnl = position.market_value - (position.shares * position.avg_cost)
                position.weight = position.market_value / total_value if total_value > 0 else 0
    
    def buy(self, symbol: str, shares: int, price: float, reason: str = "") -> bool:
        """주식 매수"""
        try:
            total_cost = shares * price
            commission = total_cost * self.transaction_cost
            total_with_commission = total_cost + commission
            
            # 현금 부족 검사
            if total_with_commission > self.cash:
                available_shares = int(self.cash / (price * (1 + self.transaction_cost)))
                if available_shares <= 0:
                    logger.warning(f"Insufficient cash to buy {symbol}")
                    return False
                shares = available_shares
                total_cost = shares * price
                commission = total_cost * self.transaction_cost
                total_with_commission = total_cost + commission
            
            # 현금 차감
            self.cash -= total_with_commission
            
            # 포지션 업데이트
            if symbol in self.positions:
                # 기존 포지션에 추가
                old_position = self.positions[symbol]
                total_shares = old_position.shares + shares
                total_cost_basis = (old_position.shares * old_position.avg_cost) + total_cost
                new_avg_cost = total_cost_basis / total_shares
                
                self.positions[symbol] = Position(
                    symbol=symbol,
                    shares=total_shares,
                    avg_cost=new_avg_cost,
                    current_price=price
                )
            else:
                # 새로운 포지션
                self.positions[symbol] = Position(
                    symbol=symbol,
                    shares=shares,
                    avg_cost=price,
                    current_price=price
                )
            
            # 거래 기록
            trade = Trade(
                date=datetime.now(),
                symbol=symbol,
                action='buy',
                shares=shares,
                price=price,
                total_value=total_cost,
                commission=commission,
                reason=reason
            )
            self.trade_history.append(trade)
            
            logger.info(f"Bought {shares} shares of {symbol} at ${price:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"Error buying {symbol}: {e}")
            return False
    
    def sell(self, symbol: str, shares: int, price: float, reason: str = "") -> bool:
        """주식 매도"""
        try:
            if symbol not in self.positions:
                logger.warning(f"No position in {symbol} to sell")
                return False
            
            position = self.positions[symbol]
            if shares > position.shares:
                logger.warning(f"Trying to sell {shares} shares but only have {position.shares}")
                shares = position.shares
            
            if shares <= 0:
                return False
            
            total_proceeds = shares * price
            commission = total_proceeds * self.transaction_cost
            net_proceeds = total_proceeds - commission
            
            # 현금 증가
            self.cash += net_proceeds
            
            # 포지션 업데이트
            if shares == position.shares:
                # 전량 매도
                del self.positions[symbol]
            else:
                # 부분 매도
                self.positions[symbol] = Position(
                    symbol=symbol,
                    shares=position.shares - shares,
                    avg_cost=position.avg_cost,
                    current_price=price
                )
            
            # 거래 기록
            trade = Trade(
                date=datetime.now(),
                symbol=symbol,
                action='sell',
                shares=shares,
                price=price,
                total_value=total_proceeds,
                commission=commission,
                reason=reason
            )
            self.trade_history.append(trade)
            
            logger.info(f"Sold {shares} shares of {symbol} at ${price:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"Error selling {symbol}: {e}")
            return False
    
    def rebalance_to_target(self, target_positions: Dict[str, int], current_prices: Dict[str, float]):
        """목표 포지션으로 리밸런싱"""
        try:
            # 현재 포지션과 목표 포지션 비교
            current_symbols = set(self.positions.keys())
            target_symbols = set(target_positions.keys())
            
            # 매도할 포지션들 (목표에 없거나 줄여야 할 포지션)
            for symbol in current_symbols:
                current_shares = self.positions[symbol].shares
                target_shares = target_positions.get(symbol, 0)
                
                if target_shares < current_shares:
                    shares_to_sell = current_shares - target_shares
                    if symbol in current_prices and shares_to_sell > 0:
                        self.sell(symbol, shares_to_sell, current_prices[symbol], "Rebalancing")
            
            # 매수할 포지션들 (새로 추가하거나 늘려야 할 포지션)
            for symbol in target_symbols:
                current_shares = self.positions.get(symbol, Position(symbol, 0, 0)).shares
                target_shares = target_positions[symbol]
                
                if target_shares > current_shares:
                    shares_to_buy = target_shares - current_shares
                    if symbol in current_prices and shares_to_buy > 0:
                        self.buy(symbol, shares_to_buy, current_prices[symbol], "Rebalancing")
            
        except Exception as e:
            logger.error(f"Error rebalancing portfolio: {e}")
    
    def get_current_positions(self) -> Dict[str, int]:
        """현재 포지션 반환"""
        return {symbol: position.shares for symbol, position in self.positions.items()}
    
    def get_position_weights(self, current_prices: Dict[str, float]) -> Dict[str, float]:
        """포지션별 가중치 반환"""
        self.update_positions(current_prices)
        return {symbol: position.weight for symbol, position in self.positions.items()}
    
    def get_trade_history(self) -> List[Dict[str, Any]]:
        """거래 기록 반환"""
        return [
            {
                'date': trade.date,
                'symbol': trade.symbol,
                'action': trade.action,
                'shares': trade.shares,
                'price': trade.price,
                'total_value': trade.total_value,
                'commission': trade.commission,
                'reason': trade.reason
            }
            for trade in self.trade_history
        ]
    
    def get_history(self) -> List[Dict[str, Any]]:
        """포트폴리오 히스토리 반환"""
        return self.value_history
    
    def record_daily_value(self, date: datetime, current_prices: Dict[str, float]):
        """일별 포트폴리오 가치 기록"""
        self.update_positions(current_prices)
        total_value = self.get_total_value(current_prices)
        
        position_details = {}
        for symbol, position in self.positions.items():
            position_details[symbol] = {
                'shares': position.shares,
                'price': position.current_price,
                'market_value': position.market_value,
                'weight': position.weight,
                'unrealized_pnl': position.unrealized_pnl
            }
        
        daily_record = {
            'date': date,
            'total_value': total_value,
            'cash': self.cash,
            'invested_value': total_value - self.cash,
            'positions': position_details,
            'position_count': len(self.positions)
        }
        
        self.value_history.append(daily_record)
    
    def get_portfolio_summary(self, current_prices: Dict[str, float]) -> Dict[str, Any]:
        """포트폴리오 요약 정보"""
        self.update_positions(current_prices)
        total_value = self.get_total_value(current_prices)
        
        return {
            'total_value': total_value,
            'cash': self.cash,
            'invested_value': total_value - self.cash,
            'total_return': (total_value / self.initial_cash) - 1,
            'position_count': len(self.positions),
            'largest_position': max(self.positions.values(), key=lambda p: p.weight) if self.positions else None,
            'total_trades': len(self.trade_history),
            'total_commissions': sum(trade.commission for trade in self.trade_history)
        }
    
    def validate_portfolio_constraints(self, current_prices: Dict[str, float]) -> List[str]:
        """포트폴리오 제약 조건 검사"""
        warnings = []
        
        if len(self.positions) > self.max_positions:
            warnings.append(f"포지션 수가 최대치 {self.max_positions}를 초과했습니다: {len(self.positions)}")
        
        self.update_positions(current_prices)
        for symbol, position in self.positions.items():
            if position.weight > self.max_position_size:
                warnings.append(f"{symbol} 포지션이 최대 비중 {self.max_position_size:.1%}를 초과했습니다: {position.weight:.1%}")
            
            if 0 < position.weight < self.min_position_size:
                warnings.append(f"{symbol} 포지션이 최소 비중 {self.min_position_size:.1%} 미만입니다: {position.weight:.1%}")
        
        return warnings