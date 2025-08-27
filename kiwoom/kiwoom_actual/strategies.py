"""
자동매매 전략 모듈
"""

import logging
import random
from typing import Dict, List, Any
from datetime import datetime, timedelta

class TradingStrategies:
    """매매 전략 클래스"""
    
    def __init__(self, trading_service):
        self.trading_service = trading_service
        self.logger = logging.getLogger(__name__)
    
    def momentum_strategy(self, stock_code: str) -> Dict[str, Any]:
        """모멘텀 전략"""
        try:
            stock_info = self.trading_service.get_stock_info(stock_code)
            
            if not stock_info:
                return {'success': False, 'error': '종목 정보를 가져올 수 없습니다'}
            
            change_rate = stock_info.get('change_rate', 0.0)
            current_price = stock_info.get('current_price', 0)
            
            # 모멘텀 전략 로직
            if change_rate > 3.0:  # 3% 이상 상승 시 매수 신호
                portfolio = self.trading_service.get_portfolio()
                
                # 이미 보유 중인지 확인
                is_holding = any(item['stock_code'] == stock_code for item in portfolio)
                
                if not is_holding:
                    # 매수 수량 계산 (100만원 기준)
                    target_amount = 1000000
                    quantity = target_amount // current_price
                    
                    if quantity > 0:
                        result = self.trading_service.place_buy_order(stock_code, quantity, current_price)
                        if result.get('success'):
                            return {
                                'success': True,
                                'action': 'buy',
                                'message': f'모멘텀 매수 신호: {stock_code} {quantity}주'
                            }
                
            elif change_rate < -3.0:  # 3% 이상 하락 시 매도 신호
                portfolio = self.trading_service.get_portfolio()
                
                for item in portfolio:
                    if item['stock_code'] == stock_code:
                        quantity = item['quantity']
                        result = self.trading_service.place_sell_order(stock_code, quantity, current_price)
                        if result.get('success'):
                            return {
                                'success': True,
                                'action': 'sell',
                                'message': f'모멘텀 매도 신호: {stock_code} {quantity}주'
                            }
            
            return {
                'success': True,
                'action': 'hold',
                'message': f'모멘텀 전략: 관망 (등락률 {change_rate:+.2f}%)'
            }
            
        except Exception as e:
            self.logger.error(f"모멘텀 전략 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def mean_reversion_strategy(self, stock_code: str) -> Dict[str, Any]:
        """평균회귀 전략"""
        try:
            stock_info = self.trading_service.get_stock_info(stock_code)
            
            if not stock_info:
                return {'success': False, 'error': '종목 정보를 가져올 수 없습니다'}
            
            current_price = stock_info.get('current_price', 0)
            high_price = stock_info.get('high_price', current_price)
            low_price = stock_info.get('low_price', current_price)
            
            # 일중 평균가 계산
            avg_price = (high_price + low_price) / 2
            
            # 평균회귀 전략 로직
            if current_price < avg_price * 0.98:  # 평균가 대비 2% 이상 하락
                portfolio = self.trading_service.get_portfolio()
                is_holding = any(item['stock_code'] == stock_code for item in portfolio)
                
                if not is_holding:
                    # 매수 신호
                    target_amount = 1000000
                    quantity = target_amount // current_price
                    
                    if quantity > 0:
                        result = self.trading_service.place_buy_order(stock_code, quantity, current_price)
                        if result.get('success'):
                            return {
                                'success': True,
                                'action': 'buy',
                                'message': f'평균회귀 매수: {stock_code} {quantity}주'
                            }
            
            elif current_price > avg_price * 1.02:  # 평균가 대비 2% 이상 상승
                portfolio = self.trading_service.get_portfolio()
                
                for item in portfolio:
                    if item['stock_code'] == stock_code:
                        quantity = item['quantity']
                        result = self.trading_service.place_sell_order(stock_code, quantity, current_price)
                        if result.get('success'):
                            return {
                                'success': True,
                                'action': 'sell',
                                'message': f'평균회귀 매도: {stock_code} {quantity}주'
                            }
            
            return {
                'success': True,
                'action': 'hold',
                'message': f'평균회귀 전략: 관망 (현재가 {current_price:,}원, 평균가 {avg_price:,.0f}원)'
            }
            
        except Exception as e:
            self.logger.error(f"평균회귀 전략 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def breakout_strategy(self, stock_code: str) -> Dict[str, Any]:
        """돌파 전략"""
        try:
            stock_info = self.trading_service.get_stock_info(stock_code)
            
            if not stock_info:
                return {'success': False, 'error': '종목 정보를 가져올 수 없습니다'}
            
            current_price = stock_info.get('current_price', 0)
            high_price = stock_info.get('high_price', current_price)
            low_price = stock_info.get('low_price', current_price)
            volume = stock_info.get('volume', 0)
            
            # 돌파 전략 로직
            price_range = high_price - low_price
            breakout_threshold = price_range * 0.1  # 일중 변동폭의 10%
            
            # 상향 돌파 확인
            if current_price >= high_price * 0.98 and volume > 1000000:  # 고가 근처 + 거래량 증가
                portfolio = self.trading_service.get_portfolio()
                is_holding = any(item['stock_code'] == stock_code for item in portfolio)
                
                if not is_holding:
                    target_amount = 1500000  # 돌파 전략은 좀 더 큰 금액
                    quantity = target_amount // current_price
                    
                    if quantity > 0:
                        result = self.trading_service.place_buy_order(stock_code, quantity, current_price)
                        if result.get('success'):
                            return {
                                'success': True,
                                'action': 'buy',
                                'message': f'상향돌파 매수: {stock_code} {quantity}주'
                            }
            
            # 하향 돌파 확인 (손절)
            elif current_price <= low_price * 1.02:  # 저가 근처
                portfolio = self.trading_service.get_portfolio()
                
                for item in portfolio:
                    if item['stock_code'] == stock_code:
                        quantity = item['quantity']
                        result = self.trading_service.place_sell_order(stock_code, quantity, current_price)
                        if result.get('success'):
                            return {
                                'success': True,
                                'action': 'sell',
                                'message': f'하향돌파 매도: {stock_code} {quantity}주'
                            }
            
            return {
                'success': True,
                'action': 'hold',
                'message': f'돌파 전략: 관망 (현재가 {current_price:,}원, 고가 {high_price:,}원)'
            }
            
        except Exception as e:
            self.logger.error(f"돌파 전략 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def risk_management_check(self, stock_code: str) -> Dict[str, Any]:
        """리스크 관리 체크"""
        try:
            return self.trading_service.apply_risk_management(stock_code)
            
        except Exception as e:
            self.logger.error(f"리스크 관리 체크 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def calculate_position_size(self, stock_code: str, target_amount: int) -> int:
        """포지션 크기 계산"""
        try:
            stock_info = self.trading_service.get_stock_info(stock_code)
            current_price = stock_info.get('current_price', 0)
            
            if current_price <= 0:
                return 0
            
            # 기본 수량 계산
            quantity = target_amount // current_price
            
            # 최대 포지션 크기 제한
            account_info = self.trading_service.get_account_info()
            total_asset = account_info.get('balance', 0) if account_info else 0
            
            max_position_value = total_asset * 0.1  # 총 자산의 10%
            max_quantity = max_position_value // current_price
            
            return min(quantity, max_quantity)
            
        except Exception as e:
            self.logger.error(f"포지션 크기 계산 오류: {e}")
            return 0
    
    def analyze_market_condition(self) -> Dict[str, Any]:
        """시장 상황 분석"""
        try:
            # 인기 종목들의 평균 등락률 계산
            popular_stocks = self.trading_service.get_popular_stocks()
            
            if not popular_stocks:
                return {'condition': 'unknown', 'message': '시장 데이터 부족'}
            
            total_change = sum(stock.get('change_rate', 0.0) for stock in popular_stocks)
            avg_change = total_change / len(popular_stocks)
            
            # 상승/하락 종목 수 계산
            rising_count = sum(1 for stock in popular_stocks if stock.get('change_rate', 0) > 0)
            falling_count = len(popular_stocks) - rising_count
            
            # 시장 상황 판단
            if avg_change > 1.0 and rising_count > falling_count:
                condition = 'bullish'
                message = '강세장 (적극적 매수 전략 권장)'
            elif avg_change < -1.0 and falling_count > rising_count:
                condition = 'bearish'
                message = '약세장 (방어적 전략 권장)'
            else:
                condition = 'neutral'
                message = '횡보장 (선별적 투자 권장)'
            
            return {
                'condition': condition,
                'avg_change_rate': avg_change,
                'rising_stocks': rising_count,
                'falling_stocks': falling_count,
                'total_stocks': len(popular_stocks),
                'message': message
            }
            
        except Exception as e:
            self.logger.error(f"시장 상황 분석 오류: {e}")
            return {'condition': 'error', 'message': f'분석 오류: {str(e)}'}
    
    def get_strategy_recommendation(self, stock_code: str) -> Dict[str, Any]:
        """전략 추천"""
        try:
            stock_info = self.trading_service.get_stock_info(stock_code)
            market_condition = self.analyze_market_condition()
            
            if not stock_info:
                return {'success': False, 'error': '종목 정보 부족'}
            
            change_rate = stock_info.get('change_rate', 0.0)
            volume = stock_info.get('volume', 0)
            
            recommendations = []
            
            # 시장 상황별 추천
            if market_condition['condition'] == 'bullish':
                if change_rate > 2.0:
                    recommendations.append("모멘텀 전략으로 추세 추종")
                elif change_rate < -2.0:
                    recommendations.append("평균회귀 전략으로 반등 기대")
            
            elif market_condition['condition'] == 'bearish':
                recommendations.append("방어적 포지션 유지")
                if change_rate < -5.0:
                    recommendations.append("과매도 구간에서 선별적 매수")
            
            else:  # neutral
                if volume > 2000000:
                    recommendations.append("거래량 증가로 돌파 전략 고려")
                else:
                    recommendations.append("횡보 구간에서 신중한 접근")
            
            return {
                'success': True,
                'stock_code': stock_code,
                'market_condition': market_condition['condition'],
                'recommendations': recommendations,
                'current_change_rate': change_rate,
                'volume': volume
            }
            
        except Exception as e:
            self.logger.error(f"전략 추천 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def backtest_strategy(self, strategy_name: str, stock_code: str, days: int = 30) -> Dict[str, Any]:
        """전략 백테스트 (모의)"""
        try:
            # 모의 백테스트 결과 생성
            initial_capital = 10000000  # 1천만원
            
            # 랜덤 수익률 생성 (실제로는 과거 데이터 사용)
            daily_returns = []
            cumulative_return = 1.0
            
            for day in range(days):
                # 전략별 수익률 특성
                if strategy_name == "momentum":
                    daily_return = random.gauss(0.002, 0.02)  # 평균 0.2%, 변동성 2%
                elif strategy_name == "mean_reversion":
                    daily_return = random.gauss(0.001, 0.015)  # 평균 0.1%, 변동성 1.5%
                elif strategy_name == "breakout":
                    daily_return = random.gauss(0.003, 0.025)  # 평균 0.3%, 변동성 2.5%
                else:
                    daily_return = random.gauss(0.0, 0.01)
                
                daily_returns.append(daily_return)
                cumulative_return *= (1 + daily_return)
            
            final_capital = initial_capital * cumulative_return
            total_return = (final_capital - initial_capital) / initial_capital * 100
            
            # 통계 계산
            avg_daily_return = sum(daily_returns) / len(daily_returns) * 100
            volatility = (sum((r - sum(daily_returns)/len(daily_returns))**2 for r in daily_returns) / len(daily_returns))**0.5 * 100
            
            win_rate = sum(1 for r in daily_returns if r > 0) / len(daily_returns) * 100
            max_drawdown = min(daily_returns) * 100
            
            return {
                'success': True,
                'strategy': strategy_name,
                'stock_code': stock_code,
                'period_days': days,
                'initial_capital': initial_capital,
                'final_capital': int(final_capital),
                'total_return': round(total_return, 2),
                'avg_daily_return': round(avg_daily_return, 3),
                'volatility': round(volatility, 2),
                'win_rate': round(win_rate, 1),
                'max_drawdown': round(max_drawdown, 2),
                'sharpe_ratio': round(avg_daily_return / volatility if volatility > 0 else 0, 2)
            }
            
        except Exception as e:
            self.logger.error(f"백테스트 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def portfolio_optimization(self) -> Dict[str, Any]:
        """포트폴리오 최적화"""
        try:
            portfolio = self.trading_service.get_portfolio()
            account_info = self.trading_service.get_account_info()
            
            if not portfolio:
                return {'success': False, 'error': '포트폴리오가 비어있습니다'}
            
            total_value = sum(item.get('market_value', 0) for item in portfolio)
            recommendations = []
            
            # 집중도 분석
            for item in portfolio:
                weight = item.get('market_value', 0) / total_value if total_value > 0 else 0
                
                if weight > 0.3:  # 30% 이상 집중
                    recommendations.append(f"{item['stock_code']} 비중 과다 ({weight*100:.1f}%) - 분산 권장")
                elif weight < 0.05:  # 5% 미만
                    recommendations.append(f"{item['stock_code']} 비중 과소 ({weight*100:.1f}%) - 정리 고려")
            
            # 손익 분석
            for item in portfolio:
                profit_rate = item.get('profit_rate', 0.0)
                
                if profit_rate > 20:  # 20% 이상 수익
                    recommendations.append(f"{item['stock_code']} 고수익 달성 - 익절 고려")
                elif profit_rate < -10:  # 10% 이상 손실
                    recommendations.append(f"{item['stock_code']} 손실 확대 - 손절 고려")
            
            return {
                'success': True,
                'total_value': total_value,
                'portfolio_count': len(portfolio),
                'recommendations': recommendations,
                'diversification_score': min(len(portfolio) * 20, 100)  # 종목 수에 따른 분산도
            }
