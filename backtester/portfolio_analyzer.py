"""
File: backtester/portfolio_analyzer.py
Portfolio Performance Analysis Module
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime, timedelta

class PortfolioAnalyzer:
    """Analyze portfolio performance and calculate metrics"""
    
    def __init__(self):
        self.risk_free_rate = 0.02  # 2% annual risk-free rate
    
    def calculate_metrics(self, portfolio_value: List, symbol: str, days: int) -> Dict:
        """Calculate comprehensive performance metrics"""
        portfolio_series = pd.Series(portfolio_value)
        
        # Basic return calculations
        total_return = (portfolio_series.iloc[-1] / portfolio_series.iloc[0] - 1) * 100
        annual_return = ((portfolio_series.iloc[-1] / portfolio_series.iloc[0]) ** (365 / days) - 1) * 100
        
        # Calculate daily returns
        daily_returns = portfolio_series.pct_change().dropna()
        
        # Risk metrics
        volatility = daily_returns.std() * np.sqrt(252) * 100
        sharpe_ratio = self._calculate_sharpe_ratio(daily_returns, annual_return)
        sortino_ratio = self._calculate_sortino_ratio(daily_returns, annual_return)
        
        # Drawdown analysis
        max_drawdown = self._calculate_max_drawdown(portfolio_series)
        
        # Additional metrics
        win_rate = (daily_returns > 0).mean() * 100
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown < 0 else 0
        
        # Monthly returns
        monthly_returns = self._calculate_monthly_returns(portfolio_series, days)
        
        return {
            'Symbol': symbol,
            'Total_Return_%': round(total_return, 2),
            'Annual_Return_%': round(annual_return, 2),
            'Volatility_%': round(volatility, 2),
            'Sharpe_Ratio': round(sharpe_ratio, 2),
            'Sortino_Ratio': round(sortino_ratio, 2),
            'Calmar_Ratio': round(calmar_ratio, 2),
            'Max_Drawdown_%': round(abs(max_drawdown), 2),
            'Win_Rate_%': round(win_rate, 2),
            'Final_Value': round(portfolio_series.iloc[-1], 2),
            'Monthly_Returns': monthly_returns,
            'Best_Month_%': round(max(monthly_returns) if monthly_returns else 0, 2),
            'Worst_Month_%': round(min(monthly_returns) if monthly_returns else 0, 2)
        }
    
    def _calculate_sharpe_ratio(self, daily_returns: pd.Series, annual_return: float) -> float:
        """Calculate Sharpe ratio"""
        if daily_returns.std() == 0:
            return 0
        
        excess_return = annual_return - self.risk_free_rate * 100
        volatility = daily_returns.std() * np.sqrt(252) * 100
        
        return excess_return / volatility if volatility > 0 else 0
    
    def _calculate_sortino_ratio(self, daily_returns: pd.Series, annual_return: float) -> float:
        """Calculate Sortino ratio"""
        downside_returns = daily_returns[daily_returns < 0]
        
        if len(downside_returns) == 0:
            return 0
        
        downside_std = downside_returns.std() * np.sqrt(252) * 100
        excess_return = annual_return - self.risk_free_rate * 100
        
        return excess_return / downside_std if downside_std > 0 else 0
    
    def _calculate_max_drawdown(self, portfolio_series: pd.Series) -> float:
        """Calculate maximum drawdown"""
        cumulative = portfolio_series.copy()
        rolling_max = cumulative.expanding().max()
        drawdown = ((cumulative - rolling_max) / rolling_max * 100)
        
        return drawdown.min()
    
    def _calculate_monthly_returns(self, portfolio_series: pd.Series, days: int) -> List[float]:
        """Calculate monthly returns"""
        if len(portfolio_series) < 30:
            return []
        
        monthly_returns = []
        days_per_month = max(1, len(portfolio_series) // (days // 30))
        
        for i in range(0, len(portfolio_series) - days_per_month, days_per_month):
            start_val = portfolio_series.iloc[i]
            end_val = portfolio_series.iloc[min(i + days_per_month, len(portfolio_series) - 1)]
            monthly_ret = (end_val / start_val - 1) * 100
            monthly_returns.append(monthly_ret)
        
        return monthly_returns
    
    def calculate_portfolio_metrics(self, individual_results: List[Dict], weights: Dict = None) -> Dict:
        """Calculate metrics for a portfolio of stocks"""
        if not individual_results:
            return {}
        
        # Default equal weights if not provided
        if weights is None:
            weights = {result['Symbol']: 1.0 / len(individual_results) 
                      for result in individual_results}
        
        # Calculate weighted portfolio performance
        portfolio_values = []
        dates = None
        
        for result in individual_results:
            symbol = result['Symbol']
            weight = weights.get(symbol, 0)
            
            if 'Portfolio_History' in result and weight > 0:
                history = np.array(result['Portfolio_History'])
                weighted_history = history * weight
                portfolio_values.append(weighted_history)
        
        if not portfolio_values:
            return {}
        
        # Sum weighted portfolio values
        total_portfolio_value = np.sum(portfolio_values, axis=0)
        
        # Calculate portfolio metrics
        portfolio_series = pd.Series(total_portfolio_value)
        days = len(portfolio_series)
        
        metrics = self.calculate_metrics(total_portfolio_value.tolist(), 'PORTFOLIO', days)
        
        # Add portfolio-specific information
        metrics.update({
            'Weights': weights,
            'Components': list(weights.keys()),
            'Portfolio_History': total_portfolio_value.tolist()
        })
        
        return metrics
    
    def calculate_risk_metrics(self, portfolio_value: List) -> Dict:
        """Calculate advanced risk metrics"""
        portfolio_series = pd.Series(portfolio_value)
        daily_returns = portfolio_series.pct_change().dropna()
        
        if len(daily_returns) == 0:
            return {}
        
        # Value at Risk (VaR)
        var_95 = np.percentile(daily_returns, 5) * 100
        var_99 = np.percentile(daily_returns, 1) * 100
        
        # Conditional Value at Risk (CVaR)
        cvar_95 = daily_returns[daily_returns <= np.percentile(daily_returns, 5)].mean() * 100
        cvar_99 = daily_returns[daily_returns <= np.percentile(daily_returns, 1)].mean() * 100
        
        # Maximum consecutive losses
        consecutive_losses = self._calculate_consecutive_losses(daily_returns)
        
        # Beta (assuming market return is 8% annually with 15% volatility)
        market_returns = np.random.normal(0.0003, 0.015, len(daily_returns))  # Simplified market proxy
        beta = np.cov(daily_returns, market_returns)[0, 1] / np.var(market_returns)
        
        # Skewness and Kurtosis
        skewness = daily_returns.skew()
        kurtosis = daily_returns.kurtosis()
        
        return {
            'VaR_95%': round(var_95, 2),
            'VaR_99%': round(var_99, 2),
            'CVaR_95%': round(cvar_95, 2),
            'CVaR_99%': round(cvar_99, 2),
            'Max_Consecutive_Losses': consecutive_losses,
            'Beta': round(beta, 2),
            'Skewness': round(skewness, 2),
            'Kurtosis': round(kurtosis, 2)
        }
    
    def _calculate_consecutive_losses(self, daily_returns: pd.Series) -> int:
        """Calculate maximum consecutive losing days"""
        losing_days = (daily_returns < 0).astype(int)
        
        max_consecutive = 0
        current_consecutive = 0
        
        for loss in losing_days:
            if loss == 1:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0
        
        return max_consecutive
    
    def calculate_rolling_metrics(self, portfolio_value: List, window_days: int = 252) -> Dict:
        """Calculate rolling performance metrics"""
        portfolio_series = pd.Series(portfolio_value)
        
        if len(portfolio_series) < window_days:
            return {}
        
        rolling_returns = []
        rolling_volatilities = []
        rolling_sharpes = []
        
        for i in range(window_days, len(portfolio_series)):
            window_data = portfolio_series.iloc[i-window_days:i]
            window_returns = window_data.pct_change().dropna()
            
            if len(window_returns) > 0:
                # Annual return for this window
                annual_ret = ((window_data.iloc[-1] / window_data.iloc[0]) ** (252 / window_days) - 1) * 100
                
                # Volatility
                vol = window_returns.std() * np.sqrt(252) * 100
                
                # Sharpe ratio
                sharpe = (annual_ret - self.risk_free_rate * 100) / vol if vol > 0 else 0
                
                rolling_returns.append(annual_ret)
                rolling_volatilities.append(vol)
                rolling_sharpes.append(sharpe)
        
        return {
            'Rolling_Returns': rolling_returns,
            'Rolling_Volatilities': rolling_volatilities,
            'Rolling_Sharpes': rolling_sharpes,
            'Avg_Rolling_Sharpe': np.mean(rolling_sharpes) if rolling_sharpes else 0,
            'Sharpe_Stability': np.std(rolling_sharpes) if rolling_sharpes else 0
        }
    
    def compare_to_benchmark(self, portfolio_value: List, benchmark_return: float = 0.10) -> Dict:
        """Compare portfolio performance to benchmark"""
        portfolio_series = pd.Series(portfolio_value)
        days = len(portfolio_series)
        
        # Portfolio metrics
        portfolio_annual_return = ((portfolio_series.iloc[-1] / portfolio_series.iloc[0]) ** (365 / days) - 1)
        
        # Benchmark comparison
        alpha = portfolio_annual_return - benchmark_return
        
        # Tracking error (simplified)
        daily_returns = portfolio_series.pct_change().dropna()
        benchmark_daily = (1 + benchmark_return) ** (1/252) - 1
        tracking_error = (daily_returns - benchmark_daily).std() * np.sqrt(252)
        
        # Information ratio
        information_ratio = alpha / tracking_error if tracking_error > 0 else 0
        
        return {
            'Portfolio_Annual_Return': round(portfolio_annual_return * 100, 2),
            'Benchmark_Return': round(benchmark_return * 100, 2),
            'Alpha': round(alpha * 100, 2),
            'Tracking_Error': round(tracking_error * 100, 2),
            'Information_Ratio': round(information_ratio, 2),
            'Outperformance_Days': (daily_returns > benchmark_daily).sum(),
            'Total_Days': len(daily_returns)
        }
    
    def generate_performance_summary(self, results: List[Dict]) -> Dict:
        """Generate comprehensive performance summary"""
        if not results:
            return {}
        
        # Extract key metrics
        annual_returns = [r['Annual_Return_%'] for r in results]
        sharpe_ratios = [r['Sharpe_Ratio'] for r in results]
        max_drawdowns = [r['Max_Drawdown_%'] for r in results]
        win_rates = [r['Win_Rate_%'] for r in results]
        
        summary = {
            'Total_Strategies_Analyzed': len(results),
            'Best_Annual_Return': max(annual_returns),
            'Worst_Annual_Return': min(annual_returns),
            'Average_Annual_Return': np.mean(annual_returns),
            'Median_Annual_Return': np.median(annual_returns),
            'Best_Sharpe_Ratio': max(sharpe_ratios),
            'Average_Sharpe_Ratio': np.mean(sharpe_ratios),
            'Lowest_Max_Drawdown': min(max_drawdowns),
            'Average_Max_Drawdown': np.mean(max_drawdowns),
            'Highest_Win_Rate': max(win_rates),
            'Average_Win_Rate': np.mean(win_rates),
            'Strategies_With_Positive_Returns': sum(1 for r in annual_returns if r > 0),
            'Strategies_With_Sharpe_Above_1': sum(1 for s in sharpe_ratios if s > 1.0)
        }
        
        return summary