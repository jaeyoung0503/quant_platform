#file: quant_actual/backend/trading/engine.py

from sqlalchemy import create_engine, event, text  # text import 추가
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import sqlite3
from contextlib import contextmanager
import logging
from pathlib import Path
import threading
import time

from models import Base
from utils.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# 데이터베이스 파일 경로
DATABASE_DIR = Path("data")
DATABASE_DIR.mkdir(exist_ok=True)
DATABASE_URL = f"sqlite:///{DATABASE_DIR}/quantrade.db"

# SQLAlchemy 엔진 생성 - 연결 풀 설정 개선
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 10,
        "isolation_level": None
    },
    poolclass=StaticPool,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False,
    future=True
)

# 세션 팩토리
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    expire_on_commit=False
)

# 스레드 로컬 세션 관리
_session_registry = threading.local()

# SQLite 최적화 설정
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """SQLite 연결 시 성능 최적화 설정"""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        
        try:
            # 성능 최적화 설정
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL") 
            cursor.execute("PRAGMA cache_size=2000")
            cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA busy_timeout=5000")
            
            logger.debug("SQLite 최적화 설정 적용됨")
            
        except Exception as e:
            logger.warning(f"SQLite 설정 적용 중 오류: {e}")
        finally:
            cursor.close()

def init_db():
    """데이터베이스 초기화 - 수정됨"""
    try:
        logger.info("데이터베이스 초기화 시작...")
        
        # 데이터베이스 연결 테스트 - text() 사용
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1")).fetchone()
            logger.debug(f"데이터베이스 연결 테스트: {result}")
        
        # 모든 테이블 생성
        Base.metadata.create_all(bind=engine)
        logger.info("데이터베이스 테이블 생성 완료")
        
        # 초기 데이터 삽입
        create_initial_data_safe()
        logger.info("초기 데이터 생성 완료")
        
        return True
        
    except Exception as e:
        logger.error(f"데이터베이스 초기화 실패: {e}")
        return False

def check_database_health():
    """데이터베이스 상태 체크 - 수정됨"""
    try:
        start_time = time.time()
        
        with get_db_session() as db:
            # text() 사용하여 쿼리 실행
            result = db.execute(text("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")).fetchone()
            table_count = result[0] if result else 0
            
            # 각 주요 테이블 레코드 수 확인
            from models import Strategy, Stock, Portfolio
            
            strategy_count = db.query(Strategy).count()
            stock_count = db.query(Stock).count()
            portfolio_count = db.query(Portfolio).count()
            
        response_time = time.time() - start_time
        
        health_status = {
            "healthy": True,
            "response_time_ms": round(response_time * 1000, 2),
            "tables": table_count,
            "records": {
                "strategies": strategy_count,
                "stocks": stock_count,
                "portfolios": portfolio_count
            }
        }
        
        logger.debug(f"데이터베이스 상태: {health_status}")
        return health_status
        
    except Exception as e:
        logger.error(f"데이터베이스 상태 체크 실패: {e}")
        return {
            "healthy": False,
            "error": str(e),
            "response_time_ms": -1,
            "tables": 0,
            "records": {}
        }

# 나머지 함수들은 동일하게 유지...