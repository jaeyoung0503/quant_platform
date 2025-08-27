# file: kiwoom_mock/stratiges.py

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass

@dataclass
class TradingSignal:
    """거래 신호"""
    stock_code: str
    signal_type: str  # BUY, SELL, HOLD
    strength: float   # 0.0 ~ 1.0
    price: int
    quantity: int
    reason: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class BaseStrategy(ABC):
    """투자 전략 기본 클래스"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"strategy.{name}")
        self.is_active = False
        self.parameters = {}
    
    @abstractmethod
    def analyze(self, stock_code: str, price_data: Dict, portfolio: Dict) -> TradingSignal:
        """분석 및 신호 생성"""
        pass
    
    def set_parameter(self, key: str, value):
        """파라미터 설정"""
        self.parameters[key] = value
    
    def get_parameter(self, key: str, default=None):
        """파라미터 조회"""
        return self.parameters.get(key, default)

class SimpleMovingAverageStrategy(BaseStrategy):
    """단순 이동평균 전략"""
    
    def __init__(self, short_period=5, long_period=20):
        super().__init__("단순이동평균")
        self.set_parameter("short_period", short_period)
        self.set_parameter("long_period", long_period)
        self.price_history = {}
    
    def analyze(self, stock_code: str, price_data: Dict, portfolio: Dict) -> TradingSignal:
        """이동평균 분석"""
        current_price = price_data.get('current_price', 0)
        
        # 가격 히스토리 업데이트
        if stock_code not in self.price_history:
            self.price_history[stock_code] = []
        
        self.price_history[stock_code].append(current_price)
        
        # 최대 100개까지만 보관
        if len(self.price_history[stock_code]) > 100:
            self.price_history[stock_code] = self.price_history[stock_code][-100:]
        
        # 이동평균 계산
        short_ma = self._calculate_ma(stock_code, self.get_parameter("short_period"))
        long_ma = self._calculate_ma(stock_code, self.get_parameter("long_period"))
        
        if short_ma is None or long_ma is None:
            return TradingSignal(
                stock_code=stock_code,
                signal_type="HOLD",
                strength=0.0,
                price=current_price,
                quantity=0,
                reason="데이터 부족"
            )
        
        # 신호 생성
        if short_ma > long_ma * 1.01:  # 1% 이상 차이
            # 매수 신호
            strength = min((short_ma - long_ma) / long_ma * 20, 1.0)
            quantity = self._calculate_buy_quantity(current_price, portfolio)
            
            return TradingSignal(
                stock_code=stock_code,
                signal_type="BUY",
                strength=strength,
                price=current_price,
                quantity=quantity,
                reason=f"골든크로스 (단기:{short_ma:.0f} > 장기:{long_ma:.0f})"
            )
            
        elif short_ma < long_ma * 0.99:  # 1% 이상 차이
            # 매도 신호
            strength = min((long_ma - short_ma) / long_ma * 20, 1.0)
            quantity = self._calculate_sell_quantity(stock_code, portfolio)
            
            return TradingSignal(
                stock_code=stock_code,
                signal_type="SELL",
                strength=strength,
                price=current_price,
                quantity=quantity,
                reason=f"데드크로스 (단기:{short_ma:.0f} < 장기:{long_ma:.0f})"
            )
        
        return TradingSignal(
            stock_code=stock_code,
            signal_type="HOLD",
            strength=0.5,
            price=current_price,
            quantity=0,
            reason="이동평균 신호 없음"
        )
    
    def _calculate_ma(self, stock_code: str, period: int) -> Optional[float]:
        """이동평균 계산"""
        if stock_code not in self.price_history:
            return None
        
        prices = self.price_history[stock_code]
        if len(prices) < period:
            return None
        
        return sum(prices[-period:]) / period
    
    def _calculate_buy_quantity(self, price: int, portfolio: Dict) -> int:
        """매수 수량 계산"""
        cash_balance = portfolio.get('cash_balance', 0)
        max_investment = cash_balance * 0.1  # 잔고의 10%
        return int(max_investment / price) if price > 0 else 0
    
    def _calculate_sell_quantity(self, stock_code: str, portfolio: Dict) -> int:
        """매도 수량 계산"""
        holdings = portfolio.get('holdings', {})
        for holding in holdings:
            if holding['stock_code'] == stock_code:
                return holding['quantity'] // 2  # 보유량의 50%
        return 0

class RSIStrategy(BaseStrategy):
    """RSI 전략"""
    
    def __init__(self, period=14, oversold=30, overbought=70):
        super().__init__("RSI")
        self.set_parameter("period", period)
        self.set_parameter("oversold", oversold)
        self.set_parameter("overbought", overbought)
        self.price_history = {}
    
    def analyze(self, stock_code: str, price_data: Dict, portfolio: Dict) -> TradingSignal:
        """RSI 분석"""
        current_price = price_data.get('current_price', 0)
        
        # 가격 히스토리 업데이트
        if stock_code not in self.price_history:
            self.price_history[stock_code] = []
        
        self.price_history[stock_code].append(current_price)
        
        # RSI 계산
        rsi = self._calculate_rsi(stock_code)
        
        if rsi is None:
            return TradingSignal(
                stock_code=stock_code,
                signal_type="HOLD",
                strength=0.0,
                price=current_price,
                quantity=0,
                reason="RSI 계산 불가"
            )
        
        oversold = self.get_parameter("oversold")
        overbought = self.get_parameter("overbought")
        
        if rsi < oversold:
            # 과매도 - 매수
            strength = (oversold - rsi) / oversold
            quantity = self._calculate_buy_quantity(current_price, portfolio)
            
            return TradingSignal(
                stock_code=stock_code,
                signal_type="BUY",
                strength=strength,
                price=current_price,
                quantity=quantity,
                reason=f"RSI 과매도 ({rsi:.1f})"
            )
            
        elif rsi > overbought:
            # 과매수 - 매도
            strength = (rsi - overbought) / (100 - overbought)
            quantity = self._calculate_sell_quantity(stock_code, portfolio)
            
            return TradingSignal(
                stock_code=stock_code,
                signal_type="SELL",
                strength=strength,
                price=current_price,
                quantity=quantity,
                reason=f"RSI 과매수 ({rsi:.1f})"
            )
        
        return TradingSignal(
            stock_code=stock_code,
            signal_type="HOLD",
            strength=0.5,
            price=current_price,
            quantity=0,
            reason=f"RSI 중립 ({rsi:.1f})"
        )
    
    def _calculate_rsi(self, stock_code: str) -> Optional[float]:
        """RSI 계산"""
        if stock_code not in self.price_history:
            return None
        
        prices = self.price_history[stock_code]
        period = self.get_parameter("period")
        
        if len(prices) < period + 1:
            return None
        
        gains = []
        losses = []
        
        for i in range(1, len(prices[-period-1:])):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(-change)
        
        if len(gains) < period:
            return None
        
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_buy_quantity(self, price: int, portfolio: Dict) -> int:
        """매수 수량 계산"""
        cash_balance = portfolio.get('cash_balance', 0)
        max_investment = cash_balance * 0.05  # 잔고의 5%
        return int(max_investment / price) if price > 0 else 0
    
    def _calculate_sell_quantity(self, stock_code: str, portfolio: Dict) -> int:
        """매도 수량 계산"""
        holdings = portfolio.get('holdings', {})
        for holding in holdings:
            if holding['stock_code'] == stock_code:
                return holding['quantity'] // 3  # 보유량의 1/3
        return 0

class StrategyManager:
    """전략 관리자"""
    
    def __init__(self):
        self.strategies = {}
        self.active_strategies = []
        self.logger = logging.getLogger(__name__)
        
        # 기본 전략들 등록
        self.register_default_strategies()
    
    def register_default_strategies(self):
        """기본 전략들 등록"""
        ma_strategy = SimpleMovingAverageStrategy()
        rsi_strategy = RSIStrategy()
        
        self.register_strategy(ma_strategy)
        self.register_strategy(rsi_strategy)
    
    def register_strategy(self, strategy: BaseStrategy):
        """전략 등록"""
        self.strategies[strategy.name] = strategy
        self.logger.info(f"전략 등록: {strategy.name}")
    
    def activate_strategy(self, strategy_name: str):
        """전략 활성화"""
        if strategy_name in self.strategies:
            strategy = self.strategies[strategy_name]
            if strategy not in self.active_strategies:
                self.active_strategies.append(strategy)
                strategy.is_active = True
                self.logger.info(f"전략 활성화: {strategy_name}")
    
    def deactivate_strategy(self, strategy_name: str):
        """전략 비활성화"""
        if strategy_name in self.strategies:
            strategy = self.strategies[strategy_name]
            if strategy in self.active_strategies:
                self.active_strategies.remove(strategy)
                strategy.is_active = False
                self.logger.info(f"전략 비활성화: {strategy_name}")
    
    def analyze_stock(self, stock_code: str, price_data: Dict, portfolio: Dict) -> List[TradingSignal]:
        """종목 분석"""
        signals = []
        
        for strategy in self.active_strategies:
            try:
                signal = strategy.analyze(stock_code, price_data, portfolio)
                if signal.signal_type != "HOLD":
                    signals.append(signal)
            except Exception as e:
                self.logger.error(f"전략 {strategy.name} 분석 오류: {e}")
        
        return signals
    
    def get_strategy_list(self) -> List[Dict]:
        """전략 목록 조회"""
        strategy_list = []
        
        for name, strategy in self.strategies.items():
            info = {
                'name': name,
                'is_active': strategy.is_active,
                'parameters': strategy.parameters
            }
            strategy_list.append(info)
        
        return strategy_list
        
##utility.py
# utils.py - 유틸리티 함수들

import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Any

def create_directories():
    """필수 디렉토리 생성"""
    directories = [
        "logs",
        "backups", 
        "data",
        "database"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def check_requirements() -> bool:
    """시스템 요구사항 확인"""
    try:
        # Python 버전 확인
        if sys.version_info < (3, 7):
            print("Python 3.7 이상이 필요합니다.")
            return False
        
        # 필수 모듈 확인
        required_modules = ['PyQt5', 'sqlite3']
        missing = []
        
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                missing.append(module)
        
        if missing:
            print(f"필수 모듈 누락: {', '.join(missing)}")
            print("pip install PyQt5 pandas 로 설치하세요.")
            return False
        
        return True
        
    except Exception as e:
        print(f"요구사항 확인 오류: {e}")
        return False

def format_currency(amount: int) -> str:
    """통화 포맷팅"""
    return f"{amount:,}원"

def format_percentage(rate: float) -> str:
    """퍼센트 포맷팅"""
    return f"{rate:+.2f}%"

def format_number(number: int) -> str:
    """숫자 포맷팅"""
    return f"{number:,}"

def validate_stock_code(stock_code: str) -> bool:
    """종목코드 유효성 검사"""
    return len(stock_code) == 6 and stock_code.isdigit()

def validate_positive_number(value: str) -> bool:
    """양수 유효성 검사"""
    try:
        return int(value) > 0
    except ValueError:
        return False

def calculate_profit_rate(current_price: int, avg_price: int) -> float:
    """수익률 계산"""
    if avg_price <= 0:
        return 0.0
    return (current_price - avg_price) / avg_price * 100

def get_timestamp_string() -> str:
    """타임스탬프 문자열 생성"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def safe_int_convert(value: str, default: int = 0) -> int:
    """안전한 정수 변환"""
    try:
        return int(value.replace(",", "").strip())
    except (ValueError, AttributeError):
        return default

def safe_float_convert(value: str, default: float = 0.0) -> float:
    """안전한 실수 변환"""
    try:
        return float(value.replace(",", "").strip())
    except (ValueError, AttributeError):
        return default

class DataValidator:
    """데이터 유효성 검사 클래스"""
    
    @staticmethod
    def validate_order_data(stock_code: str, quantity: int, price: int) -> Dict:
        """주문 데이터 유효성 검사"""
        errors = []
        
        if not validate_stock_code(stock_code):
            errors.append("올바른 종목코드를 입력하세요.")
        
        if quantity <= 0:
            errors.append("수량은 0보다 커야 합니다.")
        
        if price <= 0:
            errors.append("가격은 0보다 커야 합니다.")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    @staticmethod
    def validate_account_number(account_no: str) -> bool:
        """계좌번호 유효성 검사"""
        return len(account_no) == 10 and account_no.isdigit()

class FileManager:
    """파일 관리 유틸리티"""
    
    @staticmethod
    def ensure_directory_exists(path: str):
        """디렉토리 존재 확인 및 생성"""
        os.makedirs(path, exist_ok=True)
    
    @staticmethod
    def backup_file(source_path: str, backup_dir: str = "backups") -> str:
        """파일 백업"""
        try:
            FileManager.ensure_directory_exists(backup_dir)
            
            filename = os.path.basename(source_path)
            timestamp = get_timestamp_string()
            backup_filename = f"{timestamp}_{filename}"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            import shutil
            shutil.copy2(source_path, backup_path)
            
            return backup_path
            
        except Exception as e:
            logging.getLogger(__name__).error(f"파일 백업 오류: {e}")
            return ""
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """파일 크기 조회"""
        try:
            return os.path.getsize(file_path)
        except:
            return 0

