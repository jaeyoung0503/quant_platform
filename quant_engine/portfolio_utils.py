"""
Portfolio Utilities Module - 포트폴리오 관리 유틸리티
리밸런싱, 가중치 계산, 포트폴리오 최적화 관련 함수들 250여 라인
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union
import scipy.optimize as sco
from scipy import linalg
import warnings

# 포트폴리오 가중치 계산
def equal_weight_portfolio(symbols: List[str]) -> Dict[str, float]:
    """동일 가중치 포트폴리오"""
    if not symbols:
        return {}
    
    weight = 1.0 / len(symbols)
    return {symbol: weight for symbol in symbols}

def market_cap_weighted_portfolio(symbols: List[str], market_caps: Dict[str, float]) -> Dict[str, float]:
    """시가총액 가중 포트폴리오"""
    total_market_cap = sum(market_caps.get(symbol, 0) for symbol in symbols)
    
    if total_market_cap == 0:
        return equal_weight_portfolio(symbols)
    
    return {symbol: market_caps.get(symbol, 0) / total_market_cap for symbol in symbols}

def inverse_volatility_weighted_portfolio(returns: pd.DataFrame) -> Dict[str, float]:
    """역변동성 가중 포트폴리오"""
    volatilities = returns.std()
    
    # 0으로 나누기 방지
    volatilities = volatilities.replace(0, volatilities.mean())
    
    inverse_vol = 1 / volatilities
    total_inverse_vol = inverse_vol.sum()
    
    return (inverse_vol / total_inverse_vol).to_dict()

def risk_parity_portfolio(returns: pd.DataFrame, method: str = 'naive') -> Dict[str, float]:
    """리스크 패리티 포트폴리오"""
    if method == 'naive':
        return inverse_volatility_weighted_portfolio(returns)
    
    # 고급 리스크 패리티 (각 자산의 리스크 기여도 동일)
    cov_matrix = returns.cov().values
    n_assets = len(returns.columns)
    
    def risk_budget_objective(weights, cov_matrix):
        portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
        marginal_contrib = np.dot(cov_matrix, weights) / portfolio_vol
        contrib = np.multiply(marginal_contrib, weights)
        
        # 각 자산의 리스크 기여도가 동일하도록
        target_contrib = portfolio_vol / n_assets
        return np.sum(np.square(contrib - target_contrib))
    
    # 제약조건
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    bounds = tuple((0.01, 0.5) for _ in range(n_assets))  # 1%-50% 제한
    
    # 초기값
    x0 = np.array([1/n_assets] * n_assets)
    
    try:
        result = sco.minimize(risk_budget_objective, x0, args=(cov_matrix,),
                             method='SLSQP', bounds=bounds, constraints=constraints)
        
        if result.success:
            return dict(zip(returns.columns, result.x))
        else:
            return inverse_volatility_weighted_portfolio(returns)
    except:
        return inverse_volatility_weighted_portfolio(returns)

def minimum_variance_portfolio(returns: pd.DataFrame) -> Dict[str, float]:
    """최소분산 포트폴리오"""
    cov_matrix = returns.cov().values
    n_assets = len(returns.columns)
    
    # 목적함수: 포트폴리오 분산 최소화
    def portfolio_variance(weights, cov_matrix):
        return np.dot(weights, np.dot(cov_matrix, weights))
    
    # 제약조건
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    bounds = tuple((0, 1) for _ in range(n_assets))
    
    # 초기값
    x0 = np.array([1/n_assets] * n_assets)
    
    try:
        result = sco.minimize(portfolio_variance, x0, args=(cov_matrix,),
                             method='SLSQP', bounds=bounds, constraints=constraints)
        
        if result.success:
            return dict(zip(returns.columns, result.x))
        else:
            return equal_weight_portfolio(returns.columns.tolist())
    except:
        return equal_weight_portfolio(returns.columns.tolist())

def maximum_diversification_portfolio(returns: pd.DataFrame) -> Dict[str, float]:
    """최대분산효과 포트폴리오"""
    cov_matrix = returns.cov().values
    volatilities = returns.std().values
    n_assets = len(returns.columns)
    
    def diversification_ratio(weights, cov_matrix, volatilities):
        portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
        weighted_avg_vol = np.dot(weights, volatilities)
        return -weighted_avg_vol / portfolio_vol  # 음수로 최대화를 최소화로 변환
    
    # 제약조건
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    bounds = tuple((0, 1) for _ in range(n_assets))
    
    # 초기값
    x0 = np.array([1/n_assets] * n_assets)
    
    try:
        result = sco.minimize(diversification_ratio, x0, 
                             args=(cov_matrix, volatilities),
                             method='SLSQP', bounds=bounds, constraints=constraints)
        
        if result.success:
            return dict(zip(returns.columns, result.x))
        else:
            return equal_weight_portfolio(returns.columns.tolist())
    except:
        return equal_weight_portfolio(returns.columns.tolist())

# 리밸런싱 함수들
def calculate_rebalancing_trades(current_weights: Dict[str, float], 
                                target_weights: Dict[str, float],
                                portfolio_value: float,
                                threshold: float = 0.05) -> Dict[str, Dict]:
    """리밸런싱 거래 계산"""
    trades = {}
    
    # 모든 종목 리스트
    all_symbols = set(current_weights.keys()) | set(target_weights.keys())
    
    for symbol in all_symbols:
        current_weight = current_weights.get(symbol, 0.0)
        target_weight = target_weights.get(symbol, 0.0)
        weight_diff = target_weight - current_weight
        
        # 임계값 이상의 차이만 거래
        if abs(weight_diff) > threshold:
            current_value = current_weight * portfolio_value
            target_value = target_weight * portfolio_value
            trade_value = target_value - current_value
            
            trades[symbol] = {
                'current_weight': current_weight,
                'target_weight': target_weight,
                'weight_diff': weight_diff,
                'current_value': current_value,
                'target_value': target_value,
                'trade_value': trade_value,
                'trade_type': 'BUY' if trade_value > 0 else 'SELL'
            }
    
    return trades

def optimize_rebalancing_frequency(returns: pd.DataFrame, 
                                  target_weights: pd.Series,
                                  transaction_cost: float = 0.001) -> Dict:
    """최적 리밸런싱 빈도 계산"""
    frequencies = [1, 5, 21, 63, 126, 252]  # 일, 주, 월, 분기, 반기, 연
    results = {}
    
    for freq in frequencies:
        # 해당 빈도로 리밸런싱했을 때의 성과 계산
        rebalanced_returns = simulate_rebalanced_returns(
            returns, target_weights, freq, transaction_cost
        )
        
        total_return = (1 + rebalanced_returns).prod() - 1
        volatility = rebalanced_returns.std() * np.sqrt(252)
        sharpe_ratio = (rebalanced_returns.mean() * 252) / (rebalanced_returns.std() * np.sqrt(252))
        
        results[freq] = {
            'frequency_days': freq,
            'total_return': total_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'total_transactions': len(returns) // freq
        }
    
    # 샤프 비율 기준 최적 빈도 선택
    optimal_freq = max(results.keys(), key=lambda x: results[x]['sharpe_ratio'])
    
    return {
        'optimal_frequency': optimal_freq,
        'results': results
    }

def simulate_rebalanced_returns(returns: pd.DataFrame, 
                               target_weights: pd.Series,
                               rebalance_frequency: int,
                               transaction_cost: float = 0.001) -> pd.Series:
    """리밸런싱 시뮬레이션"""
    portfolio_returns = []
    current_weights = target_weights.copy()
    
    for i in range(len(returns)):
        # 일일 수익률 계산
        daily_return = (returns.iloc[i] * current_weights).sum()
        portfolio_returns.append(daily_return)
        
        # 가중치 업데이트 (수익률에 따른 자연적 변화)
        current_weights = current_weights * (1 + returns.iloc[i])
        current_weights = current_weights / current_weights.sum()
        
        # 리밸런싱 시점
        if (i + 1) % rebalance_frequency == 0:
            # 거래비용 차감
            rebalancing_cost = transaction_cost * np.sum(np.abs(current_weights - target_weights))
            portfolio_returns[-1] -= rebalancing_cost
            
            # 목표 가중치로 리밸런싱
            current_weights = target_weights.copy()
    
    return pd.Series(portfolio_returns, index=returns.index)

# 포트폴리오 성과 측정
def calculate_portfolio_metrics(returns: pd.Series, 
                               benchmark_returns: Optional[pd.Series] = None,
                               risk_free_rate: float = 0.02) -> Dict[str, float]:
    """포트폴리오 성과 지표 계산"""
    metrics = {}
    
    if len(returns) == 0:
        return metrics
    
    # 기본 지표
    metrics['total_return'] = (1 + returns).prod() - 1
    metrics['annualized_return'] = (1 + returns.mean()) ** 252 - 1
    metrics['volatility'] = returns.std() * np.sqrt(252)
    metrics['sharpe_ratio'] = (metrics['annualized_return'] - risk_free_rate) / metrics['volatility']
    
    # 하방 위험 지표
    downside_returns = returns[returns < 0]
    if len(downside_returns) > 0:
        metrics['downside_volatility'] = downside_returns.std() * np.sqrt(252)
        metrics['sortino_ratio'] = (metrics['annualized_return'] - risk_free_rate) / metrics['downside_volatility']
    else:
        metrics['downside_volatility'] = 0
        metrics['sortino_ratio'] = float('inf')
    
    # 최대 낙폭
    cumulative_returns = (1 + returns).cumprod()
    running_max = cumulative_returns.expanding().max()
    drawdown = (cumulative_returns - running_max) / running_max
    metrics['max_drawdown'] = drawdown.min()
    
    # VaR
    metrics['var_95'] = returns.quantile(0.05)
    metrics['cvar_95'] = returns[returns <= metrics['var_95']].mean()
    
    # 승률
    metrics['win_rate'] = (returns > 0).mean()
    
    # 벤치마크 대비 지표
    if benchmark_returns is not None and len(benchmark_returns) == len(returns):
        excess_returns = returns - benchmark_returns
        metrics['alpha'] = excess_returns.mean() * 252
        
        # 베타 계산
        covariance = np.cov(returns, benchmark_returns)[0, 1]
        benchmark_variance = benchmark_returns.var()
        metrics['beta'] = covariance / benchmark_variance if benchmark_variance != 0 else 0
        
        # 정보비율
        tracking_error = excess_returns.std() * np.sqrt(252)
        metrics['information_ratio'] = metrics['alpha'] / tracking_error if tracking_error != 0 else 0
    
    return metrics

def calculate_risk_attribution(returns: pd.DataFrame, weights: pd.Series) -> Dict[str, float]:
    """리스크 기여도 분석"""
    cov_matrix = returns.cov()
    portfolio_variance = np.dot(weights, np.dot(cov_matrix, weights))
    portfolio_volatility = np.sqrt(portfolio_variance)
    
    # 한계 기여도
    marginal_contrib = np.dot(cov_matrix, weights) / portfolio_volatility
    
    # 개별 기여도
    contrib = weights * marginal_contrib
    
    # 백분율로 변환
    risk_attribution = (contrib / portfolio_variance).to_dict()
    
    return risk_attribution

def calculate_performance_attribution(returns: pd.DataFrame, 
                                    weights: pd.Series,
                                    benchmark_returns: pd.Series) -> Dict[str, Dict[str, float]]:
    """성과 기여도 분석"""
    attribution = {}
    
    # 포트폴리오 수익률
    portfolio_returns = (returns * weights).sum(axis=1)
    
    for asset in returns.columns:
        asset_return = returns[asset].mean() * 252
        benchmark_return = benchmark_returns.mean() * 252
        weight = weights[asset]
        
        # 자산 선택 효과
        selection_effect = (asset_return - benchmark_return) * weight
        
        # 가중치 효과 (벤치마크 가중치가 있다면)
        # 여기서는 동일가중치를 벤치마크로 가정
        benchmark_weight = 1 / len(returns.columns)
        allocation_effect = (weight - benchmark_weight) * benchmark_return
        
        attribution[asset] = {
            'selection_effect': selection_effect,
            'allocation_effect': allocation_effect,
            'total_contribution': selection_effect + allocation_effect
        }
    
    return attribution

# 포트폴리오 최적화 유틸리티
def efficient_frontier(returns: pd.DataFrame, 
                      n_portfolios: int = 100) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """효율적 프론티어 계산"""
    n_assets = len(returns.columns)
    mean_returns = returns.mean() * 252
    cov_matrix = returns.cov() * 252
    
    # 목표 수익률 범위
    min_ret = mean_returns.min()
    max_ret = mean_returns.max()
    target_returns = np.linspace(min_ret, max_ret, n_portfolios)
    
    efficient_portfolios = []
    
    for target_return in target_returns:
        # 목적함수: 분산 최소화
        def portfolio_variance(weights):
            return np.dot(weights, np.dot(cov_matrix, weights))
        
        # 제약조건
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # 가중치 합 = 1
            {'type': 'eq', 'fun': lambda x: np.dot(x, mean_returns) - target_return}  # 목표 수익률
        ]
        bounds = tuple((0, 1) for _ in range(n_assets))
        
        # 최적화
        result = sco.minimize(portfolio_variance, 
                             np.array([1/n_assets] * n_assets),
                             method='SLSQP', 
                             bounds=bounds, 
                             constraints=constraints)
        
        if result.success:
            efficient_portfolios.append(result.x)
        else:
            efficient_portfolios.append(np.array([1/n_assets] * n_assets))
    
    efficient_portfolios = np.array(efficient_portfolios)
    
    # 효율적 프론티어의 수익률과 위험
    frontier_returns = np.array([np.dot(weights, mean_returns) 
                                for weights in efficient_portfolios])
    frontier_volatility = np.array([np.sqrt(np.dot(weights, np.dot(cov_matrix, weights))) 
                                   for weights in efficient_portfolios])
    
    return efficient_portfolios, frontier_returns, frontier_volatility

def black_litterman_optimization(returns: pd.DataFrame,
                                 market_caps: pd.Series,
                                 views: Dict[str, float] = None,
                                 view_confidence: float = 0.25) -> Dict[str, float]:
    """블랙-리터만 모델"""
    # 시장 균형 수익률 (CAPM 기반)
    market_weights = market_caps / market_caps.sum()
    cov_matrix = returns.cov() * 252
    risk_aversion = 3.0  # 일반적인 위험회피계수
    
    # 암시 수익률
    implied_returns = risk_aversion * np.dot(cov_matrix, market_weights)
    
    if views is None:
        # 뷰가 없으면 시장 포트폴리오 반환
        return market_weights.to_dict()
    
    # 뷰 행렬 구성
    P = np.zeros((len(views), len(returns.columns)))
    Q = np.zeros(len(views))
    
    for i, (asset, view_return) in enumerate(views.items()):
        if asset in returns.columns:
            asset_idx = returns.columns.get_loc(asset)
            P[i, asset_idx] = 1
            Q[i] = view_return
    
    # 뷰의 불확실성 행렬
    omega = view_confidence * np.dot(P, np.dot(cov_matrix, P.T))
    
    # 사전 불확실성
    tau = 1 / len(returns)
    
    try:
        # 블랙-리터만 수익률
        M1 = linalg.inv(tau * cov_matrix)
        M2 = np.dot(P.T, np.dot(linalg.inv(omega), P))
        M3 = np.dot(linalg.inv(tau * cov_matrix), implied_returns)
        M4 = np.dot(P.T, np.dot(linalg.inv(omega), Q))
        
        mu_bl = np.dot(linalg.inv(M1 + M2), M3 + M4)
        cov_bl = linalg.inv(M1 + M2)
        
        # 최적 가중치
        optimal_weights = np.dot(linalg.inv(risk_aversion * cov_bl), mu_bl)
        
        # 정규화
        optimal_weights = optimal_weights / optimal_weights.sum()
        
        return dict(zip(returns.columns, optimal_weights))
    
    except:
        # 계산 실패시 시장 포트폴리오 반환
        return market_weights.to_dict()

def kelly_criterion_weights(expected_returns: pd.Series, 
                           covariance_matrix: pd.DataFrame,
                           max_leverage: float = 1.0) -> Dict[str, float]:
    """켈리 기준 포지션 사이징"""
    try:
        # 켈리 공식: f = (μ - r) / σ²
        # 다자산의 경우: f = Σ^(-1) * (μ - r)
        risk_free_rate = 0.02 / 252  # 일일 무위험수익률
        excess_returns = expected_returns - risk_free_rate
        
        # 공분산 행렬의 역행렬
        inv_cov = linalg.inv(covariance_matrix.values)
        
        # 켈리 가중치
        kelly_weights = np.dot(inv_cov, excess_returns.values)
        
        # 레버리지 제한
        total_leverage = np.abs(kelly_weights).sum()
        if total_leverage > max_leverage:
            kelly_weights = kelly_weights * (max_leverage / total_leverage)
        
        # 음수 가중치를 0으로 설정 (롱온리)
        kelly_weights = np.maximum(kelly_weights, 0)
        
        # 정규화
        if kelly_weights.sum() > 0:
            kelly_weights = kelly_weights / kelly_weights.sum()
        else:
            kelly_weights = np.ones(len(expected_returns)) / len(expected_returns)
        
        return dict(zip(expected_returns.index, kelly_weights))
    
    except:
        # 계산 실패시 동일가중치 반환
        return equal_weight_portfolio(expected_returns.index.tolist()) 
