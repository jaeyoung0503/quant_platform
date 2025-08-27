# file: backend/api.py - Simplified version to fix imports

from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime, timedelta
import json
import logging
from typing import List, Dict, Any, Optional

# Simple database for testing
from database import get_db_session, init_db

logger = logging.getLogger(__name__)
router = APIRouter()

# Mock data for testing when database is not available
MOCK_PORTFOLIO = {
    "total_value": 50000000.0,
    "cash": 24000000.0,
    "invested_amount": 26000000.0,
    "realized_pnl": 120000.0,
    "unrealized_pnl": 340000.0,
    "daily_pnl": 89000.0,
    "total_return": 0.92,
    "timestamp": datetime.now().isoformat()
}

MOCK_POSITIONS = [
    {
        "id": 1,
        "strategy_name": "볼린저밴드 평균회귀",
        "stock_code": "005930",
        "stock_name": "삼성전자",
        "quantity": 100,
        "avg_price": 71200,
        "current_price": 72100,
        "unrealized_pnl": 90000,
        "realized_pnl": 0
    },
    {
        "id": 2,
        "strategy_name": "RSI 역추세",
        "stock_code": "035720",
        "stock_name": "카카오",
        "quantity": 200,
        "avg_price": 89500,
        "current_price": 91000,
        "unrealized_pnl": 300000,
        "realized_pnl": 50000
    }
]

MOCK_ORDERS = [
    {
        "id": 1,
        "strategy_id": 1,
        "stock_code": "005930",
        "stock_name": "삼성전자",
        "order_type": "buy",
        "quantity": 100,
        "price": 71200,
        "status": "filled",
        "order_time": (datetime.now() - timedelta(hours=2)).isoformat(),
        "fill_time": (datetime.now() - timedelta(hours=2)).isoformat(),
        "fill_price": 71200
    },
    {
        "id": 2,
        "strategy_id": 2,
        "stock_code": "035720",
        "stock_name": "카카오",
        "order_type": "buy",
        "quantity": 200,
        "price": 89500,
        "status": "filled",
        "order_time": (datetime.now() - timedelta(hours=1)).isoformat(),
        "fill_time": (datetime.now() - timedelta(hours=1)).isoformat(),
        "fill_price": 89500
    }
]

MOCK_STRATEGIES = [
    {
        "id": 1,
        "name": "볼린저밴드 평균회귀",
        "strategy_type": "bollinger_bands",
        "is_active": True,
        "investment_amount": 10000000.0,
        "target_stocks": ["005930", "000660", "035420"],
        "parameters": {
            "period": 20,
            "std_multiplier": 2.0,
            "stop_loss": 0.05,
            "take_profit": 0.03
        },
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    },
    {
        "id": 2,
        "name": "RSI 역추세",
        "strategy_type": "rsi_reversal", 
        "is_active": True,
        "investment_amount": 8000000.0,
        "target_stocks": ["035720", "051910"],
        "parameters": {
            "period": 14,
            "oversold": 30,
            "overbought": 70,
            "stop_loss": 0.04
        },
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    },
    {
        "id": 3,
        "name": "모멘텀 추세추종",
        "strategy_type": "momentum",
        "is_active": False,
        "investment_amount": 5000000.0,
        "target_stocks": ["006400", "207940"],
        "parameters": {
            "short_period": 12,
            "long_period": 26,
            "signal_period": 9
        },
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
]

@router.get("/portfolio")
async def get_portfolio_status():
    """포트폴리오 현황 조회"""
    try:
        # Update with some variation for realism
        portfolio = MOCK_PORTFOLIO.copy()
        portfolio["timestamp"] = datetime.now().isoformat()
        return portfolio
    except Exception as e:
        logger.error(f"포트폴리오 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch portfolio")

@router.get("/portfolio/positions")
async def get_current_positions():
    """현재 포지션 조회"""
    try:
        return MOCK_POSITIONS
    except Exception as e:
        logger.error(f"포지션 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch positions")

@router.get("/strategies")
async def get_strategies():
    """전략 목록 조회"""
    try:
        return MOCK_STRATEGIES
    except Exception as e:
        logger.error(f"전략 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch strategies")

@router.post("/strategies/toggle")
async def toggle_strategy(request: dict):
    """전략 활성화/비활성화"""
    try:
        strategy_id = request.get("id")
        new_active_state = request.get("active", False)
        
        # Find and update strategy in mock data
        for strategy in MOCK_STRATEGIES:
            if strategy["id"] == strategy_id:
                strategy["is_active"] = new_active_state
                strategy["updated_at"] = datetime.now().isoformat()
                break
        
        status = "활성화" if new_active_state else "비활성화"
        logger.info(f"전략 {status}: {strategy_id}")
        
        return {
            "success": True,
            "message": f"전략이 {status}되었습니다.",
            "strategy_id": strategy_id,
            "is_active": new_active_state
        }
    except Exception as e:
        logger.error(f"전략 토글 실패: {e}")
        raise HTTPException(status_code=500, detail="Failed to toggle strategy")

@router.get("/orders")
async def get_recent_orders(limit: int = 50, status: Optional[str] = None):
    """최근 주문 내역 조회"""
    try:
        orders = MOCK_ORDERS.copy()
        if status:
            orders = [order for order in orders if order["status"] == status]
        return orders[:limit]
    except Exception as e:
        logger.error(f"주문 내역 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch orders")

@router.post("/trading/start")
async def start_trading():
    """자동매매 시작"""
    try:
        from trading_engine_manager import get_trading_engine
        trading_engine = get_trading_engine()
        await trading_engine.start_trading()
        
        logger.info("자동매매 시작됨")
        return {"success": True, "message": "자동매매가 시작되었습니다."}
        
    except Exception as e:
        logger.error(f"자동매매 시작 실패: {e}")
        raise HTTPException(status_code=500, detail="Failed to start trading")

@router.post("/trading/stop")
async def stop_trading():
    """자동매매 중지"""
    try:
        from trading_engine_manager import get_trading_engine
        trading_engine = get_trading_engine()
        await trading_engine.stop_trading()
        
        logger.info("자동매매 중지됨")
        return {"success": True, "message": "자동매매가 중지되었습니다."}
        
    except Exception as e:
        logger.error(f"자동매매 중지 실패: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop trading")

@router.post("/trading/emergency-stop")
async def emergency_stop():
    """긴급 중단"""
    try:
        from trading_engine_manager import get_trading_engine
        trading_engine = get_trading_engine()
        await trading_engine.emergency_stop()
        
        logger.critical("긴급중단 실행됨")
        return {"success": True, "message": "긴급중단이 실행되었습니다."}
        
    except Exception as e:
        logger.error(f"긴급중단 실패: {e}")
        raise HTTPException(status_code=500, detail="Failed to emergency stop")

@router.get("/stocks")
async def get_stocks():
    """종목 목록 조회"""
    try:
        # Mock stock data
        stocks = [
            {"id": 1, "code": "005930", "name": "삼성전자", "market": "KOSPI", "current_price": 72100, "updated_at": datetime.now().isoformat()},
            {"id": 2, "code": "000660", "name": "SK하이닉스", "market": "KOSPI", "current_price": 124500, "updated_at": datetime.now().isoformat()},
            {"id": 3, "code": "035420", "name": "NAVER", "market": "KOSPI", "current_price": 198000, "updated_at": datetime.now().isoformat()},
            {"id": 4, "code": "035720", "name": "카카오", "market": "KOSPI", "current_price": 91000, "updated_at": datetime.now().isoformat()},
        ]
        return stocks
    except Exception as e:
        logger.error(f"종목 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stocks")

@router.get("/system/status")
async def get_system_status():
    """시스템 상태 조회"""
    try:
        from trading_engine_manager import get_trading_engine
        trading_engine = get_trading_engine()
        
        return {
            "is_running": trading_engine.is_running if trading_engine else False,
            "api_connected": True,  # Mock connection
            "active_strategies": len([s for s in MOCK_STRATEGIES if s["is_active"]]),
            "current_positions": len(MOCK_POSITIONS),
            "total_orders_today": len(MOCK_ORDERS),
            "last_update": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"시스템 상태 조회 실패: {e}")
        return {
            "is_running": False,
            "api_connected": False,
            "active_strategies": 0,
            "current_positions": 0,
            "total_orders_today": 0,
            "last_update": datetime.now().isoformat(),
            "error": str(e)
        }

@router.get("/realtime/market-data")
async def get_realtime_market_data():
    """실시간 시장 데이터 조회"""
    try:
        # Mock market data
        market_data = {
            "005930": {"current_price": 72100, "volume": 12450000, "timestamp": datetime.now().isoformat()},
            "035720": {"current_price": 91000, "volume": 3200000, "timestamp": datetime.now().isoformat()},
        }
        return market_data
    except Exception as e:
        logger.error(f"실시간 데이터 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch market data")

@router.get("/realtime/signals")
async def get_recent_signals(limit: int = 20):
    """최근 트레이딩 신호 조회"""
    try:
        # Mock signals
        signals = []
        return signals
    except Exception as e:
        logger.error(f"신호 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch signals")