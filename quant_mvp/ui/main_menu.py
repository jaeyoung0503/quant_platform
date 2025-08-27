"""
file: quant_mvp/ui/main_menu.py
메인 메뉴 UI
"""

import os
import json
from typing import Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.prompt import Prompt, Confirm
import logging

logger = logging.getLogger(__name__)

class MainMenu:
    """메인 메뉴 클래스"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.console = Console()
    
    def show_welcome_banner(self):
        """환영 메시지 및 배너 표시"""
        title = Text("🚀 Quant Strategy MVP", style="bold blue")
        subtitle = Text("퀀트 전략 백테스팅 시스템", style="italic")
        
        banner_text = Text()
        banner_text.append("📈 기술적 분석: ", style="bold green")
        banner_text.append("모멘텀, RSI, 볼린저밴드, MACD, 평균회귀\n")
        banner_text.append("📊 재무 기반: ", style="bold blue")
        banner_text.append("가치투자, 성장투자, 퀄리티, 배당\n")
        banner_text.append("🔄 혼합 전략: ", style="bold magenta")
        banner_text.append("GARP, 모멘텀+밸류\n")
        banner_text.append("💼 포트폴리오: ", style="bold yellow")
        banner_text.append("최적화 및 리스크 관리")
        
        panel = Panel(
            banner_text,
            title=title,
            subtitle=subtitle,
            border_style="blue",
            padding=(1, 2)
        )
        
        self.console.print()
        self.console.print(panel)
        self.console.print()
    
    def show_main_menu(self) -> str:
        """메인 메뉴 표시 및 선택 받기"""
        menu_table = Table(show_header=False, box=None, padding=(0, 2))
        menu_table.add_column("Option", style="bold cyan", width=3)
        menu_table.add_column("Description", style="white")
        
        menu_options = [
            ("1", "🎯 전략 조합 빌더 - 나만의 퀀트 전략 만들기"),
            ("2", "⚡ 빠른 백테스트 - 기본 설정으로 즉시 실행"),
            ("3", "📊 전략 비교 분석 - 여러 전략 성과 비교"),
            ("4", "🔧 파라미터 최적화 - 최적 파라미터 찾기"),
            ("5", "📈 포트폴리오 분석 - 위험도 및 수익률 분석"),
            ("6", "📋 백테스트 히스토리 - 이전 결과 확인"),
            ("7", "⚙️  설정 관리 - 기본값 변경"),
            ("8", "❓ 도움말 - 사용법 안내"),
            ("9", "🚪 종료")
        ]
        
        for option, description in menu_options:
            menu_table.add_row(option, description)
        
        panel = Panel(
            menu_table,
            title="📋 메인 메뉴",
            border_style="green",
            padding=(1, 2)
        )
        
        self.console.print(panel)
        
        while True:
            choice = Prompt.ask(
                "\n🎯 원하는 작업을 선택하세요",
                choices=[str(i) for i in range(1, 10)],
                default="1"
            )
            
            if choice in [str(i) for i in range(1, 10)]:
                return choice
            else:
                self.console.print("❌ 잘못된 선택입니다. 1-9 사이의 숫자를 입력해주세요.", style="red")
    
    def show_strategy_categories(self) -> Dict[str, Any]:
        """전략 카테고리 표시"""
        categories_table = Table(title="📊 사용 가능한 전략 카테고리", show_header=True, box=None)
        categories_table.add_column("카테고리", style="bold blue", width=15)
        categories_table.add_column("전략", style="white", width=50)
        categories_table.add_column("설명", style="dim", width=30)
        
        strategy_info = {
            "기술적 분석": {
                "strategies": ["모멘텀", "RSI", "볼린저밴드", "MACD", "평균회귀"],
                "description": "주가 움직임과 거래량 기반"
            },
            "재무 기반": {
                "strategies": ["가치투자", "성장투자", "퀄리티", "배당"],
                "description": "기업 재무제표 기반"
            },
            "혼합 전략": {
                "strategies": ["GARP", "모멘텀+밸류"],
                "description": "기술적+재무적 분석 결합"
            }
        }
        
        for category, info in strategy_info.items():
            strategies_text = ", ".join(info["strategies"])
            categories_table.add_row(category, strategies_text, info["description"])
        
        self.console.print(categories_table)
        self.console.print()
        
        return strategy_info
    
    def show_quick_start_options(self) -> str:
        """빠른 시작 옵션 표시"""
        quick_options = Table(show_header=False, box=None, padding=(0, 2))
        quick_options.add_column("Option", style="bold cyan", width=3)
        quick_options.add_column("Description", style="white")
        
        options = [
            ("1", "💰 보수적 포트폴리오 (낮은 위험, 안정적 수익)"),
            ("2", "⚖️  균형 포트폴리오 (중간 위험, 적당한 수익)"),
            ("3", "🚀 공격적 포트폴리오 (높은 위험, 높은 수익 추구)"),
            ("4", "🎯 커스텀 설정 (직접 전략 조합)")
        ]
        
        for option, description in options:
            quick_options.add_row(option, description)
        
        panel = Panel(
            quick_options,
            title="⚡ 빠른 백테스트 옵션",
            border_style="yellow",
            padding=(1, 2)
        )
        
        self.console.print(panel)
        
        choice = Prompt.ask(
            "\n옵션을 선택하세요",
            choices=["1", "2", "3", "4"],
            default="2"
        )
        
        return choice
    
    def show_system_status(self):
        """시스템 상태 표시"""
        from data.data_loader import DataLoader
        
        status_table = Table(title="🔍 시스템 상태", show_header=True)
        status_table.add_column("항목", style="bold blue")
        status_table.add_column("상태", style="green")
        status_table.add_column("세부 정보", style="dim")
        
        # 데이터 파일 확인
        loader = DataLoader(self.config)
        try:
            symbols = loader.get_symbols_list()
            data_status = f"✅ 정상 ({len(symbols)}개 종목)"
            data_detail = f"종목: {', '.join(symbols[:5])}{'...' if len(symbols) > 5 else ''}"
        except Exception as e:
            data_status = "❌ 오류"
            data_detail = str(e)[:50]
        
        # 출력 디렉토리 확인
        output_dirs = [
            self.config['output']['reports_dir'],
            self.config['output']['charts_dir'],
            self.config['output']['logs_dir']
        ]
        
        missing_dirs = [d for d in output_dirs if not os.path.exists(d)]
        if not missing_dirs:
            output_status = "✅ 준비됨"
            output_detail = "모든 출력 디렉토리 존재"
        else:
            output_status = "⚠️  일부 누락"
            output_detail = f"누락: {len(missing_dirs)}개 디렉토리"
        
        # 설정 파일 확인
        config_status = "✅ 로드됨"
        config_detail = f"기본 투자금액: ${self.config['investment']['default_amount']:,}"
        
        status_table.add_row("데이터 파일", data_status, data_detail)
        status_table.add_row("출력 디렉토리", output_status, output_detail)
        status_table.add_row("설정 파일", config_status, config_detail)
        
        self.console.print(status_table)
        self.console.print()
    
    def show_help_menu(self):
        """도움말 표시"""
        help_text = Text()
        help_text.append("🎯 전략 조합 빌더\n", style="bold blue")
        help_text.append("- 여러 전략을 조합하여 나만의 포트폴리오 생성\n")
        help_text.append("- 각 전략의 가중치와 파라미터 조정 가능\n")
        help_text.append("- 투자 금액과 백테스트 기간 설정\n\n")
        
        help_text.append("⚡ 빠른 백테스트\n", style="bold yellow")
        help_text.append("- 미리 설정된 포트폴리오로 즉시 백테스트 실행\n")
        help_text.append("- 보수적/균형/공격적 3가지 옵션 제공\n\n")
        
        help_text.append("📊 전략 비교 분석\n", style="bold green")
        help_text.append("- 여러 전략의 성과를 동시에 비교\n")
        help_text.append("- 위험 대비 수익률, 샤프 비율 등 분석\n\n")
        
        help_text.append("🔧 파라미터 최적화\n", style="bold magenta")
        help_text.append("- 그리드 서치를 통한 최적 파라미터 탐색\n")
        help_text.append("- 백테스트 성과 기준으로 자동 최적화\n\n")
        
        help_text.append("💡 팁\n", style="bold cyan")
        help_text.append("- ESC 키로 언제든 이전 메뉴로 돌아갈 수 있습니다\n")
        help_text.append("- 결과는 outputs/ 폴더에 자동 저장됩니다\n")
        help_text.append("- 백테스트 완료 후 브라우저에서 자동으로 결과를 확인할 수 있습니다\n")
        help_text.append("- 히스토리에서 이전 백테스트 결과를 다시 볼 수 있습니다\n")
        
        panel = Panel(
            help_text,
            title="❓ 도움말",
            border_style="blue",
            padding=(1, 2)
        )
        
        self.console.print(panel)
        
        Prompt.ask("\n계속하려면 Enter를 누르세요", default="")
    
    def show_settings_menu(self) -> str:
        """설정 메뉴 표시"""
        settings_table = Table(show_header=False, box=None, padding=(0, 2))
        settings_table.add_column("Option", style="bold cyan", width=3)
        settings_table.add_column("Description", style="white")
        settings_table.add_column("Current", style="dim")
        
        current_settings = [
            ("1", "기본 투자 금액", f"${self.config['investment']['default_amount']:,}"),
            ("2", "백테스트 기간", f"{self.config['investment']['default_start_date']} ~ {self.config['investment']['default_end_date']}"),
            ("3", "리밸런싱 주기", self.config['investment']['rebalancing_frequency']),
            ("4", "최대 포지션 수", str(self.config['portfolio']['max_positions'])),
            ("5", "거래 비용", f"{self.config['portfolio']['transaction_cost']:.3f}"),
            ("6", "브라우저 자동 열기", "예" if self.config['output']['auto_open_browser'] else "아니오"),
            ("7", "기본값으로 복원", ""),
            ("8", "뒤로 가기", "")
        ]
        
        for option, description, current in current_settings:
            settings_table.add_row(option, description, current)
        
        panel = Panel(
            settings_table,
            title="⚙️ 설정 관리",
            border_style="cyan",
            padding=(1, 2)
        )
        
        self.console.print(panel)
        
        choice = Prompt.ask(
            "\n변경할 설정을 선택하세요",
            choices=[str(i) for i in range(1, 9)],
            default="8"
        )
        
        return choice
    
    def update_setting(self, setting_key: str) -> bool:
        """설정 업데이트"""
        try:
            if setting_key == "1":  # 투자 금액
                current = self.config['investment']['default_amount']
                new_amount = Prompt.ask(
                    f"새로운 투자 금액을 입력하세요 (현재: ${current:,})",
                    default=str(current)
                )
                self.config['investment']['default_amount'] = int(float(new_amount))
                
            elif setting_key == "2":  # 백테스트 기간
                current_start = self.config['investment']['default_start_date']
                current_end = self.config['investment']['default_end_date']
                
                new_start = Prompt.ask(
                    f"시작 날짜 (YYYY-MM-DD, 현재: {current_start})",
                    default=current_start
                )
                new_end = Prompt.ask(
                    f"종료 날짜 (YYYY-MM-DD, 현재: {current_end})",
                    default=current_end
                )
                
                self.config['investment']['default_start_date'] = new_start
                self.config['investment']['default_end_date'] = new_end
                
            elif setting_key == "3":  # 리밸런싱 주기
                current = self.config['investment']['rebalancing_frequency']
                new_freq = Prompt.ask(
                    f"리밸런싱 주기 (현재: {current})",
                    choices=["monthly", "quarterly", "yearly"],
                    default=current
                )
                self.config['investment']['rebalancing_frequency'] = new_freq
                
            elif setting_key == "4":  # 최대 포지션 수
                current = self.config['portfolio']['max_positions']
                new_positions = Prompt.ask(
                    f"최대 포지션 수 (현재: {current})",
                    default=str(current)
                )
                self.config['portfolio']['max_positions'] = int(new_positions)
                
            elif setting_key == "5":  # 거래 비용
                current = self.config['portfolio']['transaction_cost']
                new_cost = Prompt.ask(
                    f"거래 비용 (소수, 현재: {current})",
                    default=str(current)
                )
                self.config['portfolio']['transaction_cost'] = float(new_cost)
                
            elif setting_key == "6":  # 브라우저 자동 열기
                current = self.config['output']['auto_open_browser']
                new_auto_open = Confirm.ask(
                    f"결과 완료 후 브라우저 자동 열기? (현재: {'예' if current else '아니오'})",
                    default=current
                )
                self.config['output']['auto_open_browser'] = new_auto_open
                
            elif setting_key == "7":  # 기본값으로 복원
                if Confirm.ask("모든 설정을 기본값으로 복원하시겠습니까?", default=False):
                    self.reset_to_defaults()
                    self.console.print("✅ 모든 설정이 기본값으로 복원되었습니다.", style="green")
                    return True
            
            # 설정 파일 저장
            self.save_config()
            self.console.print("✅ 설정이 저장되었습니다.", style="green")
            return True
            
        except Exception as e:
            self.console.print(f"❌ 설정 업데이트 중 오류: {e}", style="red")
            return False
    
    def reset_to_defaults(self):
        """기본 설정으로 복원"""
        default_config = {
            "investment": {
                "default_amount": 100000,
                "default_start_date": "2020-01-01",
                "default_end_date": "2024-12-31",
                "rebalancing_frequency": "quarterly"
            },
            "portfolio": {
                "max_positions": 20,
                "max_position_size": 0.1,
                "min_position_size": 0.02,
                "transaction_cost": 0.001
            },
            "output": {
                "auto_open_browser": True
            }
        }
        
        # 기존 설정과 병합
        for category, settings in default_config.items():
            if category in self.config:
                self.config[category].update(settings)
    
    def save_config(self):
        """설정을 파일에 저장"""
        try:
            with open("config.json", 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise
    
    def show_exit_message(self):
        """종료 메시지 표시"""
        exit_text = Text()
        exit_text.append("👋 Quant Strategy MVP를 이용해 주셔서 감사합니다!\n\n", style="bold blue")
        exit_text.append("📊 백테스트 결과는 outputs/ 폴더에 저장되었습니다.\n", style="green")
        exit_text.append("📈 언제든 다시 실행하여 새로운 전략을 시도해보세요.\n", style="yellow")
        exit_text.append("💡 질문이나 개선사항이 있으시면 GitHub 이슈를 등록해주세요.\n", style="cyan")
        
        panel = Panel(
            exit_text,
            title="🚪 안녕히 가세요!",
            border_style="blue",
            padding=(1, 2)
        )
        
        self.console.print(panel)
    
    def show_error(self, message: str, details: str = None):
        """오류 메시지 표시"""
        error_text = Text()
        error_text.append(f"❌ {message}\n", style="bold red")
        
        if details:
            error_text.append(f"세부사항: {details}\n", style="dim red")
        
        error_text.append("다시 시도하거나 도움말을 참고하세요.", style="yellow")
        
        panel = Panel(
            error_text,
            title="⚠️ 오류",
            border_style="red",
            padding=(1, 1)
        )
        
        self.console.print(panel)
    
    def show_success(self, message: str, details: str = None):
        """성공 메시지 표시"""
        success_text = Text()
        success_text.append(f"✅ {message}\n", style="bold green")
        
        if details:
            success_text.append(f"{details}\n", style="green")
        
        panel = Panel(
            success_text,
            title="🎉 성공",
            border_style="green",
            padding=(1, 1)
        )
        
        self.console.print(panel)
    
    def show_progress_start(self, task_name: str):
        """작업 시작 표시"""
        self.console.print(f"\n🚀 {task_name} 시작...", style="bold blue")
    
    def show_progress_step(self, step_name: str):
        """작업 단계 표시"""
        self.console.print(f"   ⚙️ {step_name}", style="dim blue")
    
    def show_progress_complete(self, task_name: str):
        """작업 완료 표시"""
        self.console.print(f"✅ {task_name} 완료!", style="bold green")