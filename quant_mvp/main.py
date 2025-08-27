#file: quant_mvp/main.py
"""
나만의 전략 만들기
"""

import sys
import os
import json
from pathlib import Path
from ui.interactive import InteractiveMenu
from utils.helpers import setup_logging, create_output_directories

def load_config():
    """설정 파일 로드"""
    config_path = Path("config.json")
    if not config_path.exists():
        print("❌ config.json 파일을 찾을 수 없습니다.")
        sys.exit(1)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ config.json 파일 형식이 잘못되었습니다: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 설정 파일 로드 중 오류 발생: {e}")
        sys.exit(1)

def check_dependencies():
    """필수 디렉토리 및 파일 확인"""
    required_dirs = [
        "data/sample_data",
        "outputs/reports",
        "outputs/charts", 
        "outputs/logs"
    ]
    
    required_files = [
        "data/sample_data/market_prices.csv",
        "data/sample_data/financials.csv",
        "data/sample_data/market_data.csv"
    ]
    
    # 디렉토리 생성
    for dir_path in required_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    # 필수 파일 확인
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("⚠️  다음 샘플 데이터 파일들이 없습니다:")
        for file in missing_files:
            print(f"   - {file}")
        print("\n샘플 데이터를 생성하시겠습니까? [y/N]: ", end="")
        
        if input().lower().strip() == 'y':
            from data.data_loader import generate_sample_data
            print("📊 샘플 데이터를 생성중...")
            generate_sample_data()
            print("✅ 샘플 데이터 생성 완료")
        else:
            print("❌ 샘플 데이터 없이는 실행할 수 없습니다.")
            sys.exit(1)

def show_welcome():
    """환영 메시지 표시"""
    print("\n" + "="*60)
    print("🚀 Quant Strategy MVP - 퀀트 전략 백테스팅 시스템")
    print("="*60)
    print("📈 기술적 분석 전략: 모멘텀, RSI, 볼린저밴드, MACD")
    print("📊 재무 기반 전략: 가치투자, 성장투자, 퀄리티, 배당")
    print("🔄 혼합 전략: GARP, 모멘텀+밸류")
    print("💼 포트폴리오 최적화 및 리스크 관리")
    print("="*60 + "\n")

def main():
    """메인 함수"""
    try:
        # 환영 메시지
        show_welcome()
        
        # 설정 로드
        config = load_config()
        
        # 의존성 확인
        check_dependencies()
        
        # 로깅 설정
        setup_logging(config['output']['reports_dir'])
        
        # 출력 디렉토리 생성
        create_output_directories(config)
        
        # 인터랙티브 메뉴 시작
        menu = InteractiveMenu(config)
        menu.run()
        
    except KeyboardInterrupt:
        print("\n\n👋 프로그램을 종료합니다.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류가 발생했습니다: {e}")
        print("🐛 오류 세부사항은 로그 파일을 확인해주세요.")
        sys.exit(1)

if __name__ == "__main__":
    main()
    
    #
    
    #!/usr/bin/env python3
"""
Quant Strategy MVP - Main Entry Point
CLI 기반 퀀트 전략 백테스팅 시스템
"""

import sys
import os
import json
from pathlib import Path
from ui.interactive import InteractiveMenu
from utils.helpers import setup_logging, create_output_directories

def load_config():
    """설정 파일 로드"""
    config_path = Path("config.json")
    if not config_path.exists():
        print("❌ config.json 파일을 찾을 수 없습니다.")
        sys.exit(1)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ config.json 파일 형식이 잘못되었습니다: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 설정 파일 로드 중 오류 발생: {e}")
        sys.exit(1)

def check_dependencies():
    """필수 디렉토리 및 파일 확인"""
    required_dirs = [
        "data/sample_data",
        "outputs/reports",
        "outputs/charts", 
        "outputs/logs"
    ]
    
    required_files = [
        "data/sample_data/market_prices.csv",
        "data/sample_data/financials.csv",
        "data/sample_data/market_data.csv"
    ]
    
    # 디렉토리 생성
    for dir_path in required_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    # 필수 파일 확인
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("⚠️  다음 샘플 데이터 파일들이 없습니다:")
        for file in missing_files:
            print(f"   - {file}")
        print("\n샘플 데이터를 생성하시겠습니까? [y/N]: ", end="")
        
        if input().lower().strip() == 'y':
            from data.data_loader import generate_sample_data
            print("📊 샘플 데이터를 생성중...")
            generate_sample_data()
            print("✅ 샘플 데이터 생성 완료")
        else:
            print("❌ 샘플 데이터 없이는 실행할 수 없습니다.")
            sys.exit(1)

def show_welcome():
    """환영 메시지 표시"""
    print("\n" + "="*60)
    print("🚀 Quant Strategy MVP - 퀀트 전략 백테스팅 시스템")
    print("="*60)
    print("📈 기술적 분석 전략: 모멘텀, RSI, 볼린저밴드, MACD")
    print("📊 재무 기반 전략: 가치투자, 성장투자, 퀄리티, 배당")
    print("🔄 혼합 전략: GARP, 모멘텀+밸류")
    print("💼 포트폴리오 최적화 및 리스크 관리")
    print("="*60 + "\n")

def main():
    """메인 함수"""
    try:
        # 환영 메시지
        show_welcome()
        
        # 설정 로드
        config = load_config()
        
        # 의존성 확인
        check_dependencies()
        
        # 로깅 설정
        setup_logging(config['output']['reports_dir'])
        
        # 출력 디렉토리 생성
        create_output_directories(config)
        
        # 인터랙티브 메뉴 시작
        menu = InteractiveMenu(config)
        menu.run()
        
    except KeyboardInterrupt:
        print("\n\n👋 프로그램을 종료합니다.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류가 발생했습니다: {e}")
        print("🐛 오류 세부사항은 로그 파일을 확인해주세요.")
        sys.exit(1)

if __name__ == "__main__":
    main()