"""
File: backtester/backtesting_engine.py
Backtesting Engine for Strategy Execution
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from .portfolio_analyzer import PortfolioAnalyzer

class BacktestingEngine:
    """Engine for executing backtests on trading strategies"""
    
    def __init__(self):
        self.portfolio_analyzer = PortfolioAnalyzer()
    
    def run_multi_stock_backtest(self, strategy, stock_data: Dict, days: int) -> List[Dict]:
        """Run backtest on multiple stocks"""
        print("🔍 개별 종목 분석 중...")
        
        individual_results = self._run_individual_stock_analysis(strategy, stock_data, days)
        
        if not individual_results:
            print("❌ 분석할 수 있는 종목이 없습니다.")
            return []
        
        print(f"✅ {len(individual_results)}개 종목 분석 완료")
        return individual_results
    
    def _run_individual_stock_analysis(self, strategy, stock_data: Dict, days: int) -> List[Dict]:
        """Analyze individual stocks with the given strategy"""
        results = []
        total_stocks = len(stock_data)
        processed = 0
        
        for symbol, data in stock_data.items():
            try:
                processed += 1
                if processed % 10 == 0:
                    print(f"   진행률: {processed}/{total_stocks} ({processed/total_stocks*100:.1f}%)")
                
                # Get data for the specified period
                end_date = data.index[-1]
                start_date = end_date - timedelta(days=days)
                period_data = data[data.index >= start_date].copy()
                
                if len(period_data) < 30:  # Need minimum data points
                    continue
                
                # Execute strategy
                result = self._execute_strategy(strategy, symbol, period_data, days)
                if result:
                    results.append(result)
                
            except Exception as e:
                continue
        
        # Sort by Sharpe ratio
        return sorted(results, key=lambda x: x['Sharpe_Ratio'], reverse=True)
    
    def _execute_strategy(self, strategy, symbol: str, data: pd.DataFrame, days: int) -> Dict:
        """Execute strategy on single stock"""
        try:
            # Generate trading signals
            signals = strategy.generate_signals(data)
            
            # Calculate portfolio value
            portfolio_value = strategy.calculate_returns(data, signals)
            
            # Calculate performance metrics
            metrics = self.portfolio_analyzer.calculate_metrics(
                portfolio_value, symbol, days
            )
            
            # Add additional data
            metrics['Portfolio_History'] = portfolio_value
            metrics['Signals'] = signals
            
            return metrics
            
        except Exception as e:
            return None
    
    def run_strategy_comparison(self, strategies: List, stock_data: Dict, days: int) -> Dict:
        """Compare multiple strategies on the same dataset"""
        comparison_results = {}
        
        print(f"📊 {len(strategies)}개 전략 비교 분석 중...")
        
        for strategy_name, strategy_obj in strategies:
            print(f"🔄 {strategy_name} 분석 중...")
            
            try:
                results = self.run_multi_stock_backtest(strategy_obj, stock_data, days)
                
                if results:
                    # Get average performance across all stocks
                    avg_metrics = self._calculate_average_performance(results)
                    comparison_results[strategy_name] = {
                        'average_metrics': avg_metrics,
                        'individual_results': results,
                        'top_stock': results[0] if results else None
                    }
            except Exception as e:
                print(f"⚠️ {strategy_name} 분석 실패: {str(e)}")
                continue
        
        return comparison_results
    
    def _calculate_average_performance(self, results: List[Dict]) -> Dict:
        """Calculate average performance metrics across all stocks"""
        if not results:
            return {}
        
        metrics = {}
        metric_keys = ['Total_Return_%', 'Annual_Return_%', 'Volatility_%', 
                      'Sharpe_Ratio', 'Max_Drawdown_%', 'Win_Rate_%']
        
        for key in metric_keys:
            values = [result.get(key, 0) for result in results if key in result]
            if values:
                metrics[f'Avg_{key}'] = np.mean(values)
                metrics[f'Median_{key}'] = np.median(values)
                metrics[f'Std_{key}'] = np.std(values)
        
        return metrics
    
    def run_monte_carlo_simulation(self, strategy, stock_data: Dict, 
                                days: int, num_simulations: int = 1000) -> Dict:
        """Run Monte Carlo simulation for strategy"""
        print(f"🎲 몬테카를로 시뮬레이션 실행 중... ({num_simulations}회)")
        
        simulation_results = []
        
        # Sample a subset of stocks for simulation
        sample_symbols = np.random.choice(
            list(stock_data.keys()), 
            size=min(20, len(stock_data)), 
            replace=False
        )
        
        for i in range(num_simulations):
            if (i + 1) % 100 == 0:
                print(f"   시뮬레이션 진행률: {i+1}/{num_simulations}")
            
            try:
                # Randomly select a stock
                symbol = np.random.choice(sample_symbols)
                data = stock_data[symbol]
                
                # Add noise to the data
                noisy_data = self._add_noise_to_data(data, days)
                
                # Run strategy
                result = self._execute_strategy(strategy, symbol, noisy_data, days)
                
                if result:
                    simulation_results.append(result['Annual_Return_%'])
            
            except Exception:
                continue
        
        # Calculate simulation statistics
        simulation_stats = {
            'Mean_Return': np.mean(simulation_results),
            'Std_Return': np.std(simulation_results),
            'Min_Return': np.min(simulation_results),
            'Max_Return': np.max(simulation_results),
            'Percentile_5': np.percentile(simulation_results, 5),
            'Percentile_95': np.percentile(simulation_results, 95),
            'Probability_Positive': (np.array(simulation_results) > 0).mean(),
            'All_Returns': simulation_results
        }
        
        return simulation_stats
    
    def _add_noise_to_data(self, data: pd.DataFrame, days: int) -> pd.DataFrame:
        """Add random noise to stock data for Monte Carlo simulation"""
        end_date = data.index[-1]
        start_date = end_date - timedelta(days=days)
        period_data = data[data.index >= start_date].copy()
        
        # Add noise to price data
        price_noise = np.random.normal(0, 0.01, len(period_data))
        period_data['Close'] = period_data['Close'] * (1 + price_noise)
        
        # Add noise to volume
        volume_noise = np.random.normal(1, 0.1, len(period_data))
        period_data['Volume'] = period_data['Volume'] * np.abs(volume_noise)
        
        return period_data
    
    def run_sensitivity_analysis(self, strategy, stock_data: Dict, 
                                days: int, parameter_ranges: Dict) -> Dict:
        """Run sensitivity analysis on strategy parameters"""
        print("📈 민감도 분석 실행 중...")
        
        sensitivity_results = {}
        
        # Get baseline performance
        baseline_results = self.run_multi_stock_backtest(strategy, stock_data, days)
        baseline_sharpe = np.mean([r['Sharpe_Ratio'] for r in baseline_results])
        
        # Test parameter variations
        for param_name, param_range in parameter_ranges.items():
            print(f"   {param_name} 매개변수 테스트 중...")
            
            param_results = []
            
            for param_value in param_range:
                try:
                    # Modify strategy parameter
                    modified_strategy = self._modify_strategy_parameter(
                        strategy, param_name, param_value
                    )
                    
                    # Run backtest
                    results = self.run_multi_stock_backtest(
                        modified_strategy, stock_data, days
                    )
                    
                    if results:
                        avg_sharpe = np.mean([r['Sharpe_Ratio'] for r in results])
                        param_results.append({
                            'parameter_value': param_value,
                            'avg_sharpe': avg_sharpe,
                            'sharpe_change': avg_sharpe - baseline_sharpe
                        })
                
                except Exception:
                    continue
            
            sensitivity_results[param_name] = param_results
        
        return sensitivity_results
    
    def _modify_strategy_parameter(self, strategy, param_name: str, param_value):
        """Modify strategy parameter for sensitivity analysis"""
        # This is a simplified implementation
        # In practice, you'd need to implement parameter modification for each strategy
        modified_strategy = strategy.__class__()
        
        if hasattr(modified_strategy, param_name):
            setattr(modified_strategy, param_name, param_value)
        
        return modified_strategy
    
    def run_walk_forward_analysis(self, strategy, stock_data: Dict, 
                                window_days: int = 365, step_days: int = 30) -> Dict:
        """Run walk-forward analysis"""
        print("🚶 워크 포워드 분석 실행 중...")
        
        walk_forward_results = []
        
        # Get date range
        all_dates = list(stock_data.values())[0].index
        start_date = all_dates[0]
        end_date = all_dates[-1]
        
        current_date = start_date + timedelta(days=window_days)
        
        while current_date <= end_date:
            try:
                # Define analysis window
                window_start = current_date - timedelta(days=window_days)
                window_end = current_date
                
                # Create subset of data for this window
                window_data = {}
                for symbol, data in stock_data.items():
                    mask = (data.index >= window_start) & (data.index <= window_end)
                    window_data[symbol] = data[mask]
                
                # Run analysis on this window
                results = self.run_multi_stock_backtest(strategy, window_data, window_days)
                
                if results:
                    avg_performance = self._calculate_average_performance(results)
                    walk_forward_results.append({
                        'window_end': window_end,
                        'window_start': window_start,
                        'performance': avg_performance,
                        'num_stocks': len(results)
                    })
                
                current_date += timedelta(days=step_days)
                
            except Exception:
                current_date += timedelta(days=step_days)
                continue
        
        return {
            'walk_forward_results': walk_forward_results,
            'stability_score': self._calculate_stability_score(walk_forward_results)
        }
    
    def _calculate_stability_score(self, walk_forward_results: List[Dict]) -> float:
        """Calculate strategy stability score from walk-forward analysis"""
        if not walk_forward_results:
            return 0.0
        
        sharpe_ratios = []
        for result in walk_forward_results:
            if 'Avg_Sharpe_Ratio' in result['performance']:
                sharpe_ratios.append(result['performance']['Avg_Sharpe_Ratio'])
        
        if not sharpe_ratios:
            return 0.0
        
        # Stability score based on consistency of Sharpe ratios
        mean_sharpe = np.mean(sharpe_ratios)
        std_sharpe = np.std(sharpe_ratios)
        
        # Higher mean and lower std = higher stability
        stability_score = mean_sharpe / (std_sharpe + 0.1)  # Add small constant to avoid division by zero
        
        return max(0, min(10, stability_score))  # Scale 0-10