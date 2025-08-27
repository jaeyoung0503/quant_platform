"""
file: kiwoom_mock/database.py
데이터베이스 관리 모듈
"""

import sqlite3
import logging
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from config import Config

class DatabaseManager:
    """데이터베이스 관리 클래스"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.DATABASE_PATH
        self.logger = logging.getLogger(__name__)
        self.initialize_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """데이터베이스 연결 생성"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def initialize_database(self):
        """데이터베이스 테이블 초기화"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 계좌 정보 테이블
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    account_no TEXT PRIMARY KEY,
                    account_name TEXT,
                    balance INTEGER DEFAULT 0,
                    buying_power INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')
                
                # 종목 정보 테이블
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS stocks (
                    stock_code TEXT PRIMARY KEY,
                    stock_name TEXT,
                    market_type TEXT,
                    sector TEXT,
                    current_price INTEGER DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')
                
                # 포트폴리오 테이블
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS portfolio (
                    account_no TEXT,
                    stock_code TEXT,
                    quantity INTEGER DEFAULT 0,
                    avg_price INTEGER DEFAULT 0,
                    current_price INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (account_no, stock_code),
                    FOREIGN KEY (account_no) REFERENCES accounts (account_no),
                    FOREIGN KEY (stock_code) REFERENCES stocks (stock_code)
                )
                ''')
                
                # 주문 내역 테이블
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_no TEXT,
                    stock_code TEXT,
                    order_type TEXT,
                    order_status TEXT DEFAULT '접수',
                    quantity INTEGER,
                    price INTEGER,
                    executed_quantity INTEGER DEFAULT 0,
                    executed_price INTEGER DEFAULT 0,
                    order_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    executed_time TIMESTAMP,
                    FOREIGN KEY (account_no) REFERENCES accounts (account_no),
                    FOREIGN KEY (stock_code) REFERENCES stocks (stock_code)
                )
                ''')
                
                # 거래 내역 테이블
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_no TEXT,
                    stock_code TEXT,
                    transaction_type TEXT,
                    quantity INTEGER,
                    price INTEGER,
                    amount INTEGER,
                    fee INTEGER DEFAULT 0,
                    transaction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_no) REFERENCES accounts (account_no),
                    FOREIGN KEY (stock_code) REFERENCES stocks (stock_code)
                )
                ''')
                
                # 기본 계좌 생성
                cursor.execute('''
                INSERT OR IGNORE INTO accounts (account_no, account_name, balance, buying_power)
                VALUES (?, ?, ?, ?)
                ''', (Config.DEFAULT_ACCOUNT, "모의투자계좌", Config.INITIAL_BALANCE, Config.INITIAL_BALANCE))
                
                conn.commit()
                self.logger.info("데이터베이스 초기화 완료")
                
        except Exception as e:
            self.logger.error(f"데이터베이스 초기화 오류: {e}")
            raise
    
    def get_account_info(self, account_no: str) -> Optional[Dict]:
        """계좌 정보 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM accounts WHERE account_no = ?", (account_no,))
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            self.logger.error(f"계좌 정보 조회 오류: {e}")
            return None
    
    def update_account_balance(self, account_no: str, balance: int, buying_power: int = None):
        """계좌 잔고 업데이트"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if buying_power is None:
                    buying_power = balance
                
                cursor.execute('''
                UPDATE accounts 
                SET balance = ?, buying_power = ?, updated_at = CURRENT_TIMESTAMP
                WHERE account_no = ?
                ''', (balance, buying_power, account_no))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"계좌 잔고 업데이트 오류: {e}")
            return False
    
    def save_stock_info(self, stock_code: str, stock_name: str, current_price: int):
        """종목 정보 저장"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                INSERT OR REPLACE INTO stocks 
                (stock_code, stock_name, current_price, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (stock_code, stock_name, current_price))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"종목 정보 저장 오류: {e}")
            return False
    
    def get_portfolio(self, account_no: str) -> List[Dict]:
        """포트폴리오 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT p.*, s.stock_name 
                FROM portfolio p
                LEFT JOIN stocks s ON p.stock_code = s.stock_code
                WHERE p.account_no = ? AND p.quantity > 0
                ORDER BY p.updated_at DESC
                ''', (account_no,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"포트폴리오 조회 오류: {e}")
            return []
    
    def update_portfolio(self, account_no: str, stock_code: str, quantity: int, avg_price: int):
        """포트폴리오 업데이트"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 기존 보유량 확인
                cursor.execute('''
                SELECT quantity, avg_price FROM portfolio 
                WHERE account_no = ? AND stock_code = ?
                ''', (account_no, stock_code))
                
                existing = cursor.fetchone()
                
                if existing:
                    # 기존 보유 종목 업데이트
                    old_qty = existing['quantity']
                    old_avg = existing['avg_price']
                    
                    new_qty = old_qty + quantity
                    
                    if new_qty > 0:
                        # 평균단가 재계산
                        total_amount = (old_qty * old_avg) + (quantity * avg_price)
                        new_avg = total_amount // new_qty
                        
                        cursor.execute('''
                        UPDATE portfolio 
                        SET quantity = ?, avg_price = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE account_no = ? AND stock_code = ?
                        ''', (new_qty, new_avg, account_no, stock_code))
                    else:
                        # 수량이 0 이하면 삭제
                        cursor.execute('''
                        DELETE FROM portfolio 
                        WHERE account_no = ? AND stock_code = ?
                        ''', (account_no, stock_code))
                else:
                    # 신규 종목 추가
                    if quantity > 0:
                        cursor.execute('''
                        INSERT INTO portfolio 
                        (account_no, stock_code, quantity, avg_price)
                        VALUES (?, ?, ?, ?)
                        ''', (account_no, stock_code, quantity, avg_price))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"포트폴리오 업데이트 오류: {e}")
            return False
    
    def save_order(self, account_no: str, stock_code: str, order_type: str, 
                   quantity: int, price: int) -> Optional[int]:
        """주문 저장"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                INSERT INTO orders 
                (account_no, stock_code, order_type, quantity, price)
                VALUES (?, ?, ?, ?, ?)
                ''', (account_no, stock_code, order_type, quantity, price))
                
                order_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"주문 저장 완료: ID {order_id}")
                return order_id
                
        except Exception as e:
            self.logger.error(f"주문 저장 오류: {e}")
            return None
    
    def update_order_status(self, order_id: int, status: str, 
                           executed_quantity: int = 0, executed_price: int = 0):
        """주문 상태 업데이트"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                UPDATE orders 
                SET order_status = ?, executed_quantity = ?, executed_price = ?,
                    executed_time = CASE WHEN ? = '체결' THEN CURRENT_TIMESTAMP ELSE executed_time END
                WHERE id = ?
                ''', (status, executed_quantity, executed_price, status, order_id))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"주문 상태 업데이트 오류: {e}")
            return False
    
    def get_orders(self, account_no: str, status: str = None) -> List[Dict]:
        """주문 내역 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if status:
                    cursor.execute('''
                    SELECT o.*, s.stock_name 
                    FROM orders o
                    LEFT JOIN stocks s ON o.stock_code = s.stock_code
                    WHERE o.account_no = ? AND o.order_status = ?
                    ORDER BY o.order_time DESC
                    ''', (account_no, status))
                else:
                    cursor.execute('''
                    SELECT o.*, s.stock_name 
                    FROM orders o
                    LEFT JOIN stocks s ON o.stock_code = s.stock_code
                    WHERE o.account_no = ?
                    ORDER BY o.order_time DESC
                    ''', (account_no,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"주문 내역 조회 오류: {e}")
            return []
    
    def save_transaction(self, account_no: str, stock_code: str, transaction_type: str,
                        quantity: int, price: int, fee: int = 0) -> bool:
        """거래 내역 저장"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                amount = quantity * price
                
                cursor.execute('''
                INSERT INTO transactions 
                (account_no, stock_code, transaction_type, quantity, price, amount, fee)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (account_no, stock_code, transaction_type, quantity, price, amount, fee))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"거래 내역 저장 오류: {e}")
            return False
    
    def get_transactions(self, account_no: str, start_date: str = None) -> List[Dict]:
        """거래 내역 조회"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if start_date:
                    cursor.execute('''
                    SELECT t.*, s.stock_name 
                    FROM transactions t
                    LEFT JOIN stocks s ON t.stock_code = s.stock_code
                    WHERE t.account_no = ? AND DATE(t.transaction_time) >= ?
                    ORDER BY t.transaction_time DESC
                    ''', (account_no, start_date))
                else:
                    cursor.execute('''
                    SELECT t.*, s.stock_name 
                    FROM transactions t
                    LEFT JOIN stocks s ON t.stock_code = s.stock_code
                    WHERE t.account_no = ?
                    ORDER BY t.transaction_time DESC
                    LIMIT 100
                    ''', (account_no,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"거래 내역 조회 오류: {e}")
            return []
    
    def backup_database(self) -> bool:
        """데이터베이스 백업"""
        try:
            backup_dir = Config.BACKUP_PATH
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"trading_backup_{timestamp}.db")
            
            # 파일 복사
            import shutil
            shutil.copy2(self.db_path, backup_path)
            
            self.logger.info(f"데이터베이스 백업 완료: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"데이터베이스 백업 오류: {e}")
            return False
    
    def cleanup_old_data(self, days: int = 30):
        """오래된 데이터 정리"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 30일 이전 거래 내역 삭제
                cursor.execute('''
                DELETE FROM transactions 
                WHERE transaction_time < datetime('now', '-{} days')
                '''.format(days))
                
                # 체결되지 않은 오래된 주문 삭제
                cursor.execute('''
                DELETE FROM orders 
                WHERE order_status != '체결' 
                AND order_time < datetime('now', '-{} days')
                '''.format(days))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                self.logger.info(f"오래된 데이터 정리 완료: {deleted_count}건 삭제")
                return True
                
        except Exception as e:
            self.logger.error(f"데이터 정리 오류: {e}")
            return False

def initialize_database():
    """데이터베이스 초기화 실행"""
    try:
        print("데이터베이스 초기화 중...")
        
        # 설정에서 디렉토리 생성
        Config.ensure_directories()
        
        # 데이터베이스 매니저 생성 (자동으로 초기화됨)
        db_manager = DatabaseManager()
        
        print("✓ 데이터베이스 초기화 완료")
        print(f"✓ 데이터베이스 파일: {db_manager.db_path}")
        
        # 기본 계좌 확인
        account_info = db_manager.get_account_info(Config.DEFAULT_ACCOUNT)
        if account_info:
            print(f"✓ 기본 계좌 설정됨: {account_info['account_no']}")
            print(f"✓ 초기 잔고: {account_info['balance']:,}원")
        
        return True
        
    except Exception as e:
        print(f"✗ 데이터베이스 초기화 실패: {e}")
        return False

if __name__ == "__main__":
    initialize_database()