"""
file: main.py
키움증권 모의투자 시스템 - 수정된 메인 실행 파일
"""

import sys
import os
import logging
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer

# 프로젝트 모듈들
from config import Config

class TradingSystem:
    """메인 거래 시스템"""
    
    def __init__(self):
        self.config = Config()
        self.app = None  # QApplication 참조 저장
        
        # 먼저 디렉토리 생성
        self.setup_directories()
        
        # 로깅 설정
        self.setup_logging()
        
        self.logger.info("거래 시스템 초기화 시작")
        
        # 나머지 컴포넌트들은 QApplication 생성 후에 초기화
        self.db_manager = None
        self.kiwoom_api = None
        self.trading_service = None
    
    def setup_directories(self):
        """필요한 디렉토리 생성 (QApplication 없이도 실행 가능)"""
        directories = ['logs', 'backups', 'data', 'exports']
        
        for directory in directories:
            try:
                os.makedirs(directory, exist_ok=True)
                print(f"📁 디렉토리 준비: {directory}")
            except Exception as e:
                print(f"❌ 디렉토리 생성 실패: {directory} - {e}")
    
    def setup_logging(self):
        """로깅 설정"""
        try:
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
            print("✅ 로깅 시스템 준비 완료")
            
        except Exception as e:
            print(f"❌ 로깅 설정 오류: {e}")
            # 기본 로깅이라도 설정
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger(__name__)
    
    def initialize_components(self):
        """QApplication 생성 후 컴포넌트 초기화"""
        try:
            # 데이터베이스 초기화
            from database import DatabaseManager
            self.db_manager = DatabaseManager()
            self.logger.info("데이터베이스 매니저 초기화 완료")
            
            # API 초기화
            from kiwoom_api import KiwoomAPI
            self.kiwoom_api = KiwoomAPI()
            self.logger.info("키움 API 초기화 완료")
            
            # 거래 서비스 초기화
            from trading_service import TradingService
            self.trading_service = TradingService(self.kiwoom_api, self.db_manager)
            self.logger.info("거래 서비스 초기화 완료")
            
            return True
            
        except Exception as e:
            self.logger.error(f"컴포넌트 초기화 오류: {e}")
            return False
    
    def initialize_api(self):
        """API 초기화"""
        try:
            if self.kiwoom_api and self.kiwoom_api.initialize():
                self.logger.info("키움 API 초기화 성공")
                
                if self.kiwoom_api.is_connected():
                    self.logger.info("키움 API 연결 확인됨")
                    return True
                else:
                    self.logger.warning("키움 API 연결되지 않음 - 모의 모드로 실행")
                    return False
            else:
                self.logger.error("키움 API 초기화 실패")
                return False
                
        except Exception as e:
            self.logger.error(f"API 초기화 오류: {e}")
            return False
    
    def run(self):
        """시스템 실행"""
        try:
            print("🎯 키움 모의투자 시스템 시작 중...")
            
            # 1. QApplication 먼저 생성
            self.app = QApplication(sys.argv)
            self.app.setApplicationName("키움 모의투자 시스템")
            print("✅ QApplication 생성 완료")
            
            # 2. QApplication 생성 후 컴포넌트 초기화
            if not self.initialize_components():
                if self.app:
                    QMessageBox.critical(None, "초기화 오류", 
                        "시스템 컴포넌트 초기화에 실패했습니다.\n"
                        "필요한 모듈들이 모두 설치되어 있는지 확인하세요.")
                return 1
            
            print("✅ 시스템 컴포넌트 초기화 완료")
            
            # 3. API 초기화 시도
            api_connected = self.initialize_api()
            print(f"✅ API 상태: {'연결됨' if api_connected else '모의 모드'}")
            
            # 4. 메인 윈도우 생성
            from gui_windows import MainWindow
            main_window = MainWindow(
                trading_service=self.trading_service,
                api_connected=api_connected
            )
            
            print("✅ 메인 윈도우 생성 완료")
            
            # 5. 윈도우 표시
            main_window.show()
            self.logger.info("시스템 실행 완료")
            print("🎉 모의투자 시스템이 시작되었습니다!")
            
            # 6. 이벤트 루프 시작
            return self.app.exec_()
            
        except Exception as e:
            self.logger.error(f"시스템 실행 오류: {e}") if hasattr(self, 'logger') else print(f"시스템 실행 오류: {e}")
            
            if self.app:
                QMessageBox.critical(None, "시스템 오류", 
                    f"시스템 실행 중 오류가 발생했습니다:\n{str(e)}")
            
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
        
        # 로그가 가능하면 로그에도 기록
        try:
            import logging
            logging.error(f"메인 함수 오류: {e}")
        except:
            pass
        
        return 1

if __name__ == "__main__":
    sys.exit(main())