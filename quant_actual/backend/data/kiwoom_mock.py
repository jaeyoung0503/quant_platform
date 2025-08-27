#file: backend/data/kiwoom_mock.py

import asyncio
import logging
import random
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import uuid

logger = logging.getLogger(__name__)

class KiwoomClient:
    """키움 Open API 모의 클라이언트"""
    
    def __init__(self):
        self.is_connected = False
        self.account_number = "8012345-01"
        self.server_type = "DEMO"  # DEMO or REAL
        
        # 모의 데이터
        self.mock_prices = {}
        self.mock_orders = {}
        self.order_counter = 1000
        
        # 초기 가격 설정
        self.initialize_mock_data()
        
        # 가격 변동 시뮬레이션 태스크
        self.price_update_task = None
    
    def initialize_mock_data(self):
        """모의 데이터 초기화"""
        # 주요 종목의 초기 가격 설정
        self.mock_prices = {
            '005930': {  # 삼성전자
                'current_price': 71200,
                'prev_close': 70800,
                'volume': 12450000,
                'high': 71800,
                'low': 70500,
                'market_cap': 425000000000000,
                'last_update': datetime.now()
            },
            '000660': {  # SK하이닉스
                'current_price': 124500,
                'prev_close': 123000,
                'volume': 8200000,
                'high': 125800,
                'low': 123200,
                'market_cap': 90000000000000,
                'last_update': datetime.now()
            },
            '035420': {  # NAVER
                'current_price': 198000,
                'prev_close': 195000,
                'volume': 1800000,
                'high': 199500,
                'low': 196000,
                'market_cap': 32000000000000,
                'last_update': datetime.now()
            },
            '035720': {  # 카카오
                'current_price': 89500,
                'prev_close': 87200,
                'volume': 3200000,
                'high': 90200,
                'low': 88100,
                'market_cap': 38000000000000,
                'last_update': datetime.now()
            },
            '051910': {  # LG화학
                'current_price': 486000,
                'prev_close': 482000,
                'volume': 450000,
                'high': 489000,
                'low': 483000,
                'market_cap': 34000000000000,
                'last_update': datetime.now()
            },
            '006400': {  # 삼성SDI
                'current_price': 425000,
                'prev_close': 420000,
                'volume': 380000,
                'high': 428000,
                'low': 422000,
                'market_cap': 28000000000000,
                'last_update': datetime.now()
            },
            '207940': {  # 삼성바이오로직스
                'current_price': 785000,
                'prev_close': 780000,
                'volume': 120000,
                'high': 790000,
                'low': 775000,
                'market_cap': 53000000000000,
                'last_update': datetime.now()
            },
            '373220': {  # LG에너지솔루션
                'current_price': 412000,
                'prev_close': 408000,
                'volume': 680000,
                'high': 415000,
                'low': 409000,
                'market_cap': 96000000000000,
                'last_update': datetime.now()
            }
        }
    
    async def connect(self):
        """키움 API 연결"""
        try:
            logger.info("키움 API 연결 시도 중...")
            
            # 연결 시뮬레이션 (2초 대기)
            await asyncio.sleep(2)
            
            self.is_connected = True
            
            # 실시간 가격 업데이트 시작
            self.price_update_task = asyncio.create_task(self.simulate_price_updates())
            
            logger.info("키움 API 연결 완료 (모의투자 모드)")
            return True
            
        except Exception as e:
            logger.error(f"키움 API 연결 실패: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """키움 API 연결 해제"""
        try:
            self.is_connected = False
            
            if self.price_update_task:
                self.price_update_task.cancel()
            
            logger.info("키움 API 연결 해제됨")
            
        except Exception as e:
            logger.error(f"키움 API 연결 해제 실패: {e}")
    
    async def simulate_price_updates(self):
        """실시간 가격 변동 시뮬레이션"""
        try:
            while self.is_connected:
                await asyncio.sleep(1)  # 1초마다 업데이트
                
                for stock_code in self.mock_prices:
                    await self.update_mock_price(stock_code)
                    
        except asyncio.CancelledError:
            logger.info("가격 업데이트 시뮬레이션 종료")
        except Exception as e:
            logger.error(f"가격 업데이트 시뮬레이션 오류: {e}")
    
    async def update_mock_price(self, stock_code: str):
        """개별 종목 가격 업데이트"""
        try:
            if stock_code not in self.mock_prices:
                return
            
            price_data = self.mock_prices[stock_code]
            current_price = price_data['current_price']
            
            # 가격 변동 시뮬레이션 (±2% 범위)
            change_rate = random.uniform(-0.02, 0.02)
            new_price = current_price * (1 + change_rate)
            
            # 일정 범위 내에서만 변동하도록 제한
            prev_close = price_data['prev_close']
            max_price = prev_close * 1.30  # 상한가 30%
            min_price = prev_close * 0.70  # 하한가 -30%
            
            new_price = max(min_price, min(max_price, new_price))
            
            # 가격 데이터 업데이트
            price_data['current_price'] = int(new_price)
            price_data['volume'] += random.randint(1000, 10000)
            price_data['high'] = max(price_data['high'], int(new_price))
            price_data['low'] = min(price_data['low'], int(new_price))
            price_data['last_update'] = datetime.now()
            
        except Exception as e:
            logger.error(f"가격 업데이트 오류 {stock_code}: {e}")
    
    async def get_current_price(self, stock_code: str) -> Dict[str, Any]:
        """현재 시세 조회"""
        try:
            if not self.is_connected:
                raise Exception("API 연결되지 않음")
            
            if stock_code not in self.mock_prices:
                # 새로운 종목인 경우 기본 데이터 생성
                self.mock_prices[stock_code] = {
                    'current_price': random.randint(50000, 500000),
                    'prev_close': random.randint(50000, 500000),
                    'volume': random.randint(100000, 5000000),
                    'high': 0,
                    'low': 999999999,
                    'market_cap': random.randint(1000000000000, 100000000000000),
                    'last_update': datetime.now()
                }
            
            price_data = self.mock_prices[stock_code].copy()
            
            # 추가 정보 계산
            price_change = price_data['current_price'] - price_data['prev_close']
            change_rate = (price_change / price_data['prev_close']) * 100
            
            price_data.update({
                'price_change': price_change,
                'change_rate': change_rate,
                'bid_price': price_data['current_price'] - 100,
                'ask_price': price_data['current_price'] + 100,
                'timestamp': datetime.now().isoformat()
            })
            
            return price_data
            
        except Exception as e:
            logger.error(f"시세 조회 오류 {stock_code}: {e}")
            return {
                'current_price': 100000,
                'prev_close': 100000,
                'volume': 0,
                'error': str(e)
            }
    
    async def send_order(self, stock_code: str, order_type: str, quantity: int, price: float) -> str:
        """주문 전송"""
        try:
            if not self.is_connected:
                raise Exception("API 연결되지 않음")
            
            # 주문 번호 생성
            order_id = f"ORD{self.order_counter:06d}"
            self.order_counter += 1
            
            # 주문 데이터 생성
            order_data = {
                'order_id': order_id,
                'stock_code': stock_code,
                'order_type': order_type.upper(),
                'quantity': quantity,
                'price': price,
                'status': 'pending',
                'order_time': datetime.now(),
                'fill_time': None,
                'fill_price': None,
                'fill_quantity': None,
                'remaining_quantity': quantity,
                'account_number': self.account_number
            }
            
            # 주문 저장
            self.mock_orders[order_id] = order_data
            
            # 주문 처리 시뮬레이션 시작
            asyncio.create_task(self.simulate_order_fill(order_id))
            
            logger.info(f"주문 전송 완료: {stock_code} {order_type} {quantity}주 @ {price}")
            return order_id
            
        except Exception as e:
            logger.error(f"주문 전송 실패: {e}")
            raise
    
    async def simulate_order_fill(self, order_id: str):
        """주문 체결 시뮬레이션"""
        try:
            await asyncio.sleep(random.uniform(1, 5))  # 1-5초 후 체결
            
            if order_id not in self.mock_orders:
                return
            
            order = self.mock_orders[order_id]
            
            # 체결 확률 (90%)
            if random.random() < 0.9:
                # 체결 처리
                stock_code = order['stock_code']
                current_market_price = self.mock_prices.get(stock_code, {}).get('current_price', order['price'])
                
                # 체결가 결정 (주문가 근처에서 체결)
                if order['order_type'] == 'BUY':
                    fill_price = min(order['price'], current_market_price + random.randint(-500, 500))
                else:  # SELL
                    fill_price = max(order['price'], current_market_price + random.randint(-500, 500))
                
                fill_quantity = order['quantity']  # 전량 체결
                
                # 주문 상태 업데이트
                order.update({
                    'status': 'filled',
                    'fill_time': datetime.now(),
                    'fill_price': fill_price,
                    'fill_quantity': fill_quantity,
                    'remaining_quantity': 0,
                    'commission': self.calculate_commission(fill_price * fill_quantity)
                })
                
                logger.info(f"주문 체결: {order_id} - {fill_quantity}주 @ {fill_price}")
                
            else:
                # 주문 취소 또는 거부
                order['status'] = random.choice(['cancelled', 'rejected'])
                logger.info(f"주문 {order['status']}: {order_id}")
                
        except Exception as e:
            logger.error(f"주문 체결 시뮬레이션 오류 {order_id}: {e}")
    
    def calculate_commission(self, trade_amount: float) -> float:
        """수수료 계산"""
        # 간단한 수수료 계산 (거래금액의 0.015%)
        commission_rate = 0.00015
        return trade_amount * commission_rate
    
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """주문 상태 조회"""
        try:
            if order_id not in self.mock_orders:
                return {'status': 'not_found', 'error': '주문을 찾을 수 없음'}
            
            order = self.mock_orders[order_id].copy()
            return order
            
        except Exception as e:
            logger.error(f"주문 상태 조회 오류 {order_id}: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def cancel_order(self, order_id: str) -> bool:
        """주문 취소"""
        try:
            if order_id not in self.mock_orders:
                return False
            
            order = self.mock_orders[order_id]
            
            if order['status'] == 'pending':
                order['status'] = 'cancelled'
                order['cancel_time'] = datetime.now()
                logger.info(f"주문 취소됨: {order_id}")
                return True
            else:
                logger.warning(f"취소할 수 없는 주문 상태: {order_id} ({order['status']})")
                return False
                
        except Exception as e:
            logger.error(f"주문 취소 오류 {order_id}: {e}")
            return False
    
    async def get_account_info(self) -> Dict[str, Any]:
        """계좌 정보 조회"""
        try:
            if not self.is_connected:
                raise Exception("API 연결되지 않음")
            
            # 모의 계좌 정보
            account_info = {
                'account_number': self.account_number,
                'account_name': '모의투자계좌',
                'total_cash': 50000000,  # 5천만원
                'available_cash': 24000000,  # 2천4백만원
                'total_evaluation': 50000000,
                'total_profit_loss': 0,
                'profit_loss_rate': 0.0,
                'server_type': self.server_type
            }
            
            return account_info
            
        except Exception as e:
            logger.error(f"계좌 정보 조회 오류: {e}")
            return {}
    
    async def get_balance(self) -> List[Dict[str, Any]]:
        """잔고 조회"""
        try:
            if not self.is_connected:
                raise Exception("API 연결되지 않음")
            
            # 모의 잔고 데이터
            balance = []
            
            # 현재 보유 종목 시뮬레이션
            holdings = {
                '005930': {'quantity': 50, 'avg_price': 70000},
                '035720': {'quantity': 30, 'avg_price': 88000}
            }
            
            for stock_code, holding in holdings.items():
                current_price_data = await self.get_current_price(stock_code)
                current_price = current_price_data['current_price']
                
                quantity = holding['quantity']
                avg_price = holding['avg_price']
                current_value = current_price * quantity
                purchase_value = avg_price * quantity
                profit_loss = current_value - purchase_value
                profit_loss_rate = (profit_loss / purchase_value) * 100
                
                balance_item = {
                    'stock_code': stock_code,
                    'stock_name': self.get_stock_name(stock_code),
                    'quantity': quantity,
                    'avg_price': avg_price,
                    'current_price': current_price,
                    'current_value': current_value,
                    'purchase_value': purchase_value,
                    'profit_loss': profit_loss,
                    'profit_loss_rate': profit_loss_rate,
                    'loan_amount': 0  # 신용거래 없음
                }
                
                balance.append(balance_item)
            
            return balance
            
        except Exception as e:
            logger.error(f"잔고 조회 오류: {e}")
            return []
    
    def get_stock_name(self, stock_code: str) -> str:
        """종목명 조회"""
        stock_names = {
            '005930': '삼성전자',
            '000660': 'SK하이닉스',
            '035420': 'NAVER',
            '035720': '카카오',
            '051910': 'LG화학',
            '006400': '삼성SDI',
            '207940': '삼성바이오로직스',
            '373220': 'LG에너지솔루션'
        }
        return stock_names.get(stock_code, f'종목{stock_code}')
    
    async def get_order_history(self, days: int = 30) -> List[Dict[str, Any]]:
        """주문 내역 조회"""
        try:
            if not self.is_connected:
                raise Exception("API 연결되지 않음")
            
            # 날짜 범위 설정
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 조건에 맞는 주문들 필터링
            history = []
            for order_id, order in self.mock_orders.items():
                order_time = order['order_time']
                if start_date <= order_time <= end_date:
                    history_item = order.copy()
                    history_item['stock_name'] = self.get_stock_name(order['stock_code'])
                    history.append(history_item)
            
            # 주문 시간 역순 정렬
            history.sort(key=lambda x: x['order_time'], reverse=True)
            
            return history
            
        except Exception as e:
            logger.error(f"주문 내역 조회 오류: {e}")
            return []
    
    async def get_market_status(self) -> Dict[str, Any]:
        """시장 상태 조회"""
        try:
            current_time = datetime.now()
            current_hour = current_time.hour
            current_minute = current_time.minute
            
            # 시장 개장 시간 체크 (9:00 - 15:30)
            is_market_open = False
            market_status = "장마감"
            
            if current_time.weekday() < 5:  # 평일
                if (current_hour == 9 and current_minute >= 0) or \
                   (9 < current_hour < 15) or \
                   (current_hour == 15 and current_minute <= 30):
                    is_market_open = True
                    market_status = "정규장"
                elif current_hour == 8 and current_minute >= 30:
                    market_status = "장전동시호가"
                elif current_hour == 15 and 30 < current_minute <= 40:
                    market_status = "장후동시호가"
            
            return {
                'is_open': is_market_open,
                'status': market_status,
                'server_time': current_time.isoformat(),
                'kospi_index': random.randint(2400, 2800),
                'kosdaq_index': random.randint(800, 1000),
                'exchange_rate': random.uniform(1300, 1400)  # 달러 환율
            }
            
        except Exception as e:
            logger.error(f"시장 상태 조회 오류: {e}")
            return {'is_open': False, 'status': 'error'}
    
    async def get_stock_info(self, stock_code: str) -> Dict[str, Any]:
        """종목 상세 정보 조회"""
        try:
            if not self.is_connected:
                raise Exception("API 연결되지 않음")
            
            # 기본 시세 정보 조회
            price_data = await self.get_current_price(stock_code)
            
            # 추가 종목 정보
            stock_info = {
                'stock_code': stock_code,
                'stock_name': self.get_stock_name(stock_code),
                'market': 'KOSPI' if stock_code.startswith(('00', '05')) else 'KOSDAQ',
                'sector': self.get_stock_sector(stock_code),
                'market_cap': price_data.get('market_cap', 0),
                'shares_outstanding': random.randint(100000000, 1000000000),
                'per': random.uniform(8.0, 25.0),
                'pbr': random.uniform(0.8, 3.0),
                'roe': random.uniform(5.0, 20.0),
                'dividend_yield': random.uniform(1.0, 5.0),
                'foreign_ownership': random.uniform(10.0, 70.0),
                '52_week_high': int(price_data['current_price'] * random.uniform(1.2, 1.8)),
                '52_week_low': int(price_data['current_price'] * random.uniform(0.6, 0.9))
            }
            
            stock_info.update(price_data)
            
            return stock_info
            
        except Exception as e:
            logger.error(f"종목 정보 조회 오류 {stock_code}: {e}")
            return {}
    
    def get_stock_sector(self, stock_code: str) -> str:
        """종목 섹터 조회"""
        sector_map = {
            '005930': '반도체',
            '000660': '반도체',
            '035420': '인터넷',
            '035720': '인터넷',
            '051910': '화학',
            '006400': '배터리',
            '207940': '바이오',
            '373220': '배터리'
        }
        return sector_map.get(stock_code, '기타')
    
    async def get_candle_data(self, stock_code: str, period: str = 'D', count: int = 100) -> List[Dict[str, Any]]:
        """캔들 데이터 조회"""
        try:
            if not self.is_connected:
                raise Exception("API 연결되지 않음")
            
            # 현재 가격 기준으로 과거 캔들 데이터 시뮬레이션
            current_price_data = await self.get_current_price(stock_code)
            base_price = current_price_data['current_price']
            
            candles = []
            current_date = datetime.now()
            
            for i in range(count):
                # 날짜 계산
                if period == 'D':
                    date = current_date - timedelta(days=i)
                elif period == 'W':
                    date = current_date - timedelta(weeks=i)
                elif period == 'M':
                    date = current_date - timedelta(days=i*30)
                else:  # minute
                    date = current_date - timedelta(minutes=i)
                
                # 가격 시뮬레이션
                price_variation = random.uniform(0.9, 1.1)
                open_price = int(base_price * price_variation)
                
                high_variation = random.uniform(1.0, 1.05)
                high_price = int(open_price * high_variation)
                
                low_variation = random.uniform(0.95, 1.0)
                low_price = int(open_price * low_variation)
                
                close_variation = random.uniform(0.98, 1.02)
                close_price = int(open_price * close_variation)
                
                volume = random.randint(100000, 5000000)
                
                candle = {
                    'date': date.strftime('%Y%m%d'),
                    'time': date.strftime('%H%M%S') if period in ['1', '5', '15', '30', '60'] else None,
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'close': close_price,
                    'volume': volume,
                    'amount': close_price * volume
                }
                
                candles.append(candle)
                
                # 다음 계산을 위해 base_price 조정
                base_price = close_price
            
            # 시간순 정렬
            candles.reverse()
            
            return candles
            
        except Exception as e:
            logger.error(f"캔들 데이터 조회 오류 {stock_code}: {e}")
            return []
    
    async def get_market_capitalization(self, market: str = 'KOSPI') -> List[Dict[str, Any]]:
        """시가총액 상위 종목 조회"""
        try:
            if not self.is_connected:
                raise Exception("API 연결되지 않음")
            
            # 시가총액 상위 종목 시뮬레이션
            top_stocks = []
            
            if market == 'KOSPI':
                stock_list = ['005930', '000660', '035420', '051910', '006400', '207940', '373220']
            else:  # KOSDAQ
                stock_list = ['035720']
            
            for i, stock_code in enumerate(stock_list):
                price_data = await self.get_current_price(stock_code)
                
                stock_info = {
                    'rank': i + 1,
                    'stock_code': stock_code,
                    'stock_name': self.get_stock_name(stock_code),
                    'current_price': price_data['current_price'],
                    'change_rate': price_data.get('change_rate', 0),
                    'market_cap': price_data.get('market_cap', 0),
                    'volume': price_data['volume']
                }
                
                top_stocks.append(stock_info)
            
            # 시가총액 기준 정렬
            top_stocks.sort(key=lambda x: x['market_cap'], reverse=True)
            
            return top_stocks
            
        except Exception as e:
            logger.error(f"시가총액 조회 오류: {e}")
            return []
    
    async def search_stock(self, keyword: str) -> List[Dict[str, Any]]:
        """종목 검색"""
        try:
            if not self.is_connected:
                raise Exception("API 연결되지 않음")
            
            results = []
            
            # 모든 종목에서 검색
            for stock_code in self.mock_prices.keys():
                stock_name = self.get_stock_name(stock_code)
                
                # 종목코드나 종목명에 키워드가 포함된 경우
                if keyword.lower() in stock_code.lower() or keyword in stock_name:
                    price_data = await self.get_current_price(stock_code)
                    
                    result = {
                        'stock_code': stock_code,
                        'stock_name': stock_name,
                        'current_price': price_data['current_price'],
                        'change_rate': price_data.get('change_rate', 0),
                        'market': 'KOSPI' if stock_code.startswith(('00', '05')) else 'KOSDAQ'
                    }
                    
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"종목 검색 오류: {e}")
            return []
    
    async def get_news(self, stock_code: str = None, count: int = 10) -> List[Dict[str, Any]]:
        """뉴스 조회"""
        try:
            if not self.is_connected:
                raise Exception("API 연결되지 않음")
            
            # 모의 뉴스 데이터 생성
            news_titles = [
                "반도체 업황 개선 기대감 확산",
                "4분기 실적 전망 양호",
                "신제품 출시로 매출 증대 예상",
                "해외 시장 진출 계획 발표",
                "ESG 경영 강화 방안 공개",
                "디지털 전환 투자 확대",
                "친환경 기술 개발 박차",
                "글로벌 파트너십 체결"
            ]
            
            news_list = []
            
            for i in range(count):
                news_time = datetime.now() - timedelta(hours=random.randint(1, 48))
                
                news_item = {
                    'title': random.choice(news_titles),
                    'content': "관련 뉴스 내용입니다.",
                    'source': random.choice(['연합뉴스', '이데일리', '매일경제', '한국경제']),
                    'datetime': news_time.isoformat(),
                    'stock_code': stock_code if stock_code else random.choice(list(self.mock_prices.keys())),
                    'url': f"http://example.com/news/{i+1}"
                }
                
                news_list.append(news_item)
            
            # 시간순 정렬
            news_list.sort(key=lambda x: x['datetime'], reverse=True)
            
            return news_list
            
        except Exception as e:
            logger.error(f"뉴스 조회 오류: {e}")
            return []
    
    def get_connection_status(self) -> Dict[str, Any]:
        """연결 상태 확인"""
        return {
            'is_connected': self.is_connected,
            'account_number': self.account_number if self.is_connected else None,
            'server_type': self.server_type,
            'api_version': '1.0.0',
            'connection_time': datetime.now().isoformat() if self.is_connected else None
        } 
