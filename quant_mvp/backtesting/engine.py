"""
file: quant_mvp/backtesting/engine.py
백테스트 엔진 핵심 클래스
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

from data.data_loader import DataLoader
from strategies.strategy_combiner import StrategyCombiner
from .portfolio import Portfolio
from .metrics import PerformanceMetrics
from utils.helpers import ProgressBar

logger = logging.getLogger(__name__)

class BacktestEngine:
    """백테스트 실행 엔진"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_loader = DataLoader(config)
        self.strategy_combiner = StrategyCombiner(config)
        self.portfolio = None
        self.metrics = PerformanceMetrics(config)
        
        # 백테스트 상태
        self.current_date = None
        self.results = {}
        
    def run_backtest(self, strategy_config: Dict[str, Any]) -> Dict[str, Any]:
        """백테스트 실행"""
        try:
            logger.info("Starting backtest execution")
            
            # 1. 데이터 로드
            print("📊 데이터 로딩 중...")
            data = self._load_backtest_data(strategy_config)
            if data is None:
                logger.error("Failed to load backtest data")
                return None
            
            # 2. 포트폴리오 초기화
            print("💼 포트폴리오 초기화 중...")
            self.portfolio = Portfolio(
                initial_cash=strategy_config['investment_amount'],
                config=self.config
            )
            
            # 3. 전략 조합 초기화
            print("🎯 전략 조합 설정 중...")
            combined_strategy = self._setup_combined_strategy(strategy_config)
            if combined_strategy is None:
                logger.error("Failed to setup combined strategy")
                return None
            
            # 4. 백테스트 실행
            print("⚡ 백테스트 실행 중...")
            backtest_results = self._execute_backtest(data, combined_strategy, strategy_config)
            
            # 5. 성과 분석
            print("📈 성과 분석 중...")
            performance_results = self._analyze_performance(backtest_results)
            
            # 6. 최종 결과 구성
            final_results = {
                'strategy_config': strategy_config,
                'backtest_results': backtest_results,
                'performance_summary': performance_results,
                'portfolio_history': self.portfolio.get_history(),
                'trade_history': self.portfolio.get_trade_history(),
                'execution_time': datetime.now().isoformat()
            }
            
            logger.info("Backtest execution completed successfully")
            return final_results
            
        except Exception as e:
            logger.error(f"Backtest execution failed: {e}")
            print(f"❌ 백테스트 실행 중 오류: {e}")
            return None
    
    def _load_backtest_data(self, strategy_config: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """백테스트 데이터 로드"""
        try:
            start_date = strategy_config['start_date']
            end_date = strategy_config['end_date']
            
            # 가격 데이터와 재무 데이터 병합
            price_data = self.data_loader.load_price_data()
            financial_data = self.data_loader.load_financial_data()
            market_data = self.data_loader.load_market_data()
            
            # 날짜 범위 필터링
            price_data = price_data[
                (price_data['date'] >= start_date) & 
                (price_data['date'] <= end_date)
            ]
            
            if price_data.empty:
                logger.error("No price data available for the specified date range")
                return None
            
            # 재무 데이터와 병합
            merged_data = self.data_loader.merge_price_financial_data()
            merged_data = merged_data[
                (merged_data['date'] >= start_date) & 
                (merged_data['date'] <= end_date)
            ]
            
            logger.info(f"Loaded data: {len(merged_data)} records, "
                      f"{len(merged_data['symbol'].unique())} symbols")
            
            return merged_data
            
        except Exception as e:
            logger.error(f"Error loading backtest data: {e}")
            return None
    
    def _setup_combined_strategy(self, strategy_config: Dict[str, Any]) -> Optional[object]:
        """전략 조합 설정"""
        try:
            strategies = strategy_config['strategies']
            parameters = strategy_config.get('parameters', {})
            
            # 전략 인스턴스 생성
            strategy_instances = []
            for strategy_info in strategies:
                strategy_name = strategy_info['name']
                strategy_weight = strategy_info['weight']
                strategy_params = parameters.get(strategy_name, {})
                
                strategy_instance = self.strategy_combiner.create_strategy(
                    strategy_name, strategy_params
                )
                
                if strategy_instance is None:
                    logger.error(f"Failed to create strategy: {strategy_name}")
                    return None
                
                strategy_instances.append({
                    'strategy': strategy_instance,
                    'weight': strategy_weight,
                    'name': strategy_name
                })
            
            # 조합 전략 생성
            combined_strategy = self.strategy_combiner.combine_strategies(strategy_instances)
            return combined_strategy
            
        except Exception as e:
            logger.error(f"Error setting up combined strategy: {e}")
            return None
    
    def _execute_backtest(self, data: pd.DataFrame, combined_strategy: object, 
                        strategy_config: Dict[str, Any]) -> Dict[str, Any]:
        """백테스트 실행"""
        try:
            # 백테스트 기간 설정
            start_date = pd.to_datetime(strategy_config['start_date'])
            end_date = pd.to_datetime(strategy_config['end_date'])
            
            # 리밸런싱 주기 설정
            rebalancing_freq = strategy_config.get('rebalancing_freq', 'quarterly')
            rebalancing_dates = self._generate_rebalancing_dates(
                start_date, end_date, rebalancing_freq
            )
            
            # 일별 데이터 그룹화
            daily_data = data.groupby('date')
            trading_dates = sorted(daily_data.groups.keys())
            
            # 진행률 표시
            progress = ProgressBar(len(trading_dates), "백테스트 진행")
            
            # 백테스트 실행
            portfolio_values = []
            signals_history = []
            
            for i, current_date in enumerate(trading_dates):
                self.current_date = current_date
                day_data = daily_data.get_group(current_date)
                
                # 리밸런싱 날짜인지 확인
                is_rebalancing_date = any(
                    abs((current_date - rebal_date).days) <= 1 
                    for rebal_date in rebalancing_dates
                )
                
                if is_rebalancing_date or i == 0:  # 첫날 또는 리밸런싱 날짜
                    # 전략 신호 생성
                    signals = self._generate_daily_signals(day_data, combined_strategy)
                    
                    if signals:
                        signals_history.extend([
                            {**signal.__dict__, 'date': current_date} 
                            for signal in signals
                        ])
                        
                        # 포트폴리오 리밸런싱
                        self._execute_rebalancing(signals, day_data)
                
                # 포트폴리오 가치 업데이트
                portfolio_value = self._update_portfolio_value(day_data)
                portfolio_values.append({
                    'date': current_date,
                    'total_value': portfolio_value,
                    'cash': self.portfolio.cash,
                    'positions': self.portfolio.get_current_positions()
                })
                
                progress.update()
            
            return {
                'portfolio_values': portfolio_values,
                'signals_history': signals_history,
                'rebalancing_dates': rebalancing_dates,
                'trading_dates': trading_dates
            }
            
        except Exception as e:
            logger.error(f"Error executing backtest: {e}")
            raise
    
    def _generate_rebalancing_dates(self, start_date: pd.Timestamp, 
                                   end_date: pd.Timestamp, 
                                   frequency: str) -> List[pd.Timestamp]:
        """리밸런싱 날짜 생성"""
        rebalancing_dates = []
        
        if frequency == 'monthly':
            freq_str = 'MS'  # Month Start
        elif frequency == 'quarterly':
            freq_str = 'QS'  # Quarter Start
        elif frequency == 'yearly':
            freq_str = 'YS'  # Year Start
        else:
            freq_str = 'QS'  # 기본값
        
        date_range = pd.date_range(
            start=start_date, 
            end=end_date, 
            freq=freq_str
        )
        
        return date_range.tolist()
    
    def _generate_daily_signals(self, day_data: pd.DataFrame, 
                               combined_strategy: object) -> List[object]:
        """일별 전략 신호 생성"""
        try:
            # 과거 데이터 포함하여 전략에 전달 (최소 60일)
            lookback_days = 60
            end_date = day_data['date'].iloc[0]
            start_date = end_date - timedelta(days=lookback_days)
            
            # 전체 데이터에서 필요한 기간 추출
            historical_data = self.data_loader.load_price_data()
            historical_data = historical_data[
                (historical_data['date'] >= start_date) &
                (historical_data['date'] <= end_date)
            ]
            
            if len(historical_data) < 30:  # 최소 30일 데이터 필요
                return []
            
            # 전략 신호 생성
            signals = combined_strategy.generate_signals(historical_data)
            return signals
            
        except Exception as e:
            logger.error(f"Error generating daily signals: {e}")
            return []
    
    def _execute_rebalancing(self, signals: List[object], day_data: pd.DataFrame):
        """리밸런싱 실행"""
        try:
            if not signals:
                return
            
            # 현재 가격 정보
            current_prices = {}
            for _, row in day_data.iterrows():
                current_prices[row['symbol']] = row['close']
            
            # 목표 포지션 계산
            total_value = self.portfolio.get_total_value(current_prices)
            target_positions = {}
            
            for signal in signals:
                if signal.action == 'buy' and signal.symbol in current_prices:
                    target_value = total_value * signal.weight
                    target_shares = int(target_value / current_prices[signal.symbol])
                    
                    if target_shares > 0:
                        target_positions[signal.symbol] = target_shares
            
            # 포트폴리오 리밸런싱
            self.portfolio.rebalance_to_target(target_positions, current_prices)
            
        except Exception as e:
            logger.error(f"Error executing rebalancing: {e}")
    
    def _update_portfolio_value(self, day_data: pd.DataFrame) -> float:
        """포트폴리오 가치 업데이트"""
        try:
            current_prices = {}
            for _, row in day_data.iterrows():
                current_prices[row['symbol']] = row['close']
            
            return self.portfolio.get_total_value(current_prices)
            
        except Exception as e:
            logger.error(f"Error updating portfolio value: {e}")
            return 0.0
    
    def _analyze_performance(self, backtest_results: Dict[str, Any]) -> Dict[str, Any]:
        """성과 분석"""
        try:
            portfolio_values = backtest_results['portfolio_values']
            
            if not portfolio_values:
                return {}
            
            # 일별 수익률 계산
            values = [pv['total_value'] for pv in portfolio_values]
            dates = [pv['date'] for pv in portfolio_values]
            
            returns_series = pd.Series(values, index=dates).pct_change().dropna()
            
            # 성과 지표 계산
            performance_metrics = self.metrics.calculate_comprehensive_metrics(returns_series)
            
            # 추가 분석
            performance_metrics.update({
                'initial_value': values[0],
                'final_value': values[-1],
                'total_trades': len(self.portfolio.get_trade_history()),
                'trading_days': len(portfolio_values),
                'average_position_count': self._calculate_average_position_count(portfolio_values)
            })
            
            return performance_metrics
            
        except Exception as e:
            logger.error(f"Error analyzing performance: {e}")
            return {}
    
    def _calculate_average_position_count(self, portfolio_values: List[Dict]) -> float:
        """평균 포지션 수 계산"""
        try:
            position_counts = []
            for pv in portfolio_values:
                positions = pv.get('positions', {})
                position_counts.append(len([p for p in positions.values() if p > 0]))
            
            return np.mean(position_counts) if position_counts else 0
            
        except Exception as e:
            logger.error(f"Error calculating average position count: {e}")
            return 0
    
    def get_backtest_summary(self) -> Dict[str, Any]:
        """백테스트 요약 정보 반환"""
        if not self.results:
            return {}
        
        summary = {
            'execution_date': self.results.get('execution_time'),
            'strategy_count': len(self.results.get('strategy_config', {}).get('strategies', [])),
            'backtest_period': f"{self.results.get('strategy_config', {}).get('start_date')} - {self.results.get('strategy_config', {}).get('end_date')}",
            'total_trades': self.results.get('performance_summary', {}).get('total_trades', 0),
            'final_return': self.results.get('performance_summary', {}).get('total_return', 0)
        }
        
        return summary