"""
File: backtester/core.py
Quant Strategy Backtester - Core Engine (수정된 MVP 버전)
실제 차트 호출이 가능하도록 수정
"""

import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
import os

# Import only implemented strategies
from .strategies import (
    BaseStrategy,
    PERStrategy,
    RSIStrategy,
    MovingAverageStrategy,
    Top10CompositeStrategy
)

from .data_generator import DataGenerator
from .backtesting_engine import BacktestingEngine
from .portfolio_analyzer import PortfolioAnalyzer

# 수정된 import - 실제 작동하는 버전
try:
    from .graph.mvp_visualizer import MVPPortfolioVisualizer
    VISUALIZER_AVAILABLE = True
    print("✅ MVPPortfolioVisualizer import 성공")
except ImportError as e:
    print(f"⚠️ MVPPortfolioVisualizer import 실패: {e}")
    print("📊 기본 시각화 기능을 사용합니다.")
    VISUALIZER_AVAILABLE = False

class QuantBacktester:
    """Main backtesting engine for quantitative strategies"""
    
    def __init__(self):
        # Initialize components
        self.data_generator = DataGenerator()
        self.backtest_engine = BacktestingEngine()
        self.portfolio_analyzer = PortfolioAnalyzer()
        
        # 시각화 객체 초기화 (안전한 방식)
        self.visualizer = None
        if VISUALIZER_AVAILABLE:
            try:
                self.visualizer = MVPPortfolioVisualizer()
                print("✅ MVPPortfolioVisualizer 초기화 완료!")
            except Exception as e:
                print(f"⚠️ MVPPortfolioVisualizer 초기화 실패: {e}")
                self.visualizer = None
        else:
            print("📊 시각화 기능을 사용하지 않고 계속합니다.")
        
        # Load sample data
        self.sample_stocks = self.data_generator.generate_sample_data()
        
        # Strategy definitions (using only implemented strategies)
        self.strategies = self._initialize_strategies()
        self.strategy_descriptions = self._get_strategy_descriptions()
        
        # Default settings
        self.default_period_days = 3650  # 10 years

    def _initialize_strategies(self):
        """Initialize 4 core trading strategies using implemented classes"""
        return {
            '1': ('PER Value Strategy', PERStrategy()),
            '2': ('RSI Mean Reversion', RSIStrategy()),
            '3': ('Moving Average Trend', MovingAverageStrategy()),
            '4': ('TOP 10 Composite Strategy', Top10CompositeStrategy()),
        }

    def _get_strategy_descriptions(self):
        """Get strategy descriptions"""
        return {
            '1': {
                'short': 'PER 기반 가치투자 전략',
                'detailed': '''
📈 PER Value Strategy (PER 가치투자 전략)
=====================================

🎯 투자 철학:
"저평가된 우량주를 발굴하여 장기 보유"

📊 전략 개요:
• PER(주가수익비율)이 낮은 종목을 선별하는 가치투자 전략
• 12배 이하 저PER 종목 매수, 25배 이상 고PER 종목 매도
• 모멘텀 필터로 하락 추세 종목 제외
                '''
            },
            '2': {
                'short': 'RSI 기반 과매수/과매도 역발상 전략',
                'detailed': '''
🔄 RSI Mean Reversion Strategy (RSI 평균회귀 전략)
===========================================

🎯 투자 철학:
"과도하게 오르거나 내린 주식은 평균값으로 돌아간다"

📊 전략 개요:
• RSI(상대강도지수)를 활용한 과매수/과매도 구간 역발상 전략
• 30 이하 과매도에서 매수, 70 이상 과매수에서 매도
                '''
            },
            '3': {
                'short': '이동평균 기반 추세 추종 전략',
                'detailed': '''
📈 Moving Average Trend Strategy (이동평균 추세 전략)
=============================================

🎯 투자 철학:
"트렌드는 친구다 - 추세를 따라가는 것이 최선"

📊 전략 개요:
• 다중 기간 이동평균을 활용한 추세 추종 전략
• 골든크로스 매수, 데드크로스 매도
                '''
            },
            '4': {
                'short': '재무지표 + 기술지표 통합 분석',
                'detailed': '''
🎯 TOP 10 Composite Strategy (종합 지표 전략)
======================================

🎯 투자 철학:
"다양한 관점의 지표를 통합하여 종합적 투자 판단"

📊 전략 개요:
• 5개 재무지표 + 5개 기술지표를 통합한 멀티팩터 전략
• 각 지표에 가중치를 부여하여 종합 점수 산출
                '''
            }
        }

    def display_menu(self):
        """Display the main menu interface"""
        print("\n" + "="*90)
        print("    🚀 QUANTITATIVE STRATEGY BACKTESTER 2.0 - MVP VERSION 🚀")
        print("         10년 멀티종목 포트폴리오 분석 시스템 (핵심 3개 그래프)")
        print("="*90)
        print("\n📊 Available Strategies (4 Core Strategies):")
        print("-" * 90)
        
        for key, (name, _) in self.strategies.items():
            desc = self.strategy_descriptions[key]['short']
            print(f"  {key:2s}. {name:<30} - {desc}")
        
        print(f"\n🔍 전략 상세정보: 전략 번호 입력 후 'info'를 붙이면 상세 설명을 볼 수 있습니다 (예: 1 info)")
        print(f"⏰ 분석 기간: 10년 고정 (3,650일)")
        print(f"📈 분석 방식: 멀티종목 개별 분석")
        
        # 시각화 상태 표시
        if self.visualizer:
            print(f"📊 시각화: MVP 핵심 3개 그래프 (Equity Curve, Performance Dashboard, Drawdown Analysis)")
        else:
            print(f"📊 시각화: 사용 불가 (차트 생성 건너뜀)")

    def get_user_selection(self) -> str:
        """Get user selection for strategy"""
        while True:
            try:
                user_input = input("\n🎯 전략을 선택하세요 (1-4, 또는 '번호 info'로 상세정보): ").strip()
                
                # Handle detailed info request
                if ' info' in user_input:
                    strategy_num = user_input.replace(' info', '').strip()
                    if strategy_num in self.strategies and strategy_num in self.strategy_descriptions:
                        print("\n" + "="*80)
                        print(self.strategy_descriptions[strategy_num]['detailed'])
                        print("="*80)
                        continue
                    else:
                        print("❌ 해당 전략의 상세 정보가 없습니다.")
                        continue
                
                # Handle strategy selection
                if user_input in [str(i) for i in range(1, 5)]:
                    strategy_name = self.strategies[user_input][0]
                    print(f"✅ 선택된 전략: {strategy_name}")
                    if user_input in self.strategy_descriptions:
                        print(f"📝 요약: {self.strategy_descriptions[user_input]['short']}")
                    return user_input
                else:
                    print("❌ 잘못된 입력입니다. 1-4 사이의 숫자를 입력하세요.")
            except (ValueError, KeyboardInterrupt):
                print("❌ 잘못된 입력입니다. 다시 시도하세요.")

    def run_backtest(self, strategy_choice: str) -> Dict:
        """Execute the backtesting process"""
        strategy_name, strategy_obj = self.strategies[strategy_choice]
        
        print(f"\n⚡ 백테스팅 실행 중...")
        print(f"📊 전략: {strategy_name}")
        print(f"📅 기간: 10년 (3,650일)")
        print(f"🎯 분석: 멀티종목 개별 분석")
        print("-" * 60)
        
        start_time = time.time()
        
        # Run multi-stock backtest
        results = self.backtest_engine.run_multi_stock_backtest(
            strategy_obj, 
            self.sample_stocks, 
            self.default_period_days
        )
        
        execution_time = time.time() - start_time
        print(f"✅ 백테스트 완료! 실행시간: {execution_time:.2f}초")
        
        return {
            'results': results,
            'strategy_name': strategy_name,
            'execution_time': execution_time
        }

    def display_results(self, backtest_data: Dict):
        """Display formatted backtest results"""
        results = backtest_data['results']
        
        if not results:
            print("❌ 표시할 결과가 없습니다.")
            return None
        
        strategy_name = backtest_data['strategy_name']
        execution_time = backtest_data['execution_time']
        
        print(f"\n🏆 백테스트 결과 - {strategy_name}")
        print(f"⏱️  실행시간: {execution_time:.2f}초")
        print("="*100)
        
        # Display top 15 results
        print(f"\n📊 개별 종목 성과 (TOP 15)")
        print("-"*100)
        print(f"{'순위':<4} {'종목':<8} {'총수익률%':<10} {'연수익률%':<10} {'샤프':<8} {'변동성%':<8} {'최대낙폭%':<10} {'승률%':<8}")
        print("-"*100)
        
        top_stocks = results[:15]
        for i, stock in enumerate(top_stocks, 1):
            print(f"{i:<4} {stock['Symbol']:<8} {stock['Total_Return_%']:<10.2f} "
                  f"{stock['Annual_Return_%']:<10.2f} {stock['Sharpe_Ratio']:<8.2f} "
                  f"{stock['Volatility_%']:<8.2f} {stock['Max_Drawdown_%']:<10.2f} "
                  f"{stock['Win_Rate_%']:<8.2f}")
        
        return results

    def _prepare_chart_data(self, stock_result: Dict, strategy_name: str) -> Dict:
        """차트 데이터 준비"""
        try:
            # 포트폴리오 히스토리 검증 및 변환
            portfolio_history = stock_result.get('Portfolio_History', [])
            
            if not portfolio_history:
                # 가상 데이터 생성 (실제 환경에서는 실제 데이터 사용)
                print("⚠️ 포트폴리오 히스토리가 없어 가상 데이터를 생성합니다.")
                total_return = stock_result.get('Total_Return_%', 0)
                days = 2500  # 10년 가정
                
                # 총 수익률을 기반으로 가상 포트폴리오 생성
                np.random.seed(42)
                daily_returns = np.random.normal(total_return/days/100, 0.01, days)
                portfolio_values = [10000]
                for ret in daily_returns:
                    portfolio_values.append(portfolio_values[-1] * (1 + ret))
                
                portfolio_history = portfolio_values
            
            # pandas Series로 변환
            if isinstance(portfolio_history, list):
                # 날짜 인덱스 생성
                start_date = datetime.now() - timedelta(days=len(portfolio_history))
                dates = pd.date_range(start=start_date, periods=len(portfolio_history), freq='D')
                portfolio_history = pd.Series(portfolio_history, index=dates)
            
            chart_data = {
                'portfolio_history': portfolio_history,
                'symbol': stock_result.get('Symbol', 'Unknown'),
                'strategy_name': strategy_name,
                'period_name': '10년',
                'total_return': stock_result.get('Total_Return_%', 0),
                'sharpe_ratio': stock_result.get('Sharpe_Ratio', 0),
                'max_drawdown': stock_result.get('Max_Drawdown_%', 0),
                'volatility': stock_result.get('Volatility_%', 15),
                'win_rate': stock_result.get('Win_Rate_%', 50)
            }
            
            return chart_data
            
        except Exception as e:
            print(f"⚠️ 차트 데이터 준비 중 오류: {str(e)}")
            # 최소한의 기본 데이터 반환
            return {
                'portfolio_history': pd.Series([10000, 10500, 11000]),
                'symbol': 'ERROR',
                'strategy_name': strategy_name,
                'total_return': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'volatility': 15,
                'win_rate': 50
            }

    def generate_mvp_visualization(self, results, strategy_name: str):
        """Generate MVP 핵심 3개 그래프만 생성 - 실제 작동 버전"""
        
        # 시각화 기능 사용 불가 시 건너뜀
        if not self.visualizer:
            print("❌ 시각화 기능을 사용할 수 없습니다.")
            print("💡 차트 생성을 건너뛰고 텍스트 결과만 제공합니다.")
            return False
        
        if not results:
            print("❌ 시각화할 데이터가 없습니다.")
            return False
        
        print(f"\n📈 MVP 핵심 3개 그래프 생성 중...")
        print(f"📊 생성될 그래프:")
        print(f"   1️⃣ Equity Curve (자산 성장 곡선)")
        print(f"   2️⃣ Performance Dashboard (성과 대시보드)")
        print(f"   3️⃣ Drawdown Analysis (낙폭 분석)")
        
        try:
            # 최고 성과 종목 선택
            top_stock = results[0]
            print(f"📈 분석 대상: {top_stock.get('Symbol', 'Unknown')} (최고 성과 종목)")
            
            # 차트 데이터 준비
            chart_data = self._prepare_chart_data(top_stock, strategy_name)
            
            # MVP 핵심 3개 그래프 생성
            success_count, total_count = self.visualizer.create_mvp_suite(chart_data)
            
            # 결과 출력
            if success_count > 0:
                print(f"\n🎉 MVP 차트 생성 완료: {success_count}/{total_count} 성공!")
                print("📁 생성된 MVP 파일:")
                if success_count >= 1:
                    print("   - equity_curve.png (자산 성장 곡선)")
                if success_count >= 2:
                    print("   - performance_dashboard.png (성과 대시보드)")
                if success_count >= 3:
                    print("   - drawdown_analysis.png (낙폭 분석)")
                
                print(f"\n💡 MVP 버전: 핵심 3개 그래프로 퀀트 전략의 80% 분석 완료!")
                return True
            else:
                print("❌ 모든 MVP 차트 생성에 실패했습니다.")
                return False
                
        except Exception as e:
            print(f"⚠️ MVP 시각화 생성 중 오류 발생: {str(e)}")
            print("🔄 시각화 없이 계속 진행합니다.")
            return False

    def create_strategy_comparison_mode(self):
        """Create a mode to compare multiple strategies"""
        print("\n📊 전략 비교 모드 (MVP 버전)")
        print("-" * 50)
        
        selected_strategies = []
        
        while len(selected_strategies) < 4:
            print(f"\n현재 선택된 전략: {len(selected_strategies)}/4")
            for i, (name, _) in enumerate(selected_strategies, 1):
                print(f"  {i}. {name}")
            
            if len(selected_strategies) > 0:
                choice = input("\n더 추가하시겠습니까? (y/n): ").strip().lower()
                if choice not in ['y', 'yes', '네']:
                    break
            
            self.display_menu()
            strategy_choice = self.get_user_selection()
            strategy_name, strategy_obj = self.strategies[strategy_choice]
            
            if strategy_name not in [s[0] for s in selected_strategies]:
                selected_strategies.append((strategy_name, strategy_obj))
                print(f"✅ '{strategy_name}' 전략이 추가되었습니다.")
            else:
                print(f"⚠️ '{strategy_name}' 전략은 이미 선택되었습니다.")
        
        return selected_strategies

    def run_strategy_comparison(self):
        """Run comparison between multiple strategies - MVP 버전"""
        selected_strategies = self.create_strategy_comparison_mode()
        
        if len(selected_strategies) < 2:
            print("❌ 비교를 위해서는 최소 2개의 전략이 필요합니다.")
            return
        
        print(f"\n🔄 {len(selected_strategies)}개 전략 비교 분석 시작... (MVP 버전)")
        
        comparison_results = {}
        
        for strategy_name, strategy_obj in selected_strategies:
            print(f"\n📊 {strategy_name} 분석 중...")
            results = self.backtest_engine.run_multi_stock_backtest(
                strategy_obj, 
                self.sample_stocks, 
                self.default_period_days
            )
            comparison_results[strategy_name] = results
        
        # Display comparison results
        self.display_comparison_results(comparison_results)
        
        # MVP 비교 시각화 생성
        if self.visualizer and len(comparison_results) > 1:
            viz_choice = input("\n📊 전략 비교 차트를 생성하시겠습니까? (y/n): ").strip().lower()
            if viz_choice in ['y', 'yes', '네', 'ㅇ']:
                self.generate_mvp_comparison_visualization(comparison_results)

    def generate_mvp_comparison_visualization(self, comparison_results: Dict):
        """Generate MVP comparison visualization - 핵심만"""
        if not self.visualizer:
            print("❌ 시각화 기능을 사용할 수 없습니다.")
            return False
            
        try:
            # 비교 결과를 리스트 형태로 변환
            comparison_list = []
            for strategy_name, results in comparison_results.items():
                if results:
                    best_result = results[0]  # 최고 성과 종목
                    comparison_list.append({
                        'Strategy': strategy_name,
                        'Annual_Return_%': best_result['Annual_Return_%'],
                        'Sharpe_Ratio': best_result['Sharpe_Ratio'],
                        'Max_Drawdown_%': best_result['Max_Drawdown_%'],
                        'Volatility_%': best_result.get('Volatility_%', 15),
                        'Win_Rate_%': best_result.get('Win_Rate_%', 50)
                    })
            
            print("🎨 MVP 전략 비교 시각화를 생성하는 중...")
            print("📊 생성할 차트: 핵심 전략 비교 차트만")
            
            # MVP: 기본 전략 비교 차트만 생성
            success = self.visualizer.create_strategy_comparison(comparison_list)
            
            if success:
                print("✅ 전략 비교 차트가 생성되었습니다!")
                print("📁 생성된 파일: strategy_comparison_mvp.png")
                return True
            else:
                print("❌ 전략 비교 차트 생성에 실패했습니다.")
                return False
                
        except Exception as e:
            print(f"⚠️ MVP 비교 시각화 생성 중 오류: {str(e)}")
            return False

    def display_comparison_results(self, comparison_results: Dict):
        """Display comparison results between strategies"""
        print(f"\n🏆 전략 비교 결과 (MVP 버전)")
        print("="*120)
        
        # Calculate average metrics for each strategy
        strategy_metrics = {}
        for strategy_name, results in comparison_results.items():
            if results:
                avg_return = np.mean([r['Total_Return_%'] for r in results])
                avg_sharpe = np.mean([r['Sharpe_Ratio'] for r in results])
                avg_drawdown = np.mean([r['Max_Drawdown_%'] for r in results])
                avg_winrate = np.mean([r['Win_Rate_%'] for r in results])
                
                strategy_metrics[strategy_name] = {
                    'avg_return': avg_return,
                    'avg_sharpe': avg_sharpe,
                    'avg_drawdown': avg_drawdown,
                    'avg_winrate': avg_winrate,
                    'num_stocks': len(results)
                }
        
        # Display summary table
        print(f"\n📊 전략별 평균 성과")
        print("-"*120)
        print(f"{'전략명':<25} {'평균수익률%':<12} {'평균샤프':<10} {'평균낙폭%':<12} {'평균승률%':<12} {'분석종목수':<10}")
        print("-"*120)
        
        for strategy_name, metrics in strategy_metrics.items():
            print(f"{strategy_name:<25} {metrics['avg_return']:<12.2f} "
                  f"{metrics['avg_sharpe']:<10.2f} {metrics['avg_drawdown']:<12.2f} "
                  f"{metrics['avg_winrate']:<12.2f} {metrics['num_stocks']:<10}")
        
        # Rank strategies
        print(f"\n🏅 전략 순위")
        print("-"*60)
        
        # Sort by Sharpe ratio
        sorted_strategies = sorted(
            strategy_metrics.items(), 
            key=lambda x: x[1]['avg_sharpe'], 
            reverse=True
        )
        
        for i, (strategy_name, metrics) in enumerate(sorted_strategies, 1):
            print(f"{i}. {strategy_name} (샤프 비율: {metrics['avg_sharpe']:.3f})")

    def run(self):
        """Main execution loop - MVP 버전"""
        try:
            print("🔄 퀀트 전략 백테스터를 초기화하는 중... (MVP 버전)")
            
            # 시각화 상태 확인
            if self.visualizer:
                print("✅ 초기화 완료! 핵심 3개 그래프로 빠른 분석 제공")
            else:
                print("✅ 초기화 완료! (시각화 없이 텍스트 결과만 제공)")
            
            while True:
                print(f"\n🎯 모드 선택:")
                print(f"  1. 개별 전략 분석 (MVP 핵심 3개 그래프)")
                print(f"  2. 전략 비교 분석 (MVP 버전)")
                
                mode_choice = input("\n모드를 선택하세요 (1-2): ").strip()
                
                if mode_choice == '1':
                    # Individual strategy analysis
                    self.display_menu()
                    strategy_choice = self.get_user_selection()
                    
                    # Confirmation message
                    strategy_name = self.strategies[strategy_choice][0]
                    print(f"\n🚀 '{strategy_name}' 전략으로 10년 멀티종목 백테스트를 시작합니다.")
                    print(f"📊 MVP 버전: 핵심 3개 그래프로 빠른 분석")
                    
                    # Run backtest
                    backtest_data = self.run_backtest(strategy_choice)
                    
                    # Display results
                    results = self.display_results(backtest_data)
                    
                    # Generate MVP visualization (핵심 3개 그래프만)
                    if results:
                        if self.visualizer:
                            viz_choice = input("\n📊 MVP 핵심 3개 그래프를 생성하시겠습니까? (y/n): ").strip().lower()
                            if viz_choice in ['y', 'yes', '네', 'ㅇ']:
                                self.generate_mvp_visualization(results, backtest_data['strategy_name'])
                        else:
                            print("\n💡 시각화 기능이 비활성화되어 차트 생성을 건너뜁니다.")
                
                elif mode_choice == '2':
                    # Strategy comparison analysis - MVP version
                    self.run_strategy_comparison()
                
                else:
                    print("❌ 잘못된 입력입니다. 1 또는 2를 입력하세요.")
                    continue
                
                # Continue option
                print(f"\n" + "="*80)
                continue_choice = input("🔄 다른 분석을 수행하시겠습니까? (y/n): ").strip().lower()
                if continue_choice not in ['y', 'yes', '네', 'ㅇ']:
                    break
                    
        except KeyboardInterrupt:
            print(f"\n\n👋 MVP 백테스팅 세션이 종료되었습니다. 감사합니다!")
        except Exception as e:
            print(f"\n❌ 오류가 발생했습니다: {str(e)}")
            print("다시 시도하거나 지원팀에 문의해 주세요.")


# MVP 전용 간소화된 클래스
class MVPQuantBacktester(QuantBacktester):
    """MVP 버전 - 핵심 3개 그래프만 지원하는 간소화된 백테스터"""
    
    def __init__(self):
        super().__init__()
        print("🎯 MVP 모드: 핵심 3개 그래프로 빠른 퀀트 분석!")
    
    def display_menu(self):
        """MVP 전용 메뉴"""
        print("\n" + "="*90)
        print("    🚀 QUANT BACKTESTER MVP - 핵심 3개 그래프 🚀")
        print("         빠르고 효율적인 퀀트 전략 분석")
        print("="*90)
        print("\n📊 MVP 핵심 그래프:")
        print("   1️⃣ Equity Curve (자산 성장 곡선) - 가장 중요!")
        print("   2️⃣ Performance Dashboard (성과 대시보드)")
        print("   3️⃣ Drawdown Analysis (낙폭 분석)")
        print("\n📈 Available Strategies:")
        print("-" * 90)
        
        for key, (name, _) in self.strategies.items():
            desc = self.strategy_descriptions[key]['short']
            print(f"  {key:2s}. {name:<30} - {desc}")
        
        print(f"\n💡 MVP 장점: 핵심만 골라서 빠른 분석, 80% 효과를 20% 노력으로!")


if __name__ == "__main__":
    # MVP 버전으로 실행
    print("🎯 MVP 퀀트 백테스터를 시작합니다...")
    
    try:
        backtester = MVPQuantBacktester()
        backtester.run()
    except Exception as e:
        print(f"❌ 백테스터 실행 중 오류: {str(e)}")
        print("💡 의존성 문제가 있을 수 있습니다. 필요한 모듈들이 설치되어 있는지 확인해주세요.")