"""
file: kiwoom_mock/trading_service.py
거래 서비스 모듈
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from config import Config

class TradingService:
    """거래 서비스 클래스"""
    
    def __init__(self, kiwoom_api, database_manager):
        self.api = kiwoom_api
        self.db = database_manager
        self.logger = logging.getLogger(__name__)
        self.current_account = Config.DEFAULT_ACCOUNT
        
        # API 이벤트 연결
        self.api.order_completed.connect(self.on_order_completed)
        self.api.data_received.connect(self.on_data_received)
    
    def set_account(self, account_no: str):
        """거래 계좌 설정"""
        self.current_account = account_no
        self.logger.info(f"거래 계좌 설정: {account_no}")
    
    def get_account_info(self) -> Dict[str, Any]:
        """계좌 정보 조회"""
        try:
            # 데이터베이스에서 계좌 정보 조회
            account_info = self.db.get_account_info(self.current_account)
            
            if account_info:
                # API에서 실시간 잔고 조회
                api_balance = self.api.get_balance(self.current_account)
                
                if api_balance:
                    account_info.update(api_balance)
                
                return account_info
            
            return None
            
        except Exception as e:
            self.logger.error(f"계좌 정보 조회 오류: {e}")
            return None
    
    def get_stock_info(self, stock_code: str) -> Dict[str, Any]:
        """종목 정보 조회"""
        try:
            stock_info = self.api.get_stock_info(stock_code)
            
            if stock_info and 'current_price' in stock_info:
                # 데이터베이스에 종목 정보 저장
                self.db.save_stock_info(
                    stock_code, 
                    stock_info.get('stock_name', stock_code),
                    stock_info['current_price']
                )
            
            return stock_info
            
        except Exception as e:
            self.logger.error(f"종목 정보 조회 오류: {e}")
            return {}
    
    def place_buy_order(self, stock_code: str, quantity: int, price: int) -> Dict[str, Any]:
        """매수 주문"""
        try:
            # 주문 전 검증
            validation_result = self.validate_buy_order(stock_code, quantity, price)
            if not validation_result['success']:
                return validation_result
            
            # API 주문 실행
            order_result = self.api.place_order(
                self.current_account, stock_code, '지정가매수', quantity, price
            )
            
            if order_result.get('success'):
                # 데이터베이스에 주문 저장
                order_id = self.db.save_order(
                    self.current_account, stock_code, '매수', quantity, price
                )
                
                if order_id:
                    order_result['db_order_id'] = order_id
                    self.logger.info(f"매수 주문 완료: {stock_code} {quantity}주 @ {price:,}원")
                
                return order_result
            else:
                self.logger.error(f"매수 주문 실패: {order_result.get('error', '알 수 없는 오류')}")
                return order_result
                
        except Exception as e:
            self.logger.error(f"매수 주문 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def place_sell_order(self, stock_code: str, quantity: int, price: int) -> Dict[str, Any]:
        """매도 주문"""
        try:
            # 주문 전 검증
            validation_result = self.validate_sell_order(stock_code, quantity, price)
            if not validation_result['success']:
                return validation_result
            
            # API 주문 실행
            order_result = self.api.place_order(
                self.current_account, stock_code, '지정가매도', quantity, price
            )
            
            if order_result.get('success'):
                # 데이터베이스에 주문 저장
                order_id = self.db.save_order(
                    self.current_account, stock_code, '매도', quantity, price
                )
                
                if order_id:
                    order_result['db_order_id'] = order_id
                    self.logger.info(f"매도 주문 완료: {stock_code} {quantity}주 @ {price:,}원")
                
                return order_result
            else:
                self.logger.error(f"매도 주문 실패: {order_result.get('error', '알 수 없는 오류')}")
                return order_result
                
        except Exception as e:
            self.logger.error(f"매도 주문 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def validate_buy_order(self, stock_code: str, quantity: int, price: int) -> Dict[str, Any]:
        """매수 주문 검증"""
        try:
            # 계좌 정보 확인
            account_info = self.get_account_info()
            if not account_info:
                return {'success': False, 'error': '계좌 정보를 가져올 수 없습니다'}
            
            # 주문 금액 계산
            order_amount = quantity * price
            available_balance = account_info.get('buying_power', 0)
            
            # 잔고 부족 확인
            if order_amount > available_balance:
                return {
                    'success': False, 
                    'error': f'잔고 부족: 필요 {order_amount:,}원, 보유 {available_balance:,}원'
                }
            
            # 기본 유효성 검사
            if quantity <= 0:
                return {'success': False, 'error': '수량은 양수여야 합니다'}
            
            if price <= 0:
                return {'success': False, 'error': '가격은 양수여야 합니다'}
            
            if len(stock_code) != 6 or not stock_code.isdigit():
                return {'success': False, 'error': '종목코드는 6자리 숫자여야 합니다'}
            
            return {'success': True, 'message': '매수 주문 검증 통과'}
            
        except Exception as e:
            self.logger.error(f"매수 주문 검증 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def validate_sell_order(self, stock_code: str, quantity: int, price: int) -> Dict[str, Any]:
        """매도 주문 검증"""
        try:
            # 포트폴리오에서 보유 수량 확인
            portfolio = self.db.get_portfolio(self.current_account)
            
            holding = None
            for item in portfolio:
                if item['stock_code'] == stock_code:
                    holding = item
                    break
            
            if not holding:
                return {'success': False, 'error': f'종목 {stock_code}을(를) 보유하고 있지 않습니다'}
            
            available_qty = holding['quantity']
            if quantity > available_qty:
                return {
                    'success': False, 
                    'error': f'수량 부족: 매도 {quantity}주, 보유 {available_qty}주'
                }
            
            # 기본 유효성 검사
            if quantity <= 0:
                return {'success': False, 'error': '수량은 양수여야 합니다'}
            
            if price <= 0:
                return {'success': False, 'error': '가격은 양수여야 합니다'}
            
            return {'success': True, 'message': '매도 주문 검증 통과'}
            
        except Exception as e:
            self.logger.error(f"매도 주문 검증 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_portfolio(self) -> List[Dict[str, Any]]:
        """포트폴리오 조회"""
        try:
            portfolio = self.db.get_portfolio(self.current_account)
            
            # 각 종목의 현재가 정보 추가
            for item in portfolio:
                stock_info = self.get_stock_info(item['stock_code'])
                if stock_info:
                    item['current_price'] = stock_info.get('current_price', 0)
                    item['market_value'] = item['quantity'] * item['current_price']
                    
                    # 손익 계산
                    if item['avg_price'] > 0:
                        item['profit_loss'] = item['market_value'] - (item['quantity'] * item['avg_price'])
                        item['profit_rate'] = (item['current_price'] - item['avg_price']) / item['avg_price'] * 100
                    else:
                        item['profit_loss'] = 0
                        item['profit_rate'] = 0.0
            
            return portfolio
            
        except Exception as e:
            self.logger.error(f"포트폴리오 조회 오류: {e}")
            return []
    
    def get_order_list(self, status: str = None) -> List[Dict[str, Any]]:
        """주문 내역 조회"""
        try:
            return self.db.get_orders(self.current_account, status)
            
        except Exception as e:
            self.logger.error(f"주문 내역 조회 오류: {e}")
            return []
    
    def get_transaction_list(self, start_date: str = None) -> List[Dict[str, Any]]:
        """거래 내역 조회"""
        try:
            return self.db.get_transactions(self.current_account, start_date)
            
        except Exception as e:
            self.logger.error(f"거래 내역 조회 오류: {e}")
            return []
    
    def on_order_completed(self, event_type: str, data: Dict[str, Any]):
        """주문 체결 이벤트 처리"""
        try:
            if event_type == "주문체결":
                stock_code = data.get('stock_code', '')
                executed_qty = int(data.get('executed_quantity', 0))
                executed_price = int(data.get('executed_price', 0))
                
                if executed_qty > 0 and executed_price > 0:
                    # 포트폴리오 업데이트
                    self.db.update_portfolio(
                        self.current_account, stock_code, executed_qty, executed_price
                    )
                    
                    # 거래 내역 저장
                    transaction_type = "매수" if executed_qty > 0 else "매도"
                    self.db.save_transaction(
                        self.current_account, stock_code, transaction_type,
                        abs(executed_qty), executed_price
                    )
                    
                    self.logger.info(f"주문 체결 처리 완료: {stock_code} {executed_qty}주")
                
        except Exception as e:
            self.logger.error(f"주문 체결 처리 오류: {e}")
    
    def on_data_received(self, data_type: str, data: Dict[str, Any]):
        """데이터 수신 이벤트 처리"""
        try:
            if data_type == "잔고변경":
                # 잔고 변경 시 데이터베이스 업데이트
                self.update_account_from_api()
            elif data_type == "주식기본정보":
                # 종목 정보 업데이트
                if 'stock_code' in data and 'current_price' in data:
                    self.db.save_stock_info(
                        data['stock_code'],
                        data.get('stock_name', ''),
                        data['current_price']
                    )
            
        except Exception as e:
            self.logger.error(f"데이터 수신 처리 오류: {e}")
    
    def update_account_from_api(self):
        """API에서 계좌 정보 업데이트"""
        try:
            balance_info = self.api.get_balance(self.current_account)
            
            if balance_info:
                self.db.update_account_balance(
                    self.current_account,
                    balance_info.get('balance', 0),
                    balance_info.get('buying_power', 0)
                )
                
        except Exception as e:
            self.logger.error(f"API에서 계좌 정보 업데이트 오류: {e}")
    
    def calculate_portfolio_summary(self) -> Dict[str, Any]:
        """포트폴리오 요약 정보 계산"""
        try:
            portfolio = self.get_portfolio()
            account_info = self.get_account_info()
            
            total_value = 0
            total_profit_loss = 0
            total_investment = 0
            
            for item in portfolio:
                market_value = item.get('market_value', 0)
                profit_loss = item.get('profit_loss', 0)
                investment = item['quantity'] * item['avg_price']
                
                total_value += market_value
                total_profit_loss += profit_loss
                total_investment += investment
            
            cash_balance = account_info.get('balance', 0) if account_info else 0
            total_asset = total_value + cash_balance
            
            return {
                'total_asset': total_asset,
                'cash_balance': cash_balance,
                'stock_value': total_value,
                'total_profit_loss': total_profit_loss,
                'total_investment': total_investment,
                'profit_rate': (total_profit_loss / total_investment * 100) if total_investment > 0 else 0.0,
                'portfolio_count': len(portfolio)
            }
            
        except Exception as e:
            self.logger.error(f"포트폴리오 요약 계산 오류: {e}")
            return {}
    
    def get_market_status(self) -> Dict[str, Any]:
        """시장 상태 정보"""
        try:
            is_open = Config.is_market_open()
            api_connected = self.api.is_connected()
            
            return {
                'market_open': is_open,
                'api_connected': api_connected,
                'current_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'market_open_time': Config.MARKET_OPEN_TIME,
                'market_close_time': Config.MARKET_CLOSE_TIME
            }
            
        except Exception as e:
            self.logger.error(f"시장 상태 조회 오류: {e}")
            return {}
    
    def auto_execute_strategy(self, strategy_name: str, stock_code: str) -> Dict[str, Any]:
        """자동 매매 전략 실행"""
        try:
            from strategies import TradingStrategies
            
            strategy = TradingStrategies(self)
            
            if strategy_name == "momentum":
                return strategy.momentum_strategy(stock_code)
            elif strategy_name == "mean_reversion":
                return strategy.mean_reversion_strategy(stock_code)
            elif strategy_name == "breakout":
                return strategy.breakout_strategy(stock_code)
            else:
                return {'success': False, 'error': f'알 수 없는 전략: {strategy_name}'}
                
        except Exception as e:
            self.logger.error(f"자동 매매 전략 실행 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def apply_risk_management(self, stock_code: str) -> Dict[str, Any]:
        """리스크 관리 적용"""
        try:
            portfolio = self.get_portfolio()
            
            for item in portfolio:
                if item['stock_code'] == stock_code:
                    current_price = item.get('current_price', 0)
                    avg_price = item.get('avg_price', 0)
                    quantity = item.get('quantity', 0)
                    
                    if current_price > 0 and avg_price > 0:
                        # 손실률 계산
                        loss_rate = (avg_price - current_price) / avg_price
                        
                        # 손절매 체크
                        if loss_rate >= Config.STOP_LOSS_RATE:
                            result = self.place_sell_order(stock_code, quantity, current_price)
                            if result.get('success'):
                                return {
                                    'success': True,
                                    'action': 'stop_loss',
                                    'message': f'손절매 실행: {stock_code} {quantity}주'
                                }
                        
                        # 익절매 체크
                        profit_rate = (current_price - avg_price) / avg_price
                        if profit_rate >= Config.TAKE_PROFIT_RATE:
                            result = self.place_sell_order(stock_code, quantity, current_price)
                            if result.get('success'):
                                return {
                                    'success': True,
                                    'action': 'take_profit',
                                    'message': f'익절매 실행: {stock_code} {quantity}주'
                                }
            
            return {'success': True, 'action': 'no_action', 'message': '리스크 관리 조건 미충족'}
            
        except Exception as e:
            self.logger.error(f"리스크 관리 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_popular_stocks(self) -> List[Dict[str, Any]]:
        """인기 종목 정보 조회"""
        try:
            popular_stocks = []
            
            for stock_code, stock_name in Config.POPULAR_STOCKS.items():
                stock_info = self.get_stock_info(stock_code)
                if stock_info:
                    popular_stocks.append({
                        'stock_code': stock_code,
                        'stock_name': stock_name,
                        'current_price': stock_info.get('current_price', 0),
                        'change_rate': stock_info.get('change_rate', 0.0)
                    })
            
            return popular_stocks
            
        except Exception as e:
            self.logger.error(f"인기 종목 조회 오류: {e}")
            return []
    
    def get_daily_pnl(self) -> Dict[str, Any]:
        """일일 손익 계산"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            transactions = self.get_transaction_list(today)
            
            daily_profit = 0
            daily_trades = len(transactions)
            
            for transaction in transactions:
                if transaction['transaction_type'] == '매도':
                    # 매도 수익 계산 (간단히 거래금액으로)
                    daily_profit += transaction['amount']
                elif transaction['transaction_type'] == '매수':
                    daily_profit -= transaction['amount']
            
            return {
                'date': today,
                'profit_loss': daily_profit,
                'trade_count': daily_trades,
                'success': True
            }
            
        except Exception as e:
            self.logger.error(f"일일 손익 계산 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_stock_ranking(self, sort_by: str = 'profit_rate') -> List[Dict[str, Any]]:
        """보유 종목 순위"""
        try:
            portfolio = self.get_portfolio()
            
            if not portfolio:
                return []
            
            # 정렬 기준에 따라 정렬
            if sort_by == 'profit_rate':
                portfolio.sort(key=lambda x: x.get('profit_rate', 0.0), reverse=True)
            elif sort_by == 'profit_loss':
                portfolio.sort(key=lambda x: x.get('profit_loss', 0), reverse=True)
            elif sort_by == 'market_value':
                portfolio.sort(key=lambda x: x.get('market_value', 0), reverse=True)
            
            return portfolio
            
        except Exception as e:
            self.logger.error(f"종목 순위 조회 오류: {e}")
            return []
