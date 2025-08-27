"""
file: quant_mvp/utils/helpers.py
공통 유틸리티 함수들
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd
import numpy as np

def setup_logging(log_dir: str, level: int = logging.INFO):
    """로깅 설정"""
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    log_file = Path(log_dir) / f"quant_mvp_{datetime.now().strftime('%Y%m%d')}.log"
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def create_output_directories(config: Dict[str, Any]):
    """출력 디렉토리 생성"""
    dirs_to_create = [
        config['output']['reports_dir'],
        config['output']['charts_dir'],
        config['output']['logs_dir'],
        'outputs/portfolios'
    ]
    
    for dir_path in dirs_to_create:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

def format_currency(amount: float, currency: str = "USD") -> str:
    """통화 포맷팅"""
    if currency == "USD":
        return f"${amount:,.2f}"
    elif currency == "KRW":
        return f"₩{amount:,.0f}"
    else:
        return f"{amount:,.2f} {currency}"

def format_percentage(value: float, decimal_places: int = 2) -> str:
    """퍼센테지 포맷팅"""
    return f"{value * 100:.{decimal_places}f}%"

def format_number(value: float, decimal_places: int = 2) -> str:
    """숫자 포맷팅"""
    return f"{value:,.{decimal_places}f}"

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """안전한 나누기"""
    return numerator / denominator if denominator != 0 else default

def calculate_cagr(start_value: float, end_value: float, years: float) -> float:
    """연평균 성장률 계산"""
    if start_value <= 0 or end_value <= 0 or years <= 0:
        return 0.0
    return (end_value / start_value) ** (1 / years) - 1

def calculate_volatility(returns: pd.Series, annualize: bool = True) -> float:
    """변동성 계산"""
    vol = returns.std()
    return vol * np.sqrt(252) if annualize else vol

def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
    """샤프 비율 계산"""
    excess_returns = returns.mean() * 252 - risk_free_rate
    volatility = calculate_volatility(returns)
    return safe_divide(excess_returns, volatility)

def calculate_max_drawdown(cumulative_returns: pd.Series) -> float:
    """최대 낙폭 계산"""
    running_max = cumulative_returns.expanding().max()
    drawdown = (cumulative_returns - running_max) / running_max
    return drawdown.min()

def calculate_calmar_ratio(returns: pd.Series) -> float:
    """칼마 비율 계산"""
    annual_return = returns.mean() * 252
    cumulative = (1 + returns).cumprod()
    max_dd = abs(calculate_max_drawdown(cumulative))
    return safe_divide(annual_return, max_dd)

def validate_date_range(start_date: str, end_date: str) -> bool:
    """날짜 범위 검증"""
    try:
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        return start < end
    except:
        return False

def get_business_days(start_date: str, end_date: str) -> int:
    """영업일수 계산"""
    try:
        return len(pd.bdate_range(start_date, end_date))
    except:
        return 0

def clean_data(df: pd.DataFrame, fill_method: str = 'ffill') -> pd.DataFrame:
    """데이터 정제"""
    df_clean = df.copy()
    
    # 결측값 처리
    if fill_method == 'ffill':
        df_clean = df_clean.fillna(method='ffill')
    elif fill_method == 'bfill':
        df_clean = df_clean.fillna(method='bfill')
    elif fill_method == 'drop':
        df_clean = df_clean.dropna()
    
    # 무한값 제거
    df_clean = df_clean.replace([np.inf, -np.inf], np.nan)
    df_clean = df_clean.fillna(method='ffill')
    
    return df_clean

def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    """가중치 정규화"""
    total = sum(abs(w) for w in weights.values())
    if total == 0:
        return weights
    return {symbol: weight / total for symbol, weight in weights.items()}

def rebalance_portfolio(current_weights: Dict[str, float], 
                       target_weights: Dict[str, float],
                       threshold: float = 0.05) -> Dict[str, float]:
    """포트폴리오 리밸런싱 필요 여부 확인"""
    rebalance_needed = {}
    
    all_symbols = set(current_weights.keys()) | set(target_weights.keys())
    
    for symbol in all_symbols:
        current = current_weights.get(symbol, 0.0)
        target = target_weights.get(symbol, 0.0)
        
        if abs(current - target) > threshold:
            rebalance_needed[symbol] = target - current
    
    return rebalance_needed

def save_to_csv(data: pd.DataFrame, filepath: str, index: bool = True):
    """CSV 파일로 저장"""
    try:
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        data.to_csv(filepath, index=index, encoding='utf-8')
        return True
    except Exception as e:
        logging.error(f"Failed to save CSV {filepath}: {e}")
        return False

def load_from_csv(filepath: str, index_col: str = None) -> pd.DataFrame:
    """CSV 파일에서 로드"""
    try:
        return pd.read_csv(filepath, index_col=index_col, parse_dates=True)
    except Exception as e:
        logging.error(f"Failed to load CSV {filepath}: {e}")
        return pd.DataFrame()

class ProgressBar:
    """간단한 진행률 표시"""
    
    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description
    
    def update(self, increment: int = 1):
        """진행률 업데이트"""
        self.current += increment
        percent = (self.current / self.total) * 100
        bar_length = 40
        filled_length = int(bar_length * self.current // self.total)
        
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        print(f'\r{self.description}: |{bar}| {percent:.1f}%', end='')
        
        if self.current >= self.total:
            print()  # 새 줄