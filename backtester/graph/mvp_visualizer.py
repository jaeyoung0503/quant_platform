"""
File: backtester/graph/mvp_visualizer.py
MVP Portfolio Visualizer - 핵심 3개 그래프만 지원
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

# MVP 전용 차트 생성기들 import
from .equity_curve_chart import EquityCurveChart
from .performance_dashboard_chart import PerformanceDashboardChart  
from .drawdown_analysis_chart import DrawdownAnalysisChart

class MVPPortfolioVisualizer:
    """
    MVP 버전 포트폴리오 시각화 클래스
    핵심 3개 그래프만 지원: Equity Curve, Performance Dashboard, Drawdown Analysis
    """
    
    def __init__(self, output_dir: str = "charts", style: str = "seaborn-v0_8"):
        """
        Initialize MVP Portfolio Visualizer
        
        Args:
            output_dir: 차트 저장 디렉토리
            style: matplotlib 스타일
        """
        self.output_dir = output_dir
        self.style = style
        
        # 출력 디렉토리 생성
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # matplotlib 설정
        plt.style.use(style)
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.grid'] = True
        plt.rcParams['grid.alpha'] = 0.3
        
        # 한글 폰트 설정 (선택사항)
        try:
            plt.rcParams['font.family'] = 'DejaVu Sans'
        except:
            pass
        
        # MVP 차트 생성기들 초기화
        self.equity_chart = EquityCurveChart(output_dir)
        self.performance_chart = PerformanceDashboardChart(output_dir)
        self.drawdown_chart = DrawdownAnalysisChart(output_dir)
        
        print("✅ MVP PortfolioVisualizer 초기화 완료 (핵심 3개 그래프)")

    def create_equity_curve(self, chart_data: Dict) -> bool:
        """
        1️⃣ Equity Curve (자산 성장 곡선) 생성 - 가장 중요!
        
        Args:
            chart_data: 차트 데이터 딕셔너리
            
        Returns:
            bool: 성공 여부
        """
        try:
            return self.equity_chart.create(chart_data)
        except Exception as e:
            print(f"❌ Equity Curve 생성 실패: {str(e)}")
            return False

    def create_performance_dashboard(self, chart_data: Dict) -> bool:
        """
        2️⃣ Performance Dashboard (성과 대시보드) 생성
        
        Args:
            chart_data: 차트 데이터 딕셔너리
            
        Returns:
            bool: 성공 여부
        """
        try:
            return self.performance_chart.create(chart_data)
        except Exception as e:
            print(f"❌ Performance Dashboard 생성 실패: {str(e)}")
            return False

    def create_drawdown_analysis(self, chart_data: Dict) -> bool:
        """
        3️⃣ Drawdown Analysis (낙폭 분석) 생성
        
        Args:
            chart_data: 차트 데이터 딕셔너리
            
        Returns:
            bool: 성공 여부
        """
        try:
            return self.drawdown_chart.create(chart_data)
        except Exception as e:
            print(f"❌ Drawdown Analysis 생성 실패: {str(e)}")
            return False

    def create_mvp_suite(self, chart_data: Dict) -> tuple:
        """
        MVP 핵심 3개 그래프 한 번에 생성
        
        Args:
            chart_data: 차트 데이터 딕셔너리
            
        Returns:
            tuple: (성공한 차트 수, 전체 차트 수)
        """
        print("🎨 MVP 핵심 3개 그래프 생성 시작...")
        
        success_count = 0
        total_count = 3
        
        # 1️⃣ Equity Curve (가장 중요!)
        print("📈 1. Equity Curve 생성 중...")
        if self.create_equity_curve(chart_data):
            success_count += 1
            print("✅ Equity Curve 완료")
        else:
            print("❌ Equity Curve 실패")
        
        # 2️⃣ Performance Dashboard
        print("📊 2. Performance Dashboard 생성 중...")
        if self.create_performance_dashboard(chart_data):
            success_count += 1
            print("✅ Performance Dashboard 완료")
        else:
            print("❌ Performance Dashboard 실패")
        
        # 3️⃣ Drawdown Analysis
        print("📉 3. Drawdown Analysis 생성 중...")
        if self.create_drawdown_analysis(chart_data):
            success_count += 1
            print("✅ Drawdown Analysis 완료")
        else:
            print("❌ Drawdown Analysis 실패")
        
        print(f"\n🎉 MVP 차트 생성 완료: {success_count}/{total_count}")
        
        return success_count, total_count

    def create_strategy_comparison(self, comparison_data: List[Dict]) -> bool:
        """
        전략 비교 차트 생성 (MVP 간소화 버전)
        
        Args:
            comparison_data: 전략별 성과 데이터 리스트
            
        Returns:
            bool: 성공 여부
        """
        try:
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('Strategy Comparison (MVP)', fontsize=16, fontweight='bold')
            
            # 데이터 준비
            strategies = [item['Strategy'] for item in comparison_data]
            annual_returns = [item['Annual_Return_%'] for item in comparison_data]
            sharpe_ratios = [item['Sharpe_Ratio'] for item in comparison_data]
            max_drawdowns = [abs(item['Max_Drawdown_%']) for item in comparison_data]
            volatilities = [item['Volatility_%'] for item in comparison_data]
            
            # 1. 연간 수익률 비교
            bars1 = axes[0,0].bar(strategies, annual_returns, 
                                  color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'][:len(strategies)])
            axes[0,0].set_title('Annual Returns Comparison')
            axes[0,0].set_ylabel('Annual Return (%)')
            axes[0,0].tick_params(axis='x', rotation=45)
            
            # 값 표시
            for bar, value in zip(bars1, annual_returns):
                axes[0,0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                              f'{value:.1f}%', ha='center', va='bottom')
            
            # 2. 샤프 비율 비교
            bars2 = axes[0,1].bar(strategies, sharpe_ratios,
                                  color=['#ff9999', '#66b3ff', '#99ff99', '#ffcc99'][:len(strategies)])
            axes[0,1].set_title('Sharpe Ratio Comparison')
            axes[0,1].set_ylabel('Sharpe Ratio')
            axes[0,1].tick_params(axis='x', rotation=45)
            axes[0,1].axhline(y=1.0, color='red', linestyle='--', alpha=0.7, label='Sharpe = 1.0')
            axes[0,1].legend()
            
            # 값 표시
            for bar, value in zip(bars2, sharpe_ratios):
                axes[0,1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                              f'{value:.2f}', ha='center', va='bottom')
            
            # 3. 리스크-수익률 산점도
            scatter = axes[1,0].scatter(volatilities, annual_returns, 
                                       s=100, alpha=0.7, 
                                       c=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'][:len(strategies)])
            axes[1,0].set_xlabel('Volatility (%)')
            axes[1,0].set_ylabel('Annual Return (%)')
            axes[1,0].set_title('Risk-Return Profile')
            
            # 전략명 라벨링
            for i, strategy in enumerate(strategies):
                axes[1,0].annotate(strategy, (volatilities[i], annual_returns[i]),
                                  xytext=(5, 5), textcoords='offset points', fontsize=9)
            
            # 4. 최대 낙폭 비교
            bars4 = axes[1,1].bar(strategies, max_drawdowns,
                                  color=['#ffb3ba', '#ffdfba', '#ffffba', '#baffc9'][:len(strategies)])
            axes[1,1].set_title('Maximum Drawdown Comparison')
            axes[1,1].set_ylabel('Max Drawdown (%)')
            axes[1,1].tick_params(axis='x', rotation=45)
            
            # 값 표시
            for bar, value in zip(bars4, max_drawdowns):
                axes[1,1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
                              f'{value:.1f}%', ha='center', va='bottom')
            
            plt.tight_layout()
            
            # 저장
            filepath = f"{self.output_dir}/strategy_comparison_mvp.png"
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"✅ 전략 비교 차트 저장: {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ 전략 비교 차트 생성 실패: {str(e)}")
            return False

    def get_chart_summary(self) -> Dict:
        """
        생성된 차트 요약 정보 반환
        
        Returns:
            Dict: 차트 정보
        """
        return {
            'total_charts': 3,
            'chart_types': [
                'Equity Curve (자산 성장 곡선)',
                'Performance Dashboard (성과 대시보드)', 
                'Drawdown Analysis (낙폭 분석)'
            ],
            'output_dir': self.output_dir,
            'version': 'MVP'
        }


# Legacy 호환성을 위한 alias
PortfolioVisualizer = MVPPortfolioVisualizer