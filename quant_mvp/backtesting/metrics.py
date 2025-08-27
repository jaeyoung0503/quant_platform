"""
file: quant_mvp/backtesting/metrics.py
백테스트 성과 지표 계산
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PerformanceMetrics:
    """성과 지표 계산 클래스"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.risk_free_rate = 0.02  # 2% 무위험 수익률
    
    def calculate_comprehensive_metrics(self, returns: pd.Series) -> Dict[str, Any]:
        """종합적인 성과 지표 계산"""
        try:
            if returns.empty or returns.isna().all():
                logger.warning("Empty or all-NaN returns series")
                return self._get_empty_metrics()
            
            # 기본 수익률 지표
            basic_metrics = self._calculate_basic_return_metrics(returns)
            
            # 위험 지표
            risk_metrics = self._calculate_risk_metrics(returns)
            
            # 위험 조정 수익률 지표
            risk_adjusted_metrics = self._calculate_risk_adjusted_metrics(returns)
            
            # 하방 위험 지표
            downside_metrics = self._calculate_downside_metrics(returns)
            
            # 월별/연도별 분석
            periodic_metrics = self._calculate_periodic_metrics(returns)
            
            # 모든 지표 통합
            comprehensive_metrics = {
                **basic_metrics,
                **risk_metrics,
                **risk_adjusted_metrics,
                **downside_metrics,
                **periodic_metrics
            }
            
            return comprehensive_metrics
            
        except Exception as e:
            logger.error(f"Error calculating comprehensive metrics: {e}")
            return self._get_empty_metrics()
    
    def _calculate_basic_return_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """기본 수익률 지표"""
        # 누적 수익률
        cumulative_returns = (1 + returns).cumprod()
        total_return = cumulative_returns.iloc[-1] - 1
        
        # 연평균 수익률
        years = len(returns) / 252  # 252 영업일
        annual_return = (1 + total_return) ** (1/years) - 1 if years > 0 else 0
        
        # 평균 일일 수익률
        mean_daily_return = returns.mean()
        
        # 승률
        win_rate = (returns > 0).mean()
        
        # 최고/최저 수익률
        best_day = returns.max()
        worst_day = returns.min()
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'mean_daily_return': mean_daily_return,
            'win_rate': win_rate,
            'best_day_return': best_day,
            'worst_day_return': worst_day
        }
    
    def _calculate_risk_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """위험 지표"""
        # 변동성
        daily_volatility = returns.std()
        annual_volatility = daily_volatility * np.sqrt(252)
        
        # 최대 낙폭
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # 최대 낙폭 지속 기간
        max_dd_duration = self._calculate_max_drawdown_duration(drawdown)
        
        # VaR (Value at Risk) - 95% 신뢰구간
        var_95 = returns.quantile(0.05)
        
        # CVaR (Conditional Value at Risk)
        cvar_95 = returns[returns <= var_95].mean()
        
        return {
            'daily_volatility': daily_volatility,
            'annual_volatility': annual_volatility,
            'max_drawdown': max_drawdown,
            'max_drawdown_duration': max_dd_duration,
            'var_95': var_95,
            'cvar_95': cvar_95
        }
    
    def _calculate_risk_adjusted_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """위험 조정 수익률 지표"""
        annual_return = returns.mean() * 252
        annual_volatility = returns.std() * np.sqrt(252)
        
        # 샤프 비율
        sharpe_ratio = (annual_return - self.risk_free_rate) / annual_volatility if annual_volatility != 0 else 0
        
        # 정보 비율 (Information Ratio)
        # 벤치마크 대비 초과 수익률 / 추적 오차
        # 여기서는 무위험 수익률을 벤치마크로 사용
        excess_returns = returns - (self.risk_free_rate / 252)
        information_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252) if excess_returns.std() != 0 else 0
        
        # 칼마 비율 (Calmar Ratio)
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = abs(drawdown.min())
        calmar_ratio = annual_return / max_drawdown if max_drawdown != 0 else 0
        
        # 소티노 비율 (Sortino Ratio)
        downside_returns = returns[returns < 0]
        downside_deviation = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
        sortino_ratio = (annual_return - self.risk_free_rate) / downside_deviation if downside_deviation != 0 else 0
        
        return {
            'sharpe_ratio': sharpe_ratio,
            'information_ratio': information_ratio,
            'calmar_ratio': calmar_ratio,
            'sortino_ratio': sortino_ratio
        }
    
    def _calculate_downside_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """하방 위험 지표"""
        # 하방 변동성
        downside_returns = returns[returns < 0]
        downside_volatility = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
        
        # 손실 일수 비율
        loss_days_ratio = (returns < 0).mean()
        
        # 평균 손실
        avg_loss = downside_returns.mean() if len(downside_returns) > 0 else 0
        
        # 최대 연속 손실 일수
        max_consecutive_losses = self._calculate_max_consecutive_losses(returns)
        
        # 손익 비율 (Profit Factor)
        gains = returns[returns > 0]
        losses = returns[returns < 0]
        total_gains = gains.sum()
        total_losses = abs(losses.sum())
        profit_factor = total_gains / total_losses if total_losses != 0 else float('inf')
        
        return {
            'downside_volatility': downside_volatility,
            'loss_days_ratio': loss_days_ratio,
            'avg_loss': avg_loss,
            'max_consecutive_losses': max_consecutive_losses,
            'profit_factor': profit_factor
        }
    
    def _calculate_periodic_metrics(self, returns: pd.Series) -> Dict[str, Any]:
        """기간별 분석"""
        try:
            # 월별 수익률
            monthly_returns = returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
            
            # 연도별 수익률 (충분한 데이터가 있을 경우)
            yearly_returns = returns.resample('Y').apply(lambda x: (1 + x).prod() - 1)
            
            # 월별 통계
            monthly_stats = {
                'monthly_mean': monthly_returns.mean(),
                'monthly_std': monthly_returns.std(),
                'monthly_sharpe': monthly_returns.mean() / monthly_returns.std() * np.sqrt(12) if monthly_returns.std() != 0 else 0,
                'positive_months_ratio': (monthly_returns > 0).mean(),
                'best_month': monthly_returns.max(),
                'worst_month': monthly_returns.min()
            }
            
            # 연도별 통계 (2년 이상 데이터가 있을 경우)
            yearly_stats = {}
            if len(yearly_returns) >= 2:
                yearly_stats = {
                    'yearly_mean': yearly_returns.mean(),
                    'yearly_std': yearly_returns.std(),
                    'positive_years_ratio': (yearly_returns > 0).mean(),
                    'best_year': yearly_returns.max(),
                    'worst_year': yearly_returns.min()
                }
            
            return {**monthly_stats, **yearly_stats}
            
        except Exception as e:
            logger.error(f"Error calculating periodic metrics: {e}")
            return {}
    
    def _calculate_max_drawdown_duration(self, drawdown: pd.Series) -> int:
        """최대 낙폭 지속 기간 계산"""
        try:
            is_in_drawdown = drawdown < 0
            drawdown_periods = []
            current_period = 0
            
            for in_dd in is_in_drawdown:
                if in_dd:
                    current_period += 1
                else:
                    if current_period > 0:
                        drawdown_periods.append(current_period)
                    current_period = 0
            
            # 마지막 기간 처리
            if current_period > 0:
                drawdown_periods.append(current_period)
            
            return max(drawdown_periods) if drawdown_periods else 0
            
        except Exception as e:
            logger.error(f"Error calculating max drawdown duration: {e}")
            return 0
    
    def _calculate_max_consecutive_losses(self, returns: pd.Series) -> int:
        """최대 연속 손실 일수 계산"""
        try:
            is_loss = returns < 0
            max_consecutive = 0
            current_consecutive = 0
            
            for loss in is_loss:
                if loss:
                    current_consecutive += 1
                    max_consecutive = max(max_consecutive, current_consecutive)
                else:
                    current_consecutive = 0
            
            return max_consecutive
            
        except Exception as e:
            logger.error(f"Error calculating max consecutive losses: {e}")
            return 0
    
    def _get_empty_metrics(self) -> Dict[str, Any]:
        """빈 지표 반환"""
        return {
            'total_return': 0.0,
            'annual_return': 0.0,
            'annual_volatility': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'win_rate': 0.0,
            'sortino_ratio': 0.0,
            'calmar_ratio': 0.0,
            'var_95': 0.0,
            'profit_factor': 0.0
        }
    
    def calculate_benchmark_comparison(self, portfolio_returns: pd.Series, 
                                     benchmark_returns: pd.Series) -> Dict[str, float]:
        """벤치마크 대비 성과 비교"""
        try:
            if portfolio_returns.empty or benchmark_returns.empty:
                return {}
            
            # 공통 날짜만 사용
            common_dates = portfolio_returns.index.intersection(benchmark_returns.index)
            if len(common_dates) == 0:
                return {}
            
            port_ret = portfolio_returns.loc[common_dates]
            bench_ret = benchmark_returns.loc[common_dates]
            
            # 누적 수익률
            port_cum_ret = (1 + port_ret).cumprod().iloc[-1] - 1
            bench_cum_ret = (1 + bench_ret).cumprod().iloc[-1] - 1
            
            # 초과 수익률
            excess_return = port_cum_ret - bench_cum_ret
            
            # 베타 계산
            covariance = np.cov(port_ret, bench_ret)[0, 1]
            benchmark_variance = bench_ret.var()
            beta = covariance / benchmark_variance if benchmark_variance != 0 else 0
            
            # 알파 계산
            port_annual_ret = port_ret.mean() * 252
            bench_annual_ret = bench_ret.mean() * 252
            alpha = port_annual_ret - (self.risk_free_rate + beta * (bench_annual_ret - self.risk_free_rate))
            
            # 추적 오차
            excess_daily_returns = port_ret - bench_ret
            tracking_error = excess_daily_returns.std() * np.sqrt(252)
            
            # 정보 비율
            information_ratio = excess_daily_returns.mean() / excess_daily_returns.std() * np.sqrt(252) if excess_daily_returns.std() != 0 else 0
            
            return {
                'portfolio_total_return': port_cum_ret,
                'benchmark_total_return': bench_cum_ret,
                'excess_return': excess_return,
                'beta': beta,
                'alpha': alpha,
                'tracking_error': tracking_error,
                'information_ratio': information_ratio
            }
            
        except Exception as e:
            logger.error(f"Error calculating benchmark comparison: {e}")
            return {}
    
    def format_metrics_for_display(self, metrics: Dict[str, Any]) -> Dict[str, str]:
        """지표를 표시용으로 포맷팅"""
        formatted = {}
        
        percentage_fields = [
            'total_return', 'annual_return', 'annual_volatility', 'max_drawdown',
            'win_rate', 'var_95', 'best_day_return', 'worst_day_return',
            'excess_return', 'alpha', 'tracking_error'
        ]
        
        ratio_fields = [
            'sharpe_ratio', 'sortino_ratio', 'calmar_ratio', 'information_ratio',
            'beta', 'profit_factor'
        ]
        
        for key, value in metrics.items():
            if key in percentage_fields:
                formatted[key] = f"{value:.2%}"
            elif key in ratio_fields:
                formatted[key] = f"{value:.2f}"
            elif isinstance(value, (int, float)):
                formatted[key] = f"{value:.2f}"
            else:
                formatted[key] = str(value)
        
        return formatted