"""
File: backtester/graph/drawdown_analysis_chart.py
Drawdown Analysis Chart - 낙폭 분석
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

class DrawdownAnalysisChart:
    """
    Drawdown Analysis (낙폭 분석) 차트 생성기
    리스크 관리의 핵심 지표인 낙폭을 상세 분석
    """
    
    def __init__(self, output_dir: str = "charts"):
        self.output_dir = output_dir
    
    def create(self, chart_data: Dict) -> bool:
        """
        Drawdown Analysis 차트 생성
        
        Args:
            chart_data: 차트 데이터
                - portfolio_history: 포트폴리오 가치 시계열
                - strategy_name: 전략명
                - max_drawdown: 최대 낙폭
                
        Returns:
            bool: 성공 여부
        """
        try:
            # 데이터 추출
            portfolio_history = chart_data['portfolio_history']
            strategy_name = chart_data.get('strategy_name', 'Strategy')
            symbol = chart_data.get('symbol', 'Portfolio')
            
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
            
            # 낙폭 계산
            peak = portfolio_history.cummax()
            drawdown = (portfolio_history - peak) / peak * 100
            max_dd = drawdown.min()
            
            # 2x2 서브플롯 생성
            fig, axes = plt.subplots(2, 2, figsize=(16, 12))
            fig.suptitle(f'📉 Drawdown Analysis - {strategy_name}\n'
                        f'Symbol: {symbol} | Max Drawdown: {max_dd:.1f}%', 
                        fontsize=16, fontweight='bold', y=0.95)
            
            # 1. 포트폴리오 가치 + 최고점
            self._create_portfolio_with_peaks(axes[0, 0], portfolio_history, peak)
            
            # 2. 낙폭 시계열
            self._create_drawdown_timeseries(axes[0, 1], drawdown)
            
            # 3. 낙폭 통계 및 회복 시간
            self._create_drawdown_statistics(axes[1, 0], drawdown, portfolio_history)
            
            # 4. 낙폭 분포 히스토그램
            self._create_drawdown_distribution(axes[1, 1], drawdown)
            
            plt.tight_layout(rect=[0, 0.03, 1, 0.92])
            
            # 저장
            filepath = f"{self.output_dir}/drawdown_analysis.png"
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"✅ Drawdown Analysis 저장: {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ Drawdown Analysis 생성 실패: {str(e)}")
            return False
    
    def _create_portfolio_with_peaks(self, ax, portfolio_history: pd.Series, peak: pd.Series):
        """포트폴리오 가치와 최고점 표시"""
        try:
            # 포트폴리오 가치
            ax.plot(portfolio_history.index, portfolio_history.values, 
                   linewidth=2, color='blue', label='Portfolio Value')
            
            # 최고점 (Peak)
            ax.plot(peak.index, peak.values, 
                   linewidth=2, color='red', linestyle='--', alpha=0.7, label='Peak')
            
            # 낙폭 구간 음영
            ax.fill_between(portfolio_history.index, portfolio_history.values, peak.values,
                           where=(portfolio_history < peak), alpha=0.3, color='red', 
                           label='Drawdown Area')
            
            # 최대 낙폭 지점 표시
            max_dd_idx = (portfolio_history - peak).idxmin()
            max_dd_val = portfolio_history[max_dd_idx]
            ax.scatter(max_dd_idx, max_dd_val, color='red', s=150, 
                      marker='v', zorder=5, label='Max Drawdown')
            
            ax.set_title('Portfolio Value & Peaks')
            ax.set_ylabel('Portfolio Value ($)')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # X축 날짜 포맷팅
            if len(portfolio_history) > 1000:
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
                ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
            
        except Exception as e:
            ax.text(0.5, 0.5, f'Error: {str(e)[:50]}', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Portfolio Value & Peaks (Error)')
    
    def _create_drawdown_timeseries(self, ax, drawdown: pd.Series):
        """낙폭 시계열 차트"""
        try:
            # 낙폭 차트
            ax.fill_between(drawdown.index, drawdown.values, 0, 
                           alpha=0.7, color='red', label='Drawdown')
            ax.plot(drawdown.index, drawdown.values, 
                   linewidth=1, color='darkred')
            
            # 최대 낙폭 라인
            max_dd = drawdown.min()
            ax.axhline(y=max_dd, color='red', linestyle='--', linewidth=2,
                      label=f'Max DD: {max_dd:.1f}%')
            
            # -10%, -20% 기준선
            ax.axhline(y=-10, color='orange', linestyle=':', alpha=0.7, label='-10%')
            ax.axhline(y=-20, color='red', linestyle=':', alpha=0.7, label='-20%')
            
            ax.set_title(f'Drawdown Over Time (Max: {max_dd:.1f}%)')
            ax.set_ylabel('Drawdown (%)')
            ax.legend()
            ax.grid(True, alpha=0.3)
            ax.set_ylim(min(max_dd * 1.1, -1), 1)
            
        except Exception as e:
            ax.text(0.5, 0.5, f'Error: {str(e)[:50]}', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Drawdown Over Time (Error)')
    
    def _create_drawdown_statistics(self, ax, drawdown: pd.Series, portfolio_history: pd.Series):
        """낙폭 통계 및 회복 시간 분석"""
        try:
            # 낙폭 기간 분석
            dd_periods = self._analyze_drawdown_periods(drawdown, portfolio_history)
            
            ax.axis('off')
            
            # 통계 텍스트 생성
            max_dd = drawdown.min()
            avg_dd = drawdown[drawdown < 0].mean() if (drawdown < 0).any() else 0
            dd_days = (drawdown < -5).sum()  # -5% 이상 낙폭 일수
            
            stats_text = f"""📊 Drawdown Statistics
            
• Maximum Drawdown: {max_dd:.1f}%
• Average Drawdown: {avg_dd:.1f}%
• Days in Drawdown (>5%): {dd_days} days
• Drawdown Frequency: {len(dd_periods)} periods

📈 Recovery Analysis"""
            
            if dd_periods:
                max_recovery = max([period['recovery_days'] for period in dd_periods if period['recovery_days'] is not None])
                avg_recovery = np.mean([period['recovery_days'] for period in dd_periods if period['recovery_days'] is not None])
                
                stats_text += f"""
• Longest Recovery: {max_recovery:.0f} days
• Average Recovery: {avg_recovery:.1f} days
• Current Status: {'In Drawdown' if drawdown.iloc[-1] < -1 else 'At Peak'}

🎯 Risk Assessment"""
                
                # 리스크 등급 평가
                if abs(max_dd) < 10:
                    risk_level = "Low Risk 🟢"
                elif abs(max_dd) < 20:
                    risk_level = "Medium Risk 🟡"
                else:
                    risk_level = "High Risk 🔴"
                
                stats_text += f"""
• Risk Level: {risk_level}
• Recovery Efficiency: {'Good' if avg_recovery < 100 else 'Poor'}
• Stability Score: {max(0, 100 + max_dd):.0f}/100"""
            
            ax.text(0.05, 0.95, stats_text, transform=ax.transAxes, 
                   fontsize=11, verticalalignment='top',
                   bbox=dict(boxstyle="round,pad=0.5", facecolor='lightblue', alpha=0.8))
            
            ax.set_title('Drawdown Statistics & Recovery Analysis', fontsize=12, fontweight='bold')
            
        except Exception as e:
            ax.text(0.5, 0.5, f'Error: {str(e)[:50]}', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Drawdown Statistics (Error)')
    
    def _create_drawdown_distribution(self, ax, drawdown: pd.Series):
        """낙폭 분포 히스토그램"""
        try:
            # 음수 낙폭만 선택
            negative_dd = drawdown[drawdown < 0].values
            
            if len(negative_dd) == 0:
                ax.text(0.5, 0.5, 'No Drawdown Data', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Drawdown Distribution')
                return
            
            # 히스토그램
            n, bins, patches = ax.hist(negative_dd, bins=30, alpha=0.7, 
                                      color='lightcoral', edgecolor='black')
            
            # 색상 그라데이션 (깊은 낙폭일수록 진한 빨강)
            for i, patch in enumerate(patches):
                patch.set_facecolor(plt.cm.Reds(0.3 + 0.7 * i / len(patches)))
            
            # 통계 라인들
            mean_dd = negative_dd.mean()
            median_dd = np.median(negative_dd)
            max_dd = negative_dd.min()
            
            ax.axvline(mean_dd, color='blue', linestyle='--', linewidth=2, 
                      label=f'Mean: {mean_dd:.1f}%')
            ax.axvline(median_dd, color='green', linestyle='--', linewidth=2, 
                      label=f'Median: {median_dd:.1f}%')
            ax.axvline(max_dd, color='red', linestyle='--', linewidth=2, 
                      label=f'Max: {max_dd:.1f}%')
            
            # VaR 라인 (95% 신뢰구간)
            var_95 = np.percentile(negative_dd, 5)
            ax.axvline(var_95, color='purple', linestyle=':', linewidth=2, 
                      label=f'VaR 95%: {var_95:.1f}%')
            
            ax.set_title('Drawdown Distribution')
            ax.set_xlabel('Drawdown (%)')
            ax.set_ylabel('Frequency')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
        except Exception as e:
            ax.text(0.5, 0.5, f'Error: {str(e)[:50]}', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Drawdown Distribution (Error)')
    
    def _analyze_drawdown_periods(self, drawdown: pd.Series, portfolio_history: pd.Series) -> list:
        """낙폭 기간 분석"""
        try:
            periods = []
            in_drawdown = False
            start_idx = None
            
            for i, dd in enumerate(drawdown):
                if dd < -1 and not in_drawdown:  # 낙폭 시작 (-1% 기준)
                    in_drawdown = True
                    start_idx = i
                elif dd >= -0.1 and in_drawdown:  # 낙폭 종료 (거의 회복)
                    in_drawdown = False
                    if start_idx is not None:
                        period_data = {
                            'start_date': drawdown.index[start_idx],
                            'end_date': drawdown.index[i],
                            'duration_days': i - start_idx,
                            'max_drawdown': drawdown.iloc[start_idx:i+1].min(),
                            'recovery_days': i - start_idx
                        }
                        periods.append(period_data)
            
            # 현재 낙폭 중인 경우
            if in_drawdown and start_idx is not None:
                period_data = {
                    'start_date': drawdown.index[start_idx],
                    'end_date': drawdown.index[-1],
                    'duration_days': len(drawdown) - start_idx,
                    'max_drawdown': drawdown.iloc[start_idx:].min(),
                    'recovery_days': None  # 아직 회복 안됨
                }
                periods.append(period_data)
            
            return periods
            
        except Exception as e:
            print(f"⚠️ Drawdown periods 분석 실패: {str(e)}")
            return []