"""
File: backtester/__init__.py
Backtester Package Initialization
"""

from .core import QuantBacktester
from .data_generator import DataGenerator
from .backtesting_engine import BacktestingEngine
from .portfolio_analyzer import PortfolioAnalyzer
from .visualizer import PortfolioVisualizer

__version__ = "2.0.0"
__author__ = "Quant Strategy Team"
__description__ = "Professional Quantitative Strategy Backtesting System"

__all__ = [
    'QuantBacktester',
    'DataGenerator', 
    'BacktestingEngine',
    'PortfolioAnalyzer',
    'PortfolioVisualizer'
]