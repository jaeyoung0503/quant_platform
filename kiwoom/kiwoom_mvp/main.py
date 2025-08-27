""" file: stock_data_mvp/main.py
키증권 주식 데이터 수집기 - 메인 실행 파일
Phase 1 MVP

CLI 인터페이스를 통한 전체 애플리케이션 실행
사용자 메뉴, 종목 검색, 데이터 수집, 차트 생성 통합
"""

import sys
import os
import logging
import signal
from datetime import datetime
from typing import Optional, List, Dict, Any

# 모듈 import
from config import get_config, print_config_summary
from kiwoom_api import get_kiwoom_manager, KiwoomAPI
from stock_searcher import get_stock_searcher
from data_manager import get_data_manager  
from chart_viewer import get_chart_viewer
from connection_monitor import get_connection_monitor, ConnectionStatus

class StockDataCollector:
    """주식 데이터 수집기 메인 클래스"""
    
    def __init__(self):
        """메인 애플리케이션 초기화"""
        # 설정 및 로깅
        self.config = get_config()
        self.logger = self._setup_logging()
        
        # 컴포넌트 초기화
        self.kiwoom_manager = get_kiwoom_manager()
        self.stock_searcher = get_stock_searcher() 
        self.data_manager = get_data_manager()
        self.chart_viewer = get_chart_viewer()
        self.connection_monitor = get_connection_monitor()
        
        # 키움 API 인스턴스
        self.kiwoom_api: Optional[KiwoomAPI] = None
        
        # 프로그램 상태
        self.running = True
        self.connected = False
        
        # 시그널 핸들러 등록
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _setup_logging(self) -> logging.Logger:
        """로깅 설정"""
        logger = logging.getLogger(__name__)
        
        # 로그 포맷터
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 콘솔 핸들러
        if self.config.CONSOLE_LOG:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(self.config.LOG_LEVEL)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # 파일 핸들러
        if self.config.FILE_LOG:
            log_file = self.config.LOG_SAVE_PATH / self.config.get_log_filename('main')
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(self.config.LOG_LEVEL)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        logger.setLevel(self.config.LOG_LEVEL)
        return logger
    
    def _signal_handler(self, signum, frame):
        """시그널 핸들러 (Ctrl+C 등)"""
        print("\n\n🛑 프로그램 종료 요청 받음...")
        self.shutdown()
        sys.exit(0)
    
    def startup(self) -> bool:
        """애플리케이션 시작"""
        try:
            self._print_startup_banner()
            
            # 설정 검증
            if not self._validate_configuration():
                return False
            
            # 키움 API 초기화
            if not self._initialize_kiwoom():
                return False
            
            # 연결 모니터링 시작
            self.connection_monitor.start_monitoring()
            
            self.logger.info("✅ 애플리케이션 시작 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 애플리케이션 시작 실패: {e}")
            return False
    
    def _print_startup_banner(self):
        """시작 배너 출력"""
        print("=" * 60)
        print("📈 키움증권 주식 데이터 수집기 v1.0")
        print("   Phase 1 MVP - 데이터 수집 & 차트 생성")
        print("=" * 60)
        print(f"🕐 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
    
    def _validate_configuration(self) -> bool:
        """설정 검증"""
        self.logger.info("🔧 설정 검증 중...")
        
        # 키움 계정 정보 확인
        if not self.config.has_kiwoom_credentials():
            print("❌ 키움증권 계정 정보가 설정되지 않았습니다.")
            print("   .env 파일에서 KIWOOM_ID, KIWOOM_PASSWORD, KIWOOM_CERT_PASSWORD를 설정하세요.")
            return False
        
        # 필수 디렉토리 확인 (이미 config에서 생성되지만 재확인)
        required_dirs = [
            self.config.CSV_SAVE_PATH,
            self.config.CHART_SAVE_PATH,
            self.config.LOG_SAVE_PATH
        ]
        
        for directory in required_dirs:
            if not directory.exists():
                try:
                    directory.mkdir(parents=True, exist_ok=True)
                    self.logger.info(f"📁 디렉토리 생성: {directory}")
                except Exception as e:
                    self.logger.error(f"❌ 디렉토리 생성 실패 ({directory}): {e}")
                    return False
        
        self.logger.info("✅ 설정 검증 완료")
        return True
    
    def _initialize_kiwoom(self) -> bool:
        """키움 API 초기화"""
        self.logger.info("🔄 키움 API 초기화 중...")
        
        # 진단 시작
        self.connection_monitor.start_diagnostic()
        
        try:
            # 1단계: 환경 확인
            self.connection_monitor.update_diagnostic_step(1, "running", "환경 확인 중...")
            
            # PyQt5 및 키움 API 모듈 확인은 import에서 이미 처리됨
            self.connection_monitor.update_diagnostic_step(1, "success", "환경 확인 완료")
            
            # 2단계: COM 객체 생성
            self.connection_monitor.update_diagnostic_step(2, "running", "키움 API 초기화 중...")
            
            if not self.kiwoom_manager.initialize():
                self.connection_monitor.update_diagnostic_step(2, "failed", "키움 API 초기화 실패")
                return False
            
            self.kiwoom_api = self.kiwoom_manager.get_api()
            if not self.kiwoom_api or not self.kiwoom_api.connected:
                self.connection_monitor.update_diagnostic_step(2, "failed", "COM 객체 생성 실패")
                return False
            
            self.connection_monitor.update_diagnostic_step(2, "success", "COM 객체 생성 완료")
            
            # 3단계: 로그인 시도
            self.connection_monitor.update_diagnostic_step(3, "running", "키움 서버 로그인 중...")
            self.connection_monitor.set_status(ConnectionStatus.CONNECTING, "키움 서버 연결 시도")
            
            if not self.kiwoom_manager.connect():
                self.connection_monitor.update_diagnostic_step(3, "failed", "로그인 실패")
                self.connection_monitor.set_status(ConnectionStatus.ERROR, "로그인 실패")
                return False
            
            self.connection_monitor.update_diagnostic_step(3, "success", "로그인 성공")
            
            # 4단계: 계좌 정보 확인
            self.connection_monitor.update_diagnostic_step(4, "running", "계좌 정보 조회 중...")
            
            connection_info = self.kiwoom_api.get_connection_info()
            if connection_info['account_count'] == 0:
                self.connection_monitor.update_diagnostic_step(4, "failed", "사용 가능한 계좌 없음")
                self.connection_monitor.set_status(ConnectionStatus.ERROR, "계좌 정보 없음")
                return False
            
            self.connection_monitor.update_diagnostic_step(4, "success", f"계좌 {connection_info['account_count']}개 확인")
            
            # 5단계: 시장 데이터 준비
            self.connection_monitor.update_diagnostic_step(5, "running", "시장 데이터 연결 확인 중...")
            
            # 간단한 테스트 요청 (삼성전자 기본 정보)
            test_result = self.kiwoom_api.get_stock_basic_info("005930")
            if test_result is None:
                self.connection_monitor.update_diagnostic_step(5, "failed", "시장 데이터 접근 불가")
                self.connection_monitor.set_status(ConnectionStatus.ERROR, "시장 데이터 연결 실패")
                return False
            
            self.connection_monitor.update_diagnostic_step(5, "success", "시장 데이터 연결 확인")
            
            # 최종 연결 완료
            self.connected = True
            self.connection_monitor.set_status(ConnectionStatus.CONNECTED, "모든 연결 완료")
            
            self.logger.info("✅ 키움 API 초기화 및 연결 완료")
            return True
            
        except Exception as e:
            self.connection_monitor.set_status(ConnectionStatus.ERROR, f"초기화 오류: {str(e)}")
            self.logger.error(f"❌ 키움 API 초기화 실패: {e}")
            return False
    
    def run(self):
        """메인 실행 루프"""
        try:
            while self.running:
                self._show_main_menu()
                choice = self._get_user_input("선택 (1-6): ", "1234560")
                
                if choice == '1':
                    self._collect_stock_data_menu()
                elif choice == '2':
                    self._view_charts_menu()
                elif choice == '3':
                    self._connection_status_menu()
                elif choice == '4':
                    self._settings_menu()
                elif choice == '5':
                    self._show_help()
                elif choice == '6' or choice == '0':
                    self._confirm_exit()
                    break
                else:
                    print("❌ 잘못된 선택입니다. 다시 입력해주세요.")
                
                if self.running:
                    input("\n계속하려면 Enter 키를 누르세요...")
        
        except KeyboardInterrupt:
            print("\n\n🛑 사용자가 프로그램을 중단했습니다.")
        except Exception as e:
            self.logger.error(f"❌ 실행 중 오류 발생: {e}")
            print(f"❌ 오류가 발생했습니다: {e}")
        finally:
            self.shutdown()
    
    def _show_main_menu(self):
        """메인 메뉴 표시"""
        print("\n" + "=" * 50)
        print("📊 키움증권 주식 데이터 수집기 - 메인 메뉴")
        print("=" * 50)
        
        # 연결 상태 표시
        if self.connected:
            status_msg = "✅ 키움 API 연결됨"
            if self.kiwoom_api:
                conn_info = self.kiwoom_api.get_connection_info()
                status_msg += f" | 계좌: {conn_info.get('account_number', 'N/A')}"
        else:
            status_msg = "❌ 키움 API 연결 안됨"
        
        print(f"상태: {status_msg}")
        print()
        
        # 메뉴 항목
        print("1. 📈 종목 데이터 수집")
        print("2. 📊 차트 보기")  
        print("3. 🔍 연결 상태 확인")
        print("4. ⚙️  설정")
        print("5. ❓ 도움말")
        print("6. 🚪 종료")
        print()
    
    def _get_user_input(self, prompt: str, valid_chars: str = None) -> str:
        """사용자 입력 받기"""
        while True:
            try:
                user_input = input(prompt).strip()
                
                if valid_chars and user_input not in valid_chars:
                    print(f"❌ '{valid_chars}' 중에서 선택해주세요.")
                    continue
                
                return user_input
            
            except KeyboardInterrupt:
                print("\n\n🛑 입력이 취소되었습니다.")
                return ""
            except EOFError:
                print("\n\n🛑 입력 스트림이 종료되었습니다.")
                return ""
    
    def _collect_stock_data_menu(self):
        """종목 데이터 수집 메뉴"""
        if not self.connected:
            print("❌ 키움 API에 연결되지 않았습니다. 먼저 연결을 확인해주세요.")
            return
        
        print("\n" + "=" * 50)
        print("📈 종목 데이터 수집")
        print("=" * 50)
        
        # 종목 검색
        print("종목명 또는 종목코드를 입력하세요:")
        print("💡 예시: 005930, 삼성전자, 삼성 등")
        print()
        
        query = input("> ").strip()
        if not query:
            print("❌ 검색어를 입력해주세요.")
            return
        
        # 종목 검색
        print(f"🔍 '{query}' 검색 중...")
        search_results = self.stock_searcher.search_smart(query, 10)
        
        if not search_results:
            print(f"❌ '{query}' 검색 결과가 없습니다.")
            print("💡 정확한 종목명이나 6자리 종목코드를 입력해주세요.")
            return
        
        # 검색 결과 표시
        selected_stock = None
        
        if len(search_results) == 1:
            # 단일 결과
            stock = search_results[0]
            print(f"✅ 종목 확인: {stock['name']} ({stock['code']})")
            
            confirm = self._get_user_input("데이터를 수집하시겠습니까? (y/n): ", "ynYN")
            if confirm.lower() == 'y':
                selected_stock = stock
        else:
            # 다중 결과 - 선택 메뉴
            print(f"\n🔍 '{query}' 검색 결과 ({len(search_results)}개):")
            print("┌─────┬─────────┬────────────────────┬────────┐")
            print("│ 번호│ 종목코드│      종목명        │ 시장   │")
            print("├─────┼─────────┼────────────────────┼────────┤")
            
            for i, stock in enumerate(search_results, 1):
                name_padded = stock['name'][:18].ljust(18)
                market = stock.get('market', 'N/A')[:6].ljust(6)
                print(f"│  {i:2} │ {stock['code']} │ {name_padded} │ {market} │")
            
            print("└─────┴─────────┴────────────────────┴────────┘")
            print()
            
            choice = self._get_user_input(f"선택할 종목 번호 (1-{len(search_results)}) 또는 0(취소): ", 
                                        "0" + "".join(str(i) for i in range(1, len(search_results) + 1)))
            
            if choice != '0':
                selected_stock = search_results[int(choice) - 1]
        
        if not selected_stock:
            print("🚫 데이터 수집이 취소되었습니다.")
            return
        
        # 데이터 수집 실행
        self._execute_data_collection(selected_stock)
    
    def _execute_data_collection(self, stock: Dict):
        """데이터 수집 실행"""
        stock_code = stock['code']
        stock_name = stock['name']
        
        print(f"\n📊 {stock_name}({stock_code}) 데이터 수집 시작...")
        
        # 수집 기간 설정
        period_days = self.config.DEFAULT_PERIOD_DAYS
        print(f"📅 수집 기간: 최근 {period_days}일")
        
        try:
            # 현재가 정보 조회
            print("🔄 현재가 정보 조회 중...")
            basic_info = self.kiwoom_api.get_stock_basic_info(stock_code)
            
            if basic_info:
                print(f"💰 현재가: {basic_info.get('현재가', 0):,}원")
                print(f"📊 거래량: {basic_info.get('거래량', 0):,}주")
            
            # 일봉 데이터 수집
            print("📈 일봉 데이터 수집 중...")
            self.connection_monitor.record_data_request()
            
            daily_data = self.kiwoom_api.get_daily_stock_data(stock_code, period_days)
            
            if daily_data is None or daily_data.empty:
                print(f"❌ {stock_name} 데이터 수집 실패")
                self.connection_monitor.record_data_request(successful=False)
                return
            
            print(f"✅ 데이터 수집 완료: {len(daily_data)}개 레코드")
            
            # 데이터 저장
            print("💾 데이터 저장 중...")
            saved_path = self.data_manager.save_daily_data(stock_code, stock_name, daily_data)
            
            if saved_path:
                print(f"✅ 데이터 저장 완료: {os.path.basename(saved_path)}")
                
                # 수집 요약 표시
                self._show_collection_summary(daily_data, stock_name, stock_code)
                
                # 차트 생성 옵션
                create_chart = self._get_user_input("\n차트를 생성하시겠습니까? (y/n): ", "ynYN")
                
                if create_chart.lower() == 'y':
                    self._create_chart_for_stock(stock_code, stock_name, daily_data)
            else:
                print("❌ 데이터 저장 실패")
            
        except Exception as e:
            self.logger.error(f"❌ 데이터 수집 중 오류: {e}")
            print(f"❌ 데이터 수집 중 오류가 발생했습니다: {e}")
            self.connection_monitor.record_data_request(successful=False)
    
    def _show_collection_summary(self, data, stock_name: str, stock_code: str):
        """수집 요약 정보 표시"""
        print(f"\n📊 수집 요약 - {stock_name}({stock_code}):")
        print("┌────────────────┬─────────────────┐")
        print("│     항목       │      값         │")
        print("├────────────────┼─────────────────┤")
        print(f"│ 데이터 개수    │ {len(data):>13}개 │")
        print(f"│ 기간 시작      │ {data['날짜'].min():>13} │")
        print(f"│ 기간 종료      │ {data['날짜'].max():>13} │")
        print(f"│ 최고가         │ {data['고가'].max():>10,}원 │")
        print(f"│ 최저가         │ {data['저가'].min():>10,}원 │")
        print(f"│ 평균 거래량    │ {int(data['거래량'].mean()):>10,}주 │")
        print("└────────────────┴─────────────────┘")
    
    def _create_chart_for_stock(self, stock_code: str, stock_name: str, data):
        """종목 차트 생성"""
        print(f"\n🎨 {stock_name} 차트 생성 중...")
        
        try:
            chart_path = self.chart_viewer.create_and_save_chart(
                data=data,
                stock_code=stock_code,
                stock_name=stock_name,
                chart_type='candlestick',
                show_volume=True,
                show_ma=True,
                auto_open=self.config.AUTO_OPEN_CHART
            )
            
            if chart_path:
                print(f"✅ 차트 생성 완료: {os.path.basename(chart_path)}")
                if self.config.AUTO_OPEN_CHART:
                    print("🌐 브라우저에서 차트를 여는 중...")
                else:
                    print(f"📁 차트 경로: {chart_path}")
            else:
                print("❌ 차트 생성 실패")
                
        except Exception as e:
            self.logger.error(f"❌ 차트 생성 오류: {e}")
            print(f"❌ 차트 생성 중 오류: {e}")
    
    def _view_charts_menu(self):
        """차트 보기 메뉴"""
        print("\n" + "=" * 50)
        print("📊 차트 보기")
        print("=" * 50)
        
        # 저장된 차트 목록 조회
        chart_list = self.chart_viewer.get_chart_list()
        
        if not chart_list:
            print("📂 저장된 차트가 없습니다.")
            print("💡 먼저 종목 데이터를 수집하고 차트를 생성해주세요.")
            return
        
        print(f"📊 저장된 차트 목록 ({len(chart_list)}개):")
        print("┌─────┬─────────┬────────────┬──────────┬─────────────────────┐")
        print("│ 번호│ 종목코드│  종목명    │ 차트타입 │     생성 시간       │")
        print("├─────┼─────────┼────────────┼──────────┼─────────────────────┤")
        
        for i, chart in enumerate(chart_list[:20], 1):  # 최대 20개만 표시
            name_padded = chart['name'][:10].ljust(10)
            chart_type_padded = chart['chart_type'][:8].ljust(8)
            created_time = chart['created'].strftime('%Y-%m-%d %H:%M')
            print(f"│  {i:2} │ {chart['code']} │ {name_padded} │ {chart_type_padded} │ {created_time} │")
        
        print("└─────┴─────────┴────────────┴──────────┴─────────────────────┘")
        
        if len(chart_list) > 20:
            print(f"... 및 {len(chart_list) - 20}개 더")
        
        print()
        choice = self._get_user_input(f"열려할 차트 번호 (1-{min(20, len(chart_list))}) 또는 0(취소): ",
                                    "0" + "".join(str(i) for i in range(1, min(21, len(chart_list) + 1))))
        
        if choice != '0':
            selected_chart = chart_list[int(choice) - 1]
            chart_path = selected_chart['filepath']
            
            print(f"🌐 차트 열기: {selected_chart['name']} {selected_chart['chart_type']}")
            
            if self.chart_viewer.show_chart(chart_path):
                print("✅ 브라우저에서 차트를 여는 중...")
            else:
                print("❌ 차트 열기 실패")
    
    def _connection_status_menu(self):
        """연결 상태 확인 메뉴"""
        print("\n" + "=" * 50)
        print("🔍 연결 상태 및 진단")
        print("=" * 50)
        
        # 실시간 상태 리포트 출력
        status_report = self.connection_monitor.generate_status_report()
        print(status_report)
        
        # 진단 리포트
        print("\n📋 진단 결과:")
        diagnostic_report = self.connection_monitor.get_diagnostic_report()
        
        for step in diagnostic_report['steps']:
            status_emoji = {
                'success': '✅',
                'failed': '❌',
                'running': '🔄',
                'pending': '⏸️',
                'skipped': '⏭️'
            }
            
            emoji = status_emoji.get(step['status'], '❓')
            print(f"{emoji} 단계 {step['step_number']}: {step['step_name']} - {step['status']}")
            
            if step['error_details']:
                print(f"    오류: {step['error_details']}")
        
        # 추가 옵션
        print(f"\n선택 옵션:")
        print("1. 연결 재시도")
        print("2. 진단 로그 내보내기") 
        print("3. 통계 초기화")
        print("0. 돌아가기")
        
        choice = self._get_user_input("선택: ", "01230")
        
        if choice == '1':
            self._retry_connection()
        elif choice == '2':
            self._export_diagnostic_log()
        elif choice == '3':
            self._reset_connection_stats()
    
    def _retry_connection(self):
        """연결 재시도"""
        print("\n🔄 키움 API 재연결 시도...")
        self.connected = False
        
        if self._initialize_kiwoom():
            print("✅ 재연결 성공!")
        else:
            print("❌ 재연결 실패")
    
    def _export_diagnostic_log(self):
        """진단 로그 내보내기"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_filename = f"키움API_진단로그_{timestamp}.txt"
        log_path = self.config.LOG_SAVE_PATH / log_filename
        
        print(f"\n📝 진단 로그 내보내기 중...")
        
        if self.connection_monitor.export_diagnostic_log(str(log_path)):
            print(f"✅ 진단 로그 저장 완료: {log_filename}")
            print(f"📁 저장 경로: {log_path}")
        else:
            print("❌ 진단 로그 내보내기 실패")
    
    def _reset_connection_stats(self):
        """연결 통계 초기화"""
        confirm = self._get_user_input("연결 통계를 초기화하시겠습니까? (y/n): ", "ynYN")
        
        if confirm.lower() == 'y':
            self.connection_monitor.reset_stats()
            self.connection_monitor.clear_events()
            print("✅ 연결 통계가 초기화되었습니다.")
        else:
            print("🚫 초기화가 취소되었습니다.")
    
    def _settings_menu(self):
        """설정 메뉴"""
        print("\n" + "=" * 50)
        print("⚙️ 설정")
        print("=" * 50)
        
        # 현재 설정 표시
        summary = self.config.get_setting_summary()
        
        print("📊 현재 설정:")
        print(f"┌─────────────────────────────────────┐")
        print(f"│ 1. 기본 수집 기간: {summary['data_collection']['default_period']:>15}일 │")
        print(f"│ 2. 데이터 저장 경로: {str(self.config.CSV_SAVE_PATH)[-13:]:>13} │")
        print(f"│ 3. 차트 저장 경로: {str(self.config.CHART_SAVE_PATH)[-15:]:>15} │")
        print(f"│ 4. 자동 차트 열기: {str(summary['chart_options']['auto_open']):>15} │")
        print(f"│ 5. 차트 테마: {summary['chart_options']['theme']:>20} │")
        print(f"│ 6. 로그 레벨: {summary['debug']['log_level']:>20} │")
        print(f"└─────────────────────────────────────┘")
        
        print(f"\n0. 돌아가기")
        
        choice = self._get_user_input("변경할 설정 번호: ", "0123456")
        
        if choice == '1':
            self._change_default_period()
        elif choice == '4':
            self._toggle_auto_open_chart()
        elif choice == '0':
            return
        else:
            print("💡 해당 설정은 .env 파일에서 직접 수정해주세요.")
    
    def _change_default_period(self):
        """기본 수집 기간 변경"""
        print(f"\n현재 기본 수집 기간: {self.config.DEFAULT_PERIOD_DAYS}일")
        print("새로운 수집 기간을 입력하세요 (1-365일):")
        
        try:
            new_period = input("> ").strip()
            period_days = int(new_period)
            
            if 1 <= period_days <= 365:
                self.config.DEFAULT_PERIOD_DAYS = period_days
                print(f"✅ 기본 수집 기간이 {period_days}일로 변경되었습니다.")
                print("💡 이 변경은 현재 세션에서만 적용됩니다.")
            else:
                print("❌ 1-365 범위의 값을 입력해주세요.")
        except ValueError:
            print("❌ 숫자를 입력해주세요.")
    
    def _toggle_auto_open_chart(self):
        """자동 차트 열기 토글"""
        current = self.config.AUTO_OPEN_CHART
        self.config.AUTO_OPEN_CHART = not current
        
        status = "활성화" if self.config.AUTO_OPEN_CHART else "비활성화"
        print(f"✅ 자동 차트 열기가 {status}되었습니다.")
        print("💡 이 변경은 현재 세션에서만 적용됩니다.")
    
    def _show_help(self):
        """도움말 표시"""
        print("\n" + "=" * 50)
        print("❓ 도움말")
        print("=" * 50)
        
        help_text = """
📖 사용법:

1. 📈 종목 데이터 수집
   - 종목코드(예: 005930) 또는 종목명(예: 삼성전자) 입력
   - 부분 검색 지원 (예: "삼성" 입력시 삼성 관련 종목들 표시)
   - 일봉 데이터 자동 수집 및 CSV 저장
   - 캔들스틱 차트 자동 생성 옵션

2. 📊 차트 보기  
   - 저장된 차트 목록에서 선택하여 브라우저에서 열기
   - 캔들스틱, 이동평균선, 거래량 포함

3. 🔍 연결 상태 확인
   - 키움 API 연결 상태 실시간 모니터링
   - 단계별 진단 결과 확인
   - 연결 통계 및 성능 정보

4. ⚙️ 설정
   - 기본 수집 기간, 차트 옵션 등 변경
   - 자세한 설정은 .env 파일 편집

💡 팁:
   - Ctrl+C로 언제든 프로그램 종료 가능
   - 로그 파일에서 상세한 실행 기록 확인 가능
   - 차트는 HTML 파일로 저장되어 오프라인에서도 확인 가능

🔧 문제 해결:
   - 연결 실패시: 키움증권 HTS 먼저 실행 후 재시도
   - 데이터 수집 실패시: 연결 상태 확인 메뉴에서 진단
   - 차트가 열리지 않을 때: 브라우저 설정 확인
        """
        
        print(help_text)
    
    def _confirm_exit(self):
        """종료 확인"""
        if self.connected:
            print("⚠️ 키움 API가 연결되어 있습니다.")
        
        confirm = self._get_user_input("정말 종료하시겠습니까? (y/n): ", "ynYN")
        
        if confirm.lower() == 'y':
            self.running = False
            print("👋 프로그램을 종료합니다...")
        else:
            print("🔄 메인 메뉴로 돌아갑니다.")
    
    def shutdown(self):
        """애플리케이션 종료"""
        try:
            print("\n🧹 종료 작업 중...")
            
            # 연결 모니터링 중지
            self.connection_monitor.stop_monitoring()
            
            # 키움 API 연결 해제
            if self.kiwoom_manager:
                self.kiwoom_manager.cleanup()
            
            # 캐시 정리
            self.data_manager.clear_cache()
            
            # 오래된 백업 파일 정리 (7일)
            self.data_manager.cleanup_old_backups(7)
            self.chart_viewer.cleanup_old_charts(7)
            
            self.logger.info("✅ 애플리케이션 종료 완료")
            print("✅ 종료 작업 완료")
            
        except Exception as e:
            self.logger.error(f"❌ 종료 중 오류: {e}")
            print(f"⚠️ 종료 중 오류 발생: {e}")

def main():
    """메인 함수"""
    try:
        # 애플리케이션 생성
        app = StockDataCollector()
        
        # 시작
        if not app.startup():
            print("❌ 애플리케이션 시작에 실패했습니다.")
            return 1
        
        # 실행
        app.run()
        
        return 0
        
    except Exception as e:
        print(f"❌ 예상하지 못한 오류가 발생했습니다: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())