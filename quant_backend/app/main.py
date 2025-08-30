# main.py - 환경 선택 기능과 전략 실행 통합
import asyncio
import sys
import argparse
from typing import Optional, List, Dict
from datetime import datetime

# 로컬 모듈 임포트
from config import EnvironmentSelector

class QuantTradingSystem:
    """퀀트 트레이딩 시스템 메인 클래스"""
    
    def __init__(self):
        self.env_selector: Optional[EnvironmentSelector] = None
        self.kis_auth = None
        self.kis_ws = None
        self.data_processor = None
        self.chart_manager = None
        self.auto_execute = False
        self.monitored_stocks = []
    
    async def initialize_environment(self, env_type: str = "interactive"):
        """환경 초기화"""
        try:
            # 지연 임포트로 순환 임포트 방지
            from services.kis_auth import KISAuth
            from services.kis_websocket import KISWebSocket
            from services.data_processor import TickDataProcessor, RealTimeChartManager
            
            print(f"\n시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 환경 선택
            self.env_selector = EnvironmentSelector()
            
            if env_type == "interactive":
                selected_env = self.env_selector.select_environment_interactive()
            else:
                selected_env = self.env_selector.select_environment_auto(env_type)
            
            # 선택된 환경 정보 출력
            self.env_selector.print_environment_info()
            
            # 인증 서비스 초기화
            print(f"\n인증 서비스 초기화 중...")
            self.kis_auth = KISAuth(
                app_key=selected_env.app_key,
                app_secret=selected_env.app_secret,
                base_url=selected_env.base_url,
                account_number=selected_env.account_number
            )
            
            # 토큰 발급 테스트
            await self.kis_auth.get_access_token()
            print(f"인증 완료")
            
            # 데이터 처리기 초기화
            self.data_processor = TickDataProcessor()
            self.chart_manager = RealTimeChartManager(self.data_processor)
            
            # WebSocket 서비스 초기화
            print(f"실시간 데이터 시스템 초기화 중...")
            self.kis_ws = KISWebSocket(self.kis_auth, selected_env.ws_url)
            
            print(f"환경 초기화 완료!")
            return selected_env
            
        except Exception as e:
            print(f"환경 초기화 실패: {e}")
            raise
    
    async def start_monitoring(self, stock_codes: List[str]):
        """모니터링 시작"""
        self.monitored_stocks = stock_codes
        
        try:
            # WebSocket 연결
            await self.kis_ws.connect()
            
            # 각 종목 구독
            for stock_code in stock_codes:
                await self.subscribe_stock(stock_code)
                await asyncio.sleep(1)  # API 안정성을 위한 지연
            
            print(f"\n모니터링 시작 완료")
            print(f"대상 종목: {', '.join(stock_codes)}")
            
        except Exception as e:
            print(f"모니터링 시작 실패: {e}")
            raise
    
    async def subscribe_stock(self, stock_code: str):
        """종목 구독 및 콜백 설정"""
        async def price_callback(tick_data):
            """실시간 가격 데이터 콜백"""
            # 데이터 처리
            await self.data_processor.process_tick(tick_data)
            
            # 차트 업데이트 브로드캐스트
            await self.chart_manager.broadcast_chart_update(stock_code, tick_data)
            
            # 전략 실행 (자동 모드인 경우)
            if self.auto_execute:
                await self.execute_strategy(tick_data)
        
        # WebSocket 구독
        await self.kis_ws.subscribe_realtime_price(stock_code, price_callback)
    
    async def execute_strategy(self, tick_data: Dict):
        """전략 실행 로직"""
        # 간단한 모멘텀 전략 예시
        stock_code = tick_data['code']
        price = tick_data['price']
        change_rate = tick_data['change_rate']
        
        # 급등/급락 감지
        if abs(change_rate) > 5.0:  # 5% 이상 변동
            if change_rate > 5.0:
                print(f"전략 신호 - {stock_code} 급등 감지: {change_rate:.2f}%")
            else:
                print(f"전략 신호 - {stock_code} 급락 감지: {change_rate:.2f}%")
    
    async def handle_user_commands(self):
        """사용자 명령 처리"""
        print(f"\n" + "="*60)
        print("사용 가능한 명령어:")
        print("  status  - 시스템 상태 확인")
        print("  chart   - 차트 상태 확인")
        print("  add     - 종목 추가 모니터링")
        print("  switch  - 환경 변경")
        print("  quit    - 종료")
        print("="*60)
        
        while True:
            try:
                print(f"\n명령 입력 (또는 Ctrl+C 종료): ", end="")
                command = input().strip().lower()
                
                if command == "status":
                    self.kis_ws.print_connection_status()
                    
                elif command == "chart":
                    self.chart_manager.print_chart_status()
                    
                elif command == "add":
                    print("추가할 종목코드 입력: ", end="")
                    stock_code = input().strip()
                    if stock_code:
                        await self.subscribe_stock(stock_code)
                        self.monitored_stocks.append(stock_code)
                        print(f"{stock_code} 모니터링 추가됨")
                        
                elif command == "switch":
                    await self.switch_environment()
                    
                elif command in ["quit", "exit", "q"]:
                    break
                    
                else:
                    print(f"알 수 없는 명령: {command}")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"명령 처리 오류: {e}")
    
    async def switch_environment(self):
        """실행 중 환경 변경"""
        try:
            # 지연 임포트
            from services.kis_auth import KISAuth
            from services.kis_websocket import KISWebSocket
            
            print(f"\n환경 변경 중...")
            
            # 기존 연결 종료
            if self.kis_ws:
                await self.kis_ws.disconnect()
            
            # 새 환경 선택
            new_env = self.env_selector.select_environment_interactive()
            
            # 새 인증 서비스 초기화
            self.kis_auth = KISAuth(
                app_key=new_env.app_key,
                app_secret=new_env.app_secret,
                base_url=new_env.base_url,
                account_number=new_env.account_number
            )
            
            await self.kis_auth.get_access_token()
            
            # 새 WebSocket 서비스 초기화
            self.kis_ws = KISWebSocket(self.kis_auth, new_env.ws_url)
            
            # 기존 모니터링 종목 재시작
            if self.monitored_stocks:
                await self.start_monitoring(self.monitored_stocks)
            
            print(f"{new_env.name} 환경으로 변경 완료!")
            self.env_selector.print_environment_info()
            
        except Exception as e:
            print(f"환경 변경 실패: {e}")
    
    async def cleanup(self):
        """시스템 정리"""
        if self.kis_ws:
            await self.kis_ws.disconnect()
        print("시스템 정리 완료")

def parse_arguments():
    """명령행 인수 파싱"""
    parser = argparse.ArgumentParser(description='KIS 실시간 퀀트 전략 시스템')
    parser.add_argument(
        '--env', 
        choices=['mock', 'real', 'interactive'], 
        default='interactive',
        help='실행 환경 선택'
    )
    parser.add_argument(
        '--stocks',
        nargs='+',
        default=['005930', '000660'],
        help='모니터링할 종목 코드'
    )
    parser.add_argument(
        '--auto-execute',
        action='store_true',
        help='자동 실행 모드 활성화'
    )
    
    return parser.parse_args()

def print_startup_banner():
    """시작 배너 출력"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                 KIS 실시간 퀀트 전략 시스템                   ║
    ║                                                              ║
    ║  실시간 모멘텀/역모멘텀 전략                                  ║
    ║  기술적 지표: RSI, 볼린저밴드, 이동평균                       ║
    ║  자동 재연결 및 안정성 보장                                   ║
    ║  모의투자/실전투자 환경 선택                                  ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

async def main():
    """메인 실행 함수"""
    system = QuantTradingSystem()
    
    try:
        # 명령행 인수 파싱
        args = parse_arguments()
        
        print("="*80)
        print("KIS 실시간 퀀트 전략 시스템")
        print("="*80)
        
        # 환경 초기화
        selected_env = await system.initialize_environment(args.env)
        
        # 전략 설정
        if args.auto_execute:
            system.auto_execute = True
            print(f"자동 실행 모드 활성화")
        else:
            print(f"수동 확인 모드 활성화")
        
        # 모니터링 시작
        print(f"\n실시간 모니터링 시작")
        await system.start_monitoring(args.stocks)
        
        # 사용자 명령 대기
        await system.handle_user_commands()
        
    except KeyboardInterrupt:
        print(f"\n\n사용자가 중단했습니다.")
    except Exception as e:
        print(f"시스템 오류: {e}")
    finally:
        await system.cleanup()

if __name__ == "__main__":
    print_startup_banner()
    
    # 명령행 사용법 안내
    if len(sys.argv) == 1:
        print("사용법:")
        print("  python main.py                           # 대화형 환경 선택")
        print("  python main.py --env mock                # 모의투자 자동 선택")
        print("  python main.py --env real                # 실전투자 자동 선택") 
        print("  python main.py --env mock --auto-execute # 모의투자 + 자동실행")
        print("  python main.py --stocks 005930 000660    # 특정 종목 모니터링")
        print()
    
    # 메인 실행
    asyncio.run(main())