#!/usr/bin/env python3
"""
백테스트 실행 스크립트
입력: JSON 파일 (전략ID, 파라미터, 시장데이터)
출력: JSON 파일 (백테스트 결과)
"""

import json
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# quant_engine 모듈 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'quant_engine'))

def load_input_data(input_file):
    """입력 데이터 로드"""
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise Exception(f"입력 파일 로드 실패: {str(e)}")

def prepare_market_data(market_data):
    """시장 데이터를 DataFrame으로 변환"""
    try:
        df = pd.DataFrame(market_data)
        
        # 날짜 컬럼이 있으면 인덱스로 설정
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
        
        # 필수 컬럼 확인
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in df.columns:
                df[col] = df.get('close', 100) + np.random.randn(len(df)) * 0.01
        
        return df
        
    except Exception as e:
        raise Exception(f"시장 데이터 준비 실패: {str(e)}")

def run_backtest(strategy_id, parameters, market_data):
    """백테스트 실행"""
    try:
        from strategy_factory import strategy_registry, initialize_strategy_system
        from portfolio_utils import calculate_portfolio_metrics
        
        # 전략 시스템 초기화
        initialize_strategy_system()
        
        # 전략 생성
        strategy = strategy_registry.create_strategy(strategy_id, **parameters)
        
        # 데이터 준비
        df = prepare_market_data(market_data)
        
        # 전략 실행
        signals = strategy.generate_signals(df)
        weights = strategy.calculate_weights(signals)
        
        # 포트폴리오 수익률 계산 (간단한 구현)
        portfolio_returns = calculate_simple_returns(df, weights)
        
        # 성과 지표 계산
        metrics = calculate_portfolio_metrics(portfolio_returns)
        
        # 결과 구성
        result = {
            'strategy_name': strategy.name,
            'symbol': 'PORTFOLIO',
            'totalReturn': float(metrics.get('total_return', 0) * 100),
            'annualReturn': float(metrics.get('annualized_return', 0) * 100),
            'volatility': float(metrics.get('volatility', 0) * 100),
            'sharpeRatio': float(metrics.get('sharpe_ratio', 0)),
            'sortinoRatio': float(metrics.get('sortino_ratio', 0)),
            'calmarRatio': float(metrics.get('sharpe_ratio', 0) * 0.8),  # 근사값
            'maxDrawdown': float(abs(metrics.get('max_drawdown', 0)) * 100),
            'winRate': float(metrics.get('win_rate', 0) * 100),
            'finalValue': float((1 + metrics.get('total_return', 0)) * 100000),
            'portfolioHistory': generate_portfolio_history(portfolio_returns),
            'components': [w.symbol for w in weights[:5]] if weights else [],
            'weights': {w.symbol: float(w.weight) for w in weights[:5]} if weights else {}
        }
        
        return result
        
    except Exception as e:
        raise Exception(f"백테스트 실행 실패: {str(e)}")

def calculate_simple_returns(df, weights):
    """간단한 포트폴리오 수익률 계산"""
    if not weights:
        # 가중치가 없으면 시장 평균 수익률 사용
        returns = df['close'].pct_change().dropna()
        return returns
    
    # 가중치 기반 포트폴리오 수익률
    portfolio_returns = pd.Series(index=df.index, dtype=float)
    
    # 간단한 구현: 동일 가중치로 가정
    equal_weight = 1.0 / len(weights)
    returns = df['close'].pct_change().dropna()
    
    return returns * equal_weight

def generate_portfolio_history(returns, initial_value=100000):
    """포트폴리오 가치 변화 히스토리 생성"""
    if len(returns) == 0:
        return [initial_value]
    
    cumulative = (1 + returns).cumprod()
    portfolio_values = (cumulative * initial_value).tolist()
    
    # 최대 1000개 포인트로 제한
    if len(portfolio_values) > 1000:
        step = len(portfolio_values) // 1000
        portfolio_values = portfolio_values[::step]
    
    return portfolio_values

def save_output(output_file, result):
    """결과를 JSON 파일로 저장"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise Exception(f"결과 파일 저장 실패: {str(e)}")

def main():
    if len(sys.argv) != 3:
        print("사용법: python backtest_runner.py <input_file> <output_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
        # 입력 데이터 로드
        input_data = load_input_data(input_file)
        
        strategy_id = input_data['strategy_id']
        parameters = input_data.get('parameters', {})
        market_data = input_data['market_data']
        
        # 백테스트 실행
        result = run_backtest(strategy_id, parameters, market_data)
        
        # 결과 저장
        save_output(output_file, result)
        
    except Exception as e:
        # 에러 결과 저장
        error_result = {
            'error': str(e),
            'strategy_name': input_data.get('strategy_id', 'Unknown'),
            'symbol': 'ERROR',
            'totalReturn': 0,
            'annualReturn': 0,
            'volatility': 0,
            'sharpeRatio': 0,
            'maxDrawdown': 0,
            'portfolioHistory': [100000]
        }
        
        save_output(output_file, error_result)
        sys.exit(1)

if __name__ == '__main__':
    main()