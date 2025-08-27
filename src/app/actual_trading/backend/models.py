# file: backend/models.py

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, validator
from enum import Enum

Base = declarative_base()

# Enum 정의
class OrderStatus(str, Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

class OrderType(str, Enum):
    BUY = "buy"
    SELL = "sell"

class StrategyType(str, Enum):
    BOLLINGER_BANDS = "bollinger_bands"
    RSI_REVERSAL = "rsi_reversal"
    MOMENTUM = "momentum"
    MOVING_AVERAGE = "moving_average"

# SQLAlchemy 모델 (데이터베이스 테이블)
class Strategy(Base):
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    strategy_type = Column(String)
    is_active = Column(Boolean, default=False)
    investment_amount = Column(Float)
    target_stocks = Column(Text)  # JSON 문자열로 저장
    parameters = Column(Text)  # JSON 문자열로 저장
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    orders = relationship("Order", back_populates="strategy")
    positions = relationship("Position", back_populates="strategy")

class Stock(Base):
    __tablename__ = "stocks"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)  # 종목코드 (예: 005930)
    name = Column(String)  # 종목명 (예: 삼성전자)
    market = Column(String)  # 시장구분 (KOSPI, KOSDAQ)
    current_price = Column(Float)
    prev_close = Column(Float)
    volume = Column(Integer)
    market_cap = Column(Float)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    orders = relationship("Order", back_populates="stock")
    positions = relationship("Position", back_populates="stock")
    price_history = relationship("PriceHistory", back_populates="stock")

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    stock_id = Column(Integer, ForeignKey("stocks.id"))
    order_type = Column(String)  # buy, sell
    quantity = Column(Integer)
    price = Column(Float)
    status = Column(String, default="pending")
    order_time = Column(DateTime, default=datetime.utcnow)
    fill_time = Column(DateTime)
    fill_price = Column(Float)
    fill_quantity = Column(Integer)
    commission = Column(Float, default=0.0)
    kiwoom_order_id = Column(String)  # 키움 API 주문번호
    
    # 관계 설정
    strategy = relationship("Strategy", back_populates="orders")
    stock = relationship("Stock", back_populates="orders")

class Position(Base):
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    stock_id = Column(Integer, ForeignKey("stocks.id"))
    quantity = Column(Integer)
    avg_price = Column(Float)
    current_price = Column(Float)
    unrealized_pnl = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    strategy = relationship("Strategy", back_populates="positions")
    stock = relationship("Stock", back_populates="positions")

class Portfolio(Base):
    __tablename__ = "portfolio"
    
    id = Column(Integer, primary_key=True, index=True)
    total_value = Column(Float)
    cash = Column(Float)
    invested_amount = Column(Float)
    realized_pnl = Column(Float, default=0.0)
    unrealized_pnl = Column(Float, default=0.0)
    daily_pnl = Column(Float, default=0.0)
    total_return = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow)

class PriceHistory(Base):
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"))
    price = Column(Float)
    volume = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # 관계 설정
    stock = relationship("Stock", back_populates="price_history")

class BacktestResult(Base):
    __tablename__ = "backtest_results"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_name = Column(String)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    total_return = Column(Float)
    annual_return = Column(Float)
    max_drawdown = Column(Float)
    sharpe_ratio = Column(Float)
    win_rate = Column(Float)
    total_trades = Column(Integer)
    results_data = Column(Text)  # JSON으로 상세 결과 저장
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic 모델 (API 요청/응답)
class StrategyBase(BaseModel):
    name: str
    strategy_type: StrategyType
    is_active: bool = False
    investment_amount: float
    target_stocks: list[str] = []
    parameters: dict = {}

class StrategyCreate(StrategyBase):
    pass

class StrategyUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    investment_amount: Optional[float] = None
    target_stocks: Optional[list[str]] = None
    parameters: Optional[dict] = None

class StrategyResponse(StrategyBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class StockBase(BaseModel):
    code: str
    name: str
    market: str = "KOSPI"

class StockResponse(StockBase):
    id: int
    current_price: Optional[float] = None
    prev_close: Optional[float] = None
    volume: Optional[int] = None
    updated_at: datetime
    
    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    strategy_id: int
    stock_code: str
    order_type: OrderType
    quantity: int
    price: float

class OrderCreate(OrderBase):
    pass

class OrderResponse(BaseModel):
    id: int
    strategy_id: int
    stock_code: str
    stock_name: str
    order_type: str
    quantity: int
    price: float
    status: str
    order_time: datetime
    fill_time: Optional[datetime] = None
    fill_price: Optional[float] = None
    fill_quantity: Optional[int] = None
    
    class Config:
        from_attributes = True

class PositionResponse(BaseModel):
    id: int
    strategy_name: str
    stock_code: str
    stock_name: str
    quantity: int
    avg_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float
    
    class Config:
        from_attributes = True

class PortfolioResponse(BaseModel):
    total_value: float
    cash: float
    invested_amount: float
    realized_pnl: float
    unrealized_pnl: float
    daily_pnl: float
    total_return: float
    timestamp: datetime
    
    class Config:
        from_attributes = True

class TradingSignal(BaseModel):
    stock_code: str
    strategy_name: str
    signal_type: OrderType
    quantity: int
    price: float
    confidence: float
    timestamp: datetime = datetime.now()

class BacktestRequest(BaseModel):
    strategy_type: StrategyType
    parameters: dict
    target_stocks: list[str]
    start_date: datetime
    end_date: datetime
    initial_capital: float = 10000000  # 1천만원

class BacktestResponse(BaseModel):
    total_return: float
    annual_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    total_trades: int
    strategy_performance: dict
    
    @validator('total_return', 'annual_return', 'max_drawdown', 'sharpe_ratio', 'win_rate')
    def round_percentages(cls, v):
        return round(v, 2)

class RiskMetrics(BaseModel):
    daily_loss_limit: float = -0.02  # -2%
    position_size_limit: float = 0.05  # 5%
    max_positions: int = 10
    current_daily_loss: float = 0.0
    is_safe_to_trade: bool = True

class MarketDataResponse(BaseModel):
    stock_code: str
    price: float
    volume: int
    timestamp: datetime
    
class SystemStatus(BaseModel):
    is_running: bool
    api_connected: bool
    active_strategies: int
    current_positions: int
    total_orders_today: int
    last_update: Optional[datetime] = None
