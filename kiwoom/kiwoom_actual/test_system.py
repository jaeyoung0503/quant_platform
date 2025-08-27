"""
시스템 테스트용 파일 - 단계별 초기화 확인
"""

import sys
import os
import logging
from datetime import datetime

def test_step_1_directories():
    """1단계: 디렉토리 생성 테스트"""
    print("=" * 50)
    print("1단계: 디렉토리 생성 테스트")
    print("=" * 50)
    
    directories = ['logs', 'backups', 'data', 'exports']
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✓ {directory} 디렉토리 생성 성공")
        except Exception as e:
            print(f"✗ {directory} 디렉토리 생성 실패: {e}")
            return False
    
    print("✅ 1단계 완료\n")
    return True

def test_step_2_logging():
    """2단계: 로깅 시스템 테스트"""
    print("=" * 50)
    print("2단계: 로깅 시스템 테스트")
    print("=" * 50)
    
    try:
        log_file = f"logs/test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        logger = logging.getLogger("test")
        logger.info("테스트 로그 메시지")
        print(f"✓ 로그 파일 생성: {log_file}")
        print("✅ 2단계 완료\n")
        return True
        
    except Exception as e:
        print(f"✗ 로깅 시스템 실패: {e}")
        return False

def test_step_3_imports():
    """3단계: 모듈 임포트 테스트"""
    print("=" * 50)
    print("3단계: 모듈 임포트 테스트")
    print("=" * 50)
    
    modules_to_test = [
        ('PyQt5.QtWidgets', 'QApplication'),
        ('PyQt5.QtCore', 'QTimer'),
        ('config', 'Config'),
        ('database', 'DatabaseManager'),
    ]
    
    for module_name, class_name in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            print(f"✓ {module_name}.{class_name} 임포트 성공")
        except ImportError as e:
            print(f"✗ {module_name} 모듈 없음: {e}")
            return False
        except AttributeError as e:
            print(f"✗ {class_name} 클래스 없음: {e}")
            return False
        except Exception as e:
            print(f"✗ {module_name} 임포트 실패: {e}")
            return False
    
    print("✅ 3단계 완료\n")
    return True

def test_step_4_qapplication():
    """4단계: QApplication 생성 테스트"""
    print("=" * 50)
    print("4단계: QApplication 생성 테스트")
    print("=" * 50)
    
    try:
        from PyQt5.QtWidgets import QApplication
        
        # 기존 QApplication이 있으면 사용
        if QApplication.instance() is None:
            app = QApplication(sys.argv)
            print("✓ 새로운 QApplication 생성")
        else:
            app = QApplication.instance()
            print("✓ 기존 QApplication 사용")
        
        print(f"✓ QApplication 상태: {app.applicationName()}")
        print("✅ 4단계 완료\n")
        return True, app
        
    except Exception as e:
        print(f"✗ QApplication 생성 실패: {e}")
        return False, None

def test_step_5_database():
    """5단계: 데이터베이스 초기화 테스트"""
    print("=" * 50)
    print("5단계: 데이터베이스 초기화 테스트")
    print("=" * 50)
    
    try:
        from database import DatabaseManager
        
        db = DatabaseManager()
        print("✓ 데이터베이스 매니저 생성 성공")
        
        # 기본 계좌 정보 확인
        from config import Config
        account_info = db.get_account_info(Config.DEFAULT_ACCOUNT)
        
        if account_info:
            print(f"✓ 기본 계좌 정보: {account_info['account_no']}")
            print(f"✓ 초기 잔고: {account_info['balance']:,}원")
        else:
            print("✗ 기본 계좌 정보 없음")
            return False
        
        print("✅ 5단계 완료\n")
        return True, db
        
    except Exception as e:
        print(f"✗ 데이터베이스 초기화 실패: {e}")
        return False, None

def test_step_6_kiwoom_api():
    """6단계: 키움 API 초기화 테스트"""
    print("=" * 50)
    print("6단계: 키움 API 초기화 테스트")
    print("=" * 50)
    
    try:
        # 키움 API 가용성 확인
        try:
            from PyQt5.QAxContainer import QAxWidget
            print("✓ 키움 OpenAPI 라이브러리 사용 가능")
            kiwoom_available = True
        except ImportError:
            print("⚠ 키움 OpenAPI 라이브러리 없음 - 모의 모드만 가능")
            kiwoom_available = False
        
        # API 객체 생성 테스트
        from kiwoom_api import KiwoomAPI
        
        print("API 객체 생성 중...")
        api = KiwoomAPI()
        print("✓ 키움 API 객체 생성 성공")
        
        # 상태 확인
        if hasattr(api, 'get_api_status'):
            status = api.get_api_status()
            print(f"✓ API 상태: {status}")
        
        print("✅ 6단계 완료\n")
        return True, api
        
    except Exception as e:
        print(f"✗ 키움 API 초기화 실패: {e}")
        print("모의 모드로 계속 진행...")
        return False, None

def test_step_7_trading_service():
    """7단계: 거래 서비스 초기화 테스트"""
    print("=" * 50)
    print("7단계: 거래 서비스 초기화 테스트")
    print("=" * 50)
    
    try:
        from trading_service import TradingService
        from kiwoom_api import KiwoomAPI
        from database import DatabaseManager
        
        # 의존성 객체들 생성
        api = KiwoomAPI()
        db = DatabaseManager()
        
        # 거래 서비스 생성
        trading_service = TradingService(api, db)
        print("✓ 거래 서비스 생성 성공")
        
        # 기본 기능 테스트
        account_info = trading_service.get_account_info()
        if account_info:
            print(f"✓ 계좌 정보 조회 성공: {account_info['account_no']}")
        
        # 종목 정보 테스트
        stock_info = trading_service.get_stock_info("005930")
        if stock_info:
            print(f"✓ 종목 정보 조회 성공: {stock_info.get('stock_name', '삼성전자')}")
        
        print("✅ 7단계 완료\n")
        return True, trading_service
        
    except Exception as e:
        print(f"✗ 거래 서비스 초기화 실패: {e}")
        return False, None

def main():
    """메인 테스트 함수"""
    print("🚀 키움 모의투자 시스템 단계별 테스트 시작")
    print("=" * 60)
    
    # 1단계: 디렉토리
    if not test_step_1_directories():
        print("❌ 1단계 실패 - 테스트 중단")
        return 1
    
    # 2단계: 로깅
    if not test_step_2_logging():
        print("❌ 2단계 실패 - 테스트 중단")
        return 1
    
    # 3단계: 모듈 임포트
    if not test_step_3_imports():
        print("❌ 3단계 실패 - 테스트 중단")
        return 1
    
    # 4단계: QApplication
    success, app = test_step_4_qapplication()
    if not success:
        print("❌ 4단계 실패 - 테스트 중단")
        return 1
    
    # 5단계: 데이터베이스
    success, db = test_step_5_database()
    if not success:
        print("❌ 5단계 실패 - 테스트 중단")
        return 1
    
    # 6단계: 키움 API (실패해도 계속)
    api_success, api = test_step_6_kiwoom_api()
    if not api_success:
        print("⚠ 6단계 부분 실패 - 모의 모드로 계속")
    
    # 7단계: 거래 서비스
    success, trading_service = test_step_7_trading_service()
    if not success:
        print("❌ 7단계 실패 - 테스트 중단")
        return 1
    
    # 최종 결과
    print("=" * 60)
    print("🎉 모든 테스트 완료!")
    print("✅ 시스템이 정상적으로 초기화될 수 있습니다.")
    print()
    print("다음 명령으로 실제 시스템을 실행하세요:")
    print("  python main.py          # 모의투자 시스템")
    if api_success:
        print("  python real_main.py     # 실거래 시스템 (신중히!)")
    
    # GUI 테스트 옵션
    test_gui = input("\nGUI 테스트를 진행하시겠습니까? (y/N): ").strip().lower()
    
    if test_gui == 'y':
        print("\n🖥 GUI 테스트 시작...")
        try:
            from gui_windows import MainWindow
            
            main_window = MainWindow(trading_service, api_success)
            main_window.show()
            
            print("✓ GUI 윈도우가 표시되었습니다.")
            print("윈도우를 닫으면 테스트가 종료됩니다.")
            
            return app.exec_()
            
        except Exception as e:
            print(f"✗ GUI 테스트 실패: {e}")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())