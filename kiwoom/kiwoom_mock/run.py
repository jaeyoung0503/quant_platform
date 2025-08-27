#file: kiwoom_mock/run.py
"""
키움증권 모의투자 시스템 - 간단 실행 스크립트
"""

import sys
import os

def main():
    """메인 실행 함수"""
    print("키움증권 모의투자 시스템")
    print("=" * 30)
    
    try:
        # 필수 패키지 확인
        try:
            from PyQt5.QtWidgets import QApplication
        except ImportError:
            print("PyQt5가 설치되지 않았습니다.")
            print("설치 명령: pip install PyQt5")
            return 1
        
        # 디렉토리 생성
        for directory in ['logs', 'backups', 'data']:
            os.makedirs(directory, exist_ok=True)
        
        # 데이터베이스 초기화
        print("데이터베이스 초기화 중...")
        from database import initialize_database
        
        if not initialize_database():
            print("데이터베이스 초기화 실패")
            return 1
        
        # 메인 시스템 실행
        print("시스템 시작 중...")
        from main import main as main_func
        
        return main_func()
        
    except Exception as e:
        print(f"실행 오류: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())