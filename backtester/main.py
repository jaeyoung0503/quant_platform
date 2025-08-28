"""
File: main.py
처음 화면 엔진
Quantitative Trading Strategy Backtester
Main execution script
"""

import sys
import os
import time
from datetime import datetime

# Add the project root directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from backtester.core import QuantBacktester
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("프로젝트 구조를 확인하고 필요한 패키지를 설치했는지 확인하세요.")
    sys.exit(1)

def display_banner():
    """Display application banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║        🚀 QUANTITATIVE TRADING STRATEGY BACKTESTER 2.0 🚀                   ║
║                                                                              ║
║                    📊 Advanced Multi-Strategy Analysis System                ║
║                                                                              ║
║  ✨ Features:                                                                ║
║     • 10년 장기 백테스팅                                                     ║
║     • 4가지 핵심 투자 전략                                                   ║
║     • 멀티종목 포트폴리오 분석                                               ║
║     • 실시간 성과 시각화                                                     ║
║     • 리스크 관리 시스템                                                     ║
║                                                                              ║
║  🎯 Supported Strategies:                                                    ║
║     1. PER Value Strategy        - 가치투자 전략                             ║
║     2. RSI Mean Reversion        - 평균회귀 전략                             ║
║     3. Moving Average Trend      - 추세추종 전략                             ║
║     4. TOP 10 Composite          - 종합지표 전략                             ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)

def display_system_info():
    """Display system information"""
    print(f"📅 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python 버전: {sys.version.split()[0]}")
    print(f"📁 작업 디렉토리: {os.getcwd()}")
    print("-" * 80)

def check_system_requirements():
    """Check if all required packages are available"""
    required_packages = [
        'pandas', 'numpy', 'matplotlib', 'plotly'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"⚠️ 다음 패키지가 설치되지 않았습니다: {', '.join(missing_packages)}")
        print("다음 명령어로 설치하세요:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def show_quick_help():
    """Show quick help information"""
    help_text = """
🔍 Quick Start Guide:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣ 전략 선택
   • 1-4 사이의 숫자를 입력하여 전략을 선택하세요
   • '숫자 info'를 입력하면 전략 상세 정보를 볼 수 있습니다 (예: 1 info)

2️⃣ 백테스팅 실행
   • 선택한 전략으로 10년간의 백테스팅이 자동 실행됩니다
   • 여러 종목에 대해 개별적으로 분석됩니다

3️⃣ 결과 분석
   • 종목별 성과가 수익률 순으로 정렬되어 표시됩니다
   • 샤프비율, 최대낙폭, 승률 등 핵심 지표를 확인하세요

4️⃣ 시각화 (선택사항)
   • 성과 차트를 생성하여 상세한 분석을 할 수 있습니다
   • HTML 대시보드와 PNG 차트 파일이 생성됩니다

💡 Tips:
   • 여러 전략을 비교해보세요
   • 각 전략의 특성을 이해하고 시장 상황에 맞는 전략을 선택하세요
   • 백테스팅 결과는 과거 데이터 기반이므로 참고용으로만 사용하세요

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    print(help_text)

def main():
    """Main execution function"""
    try:
        # Clear screen (optional)
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Display banner and system info
        display_banner()
        display_system_info()
        
        # Check system requirements
        print("🔍 시스템 요구사항 확인 중...")
        if not check_system_requirements():
            print("\n❌ 시스템 요구사항을 만족하지 않습니다.")
            input("Press Enter to exit...")
            return
        
        print("✅ 시스템 요구사항 확인 완료!")
        
        # Show quick help
        show_help = input("\n📖 사용 가이드를 보시겠습니까? (y/n): ").strip().lower()
        if show_help in ['y', 'yes', '네', 'ㅇ']:
            show_quick_help()
        
        # Initialize and run backtester
        print("\n🚀 퀀트 백테스터를 초기화하는 중...")
        
        # Add a small delay for dramatic effect
        time.sleep(1)
        
        backtester = QuantBacktester()
        print("✅ 초기화 완료!")
        
        # Run the backtester
        backtester.run()
        
    except KeyboardInterrupt:
        print(f"\n\n👋 사용자에 의해 프로그램이 종료되었습니다.")
        print("언제든지 다시 실행해주세요!")
        
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류가 발생했습니다: {str(e)}")
        print("\n🔧 문제 해결 방법:")
        print("1. 모든 필수 패키지가 설치되었는지 확인하세요")
        print("2. Python 버전이 3.7 이상인지 확인하세요") 
        print("3. 프로젝트 폴더 구조가 올바른지 확인하세요")
        print("\n💬 지속적인 문제가 발생하면 개발팀에 문의해주세요.")
        
        # Debug information
        import traceback
        print(f"\n🐛 Debug Information:")
        print("-" * 50)
        print(traceback.format_exc())
        
    finally:
        print(f"\n⏰ 종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        input("Press Enter to close...")

if __name__ == "__main__":
    main()