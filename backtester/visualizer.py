"""
File: backtester/visualizer.py
Portfolio Visualization Module
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
from typing import Dict, List
import os

class PortfolioVisualizer:
    """Create visualizations for portfolio performance"""
    
    def __init__(self):
        # Set style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # Korean font setting for matplotlib
        plt.rcParams['font.family'] = 'DejaVu Sans'
        plt.rcParams['axes.unicode_minus'] = False
        
        # Create output directory
        self.output_dir = 'charts'
        os.makedirs(self.output_dir, exist_ok=True)
    
    def create_performance_dashboard(self, chart_data: Dict):
        """Create comprehensive performance dashboard"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(f"Portfolio Performance Dashboard - {chart_data['strategy_name']}", 
                    fontsize=16, fontweight='bold')
        
        # Portfolio value over time
        self._plot_portfolio_value(axes[0, 0], chart_data)
        
        # Rolling returns
        self._plot_rolling_returns(axes[0, 1], chart_data)
        
        # Drawdown analysis
        self._plot_drawdown(axes[1, 0], chart_data)
        
        # Performance metrics
        self._plot_metrics_summary(axes[1, 1], chart_data)
        
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/performance_dashboard.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        # Generate HTML dashboard
        self._generate_html_dashboard(chart_data)
    
    def _plot_rolling_returns(self, ax, chart_data):
        """Plot rolling returns"""
        portfolio_history = chart_data['portfolio_history']
        returns = pd.Series(portfolio_history).pct_change().dropna()
        
        # Calculate 30-day rolling returns
        rolling_returns = returns.rolling(window=30).sum() * 100
        
        dates = pd.date_range(start='2015-01-01', periods=len(rolling_returns), freq='D')
        
        ax.plot(dates, rolling_returns, linewidth=1.5, color='green', alpha=0.7)
        ax.axhline(y=0, color='red', linestyle='--', alpha=0.5)
        ax.set_title('30-Day Rolling Returns (%)', fontweight='bold')
        ax.set_ylabel('Returns (%)')
        ax.grid(True, alpha=0.3)
        
        # Add statistics
        mean_return = rolling_returns.mean()
        ax.annotate(f'Avg 30d Return: {mean_return:.2f}%', 
                   xy=(0.05, 0.95), xycoords='axes fraction',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen"))
    
    def _plot_drawdown(self, ax, chart_data):
        """Plot drawdown analysis"""
        portfolio_history = chart_data['portfolio_history']
        portfolio_series = pd.Series(portfolio_history)
        
        # Calculate drawdown
        rolling_max = portfolio_series.expanding().max()
        drawdown = ((portfolio_series - rolling_max) / rolling_max * 100)
        
        dates = pd.date_range(start='2015-01-01', periods=len(drawdown), freq='D')
        
        ax.fill_between(dates, drawdown, 0, color='red', alpha=0.3)
        ax.plot(dates, drawdown, linewidth=1, color='red')
        ax.set_title('Drawdown Analysis', fontweight='bold')
        ax.set_ylabel('Drawdown (%)')
        ax.grid(True, alpha=0.3)
        
        # Add max drawdown
        max_dd = drawdown.min()
        ax.annotate(f'Max Drawdown: {max_dd:.1f}%', 
                   xy=(0.05, 0.05), xycoords='axes fraction',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="pink"))
    
    def _plot_metrics_summary(self, ax, chart_data):
        """Plot key performance metrics"""
        metrics = {
            'Total Return (%)': chart_data['total_return'],
            'Sharpe Ratio': chart_data['sharpe_ratio'],
            'Max Drawdown (%)': chart_data['max_drawdown']
        }
        
        colors = ['skyblue', 'lightgreen', 'salmon']
        bars = ax.bar(metrics.keys(), metrics.values(), color=colors, alpha=0.7)
        
        ax.set_title('Key Performance Metrics', fontweight='bold')
        ax.set_ylabel('Value')
        
        # Add value labels on bars
        for bar, value in zip(bars, metrics.values()):
            height = bar.get_height()
            ax.annotate(f'{value:.2f}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3),  # 3 points vertical offset
                       textcoords="offset points",
                       ha='center', va='bottom', fontweight='bold')
        
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    
    def _generate_html_dashboard(self, chart_data):
        """Generate HTML dashboard"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Portfolio Dashboard - {chart_data['strategy_name']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
        .header {{ text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                  color: white; padding: 20px; border-radius: 10px; margin-bottom: 30px; }}
        .metrics-container {{ display: flex; justify-content: space-around; margin: 30px 0; }}
        .metric-box {{ background: white; padding: 20px; border-radius: 10px; text-align: center; 
                      box-shadow: 0 4px 6px rgba(0,0,0,0.1); min-width: 150px; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
        .metric-label {{ color: #7f8c8d; margin-top: 5px; }}
        .chart-container {{ text-align: center; margin: 30px 0; }}
        .footer {{ text-align: center; color: #7f8c8d; margin-top: 40px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Portfolio Performance Dashboard</h1>
        <h2>{chart_data['strategy_name']} - {chart_data['period_name']}</h2>
    </div>
    
    <div class="metrics-container">
        <div class="metric-box">
            <div class="metric-value">{chart_data['total_return']:.1f}%</div>
            <div class="metric-label">Total Return</div>
        </div>
        <div class="metric-box">
            <div class="metric-value">{chart_data['sharpe_ratio']:.2f}</div>
            <div class="metric-label">Sharpe Ratio</div>
        </div>
        <div class="metric-box">
            <div class="metric-value">{chart_data['max_drawdown']:.1f}%</div>
            <div class="metric-label">Max Drawdown</div>
        </div>
    </div>
    
    <div class="chart-container">
        <h3>📈 Performance Charts</h3>
        <img src="performance_dashboard.png" alt="Performance Dashboard" style="max-width: 100%; border-radius: 10px;">
    </div>
    
    <div class="footer">
        <p>Generated by Quantitative Strategy Backtester 2.0</p>
        <p>⚠️ Past performance does not guarantee future results</p>
    </div>
</body>
</html>
        """
        
        with open(f"{self.output_dir}/portfolio_dashboard.html", 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def create_monte_carlo_simulation(self, chart_data: Dict, num_simulations: int = 1000):
        """Create Monte Carlo simulation visualization"""
        portfolio_history = chart_data['portfolio_history']
        returns = pd.Series(portfolio_history).pct_change().dropna()
        
        # Simulation parameters
        mean_return = returns.mean()
        std_return = returns.std()
        days = len(portfolio_history)
        
        # Run simulations
        simulations = []
        for i in range(num_simulations):
            sim_returns = np.random.normal(mean_return, std_return, days)
            sim_prices = [100]  # Starting value
            
            for ret in sim_returns:
                sim_prices.append(sim_prices[-1] * (1 + ret))
            
            simulations.append(sim_prices)
        
        # Plot results
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Simulation paths
        dates = pd.date_range(start='2015-01-01', periods=days+1, freq='D')
        for sim in simulations[:100]:  # Plot first 100 simulations
            ax1.plot(dates, sim, alpha=0.1, color='gray')
        
        # Plot actual performance
        actual_normalized = [100 * (x / portfolio_history[0]) for x in portfolio_history]
        ax1.plot(dates[:-1], actual_normalized, color='red', linewidth=3, label='Actual Performance')
        
        ax1.set_title('Monte Carlo Simulation (1000 paths)', fontweight='bold')
        ax1.set_ylabel('Portfolio Value (Normalized)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Final value distribution
        final_values = [sim[-1] for sim in simulations]
        ax2.hist(final_values, bins=50, alpha=0.7, color='skyblue', edgecolor='black')
        ax2.axvline(actual_normalized[-1], color='red', linestyle='--', linewidth=2, label='Actual Final Value')
        ax2.set_title('Distribution of Final Portfolio Values', fontweight='bold')
        ax2.set_xlabel('Final Value')
        ax2.set_ylabel('Frequency')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/monte_carlo_analysis.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_drawdown_analysis(self, chart_data: Dict):
        """Create detailed drawdown analysis"""
        portfolio_history = chart_data['portfolio_history']
        portfolio_series = pd.Series(portfolio_history)
        
        # Calculate drawdown
        rolling_max = portfolio_series.expanding().max()
        drawdown = ((portfolio_series - rolling_max) / rolling_max * 100)
        
        # Find drawdown periods
        drawdown_periods = []
        in_drawdown = False
        start_idx = 0
        
        for i, dd in enumerate(drawdown):
            if dd < -1 and not in_drawdown:  # Start of drawdown (>1%)
                in_drawdown = True
                start_idx = i
            elif dd >= -0.5 and in_drawdown:  # End of drawdown
                in_drawdown = False
                if i - start_idx > 5:  # Minimum 5 days
                    drawdown_periods.append({
                        'start': start_idx,
                        'end': i,
                        'duration': i - start_idx,
                        'max_dd': drawdown[start_idx:i].min()
                    })
        
        # Create visualization
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
        
        dates = pd.date_range(start='2015-01-01', periods=len(drawdown), freq='D')
        
        # Drawdown over time
        ax1.fill_between(dates, drawdown, 0, color='red', alpha=0.3)
        ax1.plot(dates, drawdown, color='red', linewidth=1)
        ax1.set_title('Drawdown Over Time', fontweight='bold')
        ax1.set_ylabel('Drawdown (%)')
        ax1.grid(True, alpha=0.3)
        
        # Highlight major drawdown periods
        for period in drawdown_periods[:5]:  # Top 5 drawdowns
            start_date = dates[period['start']]
            end_date = dates[period['end']]
            ax1.axvspan(start_date, end_date, alpha=0.2, color='orange')
        
        # Drawdown duration vs magnitude
        if drawdown_periods:
            durations = [p['duration'] for p in drawdown_periods]
            magnitudes = [abs(p['max_dd']) for p in drawdown_periods]
            
            scatter = ax2.scatter(durations, magnitudes, alpha=0.6, s=60, c=magnitudes, cmap='Reds')
            ax2.set_title('Drawdown Duration vs Magnitude', fontweight='bold')
            ax2.set_xlabel('Duration (Days)')
            ax2.set_ylabel('Max Drawdown (%)')
            ax2.grid(True, alpha=0.3)
            
            # Add colorbar
            plt.colorbar(scatter, ax=ax2, label='Drawdown Magnitude (%)')
        
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/drawdown_analysis.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_rolling_performance(self, chart_data: Dict):
        """Create rolling performance analysis"""
        portfolio_history = chart_data['portfolio_history']
        returns = pd.Series(portfolio_history).pct_change().dropna()
        
        # Calculate rolling metrics
        windows = [30, 90, 252]  # 1 month, 3 months, 1 year
        
        fig, axes = plt.subplots(len(windows), 1, figsize=(15, 4*len(windows)))
        dates = pd.date_range(start='2015-01-01', periods=len(returns), freq='D')
        
        for i, window in enumerate(windows):
            if len(returns) > window:
                rolling_return = returns.rolling(window=window).sum() * 100
                rolling_vol = returns.rolling(window=window).std() * np.sqrt(252) * 100
                rolling_sharpe = rolling_return / (rolling_vol / np.sqrt(252/window))
                
                ax = axes[i] if len(windows) > 1 else axes
                
                # Plot rolling Sharpe ratio
                ax.plot(dates[window:], rolling_sharpe[window:], linewidth=2, label=f'{window}-Day Sharpe')
                ax.axhline(y=1.0, color='red', linestyle='--', alpha=0.5, label='Sharpe = 1.0')
                ax.set_title(f'{window}-Day Rolling Sharpe Ratio', fontweight='bold')
                ax.set_ylabel('Sharpe Ratio')
                ax.legend()
                ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/rolling_performance.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_comparison_chart(self, comparison_results: List[Dict]):
        """Create strategy comparison visualization"""
        if not comparison_results:
            return
        
        # Prepare data
        strategies = [r['Strategy'] for r in comparison_results]
        annual_returns = [r['Annual_Return_%'] for r in comparison_results]
        sharpe_ratios = [r['Sharpe_Ratio'] for r in comparison_results]
        max_drawdowns = [r['Max_Drawdown_%'] for r in comparison_results]
        
        # Create comparison plots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Annual Returns
        bars1 = ax1.bar(range(len(strategies)), annual_returns, color='skyblue', alpha=0.7)
        ax1.set_title('Annual Returns Comparison (%)', fontweight='bold')
        ax1.set_ylabel('Annual Return (%)')
        ax1.set_xticks(range(len(strategies)))
        ax1.set_xticklabels(strategies, rotation=45, ha='right')
        ax1.grid(True, alpha=0.3)
        
        # Add value labels
        for bar, value in zip(bars1, annual_returns):
            height = bar.get_height()
            ax1.annotate(f'{value:.1f}%',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', fontsize=8)
        
        # Sharpe Ratios
        bars2 = ax2.bar(range(len(strategies)), sharpe_ratios, color='lightgreen', alpha=0.7)
        ax2.set_title('Sharpe Ratio Comparison', fontweight='bold')
        ax2.set_ylabel('Sharpe Ratio')
        ax2.set_xticks(range(len(strategies)))
        ax2.set_xticklabels(strategies, rotation=45, ha='right')
        ax2.axhline(y=1.0, color='red', linestyle='--', alpha=0.5)
        ax2.grid(True, alpha=0.3)
        
        # Risk-Return Scatter
        ax3.scatter(max_drawdowns, annual_returns, s=100, alpha=0.7, c=sharpe_ratios, cmap='viridis')
        ax3.set_xlabel('Max Drawdown (%)')
        ax3.set_ylabel('Annual Return (%)')
        ax3.set_title('Risk-Return Profile', fontweight='bold')
        ax3.grid(True, alpha=0.3)
        
        # Add labels for each point
        for i, strategy in enumerate(strategies):
            ax3.annotate(strategy[:10], (max_drawdowns[i], annual_returns[i]), 
                        xytext=(5, 5), textcoords='offset points', fontsize=8)
        
        # Performance Ranking
        ranking_data = sorted(zip(strategies, sharpe_ratios), key=lambda x: x[1], reverse=True)
        ranked_strategies, ranked_sharpes = zip(*ranking_data)
        
        bars4 = ax4.barh(range(len(ranked_strategies)), ranked_sharpes, color='coral', alpha=0.7)
        ax4.set_title('Strategy Ranking (by Sharpe Ratio)', fontweight='bold')
        ax4.set_xlabel('Sharpe Ratio')
        ax4.set_yticks(range(len(ranked_strategies)))
        ax4.set_yticklabels(ranked_strategies)
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/strategy_comparison.png", dpi=300, bbox_inches='tight')
        plt.close()
        print(f"📊 전략 비교 차트가 생성되었습니다: {self.output_dir}/strategy_comparison.png")
        


# """
# File: backtester/visualizer.py
# Portfolio Performance Visualizer
# Advanced visualization module for quantitative trading strategy results
# """

# import matplotlib.pyplot as plt
# import matplotlib.dates as mdates
# import seaborn as sns
# import pandas as pd
# import numpy as np
# from datetime import datetime, timedelta
# import plotly.graph_objects as go
# from plotly.subplots import make_subplots
# import plotly.express as px
# from typing import Dict, List, Optional
# import warnings
# warnings.filterwarnings('ignore')

# # Set style for better visualizations
# plt.style.use('seaborn-v0_8-darkgrid')
# sns.set_palette("husl")

# class PortfolioVisualizer:
#     """Advanced portfolio performance visualization engine"""
    
#     def __init__(self):
#         self.colors = {
#             'primary': '#1f77b4',
#             'secondary': '#ff7f0e', 
#             'success': '#2ca02c',
#             'danger': '#d62728',
#             'warning': '#ff9800',
#             'info': '#17a2b8'
#         }
        
#         # Configure matplotlib for better plots
#         plt.rcParams['figure.figsize'] = (12, 8)
#         plt.rcParams['font.size'] = 10
#         plt.rcParams['axes.grid'] = True
#         plt.rcParams['grid.alpha'] = 0.3
    
#     @staticmethod
#     def rolling_volatility(prices, window=20, annualize=True):
#         """
#         이동 변동성(표준편차)을 계산
#         Parameters:
#             prices: pandas Series 또는 numpy array, 가격 데이터 (예: 종가)
#             window: int, 이동 창 크기 (기본값: 20일)
#             annualize: bool, 연간화 여부 (기본값: True)
#         Returns:
#             pandas Series, 이동 변동성
#         """
#         if not isinstance(prices, pd.Series):
#             prices = pd.Series(prices)
#         returns = np.log(prices / prices.shift(1)).dropna()
#         vol = returns.rolling(window=window).std()
#         if annualize:
#             vol = vol * np.sqrt(252)  # 252는 주식 시장의 평균 거래일
#         return vol

#     @staticmethod
#     def rolling_sharpe(portfolio_values, window=20, risk_free_rate=0.02):
#         """
#         이동 샤프 비율 계산
#         Parameters:
#             portfolio_values: pandas Series 또는 numpy array, 포트폴리오 가치
#             window: int, 이동 창 크기 (기본값: 20일)
#             risk_free_rate: float, 무위험 수익률 (기본값: 2%)
#         Returns:
#             pandas Series, 이동 샤프 비율
#         """
#         if not isinstance(portfolio_values, pd.Series):
#             portfolio_values = pd.Series(portfolio_values)
#         returns = portfolio_values.pct_change().dropna()
#         rolling_mean = returns.rolling(window=window).mean() * 252
#         rolling_std = returns.rolling(window=window).std() * np.sqrt(252)
#         sharpe = (rolling_mean - risk_free_rate) / (rolling_std + 1e-8)
#         return sharpe

#     def create_performance_dashboard(self, data: Dict):
#         """Create comprehensive performance dashboard"""
#         print("📊 Creating performance dashboard...")
        
#         # Create subplots
#         fig = make_subplots(
#             rows=2, cols=2,
#             subplot_titles=('Portfolio Value Over Time', 'Rolling Returns Distribution',
#                           'Drawdown Analysis', 'Risk-Return Profile'),
#             specs=[[{"secondary_y": True}, {"type": "histogram"}],
#                    [{"type": "scatter"}, {"type": "bar"}]]
#         )
        
#         # Prepare time series data
#         portfolio_history = data['portfolio_history']
#         dates = pd.date_range(
#             end=datetime.now(),
#             periods=len(portfolio_history),
#             freq='D'
#         )
        
#         # 1. Portfolio Value Over Time
#         self._add_portfolio_value_chart(fig, dates, portfolio_history, data)
        
#         # 2. Returns Distribution
#         self._add_returns_distribution(fig, portfolio_history)
        
#         # 3. Drawdown Analysis
#         self._add_drawdown_analysis(fig, dates, portfolio_history)
        
#         # 4. Risk-Return Profile
#         self._add_risk_return_profile(fig, data)
        
#         # Update layout
#         fig.update_layout(
#             title=f"Performance Dashboard - {data['strategy_name']} ({data['period_name']})",
#             showlegend=True,
#             height=800,
#             width=1200
#         )
        
#         # Save and display
#         fig.write_html("portfolio_dashboard.html")
#         print("💾 Dashboard saved as 'portfolio_dashboard.html'")
        
#         # Also create matplotlib version for quick viewing
#         self._create_matplotlib_summary(data)
    
#     def _add_portfolio_value_chart(self, fig, dates, portfolio_history, data):
#         """Add portfolio value over time chart"""
        
#         # Portfolio value line
#         fig.add_trace(
#             go.Scatter(
#                 x=dates,
#                 y=portfolio_history,
#                 mode='lines',
#                 name='Portfolio Value',
#                 line=dict(color=self.colors['primary'], width=2)
#             ),
#             row=1, col=1
#         )
        
#         # Benchmark (S&P 500 proxy)
#         benchmark = self._generate_benchmark(len(portfolio_history))
#         fig.add_trace(
#             go.Scatter(
#                 x=dates,
#                 y=benchmark,
#                 mode='lines',
#                 name='Benchmark (S&P 500)',
#                 line=dict(color=self.colors['secondary'], width=1, dash='dash')
#             ),
#             row=1, col=1
#         )
        
#         fig.update_xaxes(title_text="Date", row=1, col=1)
#         fig.update_yaxes(title_text="Portfolio Value ($)", row=1, col=1)
    
#     def _add_returns_distribution(self, fig, portfolio_history):
#         """Add returns distribution histogram"""
#         returns = pd.Series(portfolio_history).pct_change().dropna() * 100
        
#         fig.add_trace(
#             go.Histogram(
#                 x=returns,
#                 nbinsx=30,
#                 name='Daily Returns (%)',
#                 marker_color=self.colors['success'],
#                 opacity=0.7
#             ),
#             row=1, col=2
#         )
        
#         fig.update_xaxes(title_text="Daily Returns (%)", row=1, col=2)
#         fig.update_yaxes(title_text="Frequency", row=1, col=2)
    
#     def _add_drawdown_analysis(self, fig, dates, portfolio_history):
#         """Add drawdown analysis chart"""
#         cumulative = pd.Series(portfolio_history)
#         rolling_max = cumulative.expanding().max()
#         drawdown = (cumulative - rolling_max) / rolling_max * 100
        
#         fig.add_trace(
#             go.Scatter(
#                 x=dates,
#                 y=drawdown,
#                 mode='lines',
#                 fill='tonexty',
#                 name='Drawdown (%)',
#                 line=dict(color=self.colors['danger']),
#                 fillcolor='rgba(214, 39, 40, 0.3)'
#             ),
#             row=2, col=1
#         )
        
#         fig.update_xaxes(title_text="Date", row=2, col=1)
#         fig.update_yaxes(title_text="Drawdown (%)", row=2, col=1)
    
#     def _add_risk_return_profile(self, fig, data):
#         """Add risk-return scatter plot"""
        
#         # Calculate metrics for comparison
#         strategies = ['Current Strategy', 'Low Risk', 'Medium Risk', 'High Risk']
#         returns = [data['total_return'], 8, 12, 18]
#         risks = [data.get('volatility', 15), 8, 15, 25]
#         sharpes = [data.get('sharpe_ratio', 1), 1.0, 0.8, 0.7]
        
#         colors = [self.colors['primary'], self.colors['success'], 
#                  self.colors['warning'], self.colors['danger']]
        
#         for i, (strategy, ret, risk, sharpe) in enumerate(zip(strategies, returns, risks, sharpes)):
#             fig.add_trace(
#                 go.Scatter(
#                     x=[risk],
#                     y=[ret],
#                     mode='markers',
#                     name=strategy,
#                     marker=dict(
#                         size=15 if i == 0 else 10,
#                         color=colors[i],
#                         symbol='star' if i == 0 else 'circle'
#                     ),
#                     text=f"Sharpe: {sharpe:.2f}",
#                     textposition="top center"
#                 ),
#                 row=2, col=2
#             )
        
#         fig.update_xaxes(title_text="Risk (Volatility %)", row=2, col=2)
#         fig.update_yaxes(title_text="Return (%)", row=2, col=2)
    
#     def _generate_benchmark(self, length: int) -> List[float]:
#         """Generate S&P 500 benchmark data"""
#         daily_return = 0.0004  # ~10% annual
#         volatility = 0.015     # ~15% annual volatility
        
#         returns = np.random.normal(daily_return, volatility, length)
#         values = [100000]  # Start with same initial value
        
#         for ret in returns:
#             values.append(values[-1] * (1 + ret))
        
#         return values[:length]
    
#     def _create_matplotlib_summary(self, data: Dict):
#         """Create matplotlib summary charts"""
        
#         fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
#         fig.suptitle(f'Strategy Performance Summary - {data["strategy_name"]}', 
#                      fontsize=16, fontweight='bold')
        
#         portfolio_history = data['portfolio_history']
#         dates = pd.date_range(end=datetime.now(), periods=len(portfolio_history), freq='D')
        
#         # 1. Portfolio Value
#         ax1.plot(dates, portfolio_history, linewidth=2, color=self.colors['primary'], label='Portfolio')
#         benchmark = self._generate_benchmark(len(portfolio_history))
#         ax1.plot(dates, benchmark, '--', linewidth=1, color=self.colors['secondary'], label='S&P 500')
#         ax1.set_title('Portfolio Value Over Time')
#         ax1.set_ylabel('Value ($)')
#         ax1.legend()
#         ax1.grid(True, alpha=0.3)
#         ax1.axhline(y=0, color='red', linestyle='--', alpha=0.7)
        
#         # Rolling volatility
#         window = 20
#         rolling_vol = self.rolling_volatility(portfolio_history, window=window)
#         ax2.plot(dates[-len(rolling_vol):], rolling_vol * 100, color=self.colors['warning'], linewidth=2)
#         ax2.set_title(f'Rolling {window}-Day Volatility')
#         ax2.set_ylabel('Volatility (%)')
#         ax2.grid(True, alpha=0.3)
        
#         # Rolling Sharpe ratio
#         rolling_sharpe_values = self.rolling_sharpe(portfolio_history, window=window)
#         ax3.plot(dates[-len(rolling_sharpe_values):], rolling_sharpe_values, color=self.colors['success'], linewidth=2)
#         ax3.set_title(f'Rolling {window}-Day Sharpe Ratio')
#         ax3.set_ylabel('Sharpe Ratio')
#         ax3.set_xlabel('Date')
#         ax3.grid(True, alpha=0.3)
#         ax3.axhline(y=1, color='red', linestyle='--', alpha=0.7, label='Sharpe = 1.0')
#         ax3.legend()
        
#         # Risk metrics
#         returns = pd.Series(portfolio_history).pct_change().dropna() * 100
#         ax4.hist(returns, bins=30, alpha=0.7, color=self.colors['info'], edgecolor='black')
#         ax4.set_title('Returns Distribution')
#         ax4.set_xlabel('Daily Returns (%)')
#         ax4.set_ylabel('Frequency')
#         ax4.grid(True, alpha=0.3)
        
#         plt.tight_layout()
#         plt.savefig('rolling_performance.png', dpi=300, bbox_inches='tight')
#         print("💾 Rolling performance chart saved as 'rolling_performance.png'")
#         plt.show()

#     def create_monte_carlo_simulation(self, data: Dict, num_simulations: int = 1000):
#         """Create Monte Carlo simulation for future performance"""
        
#         portfolio_history = data['portfolio_history']
#         returns = pd.Series(portfolio_history).pct_change().dropna()
        
#         if len(returns) < 30:
#             print("❌ Insufficient data for Monte Carlo simulation")
#             return
        
#         # Calculate return statistics
#         mean_return = returns.mean()
#         std_return = returns.std()
        
#         # Simulation parameters
#         days_ahead = 252  # 1 year ahead
#         final_values = []
        
#         print(f"🎲 Running {num_simulations} Monte Carlo simulations...")
        
#         # Run simulations
#         for _ in range(num_simulations):
#             # Generate random returns
#             sim_returns = np.random.normal(mean_return, std_return, days_ahead)
            
#             # Calculate final portfolio value
#             sim_value = portfolio_history[-1]
#             for ret in sim_returns:
#                 sim_value *= (1 + ret)
            
#             final_values.append(sim_value)
        
#         # Analyze simulation results
#         final_values = np.array(final_values)
        
#         # Calculate percentiles
#         percentiles = [5, 25, 50, 75, 95]
#         percentile_values = np.percentile(final_values, percentiles)
        
#         # Create visualization
#         plt.figure(figsize=(14, 8))
        
#         # Histogram of outcomes
#         plt.subplot(2, 2, 1)
#         plt.hist(final_values, bins=50, alpha=0.7, color=self.colors['primary'], edgecolor='black')
#         plt.axvline(portfolio_history[-1], color='red', linestyle='--', linewidth=2, label='Current Value')
#         plt.axvline(np.mean(final_values), color='green', linestyle='--', linewidth=2, label='Expected Value')
#         plt.title('Monte Carlo Simulation Results')
#         plt.xlabel('Portfolio Value ($)')
#         plt.ylabel('Frequency')
#         plt.legend()
#         plt.grid(True, alpha=0.3)
        
#         # Percentile analysis
#         plt.subplot(2, 2, 2)
#         plt.bar(percentiles, percentile_values, alpha=0.7, color=self.colors['info'], edgecolor='black')
#         plt.title('Outcome Percentiles')
#         plt.xlabel('Percentile')
#         plt.ylabel('Portfolio Value ($)')
#         plt.grid(True, alpha=0.3)
        
#         # Returns distribution
#         returns_pct = (final_values / portfolio_history[-1] - 1) * 100
#         plt.subplot(2, 2, 3)
#         plt.hist(returns_pct, bins=50, alpha=0.7, color=self.colors['success'], edgecolor='black')
#         plt.axvline(0, color='red', linestyle='--', linewidth=2, label='Break-even')
#         plt.title('Projected Returns Distribution')
#         plt.xlabel('Return (%)')
#         plt.ylabel('Frequency')
#         plt.legend()
#         plt.grid(True, alpha=0.3)
        
#         # Risk metrics
#         plt.subplot(2, 2, 4)
#         prob_loss = (returns_pct < 0).mean() * 100
#         prob_gain_10 = (returns_pct > 10).mean() * 100
#         prob_gain_20 = (returns_pct > 20).mean() * 100
        
#         risk_metrics = ['Prob. Loss', 'Prob. >10%', 'Prob. >20%']
#         probabilities = [prob_loss, prob_gain_10, prob_gain_20]
#         colors_risk = [self.colors['danger'], self.colors['warning'], self.colors['success']]
        
#         bars = plt.bar(risk_metrics, probabilities, color=colors_risk, alpha=0.7, edgecolor='black')
#         plt.title('Probability Analysis')
#         plt.ylabel('Probability (%)')
#         plt.grid(True, alpha=0.3)
        
#         # Add value labels
#         for bar, prob in zip(bars, probabilities):
#             plt.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 1,
#                     f'{prob:.1f}%', ha='center', va='bottom', fontweight='bold')
        
#         plt.suptitle(f'Monte Carlo Analysis - {data["strategy_name"]} (1 Year Projection)', 
#                      fontsize=16, fontweight='bold')
#         plt.tight_layout()
#         plt.savefig('monte_carlo_analysis.png', dpi=300, bbox_inches='tight')
#         print("💾 Monte Carlo analysis saved as 'monte_carlo_analysis.png'")
#         plt.show()
        
#         # Print summary statistics
#         print(f"\n🎲 MONTE CARLO SIMULATION RESULTS")
#         print(f"Simulations: {num_simulations:,}")
#         print(f"Time Horizon: 1 Year")
#         print("-" * 50)
#         print(f"Expected Value: ${np.mean(final_values):,.0f}")
#         print(f"Current Value: ${portfolio_history[-1]:,.0f}")
#         print(f"Expected Return: {np.mean(returns_pct):.1f}%")
#         print(f"Volatility: {np.std(returns_pct):.1f}%")
#         print(f"Probability of Loss: {prob_loss:.1f}%")
#         print(f"95th Percentile: ${percentile_values[4]:,.0f}")
#         print(f"5th Percentile: ${percentile_values[0]:,.0f}")

#     def create_drawdown_analysis(self, data: Dict):
#         """Detailed drawdown analysis visualization"""
        
#         portfolio_history = data['portfolio_history']
#         portfolio_series = pd.Series(portfolio_history)
#         dates = pd.date_range(end=datetime.now(), periods=len(portfolio_history), freq='D')
        
#         # Calculate drawdowns
#         rolling_max = portfolio_series.expanding().max()
#         drawdown = (portfolio_series - rolling_max) / rolling_max * 100
        
#         # Find drawdown periods
#         drawdown_periods = []
#         in_drawdown = False
#         start_idx = None
        
#         for i, dd in enumerate(drawdown):
#             if dd < -1 and not in_drawdown:  # Start of drawdown
#                 in_drawdown = True
#                 start_idx = i
#             elif dd >= -0.5 and in_drawdown:  # End of drawdown
#                 if start_idx is not None:
#                     drawdown_periods.append({
#                         'start': start_idx,
#                         'end': i,
#                         'duration': i - start_idx,
#                         'magnitude': drawdown[start_idx:i+1].min()
#                     })
#                 in_drawdown = False
#                 start_idx = None
        
#         # Create visualization
#         fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        
#         # Portfolio value with drawdown periods highlighted
#         ax1.plot(dates, portfolio_history, linewidth=2, color=self.colors['primary'], label='Portfolio Value')
#         ax1.fill_between(dates, portfolio_history, rolling_max, where=(drawdown < -1), 
#                         color=self.colors['danger'], alpha=0.3, label='Drawdown Periods')
#         ax1.set_title('Portfolio Value with Drawdown Periods')
#         ax1.set_ylabel('Portfolio Value ($)')
#         ax1.legend()
#         ax1.grid(True, alpha=0.3)
#         ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
#         ax1.xaxis.set_major_locator(mdates.AutoDateLocator())
#         fig.autofmt_xdate()
        
#         # Drawdown magnitude
#         ax2.plot(dates, drawdown, linewidth=2, color=self.colors['danger'], label='Drawdown (%)')
#         ax2.fill_between(dates, drawdown, 0, where=(drawdown < 0), 
#                         color=self.colors['danger'], alpha=0.3)
#         ax2.set_title('Drawdown Analysis')
#         ax2.set_xlabel('Date')
#         ax2.set_ylabel('Drawdown (%)')
#         ax2.legend()
#         ax2.grid(True, alpha=0.3)
#         ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
#         ax2.xaxis.set_major_locator(mdates.AutoDateLocator())
        
#         # Calculate drawdown statistics
#         max_drawdown = drawdown.min()
#         avg_drawdown_duration = np.mean([period['duration'] for period in drawdown_periods]) if drawdown_periods else 0
#         num_drawdowns = len(drawdown_periods)
        
#         # Add summary text
#         summary_text = (
#             f"Max Drawdown: {max_drawdown:.2f}%\n"
#             f"Average Drawdown Duration: {avg_drawdown_duration:.1f} days\n"
#             f"Number of Drawdowns: {num_drawdowns}"
#         )
#         ax1.text(0.02, 0.98, summary_text, transform=ax1.transAxes, 
#                  fontsize=10, verticalalignment='top', 
#                  bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
#         plt.suptitle(f'Drawdown Analysis - {data["strategy_name"]}', fontsize=16, fontweight='bold')
#         plt.tight_layout()
#         plt.savefig('drawdown_analysis.png', dpi=300, bbox_inches='tight')
#         print("💾 Drawdown analysis saved as 'drawdown_analysis.png'")
#         plt.show()
        
#         # Print summary statistics
#         print(f"\n📉 DRAWDOWN ANALYSIS SUMMARY")
#         print(f"Strategy: {data['strategy_name']}")
#         print("-" * 50)
#         print(f"Maximum Drawdown: {max_drawdown:.2f}%")
#         print(f"Average Drawdown Duration: {avg_drawdown_duration:.1f} days")
#         print(f"Number of Drawdowns: {num_drawdowns}")
#         if drawdown_periods:
#             print("\nSignificant Drawdown Periods:")
#             for period in drawdown_periods:
#                 start_date = dates[period['start']].strftime('%Y-%m-%d')
#                 end_date = dates[period['end']].strftime('%Y-%m-%d')
#                 print(f" - From {start_date} to {end_date}: {period['magnitude']:.2f}% ({period['duration']} days)")

# # 테스트 코드
# if __name__ == "__main__":
#     # 더미 데이터 생성
#     data = {
#         'strategy_name': 'Test Strategy',
#         'period_name': '2020-2025',
#         'portfolio_history': np.random.random(100) * 100000 + 100000,  # 임의의 포트폴리오 가치
#         'total_return': 15.5,
#         'volatility': 12.3,
#         'sharpe_ratio': 1.2
#     }
    
#     visualizer = PortfolioVisualizer()
#     visualizer.create_performance_dashboard(data)
#     visualizer.create_drawdown_analysis(data)
#     visualizer.create_monte_carlo_simulation(data)