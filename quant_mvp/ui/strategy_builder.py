"""
file: quant_mvp/ui/strategy_builder.py
전략 조합 빌더 UI
"""

from typing import Dict, List, Any, Tuple, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt, Confirm, FloatPrompt, IntPrompt
from rich.progress import Progress, SpinnerColumn, TextColumn
import logging

from strategies.strategy_combiner import StrategyCombiner
from utils.helpers import format_currency, format_percentage, validate_date_range

logger = logging.getLogger(__name__)

class StrategyBuilder:
    """전략 조합 빌더 클래스"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.console = Console()
        self.combiner = StrategyCombiner(config)
        
        # 현재 빌드 중인 전략 정보
        self.current_build = {
            'investment_amount': config['investment']['default_amount'],
            'start_date': config['investment']['default_start_date'],
            'end_date': config['investment']['default_end_date'],
            'rebalancing_freq': config['investment']['rebalancing_frequency'],
            'strategies': [],
            'parameters': {}
        }
    
    def run_strategy_builder(self) -> Dict[str, Any]:
        """전략 빌더 실행"""
        try:
            self.show_builder_welcome()
            
            # 1단계: 기본 투자 설정
            if not self.setup_investment_parameters():
                return None
            
            # 2단계: 전략 선택 및 조합
            if not self.select_and_combine_strategies():
                return None
            
            # 3단계: 파라미터 조정
            if not self.tune_strategy_parameters():
                return None
            
            # 4단계: 최종 확인
            if not self.confirm_final_setup():
                return None
            
            return self.current_build
            
        except KeyboardInterrupt:
            self.console.print("\n❌ 전략 빌더가 취소되었습니다.", style="yellow")
            return None
        except Exception as e:
            self.console.print(f"\n❌ 전략 빌더 오류: {e}", style="red")
            logger.error(f"Strategy builder error: {e}")
            return None
    
    def show_builder_welcome(self):
        """빌더 환영 메시지"""
        welcome_text = Text()
        welcome_text.append("🎯 전략 조합 빌더에 오신 것을 환영합니다!\n\n", style="bold blue")
        welcome_text.append("4단계 과정:\n", style="bold")
        welcome_text.append("1️⃣ 투자 설정 (금액, 기간, 리밸런싱)\n", style="green")
        welcome_text.append("2️⃣ 전략 선택 및 가중치 설정\n", style="green")
        welcome_text.append("3️⃣ 전략별 파라미터 조정\n", style="green")
        welcome_text.append("4️⃣ 최종 확인 및 백테스트 실행\n", style="green")
        welcome_text.append("\n💡 팁: ESC로 언제든 이전 단계로 돌아갈 수 있습니다.", style="dim")
        
        panel = Panel(
            welcome_text,
            title="🎯 전략 조합 빌더",
            border_style="blue",
            padding=(1, 2)
        )
        
        self.console.print(panel)
    
    def setup_investment_parameters(self) -> bool:
        """1단계: 투자 파라미터 설정"""
        self.console.print("\n" + "="*60)
        self.console.print("1️⃣ 투자 설정", style="bold blue")
        self.console.print("="*60)
        
        try:
            # 투자 금액
            current_amount = self.current_build['investment_amount']
            self.console.print(f"\n💰 투자 금액 설정 (현재: {format_currency(current_amount)})")
            
            new_amount = FloatPrompt.ask(
                "투자 금액을 입력하세요 ($)",
                default=current_amount,
                show_default=True
            )
            
            if new_amount <= 0:
                self.console.print("❌ 투자 금액은 0보다 커야 합니다.", style="red")
                return False
            
            self.current_build['investment_amount'] = new_amount
            
            # 백테스트 기간
            self.console.print(f"\n📅 백테스트 기간 설정")
            current_start = self.current_build['start_date']
            current_end = self.current_build['end_date']
            
            new_start = Prompt.ask(
                "시작 날짜 (YYYY-MM-DD)",
                default=current_start
            )
            
            new_end = Prompt.ask(
                "종료 날짜 (YYYY-MM-DD)",
                default=current_end
            )
            
            if not validate_date_range(new_start, new_end):
                self.console.print("❌ 잘못된 날짜 범위입니다.", style="red")
                return False
            
            self.current_build['start_date'] = new_start
            self.current_build['end_date'] = new_end
            
            # 리밸런싱 주기
            self.console.print(f"\n🔄 리밸런싱 주기 설정")
            current_freq = self.current_build['rebalancing_freq']
            
            freq_options = {
                "1": ("monthly", "월 단위 - 더 빈번한 리밸런싱"),
                "2": ("quarterly", "분기 단위 - 균형잡힌 접근"),
                "3": ("yearly", "연 단위 - 장기 보유 전략")
            }
            
            freq_table = Table(show_header=False, box=None)
            freq_table.add_column("Choice", style="cyan", width=3)
            freq_table.add_column("Option", style="white", width=12)
            freq_table.add_column("Description", style="dim")
            
            for choice, (freq, desc) in freq_options.items():
                marker = "👉" if freq == current_freq else "  "
                freq_table.add_row(choice, f"{marker} {freq}", desc)
            
            self.console.print(freq_table)
            
            freq_choice = Prompt.ask(
                "리밸런싱 주기를 선택하세요",
                choices=["1", "2", "3"],
                default="2" if current_freq == "quarterly" else "1" if current_freq == "monthly" else "3"
            )
            
            self.current_build['rebalancing_freq'] = freq_options[freq_choice][0]
            
            # 설정 요약
            self.show_investment_summary()
            
            return Confirm.ask("\n✅ 투자 설정이 맞습니까?", default=True)
            
        except Exception as e:
            self.console.print(f"❌ 투자 설정 중 오류: {e}", style="red")
            return False
    
    def show_investment_summary(self):
        """투자 설정 요약 표시"""
        summary_table = Table(title="📋 투자 설정 요약", show_header=False)
        summary_table.add_column("항목", style="bold blue", width=15)
        summary_table.add_column("값", style="white")
        
        summary_table.add_row("투자 금액", format_currency(self.current_build['investment_amount']))
        summary_table.add_row("백테스트 기간", f"{self.current_build['start_date']} ~ {self.current_build['end_date']}")
        summary_table.add_row("리밸런싱 주기", self.current_build['rebalancing_freq'])
        
        self.console.print(summary_table)
    
    def select_and_combine_strategies(self) -> bool:
        """2단계: 전략 선택 및 조합"""
        self.console.print("\n" + "="*60)
        self.console.print("2️⃣ 전략 선택 및 조합", style="bold blue")
        self.console.print("="*60)
        
        available_strategies = self.combiner.get_available_strategies()
        
        while True:
            # 사용 가능한 전략 표시
            self.show_available_strategies(available_strategies)
            
            # 현재 선택된 전략들 표시
            if self.current_build['strategies']:
                self.show_current_strategy_mix()
            
            # 전략 선택 메뉴
            action = self.show_strategy_selection_menu()
            
            if action == "1":  # 전략 추가
                if not self.add_strategy(available_strategies):
                    continue
            elif action == "2":  # 가중치 조정
                if not self.current_build['strategies']:
                    self.console.print("❌ 먼저 전략을 추가해주세요.", style="red")
                    continue
                if not self.adjust_weights():
                    continue
            elif action == "3":  # 전략 제거
                if not self.current_build['strategies']:
                    self.console.print("❌ 제거할 전략이 없습니다.", style="red")
                    continue
                if not self.remove_strategy():
                    continue
            elif action == "4":  # 다음 단계
                if not self.current_build['strategies']:
                    self.console.print("❌ 최소 1개 전략을 선택해주세요.", style="red")
                    continue
                break
            elif action == "5":  # 이전 단계
                return self.setup_investment_parameters()
        
        return True
    
    def show_available_strategies(self, strategies: Dict[str, Dict]):
        """사용 가능한 전략 표시"""
        strategy_table = Table(title="📊 사용 가능한 전략", show_header=True)
        strategy_table.add_column("ID", style="cyan", width=4)
        strategy_table.add_column("카테고리", style="blue", width=12)
        strategy_table.add_column("전략명", style="white", width=15)
        strategy_table.add_column("설명", style="dim", width=40)
        
        strategy_id = 1
        self._strategy_mapping = {}  # ID와 전략 이름 매핑
        
        for category, strategy_list in strategies.items():
            for strategy_name, strategy_info in strategy_list.items():
                strategy_table.add_row(
                    str(strategy_id),
                    category,
                    strategy_name,
                    strategy_info.get('description', '설명 없음')
                )
                self._strategy_mapping[str(strategy_id)] = strategy_name
                strategy_id += 1
        
        self.console.print(strategy_table)
    
    def show_current_strategy_mix(self):
        """현재 전략 조합 표시"""
        current_table = Table(title="🎯 현재 선택된 전략", show_header=True)
        current_table.add_column("전략명", style="bold green", width=15)
        current_table.add_column("가중치", style="white", width=10)
        current_table.add_column("유형", style="dim", width=10)
        
        total_weight = 0
        for strategy_info in self.current_build['strategies']:
            weight_str = f"{strategy_info['weight']:.1%}"
            current_table.add_row(
                strategy_info['name'],
                weight_str,
                strategy_info.get('category', 'Unknown')
            )
            total_weight += strategy_info['weight']
        
        current_table.add_row("", "─────", "")
        current_table.add_row("총합", f"{total_weight:.1%}", "", style="bold")
        
        # 가중치 경고
        if abs(total_weight - 1.0) > 0.01:
            current_table.add_row("", "⚠️ 100%가 아님", "", style="yellow")
        
        self.console.print(current_table)
    
    def show_strategy_selection_menu(self) -> str:
        """전략 선택 메뉴"""
        menu_table = Table(show_header=False, box=None)
        menu_table.add_column("Option", style="cyan", width=3)
        menu_table.add_column("Action", style="white")
        
        menu_options = [
            ("1", "➕ 전략 추가"),
            ("2", "⚖️ 가중치 조정"),
            ("3", "❌ 전략 제거"),
            ("4", "➡️ 다음 단계 (파라미터 조정)"),
            ("5", "⬅️ 이전 단계 (투자 설정)")
        ]
        
        for option, action in menu_options:
            menu_table.add_row(option, action)
        
        self.console.print("\n" + "─"*40)
        self.console.print(menu_table)
        
        return Prompt.ask(
            "원하는 작업을 선택하세요",
            choices=["1", "2", "3", "4", "5"],
            default="1"
        )
    
    def add_strategy(self, available_strategies: Dict) -> bool:
        """전략 추가"""
        try:
            strategy_id = Prompt.ask(
                "\n추가할 전략의 ID를 입력하세요",
                choices=list(self._strategy_mapping.keys())
            )
            
            strategy_name = self._strategy_mapping[strategy_id]
            
            # 이미 추가된 전략인지 확인
            existing_names = [s['name'] for s in self.current_build['strategies']]
            if strategy_name in existing_names:
                self.console.print(f"❌ '{strategy_name}' 전략이 이미 추가되어 있습니다.", style="red")
                return False
            
            # 가중치 입력
            remaining_weight = 1.0 - sum(s['weight'] for s in self.current_build['strategies'])
            if remaining_weight <= 0:
                self.console.print("❌ 총 가중치가 이미 100%입니다. 기존 전략을 조정해주세요.", style="red")
                return False
            
            weight = FloatPrompt.ask(
                f"가중치를 입력하세요 (0.0-{remaining_weight:.2f})",
                default=min(0.2, remaining_weight)
            )
            
            if weight <= 0 or weight > remaining_weight:
                self.console.print(f"❌ 가중치는 0과 {remaining_weight:.2f} 사이여야 합니다.", style="red")
                return False
            
            # 전략 카테고리 찾기
            category = None
            for cat, strategies in available_strategies.items():
                if strategy_name in strategies:
                    category = cat
                    break
            
            # 전략 추가
            self.current_build['strategies'].append({
                'name': strategy_name,
                'weight': weight,
                'category': category
            })
            
            self.console.print(f"✅ '{strategy_name}' 전략이 추가되었습니다.", style="green")
            return True
            
        except Exception as e:
            self.console.print(f"❌ 전략 추가 중 오류: {e}", style="red")
            return False
    
    def adjust_weights(self) -> bool:
        """가중치 조정"""
        try:
            self.console.print("\n⚖️ 가중치 조정")
            self.console.print("전략별로 새로운 가중치를 입력하세요. (합계가 1.0이 되어야 함)")
            
            new_weights = []
            total_weight = 0
            
            for i, strategy_info in enumerate(self.current_build['strategies']):
                current_weight = strategy_info['weight']
                new_weight = FloatPrompt.ask(
                    f"{strategy_info['name']} 가중치 (현재: {current_weight:.2f})",
                    default=current_weight
                )
                
                if new_weight < 0:
                    self.console.print("❌ 가중치는 0 이상이어야 합니다.", style="red")
                    return False
                
                new_weights.append(new_weight)
                total_weight += new_weight
            
            # 가중치 합계 확인
            if abs(total_weight - 1.0) > 0.01:
                normalize = Confirm.ask(
                    f"가중치 합계가 {total_weight:.3f}입니다. 자동으로 정규화하시겠습니까?",
                    default=True
                )
                
                if normalize:
                    new_weights = [w / total_weight for w in new_weights]
                else:
                    return False
            
            # 가중치 업데이트
            for i, new_weight in enumerate(new_weights):
                self.current_build['strategies'][i]['weight'] = new_weight
            
            self.console.print("✅ 가중치가 조정되었습니다.", style="green")
            return True
            
        except Exception as e:
            self.console.print(f"❌ 가중치 조정 중 오류: {e}", style="red")
            return False
    
    def remove_strategy(self) -> bool:
        """전략 제거"""
        try:
            # 현재 전략 목록 표시
            strategy_table = Table(show_header=False, box=None)
            strategy_table.add_column("ID", style="cyan", width=3)
            strategy_table.add_column("Strategy", style="white", width=15)
            strategy_table.add_column("Weight", style="dim", width=10)
            
            for i, strategy_info in enumerate(self.current_build['strategies']):
                strategy_table.add_row(
                    str(i + 1),
                    strategy_info['name'],
                    f"{strategy_info['weight']:.1%}"
                )
            
            self.console.print("\n❌ 제거할 전략 선택")
            self.console.print(strategy_table)
            
            strategy_choices = [str(i + 1) for i in range(len(self.current_build['strategies']))]
            choice = Prompt.ask(
                "제거할 전략 번호",
                choices=strategy_choices + ["0"],
                default="0"
            )
            
            if choice == "0":
                return True  # 취소
            
            removed_strategy = self.current_build['strategies'].pop(int(choice) - 1)
            self.console.print(f"✅ '{removed_strategy['name']}' 전략이 제거되었습니다.", style="green")
            
            # 가중치 재분배 제안
            if self.current_build['strategies']:
                redistribute = Confirm.ask(
                    "제거된 전략의 가중치를 나머지 전략에 균등 분배하시겠습니까?",
                    default=True
                )
                
                if redistribute:
                    removed_weight = removed_strategy['weight']
                    weight_per_strategy = removed_weight / len(self.current_build['strategies'])
                    
                    for strategy_info in self.current_build['strategies']:
                        strategy_info['weight'] += weight_per_strategy
            
            return True
            
        except Exception as e:
            self.console.print(f"❌ 전략 제거 중 오류: {e}", style="red")
            return False
    
    def tune_strategy_parameters(self) -> bool:
        """3단계: 전략 파라미터 조정"""
        self.console.print("\n" + "="*60)
        self.console.print("3️⃣ 전략별 파라미터 조정", style="bold blue")
        self.console.print("="*60)
        
        try:
            for strategy_info in self.current_build['strategies']:
                strategy_name = strategy_info['name']
                self.console.print(f"\n🔧 {strategy_name} 전략 파라미터 조정")
                
                # 전략별 기본 파라미터 가져오기
                default_params = self.config['strategies'].get(strategy_name.lower(), {})
                current_params = self.current_build['parameters'].get(strategy_name, default_params.copy())
                
                if not self.tune_individual_strategy_params(strategy_name, current_params, default_params):
                    return False
                
                self.current_build['parameters'][strategy_name] = current_params
            
            # 파라미터 요약 표시
            self.show_parameters_summary()
            
            return Confirm.ask("\n✅ 파라미터 설정이 완료되었습니다. 계속하시겠습니까?", default=True)
            
        except Exception as e:
            self.console.print(f"❌ 파라미터 조정 중 오류: {e}", style="red")
            return False
    
    def tune_individual_strategy_params(self, strategy_name: str, current_params: Dict, default_params: Dict) -> bool:
        """개별 전략 파라미터 조정"""
        try:
            # 파라미터가 없으면 기본값 사용
            if not default_params:
                self.console.print(f"'{strategy_name}' 전략에 조정 가능한 파라미터가 없습니다.", style="dim")
                return True
            
            # 현재 파라미터 표시
            param_table = Table(title=f"{strategy_name} 파라미터", show_header=True)
            param_table.add_column("파라미터", style="blue", width=20)
            param_table.add_column("현재 값", style="white", width=12)
            param_table.add_column("기본 값", style="dim", width=12)
            param_table.add_column("설명", style="dim")
            
            param_descriptions = {
                'lookback_period': '수익률 계산 기간 (일)',
                'min_return_threshold': '최소 수익률 임계값',
                'period': '계산 기간 (일)',
                'overbought': 'RSI 과매수 기준',
                'oversold': 'RSI 과매도 기준',
                'std_dev': '표준편차 배수',
                'fast_period': 'MACD 빠른 기간',
                'slow_period': 'MACD 느린 기간',
                'signal_period': 'MACD 신호 기간',
                'zscore_threshold': 'Z-Score 임계값',
                'max_pe_ratio': '최대 PER',
                'max_pb_ratio': '최대 PBR',
                'min_market_cap': '최소 시가총액',
                'min_roe': '최소 ROE (%)',
                'min_roa': '최소 ROA (%)',
                'max_debt_equity': '최대 부채비율',
                'min_revenue_growth': '최소 매출 성장률 (%)',
                'min_earnings_growth': '최소 이익 성장률 (%)',
                'min_dividend_yield': '최소 배당수익률 (%)',
                'top_n': '선택할 종목 수'
            }
            
            for param, default_value in default_params.items():
                if param == 'description':  # 설명은 제외
                    continue
                    
                current_value = current_params.get(param, default_value)
                description = param_descriptions.get(param, '설명 없음')
                
                param_table.add_row(
                    param,
                    str(current_value),
                    str(default_value),
                    description
                )
            
            self.console.print(param_table)
            
            # 파라미터 수정 여부 확인
            if not Confirm.ask("\n파라미터를 수정하시겠습니까?", default=False):
                return True
            
            # 개별 파라미터 수정
            for param, default_value in default_params.items():
                if param == 'description':
                    continue
                
                current_value = current_params.get(param, default_value)
                description = param_descriptions.get(param, '')
                
                if isinstance(default_value, (int, float)):
                    if isinstance(default_value, int):
                        new_value = IntPrompt.ask(
                            f"{param} ({description})",
                            default=int(current_value)
                        )
                    else:
                        new_value = FloatPrompt.ask(
                            f"{param} ({description})",
                            default=float(current_value)
                        )
                    
                    current_params[param] = new_value
                else:
                    # 문자열 파라미터
                    new_value = Prompt.ask(
                        f"{param} ({description})",
                        default=str(current_value)
                    )
                    current_params[param] = new_value
            
            return True
            
        except Exception as e:
            self.console.print(f"❌ 파라미터 조정 중 오류: {e}", style="red")
            return False
    
    def show_parameters_summary(self):
        """파라미터 요약 표시"""
        summary_table = Table(title="🔧 파라미터 설정 요약", show_header=True)
        summary_table.add_column("전략", style="bold blue", width=15)
        summary_table.add_column("주요 파라미터", style="white")
        
        for strategy_name, params in self.current_build['parameters'].items():
            # 주요 파라미터만 표시 (최대 3개)
            key_params = []
            param_count = 0
            
            for param, value in params.items():
                if param == 'description' or param_count >= 3:
                    continue
                    
                if isinstance(value, float):
                    key_params.append(f"{param}={value:.2f}")
                else:
                    key_params.append(f"{param}={value}")
                param_count += 1
            
            if param_count > 3:
                key_params.append("...")
            
            summary_table.add_row(strategy_name, ", ".join(key_params))
        
        self.console.print(summary_table)
    
    def confirm_final_setup(self) -> bool:
        """4단계: 최종 확인"""
        self.console.print("\n" + "="*60)
        self.console.print("4️⃣ 최종 확인 및 백테스트 실행", style="bold blue")
        self.console.print("="*60)
        
        # 전체 설정 요약
        self.show_complete_summary()
        
        # 최종 확인
        if not Confirm.ask("\n🚀 위 설정으로 백테스트를 실행하시겠습니까?", default=True):
            return False
        
        # 예상 실행 시간 안내
        estimated_time = len(self.current_build['strategies']) * 5  # 전략당 약 5초 예상
        self.console.print(f"\n⏱️ 예상 실행 시간: 약 {estimated_time}초", style="dim")
        
        return True
    
    def show_complete_summary(self):
        """전체 설정 요약"""
        # 투자 설정 요약
        investment_table = Table(title="💰 투자 설정", show_header=False, box=None)
        investment_table.add_column("항목", style="bold blue", width=15)
        investment_table.add_column("값", style="white")
        
        investment_table.add_row("투자 금액", format_currency(self.current_build['investment_amount']))
        investment_table.add_row("백테스트 기간", f"{self.current_build['start_date']} ~ {self.current_build['end_date']}")
        investment_table.add_row("리밸런싱 주기", self.current_build['rebalancing_freq'])
        
        self.console.print(investment_table)
        self.console.print()
        
        # 전략 조합 요약
        strategy_table = Table(title="🎯 전략 조합", show_header=True)
        strategy_table.add_column("전략명", style="bold green", width=15)
        strategy_table.add_column("가중치", style="white", width=10)
        strategy_table.add_column("카테고리", style="dim", width=12)
        strategy_table.add_column("주요 파라미터", style="dim")
        
        for strategy_info in self.current_build['strategies']:
            strategy_name = strategy_info['name']
            weight = format_percentage(strategy_info['weight'])
            category = strategy_info.get('category', 'Unknown')
            
            # 주요 파라미터 (최대 2개)
            params = self.current_build['parameters'].get(strategy_name, {})
            key_params = []
            for i, (param, value) in enumerate(params.items()):
                if i >= 2 or param == 'description':
                    break
                if isinstance(value, float):
                    key_params.append(f"{param}={value:.1f}")
                else:
                    key_params.append(f"{param}={value}")
            
            strategy_table.add_row(
                strategy_name,
                weight,
                category,
                ", ".join(key_params) if key_params else "기본값"
            )
        
        self.console.print(strategy_table)
        
        # 포트폴리오 설정 요약
        portfolio_table = Table(title="💼 포트폴리오 설정", show_header=False, box=None)
        portfolio_table.add_column("항목", style="bold blue", width=20)
        portfolio_table.add_column("값", style="white")
        
        portfolio_table.add_row("최대 포지션 수", str(self.config['portfolio']['max_positions']))
        portfolio_table.add_row("최대 단일 포지션 비중", format_percentage(self.config['portfolio']['max_position_size']))
        portfolio_table.add_row("거래 비용", format_percentage(self.config['portfolio']['transaction_cost']))
        
        self.console.print(portfolio_table)