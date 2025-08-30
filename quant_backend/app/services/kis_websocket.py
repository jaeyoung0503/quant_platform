# services/kis_websocket.py - KIS WebSocket 실시간 데이터 클라이언트 완성본

import websockets
import json
import asyncio
from typing import Dict, List, Callable, Optional
import logging
from datetime import datetime
import base64

logger = logging.getLogger(__name__)

class KISWebSocket:
    """KIS WebSocket 실시간 데이터 클라이언트"""
    
    def __init__(self, auth_service, ws_url: str):
        self.auth = auth_service
        self.ws_url = ws_url
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.is_connected = False
        self.subscribers: Dict[str, List[Callable]] = {}
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.heartbeat_task: Optional[asyncio.Task] = None
        
    async def connect(self):
        """WebSocket 연결"""
        try:
            logger.info("KIS WebSocket 연결 시도...")
            print(f"\n[WebSocket] 연결 시도 중...")
            print(f"├─ URL: {self.ws_url}")
            print(f"└─ 시간: {datetime.now().strftime('%H:%M:%S')}")
            
            # WebSocket 연결
            self.websocket = await websockets.connect(
                self.ws_url,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10
            )
            
            self.is_connected = True
            self.reconnect_attempts = 0
            
            logger.info("KIS WebSocket 연결 완료")
            print(f"WebSocket 연결 성공!")
            
            # 승인키 전송
            await self._send_approval()
            
            # 메시지 수신 태스크 시작
            asyncio.create_task(self._listen_messages())
            
            # 하트비트 시작
            self.heartbeat_task = asyncio.create_task(self._heartbeat())
            
        except Exception as e:
            logger.error(f"WebSocket 연결 실패: {e}")
            print(f"WebSocket 연결 실패: {e}")
            await self._handle_reconnect()
    
    async def _send_approval(self):
        """승인키 전송"""
        try:
            # WebSocket 승인키 발급
            approval_key = await self.auth.get_websocket_key()
            
            approval_data = {
                "header": {
                    "approval_key": approval_key,
                    "custtype": "P",
                    "tr_type": "1",
                    "content_type": "utf-8"
                },
                "body": {
                    "input": {
                        "tr_id": "H0STCNT0",  # 실시간 시세
                        "tr_key": stock_code
                    }
                }
            }
            
            await self.websocket.send(json.dumps(subscribe_data))
            
            # 콜백 등록
            if callback:
                if stock_code not in self.subscribers:
                    self.subscribers[stock_code] = []
                self.subscribers[stock_code].append(callback)
            
            logger.info(f"실시간 시세 구독: {stock_code}")
            print(f"\n[구독 시작] {stock_code} 실시간 시세")
            print(f"├─ 구독 시간: {datetime.now().strftime('%H:%M:%S')}")
            print(f"└─ 상태: 활성")
            
        except Exception as e:
            logger.error(f"실시간 구독 실패: {e}")
            print(f"{stock_code} 구독 실패: {e}")
    
    async def subscribe_realtime_orderbook(self, stock_code: str, callback: Callable = None):
        """실시간 호가 구독"""
        if not self.is_connected:
            await self.connect()
        
        try:
            approval_key = await self.auth.get_websocket_key()
            
            subscribe_data = {
                "header": {
                    "approval_key": approval_key,
                    "custtype": "P",
                    "tr_type": "1",
                    "content_type": "utf-8"
                },
                "body": {
                    "input": {
                        "tr_id": "H0STASP0",  # 실시간 호가
                        "tr_key": stock_code
                    }
                }
            }
            
            await self.websocket.send(json.dumps(subscribe_data))
            
            if callback:
                callback_key = f"{stock_code}_orderbook"
                if callback_key not in self.subscribers:
                    self.subscribers[callback_key] = []
                self.subscribers[callback_key].append(callback)
            
            print(f"[호가 구독] {stock_code} 실시간 호가 구독 시작")
            
        except Exception as e:
            logger.error(f"호가 구독 실패: {e}")
            print(f"{stock_code} 호가 구독 실패: {e}")
    
    async def _listen_messages(self):
        """실시간 메시지 수신"""
        try:
            async for message in self.websocket:
                if isinstance(message, bytes):
                    # 바이너리 데이터 처리
                    await self._process_binary_message(message)
                else:
                    # JSON 데이터 처리
                    await self._process_json_message(message)
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket 연결이 끊어졌습니다")
            print("WebSocket 연결 끊어짐 - 재연결 시도 중...")
            self.is_connected = False
            await self._handle_reconnect()
        except Exception as e:
            logger.error(f"메시지 수신 오류: {e}")
            print(f"메시지 수신 오류: {e}")
    
    async def _process_json_message(self, message):
        """JSON 메시지 처리"""
        try:
            data = json.loads(message)
            header = data.get("header", {})
            
            # PINGPONG 응답 처리
            if header.get("tr_id") == "PINGPONG":
                print("PINGPONG 응답 수신")
                return
            
            # 기타 JSON 메시지 처리
            logger.debug(f"JSON 메시지 수신: {header.get('tr_id')}")
            
        except Exception as e:
            logger.error(f"JSON 메시지 처리 오류: {e}")
    
    async def _process_binary_message(self, message):
        """바이너리 메시지 처리 (실시간 데이터)"""
        try:
            # KIS WebSocket 바이너리 프로토콜 파싱
            if len(message) < 3:
                return
            
            # 헤더 파싱
            tr_id = message[:3].decode('utf-8', errors='ignore')
            
            if tr_id == 'H0S':  # 실시간 시세
                await self._parse_realtime_price(message)
            elif tr_id == 'H0A':  # 실시간 호가
                await self._parse_realtime_orderbook(message)
                
        except Exception as e:
            logger.error(f"바이너리 메시지 처리 오류: {e}")
    
    async def _parse_realtime_price(self, message):
        """실시간 시세 바이너리 데이터 파싱"""
        try:
            # KIS 바이너리 프로토콜에 따른 파싱
            # 실제 구현에서는 KIS 문서의 바이너리 구조를 따라야 함
            
            # 임시 파싱 로직 (실제로는 KIS 스펙에 맞게 구현 필요)
            data_str = message[3:].decode('utf-8', errors='ignore')
            fields = data_str.split('|')
            
            if len(fields) >= 10:
                stock_code = fields[0] if len(fields) > 0 else ""
                current_price = int(fields[2]) if fields[2].isdigit() else 0
                volume = int(fields[4]) if fields[4].isdigit() else 0
                
                price_data = {
                    'timestamp': datetime.now(),
                    'code': stock_code,
                    'price': current_price,
                    'volume': volume,
                    'total_volume': int(fields[5]) if len(fields) > 5 and fields[5].isdigit() else 0,
                    'change': int(fields[6]) if len(fields) > 6 and fields[6].lstrip('-').isdigit() else 0,
                    'change_rate': float(fields[7]) if len(fields) > 7 else 0.0
                }
                
                await self._handle_realtime_price(stock_code, price_data)
            
        except Exception as e:
            logger.error(f"실시간 시세 파싱 오류: {e}")
    
    async def _parse_realtime_orderbook(self, message):
        """실시간 호가 바이너리 데이터 파싱"""
        try:
            # 호가 데이터 파싱 로직
            data_str = message[3:].decode('utf-8', errors='ignore')
            fields = data_str.split('|')
            
            if len(fields) >= 20:
                stock_code = fields[0] if len(fields) > 0 else ""
                
                orderbook_data = {
                    'timestamp': datetime.now(),
                    'code': stock_code,
                    'ask_prices': [int(fields[i]) if fields[i].isdigit() else 0 for i in range(1, 11)],
                    'ask_volumes': [int(fields[i]) if fields[i].isdigit() else 0 for i in range(11, 21)],
                    'bid_prices': [int(fields[i]) if fields[i].isdigit() else 0 for i in range(21, 31)],
                    'bid_volumes': [int(fields[i]) if fields[i].isdigit() else 0 for i in range(31, 41)]
                }
                
                await self._handle_realtime_orderbook(stock_code, orderbook_data)
            
        except Exception as e:
            logger.error(f"호가 데이터 파싱 오류: {e}")
    
    async def _handle_realtime_price(self, stock_code: str, data: Dict):
        """실시간 시세 데이터 처리"""
        try:
            # 실시간 틱 출력
            self._print_tick_data(data)
            
            # 구독자들에게 콜백 실행
            if stock_code in self.subscribers:
                for callback in self.subscribers[stock_code]:
                    try:
                        await callback(data)
                    except Exception as e:
                        logger.error(f"콜백 실행 오류: {e}")
                        
        except Exception as e:
            logger.error(f"실시간 시세 처리 오류: {e}")
    
    async def _handle_realtime_orderbook(self, stock_code: str, data: Dict):
        """실시간 호가 데이터 처리"""
        try:
            # 호가창 출력
            self._print_orderbook(data)
            
            # 콜백 실행
            callback_key = f"{stock_code}_orderbook"
            if callback_key in self.subscribers:
                for callback in self.subscribers[callback_key]:
                    try:
                        await callback(data)
                    except Exception as e:
                        logger.error(f"호가 콜백 실행 오류: {e}")
                        
        except Exception as e:
            logger.error(f"호가 데이터 처리 오류: {e}")
    
    def _print_tick_data(self, data: Dict):
        """틱 데이터 실시간 출력"""
        timestamp = data['timestamp'].strftime('%H:%M:%S')
        price = data['price']
        volume = data['volume']
        change = data['change']
        change_rate = data['change_rate']
        
        # 등락 표시
        if change > 0:
            change_symbol = "▲"
            color = "상승"
        elif change < 0:
            change_symbol = "▼" 
            color = "하락"
        else:
            change_symbol = "="
            color = "보합"
        
        print(f"\n[실시간 틱] {data['code']} | {timestamp}")
        print(f"├─ 현재가: {price:,}원 ({change_symbol} {abs(change)}, {change_rate:+.2f}%) [{color}]")
        print(f"├─ 거래량: {volume:,}주")
        print(f"└─ 누적거래량: {data['total_volume']:,}주")
        
        # 급등/급락 알림
        if abs(change_rate) > 3.0:
            if change_rate > 0:
                print(f"급등 알림! {data['code']} {change_rate:.2f}% 상승")
            else:
                print(f"급락 알림! {data['code']} {change_rate:.2f}% 하락")
    
    def _print_orderbook(self, data: Dict):
        """호가창 실시간 출력"""
        timestamp = data['timestamp'].strftime('%H:%M:%S')
        
        print(f"\n[실시간 호가] {data['code']} | {timestamp}")
        print("매도 호가                    │ 매수 호가")
        print("-" * 30 + "┼" + "-" * 30)
        
        for i in range(5):  # 상위 5호가만 출력
            ask_price = data['ask_prices'][i] if i < len(data['ask_prices']) else 0
            ask_volume = data['ask_volumes'][i] if i < len(data['ask_volumes']) else 0
            bid_price = data['bid_prices'][i] if i < len(data['bid_prices']) else 0
            bid_volume = data['bid_volumes'][i] if i < len(data['bid_volumes']) else 0
            
            print(f"{ask_price:>7,} ({ask_volume:>4,})    │    {bid_price:>7,} ({bid_volume:>4,})")
    
    async def _handle_reconnect(self):
        """재연결 처리"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error("최대 재연결 시도 횟수 초과")
            print("최대 재연결 시도 횟수 초과 - 연결 포기")
            return
        
        self.reconnect_attempts += 1
        wait_time = min(2 ** self.reconnect_attempts, 30)  # 지수 백오프
        
        print(f"재연결 시도 {self.reconnect_attempts}/{self.max_reconnect_attempts} - {wait_time}초 후...")
        await asyncio.sleep(wait_time)
        
        try:
            await self.connect()
            # 기존 구독 복구
            await self._restore_subscriptions()
        except Exception as e:
            logger.error(f"재연결 실패: {e}")
            await self._handle_reconnect()
    
    async def _restore_subscriptions(self):
        """기존 구독 복구"""
        print("\n[구독 복구] 기존 구독 종목 복구 중...")
        
        restored_count = 0
        for key in list(self.subscribers.keys()):
            if "_orderbook" not in key:  # 시세 구독만 복구
                try:
                    await self.subscribe_realtime_price(key)
                    restored_count += 1
                    await asyncio.sleep(0.5)  # 구독 간 지연
                except Exception as e:
                    logger.error(f"구독 복구 실패 {key}: {e}")
        
        print(f"{restored_count}개 종목 구독 복구 완료")
    
    def add_subscriber(self, stock_code: str, callback: Callable):
        """구독자 추가"""
        if stock_code not in self.subscribers:
            self.subscribers[stock_code] = []
        self.subscribers[stock_code].append(callback)
    
    def remove_subscriber(self, stock_code: str, callback: Callable):
        """구독자 제거"""
        if stock_code in self.subscribers:
            try:
                self.subscribers[stock_code].remove(callback)
                if not self.subscribers[stock_code]:
                    del self.subscribers[stock_code]
            except ValueError:
                pass
    
    def print_connection_status(self):
        """연결 상태 상세 출력"""
        print(f"\n==================== WebSocket 상태 ====================")
        print(f"연결 상태: {'연결됨' if self.is_connected else '끊어짐'}")
        print(f"WebSocket URL: {self.ws_url}")
        print(f"구독 종목 수: {len([k for k in self.subscribers.keys() if '_orderbook' not in k])}개")
        print(f"호가 구독 수: {len([k for k in self.subscribers.keys() if '_orderbook' in k])}개")
        print(f"재연결 시도: {self.reconnect_attempts}/{self.max_reconnect_attempts}")
        print(f"마지막 연결: {datetime.now().strftime('%H:%M:%S')}")
        
        if self.subscribers:
            print(f"\n[구독 중인 종목]")
            price_subs = [k for k in self.subscribers.keys() if '_orderbook' not in k]
            orderbook_subs = [k.replace('_orderbook', '') for k in self.subscribers.keys() if '_orderbook' in k]
            
            for i, stock_code in enumerate(price_subs, 1):
                has_orderbook = stock_code in orderbook_subs
                print(f"{i:2d}. {stock_code} {'(시세+호가)' if has_orderbook else '(시세만)'}")
        
        print("=" * 54)
    
    async def unsubscribe(self, stock_code: str):
        """구독 해제"""
        try:
            if not self.is_connected:
                return
            
            approval_key = await self.auth.get_websocket_key()
            
            unsubscribe_data = {
                "header": {
                    "approval_key": approval_key,
                    "custtype": "P",
                    "tr_type": "2",  # 구독 해제
                    "content_type": "utf-8"
                },
                "body": {
                    "input": {
                        "tr_id": "H0STCNT0",
                        "tr_key": stock_code
                    }
                }
            }
            
            await self.websocket.send(json.dumps(unsubscribe_data))
            
            # 로컬 구독자 제거
            if stock_code in self.subscribers:
                del self.subscribers[stock_code]
            
            print(f"[구독 해제] {stock_code} 구독 해제 완료")
            
        except Exception as e:
            logger.error(f"구독 해제 실패: {e}")
            print(f"{stock_code} 구독 해제 실패: {e}")
    
    async def disconnect(self):
        """연결 종료"""
        self.is_connected = False
        
        # 하트비트 태스크 종료
        if self.heartbeat_task and not self.heartbeat_task.done():
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # WebSocket 연결 종료
        if self.websocket and not self.websocket.closed:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.error(f"WebSocket 종료 오류: {e}")
        
        print("WebSocket 연결 종료")
    
    def get_subscription_count(self) -> int:
        """현재 구독 수 반환"""
        return len([k for k in self.subscribers.keys() if '_orderbook' not in k])
    
    def get_subscribed_stocks(self) -> List[str]:
        """구독 중인 종목 리스트 반환"""
        return [k for k in self.subscribers.keys() if '_orderbook' not in k]    "input": {
                        "tr_id": "PINGPONG",
                        "tr_key": ""
                    }
                }
            }
            
            await self.websocket.send(json.dumps(approval_data))
            logger.info("승인키 전송 완료")
            print("WebSocket 승인키 전송 완료")
            
            # 승인 응답 대기
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"승인키 전송 실패: {e}")
            print(f"승인키 전송 실패: {e}")
            raise e
    
    async def _heartbeat(self):
        """연결 유지를 위한 하트비트"""
        while self.is_connected:
            try:
                if self.websocket and not self.websocket.closed:
                    await self.websocket.ping()
                await asyncio.sleep(30)  # 30초마다 핑
            except Exception as e:
                logger.warning(f"하트비트 실패: {e}")
                break
    
    async def subscribe_realtime_price(self, stock_code: str, callback: Callable = None):
        """실시간 시세 구독"""
        if not self.is_connected:
            await self.connect()
        
        try:
            approval_key = await self.auth.get_websocket_key()
            
            subscribe_data = {
                "header": {
                    "approval_key": approval_key,
                    "custtype": "P",
                    "tr_type": "1",
                    "content_type": "utf-8"
                },
                "body": {