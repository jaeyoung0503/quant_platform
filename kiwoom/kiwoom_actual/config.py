"""
시스템 설정 파일
"""

import os
from datetime import datetime

class Config:
    """시스템 전역 설정"""
    
    # 데이터베이스 설정
    DATABASE_PATH = "trading.db"
    BACKUP_PATH = "backups"
    
    # 로그 설정
    LOG_LEVEL = "INFO"
    LOG_FILE = f"logs/trading_{datetime.now().strftime('%Y%m%d')}.log"
    
    # 키움 API 설정
    MOCK_MODE = True  # 실제 API 연결 실패 시 모의 모드 사용
    
    # 거래 설정
    DEFAULT_ACCOUNT = "64531552"  # 투자 계좌
    INITIAL_BALANCE = 10000000  # 초기 잔고 (1천만원)
    
    # 매매 전략 설정
    MAX_POSITION_SIZE = 0.1  # 최대 포지션 크기 (10%)
    STOP_LOSS_RATE = 0.05    # 손절매 비율 (5%)
    TAKE_PROFIT_RATE = 0.1   # 익절매 비율 (10%)
    
    # 시장 시간 설정
    MARKET_OPEN_TIME = "09:00"
    MARKET_CLOSE_TIME = "15:30"
    
    # UI 설정
    WINDOW_TITLE = "키움증권 모의투자 시스템"
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 800
    
    # 데이터 업데이트 주기 (밀리초)
    UPDATE_INTERVAL = 5000  # 5초
    
    # 지원하는 주문 타입
    ORDER_TYPES = {
        '시장가매수': '03',
        '시장가매도': '02', 
        '지정가매수': '00',
        '지정가매도': '00'
    }
    
    # 자주 사용하는 종목 코드
    POPULAR_STOCKS = {
        '005930': '삼성전자',
        '000660': 'SK하이닉스',
        '035420': 'NAVER',
        '051910': 'LG화학',
        '006400': '삼성SDI',
        '035720': '카카오',
        '207940': '삼성바이오로직스',
        '373220': 'LG에너지솔루션'
    }
    
    @classmethod
    def get_stock_name(cls, stock_code):
        """종목코드로 종목명 조회"""
        return cls.POPULAR_STOCKS.get(stock_code, stock_code)
    
    @classmethod
    def is_market_open(cls):
        """장 개장 시간인지 확인"""
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        # 주말 체크
        if now.weekday() >= 5:  # 토요일(5), 일요일(6)
            return False
        
        # 시간 체크
        return cls.MARKET_OPEN_TIME <= current_time <= cls.MARKET_CLOSE_TIME
    
    @classmethod
    def ensure_directories(cls):
        """필요한 디렉토리 생성"""
        directories = [
            'logs',
            'backups', 
            'data',
            os.path.dirname(cls.LOG_FILE) if os.path.dirname(cls.LOG_FILE) else None
        ]
        
        for directory in directories:
            if directory:
                os.makedirs(directory, exist_ok=True)
