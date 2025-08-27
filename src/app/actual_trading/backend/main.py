# file: backend/main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import uvicorn
from datetime import datetime
import logging
import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/quantrade.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# 로그 디렉토리 생성
os.makedirs('logs', exist_ok=True)
os.makedirs('data', exist_ok=True)

from database import init_db
from api import router
from trading_mode_api import router as mode_router, get_current_trading_mode, get_current_kiwoom_client
from trading_engine_manager import TradingEngine, get_trading_engine, set_trading_engine

# 전역 변수
trading_engine = None
background_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 실행될 로직"""
    global trading_engine, background_task
    
    logger.info("퀀트 트레이딩 시스템 시작 중...")
    
    try:
        # 데이터베이스 초기화
        init_db()
        
        # 초기 거래 모드 설정 (환경변수 또는 기본값)
        initial_mode = os.getenv("INITIAL_TRADING_MODE", "DEMO")
        logger.info(f"초기 거래 모드: {initial_mode}")
        
        # 키움 클라이언트 초기화 (모드에 따라)
        kiwoom_client = None
        if initial_mode == "REAL":
            try:
                # Windows 환경 체크
                import platform
                if platform.system() != "Windows":
                    logger.warning("실거래 모드는 Windows에서만 지원됩니다. Demo 모드로 전환합니다.")
                    initial_mode = "DEMO"
                else:
                    try:
                        from kiwoom_real_api import get_kiwoom_real_client
                        kiwoom_client = get_kiwoom_real_client()
                        if not await kiwoom_client.initialize():
                            logger.error("실거래 클라이언트 초기화 실패. Demo 모드로 전환합니다.")
                            initial_mode = "DEMO"
                            kiwoom_client = None
                    except ImportError as e:
                        logger.error(f"실거래 모듈 import 실패: {e}. Demo 모드로 전환합니다.")
                        initial_mode = "DEMO"
                        kiwoom_client = None
            except Exception as e:
                logger.error(f"실거래 클라이언트 초기화 오류: {e}. Demo 모드로 전환합니다.")
                initial_mode = "DEMO"
                kiwoom_client = None
        
        # Demo 모드 클라이언트 초기화
        if initial_mode == "DEMO" or kiwoom_client is None:
            try:
                from data.kiwoom_mock import KiwoomClient
                kiwoom_client = KiwoomClient()
                await kiwoom_client.connect()
            except Exception as e:
                logger.error(f"Mock 클라이언트 초기화 실패: {e}")
                # 기본 더미 클라이언트 생성
                class DummyClient:
                    def __init__(self):
                        self.is_connected = True
                    async def connect(self): pass
                    async def disconnect(self): pass
                kiwoom_client = DummyClient()
        
        # 거래 모드 API에 클라이언트 설정
        try:
            import trading_mode_api
            trading_mode_api.CURRENT_TRADING_MODE = initial_mode
            trading_mode_api.KIWOOM_CLIENT_INSTANCE = kiwoom_client
        except Exception as e:
            logger.warning(f"거래 모드 API 설정 실패: {e}")
        
        # 트레이딩 엔진 초기화
        trading_engine = TradingEngine()
        trading_engine.kiwoom_client = kiwoom_client
        await trading_engine.initialize()
        
        # 전역 트레이딩 엔진 설정
        set_trading_engine(trading_engine)
        
        # 백그라운드 트레이딩 루프 시작
        background_task = asyncio.create_task(trading_engine.run())
        
        logger.info(f"시스템 초기화 완료 - 모드: {initial_mode}")
        
    except Exception as e:
        logger.error(f"시스템 초기화 실패: {e}")
        # 기본 설정으로라도 시작
        trading_engine = TradingEngine()
        set_trading_engine(trading_engine)
    
    yield
    
    # 시스템 종료 시 정리
    logger.info("시스템 종료 중...")
    if background_task:
        background_task.cancel()
        try:
            await background_task
        except asyncio.CancelledError:
            pass
    if trading_engine:
        await trading_engine.shutdown()
    logger.info("시스템 종료 완료")

# FastAPI 앱 생성
app = FastAPI(
    title="QuanTrade Pro API",
    description="퀀트 자동매매 시스템 API - Mock/Real 모드 지원",
    version="1.1.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(router, prefix="/api")
app.include_router(mode_router, prefix="/api")

@app.get("/")
async def root():
    """기본 엔드포인트"""
    try:
        current_mode = get_current_trading_mode()
    except:
        current_mode = "UNKNOWN"
    
    return {
        "message": "QuanTrade Pro API",
        "version": "1.1.0",
        "status": "running",
        "trading_mode": current_mode,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    global trading_engine
    
    try:
        engine_status = "running" if trading_engine and trading_engine.is_running else "stopped"
        
        try:
            current_mode = get_current_trading_mode()
            kiwoom_client = get_current_kiwoom_client()
            api_connected = kiwoom_client.is_connected if kiwoom_client else False
        except:
            current_mode = "UNKNOWN"
            api_connected = False
        
        return {
            "status": "healthy",
            "trading_engine": engine_status,
            "trading_mode": current_mode,
            "api_connection": api_connected,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"헬스 체크 실패: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/trading/status")
async def get_trading_status():
    """트레이딩 시스템 상태 조회"""
    global trading_engine
    
    if not trading_engine:
        return {
            "error": "Trading engine not initialized",
            "is_running": False,
            "trading_mode": "UNKNOWN"
        }
    
    try:
        current_mode = get_current_trading_mode()
        kiwoom_client = get_current_kiwoom_client()
    except:
        current_mode = "UNKNOWN"
        kiwoom_client = None
    
    return {
        "is_running": trading_engine.is_running,
        "trading_mode": current_mode,
        "api_connected": kiwoom_client.is_connected if kiwoom_client else False,
        "active_strategies": len(trading_engine.get_active_strategies()),
        "current_positions": len(trading_engine.get_current_positions()),
        "total_orders_today": trading_engine.get_daily_order_count(),
        "last_update": trading_engine.last_update.isoformat() if trading_engine.last_update else None
    }

# 개발용 편의 엔드포인트
@app.get("/dev/info")
async def development_info():
    """개발 정보"""
    import platform
    import sys
    
    try:
        current_mode = get_current_trading_mode()
        kiwoom_client = get_current_kiwoom_client()
    except:
        current_mode = "UNKNOWN"
        kiwoom_client = None
    
    return {
        "system": {
            "os": platform.system(),
            "python_version": sys.version,
            "trading_mode": current_mode
        },
        "client": {
            "type": type(kiwoom_client).__name__ if kiwoom_client else None,
            "connected": kiwoom_client.is_connected if kiwoom_client else False
        },
        "engine": {
            "running": trading_engine.is_running if trading_engine else False,
            "strategies": len(trading_engine.get_active_strategies()) if trading_engine else 0
        }
    }

if __name__ == "__main__":
    # 환경변수에서 설정 로드
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "False").lower() == "true"
    
    logger.info(f"서버 시작: http://{host}:{port}")
    logger.info(f"API 문서: http://{host}:{port}/docs")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )