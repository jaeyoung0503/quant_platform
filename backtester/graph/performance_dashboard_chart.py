"""
File: backtester/graph/performance_dashboard_chart.py
Performance Dashboard Chart - 성과 대시보드
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, Optional
import calendar

class PerformanceDashboardChart:
    """
    Performance Dashboard (성과 대시보드) 차트 생성기
    핵심 성과 지표들을 한 눈에 보여주는 대시보드
    """
    
    def __init__(self, output_dir: str = "charts"):
        self.output_dir = output_dir
    
    def create(self, chart_data: Dict) -> bool:
        """
        Performance Dashboard 차트 생성
        
        Args:
            chart_data: 차트 데이터
                - portfolio_history: 포트폴리오 가치 시계열
                - strategy_name: 전략명
                - total_return: 총 수익률
                - sharpe_ratio: 샤프 비율
                - max_drawdown: 최대 낙폭
                - volatility: 변동성
                - win_rate: 승률
                
        Returns:
            bool: 성공 여부
        """
        try:
            # 데이터 추출
            portfolio_history = chart_data['portfolio_history']
            strategy_name = chart_data.get('strategy_name', 'Strategy')
            total_return = chart_data.get('total_return', 0)
            sharpe_ratio = chart_data.get('sharpe_ratio', 0)
            max_drawdown = chart_data.get('max_drawdown', 0)
            volatility = chart_data.get('volatility', 0)
            win_rate = chart_data.get('win_rate', 0)
            
            # pandas Series로 변환
            if isinstance(portfolio_history, list):
                portfolio_history = pd.Series(portfolio_history)
            
            # 인덱스가 날짜가 아닌 경우 가상 날짜 생성
            if not isinstance(portfolio_history.index, pd.DatetimeIndex):
                start_date = datetime.now() - timedelta(days=len(portfolio_history))
                portfolio_history.index = pd.date_range(
                    start=start_date, 
                    periods=len(portfolio_history), 
                    freq='D'
                )
            
            # 2x3 서브플롯 생성
            fig, axes = plt.subplots(2, 3, figsize=(18, 12))
            fig.suptitle(f'📊 Performance Dashboard - {strategy_name}', 
                        fontsize=16, fontweight='bold', y=0.95)
            
            # 1. 월별 수익률 히트맵
            self._create_monthly_returns_heatmap(axes[0, 0], portfolio_history)
            
            # 2. 누적 수익률 vs 벤치마크
            self._create_cumulative_returns(axes[0, 1], portfolio_history)
            
            # 3. 연도별 수익률
            self._create_yearly_returns(axes[0, 2], portfolio_history)
            
            # 4. 핵심 지표 요약
            self._create_metrics_summary(axes[1, 0], chart_data)
            
            # 5. 리스크-수익률 레이더 차트
            self._create_risk_return_radar(axes[1, 1], chart_data)
            
            # 6. 월별 성과 분포
            self._create_monthly_distribution(axes[1, 2], portfolio_history)
            
            plt.tight_layout(rect=[0, 0.03, 1, 0.95])
            
            # 저장
            filepath = f"{self.output_dir}/performance_dashboard.png"
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"✅ Performance Dashboard 저장: {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ Performance Dashboard 생성 실패: {str(e)}")
            return False
    
    def _create_monthly_returns_heatmap(self, ax, portfolio_history: pd.Series):
        """월별 수익률 히트맵"""
        try:
            # 월별 수익률 계산
            monthly_returns = portfolio_history.resample('M').last().pct_change().dropna() * 100
            
            if len(monthly_returns) == 0:
                ax.text(0.5, 0.5, 'No Monthly Data', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Monthly Returns Heatmap')
                return
            
            # 연도-월 매트릭스 생성
            monthly_returns.index = pd.to_datetime(monthly_returns.index)
            years = sorted(monthly_returns.index.year.unique())
            months = range(1, 13)
            
            # 데이터 매트릭스 생성
            data_matrix = np.full((len(years), 12), np.nan)
            
            for i, year in enumerate(years):
                year_data = monthly_returns[monthly_returns.index.year == year]
                for month_return in year_data.iteritems():
                    month = month_return[0].month
                    data_matrix[i, month-1] = month_return[1]
            
            # 히트맵 생성
            mask = np.isnan(data_matrix)
            sns.heatmap(data_matrix, mask=mask, annot=True, fmt='.1f', 
                       xticklabels=[calendar.month_abbr[i] for i in months],
                       yticklabels=years, cmap='RdYlGn', center=0, ax=ax)
            
            ax.set_title('Monthly Returns Heatmap (%)')
            
        except Exception as e:
            ax.text(0.5, 0.5, f'Error: {str(e)[:50]}', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Monthly Returns Heatmap (Error)')
    
    def _create_cumulative_returns(self, ax, portfolio_history: pd.Series):
        """누적 수익률 vs 벤치마크"""
        try:
            # 누적 수익률 계산 (시작점을 100으로 정규화)
            cumulative_returns = portfolio_history / portfolio_history.iloc[0] * 100
            
            # 가상 벤치마크 생성 (시장 평균 가정: 연 7% 수익)
            days = len(portfolio_history)
            benchmark_daily_return = (1.07 ** (1/252)) - 1  # 일간 수익률
            benchmark = pd.Series([100 * ((1 + benchmark_daily_return) ** i) for i in range(days)],
                                 index=portfolio_history.index)
            
            # 플롯
            ax.plot(cumulative_returns.index, cumulative_returns.values, 
                   linewidth=2, label='Strategy', color='blue')
            ax.plot(benchmark.index, benchmark.values, 
                   linewidth=2, label='Benchmark (7%)', color='red', linestyle='--')
            
            ax.set_title('Cumulative Returns vs Benchmark')
            ax.set_ylabel('Normalized Value (Start = 100)')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
        except Exception as e:
            ax.text(0.5, 0.5, f'Error: {str(e)[:50]}', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Cumulative Returns (Error)')
    
    def _create_yearly_returns(self, ax, portfolio_history: pd.Series):
        """연도별 수익률 막대 차트"""
        try:
            # 연도별 수익률 계산
            yearly_data = portfolio_history.resample('Y').last()
            yearly_returns = yearly_data.pct_change().dropna() * 100
            
            if len(yearly_returns) == 0:
                ax.text(0.5, 0.5, 'No Yearly Data', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Annual Returns')
                return
            
            years = [str(year.year) for year in yearly_returns.index]
            values = yearly_returns.values
            
            # 색상 설정 (양수는 초록, 음수는 빨강)
            colors = ['green' if v > 0 else 'red' for v in values]
            
            bars = ax.bar(years, values, color=colors, alpha=0.7)
            
            # 값 표시
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + (1 if height >= 0 else -2),
                       f'{value:.1f}%', ha='center', va='bottom' if height >= 0 else 'top')
            
            ax.set_title('Annual Returns')
            ax.set_ylabel('Return (%)')
            ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
            ax.grid(True, alpha=0.3)
            
        except Exception as e:
            ax.text(0.5, 0.5, f'Error: {str(e)[:50]}', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Annual Returns (Error)')
    
    def _create_metrics_summary(self, ax, chart_data: Dict):
        """핵심 지표 요약"""
        try:
            # 지표 정리
            metrics = {
                'Total Return': f"{chart_data.get('total_return', 0):.1f}%",
                'Annual Return': f"{chart_data.get('total_return', 0) / 10:.1f}%",  # 10년 가정
                'Sharpe Ratio': f"{chart_data.get('sharpe_ratio', 0):.2f}",
                'Max Drawdown': f"{abs(chart_data.get('max_drawdown', 0)):.1f}%",
                'Volatility': f"{chart_data.get('volatility', 0):.1f}%",
                'Win Rate': f"{chart_data.get('win_rate', 0):.1f}%"
            }
            
            # 색상 매핑 (좋은 지표는 초록, 나쁜 지표는 빨강)
            colors = {
                'Total Return': 'green' if chart_data.get('total_return', 0) > 0 else 'red',
                'Annual Return': 'green' if chart_data.get('total_return', 0) > 0 else 'red',
                'Sharpe Ratio': 'green' if chart_data.get('sharpe_ratio', 0) > 1 else 'orange',
                'Max Drawdown': 'red' if abs(chart_data.get('max_drawdown', 0)) > 20 else 'orange',
                'Volatility': 'red' if chart_data.get('volatility', 0) > 25 else 'green',
                'Win Rate': 'green' if chart_data.get('win_rate', 0) > 50 else 'red'
            }
            
            ax.axis('off')
            
            y_positions = np.linspace(0.9, 0.1, len(metrics))
            
            for i, (metric, value) in enumerate(metrics.items()):
                color = colors.get(metric, 'black')
                ax.text(0.1, y_positions[i], f'{metric}:', fontsize=12, fontweight='bold')
                ax.text(0.6, y_positions[i], value, fontsize=12, color=color, fontweight='bold')
            
            ax.set_title('Key Metrics Summary', fontsize=14, fontweight='bold', pad=20)
            
        except Exception as e:
            ax.text(0.5, 0.5, f'Error: {str(e)[:50]}', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Key Metrics (Error)')
    
    def _create_risk_return_radar(self, ax, chart_data: Dict):
        """리스크-수익률 레이더 차트"""
        try:
            # 지표들을 0-10 스케일로 정규화
            metrics = {
                'Return': min(max(chart_data.get('total_return', 0) / 10, 0), 10),  # 100% = 10점
                'Sharpe': min(max(chart_data.get('sharpe_ratio', 0) * 2, 0), 10),    # 5.0 = 10점
                'Stability': min(max(10 - abs(chart_data.get('max_drawdown', 0)) / 5, 0), 10),  # 낙폭 낮을수록 높은 점수
                'Win Rate': min(max(chart_data.get('win_rate', 0) / 10, 0), 10),    # 100% = 10점
                'Low Risk': min(max(10 - chart_data.get('volatility', 0) / 3, 0), 10)  # 변동성 낮을수록 높은 점수
            }
            
            # 레이더 차트 데이터 준비
            labels = list(metrics.keys())
            values = list(metrics.values())
            
            # 각도 계산
            angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
            values += values[:1]  # 닫힌 도형을 위해 첫 번째 값 추가
            angles += angles[:1]
            
            # 레이더 차트 그리기
            ax.plot(angles, values, 'o-', linewidth=2, color='blue')
            ax.fill(angles, values, alpha=0.25, color='blue')
            
            # 라벨 추가
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(labels)
            ax.set_ylim(0, 10)
            ax.set_title('Risk-Return Profile', fontweight='bold')
            ax.grid(True)
            
        except Exception as e:
            ax.text(0.5, 0.5, f'Error: {str(e)[:50]}', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Risk-Return Profile (Error)')
    
    def _create_monthly_distribution(self, ax, portfolio_history: pd.Series):
        """월별 성과 분포"""
        try:
            # 월별 수익률 계산
            monthly_returns = portfolio_history.resample('M').last().pct_change().dropna() * 100
            
            if len(monthly_returns) == 0:
                ax.text(0.5, 0.5, 'No Monthly Data', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Monthly Returns Distribution')
                return
            
            # 히스토그램
            ax.hist(monthly_returns.values, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
            
            # 평균선
            mean_return = monthly_returns.mean()
            ax.axvline(mean_return, color='red', linestyle='--', linewidth=2, 
                      label=f'Mean: {mean_return:.1f}%')
            
            # 통계 정보
            std_return = monthly_returns.std()
            ax.axvline(mean_return + std_return, color='orange', linestyle=':', 
                      label=f'+1σ: {mean_return + std_return:.1f}%')
            ax.axvline(mean_return - std_return, color='orange', linestyle=':', 
                      label=f'-1σ: {mean_return - std_return:.1f}%')
            
            ax.set_title('Monthly Returns Distribution')
            ax.set_xlabel('Monthly Return (%)')
            ax.set_ylabel('Frequency')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
        except Exception as e:
            ax.text(0.5, 0.5, f'Error: {str(e)[:50]}', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Monthly Returns Distribution (Error)')