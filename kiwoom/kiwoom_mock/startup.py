"""
file: kiwoom_mock/startup.py
키움증권 모의투자 시스템 시작 스크립트
"""

import sys
import os

def check_requirements():
    """필수 요구사항 확인"""
    print("키움증권 모의투자 시스템")
    print("=" * 40)
    print("시스템 요구사항 확인 중...")
    
    # Python 버전 확인
    if sys.version_info < (3, 7):
        print("✗ Python 3.7 이상이 필요합니다")
        return False
    else:
        print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # PyQt5 확인
    try:
        from PyQt5.QtWidgets import QApplication
        print("✓ PyQt5 사용 가능")
    except ImportError:
        print("✗ PyQt5가 설치되지 않음")
        print("  설치 명령: pip install PyQt5")
        return False
    
    # pandas 확인 (선택사항)
    try:
        import pandas
        print("✓ pandas 사용 가능")
    except ImportError:
        print("⚠ pandas 권장 (선택사항)")
        print("  설치 명령: pip install pandas")
    
    # 디렉토리 생성
    directories = ['logs', 'backups', 'data', 'exports']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    print("✓ 디렉토리 생성 완료")
    
    return True

def initialize_system():
    """시스템 초기화"""
    try:
        print("\n시스템 초기화 중...")
        
        # 데이터베이스 초기화
        from database import initialize_database
        if initialize_database():
            print("✓ 데이터베이스 초기화 완료")
        else:
            print("✗ 데이터베이스 초기화 실패")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ 시스템 초기화 오류: {e}")
        return False

def start_application():
    """애플리케이션 시작"""
    try:
        print("\n애플리케이션 시작 중...")
        
        from main import main
        return main()
        
    except Exception as e:
        print(f"✗ 애플리케이션 시작 오류: {e}")
        return 1

def main():
    """메인 함수"""
    try:
        # 1. 요구사항 확인
        if not check_requirements():
            print("\n시스템 요구사항을 만족하지 않습니다.")
            input("Enter 키를 눌러 종료...")
            return 1
        
        # 2. 시스템 초기화
        if not initialize_system():
            print("\n시스템 초기화에 실패했습니다.")
            input("Enter 키를 눌러 종료...")
            return 1
        
        # 3. 애플리케이션 시작
        print("\n✅ 모든 준비 완료")
        print("애플리케이션을 시작합니다...\n")
        
        return start_application()
        
    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단됨")
        return 0
    except Exception as e:
        print(f"\n시작 스크립트 오류: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())