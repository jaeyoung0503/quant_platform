"""
file: quant_mvp/utils/visualizer.py
결과 시각화 및 리포트 생성
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import seaborn as sns
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import logging

from .helpers import format_currency, format_percentage, format_number

logger = logging.getLogger(__name__)

class ResultVisualizer:
    """결과 시각화 클래스"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.output_dir = Path(config['output']['charts_dir'])
        self.reports_dir = Path(config['output']['reports_dir'])
        
        # 스타일 설정
        plt.style.use('default')
        sns.set_palette("husl")
        
        # 출력 디렉토리 생성
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_complete_report(self, backtest_results: Dict[str, Any], 
                               strategy_config: Dict[str, Any],
                               title: str = "Backtest Report") -> Optional[str]:
        """완전한 백테스트 리포트 생성"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"{title.replace(' ', '_')}_{timestamp}.html"
            report_path = self.reports_dir / report_filename
            
            # HTML 리포트 생성
            html_content = self._generate_html_report(
                backtest_results, strategy_config, title
            )
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Complete report generated: {report_path}")
            return str(report_path.absolute())
            
        except Exception as e:
            logger.error(f"Error generating complete report: {e}")
            return None
    
    def _generate_html_report(self, backtest_results: Dict[str, Any],
                            strategy_config: Dict[str, Any],
                            title: str) -> str:
        """HTML 리포트 생성"""
        
        # 성과 데이터 준비
        performance = backtest_results.get('performance_summary', {})
        portfolio_values = backtest_results.get('backtest_results', {}).get('portfolio_values', [])
        
        # 차트 생성
        performance_chart = self._create_performance_chart(portfolio_values)
        drawdown_chart = self._create_drawdown_chart(portfolio_values)
        monthly_returns_chart = self._create_monthly_returns_heatmap(portfolio_values)
        
        html_template = f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background-color: white;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    padding: 30px;
                }}
                h1 {{
                    color: #2c3e50;
                    text-align: center;
                    border-bottom: 3px solid #3498db;
                    padding-bottom: 10px;
                }}
                h2 {{
                    color: #34495e;
                    margin-top: 40px;
                    margin-bottom: 20px;
                }}
                .metrics-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin: 30px 0;
                }}
                .metric-card {{
                    background-color: #ecf0f1;
                    padding: 20px;
                    border-radius: 8px;
                    border-left: 4px solid #3498db;
                }}
                .metric-title {{
                    font-size: 14px;
                    color: #7f8c8d;
                    margin-bottom: 5px;
                }}
                .metric-value {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #2c3e50;
                }}
                .positive {{ color: #27ae60; }}
                .negative {{ color: #e74c3c; }}
                .chart-container {{
                    margin: 30px 0;
                    padding: 20px;
                    background-color: #fafafa;
                    border-radius: 8px;
                }}
                .strategy-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                .strategy-table th, .strategy-table td {{
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}
                .strategy-table th {{
                    background-color: #34495e;
                    color: white;
                }}
                .footer {{
                    margin-top: 50px;
                    text-align: center;
                    color: #7f8c8d;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 {title}</h1>
                
                {self._generate_summary_section(performance, strategy_config)}
                
                <h2>📈 성과 차트</h2>
                <div class="chart-container">
                    <div id="performance-chart"></div>
                </div>
                
                <h2>📉 낙폭 분석</h2>
                <div class="chart-container">
                    <div id="drawdown-chart"></div>
                </div>
                
                <h2>🗓️ 월별 수익률</h2>
                <div class="chart-container">
                    <div id="monthly-returns-chart"></div>
                </div>
                
                {self._generate_strategy_details_section(strategy_config)}
                
                {self._generate_detailed_metrics_section(performance)}
                
                <div class="footer">
                    <p>Generated by Quant Strategy MVP on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </div>
            
            <script>
                {performance_chart}
                {drawdown_chart}
                {monthly_returns_chart}
            </script>
        </body>
        </html>
        """
        
        return html_template
    
    def _generate_summary_section(self, performance: Dict[str, Any], 
                                strategy_config: Dict[str, Any]) -> str:
        """요약 섹션 생성"""
        
        total_return = performance.get('total_return', 0)
        annual_return = performance.get('annual_return', 0)
        volatility = performance.get('annual_volatility', 0)
        sharpe_ratio = performance.get('sharpe_ratio', 0)
        max_drawdown = performance.get('max_drawdown', 0)
        win_rate = performance.get('win_rate', 0)
        
        return f"""
        <h2>📋 투자 개요</h2>
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-title">투자 금액</div>
                <div class="metric-value">{format_currency(strategy_config.get('investment_amount', 0))}</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">백테스트 기간</div>
                <div class="metric-value">{strategy_config.get('start_date', '')} ~ {strategy_config.get('end_date', '')}</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">전략 수</div>
                <div class="metric-value">{len(strategy_config.get('strategies', []))}</div>
            </div>
        </div>
        
        <h2>🎯 핵심 성과 지표</h2>
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-title">총 수익률</div>
                <div class="metric-value {'positive' if total_return > 0 else 'negative'}">{format_percentage(total_return)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">연평균 수익률</div>
                <div class="metric-value {'positive' if annual_return > 0 else 'negative'}">{format_percentage(annual_return)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">변동성</div>
                <div class="metric-value">{format_percentage(volatility)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">샤프 비율</div>
                <div class="metric-value {'positive' if sharpe_ratio > 0 else 'negative'}">{format_number(sharpe_ratio)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">최대 낙폭</div>
                <div class="metric-value negative">{format_percentage(max_drawdown)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">승률</div>
                <div class="metric-value">{format_percentage(win_rate)}</div>
            </div>
        </div>
        """
    
    def _generate_strategy_details_section(self, strategy_config: Dict[str, Any]) -> str:
        """전략 세부 정보 섹션"""
        
        strategies = strategy_config.get('strategies', [])
        parameters = strategy_config.get('parameters', {})
        
        strategy_rows = ""
        for strategy in strategies:
            name = strategy.get('name', '')
            weight = strategy.get('weight', 0)
            category = strategy.get('category', '')
            
            # 주요 파라미터 (최대 3개)
            strategy_params = parameters.get(name, {})
            param_items = []
            for i, (param, value) in enumerate(strategy_params.items()):
                if i >= 3 or param == 'description':
                    break
                if isinstance(value, float):
                    param_items.append(f"{param}: {value:.2f}")
                else:
                    param_items.append(f"{param}: {value}")
            
            param_str = ", ".join(param_items) if param_items else "기본값"
            
            strategy_rows += f"""
            <tr>
                <td>{name}</td>
                <td>{format_percentage(weight)}</td>
                <td>{category}</td>
                <td>{param_str}</td>
            </tr>
            """
        
        return f"""
        <h2>🎯 전략 구성</h2>
        <table class="strategy-table">
            <thead>
                <tr>
                    <th>전략명</th>
                    <th>가중치</th>
                    <th>카테고리</th>
                    <th>주요 파라미터</th>
                </tr>
            </thead>
            <tbody>
                {strategy_rows}
            </tbody>
        </table>
        """
    
    def _generate_detailed_metrics_section(self, performance: Dict[str, Any]) -> str:
        """상세 지표 섹션"""
        
        risk_metrics = [
            ('소티노 비율', performance.get('sortino_ratio', 0), 'ratio'),
            ('칼마 비율', performance.get('calmar_ratio', 0), 'ratio'),
            ('하방 변동성', performance.get('downside_volatility', 0), 'percentage'),
            ('VaR (95%)', performance.get('var_95', 0), 'percentage'),
            ('손익 비율', performance.get('profit_factor', 0), 'ratio'),
            ('최대 연속 손실', performance.get('max_consecutive_losses', 0), 'number')
        ]
        
        metrics_html = ""
        for i in range(0, len(risk_metrics), 3):
            metrics_html += '<div class="metrics-grid">'
            for j in range(3):
                if i + j < len(risk_metrics):
                    name, value, metric_type = risk_metrics[i + j]
                    if metric_type == 'percentage':
                        formatted_value = format_percentage(value)
                    elif metric_type == 'ratio':
                        formatted_value = format_number(value)
                    else:
                        formatted_value = str(int(value))
                    
                    metrics_html += f"""
                    <div class="metric-card">
                        <div class="metric-title">{name}</div>
                        <div class="metric-value">{formatted_value}</div>
                    </div>
                    """
            metrics_html += '</div>'
        
        return f"""
        <h2>📊 상세 위험 지표</h2>
        {metrics_html}
        """
    
    def _create_performance_chart(self, portfolio_values: List[Dict]) -> str:
        """성과 차트 생성 (JavaScript)"""
        if not portfolio_values:
            return "Plotly.newPlot('performance-chart', [], {title: '데이터 없음'});"
        
        dates = [pv['date'].strftime('%Y-%m-%d') for pv in portfolio_values]
        values = [pv['total_value'] for pv in portfolio_values]
        
        # 수익률 계산
        initial_value = values[0]
        returns = [(v / initial_value - 1) * 100 for v in values]
        
        return f"""
        var trace1 = {{
            x: {dates},
            y: {returns},
            type: 'scatter',
            mode: 'lines',
            name: '포트폴리오 수익률',
            line: {{color: '#3498db', width: 2}}
        }};
        
        var layout = {{
            title: '포트폴리오 수익률 추이',
            xaxis: {{title: '날짜'}},
            yaxis: {{title: '수익률 (%)', tickformat: '.1f'}},
            hovermode: 'x unified',
            showlegend: true
        }};
        
        Plotly.newPlot('performance-chart', [trace1], layout);
        """
    
    def _create_drawdown_chart(self, portfolio_values: List[Dict]) -> str:
        """낙폭 차트 생성 (JavaScript)"""
        if not portfolio_values:
            return "Plotly.newPlot('drawdown-chart', [], {title: '데이터 없음'});"
        
        dates = [pv['date'].strftime('%Y-%m-%d') for pv in portfolio_values]
        values = [pv['total_value'] for pv in portfolio_values]
        
        # 낙폭 계산
        running_max = []
        current_max = values[0]
        for value in values:
            if value > current_max:
                current_max = value
            running_max.append(current_max)
        
        drawdowns = [(value - peak) / peak * 100 for value, peak in zip(values, running_max)]
        
        return f"""
        var trace1 = {{
            x: {dates},
            y: {drawdowns},
            type: 'scatter',
            mode: 'lines',
            name: '낙폭',
            fill: 'tozeroy',
            fillcolor: 'rgba(231, 76, 60, 0.3)',
            line: {{color: '#e74c3c', width: 2}}
        }};
        
        var layout = {{
            title: '포트폴리오 낙폭 분석',
            xaxis: {{title: '날짜'}},
            yaxis: {{title: '낙폭 (%)', tickformat: '.1f'}},
            hovermode: 'x unified',
            showlegend: true
        }};
        
        Plotly.newPlot('drawdown-chart', [trace1], layout);
        """
    
    def _create_monthly_returns_heatmap(self, portfolio_values: List[Dict]) -> str:
        """월별 수익률 히트맵 생성 (JavaScript)"""
        if not portfolio_values:
            return "Plotly.newPlot('monthly-returns-chart', [], {title: '데이터 없음'});"
        
        try:
            # 월별 수익률 계산
            df = pd.DataFrame(portfolio_values)
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
            
            # 월말 값만 추출
            monthly_values = df.resample('M')['total_value'].last()
            monthly_returns = monthly_values.pct_change().dropna()
            
            # 연도와 월로 분리
            years = monthly_returns.index.year.unique()
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            
            # 히트맵 데이터 구성
            heatmap_data = []
            for year in sorted(years):
                year_data = []
                for month in range(1, 13):
                    try:
                        value = monthly_returns[
                            (monthly_returns.index.year == year) & 
                            (monthly_returns.index.month == month)
                        ].iloc[0] * 100
                        year_data.append(round(value, 2))
                    except (IndexError, KeyError):
                        year_data.append(None)
                heatmap_data.append(year_data)
            
            return f"""
            var data = [{{
                z: {heatmap_data},
                x: {months},
                y: {list(sorted(years))},
                type: 'heatmap',
                colorscale: [
                    [0, '#d73027'],
                    [0.5, '#ffffbf'],
                    [1, '#1a9850']
                ],
                zmid: 0,
                text: {heatmap_data},
                texttemplate: "%{{text:.1f}}%",
                textfont: {{"size": 10}},
                hoverongaps: false
            }}];
            
            var layout = {{
                title: '월별 수익률 히트맵',
                xaxis: {{title: '월'}},
                yaxis: {{title: '연도'}},
                height: 400
            }};
            
            Plotly.newPlot('monthly-returns-chart', data, layout);
            """
            
        except Exception as e:
            logger.error(f"Error creating monthly returns heatmap: {e}")
            return "Plotly.newPlot('monthly-returns-chart', [], {title: '월별 데이터 생성 오류'});"
    
    def create_strategy_comparison_chart(self, strategy_results: Dict[str, Dict]) -> str:
        """전략 비교 차트 생성"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"strategy_comparison_{timestamp}.png"
            filepath = self.output_dir / filename
            
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('전략 성과 비교', fontsize=16, fontweight='bold')
            
            strategies = list(strategy_results.keys())
            
            # 1. 총 수익률 비교
            returns = [strategy_results[s].get('total_return', 0) * 100 for s in strategies]
            axes[0, 0].bar(strategies, returns, color='skyblue', alpha=0.7)
            axes[0, 0].set_title('총 수익률 (%)')
            axes[0, 0].set_ylabel('수익률 (%)')
            axes[0, 0].tick_params(axis='x', rotation=45)
            
            # 2. 샤프 비율 비교
            sharpe_ratios = [strategy_results[s].get('sharpe_ratio', 0) for s in strategies]
            axes[0, 1].bar(strategies, sharpe_ratios, color='lightcoral', alpha=0.7)
            axes[0, 1].set_title('샤프 비율')
            axes[0, 1].set_ylabel('샤프 비율')
            axes[0, 1].tick_params(axis='x', rotation=45)
            
            # 3. 최대 낙폭 비교
            max_drawdowns = [strategy_results[s].get('max_drawdown', 0) * 100 for s in strategies]
            axes[1, 0].bar(strategies, max_drawdowns, color='lightgreen', alpha=0.7)
            axes[1, 0].set_title('최대 낙폭 (%)')
            axes[1, 0].set_ylabel('낙폭 (%)')
            axes[1, 0].tick_params(axis='x', rotation=45)
            
            # 4. 변동성 비교
            volatilities = [strategy_results[s].get('annual_volatility', 0) * 100 for s in strategies]
            axes[1, 1].bar(strategies, volatilities, color='gold', alpha=0.7)
            axes[1, 1].set_title('연간 변동성 (%)')
            axes[1, 1].set_ylabel('변동성 (%)')
            axes[1, 1].tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Strategy comparison chart saved: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error creating strategy comparison chart: {e}")
            return None
    
    def create_portfolio_composition_chart(self, positions: Dict[str, float], 
                                         current_prices: Dict[str, float]) -> str:
        """포트폴리오 구성 차트 생성"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"portfolio_composition_{timestamp}.png"
            filepath = self.output_dir / filename
            
            # 포지션별 가치 계산
            values = {}
            total_value = 0
            
            for symbol, shares in positions.items():
                if symbol in current_prices and shares > 0:
                    value = shares * current_prices[symbol]
                    values[symbol] = value
                    total_value += value
            
            if not values:
                logger.warning("No portfolio positions to chart")
                return None
            
            # 비중 계산 및 정렬
            weights = {k: v/total_value for k, v in values.items()}
            sorted_weights = dict(sorted(weights.items(), key=lambda x: x[1], reverse=True))
            
            # 상위 10개만 표시, 나머지는 기타로 통합
            if len(sorted_weights) > 10:
                top_10 = dict(list(sorted_weights.items())[:10])
                others_weight = sum(list(sorted_weights.values())[10:])
                if others_weight > 0:
                    top_10['기타'] = others_weight
                chart_data = top_10
            else:
                chart_data = sorted_weights
            
            # 파이 차트 생성
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 8))
            
            # 파이 차트
            colors = plt.cm.Set3(np.linspace(0, 1, len(chart_data)))
            wedges, texts, autotexts = ax1.pie(
                chart_data.values(), 
                labels=chart_data.keys(),
                autopct='%1.1f%%',
                colors=colors,
                startangle=90
            )
            ax1.set_title('포트폴리오 구성 비중')
            
            # 막대 차트
            symbols = list(chart_data.keys())
            weights_list = list(chart_data.values())
            ax2.barh(symbols, [w*100 for w in weights_list], color=colors)
            ax2.set_xlabel('비중 (%)')
            ax2.set_title('포트폴리오 구성 상세')
            ax2.grid(axis='x', alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Portfolio composition chart saved: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error creating portfolio composition chart: {e}")
            return None
    
    def create_risk_return_scatter(self, strategy_results: Dict[str, Dict]) -> str:
        """위험-수익률 산점도 생성"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"risk_return_scatter_{timestamp}.png"
            filepath = self.output_dir / filename
            
            fig, ax = plt.subplots(figsize=(12, 8))
            
            returns = []
            volatilities = []
            strategy_names = []
            
            for strategy_name, results in strategy_results.items():
                annual_return = results.get('annual_return', 0) * 100
                annual_vol = results.get('annual_volatility', 0) * 100
                returns.append(annual_return)
                volatilities.append(annual_vol)
                strategy_names.append(strategy_name)
            
            # 산점도 그리기
            scatter = ax.scatter(volatilities, returns, 
                               s=100, alpha=0.7, 
                               c=range(len(strategy_names)), 
                               cmap='viridis')
            
            # 전략 이름 레이블 추가
            for i, name in enumerate(strategy_names):
                ax.annotate(name, (volatilities[i], returns[i]), 
                          xytext=(5, 5), textcoords='offset points',
                          fontsize=10, alpha=0.8)
            
            # 효율적 프론티어 근사선 (참고용)
            if len(volatilities) > 1:
                z = np.polyfit(volatilities, returns, 1)
                p = np.poly1d(z)
                ax.plot(sorted(volatilities), p(sorted(volatilities)), 
                       "--", alpha=0.5, color='red', 
                       label='추세선')
            
            ax.set_xlabel('연간 변동성 (%)')
            ax.set_ylabel('연간 수익률 (%)')
            ax.set_title('전략별 위험-수익률 분포')
            ax.grid(True, alpha=0.3)
            ax.legend()
            
            plt.tight_layout()
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Risk-return scatter plot saved: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error creating risk-return scatter plot: {e}")
            return None
    
    def save_results_to_csv(self, backtest_results: Dict[str, Any], 
                           strategy_config: Dict[str, Any]) -> List[str]:
        """결과를 CSV 파일로 저장"""
        saved_files = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # 포트폴리오 가치 히스토리
            portfolio_values = backtest_results.get('backtest_results', {}).get('portfolio_values', [])
            if portfolio_values:
                df_values = pd.DataFrame(portfolio_values)
                values_file = self.output_dir.parent / 'portfolios' / f'portfolio_values_{timestamp}.csv'
                values_file.parent.mkdir(exist_ok=True)
                df_values.to_csv(values_file, index=False)
                saved_files.append(str(values_file))
            
            # 거래 히스토리
            trade_history = backtest_results.get('trade_history', [])
            if trade_history:
                df_trades = pd.DataFrame(trade_history)
                trades_file = self.output_dir.parent / 'portfolios' / f'trade_history_{timestamp}.csv'
                df_trades.to_csv(trades_file, index=False)
                saved_files.append(str(trades_file))
            
            # 성과 지표
            performance = backtest_results.get('performance_summary', {})
            if performance:
                df_performance = pd.DataFrame([performance])
                perf_file = self.output_dir.parent / 'portfolios' / f'performance_summary_{timestamp}.csv'
                df_performance.to_csv(perf_file, index=False)
                saved_files.append(str(perf_file))
            
            logger.info(f"Results saved to CSV files: {len(saved_files)} files")
            
        except Exception as e:
            logger.error(f"Error saving results to CSV: {e}")
        
        return saved_files