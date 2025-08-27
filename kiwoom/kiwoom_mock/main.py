"""
file: kiwoom_mock/main.py
키움증권 모의투자 시스템 - 메인 실행 파일
"""

import sys
import os
import logging
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer

# 프로젝트 모듈들
from config import Config
from database import DatabaseManager

class TradingSystem:
    """메인 거래 시스템"""
    
    def __init__(self):
        self.config = Config()
        self.setup_logging()
        self.setup_directories()
        
        # 데이터베이스 초기화
        self.db_manager = DatabaseManager()
        
        self.logger.info("거래 시스템 초기화 완료")
    
    def setup_logging(self):
        """로깅 설정"""
        log_level = getattr(logging, self.config.LOG_LEVEL)
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.LOG_FILE, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("로깅 시스템 초기화 완료")
    
    def setup_directories(self):
        """필요한 디렉토리 생성"""
        directories = ['logs', 'backups', 'data']
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
        
        self.logger.info("디렉토리 설정 완료")
    
    def initialize_api_and_services(self):
        """API 및 서비스 초기화 (QApplication 생성 후)"""
        self.kiwoom_api = None
        self.trading_service = None
        
        try:
            from kiwoom_api import KiwoomAPI
            from trading_service import TradingService
            
            # API 초기화
            self.kiwoom_api = KiwoomAPI()
            api_connected = self.kiwoom_api.initialize()
            
            # 서비스 초기화
            self.trading_service = TradingService(self.kiwoom_api, self.db_manager)
            
            if api_connected:
                self.logger.info("API 및 서비스 초기화 성공")
            else:
                self.logger.info("모의 모드로 서비스 초기화 완료")
            
            return api_connected
                
        except Exception as e:
            self.logger.error(f"API 및 서비스 초기화 오류: {e}")
            
            # 에러 발생 시에도 기본 서비스는 반드시 생성
            try:
                if self.kiwoom_api is None:
                    from kiwoom_api import KiwoomAPI
                    self.kiwoom_api = KiwoomAPI()
                
                if self.trading_service is None:
                    from trading_service import TradingService
                    self.trading_service = TradingService(self.kiwoom_api, self.db_manager)
                
                self.logger.info("기본 서비스 초기화 완료 (모의 모드)")
                return False
                
            except Exception as e2:
                self.logger.error(f"기본 서비스 초기화도 실패: {e2}")
                # 최후의 수단으로 None이라도 설정
                if self.trading_service is None:
                    self.trading_service = None
                raise e2
    
    def run(self):
        """시스템 실행"""
        try:
            # Qt 애플리케이션 생성 (가장 먼저)
            app = QApplication(sys.argv)
            app.setApplicationName("키움 모의투자 시스템")
            
            self.logger.info("QApplication 생성 완료")
            
            # API 및 서비스 초기화 (QApplication 생성 후)
            api_connected = self.initialize_api_and_services()
            
            # trading_service가 제대로 생성되었는지 확인
            if not hasattr(self, 'trading_service') or self.trading_service is None:
                self.logger.error("거래 서비스 생성 실패")
                QMessageBox.critical(None, "초기화 오류", "거래 서비스를 초기화할 수 없습니다.")
                return 1
            
            # 메인 윈도우 생성
            from gui_windows import MainWindow
            main_window = MainWindow(
                trading_service=self.trading_service,
                api_connected=api_connected
            )
            
            # 윈도우 표시
            main_window.show()
            
            self.logger.info("시스템 실행 완료")
            
            # 이벤트 루프 시작
            return app.exec_()
            
        except Exception as e:
            self.logger.error(f"시스템 실행 오류: {e}")
            
            if 'app' in locals():
                QMessageBox.critical(None, "시스템 오류", f"시스템 실행 중 오류가 발생했습니다:\n{str(e)}")
            else:
                print(f"시스템 오류: {e}")
            
            return 1

def main():
    """메인 함수"""
    try:
        print("키움증권 모의투자 시스템 시작...")
        print("=" * 50)
        
        # 시스템 생성 및 실행
        trading_system = TradingSystem()
        exit_code = trading_system.run()
        
        print("시스템 종료")
        return exit_code
        
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단됨")
        return 0
    except Exception as e:
        print(f"시스템 오류: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())