"""
File: backtester/graph/equity_curve_chart.py
Equity Curve Chart - 자산 성장 곡선 (가장 중요한 그래프!)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from typing import Dict, Optional

class EquityCurveChart:
    """
    Equity Curve (자산 성장 곡선) 차트 생성기
    퀀트 전략에서 가장 중요한 그래프!
    """
    
    def __init__(self, output_dir: str = "charts"):
        self.output_dir = output_dir
    
    def create(self, chart_data: Dict) -> bool:
        """
        Equity Curve 차트 생성
        
        Args:
            chart_data: 차트 데이터
                - portfolio_history: 포트폴리오 가치 시계열
                - symbol: 종목 심볼
                - strategy_name: 전략명
                - total_return: 총 수익률
                - sharpe_ratio: 샤프 비율
                
        Returns:
            bool: 성공 여부
        """
        try:
            # 데이터 추출
            portfolio_history = chart_data['portfolio_history']
            symbol = chart_data.get('symbol', 'Portfolio')
            strategy_name = chart_data.get('strategy_name', 'Strategy')
            total_return = chart_data.get('total_return', 0)
            sharpe_ratio = chart_data.get('sharpe_ratio', 0)
            
            # pandas Series로 변환 (필요시)
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
            
            # Figure 생성
            fig, ax = plt.subplots(figsize=(14, 8))
            
            # 메인 Equity Curve
            ax.plot(portfolio_history.index, portfolio_history.values, 
                   linewidth=2.5, color='#1f77b4', label='Portfolio Value')
            
            # 시작점과 끝점 강조
            ax.scatter(portfolio_history.index[0], portfolio_history.iloc[0], 
                      color='green', s=100, zorder=5, label='Start')
            ax.scatter(portfolio_history.index[-1], portfolio_history.iloc[-1], 
                      color='red', s=100, zorder=5, label='End')
            
            # 최고점 표시
            max_idx = portfolio_history.idxmax()
            max_val = portfolio_history.max()
            ax.scatter(max_idx, max_val, color='gold', s=150, 
                      marker='*', zorder=5, label='Peak')
            
            # 그래프 꾸미기
            ax.set_title(f'📈 Equity Curve - {strategy_name}\n'
                        f'Symbol: {symbol} | Total Return: {total_return:.1f}% | Sharpe: {sharpe_ratio:.2f}',
                        fontsize=14, fontweight='bold', pad=20)
            
            ax.set_xlabel('Date', fontsize=12)
            ax.set_ylabel('Portfolio Value ($)', fontsize=12)
            ax.grid(True, alpha=0.3)
            ax.legend(loc='upper left')
            
            # X축 날짜 포맷팅
            if len(portfolio_history) > 1000:  # 3년 이상 데이터
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
                ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
            else:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            
            plt.xticks(rotation=45)
            
            # 성과 통계 텍스트 박스
            stats_text = self._create_stats_text(portfolio_history, total_return, sharpe_ratio)
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='lightblue', alpha=0.8),
                   verticalalignment='top', fontsize=10)
            
            # 수익률 구간별 색상 표시
            self._add_return_regions(ax, portfolio_history)
            
            plt.tight_layout()
            
            # 저장
            filepath = f"{self.output_dir}/equity_curve.png"
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"✅ Equity Curve 저장: {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ Equity Curve 생성 실패: {str(e)}")
            return False
    
    def _create_stats_text(self, portfolio_history: pd.Series, total_return: float, sharpe_ratio: float) -> str:
        """통계 텍스트 생성"""
        try:
            # 기본 통계
            start_value = portfolio_history.iloc[0]
            end_value = portfolio_history.iloc[-1]
            max_value = portfolio_history.max()
            min_value = portfolio_history.min()
            
            # 계산된 수익률 (데이터에서)
            calculated_return = (end_value / start_value - 1) * 100
            
            # 변동성 계산
            returns = portfolio_history.pct_change().dropna()
            volatility = returns.std() * np.sqrt(252) * 100  # 연간화
            
            # 최대 낙폭 계산
            peak = portfolio_history.cummax()
            drawdown = (portfolio_history - peak) / peak
            max_drawdown = drawdown.min() * 100
            
            stats_text = f"""📊 Portfolio Statistics
• Start Value: ${start_value:,.0f}
• End Value: ${end_value:,.0f}
• Peak Value: ${max_value:,.0f}
• Total Return: {calculated_return:.1f}%
• Sharpe Ratio: {sharpe_ratio:.2f}
• Volatility: {volatility:.1f}%
• Max Drawdown: {max_drawdown:.1f}%
• Period: {len(portfolio_history)} days"""
            
            return stats_text
            
        except Exception as e:
            return f"📊 Stats calculation error: {str(e)}"
    
    def _add_return_regions(self, ax, portfolio_history: pd.Series):
        """수익률 구간별 배경색 추가"""
        try:
            # 시작값 기준 수익률 계산
            start_value = portfolio_history.iloc[0]
            returns = (portfolio_history / start_value - 1) * 100
            
            # 구간별 색상
            profit_mask = returns > 0
            loss_mask = returns <= 0
            
            # 수익 구간 (연한 초록)
            if profit_mask.any():
                profit_dates = portfolio_history.index[profit_mask]
                if len(profit_dates) > 1:
                    ax.axvspan(profit_dates[0], profit_dates[-1], 
                              alpha=0.1, color='green', label='Profit Period')
            
            # 손실 구간 (연한 빨강)
            if loss_mask.any():
                loss_dates = portfolio_history.index[loss_mask]
                if len(loss_dates) > 1:
                    ax.axvspan(loss_dates[0], loss_dates[-1], 
                              alpha=0.1, color='red', label='Loss Period')
                              
        except Exception as e:
            print(f"⚠️ Return regions 추가 실패: {str(e)}")
    
    def create_comparison_equity_curves(self, multiple_data: Dict) -> bool:
        """
        여러 전략의 Equity Curve 비교
        
        Args:
            multiple_data: {strategy_name: chart_data} 형태
            
        Returns:
            bool: 성공 여부
        """
        try:
            fig, ax = plt.subplots(figsize=(14, 8))
            
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
            
            for i, (strategy_name, chart_data) in enumerate(multiple_data.items()):
                portfolio_history = chart_data['portfolio_history']
                
                if isinstance(portfolio_history, list):
                    portfolio_history = pd.Series(portfolio_history)
                
                # 정규화 (시작값을 100으로)
                normalized = portfolio_history / portfolio_history.iloc[0] * 100
                
                ax.plot(normalized.index, normalized.values,
                       linewidth=2, label=strategy_name, 
                       color=colors[i % len(colors)])
            
            ax.set_title('📈 Strategy Equity Curves Comparison', 
                        fontsize=14, fontweight='bold')
            ax.set_xlabel('Date')
            ax.set_ylabel('Normalized Value (Start = 100)')
            ax.grid(True, alpha=0.3)
            ax.legend()
            
            plt.tight_layout()
            
            filepath = f"{self.output_dir}/equity_curves_comparison.png"
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"✅ Equity Curves Comparison 저장: {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ Equity Curves Comparison 생성 실패: {str(e)}")
            return False