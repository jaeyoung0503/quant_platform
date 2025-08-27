"""
파일: backtester/integrated_portfolio_optimizer.py
통합 포트폴리오 최적화 모듈
백테스터와 통합하여 선택된 전략의 상위 종목들에 대해 최적 포트폴리오 비율을 계산
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional
import warnings
import uuid

warnings.filterwarnings('ignore')

class IntegratedPortfolioOptimizer:
    """
    백테스터와 통합된 포트폴리오 최적화 클래스
    선택된 전략의 상위 성과 종목들에 대해 최적 비율을 계산
    """

    def __init__(self, lookback_period: int = 252):
        """
        초기화

        Parameters:
        -----------
        lookback_period : int
            수익률 및 공분산 계산을 위한 기간 (기본값: 252일 = 1년)
        """
        self.lookback_period = lookback_period
        self.risk_free_rate = 0.02  # 2% 무위험 수익률
        self.optimization_results = {}

    def calculate_returns_and_covariance(self, price_data: Dict[str, pd.Series]) -> Tuple[pd.Series, pd.DataFrame]:
        """
        가격 데이터로부터 기대수익률과 공분산 행렬 계산

        Parameters:
        -----------
        price_data : Dict[str, pd.Series]
            종목별 가격 데이터 딕셔너리

        Returns:
        --------
        Tuple[pd.Series, pd.DataFrame]
            연간화된 기대수익률과 공분산 행렬
        """
        prices_df = pd.DataFrame(price_data).dropna()
        
        if len(prices_df) < self.lookback_period:
            print(f"⚠️ 데이터 부족: {len(prices_df)}일 < {self.lookback_period}일")
            used_data = prices_df
        else:
            used_data = prices_df.tail(self.lookback_period)
        
        daily_returns = used_data.pct_change().dropna()
        expected_returns = daily_returns.mean() * 252
        cov_matrix = daily_returns.cov() * 252
        
        return expected_returns, cov_matrix

    def minimum_variance_portfolio(self, price_data: Dict[str, pd.Series], allow_short: bool = False) -> Dict:
        """
        최소분산 포트폴리오 계산

        Parameters:
        -----------
        price_data : Dict[str, pd.Series]
            종목별 가격 데이터
        allow_short : bool
            공매도 허용 여부 (기본값: False)

        Returns:
        --------
        Dict
            최적화 결과 (비중, 기대수익률, 변동성 등)
        """
        print("🔍 최소분산 포트폴리오 계산 중...")
        
        expected_returns, cov_matrix = self.calculate_returns_and_covariance(price_data)
        n_assets = len(expected_returns)
        
        def objective(weights):
            return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        bounds = tuple((-1, 1) if allow_short else (0, 1) for _ in range(n_assets))
        initial_weights = np.array([1/n_assets] * n_assets)
        
        result = minimize(objective, initial_weights, method='SLSQP', bounds=bounds, constraints=constraints)
        
        if not result.success:
            print("❌ 최적화 실패:", result.message)
            return self._create_equal_weight_portfolio(expected_returns, cov_matrix)
        
        optimal_weights = result.x
        portfolio_return = np.dot(optimal_weights, expected_returns)
        portfolio_volatility = np.sqrt(np.dot(optimal_weights.T, np.dot(cov_matrix, optimal_weights)))
        sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_volatility
        
        return {
            'strategy': '최소분산 포트폴리오',
            'weights': dict(zip(expected_returns.index, optimal_weights)),
            'expected_return': portfolio_return,
            'volatility': portfolio_volatility,
            'sharpe_ratio': sharpe_ratio,
            'optimization_success': True
        }

    def mean_variance_optimization(self, price_data: Dict[str, pd.Series], 
                                  target_return: Optional[float] = None,
                                  risk_aversion: float = 1.0,
                                  allow_short: bool = False) -> Dict:
        """
        평균분산 최적화 (마코위츠 최적화)

        Parameters:
        -----------
        price_data : Dict[str, pd.Series]
            종목별 가격 데이터
        target_return : float, optional
            목표 수익률 (None이면 샤프비율 최대화)
        risk_aversion : float
            위험회피계수 (높을수록 보수적)
        allow_short : bool
            공매도 허용 여부

        Returns:
        --------
        Dict
            최적화 결과
        """
        print("📊 평균분산 최적화 중...")
        
        expected_returns, cov_matrix = self.calculate_returns_and_covariance(price_data)
        n_assets = len(expected_returns)
        
        if target_return is None:
            def objective(weights):
                portfolio_return = np.dot(weights, expected_returns)
                portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                return -((portfolio_return - self.risk_free_rate) / portfolio_volatility)
            constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        else:
            def objective(weights):
                return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            constraints = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                {'type': 'eq', 'fun': lambda x: np.dot(x, expected_returns) - target_return}
            ]
        
        bounds = tuple((-1, 1) if allow_short else (0, 1) for _ in range(n_assets))
        initial_weights = np.array([1/n_assets] * n_assets)
        
        result = minimize(objective, initial_weights, method='SLSQP', bounds=bounds, constraints=constraints)
        
        if not result.success:
            print("❌ 최적화 실패:", result.message)
            return self._create_equal_weight_portfolio(expected_returns, cov_matrix)
        
        optimal_weights = result.x
        portfolio_return = np.dot(optimal_weights, expected_returns)
        portfolio_volatility = np.sqrt(np.dot(optimal_weights.T, np.dot(cov_matrix, optimal_weights)))
        sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_volatility
        
        strategy_name = "평균분산 최적화" + (f" (목표 수익률: {target_return:.1%})" if target_return else " (최대 샤프비율)")
        
        return {
            'strategy': strategy_name,
            'weights': dict(zip(expected_returns.index, optimal_weights)),
            'expected_return': portfolio_return,
            'volatility': portfolio_volatility,
            'sharpe_ratio': sharpe_ratio,
            'optimization_success': True
        }

    def optimize_strategy_portfolio(self, backtest_results: List[Dict], stock_data: Dict, 
                                  strategy_name: str, top_n: int = 10, 
                                  selection_criteria: str = 'return',
                                  strategy_signals: Optional[Dict[str, pd.Series]] = None) -> Dict:
        """
        백테스트 결과에서 상위 N개 종목을 선택하여 최적 포트폴리오 계산

        Parameters:
        -----------
        backtest_results : List[Dict]
            백테스트 결과 리스트
        stock_data : Dict
            전체 주가 데이터
        strategy_name : str
            선택된 전략 이름
        top_n : int
            상위 몇 개 종목을 선택할지 (기본값: 10)
        selection_criteria : str
            종목 선택 기준 ('return', 'sharpe', 'risk_adjusted')
        strategy_signals : Dict[str, pd.Series], optional
            신호 기반 최적화를 위한 전략 신호

        Returns:
        --------
        Dict
            최적화된 포트폴리오 결과
        """
        print(f"\n🎯 {strategy_name} 전략 포트폴리오 최적화")
        print("="*60)
        
        top_stocks = self._select_top_performing_stocks(backtest_results, top_n, selection_criteria)
        
        if len(top_stocks) < 2:
            print("❌ 최적화를 위한 충분한 종목이 없습니다 (최소 2개 필요)")
            return self._create_fallback_result(top_stocks, strategy_name)
        
        selected_price_data = self._extract_price_data(top_stocks, stock_data)
        
        if not selected_price_data:
            print("❌ 가격 데이터를 찾을 수 없습니다")
            return self._create_fallback_result(top_stocks, strategy_name)
        
        optimization_results = self._run_multiple_optimizations(selected_price_data, strategy_name, top_stocks, strategy_signals)
        recommendation = self._generate_recommendation(optimization_results, top_stocks)
        
        final_result = {
            'strategy_name': strategy_name,
            'selection_criteria': selection_criteria,
            'selected_stocks': top_stocks,
            'price_data': selected_price_data,
            'optimizations': optimization_results,
            'recommendation': recommendation,
            'equal_weight_comparison': self._calculate_equal_weight_performance(selected_price_data)
        }
        
        self.optimization_results[strategy_name] = final_result
        return final_result

    def _select_top_performing_stocks(self, backtest_results: List[Dict], top_n: int, 
                                    selection_criteria: str = 'return') -> List[Dict]:
        """
        백테스트 결과에서 상위 성과 종목 선택
        """
        individual_stocks = [result for result in backtest_results if result.get('Symbol') not in ['PORTFOLIO', 'OPTIMIZED_PORTFOLIO']]
        
        print(f"🔍 총 {len(individual_stocks)}개 종목에서 상위 {top_n}개 선택 중...")
        print(f"📊 선택 기준: {selection_criteria}")
        
        if selection_criteria == 'return':
            sorted_stocks = sorted(individual_stocks, key=lambda x: x.get('Annual_Return_%', 0), reverse=True)
            print("   기준: 연간 수익률")
        elif selection_criteria == 'sharpe':
            sorted_stocks = sorted(individual_stocks, key=lambda x: x.get('Sharpe_Ratio', 0), reverse=True)
            print("   기준: 샤프 비율")
        elif selection_criteria == 'risk_adjusted':
            sorted_stocks = sorted(individual_stocks, 
                                  key=lambda x: x.get('Annual_Return_%', 0) / x.get('Volatility_%', 1) if x.get('Volatility_%', 1) > 0 else 0, 
                                  reverse=True)
            print("   기준: 위험조정 수익률 (수익률/변동성)")
        else:
            sorted_stocks = sorted(individual_stocks, key=lambda x: x.get('Annual_Return_%', 0), reverse=True)
            print("   기준: 연간 수익률 (기본값)")
        
        selected_stocks = sorted_stocks[:top_n]
        
        print(f"\n✅ 선택된 상위 {len(selected_stocks)}개 종목:")
        print("-" * 70)
        print(f"{'순위':<4} {'종목':<8} {'연수익률%':<10} {'샤프비율':<10} {'변동성%':<8} {'위험조정':<8}")
        print("-" * 70)
        
        for i, stock in enumerate(selected_stocks, 1):
            annual_return = stock.get('Annual_Return_%', 0)
            sharpe_ratio = stock.get('Sharpe_Ratio', 0)
            volatility = stock.get('Volatility_%', 1)
            risk_adj = annual_return / volatility if volatility > 0 else 0
            print(f"{i:<4} {stock['Symbol']:<8} {annual_return:<10.2f} {sharpe_ratio:<10.3f} {volatility:<8.2f} {risk_adj:<8.3f}")
        
        return selected_stocks

    def _extract_price_data(self, selected_stocks: List[Dict], stock_data: Dict) -> Dict[str, pd.Series]:
        """
        선택된 종목들의 가격 데이터 추출
        """
        extracted_data = {}
        
        for stock in selected_stocks:
            symbol = stock['Symbol']
            if symbol in stock_data:
                if isinstance(stock_data[symbol], pd.DataFrame):
                    if 'Close' in stock_data[symbol].columns:
                        extracted_data[symbol] = stock_data[symbol]['Close']
                    else:
                        numeric_cols = stock_data[symbol].select_dtypes(include=[np.number]).columns
                        if len(numeric_cols) > 0:
                            extracted_data[symbol] = stock_data[symbol][numeric_cols[0]]
                elif isinstance(stock_data[symbol], pd.Series):
                    extracted_data[symbol] = stock_data[symbol]
        
        return extracted_data

    def _run_multiple_optimizations(self, price_data: Dict[str, pd.Series], strategy_name: str, 
                                  top_stocks: List[Dict], strategy_signals: Optional[Dict[str, pd.Series]]) -> Dict:
        """
        여러 최적화 방법 실행
        """
        print(f"\n🔍 다중 최적화 방법 실행 중...")
        results = {}
        
        try:
            print("  📉 최소분산 포트폴리오 계산 중...")
            results['minimum_variance'] = self.minimum_variance_portfolio(price_data, allow_short=False)
            
            print("  📈 최대 샤프비율 포트폴리오 계산 중...")
            results['maximum_sharpe'] = self.mean_variance_optimization(price_data, allow_short=False)
            
            print("  ⚖️ 위험 패리티 포트폴리오 계산 중...")
            results['risk_parity'] = self._calculate_risk_parity(price_data)
            
            print("  🏆 수익률 가중 포트폴리오 계산 중...")
            results['return_weighted'] = self._calculate_return_weighted_portfolio(price_data, top_stocks)
            
            print("  ⚡ 샤프비율 가중 포트폴리오 계산 중...")
            results['sharpe_weighted'] = self._calculate_sharpe_weighted_portfolio(price_data, top_stocks)
            
            if strategy_signals:
                print("  🔧 신호 조정 포트폴리오 계산 중...")
                results['signal_adjusted'] = self._apply_signal_adjustment(results['maximum_sharpe'], price_data, strategy_name, strategy_signals)
            
            print("  📊 전략 비교 중...")
            results['strategy_comparison'] = self.compare_strategies(price_data)
            
        except Exception as e:
            print(f"  ⚠️ 최적화 중 오류 발생: {str(e)}")
            results['error'] = str(e)
        
        return results

    def _calculate_risk_parity(self, price_data: Dict[str, pd.Series]) -> Dict:
        """
        위험 패리티 포트폴리오 계산
        """
        expected_returns, cov_matrix = self.calculate_returns_and_covariance(price_data)
        volatilities = np.sqrt(np.diag(cov_matrix))
        inv_vol_weights = 1 / volatilities
        inv_vol_weights = inv_vol_weights / inv_vol_weights.sum()
        
        portfolio_return = np.dot(inv_vol_weights, expected_returns)
        portfolio_variance = np.dot(inv_vol_weights.T, np.dot(cov_matrix, inv_vol_weights))
        portfolio_volatility = np.sqrt(portfolio_variance)
        sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_volatility
        
        return {
            'strategy': '위험 패리티',
            'weights': dict(zip(expected_returns.index, inv_vol_weights)),
            'expected_return': portfolio_return,
            'volatility': portfolio_volatility,
            'sharpe_ratio': sharpe_ratio,
            'optimization_success': True
        }

    def _calculate_return_weighted_portfolio(self, price_data: Dict[str, pd.Series], top_stocks: List[Dict]) -> Dict:
        """
        수익률 기반 가중 포트폴리오 계산
        """
        return_weights = {}
        total_positive_return = 0
        
        for stock in top_stocks:
            symbol = stock['Symbol']
            if symbol in price_data:
                annual_return = stock.get('Annual_Return_%', 0)
                return_weights[symbol] = max(0.1, annual_return) if annual_return > 0 else 0.1
                total_positive_return += return_weights[symbol]
        
        normalized_weights = {symbol: weight / total_positive_return for symbol, weight in return_weights.items()} if total_positive_return > 0 else {symbol: 1/len(return_weights) for symbol in return_weights}
        
        expected_returns, cov_matrix = self.calculate_returns_and_covariance(price_data)
        weights_array = np.array([normalized_weights.get(symbol, 0) for symbol in expected_returns.index])
        portfolio_return = np.dot(weights_array, expected_returns)
        portfolio_variance = np.dot(weights_array.T, np.dot(cov_matrix, weights_array))
        portfolio_volatility = np.sqrt(portfolio_variance)
        sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_volatility
        
        return {
            'strategy': '수익률 가중',
            'weights': normalized_weights,
            'expected_return': portfolio_return,
            'volatility': portfolio_volatility,
            'sharpe_ratio': sharpe_ratio,
            'optimization_success': True
        }

    def _calculate_sharpe_weighted_portfolio(self, price_data: Dict[str, pd.Series], top_stocks: List[Dict]) -> Dict:
        """
        샤프비율 기반 가중 포트폴리오 계산
        """
        sharpe_weights = {}
        for stock in top_stocks:
            symbol = stock['Symbol']
            if symbol in price_data:
                sharpe_ratio = stock.get('Sharpe_Ratio', 0)
                sharpe_weights[symbol] = max(0.1, sharpe_ratio)
        
        total_sharpe = sum(sharpe_weights.values())
        normalized_weights = {symbol: weight / total_sharpe for symbol, weight in sharpe_weights.items()} if total_sharpe > 0 else {symbol: 1/len(sharpe_weights) for symbol in sharpe_weights}
        
        expected_returns, cov_matrix = self.calculate_returns_and_covariance(price_data)
        weights_array = np.array([normalized_weights.get(symbol, 0) for symbol in expected_returns.index])
        portfolio_return = np.dot(weights_array, expected_returns)
        portfolio_variance = np.dot(weights_array.T, np.dot(cov_matrix, weights_array))
        portfolio_volatility = np.sqrt(portfolio_variance)
        sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_volatility
        
        return {
            'strategy': '샤프비율 가중',
            'weights': normalized_weights,
            'expected_return': portfolio_return,
            'volatility': portfolio_volatility,
            'sharpe_ratio': sharpe_ratio,
            'optimization_success': True
        }

    def _apply_signal_adjustment(self, base_result: Dict, price_data: Dict[str, pd.Series], 
                              strategy_name: str, strategy_signals: Dict[str, pd.Series]) -> Dict:
        """
        전략 신호를 고려한 가중치 조정
        """
        base_weights = base_result['weights']
        signal_strengths = {}
        
        for asset in base_weights.keys():
            if asset in strategy_signals:
                signals = strategy_signals[asset]
                recent_signals = signals.tail(20)
                signal_strength = recent_signals.mean()
                signal_strengths[asset] = max(0.1, abs(signal_strength))
            else:
                signal_strengths[asset] = 0.1
        
        total_signal = sum(signal_strengths.values())
        adjusted_weights = {asset: strength / total_signal for asset, strength in signal_strengths.items()}
        
        expected_returns, cov_matrix = self.calculate_returns_and_covariance(price_data)
        weights_array = np.array([adjusted_weights[asset] for asset in expected_returns.index])
        portfolio_return = np.dot(weights_array, expected_returns)
        portfolio_variance = np.dot(weights_array.T, np.dot(cov_matrix, weights_array))
        portfolio_volatility = np.sqrt(portfolio_variance)
        sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_volatility
        
        return {
            'strategy': f'{strategy_name} 신호 조정',
            'weights': adjusted_weights,
            'expected_return': portfolio_return,
            'volatility': portfolio_volatility,
            'sharpe_ratio': sharpe_ratio,
            'optimization_success': True
        }

    def _calculate_equal_weight_performance(self, price_data: Dict[str, pd.Series]) -> Dict:
        """
        균등비중 포트폴리오 성과 계산
        """
        n_assets = len(price_data)
        equal_weights = {symbol: 1/n_assets for symbol in price_data.keys()}
        
        expected_returns, cov_matrix = self.calculate_returns_and_covariance(price_data)
        weights_array = np.array([1/n_assets] * n_assets)
        portfolio_return = np.dot(weights_array, expected_returns)
        portfolio_variance = np.dot(weights_array.T, np.dot(cov_matrix, weights_array))
        portfolio_volatility = np.sqrt(portfolio_variance)
        sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_volatility
        
        return {
            'strategy': '균등비중 (원본)',
            'weights': equal_weights,
            'expected_return': portfolio_return,
            'volatility': portfolio_volatility,
            'sharpe_ratio': sharpe_ratio
        }

    def _generate_recommendation(self, optimization_results: Dict, top_stocks: List[Dict]) -> Dict:
        """
        최적화 결과를 기반으로 추천 포트폴리오 생성
        """
        print(f"\n🎯 추천 포트폴리오 생성 중...")
        
        sharpe_scores = {method: result['sharpe_ratio'] for method, result in optimization_results.items() 
                        if isinstance(result, dict) and 'sharpe_ratio' in result}
        
        if not sharpe_scores:
            print("⚠️ 유효한 최적화 결과가 없습니다. 균등비중을 추천합니다.")
            return self._create_equal_weight_recommendation(top_stocks)
        
        best_method, best_sharpe = max(sharpe_scores.items(), key=lambda x: x[1])
        recommended_portfolio = optimization_results[best_method]
        
        print(f"✅ 추천 방법: {recommended_portfolio['strategy']}")
        print(f"   샤프비율: {best_sharpe:.3f}")
        print(f"   기대수익률: {recommended_portfolio['expected_return']*100:.2f}%")
        print(f"   변동성: {recommended_portfolio['volatility']*100:.2f}%")
        
        return {
            'recommended_method': best_method,
            'portfolio': recommended_portfolio,
            'all_sharpe_scores': sharpe_scores,
            'improvement_vs_equal_weight': self._calculate_improvement_vs_equal_weight(optimization_results, recommended_portfolio)
        }

    def _calculate_improvement_vs_equal_weight(self, optimization_results: Dict, recommended_portfolio: Dict) -> Dict:
        """
        균등비중 대비 개선 효과 계산
        """
        if 'strategy_comparison' in optimization_results:
            comparison_df = optimization_results['strategy_comparison']
            equal_weight_row = comparison_df[comparison_df['Strategy'] == '균등비중']
            
            if not equal_weight_row.empty:
                equal_weight_sharpe = equal_weight_row['Sharpe Ratio'].iloc[0]
                equal_weight_return = equal_weight_row['Expected Return (%)'].iloc[0] / 100
                equal_weight_vol = equal_weight_row['Volatility (%)'].iloc[0] / 100
                
                recommended_sharpe = recommended_portfolio['sharpe_ratio']
                recommended_return = recommended_portfolio['expected_return']
                recommended_vol = recommended_portfolio['volatility']
                
                return {
                    'sharpe_improvement': recommended_sharpe - equal_weight_sharpe,
                    'return_improvement': (recommended_return - equal_weight_return) * 100,
                    'volatility_change': (recommended_vol - equal_weight_vol) * 100,
                    'improvement_percentage': ((recommended_sharpe / equal_weight_sharpe) - 1) * 100
                }
        
        return {}

    def _create_equal_weight_recommendation(self, top_stocks: List[Dict]) -> Dict:
        """
        균등비중 추천 생성 (fallback)
        """
        n_stocks = len(top_stocks)
        equal_weights = {stock['Symbol']: 1/n_stocks for stock in top_stocks}
        
        return {
            'recommended_method': '균등비중',
            'portfolio': {
                'strategy': '균등비중 (Fallback)',
                'weights': equal_weights,
                'expected_return': 0.08,
                'volatility': 0.15,
                'sharpe_ratio': 0.4
            },
            'all_sharpe_scores': {'균등비중': 0.4},
            'improvement_vs_equal_weight': {}
        }

    def _create_fallback_result(self, stocks: List[Dict], strategy_name: str) -> Dict:
        """
        fallback 결과 생성
        """
        return {
            'strategy_name': strategy_name,
            'selected_stocks': stocks,
            'error': '최적화를 위한 데이터 부족',
            'recommendation': self._create_equal_weight_recommendation(stocks)
        }

    def compare_strategies(self, price_data: Dict[str, pd.Series], allow_short: bool = False) -> pd.DataFrame:
        """
        다양한 포트폴리오 전략 비교
        """
        print("⚖️ 포트폴리오 전략 비교 중...")
        
        strategies = []
        expected_returns, cov_matrix = self.calculate_returns_and_covariance(price_data)
        n_assets = len(expected_returns)
        
        # 균등비중
        equal_weights = np.array([1/n_assets] * n_assets)
        equal_return = np.dot(equal_weights, expected_returns)
        equal_variance = np.dot(equal_weights.T, np.dot(cov_matrix, equal_weights))
        equal_volatility = np.sqrt(equal_variance)
        equal_sharpe = (equal_return - self.risk_free_rate) / equal_volatility
        
        strategies.append({
            'Strategy': '균등비중',
            'Expected Return (%)': equal_return * 100,
            'Volatility (%)': equal_volatility * 100,
            'Sharpe Ratio': equal_sharpe,
            'Weights': dict(zip(expected_returns.index, equal_weights))
        })
        
        # 최소분산
        min_var_result = self.minimum_variance_portfolio(price_data, allow_short)
        strategies.append({
            'Strategy': '최소분산',
            'Expected Return (%)': min_var_result['expected_return'] * 100,
            'Volatility (%)': min_var_result['volatility'] * 100,
            'Sharpe Ratio': min_var_result['sharpe_ratio'],
            'Weights': min_var_result['weights']
        })
        
        # 최대 샤프비율
        max_sharpe_result = self.mean_variance_optimization(price_data, allow_short=allow_short)
        strategies.append({
            'Strategy': '최대 샤프비율',
            'Expected Return (%)': max_sharpe_result['expected_return'] * 100,
            'Volatility (%)': max_sharpe_result['volatility'] * 100,
            'Sharpe Ratio': max_sharpe_result['sharpe_ratio'],
            'Weights': max_sharpe_result['weights']
        })
        
        # 위험 패리티
        inv_vol_weights = 1 / np.sqrt(np.diag(cov_matrix))
        inv_vol_weights = inv_vol_weights / inv_vol_weights.sum()
        rp_return = np.dot(inv_vol_weights, expected_returns)
        rp_variance = np.dot(inv_vol_weights.T, np.dot(cov_matrix, inv_vol_weights))
        rp_volatility = np.sqrt(rp_variance)
        rp_sharpe = (rp_return - self.risk_free_rate) / rp_volatility
        
        strategies.append({
            'Strategy': '위험 패리티',
            'Expected Return (%)': rp_return * 100,
            'Volatility (%)': rp_volatility * 100,
            'Sharpe Ratio': rp_sharpe,
            'Weights': dict(zip(expected_returns.index, inv_vol_weights))
        })
        
        return pd.DataFrame(strategies)

    def efficient_frontier(self, price_data: Dict[str, pd.Series], num_portfolios: int = 100, 
                         allow_short: bool = False) -> pd.DataFrame:
        """
        효율적 투자선 계산
        """
        print("📈 효율적 투자선 계산 중...")
        
        expected_returns, cov_matrix = self.calculate_returns_and_covariance(price_data)
        min_return, max_return = expected_returns.min(), expected_returns.max()
        target_returns = np.linspace(min_return, max_return, num_portfolios)
        
        efficient_portfolios = []
        for target_return in target_returns:
            try:
                result = self.mean_variance_optimization(price_data, target_return=target_return, allow_short=allow_short)
                if result['optimization_success']:
                    efficient_portfolios.append({
                        'return': result['expected_return'],
                        'volatility': result['volatility'],
                        'sharpe_ratio': result['sharpe_ratio']
                    })
            except:
                continue
        
        return pd.DataFrame(efficient_portfolios)

    def portfolio_risk_analysis(self, price_data: Dict[str, pd.Series], weights: Dict[str, float]) -> Dict:
        """
        포트폴리오 리스크 분석
        """
        print("\n" + "="*50)
        print("⚠️ 포트폴리오 리스크 분석")
        print("="*50)
        
        returns_data = {asset: prices.pct_change().dropna() for asset, prices in price_data.items() if asset in weights}
        returns_df = pd.DataFrame(returns_data)
        
        weights_series = pd.Series(weights)
        portfolio_returns = (returns_df * weights_series).sum(axis=1)
        
        var_95 = np.percentile(portfolio_returns, 5) * 100
        var_99 = np.percentile(portfolio_returns, 1) * 100
        es_95 = portfolio_returns[portfolio_returns <= np.percentile(portfolio_returns, 5)].mean() * 100
        es_99 = portfolio_returns[portfolio_returns <= np.percentile(portfolio_returns, 1)].mean() * 100
        
        cumulative_returns = (1 + portfolio_returns).cumprod()
        rolling_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - rolling_max) / rolling_max
        max_drawdown = drawdown.min() * 100
        
        print(f"📊 리스크 지표:")
        print(f"  95% VaR (일간):     {var_95:.2f}%")
        print(f"  99% VaR (일간):     {var_99:.2f}%")
        print(f"  95% 기대 손실:      {es_95:.2f}%")
        print(f"  99% 기대 손실:      {es_99:.2f}%")
        print(f"  최대 드로우다운:    {max_drawdown:.2f}%")
        
        correlation_matrix = returns_df.corr()
        print(f"\n📈 자산 간 상관관계:")
        print(correlation_matrix.round(3))
        
        plt.figure(figsize=(10, 8))
        sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0, square=True, linewidths=0.5, cbar_kws={"shrink": .5})
        plt.title('자산 상관관계 행렬')
        plt.tight_layout()
        plt.show()
        
        return {
            'var_95': var_95,
            'var_99': var_99,
            'es_95': es_95,
            'es_99': es_99,
            'max_drawdown': max_drawdown,
            'correlation_matrix': correlation_matrix
        }

    def visualize_results(self, comparison_df: pd.DataFrame, efficient_frontier_df: Optional[pd.DataFrame] = None):
        """
        최적화 결과 시각화
        """
        plt.style.use('seaborn-v0_8-darkgrid')
        
        if efficient_frontier_df is not None:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
            
            ax1.plot(efficient_frontier_df['volatility'] * 100, efficient_frontier_df['return'] * 100, 'b-', linewidth=2, label='효율적 투자선')
            
            colors = ['red', 'green', 'orange', 'purple']
            markers = ['o', '^', 's', 'D']
            
            for i, (_, row) in enumerate(comparison_df.iterrows()):
                ax1.scatter(row['Volatility (%)'], row['Expected Return (%)'], color=colors[i % len(colors)], 
                           marker=markers[i % len(markers)], s=100, label=row['Strategy'], alpha=0.8, edgecolors='black')
            
            ax1.set_xlabel('변동성 (%)')
            ax1.set_ylabel('기대수익률 (%)')
            ax1.set_title('효율적 투자선 및 포트폴리오 전략')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
        else:
            fig, ax2 = plt.subplots(1, 1, figsize=(10, 6))
        
        ax = ax2 if efficient_frontier_df is not None else ax2
        strategies = comparison_df['Strategy'].values
        sharpes = comparison_df['Sharpe Ratio'].values
        
        bars = ax.bar(strategies, sharpes, alpha=0.7, color=['skyblue', 'lightgreen', 'orange', 'pink'])
        ax.set_xlabel('전략')
        ax.set_ylabel('샤프비율')
        ax.set_title('샤프비율 비교')
        ax.grid(True, alpha=0.3)
        
        for bar, sharpe in zip(bars, sharpes):
            ax.text(bar.get_x() + bar.get_width()/2., sharpe + 0.01, f'{sharpe:.3f}', ha='center', va='bottom', fontweight='bold')
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    def display_optimization_results(self, result: Dict):
        """
        최적화 결과를 보기 좋게 출력
        """
        if 'error' in result:
            print(f"❌ 최적화 실패: {result['error']}")
            return
        
        strategy_name = result['strategy_name']
        selection_criteria = result.get('selection_criteria', 'return')
        selected_stocks = result['selected_stocks']
        optimizations = result.get('optimizations', {})
        recommendation = result.get('recommendation', {})
        
        print(f"\n" + "="*80)
        print(f"🎯 {strategy_name} 포트폴리오 최적화 결과")
        print(f"📊 종목 선택 기준: {selection_criteria}")
        print("="*80)
        
        print(f"\n📋 선택된 종목 ({len(selected_stocks)}개):")
        print("-" * 70)
        print(f"{'순위':<4} {'종목':<8} {'연수익률%':<10} {'샤프비율':<10} {'변동성%':<8} {'위험조정':<8}")
        print("-" * 70)
        
        sorted_by_return = sorted(selected_stocks, key=lambda x: x.get('Annual_Return_%', 0), reverse=True)
        
        for i, stock in enumerate(sorted_by_return, 1):
            annual_return = stock.get('Annual_Return_%', 0)
            sharpe_ratio = stock.get('Sharpe_Ratio', 0)
            volatility = stock.get('Volatility_%', 1)
            risk_adj = annual_return / volatility if volatility > 0 else 0
            print(f"{i:<4} {stock['Symbol']:<8} {annual_return:<10.2f} {sharpe_ratio:<10.3f} {volatility:<8.2f} {risk_adj:<8.3f}")
        
        if optimizations:
            print(f"\n📊 최적화 방법별 성과 비교:")
            print("-" * 90)
            print(f"{'방법':<25} {'샤프비율':<10} {'기대수익률':<12} {'변동성':<10} {'상태'}")
            print("-" * 90)
            
            for method, result_data in optimizations.items():
                if isinstance(result_data, dict) and 'sharpe_ratio' in result_data:
                    status = "✅" if result_data.get('optimization_success', False) else "⚠️"
                    print(f"{result_data['strategy']:<25} {result_data['sharpe_ratio']:<10.3f} "
                          f"{result_data['expected_return']*100:<12.2f}% {result_data['volatility']*100:<10.2f}% {status}")
        
        if recommendation and 'portfolio' in recommendation:
            recommended = recommendation['portfolio']
            print(f"\n🏆 추천 포트폴리오: {recommended['strategy']}")
            print("-" * 60)
            print(f"📈 기대수익률: {recommended['expected_return']*100:.2f}%")
            print(f"📉 변동성:     {recommended['volatility']*100:.2f}%")
            print(f"⚡ 샤프비율:   {recommended['sharpe_ratio']:.3f}")
            
            print(f"\n💼 포트폴리오 비중 (수익률 순):")
            weights = recommended['weights']
            stock_returns = {stock['Symbol']: stock.get('Annual_Return_%', 0) for stock in selected_stocks}
            sorted_symbols = sorted(stock_returns.items(), key=lambda x: x[1], reverse=True)
            
            print("-" * 50)
            print(f"{'종목':<8} {'비중%':<8} {'연수익률%':<12} {'기여도%':<10}")
            print("-" * 50)
            
            for symbol, return_rate in sorted_symbols:
                if symbol in weights:
                    weight = weights[symbol]
                    contribution = weight * return_rate
                    print(f"{symbol:<8} {weight*100:>6.2f}% {return_rate:>10.2f}% {contribution:>8.2f}%")
            
            total_weight = sum(weights.values())
            top_3_symbols = sorted_symbols[:3]
            top_3_weight = sum([weights.get(symbol, 0) for symbol, _ in top_3_symbols])
            weighted_return = sum([weights.get(symbol, 0) * return_rate for symbol, return_rate in sorted_symbols])
            
            print(f"\n📊 포트폴리오 분석:")
            print(f"  총 비중 합계:      {total_weight*100:.1f}%")
            print(f"  상위 3개 종목 비중: {top_3_weight*100:.1f}%")
            print(f"  가중평균 수익률:   {weighted_return:.2f}%")
            
            improvement = recommendation.get('improvement_vs_equal_weight', {})
            if improvement:
                print(f"\n📈 균등비중 대비 개선 효과:")
                if 'sharpe_improvement' in improvement:
                    print(f"  샤프비율 개선:   +{improvement['sharpe_improvement']:.3f}")
                if 'return_improvement' in improvement:
                    print(f"  수익률 개선:     +{improvement['return_improvement']:.2f}%")
                if 'improvement_percentage' in improvement:
                    print(f"  전체 개선율:     +{improvement['improvement_percentage']:.1f}%")

    def export_to_excel(self, result: Dict, filename: str = None):
        """
        결과를 엑셀 파일로 내보내기
        """
        if filename is None:
            strategy_name = result.get('strategy_name', 'portfolio').replace(' ', '_')
            filename = f"{strategy_name}_optimization_results.xlsx"
        
        print(f"\n💾 결과를 {filename}에 저장 중...")
        
        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                if 'selected_stocks' in result:
                    stocks_df = pd.DataFrame(result['selected_stocks'])
                    stocks_df.to_excel(writer, sheet_name='선택된_종목', index=False)
                
                optimization_summary = []
                if 'optimizations' in result:
                    for method, opt_result in result['optimizations'].items():
                        if isinstance(opt_result, dict) and 'sharpe_ratio' in opt_result:
                            optimization_summary.append({
                                '방법': opt_result['strategy'],
                                '샤프비율': opt_result['sharpe_ratio'],
                                '기대수익률_%': opt_result['expected_return'] * 100,
                                '변동성_%': opt_result['volatility'] * 100,
                                '성공': opt_result.get('optimization_success', False)
                            })
                
                if optimization_summary:
                    summary_df = pd.DataFrame(optimization_summary)
                    summary_df.to_excel(writer, sheet_name='최적화_요약', index=False)
                
                if 'recommendation' in result and 'portfolio' in result['recommendation']:
                    weights = result['recommendation']['portfolio']['weights']
                    weights_df = pd.DataFrame(list(weights.items()), columns=['종목', '비중_%'])
                    weights_df['비중_%'] = weights_df['비중_%'] * 100
                    weights_df = weights_df.sort_values('비중_%', ascending=False)
                    weights_df.to_excel(writer, sheet_name='추천_비중', index=False)
                
                all_weights_data = []
                if 'optimizations' in result:
                    for method, opt_result in result['optimizations'].items():
                        if isinstance(opt_result, dict) and 'weights' in opt_result:
                            for symbol, weight in opt_result['weights'].items():
                                all_weights_data.append({
                                    '방법': opt_result['strategy'],
                                    '종목': symbol,
                                    '비중_%': weight * 100
                                })
                
                if all_weights_data:
                    all_weights_df = pd.DataFrame(all_weights_data)
                    weights_pivot = all_weights_df.pivot(index='종목', columns='방법', values='비중_%')
                    weights_pivot.to_excel(writer, sheet_name='전체_방법_비중')
            
            print(f"✅ 결과가 성공적으로 {filename}에 저장되었습니다!")
        
        except Exception as e:
            print(f"❌ 파일 저장 중 오류 발생: {str(e)}")

def integrate_with_main_backtester(backtest_results: List[Dict], stock_data: Dict, 
                                 strategy_name: str, top_n: int = 10,
                                 strategy_signals: Optional[Dict[str, pd.Series]] = None) -> Dict:
    """
    Main 백테스터와 통합하여 최적화 실행

    Parameters:
    -----------
    backtest_results : List[Dict]
        백테스트 결과
    stock_data : Dict
        전체 주가 데이터
    strategy_name : str
        선택된 전략 이름
    top_n : int
        상위 몇 개 종목을 선택할지 (기본값: 10)
    strategy_signals : Dict[str, pd.Series], optional
        신호 기반 최적화를 위한 전략 신호

    Returns:
    --------
    Dict
        최적화 결과
    """
    # print(f"\n🔗 Main 백테스터와 포트폴리오 최적화 통합 실행")
    # print(f"전략: {strategy_name}")
    # print(f"대상: 상위 {top_n}개 종목")
    
    optimizer = IntegratedPortfolioOptimizer()
    result = optimizer.optimize_strategy_portfolio(
        backtest_results=backtest_results,
        stock_data=stock_data,
        strategy_name=strategy_name,
        top_n=top_n,
        strategy_signals=strategy_signals
    )    
    optimizer.display_optimization_results(result)
    optimizer.export_to_excel(result)
    
    return result

def generate_sample_data() -> Dict[str, pd.Series]:
    """
    테스트를 위한 샘플 가격 데이터 생성
    """
    np.random.seed(42)
    assets = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'FB', 'NFLX', 'NVDA', 'JPM', 'V']
    data = {}
    days = 500
    dates = pd.date_range(start='2023-01-01', periods=days, freq='D')
    
    for asset in assets:
        returns = np.random.normal(0.001 if asset == 'TSLA' else 0.0008 if asset in ['AAPL', 'MSFT'] else 0.0006,     0.03 if asset == 'TSLA' else 0.02 if asset in ['AAPL', 'MSFT'] else 0.015, days)
        prices = [100]
        for ret in returns:
            prices.append(prices[-1] * (1 + ret))
        data[asset] = pd.Series(prices[:days], index=dates)
    
    return data

def main():
    """
    테스트를 위한 메인 실행 함수
    """
    print("🚀 포트폴리오 최적화 모듈 테스트")
    print("="*50)
    
    price_data = generate_sample_data()
    print(f"✅ {len(price_data)}개 종목 샘플 데이터 생성 완료")
    
    optimizer = IntegratedPortfolioOptimizer()
    
    print("\n1️⃣ 포트폴리오 전략 비교 실행 중...")
    comparison_result = optimizer.compare_strategies(price_data, allow_short=False)
    
    print("\n2️⃣ 효율적 투자선 계산 중...")
    efficient_frontier = optimizer.efficient_frontier(price_data, num_portfolios=50)
    
    optimizer.visualize_results(comparison_result, efficient_frontier)
    
    print("\n3️⃣ 개별 최적화 결과")
    print("-" * 40)
    
    min_var = optimizer.minimum_variance_portfolio(price_data)
    print(f"🎯 최소분산 포트폴리오 샤프비율: {min_var['sharpe_ratio']:.3f}")
    
    max_sharpe = optimizer.mean_variance_optimization(price_data)
    print(f"📈 최대 샤프비율 포트폴리오 샤프비율: {max_sharpe['sharpe_ratio']:.3f}")
    
    if 'max_sharpe' in locals():
        print("\n4️⃣ 리스크 분석 실행 중...")
        risk_analysis = optimizer.portfolio_risk_analysis(price_data, max_sharpe['weights'])
    
    results = {
        'comparison': comparison_result,
        'efficient_frontier': efficient_frontier,
        'min_variance': min_var,
        'max_sharpe': max_sharpe,
        'risk_analysis': risk_analysis if 'risk_analysis' in locals() else None
    }
    
    optimizer.export_to_excel(results)
    
    print("\n🎉 포트폴리오 최적화 완료!")
    
    return results

if __name__ == "__main__":
    sample_backtest_results = [
        {'Symbol': 'PORTFOLIO', 'Sharpe_Ratio': 1.2, 'Annual_Return_%': 15.5},
        {'Symbol': 'AAPL', 'Sharpe_Ratio': 1.8, 'Annual_Return_%': 18.2, 'Volatility_%': 22.1},
        {'Symbol': 'GOOGL', 'Sharpe_Ratio': 1.5, 'Annual_Return_%': 16.8, 'Volatility_%': 25.3},
        {'Symbol': 'MSFT', 'Sharpe_Ratio': 1.4, 'Annual_Return_%': 14.9, 'Volatility_%': 20.7},
        {'Symbol': 'AMZN', 'Sharpe_Ratio': 1.1, 'Annual_Return_%': 13.2, 'Volatility_%': 28.4},
        {'Symbol': 'TSLA', 'Sharpe_Ratio': 0.9, 'Annual_Return_%': 12.1, 'Volatility_%': 35.2},
        {'Symbol': 'FB', 'Sharpe_Ratio': 1.3, 'Annual_Return_%': 15.0, 'Volatility_%': 23.5},
        {'Symbol': 'NFLX', 'Sharpe_Ratio': 1.0, 'Annual_Return_%': 14.0, 'Volatility_%': 30.1},
        {'Symbol': 'NVDA', 'Sharpe_Ratio': 1.6, 'Annual_Return_%': 17.5, 'Volatility_%': 27.8},
        {'Symbol': 'JPM', 'Sharpe_Ratio': 1.2, 'Annual_Return_%': 13.8, 'Volatility_%': 21.3},
        {'Symbol': 'V', 'Sharpe_Ratio': 1.4, 'Annual_Return_%': 15.2, 'Volatility_%': 22.9},
    ]
    
    sample_stock_data = generate_sample_data()
    
    strategy_signals = {}
    for asset, prices in sample_stock_data.items():
        ma_short = prices.rolling(20).mean()
        ma_long = prices.rolling(50).mean()
        signals = pd.Series(0, index=prices.index)
        signals[ma_short > ma_long] = 1
        signals[ma_short < ma_long] = -1
        strategy_signals[asset] = signals
    
    result = integrate_with_main_backtester(
        backtest_results=sample_backtest_results,
        stock_data=sample_stock_data,
        strategy_name="샘플 전략",
        top_n=10,
        strategy_signals=strategy_signals
    )
    
    print("\n🎉 통합 및 최적화 완료!")


# #!/usr/bin/env python3
# """
# File: backtester/integrated_optimizer.py
# Integrated Portfolio Optimizer
# Main 백테스터와 연동하여 선택된 전략의 상위 종목들에 대해 최적 포트폴리오 비율을 계산
# """

# import numpy as np
# import pandas as pd
# from typing import Dict, List, Tuple, Optional
# import warnings
# warnings.filterwarnings('ignore')

# # 기존 모듈들 임포트
# from portfolio_optimizer import PortfolioOptimizer, StrategyPortfolioOptimizer
# from strategies import *

# class IntegratedPortfolioOptimizer:
#     """
#     Main 백테스터와 통합된 포트폴리오 최적화 클래스
#     선택된 전략의 상위 성과 종목들에 대해 최적 비율을 계산
#     """
    
#     def __init__(self):
#         self.portfolio_optimizer = PortfolioOptimizer()
#         self.optimization_results = {}
        
#     def optimize_strategy_portfolio(self, backtest_results: List[Dict], 
#                                   stock_data: Dict, strategy_name: str,
#                                   top_n: int = 10, 
#                                   selection_criteria: str = 'return') -> Dict:
#         """
#         백테스트 결과에서 상위 N개 종목을 선택하여 최적 포트폴리오 계산
        
#         Parameters:
#         -----------
#         backtest_results : List[Dict]
#             Main에서 실행된 백테스트 결과 리스트
#         stock_data : Dict
#             전체 주가 데이터
#         strategy_name : str
#             선택된 전략 이름
#         top_n : int
#             상위 몇 개 종목을 선택할지 (기본값: 10)
#         selection_criteria : str
#             종목 선택 기준 ('return', 'sharpe', 'risk_adjusted')
            
#         Returns:
#         --------
#         Dict
#             최적화된 포트폴리오 결과
#         """
        
#         print(f"\n🎯 {strategy_name} 전략 포트폴리오 최적화")
#         print("="*60)
        
#         # 1. 상위 성과 종목 선택 (수익률 기준)
#         top_stocks = self._select_top_performing_stocks(
#             backtest_results, top_n, selection_criteria
#         )
        
#         if len(top_stocks) < 2:
#             print("❌ 최적화를 위한 충분한 종목이 없습니다 (최소 2개 필요)")
#             return self._create_fallback_result(top_stocks, strategy_name)
        
#         # 2. 선택된 종목들의 가격 데이터 추출
#         selected_price_data = self._extract_price_data(top_stocks, stock_data)
        
#         if not selected_price_data:
#             print("❌ 가격 데이터를 찾을 수 없습니다")
#             return self._create_fallback_result(top_stocks, strategy_name)
        
#         # 3. 다양한 최적화 방법 적용
#         optimization_results = self._run_multiple_optimizations(
#             selected_price_data, strategy_name, top_stocks
#         )
        
#         # 4. 결과 비교 및 추천
#         recommendation = self._generate_recommendation(optimization_results, top_stocks)
        
#         # 5. 수익률 기준 포트폴리오 추가 계산
#         return_weighted_result = self._calculate_return_weighted_portfolio(
#             selected_price_data, top_stocks
#         )
#         optimization_results['return_weighted'] = return_weighted_result
        
#         # 6. 결과 저장 및 반환
#         final_result = {
#             'strategy_name': strategy_name,
#             'selection_criteria': selection_criteria,
#             'selected_stocks': top_stocks,
#             'price_data': selected_price_data,
#             'optimizations': optimization_results,
#             'recommendation': recommendation,
#             'equal_weight_comparison': self._calculate_equal_weight_performance(selected_price_data)
#         }
        
#         self.optimization_results[strategy_name] = final_result
#         return final_result
    
#     def _select_top_performing_stocks(self, backtest_results: List[Dict], top_n: int, 
#                                      selection_criteria: str = 'return') -> List[Dict]:
#         """백테스트 결과에서 상위 성과 종목 선택
        
#         Parameters:
#         -----------
#         backtest_results : List[Dict]
#             백테스트 결과 리스트
#         top_n : int
#             선택할 종목 수
#         selection_criteria : str
#             선택 기준 ('return', 'sharpe', 'risk_adjusted')
#             - 'return': 연간 수익률 기준
#             - 'sharpe': 샤프 비율 기준
#             - 'risk_adjusted': 위험조정 수익률 기준
#         """
        
#         # 포트폴리오 결과 제외 (첫 번째는 보통 포트폴리오 전체 결과)
#         individual_stocks = []
        
#         for result in backtest_results:
#             if result.get('Symbol') not in ['PORTFOLIO', 'OPTIMIZED_PORTFOLIO']:
#                 individual_stocks.append(result)
        
#         print(f"🔍 총 {len(individual_stocks)}개 종목에서 상위 {top_n}개 선택 중...")
#         print(f"📊 선택 기준: {selection_criteria}")
        
#         # 선택 기준에 따른 정렬
#         if selection_criteria == 'return':
#             # 연간 수익률 기준으로 정렬
#             sorted_stocks = sorted(individual_stocks, 
#                                  key=lambda x: x.get('Annual_Return_%', 0), 
#                                  reverse=True)
#             print("   기준: 연간 수익률 (Annual Return)")
            
#         elif selection_criteria == 'sharpe':
#             # 샤프 비율 기준으로 정렬
#             sorted_stocks = sorted(individual_stocks, 
#                                  key=lambda x: x.get('Sharpe_Ratio', 0), 
#                                  reverse=True)
#             print("   기준: 샤프 비율 (Sharpe Ratio)")
            
#         elif selection_criteria == 'risk_adjusted':
#             # 위험조정 수익률 기준 (수익률 / 변동성)
#             def risk_adjusted_return(stock):
#                 annual_return = stock.get('Annual_Return_%', 0)
#                 volatility = stock.get('Volatility_%', 1)  # 0으로 나누기 방지
#                 return annual_return / volatility if volatility > 0 else 0
            
#             sorted_stocks = sorted(individual_stocks, 
#                                  key=risk_adjusted_return, 
#                                  reverse=True)
#             print("   기준: 위험조정 수익률 (Return/Volatility)")
            
#         else:
#             # 기본값: 연간 수익률
#             sorted_stocks = sorted(individual_stocks, 
#                                  key=lambda x: x.get('Annual_Return_%', 0), 
#                                  reverse=True)
#             print("   기준: 연간 수익률 (기본값)")
        
#         # 상위 N개 선택
#         selected_stocks = sorted_stocks[:top_n]
        
#         # 선택된 종목 정보 출력
#         print(f"\n✅ 선택된 상위 {len(selected_stocks)}개 종목:")
#         print("-" * 70)
#         print(f"{'순위':<4} {'종목':<8} {'연수익률%':<10} {'샤프비율':<10} {'변동성%':<8} {'위험조정':<8}")
#         print("-" * 70)
        
#         for i, stock in enumerate(selected_stocks, 1):
#             annual_return = stock.get('Annual_Return_%', 0)
#             sharpe_ratio = stock.get('Sharpe_Ratio', 0)
#             volatility = stock.get('Volatility_%', 1)
#             risk_adj = annual_return / volatility if volatility > 0 else 0
            
#             print(f"{i:<4} {stock['Symbol']:<8} {annual_return:<10.2f} "
#                   f"{sharpe_ratio:<10.3f} {volatility:<8.2f} {risk_adj:<8.3f}")
        
#         return selected_stocks
    
#     def _extract_price_data(self, selected_stocks: List[Dict], 
#                            stock_data: Dict) -> Dict[str, pd.Series]:
#         """선택된 종목들의 가격 데이터 추출"""
        
#         extracted_data = {}
        
#         for stock in selected_stocks:
#             symbol = stock['Symbol']
            
#             if symbol in stock_data:
#                 # Close 가격만 추출
#                 if isinstance(stock_data[symbol], pd.DataFrame):
#                     if 'Close' in stock_data[symbol].columns:
#                         extracted_data[symbol] = stock_data[symbol]['Close']
#                     else:
#                         # Close 컬럼이 없으면 첫 번째 숫자 컬럼 사용
#                         numeric_cols = stock_data[symbol].select_dtypes(include=[np.number]).columns
#                         if len(numeric_cols) > 0:
#                             extracted_data[symbol] = stock_data[symbol][numeric_cols[0]]
#                 elif isinstance(stock_data[symbol], pd.Series):
#                     extracted_data[symbol] = stock_data[symbol]
        
#         return extracted_data
    
#     def _run_multiple_optimizations(self, price_data: Dict[str, pd.Series], 
#                                    strategy_name: str, top_stocks: List[Dict]) -> Dict:
#         """여러 최적화 방법 실행"""
        
#         print(f"\n🔍 다중 최적화 방법 실행 중...")
        
#         results = {}
        
#         try:
#             # 1. 최소분산 포트폴리오
#             print("  📉 최소분산 포트폴리오 계산 중...")
#             min_var_result = self.portfolio_optimizer.minimum_variance_portfolio(
#                 price_data, allow_short=False
#             )
#             results['minimum_variance'] = min_var_result
            
#             # 2. 최대 샤프비율 포트폴리오
#             print("  📈 최대 샤프비율 포트폴리오 계산 중...")
#             max_sharpe_result = self.portfolio_optimizer.mean_variance_optimization(
#                 price_data, allow_short=False
#             )
#             results['maximum_sharpe'] = max_sharpe_result
            
#             # 3. 위험 패리티 포트폴리오
#             print("  ⚖️ 위험 패리티 포트폴리오 계산 중...")
#             risk_parity_result = self._calculate_risk_parity(price_data)
#             results['risk_parity'] = risk_parity_result
            
#             # 4. 수익률 가중 포트폴리오 (백테스트 수익률 기반)
#             print("  🏆 수익률 가중 포트폴리오 계산 중...")
#             return_weighted_result = self._calculate_return_weighted_portfolio(price_data, top_stocks)
#             results['return_weighted'] = return_weighted_result
            
#             # 5. 샤프비율 가중 포트폴리오 (백테스트 샤프비율 기반)  
#             print("  ⚡ 샤프비율 가중 포트폴리오 계산 중...")
#             sharpe_weighted_result = self._calculate_sharpe_weighted_portfolio(price_data, top_stocks)
#             results['sharpe_weighted'] = sharpe_weighted_result
            
#             # 6. 전략 비교
#             print("  📊 전략 종합 비교 중...")
#             comparison_result = self.portfolio_optimizer.compare_strategies(price_data)
#             results['strategy_comparison'] = comparison_result
            
#         except Exception as e:
#             print(f"  ⚠️ 최적화 중 오류 발생: {str(e)}")
#             results['error'] = str(e)
        
#         return results
    
#     def _calculate_risk_parity(self, price_data: Dict[str, pd.Series]) -> Dict:
#         """위험 패리티 포트폴리오 계산"""
        
#         # 수익률과 공분산 계산
#         expected_returns, cov_matrix = self.portfolio_optimizer.calculate_returns_and_covariance(price_data)
        
#         # 각 자산의 변동성 (대각선 원소의 제곱근)
#         volatilities = np.sqrt(np.diag(cov_matrix))
        
#         # 역변동성 가중치
#         inv_vol_weights = 1 / volatilities
#         inv_vol_weights = inv_vol_weights / inv_vol_weights.sum()
        
#         # 성과 계산
#         portfolio_return = np.dot(inv_vol_weights, expected_returns)
#         portfolio_variance = np.dot(inv_vol_weights.T, np.dot(cov_matrix, inv_vol_weights))
#         portfolio_volatility = np.sqrt(portfolio_variance)
#         sharpe_ratio = (portfolio_return - self.portfolio_optimizer.risk_free_rate) / portfolio_volatility
        
#         return {
#             'strategy': 'Risk Parity',
#             'weights': dict(zip(expected_returns.index, inv_vol_weights)),
#             'expected_return': portfolio_return,
#             'volatility': portfolio_volatility,
#             'sharpe_ratio': sharpe_ratio,
#             'optimization_success': True
#         }
    
#     def _calculate_return_weighted_portfolio(self, price_data: Dict[str, pd.Series], 
#                                             top_stocks: List[Dict]) -> Dict:
#         """수익률 기반 가중 포트폴리오 계산"""
        
#         # 연간 수익률 기반 가중치 계산
#         return_weights = {}
#         total_positive_return = 0
        
#         # 양수 수익률만 합계 계산
#         for stock in top_stocks:
#             symbol = stock['Symbol']
#             if symbol in price_data:
#                 annual_return = stock.get('Annual_Return_%', 0)
#                 if annual_return > 0:
#                     return_weights[symbol] = annual_return
#                     total_positive_return += annual_return
#                 else:
#                     return_weights[symbol] = 0.1  # 최소 비중 보장
#                     total_positive_return += 0.1
        
#         # 정규화
#         if total_positive_return > 0:
#             normalized_weights = {symbol: weight / total_positive_return 
#                                 for symbol, weight in return_weights.items()}
#         else:
#             # 모든 수익률이 음수인 경우 균등비중
#             n_assets = len(return_weights)
#             normalized_weights = {symbol: 1/n_assets for symbol in return_weights.keys()}
        
#         # 성과 계산
#         expected_returns, cov_matrix = self.portfolio_optimizer.calculate_returns_and_covariance(price_data)
        
#         weights_array = np.array([normalized_weights.get(symbol, 0) for symbol in expected_returns.index])
#         portfolio_return = np.dot(weights_array, expected_returns)
#         portfolio_variance = np.dot(weights_array.T, np.dot(cov_matrix, weights_array))
#         portfolio_volatility = np.sqrt(portfolio_variance)
#         sharpe_ratio = (portfolio_return - self.portfolio_optimizer.risk_free_rate) / portfolio_volatility
        
#         return {
#             'strategy': 'Return Weighted',
#             'weights': normalized_weights,
#             'expected_return': portfolio_return,
#             'volatility': portfolio_volatility,
#             'sharpe_ratio': sharpe_ratio,
#             'optimization_success': True
#         }
    
#     def _calculate_equal_weight_performance(self, price_data: Dict[str, pd.Series]) -> Dict:
#         """균등비중 포트폴리오 성과 계산 (기존 방식과 비교용)"""
        
#         n_assets = len(price_data)
#         equal_weights = {symbol: 1/n_assets for symbol in price_data.keys()}
        
#         expected_returns, cov_matrix = self.portfolio_optimizer.calculate_returns_and_covariance(price_data)
        
#         weights_array = np.array([1/n_assets] * n_assets)
#         portfolio_return = np.dot(weights_array, expected_returns)
#         portfolio_variance = np.dot(weights_array.T, np.dot(cov_matrix, weights_array))
#         portfolio_volatility = np.sqrt(portfolio_variance)
#         sharpe_ratio = (portfolio_return - self.portfolio_optimizer.risk_free_rate) / portfolio_volatility
        
#         return {
#             'strategy': 'Equal Weight (Original)',
#             'weights': equal_weights,
#             'expected_return': portfolio_return,
#             'volatility': portfolio_volatility,
#             'sharpe_ratio': sharpe_ratio
#         }
    
#     def _generate_recommendation(self, optimization_results: Dict, top_stocks: List[Dict]) -> Dict:
#         """최적화 결과를 기반으로 추천 포트폴리오 생성"""
        
#         print(f"\n🎯 추천 포트폴리오 생성 중...")
        
#         # 각 최적화 방법의 샤프비율 수집
#         sharpe_scores = {}
        
#         for method, result in optimization_results.items():
#             if isinstance(result, dict) and 'sharpe_ratio' in result:
#                 sharpe_scores[method] = result['sharpe_ratio']
        
#         if not sharpe_scores:
#             print("⚠️ 유효한 최적화 결과가 없습니다. 균등비중을 추천합니다.")
#             return self._create_equal_weight_recommendation(top_stocks)
        
#         # 최고 샤프비율 방법 선택
#         best_method = max(sharpe_scores.items(), key=lambda x: x[1])
#         best_method_name, best_sharpe = best_method
        
#         recommended_portfolio = optimization_results[best_method_name]
        
#         print(f"✅ 추천 방법: {recommended_portfolio['strategy']}")
#         print(f"   샤프비율: {best_sharpe:.3f}")
#         print(f"   기대수익률: {recommended_portfolio['expected_return']*100:.2f}%")
#         print(f"   변동성: {recommended_portfolio['volatility']*100:.2f}%")
        
#         return {
#             'recommended_method': best_method_name,
#             'portfolio': recommended_portfolio,
#             'all_sharpe_scores': sharpe_scores,
#             'improvement_vs_equal_weight': self._calculate_improvement_vs_equal_weight(
#                 optimization_results, recommended_portfolio
#             )
#         }
    
#     def _calculate_improvement_vs_equal_weight(self, optimization_results: Dict, 
#                                              recommended_portfolio: Dict) -> Dict:
#         """균등비중 대비 개선 효과 계산"""
        
#         if 'strategy_comparison' in optimization_results:
#             comparison_df = optimization_results['strategy_comparison']
#             equal_weight_row = comparison_df[comparison_df['Strategy'] == 'Equal Weight']
            
#             if not equal_weight_row.empty:
#                 equal_weight_sharpe = equal_weight_row['Sharpe Ratio'].iloc[0]
#                 equal_weight_return = equal_weight_row['Expected Return (%)'].iloc[0] / 100
#                 equal_weight_vol = equal_weight_row['Volatility (%)'].iloc[0] / 100
                
#                 recommended_sharpe = recommended_portfolio['sharpe_ratio']
#                 recommended_return = recommended_portfolio['expected_return']
#                 recommended_vol = recommended_portfolio['volatility']
                
#                 return {
#                     'sharpe_improvement': recommended_sharpe - equal_weight_sharpe,
#                     'return_improvement': (recommended_return - equal_weight_return) * 100,
#                     'volatility_change': (recommended_vol - equal_weight_vol) * 100,
#                     'improvement_percentage': ((recommended_sharpe / equal_weight_sharpe) - 1) * 100
#                 }
        
#         return {}
    
#     def _create_equal_weight_recommendation(self, top_stocks: List[Dict]) -> Dict:
#         """균등비중 추천 생성 (fallback)"""
#         n_stocks = len(top_stocks)
#         equal_weights = {stock['Symbol']: 1/n_stocks for stock in top_stocks}
        
#         return {
#             'recommended_method': 'equal_weight',
#             'portfolio': {
#                 'strategy': 'Equal Weight (Fallback)',
#                 'weights': equal_weights,
#                 'expected_return': 0.08,  # 가정값
#                 'volatility': 0.15,       # 가정값
#                 'sharpe_ratio': 0.4       # 가정값
#             },
#             'all_sharpe_scores': {'equal_weight': 0.4},
#             'improvement_vs_equal_weight': {}
#         }
    
#     def _create_fallback_result(self, stocks: List[Dict], strategy_name: str) -> Dict:
#         """fallback 결과 생성"""
#         return {
#             'strategy_name': strategy_name,
#             'selected_stocks': stocks,
#             'error': 'Insufficient data for optimization',
#             'recommendation': self._create_equal_weight_recommendation(stocks)
#         }
    
#     def _calculate_sharpe_weighted_portfolio(self, price_data: Dict[str, pd.Series], 
#                                            top_stocks: List[Dict]) -> Dict:
#         """샤프비율 기반 가중 포트폴리오 계산"""
        
#         # 샤프비율 기반 가중치 계산
#         sharpe_weights = {}
#         for stock in top_stocks:
#             symbol = stock['Symbol']
#             if symbol in price_data:
#                 sharpe_ratio = stock.get('Sharpe_Ratio', 0)
#                 # 음수 샤프비율은 최소값으로 설정
#                 sharpe_weights[symbol] = max(0.1, sharpe_ratio)
        
#         # 정규화
#         total_sharpe = sum(sharpe_weights.values())
#         if total_sharpe > 0:
#             normalized_weights = {symbol: weight / total_sharpe 
#                                 for symbol, weight in sharpe_weights.items()}
#         else:
#             # 모든 샤프비율이 음수인 경우 균등비중
#             n_assets = len(sharpe_weights)
#             normalized_weights = {symbol: 1/n_assets for symbol in sharpe_weights.keys()}
        
#         # 성과 계산
#         expected_returns, cov_matrix = self.portfolio_optimizer.calculate_returns_and_covariance(price_data)
        
#         weights_array = np.array([normalized_weights.get(symbol, 0) for symbol in expected_returns.index])
#         portfolio_return = np.dot(weights_array, expected_returns)
#         portfolio_variance = np.dot(weights_array.T, np.dot(cov_matrix, weights_array))
#         portfolio_volatility = np.sqrt(portfolio_variance)
#         sharpe_ratio = (portfolio_return - self.portfolio_optimizer.risk_free_rate) / portfolio_volatility
        
#         return {
#             'strategy': 'Sharpe Weighted',
#             'weights': normalized_weights,
#             'expected_return': portfolio_return,
#             'volatility': portfolio_volatility,
#             'sharpe_ratio': sharpe_ratio,
#             'optimization_success': True
#         }

#     def display_optimization_results(self, result: Dict):
#         """최적화 결과를 보기 좋게 출력"""
        
#         if 'error' in result:
#             print(f"❌ 최적화 실패: {result['error']}")
#             return
        
#         strategy_name = result['strategy_name']
#         selection_criteria = result.get('selection_criteria', 'return')
#         selected_stocks = result['selected_stocks']
#         optimizations = result.get('optimizations', {})
#         recommendation = result.get('recommendation', {})
        
#         print(f"\n" + "="*80)
#         print(f"🎯 {strategy_name} 포트폴리오 최적화 결과")
#         print(f"📊 종목 선택 기준: {selection_criteria}")
#         print("="*80)
        
#         # 선택된 종목 요약 (수익률 기준으로 재정렬)
#         print(f"\n📋 선택된 종목 ({len(selected_stocks)}개) - 수익률 순:")
#         print("-" * 70)
#         print(f"{'순위':<4} {'종목':<8} {'연수익률%':<10} {'샤프비율':<10} {'변동성%':<8} {'위험조정':<8}")
#         print("-" * 70)
        
#         # 수익률 기준으로 정렬하여 출력
#         sorted_by_return = sorted(selected_stocks, 
#                                 key=lambda x: x.get('Annual_Return_%', 0), 
#                                 reverse=True)
        
#         for i, stock in enumerate(sorted_by_return, 1):
#             annual_return = stock.get('Annual_Return_%', 0)
#             sharpe_ratio = stock.get('Sharpe_Ratio', 0)
#             volatility = stock.get('Volatility_%', 1)
#             risk_adj = annual_return / volatility if volatility > 0 else 0
            
#             print(f"{i:<4} {stock['Symbol']:<8} {annual_return:<10.2f} "
#                   f"{sharpe_ratio:<10.3f} {volatility:<8.2f} {risk_adj:<8.3f}")
        
#         # 최적화 방법별 결과 비교
#         if optimizations:
#             print(f"\n📊 최적화 방법별 성과 비교:")
#             print("-" * 90)
#             print(f"{'방법':<25} {'샤프비율':<10} {'기대수익률':<12} {'변동성':<10} {'상태'}")
#             print("-" * 90)
            
#             for method, result_data in optimizations.items():
#                 if isinstance(result_data, dict) and 'sharpe_ratio' in result_data:
#                     status = "✅" if result_data.get('optimization_success', False) else "⚠️"
#                     print(f"{result_data['strategy']:<25} "
#                           f"{result_data['sharpe_ratio']:<10.3f} "
#                           f"{result_data['expected_return']*100:<12.2f}% "
#                           f"{result_data['volatility']*100:<10.2f}% "
#                           f"{status}")
        
#         # 추천 포트폴리오
#         if recommendation and 'portfolio' in recommendation:
#             recommended = recommendation['portfolio']
#             print(f"\n🏆 추천 포트폴리오: {recommended['strategy']}")
#             print("-" * 60)
#             print(f"📈 기대수익률: {recommended['expected_return']*100:.2f}%")
#             print(f"📉 변동성:     {recommended['volatility']*100:.2f}%")
#             print(f"⚡ 샤프비율:   {recommended['sharpe_ratio']:.3f}")
            
#             # 종목별 비중 (수익률 순으로 정렬하여 표시)
#             print(f"\n💼 종목별 포트폴리오 비중 (수익률 순):")
#             weights = recommended['weights']
            
#             # 종목을 수익률 순으로 정렬
#             stock_returns = {stock['Symbol']: stock.get('Annual_Return_%', 0) 
#                            for stock in selected_stocks}
#             sorted_symbols = sorted(stock_returns.items(), key=lambda x: x[1], reverse=True)
            
#             print("-" * 50)
#             print(f"{'종목':<8} {'비중%':<8} {'연수익률%':<12} {'기여도%':<10}")
#             print("-" * 50)
            
#             for symbol, return_rate in sorted_symbols:
#                 if symbol in weights:
#                     weight = weights[symbol]
#                     contribution = weight * return_rate
#                     print(f"{symbol:<8} {weight*100:>6.2f}% {return_rate:>10.2f}% {contribution:>8.2f}%")
            
#             # 포트폴리오 분석
#             total_weight = sum(weights.values())
#             top_3_symbols = sorted_symbols[:3]
#             top_3_weight = sum([weights.get(symbol, 0) for symbol, _ in top_3_symbols])
            
#             print(f"\n📊 포트폴리오 분석:")
#             print(f"  총 비중 합계:      {total_weight*100:.1f}%")
#             print(f"  상위 3개 종목 비중: {top_3_weight*100:.1f}%")
            
#             # 가중 평균 수익률 계산
#             weighted_return = sum([weights.get(symbol, 0) * return_rate 
#                                  for symbol, return_rate in sorted_symbols])
#             print(f"  가중평균 수익률:   {weighted_return:.2f}%")
            
#             # 개선 효과
#             improvement = recommendation.get('improvement_vs_equal_weight', {})
#             if improvement:
#                 print(f"\n📈 균등비중 대비 개선 효과:")
#                 if 'sharpe_improvement' in improvement:
#                     print(f"  샤프비율 개선:   +{improvement['sharpe_improvement']:.3f}")
#                 if 'return_improvement' in improvement:
#                     print(f"  수익률 개선:     +{improvement['return_improvement']:.2f}%")
#                 if 'improvement_percentage' in improvement:
#                     print(f"  전체 개선율:     +{improvement['improvement_percentage']:.1f}%")
        
#         # 선택된 종목 요약
#         print(f"\n📋 선택된 종목 ({len(selected_stocks)}개):")
#         print("-" * 60)
#         for i, stock in enumerate(selected_stocks, 1):
#             print(f"{i:2d}. {stock['Symbol']:<8} | "
#                   f"샤프: {stock['Sharpe_Ratio']:6.3f} | "
#                   f"수익률: {stock['Annual_Return_%']:6.2f}% | "
#                   f"변동성: {stock['Volatility_%']:6.2f}%")
        
#         # 최적화 방법별 결과 비교
#         if optimizations:
#             print(f"\n📊 최적화 방법별 성과 비교:")
#             print("-" * 80)
#             print(f"{'방법':<20} {'샤프비율':<10} {'기대수익률':<12} {'변동성':<10} {'상태'}")
#             print("-" * 80)
            
#             for method, result_data in optimizations.items():
#                 if isinstance(result_data, dict) and 'sharpe_ratio' in result_data:
#                     status = "✅" if result_data.get('optimization_success', False) else "⚠️"
#                     print(f"{result_data['strategy']:<20} "
#                           f"{result_data['sharpe_ratio']:<10.3f} "
#                           f"{result_data['expected_return']*100:<12.2f}% "
#                           f"{result_data['volatility']*100:<10.2f}% "
#                           f"{status}")
        
#         # 추천 포트폴리오
#         if recommendation and 'portfolio' in recommendation:
#             recommended = recommendation['portfolio']
#             print(f"\n🏆 추천 포트폴리오: {recommended['strategy']}")
#             print("-" * 60)
#             print(f"📈 기대수익률: {recommended['expected_return']*100:.2f}%")
#             print(f"📉 변동성:     {recommended['volatility']*100:.2f}%")
#             print(f"⚡ 샤프비율:   {recommended['sharpe_ratio']:.3f}")
            
#             # 종목별 비중
#             print(f"\n💼 종목별 포트폴리오 비중:")
#             weights = recommended['weights']
#             sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
            
#             for symbol, weight in sorted_weights:
#                 print(f"  {symbol:<8}: {weight*100:>6.2f}%")
            
#             # 개선 효과
#             improvement = recommendation.get('improvement_vs_equal_weight', {})
#             if improvement:
#                 print(f"\n📈 균등비중 대비 개선 효과:")
#                 if 'sharpe_improvement' in improvement:
#                     print(f"  샤프비율 개선:   +{improvement['sharpe_improvement']:.3f}")
#                 if 'return_improvement' in improvement:
#                     print(f"  수익률 개선:     +{improvement['return_improvement']:.2f}%")
#                 if 'improvement_percentage' in improvement:
#                     print(f"  전체 개선율:     +{improvement['improvement_percentage']:.1f}%")
    
#     def export_to_excel(self, result: Dict, filename: str = None):
#         """결과를 엑셀 파일로 내보내기"""
        
#         if filename is None:
#             strategy_name = result.get('strategy_name', 'portfolio').replace(' ', '_')
#             filename = f"{strategy_name}_optimization_results.xlsx"
        
#         print(f"\n💾 결과를 {filename}에 저장 중...")
        
#         try:
#             with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                
#                 # 1. 선택된 종목 정보
#                 if 'selected_stocks' in result:
#                     stocks_df = pd.DataFrame(result['selected_stocks'])
#                     stocks_df.to_excel(writer, sheet_name='Selected_Stocks', index=False)
                
#                 # 2. 최적화 결과 요약
#                 optimization_summary = []
#                 if 'optimizations' in result:
#                     for method, opt_result in result['optimizations'].items():
#                         if isinstance(opt_result, dict) and 'sharpe_ratio' in opt_result:
#                             optimization_summary.append({
#                                 'Method': opt_result['strategy'],
#                                 'Sharpe_Ratio': opt_result['sharpe_ratio'],
#                                 'Expected_Return_%': opt_result['expected_return'] * 100,
#                                 'Volatility_%': opt_result['volatility'] * 100,
#                                 'Success': opt_result.get('optimization_success', False)
#                             })
                
#                 if optimization_summary:
#                     summary_df = pd.DataFrame(optimization_summary)
#                     summary_df.to_excel(writer, sheet_name='Optimization_Summary', index=False)
                
#                 # 3. 추천 포트폴리오 상세 비중
#                 if 'recommendation' in result and 'portfolio' in result['recommendation']:
#                     weights = result['recommendation']['portfolio']['weights']
#                     weights_df = pd.DataFrame(list(weights.items()), 
#                                             columns=['Symbol', 'Weight_%'])
#                     weights_df['Weight_%'] = weights_df['Weight_%'] * 100
#                     weights_df = weights_df.sort_values('Weight_%', ascending=False)
#                     weights_df.to_excel(writer, sheet_name='Recommended_Weights', index=False)
                
#                 # 4. 전체 최적화 상세 비중 (모든 방법)
#                 all_weights_data = []
#                 if 'optimizations' in result:
#                     for method, opt_result in result['optimizations'].items():
#                         if isinstance(opt_result, dict) and 'weights' in opt_result:
#                             for symbol, weight in opt_result['weights'].items():
#                                 all_weights_data.append({
#                                     'Method': opt_result['strategy'],
#                                     'Symbol': symbol,
#                                     'Weight_%': weight * 100
#                                 })
                
#                 if all_weights_data:
#                     all_weights_df = pd.DataFrame(all_weights_data)
#                     weights_pivot = all_weights_df.pivot(index='Symbol', 
#                                                        columns='Method', 
#                                                        values='Weight_%')
#                     weights_pivot.to_excel(writer, sheet_name='All_Methods_Weights')
            
#             print(f"✅ 결과가 성공적으로 {filename}에 저장되었습니다!")
            
#         except Exception as e:
#             print(f"❌ 파일 저장 중 오류 발생: {str(e)}")


# # Main 백테스터와의 통합 함수
# def integrate_with_main_backtester(backtest_results: List[Dict], 
#                                  stock_data: Dict, 
#                                  strategy_name: str,
#                                  top_n: int = 10) -> Dict:
#     """
#     Main 백테스터 결과와 통합하여 최적화 실행
    
#     Parameters:
#     -----------
#     backtest_results : List[Dict]
#         Main에서 실행된 백테스트 결과
#     stock_data : Dict
#         전체 주가 데이터 (Main의 sample_stocks)
#     strategy_name : str
#         선택된 전략 이름
#     top_n : int
#         상위 몇 개 종목을 선택할지
        
#     Returns:
#     --------
#     Dict
#         최적화 결과
#     """
    
#     print(f"\n🔗 Main 백테스터와 포트폴리오 최적화 통합 실행")
#     print(f"전략: {strategy_name}")
#     print(f"대상: 상위 {top_n}개 종목")
    
#     # 통합 최적화 실행
#     integrated_optimizer = IntegratedPortfolioOptimizer()
    
#     result = integrated_optimizer.optimize_strategy_portfolio(
#         backtest_results=backtest_results,
#         stock_data=stock_data,
#         strategy_name=strategy_name,
#         top_n=top_n
#     )
    
#     # 결과 출력
#     integrated_optimizer.display_optimization_results(result)
    
#     # 엑셀 저장
#     integrated_optimizer.export_to_excel(result)
    
#     return result


# # 사용 예시
# if __name__ == "__main__":
#     # 예시 데이터 (실제 Main에서 받아올 데이터 형태)
#     sample_backtest_results = [
#         {'Symbol': 'PORTFOLIO', 'Sharpe_Ratio': 1.2, 'Annual_Return_%': 15.5},
#         {'Symbol': 'AAPL', 'Sharpe_Ratio': 1.8, 'Annual_Return_%': 18.2, 'Volatility_%': 22.1},
#         {'Symbol': 'GOOGL', 'Sharpe_Ratio': 1.5, 'Annual_Return_%': 16.8, 'Volatility_%': 25.3},
#         {'Symbol': 'MSFT', 'Sharpe_Ratio': 1.4, 'Annual_Return_%': 14.9, 'Volatility_%': 20.7},
#         {'Symbol': 'AMZN', 'Sharpe_Ratio': 1.1, 'Annual_Return_%': 13.2, 'Volatility_%': 28.4},
#         {'Symbol': 'TSLA', 'Sharpe_Ratio': 0.9, 'Annual_Return_%': 12.1, 'Volatility_%': 35.2},
#     ]
    
#     # 샘플 주가 데이터
#     import numpy as np
    
#     sample_stock_data = {}
#     symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']
    
#     np.random.seed(42)
#     for symbol in symbols:
#         dates = pd.date_range(start='2023-01-01', periods=252, freq='D')
#         prices = 100 * np.cumprod(1 + np.random.normal(0.001, 0.02, 252))
#         sample_stock_data[symbol] = pd.DataFrame({
#             'Close': prices
#         }, index=dates)
    
#     # 통합 최적화 실행
#     result = integrate_with_main_backtester(
#         backtest_results=sample_backtest_results,
#         stock_data=sample_stock_data,
#         strategy_name="Sample Strategy",
#         top_n=5
#     )
    
#     print("\n🎉 통합 최적화 완료!")