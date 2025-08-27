"""
인터랙티브 UI 통합 클래스
메인 메뉴와 전략 빌더를 통합하여 사용자 인터페이스 제공
"""

import sys
import webbrowser
from typing import Dict, Any
from rich.console import Console
import logging

from .main_menu import MainMenu
from .strategy_builder import StrategyBuilder
from backtesting.engine import BacktestEngine
from utils.visualizer import ResultVisualizer

logger = logging.getLogger(__name__)

class InteractiveMenu:
    """메인 인터랙티브 메뉴 클래스"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.console = Console()
        self.main_menu = MainMenu(config)
        self.strategy_builder = StrategyBuilder(config)
        self.backtest_engine = BacktestEngine(config)
        self.visualizer = ResultVisualizer(config)
        self.running = True
    
    def run(self):
        """메인 실행 루프"""
        try:
            # 환영 메시지 표시
            self.main_menu.show_welcome_banner()
            
            while self.running:
                try:
                    # 메인 메뉴 표시 및 선택
                    choice = self.main_menu.show_main_menu()
                    
                    # 선택된 메뉴 실행
                    self.handle_menu_choice(choice)
                    
                except KeyboardInterrupt:
                    if self.confirm_exit():
                        break
                except Exception as e:
                    self.main_menu.show_error("예상치 못한 오류가 발생했습니다", str(e))
                    logger.error(f"Menu handling error: {e}")
        
        except Exception as e:
            self.console.print(f"❌ 심각한 오류: {e}", style="bold red")
            logger.critical(f"Critical error in interactive menu: {e}")
        
        finally:
            # 종료 메시지
            self.main_menu.show_exit_message()
    
    def handle_menu_choice(self, choice: str):
        """메뉴 선택 처리"""
        menu_handlers = {
            "1": self.run_strategy_builder,      # 전략 조합 빌더
            "2": self.run_quick_backtest,        # 빠른 백테스트
            "3": self.run_strategy_comparison,   # 전략 비교
            "4": self.run_parameter_optimization, # 파라미터 최적화
            "5": self.run_portfolio_analysis,    # 포트폴리오 분석
            "6": self.show_backtest_history,     # 백테스트 히스토리
            "7": self.manage_settings,           # 설정 관리
            "8": self.show_help,                 # 도움말
            "9": self.exit_program               # 종료
        }
        
        handler = menu_handlers.get(choice)
        if handler:
            handler()
        else:
            self.main_menu.show_error("잘못된 메뉴 선택")
    
    def run_strategy_builder(self):
        """전략 조합 빌더 실행"""
        try:
            self.main_menu.show_progress_start("전략 조합 빌더")
            
            # 전략 빌더 실행
            build_result = self.strategy_builder.run_strategy_builder()
            
            if build_result is None:
                self.main_menu.show_error("전략 빌더가 취소되었습니다")
                return
            
            # 백테스트 실행
            self.main_menu.show_progress_step("백테스트 실행 중...")
            backtest_result = self.backtest_engine.run_backtest(build_result)
            
            if backtest_result is None:
                self.main_menu.show_error("백테스트 실행 실패")
                return
            
            # 결과 시각화 및 리포트 생성
            self.main_menu.show_progress_step("결과 리포트 생성 중...")
            report_path = self.visualizer.generate_complete_report(
                backtest_result, 
                build_result,
                title="Custom Strategy Backtest"
            )
            
            if report_path and self.config['output']['auto_open_browser']:
                webbrowser.open(f"file://{report_path}")
            
            self.main_menu.show_progress_complete("전략 조합 빌더")
            self.main_menu.show_success(
                "백테스트가 완료되었습니다!",
                f"리포트: {report_path}"
            )
            
        except Exception as e:
            self.main_menu.show_error("전략 빌더 실행 중 오류", str(e))
            logger.error(f"Strategy builder error: {e}")
    
    def run_quick_backtest(self):
        """빠른 백테스트 실행"""
        try:
            self.main_menu.show_progress_start("빠른 백테스트")
            
            # 빠른 시작 옵션 선택
            quick_choice = self.main_menu.show_quick_start_options()
            
            # 미리 정의된 포트폴리오 설정
            preset_configs = {
                "1": self.get_conservative_portfolio(),
                "2": self.get_balanced_portfolio(),
                "3": self.get_aggressive_portfolio(),
                "4": None  # 커스텀 설정은 전략 빌더로 이동
            }
            
            if quick_choice == "4":
                # 커스텀 설정은 전략 빌더로 리다이렉트
                return self.run_strategy_builder()
            
            config = preset_configs[quick_choice]
            if config is None:
                self.main_menu.show_error("잘못된 선택")
                return
            
            # 백테스트 실행
            self.main_menu.show_progress_step("백테스트 실행 중...")
            backtest_result = self.backtest_engine.run_backtest(config)
            
            if backtest_result is None:
                self.main_menu.show_error("백테스트 실행 실패")
                return
            
            # 결과 표시
            self.main_menu.show_progress_step("결과 생성 중...")
            self.show_quick_results(backtest_result, config)
            
            self.main_menu.show_progress_complete("빠른 백테스트")
            
        except Exception as e:
            self.main_menu.show_error("빠른 백테스트 실행 중 오류", str(e))
            logger.error(f"Quick backtest error: {e}")
    
    def run_strategy_comparison(self):
        """전략 비교 실행"""
        self.main_menu.show_error("아직 구현되지 않은 기능입니다", "곧 추가될 예정입니다")
    
    def run_parameter_optimization(self):
        """파라미터 최적화 실행"""
        self.main_menu.show_error("아직 구현되지 않은 기능입니다", "곧 추가될 예정입니다")
    
    def run_portfolio_analysis(self):
        """포트폴리오 분석 실행"""
        self.main_menu.show_error("아직 구현되지 않은 기능입니다", "곧 추가될 예정입니다")
    
    def show_backtest_history(self):
        """백테스트 히스토리 표시"""
        import os
        from pathlib import Path
        
        reports_dir = Path(self.config['output']['reports_dir'])
        if not reports_dir.exists():
            self.main_menu.show_error("백테스트 히스토리가 없습니다")
            return
        
        # HTML 리포트 파일 찾기
        html_files = list(reports_dir.glob("*.html"))
        
        if not html_files:
            self.main_menu.show_error("저장된 백테스트 결과가 없습니다")
            return
        
        # 최근 파일 순으로 정렬
        html_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        from rich.table import Table
        from rich.prompt import Prompt
        import datetime
        
        # 히스토리 테이블 표시
        history_table = Table(title="📋 백테스트 히스토리", show_header=True)
        history_table.add_column("번호", style="cyan", width=4)
        history_table.add_column("파일명", style="white", width=30)
        history_table.add_column("생성 시간", style="dim", width=20)
        history_table.add_column("크기", style="dim", width=10)
        
        for i, file_path in enumerate(html_files[:10], 1):  # 최근 10개만 표시
            file_stat = file_path.stat()
            created_time = datetime.datetime.fromtimestamp(file_stat.st_mtime)
            file_size = f"{file_stat.st_size // 1024}KB"
            
            history_table.add_row(
                str(i),
                file_path.name,
                created_time.strftime("%Y-%m-%d %H:%M"),
                file_size
            )
        
        self.console.print(history_table)
        
        # 파일 선택
        choices = [str(i) for i in range(1, min(11, len(html_files) + 1))] + ["0"]
        choice = Prompt.ask(
            "\n열어볼 리포트 번호를 선택하세요 (0: 돌아가기)",
            choices=choices,
            default="0"
        )
        
        if choice != "0":
            selected_file = html_files[int(choice) - 1]
            webbrowser.open(f"file://{selected_file.absolute()}")
            self.main_menu.show_success(f"리포트를 브라우저에서 열었습니다: {selected_file.name}")
    
    def manage_settings(self):
        """설정 관리"""
        while True:
            choice = self.main_menu.show_settings_menu()
            
            if choice == "8":  # 뒤로 가기
                break
            
            if self.main_menu.update_setting(choice):
                self.main_menu.show_success("설정이 업데이트되었습니다")
    
    def show_help(self):
        """도움말 표시"""
        self.main_menu.show_help_menu()
    
    def exit_program(self):
        """프로그램 종료"""
        self.running = False
    
    def confirm_exit(self) -> bool:
        """종료 확인"""
        from rich.prompt import Confirm
        return Confirm.ask("\n정말 종료하시겠습니까?", default=False)
    
    def get_conservative_portfolio(self) -> Dict[str, Any]:
        """보수적 포트폴리오 설정"""
        return {
            'investment_amount': self.config['investment']['default_amount'],
            'start_date': self.config['investment']['default_start_date'],
            'end_date': self.config['investment']['default_end_date'],
            'rebalancing_freq': 'quarterly',
            'strategies': [
                {'name': 'Value', 'weight': 0.4, 'category': '재무 기반'},
                {'name': 'Quality', 'weight': 0.3, 'category': '재무 기반'},
                {'name': 'Dividend', 'weight': 0.3, 'category': '재무 기반'}
            ],
            'parameters': {
                'Value': self.config['strategies']['value'].copy(),
                'Quality': self.config['strategies']['quality'].copy(),
                'Dividend': self.config['strategies']['dividend'].copy()
            }
        }
    
    def get_balanced_portfolio(self) -> Dict[str, Any]:
        """균형 포트폴리오 설정"""
        return {
            'investment_amount': self.config['investment']['default_amount'],
            'start_date': self.config['investment']['default_start_date'],
            'end_date': self.config['investment']['default_end_date'],
            'rebalancing_freq': 'quarterly',
            'strategies': [
                {'name': 'Momentum', 'weight': 0.25, 'category': '기술적 분석'},
                {'name': 'Value', 'weight': 0.25, 'category': '재무 기반'},
                {'name': 'Quality', 'weight': 0.25, 'category': '재무 기반'},
                {'name': 'Growth', 'weight': 0.25, 'category': '재무 기반'}
            ],
            'parameters': {
                'Momentum': self.config['strategies']['momentum'].copy(),
                'Value': self.config['strategies']['value'].copy(),
                'Quality': self.config['strategies']['quality'].copy(),
                'Growth': self.config['strategies']['growth'].copy()
            }
        }
    
    def get_aggressive_portfolio(self) -> Dict[str, Any]:
        """공격적 포트폴리오 설정"""
        return {
            'investment_amount': self.config['investment']['default_amount'],
            'start_date': self.config['investment']['default_start_date'],
            'end_date': self.config['investment']['default_end_date'],
            'rebalancing_freq': 'monthly',
            'strategies': [
                {'name': 'Momentum', 'weight': 0.3, 'category': '기술적 분석'},
                {'name': 'Growth', 'weight': 0.3, 'category': '재무 기반'},
                {'name': 'RSI', 'weight': 0.2, 'category': '기술적 분석'},
                {'name': 'MACD', 'weight': 0.2, 'category': '기술적 분석'}
            ],
            'parameters': {
                'Momentum': self.config['strategies']['momentum'].copy(),
                'Growth': self.config['strategies']['growth'].copy(),
                'RSI': self.config['strategies']['rsi'].copy(),
                'MACD': self.config['strategies']['macd'].copy()
            }
        }
    
    def show_quick_results(self, backtest_result: Dict[str, Any], config: Dict[str, Any]):
        """빠른 백테스트 결과 표시"""
        from rich.table import Table
        from utils.helpers import format_currency, format_percentage
        
        # 성과 요약
        performance = backtest_result.get('performance_summary', {})
        
        results_table = Table(title="⚡ 빠른 백테스트 결과", show_header=True)
        results_table.add_column("지표", style="bold blue", width=20)
        results_table.add_column("값", style="white", width=15)
        results_table.add_column("벤치마크 (SPY)", style="dim", width=15)
        
        # 주요 지표 표시
        total_return = performance.get('total_return', 0)
        annual_return = performance.get('annual_return', 0)
        volatility = performance.get('volatility', 0)
        sharpe_ratio = performance.get('sharpe_ratio', 0)
        max_drawdown = performance.get('max_drawdown', 0)
        
        # 벤치마크 (SPY) 성과 (임시 데이터)
        benchmark_return = 0.52  # 52%
        benchmark_volatility = 0.16  # 16%
        benchmark_sharpe = 2.1
        
        results_table.add_row("총 수익률", format_percentage(total_return), format_percentage(benchmark_return))
        results_table.add_row("연평균 수익률", format_percentage(annual_return), "10.5%")
        results_table.add_row("변동성", format_percentage(volatility), format_percentage(benchmark_volatility))
        results_table.add_row("샤프 비율", f"{sharpe_ratio:.2f}", f"{benchmark_sharpe:.2f}")
        results_table.add_row("최대 낙폭", format_percentage(max_drawdown), "-12.8%")
        
        self.console.print(results_table)
        
        # 전략 구성
        strategy_table = Table(title="📊 포트폴리오 구성", show_header=True)
        strategy_table.add_column("전략", style="bold green", width=15)
        strategy_table.add_column("가중치", style="white", width=10)
        strategy_table.add_column("수익 기여도", style="cyan", width=12)
        
        for strategy_info in config['strategies']:
            strategy_name = strategy_info['name']
            weight = format_percentage(strategy_info['weight'])
            
            # 수익 기여도 계산 (임시)
            contribution = total_return * strategy_info['weight']
            contribution_str = format_percentage(contribution)
            
            strategy_table.add_row(strategy_name, weight, contribution_str)
        
        self.console.print(strategy_table)
        
        # 상세 리포트 생성 옵션
        from rich.prompt import Confirm
        if Confirm.ask("\n📄 상세 리포트를 생성하시겠습니까?", default=True):
            try:
                report_path = self.visualizer.generate_complete_report(
                    backtest_result, 
                    config,
                    title="Quick Backtest Results"
                )
                
                if report_path and self.config['output']['auto_open_browser']:
                    webbrowser.open(f"file://{report_path}")
                
                self.main_menu.show_success(
                    "상세 리포트가 생성되었습니다!",
                    f"파일: {report_path}"
                )
            except Exception as e:
                self.main_menu.show_error("리포트 생성 실패", str(e))