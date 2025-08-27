# file: backend/database.py - Simplified version

import sqlite3
import os
import logging
from pathlib import Path
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# 데이터베이스 파일 경로
DATABASE_DIR = Path("data")
DATABASE_DIR.mkdir(exist_ok=True)
DATABASE_FILE = DATABASE_DIR / "quantrade.db"

def init_db():
    """데이터베이스 초기화 - 테이블 생성"""
    try:
        with sqlite3.connect(DATABASE_FILE) as conn:
            cursor = conn.cursor()
            
            # 기본 테이블들 생성
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS strategies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    strategy_type TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 0,
                    investment_amount REAL,
                    target_stocks TEXT,
                    parameters TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    market TEXT DEFAULT 'KOSPI',
                    current_price REAL,
                    prev_close REAL,
                    volume INTEGER,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_id INTEGER,
                    stock_code TEXT,
                    order_type TEXT,
                    quantity INTEGER,
                    price REAL,
                    status TEXT DEFAULT 'pending',
                    order_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fill_time TIMESTAMP,
                    fill_price REAL,
                    FOREIGN KEY (strategy_id) REFERENCES strategies (id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS portfolio (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    total_value REAL,
                    cash REAL,
                    invested_amount REAL,
                    realized_pnl REAL DEFAULT 0,
                    unrealized_pnl REAL DEFAULT 0,
                    daily_pnl REAL DEFAULT 0,
                    total_return REAL DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            
            # 초기 데이터 삽입
            insert_initial_data(cursor)
            conn.commit()
            
        logger.info("데이터베이스 초기화 완료")
        
    except Exception as e:
        logger.error(f"데이터베이스 초기화 실패: {e}")
        # 에러가 나더라도 계속 진행 (메모리 모드로 동작)

def insert_initial_data(cursor):
    """초기 데이터 삽입"""
    try:
        # 주요 종목 데이터
        stocks_data = [
            ("005930", "삼성전자", "KOSPI", 71200, 70800, 12450000),
            ("000660", "SK하이닉스", "KOSPI", 124500, 123000, 8200000),
            ("035420", "NAVER", "KOSPI", 198000, 195000, 1800000),
            ("035720", "카카오", "KOSPI", 89500, 87200, 3200000),
            ("051910", "LG화학", "KOSPI", 486000, 482000, 450000),
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO stocks (code, name, market, current_price, prev_close, volume)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', stocks_data)
        
        # 기본 전략 데이터
        strategies_data = [
            ("볼린저밴드 평균회귀", "bollinger_bands", 1, 10000000.0, 
             '["005930", "000660", "035420"]', 
             '{"period": 20, "std_multiplier": 2.0, "stop_loss": 0.05, "take_profit": 0.03}'),
            ("RSI 역추세", "rsi_reversal", 1, 8000000.0,
             '["035720", "051910"]',
             '{"period": 14, "oversold": 30, "overbought": 70, "stop_loss": 0.04}'),
            ("모멘텀 추세추종", "momentum", 0, 5000000.0,
             '["006400", "207940"]',
             '{"short_period": 12, "long_period": 26, "signal_period": 9}'),
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO strategies (name, strategy_type, is_active, investment_amount, target_stocks, parameters)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', strategies_data)
        
        # 초기 포트폴리오
        cursor.execute('''
            INSERT OR IGNORE INTO portfolio (total_value, cash, invested_amount, realized_pnl, unrealized_pnl, daily_pnl, total_return)
            VALUES (50000000.0, 24000000.0, 26000000.0, 0.0, 0.0, 0.0, 0.0)
        ''')
        
    except Exception as e:
        logger.error(f"초기 데이터 삽입 실패: {e}")

@contextmanager
def get_db_session():
    """데이터베이스 세션 컨텍스트 매니저"""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
        yield conn
    except Exception as e:
        logger.error(f"데이터베이스 오류: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def get_db():
    """FastAPI 의존성 주입용 - 호환성을 위한 함수"""
    # 실제로는 SQLAlchemy 세션을 반환해야 하지만, 
    # 간단한 구현을 위해 현재는 패스
    pass

class DatabaseManager:
    """데이터베이스 관리 클래스"""
    
    @staticmethod
    def update_stock_price(stock_code: str, price: float, volume: int = 0):
        """종목 가격 업데이트"""
        try:
            with get_db_session() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE stocks SET current_price = ?, volume = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE code = ?
                ''', (price, volume, stock_code))
                conn.commit()
        except Exception as e:
            logger.error(f"종목 가격 업데이트 실패 {stock_code}: {e}")
    
    @staticmethod
    def cleanup_old_data(days: int = 30):
        """오래된 데이터 정리"""
        try:
            with get_db_session() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM portfolio WHERE timestamp < datetime('now', '-{} days')
                '''.format(days))
                conn.commit()
                logger.info(f"{days}일 이전 데이터 정리 완료")
        except Exception as e:
            logger.error(f"데이터 정리 실패: {e}")

def backup_database(backup_path: str = None):
    """데이터베이스 백업"""
    try:
        if not backup_path:
            backup_dir = Path("backups")
            backup_dir.mkdir(exist_ok=True)
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"quantrade_backup_{timestamp}.db"
        
        import shutil
        shutil.copy2(DATABASE_FILE, backup_path)
        logger.info(f"데이터베이스 백업 완료: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"데이터베이스 백업 실패: {e}")
        raise

def check_database_health():
    """데이터베이스 상태 체크"""
    try:
        with get_db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error(f"데이터베이스 연결 실패: {e}")
        return False