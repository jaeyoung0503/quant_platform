"""
file: kiwoom_mvp/config.py
키움증권 주식 데이터 수집기 - 설정 관리
Phase 1 MVP

전체 애플리케이션의 설정값을 통합 관리하는 모듈
환경변수, 기본값, 검증 등을 처리
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, Dict, Any

class Config:
    """애플리케이션 설정 관리 클래스"""
    
    def __init__(self):
        """설정 초기화"""
        # .env 파일 로드
        load_dotenv()
        
        # 기본 경로 설정
        self.BASE_DIR = Path(__file__).parent.absolute()
        
        # 설정 로드 및 검증
        self._load_kiwoom_settings()
        self._load_data_settings()
        self._load_file_settings()
        self._load_logging_settings()
        self._load_chart_settings()
        self._load_debug_settings()
        
        # 필수 디렉토리 생성
        self._create_directories()
        
    def _load_kiwoom_settings(self):
        """키움증권 관련 설정 로드"""
        self.KIWOOM_ID = os.getenv('KIWOOM_ID', '')
        self.KIWOOM_PASSWORD = os.getenv('KIWOOM_PASSWORD', '')
        self.KIWOOM_CERT_PASSWORD = os.getenv('KIWOOM_CERT_PASSWORD', '')
        
        # 필수 항목 검증
        if not self.KIWOOM_ID:
            print("⚠️  경고: KIWOOM_ID가 설정되지 않았습니다. .env 파일을 확인하세요.")
        if not self.KIWOOM_PASSWORD:
            print("⚠️  경고: KIWOOM_PASSWORD가 설정되지 않았습니다. .env 파일을 확인하세요.")
        if not self.KIWOOM_CERT_PASSWORD:
            print("⚠️  경고: KIWOOM_CERT_PASSWORD가 설정되지 않았습니다. .env 파일을 확인하세요.")
    
    def _load_data_settings(self):
        """데이터 수집 관련 설정 로드"""
        self.DEFAULT_PERIOD_DAYS = int(os.getenv('DEFAULT_PERIOD_DAYS', '30'))
        self.MAX_PERIOD_DAYS = int(os.getenv('MAX_PERIOD_DAYS', '365'))
        self.TR_REQUEST_INTERVAL = float(os.getenv('TR_REQUEST_INTERVAL', '0.2'))
        self.MAX_RETRY_COUNT = int(os.getenv('MAX_RETRY_COUNT', '3'))
        self.API_TIMEOUT = int(os.getenv('API_TIMEOUT', '30'))
        self.DATA_VALIDATION = os.getenv('DATA_VALIDATION', 'true').lower() == 'true'
        
        # 데이터 수집 제한값 검증
        if self.DEFAULT_PERIOD_DAYS > self.MAX_PERIOD_DAYS:
            self.DEFAULT_PERIOD_DAYS = self.MAX_PERIOD_DAYS
        if self.TR_REQUEST_INTERVAL < 0.1:  # 키움 제한 준수
            self.TR_REQUEST_INTERVAL = 0.2
    
    def _load_file_settings(self):
        """파일 저장 관련 설정 로드"""
        self.CSV_SAVE_PATH = Path(os.getenv('CSV_SAVE_PATH', './data/csv'))
        self.CHART_SAVE_PATH = Path(os.getenv('CHART_SAVE_PATH', './charts'))
        self.LOG_SAVE_PATH = Path(os.getenv('LOG_SAVE_PATH', './data/logs'))
        self.CSV_ENCODING = os.getenv('CSV_ENCODING', 'utf-8-sig')
        
        # 절대 경로로 변환
        if not self.CSV_SAVE_PATH.is_absolute():
            self.CSV_SAVE_PATH = self.BASE_DIR / self.CSV_SAVE_PATH
        if not self.CHART_SAVE_PATH.is_absolute():
            self.CHART_SAVE_PATH = self.BASE_DIR / self.CHART_SAVE_PATH
        if not self.LOG_SAVE_PATH.is_absolute():
            self.LOG_SAVE_PATH = self.BASE_DIR / self.LOG_SAVE_PATH
    
    def _load_logging_settings(self):
        """로깅 관련 설정 로드"""
        log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
        self.LOG_LEVEL = getattr(logging, log_level_str, logging.INFO)
        self.CONSOLE_LOG = os.getenv('CONSOLE_LOG', 'true').lower() == 'true'
        self.FILE_LOG = os.getenv('FILE_LOG', 'true').lower() == 'true'
    
    def _load_chart_settings(self):
        """차트 관련 설정 로드"""
        self.AUTO_OPEN_CHART = os.getenv('AUTO_OPEN_CHART', 'true').lower() == 'true'
        self.CHART_THEME = os.getenv('CHART_THEME', 'plotly_white')
        self.CHART_WIDTH = int(os.getenv('CHART_WIDTH', '1200'))
        self.CHART_HEIGHT = int(os.getenv('CHART_HEIGHT', '600'))
        
        # 차트 크기 검증
        if self.CHART_WIDTH < 400:
            self.CHART_WIDTH = 800
        if self.CHART_HEIGHT < 300:
            self.CHART_HEIGHT = 600
    
    def _load_debug_settings(self):
        """디버깅 관련 설정 로드"""
        self.DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
        self.PAPER_TRADING = os.getenv('PAPER_TRADING', 'true').lower() == 'true'
    
    def _create_directories(self):
        """필수 디렉토리 생성"""
        directories = [
            self.CSV_SAVE_PATH,
            self.CHART_SAVE_PATH,
            self.LOG_SAVE_PATH,
            self.BASE_DIR / 'data'
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_csv_filename(self, stock_code: str, stock_name: str, 
                        start_date: str, end_date: str, data_type: str = 'daily') -> str:
        """CSV 파일명 생성"""
        safe_name = self._sanitize_filename(stock_name)
        return f"{stock_code}_{safe_name}_{data_type}_{start_date}_{end_date}.csv"
    
    def get_chart_filename(self, stock_code: str, stock_name: str, 
                          chart_type: str = '캔들차트') -> str:
        """차트 파일명 생성"""
        safe_name = self._sanitize_filename(stock_name)
        from datetime import datetime
        today = datetime.now().strftime('%Y%m%d')
        return f"{stock_code}_{safe_name}_{chart_type}_{today}.html"
    
    def get_log_filename(self, log_type: str = 'app') -> str:
        """로그 파일명 생성"""
        from datetime import datetime
        today = datetime.now().strftime('%Y%m%d')
        return f"{log_type}_{today}.log"
    
    def _sanitize_filename(self, filename: str) -> str:
        """파일명에서 특수문자 제거"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename
    
    def validate_stock_code(self, stock_code: str) -> bool:
        """종목코드 유효성 검증"""
        if not stock_code:
            return False
        
        # 6자리 숫자인지 확인
        if len(stock_code) != 6:
            return False
        
        if not stock_code.isdigit():
            return False
        
        return True
    
    def validate_date_range(self, start_date: str, end_date: str) -> bool:
        """날짜 범위 유효성 검증"""
        try:
            from datetime import datetime
            start = datetime.strptime(start_date, '%Y%m%d')
            end = datetime.strptime(end_date, '%Y%m%d')
            
            # 시작일이 종료일보다 이후인지 확인
            if start > end:
                return False
            
            # 최대 기간을 초과하지 않는지 확인
            days_diff = (end - start).days
            if days_diff > self.MAX_PERIOD_DAYS:
                return False
            
            return True
        except ValueError:
            return False
    
    def get_setting_summary(self) -> Dict[str, Any]:
        """현재 설정값 요약 반환"""
        return {
            'data_collection': {
                'default_period': self.DEFAULT_PERIOD_DAYS,
                'max_period': self.MAX_PERIOD_DAYS,
                'tr_interval': self.TR_REQUEST_INTERVAL,
                'max_retry': self.MAX_RETRY_COUNT
            },
            'file_paths': {
                'csv_path': str(self.CSV_SAVE_PATH),
                'chart_path': str(self.CHART_SAVE_PATH),
                'log_path': str(self.LOG_SAVE_PATH)
            },
            'chart_options': {
                'auto_open': self.AUTO_OPEN_CHART,
                'theme': self.CHART_THEME,
                'width': self.CHART_WIDTH,
                'height': self.CHART_HEIGHT
            },
            'debug': {
                'debug_mode': self.DEBUG_MODE,
                'log_level': logging.getLevelName(self.LOG_LEVEL),
                'data_validation': self.DATA_VALIDATION
            }
        }
    
    def has_kiwoom_credentials(self) -> bool:
        """키움증권 계정 정보가 설정되어 있는지 확인"""
        return bool(self.KIWOOM_ID and self.KIWOOM_PASSWORD and self.KIWOOM_CERT_PASSWORD)

# 전역 설정 인스턴스
config = Config()

# 편의 함수들
def get_config() -> Config:
    """설정 인스턴스 반환"""
    return config

def print_config_summary():
    """설정 요약 출력"""
    print("=" * 50)
    print("📊 키움증권 주식 데이터 수집기 - 설정 정보")
    print("=" * 50)
    
    summary = config.get_setting_summary()
    
    print(f"🔧 데이터 수집 설정:")
    print(f"   - 기본 수집 기간: {summary['data_collection']['default_period']}일")
    print(f"   - 최대 수집 기간: {summary['data_collection']['max_period']}일")
    print(f"   - TR 요청 간격: {summary['data_collection']['tr_interval']}초")
    print(f"   - 최대 재시도: {summary['data_collection']['max_retry']}회")
    
    print(f"\n📁 파일 저장 경로:")
    print(f"   - CSV: {summary['file_paths']['csv_path']}")
    print(f"   - 차트: {summary['file_paths']['chart_path']}")
    print(f"   - 로그: {summary['file_paths']['log_path']}")
    
    print(f"\n📈 차트 설정:")
    print(f"   - 자동 열기: {summary['chart_options']['auto_open']}")
    print(f"   - 테마: {summary['chart_options']['theme']}")
    print(f"   - 크기: {summary['chart_options']['width']}x{summary['chart_options']['height']}")
    
    print(f"\n🐛 디버그 설정:")
    print(f"   - 디버그 모드: {summary['debug']['debug_mode']}")
    print(f"   - 로그 레벨: {summary['debug']['log_level']}")
    print(f"   - 데이터 검증: {summary['debug']['data_validation']}")
    
    print(f"\n🔐 계정 정보:")
    print(f"   - 키움 계정 설정: {'✅ 완료' if config.has_kiwoom_credentials() else '❌ 미설정'}")
    
    print("=" * 50)

if __name__ == "__main__":
    # 설정 테스트
    print_config_summary()
    
    # 테스트 케이스
    print("\n🧪 설정 검증 테스트:")
    print(f"종목코드 검증 (005930): {config.validate_stock_code('005930')}")
    print(f"종목코드 검증 (12345): {config.validate_stock_code('12345')}")
    print(f"날짜 범위 검증: {config.validate_date_range('20240701', '20240731')}")
    print(f"CSV 파일명: {config.get_csv_filename('005930', '삼성전자', '20240701', '20240731')}")
    print(f"차트 파일명: {config.get_chart_filename('005930', '삼성전자')}")