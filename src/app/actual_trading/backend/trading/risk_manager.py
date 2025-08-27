# file: backend/trading/risk_manager.py

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, date, time
import json

from models import TradingSignal, RiskMetrics
from database import get_db_session
from utils.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class RiskManager:
    """리스크 관리 클래스"""
    
    def __init__(self):
        # 기본 리스크 한도 설정
        self.daily_loss_limit = -0.02  # -2%
        self.position_size_limit = 0.05  # 5%
        self.max_positions = 10
        self.max_single_stock_weight = 0.15  # 15%
        self.max_sector_weight = 0.3  # 30%
        
        # 동적 리스크 추적
        self.current_daily_loss = 0.0
        self.current_positions_count = 0
        self.sector_exposure = {}
        
        # 리스크 상태
        self.risk_level = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL
        self.trading_allowed = True
        
    async def validate_signal(self, signal: TradingSignal, current_positions: Dict[str, Any]) -> bool:
        """트레이딩 신호의 리스크 검증"""
        try:
            # 1. 기본 리스크 체크
            if not self.trading_allowed:
                logger.warning("트레이딩이 비활성화됨 - 신호 거부")
                return False
            
            # 2. 일일 손실 한도 체크
            if not await self.check_daily_loss_limit():
                logger.warning("일일 손실 한도 초과 - 신호 거부")
                return False
            
            # 3. 포지션 수 한도 체크
            if signal.signal_type == "buy" and not self.check_position_count_limit(current_positions):
                logger.warning("최대 포지션 수 초과 - 매수 신호 거부")
                return False
            
            # 4. 포지션 크기 한도 체크
            if not await self.check_position_size_limit(signal):
                logger.warning("포지션 크기 한도 초과 - 신호 거부")
                return False
            
            # 5. 종목별 집중도 체크
            if not await self.check_concentration_risk(signal, current_positions):
                logger.warning("집중도 리스크 - 신호 거부")
                return False
            
            # 6. 시장 시간 체크
            if not self.check_market_hours():
                logger.warning("시장 시간 외 - 신호 거부")
                return False
            
            # 7. 변동성 체크
            if not await self.check_volatility_risk(signal):
                logger.warning("변동성 리스크 높음 - 신호 거부")
                return False
            
            logger.info(f"리스크 검증 통과: {signal.stock_code} {signal.signal_type}")
            return True
            
        except Exception as e:
            logger.error(f"리스크 검증 오류: {e}")
            return False
    
    async def check_daily_loss_limit(self) -> bool:
        """일일 손실 한도 체크"""
        try:
            # 오늘의 실현 손익 조회
            today_pnl = await self.get_today_pnl()
            self.current_daily_loss = today_pnl
            
            # 손실 한도 비교
            if today_pnl < self.daily_loss_limit:
                self.risk_level = "CRITICAL"
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"일일 손실 한도 체크 오류: {e}")
            return True  # 오류 시 안전하게 허용
    
    def check_position_count_limit(self, current_positions: Dict[str, Any]) -> bool:
        """포지션 수 한도 체크"""
        try:
            active_positions = len([pos for pos in current_positions.values() if pos['quantity'] > 0])
            self.current_positions_count = active_positions
            
            return active_positions < self.max_positions
            
        except Exception as e:
            logger.error(f"포지션 수 체크 오류: {e}")
            return True
    
    async def check_position_size_limit(self, signal: TradingSignal) -> bool:
        """포지션 크기 한도 체크"""
        try:
            # 현재 포트폴리오 총 가치 조회
            total_portfolio_value = await self.get_total_portfolio_value()
            
            # 신호의 투자 금액 계산
            signal_value = signal.quantity * signal.price
            
            # 포트폴리오 대비 비중 계산
            position_weight = signal_value / total_portfolio_value
            
            return position_weight <= self.position_size_limit
            
        except Exception as e:
            logger.error(f"포지션 크기 체크 오류: {e}")
            return True
    
    async def check_concentration_risk(self, signal: TradingSignal, current_positions: Dict[str, Any]) -> bool:
        """집중도 리스크 체크"""
        try:
            if signal.signal_type != "buy":
                return True  # 매도는 집중도 감소
            
            # 총 포트폴리오 가치
            total_value = await self.get_total_portfolio_value()
            
            # 동일 종목 집중도 체크
            current_stock_value = 0
            for pos in current_positions.values():
                if pos['stock_code'] == signal.stock_code:
                    current_stock_value += pos['quantity'] * pos['current_price']
            
            new_investment = signal.quantity * signal.price
            total_stock_value = current_stock_value + new_investment
            stock_weight = total_stock_value / total_value
            
            if stock_weight > self.max_single_stock_weight:
                logger.warning(f"종목 집중도 초과: {signal.stock_code} {stock_weight:.1%}")
                return False
            
            # 섹터 집중도 체크 (실제로는 종목-섹터 매핑 데이터 필요)
            sector = await self.get_stock_sector(signal.stock_code)
            if sector:
                sector_weight = await self.calculate_sector_weight(sector, current_positions, signal)
                if sector_weight > self.max_sector_weight:
                    logger.warning(f"섹터 집중도 초과: {sector} {sector_weight:.1%}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"집중도 리스크 체크 오류: {e}")
            return True
    
    def check_market_hours(self) -> bool:
        """시장 시간 체크"""
        try:
            now = datetime.now()
            
            # 주말 체크
            if now.weekday() >= 5:  # 토요일(5), 일요일(6)
                return False
            
            # 시장 시간 체크 (9:00 - 15:30)
            market_open = time(9, 0)
            market_close = time(15, 30)
            current_time = now.time()
            
            return market_open <= current_time <= market_close
            
        except Exception as e:
            logger.error(f"시장 시간 체크 오류: {e}")
            return False
    
    async def check_volatility_risk(self, signal: TradingSignal) -> bool:
        """변동성 리스크 체크"""
        try:
            # 종목의 최근 변동성 조회
            volatility = await self.get_stock_volatility(signal.stock_code)
            
            # 높은 변동성 종목의 경우 포지션 크기 제한
            high_volatility_threshold = 0.4  # 40% 연 변동성
            
            if volatility > high_volatility_threshold:
                # 신호의 신뢰도가 높은 경우만 허용
                return signal.confidence > 0.8
            
            return True
            
        except Exception as e:
            logger.error(f"변동성 리스크 체크 오류: {e}")
            return True
    
    async def check_daily_limits(self, current_pnl: float, current_positions: Dict[str, Any]) -> Dict[str, Any]:
        """일일 리스크 한도 체크"""
        try:
            risk_status = {
                'is_safe': True,
                'risk_level': 'LOW',
                'message': '',
                'severity': 'normal'
            }
            
            # 1. 일일 손실 체크
            loss_ratio = current_pnl / await self.get_total_portfolio_value()
            
            if loss_ratio <= self.daily_loss_limit:
                risk_status.update({
                    'is_safe': False,
                    'risk_level': 'CRITICAL',
                    'message': f'일일 손실 한도 초과: {loss_ratio:.2%}',
                    'severity': 'critical'
                })
            elif loss_ratio <= self.daily_loss_limit * 0.7:
                risk_status.update({
                    'risk_level': 'HIGH',
                    'message': f'일일 손실 경고: {loss_ratio:.2%}',
                    'severity': 'high'
                })
            elif loss_ratio <= self.daily_loss_limit * 0.5:
                risk_status.update({
                    'risk_level': 'MEDIUM',
                    'message': f'일일 손실 주의: {loss_ratio:.2%}',
                    'severity': 'medium'
                })
            
            # 2. 포지션 수 체크
            position_count = len([pos for pos in current_positions.values() if pos['quantity'] > 0])
            if position_count >= self.max_positions:
                risk_status.update({
                    'risk_level': 'HIGH',
                    'message': f'최대 포지션 수 도달: {position_count}',
                    'severity': 'high'
                })
            
            # 3. 집중도 리스크 체크
            concentration_risk = await self.check_portfolio_concentration(current_positions)
            if concentration_risk['high_concentration']:
                risk_status.update({
                    'risk_level': 'MEDIUM',
                    'message': concentration_risk['message'],
                    'severity': 'medium'
                })
            
            return risk_status
            
        except Exception as e:
            logger.error(f"일일 리스크 체크 오류: {e}")
            return {'is_safe': True, 'risk_level': 'UNKNOWN', 'message': 'Risk check failed'}
    
    async def get_current_metrics(self) -> RiskMetrics:
        """현재 리스크 지표 반환"""
        try:
            return RiskMetrics(
                daily_loss_limit=self.daily_loss_limit,
                position_size_limit=self.position_size_limit,
                max_positions=self.max_positions,
                current_daily_loss=self.current_daily_loss,
                is_safe_to_trade=self.trading_allowed
            )
        except Exception as e:
            logger.error(f"리스크 지표 조회 오류: {e}")
            return RiskMetrics()
    
    async def update_limits(self, new_limits: Dict[str, Any]):
        """리스크 한도 업데이트"""
        try:
            if 'daily_loss_limit' in new_limits:
                self.daily_loss_limit = new_limits['daily_loss_limit']
            
            if 'position_size_limit' in new_limits:
                self.position_size_limit = new_limits['position_size_limit']
            
            if 'max_positions' in new_limits:
                self.max_positions = new_limits['max_positions']
            
            if 'max_single_stock_weight' in new_limits:
                self.max_single_stock_weight = new_limits['max_single_stock_weight']
            
            if 'max_sector_weight' in new_limits:
                self.max_sector_weight = new_limits['max_sector_weight']
            
            logger.info("리스크 한도 업데이트 완료")
            
        except Exception as e:
            logger.error(f"리스크 한도 업데이트 오류: {e}")
    
    # 헬퍼 메서드들
    async def get_today_pnl(self) -> float:
        """오늘의 실현 손익 조회"""
        try:
            from models import Order, OrderStatus
            
            with get_db_session() as db:
                today = date.today()
                today_orders = db.query(Order)\
                    .filter(Order.fill_time >= datetime.combine(today, time.min))\
                    .filter(Order.status == OrderStatus.FILLED)\
                    .all()
                
                total_pnl = 0.0
                for order in today_orders:
                    if order.order_type == "sell":
                        # 간단한 손익 계산 (실제로는 더 정교한 계산 필요)
                        total_pnl += (order.fill_price - order.price) * order.fill_quantity
                
                return total_pnl
                
        except Exception as e:
            logger.error(f"오늘 손익 조회 오류: {e}")
            return 0.0
    
    async def get_total_portfolio_value(self) -> float:
        """총 포트폴리오 가치 조회"""
        try:
            from models import Portfolio
            
            with get_db_session() as db:
                latest_portfolio = db.query(Portfolio)\
                    .order_by(Portfolio.timestamp.desc())\
                    .first()
                
                return latest_portfolio.total_value if latest_portfolio else 50000000.0
                
        except Exception as e:
            logger.error(f"포트폴리오 가치 조회 오류: {e}")
            return 50000000.0  # 기본값
    
    async def get_stock_sector(self, stock_code: str) -> Optional[str]:
        """종목의 섹터 정보 조회"""
        try:
            # 간단한 섹터 매핑 (실제로는 데이터베이스나 API에서 조회)
            sector_map = {
                '005930': 'Technology',  # 삼성전자
                '000660': 'Technology',  # SK하이닉스
                '035420': 'Technology',  # NAVER
                '035720': 'Technology',  # 카카오
                '051910': 'Chemical',    # LG화학
                '006400': 'Technology',  # 삼성SDI
                '207940': 'Biotech',     # 삼성바이오로직스
                '373220': 'Battery',     # LG에너지솔루션
            }
            
            return sector_map.get(stock_code)
            
        except Exception as e:
            logger.error(f"섹터 정보 조회 오류: {e}")
            return None
    
    async def calculate_sector_weight(self, sector: str, current_positions: Dict[str, Any], 
                                   new_signal: TradingSignal) -> float:
        """섹터별 투자 비중 계산"""
        try:
            total_value = await self.get_total_portfolio_value()
            sector_value = 0.0
            
            # 현재 섹터 투자 금액 계산
            for pos in current_positions.values():
                stock_sector = await self.get_stock_sector(pos['stock_code'])
                if stock_sector == sector:
                    sector_value += pos['quantity'] * pos['current_price']
            
            # 신규 투자 금액 추가
            if new_signal.signal_type == "buy":
                signal_sector = await self.get_stock_sector(new_signal.stock_code)
                if signal_sector == sector:
                    sector_value += new_signal.quantity * new_signal.price
            
            return sector_value / total_value
            
        except Exception as e:
            logger.error(f"섹터 비중 계산 오류: {e}")
            return 0.0
    
    async def get_stock_volatility(self, stock_code: str, days: int = 30) -> float:
        """종목 변동성 계산"""
        try:
            from models import Stock, PriceHistory
            from trading.indicators import TechnicalIndicators
            
            with get_db_session() as db:
                stock = db.query(Stock).filter(Stock.code == stock_code).first()
                if not stock:
                    return 0.0
                
                # 최근 30일 가격 데이터 조회
                price_records = db.query(PriceHistory)\
                    .filter(PriceHistory.stock_id == stock.id)\
                    .order_by(PriceHistory.timestamp.desc())\
                    .limit(days)\
                    .all()
                
                if len(price_records) < 10:
                    return 0.0
                
                prices = [record.price for record in reversed(price_records)]
                return TechnicalIndicators.calculate_volatility(prices, min(20, len(prices)))
                
        except Exception as e:
            logger.error(f"변동성 계산 오류: {e}")
            return 0.0
    
    async def check_portfolio_concentration(self, current_positions: Dict[str, Any]) -> Dict[str, Any]:
        """포트폴리오 집중도 체크"""
        try:
            total_value = await self.get_total_portfolio_value()
            
            # 종목별 비중 계산
            stock_weights = {}
            for pos in current_positions.values():
                stock_value = pos['quantity'] * pos['current_price']
                weight = stock_value / total_value
                stock_weights[pos['stock_code']] = weight
            
            # 최대 종목 비중 체크
            max_weight = max(stock_weights.values()) if stock_weights else 0.0
            high_concentration = max_weight > self.max_single_stock_weight
            
            result = {
                'high_concentration': high_concentration,
                'max_stock_weight': max_weight,
                'message': f'최대 종목 비중: {max_weight:.1%}' if high_concentration else ''
            }
            
            return result
            
        except Exception as e:
            logger.error(f"집중도 체크 오류: {e}")
            return {'high_concentration': False, 'max_stock_weight': 0.0, 'message': ''}
    
    def enable_trading(self):
        """트레이딩 활성화"""
        self.trading_allowed = True
        logger.info("트레이딩 활성화됨")
    
    def disable_trading(self):
        """트레이딩 비활성화"""
        self.trading_allowed = False
        logger.warning("트레이딩 비활성화됨")
    
    def set_risk_level(self, level: str):
        """리스크 레벨 설정"""
        valid_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        if level in valid_levels:
            self.risk_level = level
            logger.info(f"리스크 레벨 설정: {level}")
            
            # 리스크 레벨에 따른 트레이딩 제한
            if level == "CRITICAL":
                self.disable_trading()
            elif level in ["LOW", "MEDIUM"]:
                self.enable_trading()

class PositionSizer:
    """포지션 크기 계산 클래스"""
    
    def __init__(self, risk_manager: RiskManager):
        self.risk_manager = risk_manager
    
    def calculate_position_size(self, signal: TradingSignal, portfolio_value: float, 
                              volatility: float = 0.2) -> int:
        """포지션 크기 계산 (Kelly Criterion 기반)"""
        try:
            # 기본 포지션 크기 (포트폴리오의 5%)
            base_position_value = portfolio_value * self.risk_manager.position_size_limit
            
            # 신호 신뢰도에 따른 조정
            confidence_multiplier = min(1.5, signal.confidence * 1.5)
            
            # 변동성에 따른 조정 (변동성이 높을수록 포지션 크기 감소)
            volatility_multiplier = max(0.5, 1 - volatility)
            
            # 최종 포지션 값 계산
            adjusted_position_value = base_position_value * confidence_multiplier * volatility_multiplier
            
            # 주식 수량 계산 (100주 단위)
            quantity = int(adjusted_position_value / signal.price / 100) * 100
            
            return max(100, quantity)  # 최소 100주
            
        except Exception as e:
            logger.error(f"포지션 크기 계산 오류: {e}")
            return 100
    
    def calculate_stop_loss_price(self, entry_price: float, atr: float, 
                                 multiplier: float = 2.0) -> float:
        """손절가 계산 (ATR 기반)"""
        try:
            return entry_price - (atr * multiplier)
        except:
            return entry_price * 0.95  # 기본 5% 손절
    
    def calculate_take_profit_price(self, entry_price: float, atr: float, 
                                  risk_reward_ratio: float = 2.0) -> float:
        """익절가 계산"""
        try:
            stop_loss = self.calculate_stop_loss_price(entry_price, atr)
            risk_amount = entry_price - stop_loss
            return entry_price + (risk_amount * risk_reward_ratio)
        except:
            return entry_price * 1.1  # 기본 10% 익절

class DrawdownManager:
    """낙폭 관리 클래스"""
    
    def __init__(self):
        self.peak_portfolio_value = 0.0
        self.current_drawdown = 0.0
        self.max_drawdown = 0.0
        self.max_drawdown_allowed = 0.15  # 15%
        
    def update_drawdown(self, current_portfolio_value: float):
        """낙폭 업데이트"""
        try:
            # 신고점 업데이트
            if current_portfolio_value > self.peak_portfolio_value:
                self.peak_portfolio_value = current_portfolio_value
                self.current_drawdown = 0.0
            else:
                # 현재 낙폭 계산
                self.current_drawdown = (self.peak_portfolio_value - current_portfolio_value) / self.peak_portfolio_value
                
                # 최대 낙폭 업데이트
                if self.current_drawdown > self.max_drawdown:
                    self.max_drawdown = self.current_drawdown
            
        except Exception as e:
            logger.error(f"낙폭 업데이트 오류: {e}")
    
    def is_drawdown_acceptable(self) -> bool:
        """낙폭이 허용 범위 내인지 확인"""
        return self.current_drawdown < self.max_drawdown_allowed
    
    def get_drawdown_status(self) -> Dict[str, float]:
        """낙폭 상태 반환"""
        return {
            'current_drawdown': self.current_drawdown,
            'max_drawdown': self.max_drawdown,
            'peak_value': self.peak_portfolio_value,
            'is_acceptable': self.is_drawdown_acceptable()
        }

class CorrelationManager:
    """상관관계 관리 클래스"""
    
    def __init__(self):
        self.correlation_matrix = {}
        self.max_correlation = 0.7  # 최대 허용 상관계수
    
    async def update_correlations(self, stock_codes: List[str], days: int = 60):
        """종목간 상관관계 업데이트"""
        try:
            from models import Stock, PriceHistory
            from trading.indicators import TechnicalIndicators
            
            price_data = {}
            
            # 각 종목의 가격 데이터 수집
            with get_db_session() as db:
                for stock_code in stock_codes:
                    stock = db.query(Stock).filter(Stock.code == stock_code).first()
                    if stock:
                        price_records = db.query(PriceHistory)\
                            .filter(PriceHistory.stock_id == stock.id)\
                            .order_by(PriceHistory.timestamp)\
                            .limit(days)\
                            .all()
                        
                        prices = [record.price for record in price_records]
                        if len(prices) >= days // 2:
                            price_data[stock_code] = prices
            
            # 상관계수 행렬 계산
            for code1 in price_data:
                for code2 in price_data:
                    if code1 != code2:
                        correlation = TechnicalIndicators.calculate_correlation(
                            price_data[code1], price_data[code2]
                        )
                        self.correlation_matrix[f"{code1}_{code2}"] = correlation
            
        except Exception as e:
            logger.error(f"상관관계 업데이트 오류: {e}")
    
    def check_correlation_risk(self, new_stock: str, existing_stocks: List[str]) -> bool:
        """새로운 종목 추가시 상관관계 리스크 체크"""
        try:
            for existing_stock in existing_stocks:
                key = f"{new_stock}_{existing_stock}"
                reverse_key = f"{existing_stock}_{new_stock}"
                
                correlation = self.correlation_matrix.get(key) or self.correlation_matrix.get(reverse_key, 0)
                
                if abs(correlation) > self.max_correlation:
                    logger.warning(f"높은 상관관계 감지: {new_stock} - {existing_stock} ({correlation:.2f})")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"상관관계 체크 오류: {e}")
            return True

class RiskAlert:
    """리스크 알림 클래스"""
    
    def __init__(self):
        self.alert_thresholds = {
            'daily_loss': -0.015,  # -1.5%
            'drawdown': 0.10,      # 10%
            'volatility': 0.35     # 35%
        }
    
    async def check_and_send_alerts(self, portfolio_data: Dict[str, Any]):
        """리스크 알림 체크 및 발송"""
        try:
            alerts = []
            
            # 일일 손실 알림
            daily_loss_ratio = portfolio_data.get('daily_pnl', 0) / portfolio_data.get('total_value', 1)
            if daily_loss_ratio <= self.alert_thresholds['daily_loss']:
                alerts.append({
                    'type': 'daily_loss',
                    'severity': 'high',
                    'message': f'일일 손실 경고: {daily_loss_ratio:.2%}',
                    'timestamp': datetime.now()
                })
            
            # 낙폭 알림
            drawdown = portfolio_data.get('current_drawdown', 0)
            if drawdown >= self.alert_thresholds['drawdown']:
                alerts.append({
                    'type': 'drawdown',
                    'severity': 'high',
                    'message': f'낙폭 경고: {drawdown:.2%}',
                    'timestamp': datetime.now()
                })
            
            # 변동성 알림
            portfolio_volatility = portfolio_data.get('volatility', 0)
            if portfolio_volatility >= self.alert_thresholds['volatility']:
                alerts.append({
                    'type': 'volatility',
                    'severity': 'medium',
                    'message': f'높은 변동성 감지: {portfolio_volatility:.2%}',
                    'timestamp': datetime.now()
                })
            
            # 알림 발송
            for alert in alerts:
                await self.send_alert(alert)
            
        except Exception as e:
            logger.error(f"리스크 알림 체크 오류: {e}")
    
    async def send_alert(self, alert: Dict[str, Any]):
        """알림 발송"""
        try:
            # 실제로는 이메일, SMS, 슬랙 등으로 알림 발송
            logger.warning(f"리스크 알림: {alert['message']}")
            
            # 데이터베이스에 알림 기록 저장
            await self.save_alert_to_db(alert)
            
        except Exception as e:
            logger.error(f"알림 발송 오류: {e}")
    
    async def save_alert_to_db(self, alert: Dict[str, Any]):
        """알림을 데이터베이스에 저장"""
        try:
            # 실제 구현에서는 Alert 테이블에 저장
            pass
        except Exception as e:
            logger.error(f"알림 저장 오류: {e}")

class EmergencyManager:
    """비상 관리 클래스"""
    
    def __init__(self, risk_manager: RiskManager):
        self.risk_manager = risk_manager
        self.emergency_triggers = {
            'flash_crash': -0.05,  # 5% 급락
            'circuit_breaker': -0.08,  # 8% 급락
            'system_error': True
        }
    
    async def check_emergency_conditions(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """비상 상황 체크"""
        try:
            emergency_status = {
                'emergency': False,
                'type': None,
                'severity': 'normal',
                'action_required': None
            }
            
            # 급락 체크
            portfolio_change = market_data.get('portfolio_change_rate', 0)
            
            if portfolio_change <= self.emergency_triggers['circuit_breaker']:
                emergency_status.update({
                    'emergency': True,
                    'type': 'circuit_breaker',
                    'severity': 'critical',
                    'action_required': 'emergency_stop'
                })
            elif portfolio_change <= self.emergency_triggers['flash_crash']:
                emergency_status.update({
                    'emergency': True,
                    'type': 'flash_crash',
                    'severity': 'high',
                    'action_required': 'stop_trading'
                })
            
            # 시스템 오류 체크
            if market_data.get('api_error', False):
                emergency_status.update({
                    'emergency': True,
                    'type': 'system_error',
                    'severity': 'high',
                    'action_required': 'emergency_stop'
                })
            
            return emergency_status
            
        except Exception as e:
            logger.error(f"비상 상황 체크 오류: {e}")
            return {'emergency': False}
    
    async def execute_emergency_action(self, action: str):
        """비상 조치 실행"""
        try:
            if action == 'emergency_stop':
                self.risk_manager.disable_trading()
                logger.critical("비상 중단 실행됨")
                
            elif action == 'stop_trading':
                self.risk_manager.disable_trading()
                logger.warning("트레이딩 중지됨")
                
            elif action == 'reduce_positions':
                # 포지션 크기 축소 로직
                logger.info("포지션 축소 모드 활성화")
                
        except Exception as e:
            logger.error(f"비상 조치 실행 오류: {e}") 
