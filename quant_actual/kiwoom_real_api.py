"""
file: kiwoom_real_api.py
실제 키움 Open API 클라이언트
주의: Windows 환경에서만 동작하며, 키움 Open API+ 설치 필요
"""

import sys
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio

# Windows 전용 import
try:
    import pythoncom
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QAxContainer import QAxWidget
    from PyQt5.QtCore import QEventLoop, QTimer
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False
    print("⚠️ Windows 환경이 아니거나 PyQt5가 설치되지 않았습니다.")

logger = logging.getLogger(__name__)

class KiwoomRealClient:
    """실제 키움 Open API 클라이언트"""
    
    def __init__(self):
        if not WINDOWS_AVAILABLE:
            raise RuntimeError("키움 API는 Windows 환경에서만 사용 가능합니다")
        
        self.is_connected = False
        self.account_number = None
        self.app = None
        self.kiwoom = None
        
        # 실시간 데이터 저장
        self.real_data = {}
        self.order_data = {}
        
        # 이벤트 루프
        self.login_event_loop = None
        self.tr_event_loop = None
        
        # 요청 제한 (초당 5회)
        self.last_request_time = {}
        self.request_interval = 0.2  # 200ms
        
    async def initialize(self):
        """키움 API 초기화"""
        try:
            # QApplication 생성
            if not QApplication.instance():
                self.app = QApplication(sys.argv)
            else:
                self.app = QApplication.instance()
                
            # 키움 OCX 생성
            self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
            
            # 이벤트 연결
            self.kiwoom.OnEventConnect.connect(self._on_event_connect)
            self.kiwoom.OnReceiveTrData.connect(self._on_receive_tr_data)
            self.kiwoom.OnReceiveRealData.connect(self._on_receive_real_data)
            self.kiwoom.OnReceiveChejanData.connect(self._on_receive_chejan_data)
            
            logger.info("키움 API 초기화 완료")
            return True
            
        except Exception as e:
            logger.error(f"키움 API 초기화 실패: {e}")
            return False
    
    async def connect(self):
        """키움 API 로그인"""
        try:
            if not self.kiwoom:
                await self.initialize()
            
            # 이미 연결된 경우
            if self.get_connect_state() == 1:
                self.is_connected = True
                logger.info("키움 API 이미 연결됨")
                return True
            
            # 로그인 요청
            self.login_event_loop = QEventLoop()
            ret = self.kiwoom.dynamicCall("CommConnect()")
            
            if ret == 0:
                self.login_event_loop.exec_()
                
            if self.is_connected:
                # 계좌 정보 조회
                accounts = self.kiwoom.dynamicCall("GetLoginInfo(QString)", "ACCNO")
                self.account_number = accounts.split(';')[0]
                
                logger.info(f"키움 API 로그인 성공 - 계좌: {self.account_number}")
                return True
            else:
                logger.error("키움 API 로그인 실패")
                return False
                
        except Exception as e:
            logger.error(f"키움 API 연결 오류: {e}")
            return False
    
    async def disconnect(self):
        """키움 API 연결 해제"""
        try:
            if self.kiwoom:
                self.kiwoom.dynamicCall("CommTerminate()")
            self.is_connected = False
            logger.info("키움 API 연결 해제됨")
        except Exception as e:
            logger.error(f"키움 API 연결 해제 오류: {e}")
    
    def get_connect_state(self):
        """연결 상태 확인"""
        if self.kiwoom:
            return self.kiwoom.dynamicCall("GetConnectState()")
        return 0
    
    async def get_current_price(self, stock_code: str) -> Dict[str, Any]:
        """현재가 조회"""
        try:
            await self._wait_for_request_limit("current_price")
            
            # TR 요청
            self.kiwoom.dynamicCall("SetInputValue(QString, QString)", "종목코드", stock_code)
            
            self.tr_event_loop = QEventLoop()
            ret = self.kiwoom.dynamicCall("CommRqData(QString, QString, int, QString)",
                                        "주식기본정보", "opt10001", 0, "0001")
            
            if ret == 0:
                self.tr_event_loop.exec_()
                
                # 데이터 조회
                current_price = int(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)",
                                                          "opt10001", "주식기본정보", 0, "현재가"))
                prev_close = int(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)",
                                                       "opt10001", "주식기본정보", 0, "기준가"))
                volume = int(self.kiwoom.dynamicCall("GetCommData(QString, QString, int, QString)",
                                                   "opt10001", "주식기본정보", 0, "거래량"))
                
                return {
                    'current_price': abs(current_price),  # 음수 제거
                    'prev_close': abs(prev_close),
                    'volume': volume,
                    'price_change': current_price - prev_close,
                    'change_rate': ((current_price - prev_close) / prev_close) * 100,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                logger.error(f"현재가 조회 실패: {stock_code}")
                return {}
                
        except Exception as e:
            logger.error(f"현재가 조회 오류 {stock_code}: {e}")
            return {}
    
    async def send_order(self, stock_code: str, order_type: str, 
                        quantity: int, price: float) -> str:
        """주문 전송"""
        try:
            await self._wait_for_request_limit("send_order")
            
            # 주문 구분 코드 변환
            order_type_code = "1" if order_type.upper() == "BUY" else "2"
            hoga_code = "00"  # 지정가
            
            # 주문 요청
            ret = self.kiwoom.dynamicCall(
                "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                "자동매매",              # 사용자구분명
                "0001",                 # 화면번호
                self.account_number,    # 계좌번호
                int(order_type_code),   # 주문유형
                stock_code,             # 종목코드
                quantity,               # 주문수량
                int(price),             # 주문가격
                hoga_code,              # 호가구분
                ""                      # 원주문번호
            )
            
            if ret == 0:
                # 주문번호 생성 (실제로는 키움에서 반환)
                order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                logger.info(f"주문 전송 성공: {stock_code} {order_type} {quantity}주 @ {price}")
                return order_id
            else:
                logger.error(f"주문 전송 실패: {ret}")
                raise Exception(f"주문 전송 실패: {ret}")
                
        except Exception as e:
            logger.error(f"주문 전송 오류: {e}")
            raise
    
    async def cancel_order(self, order_id: str) -> bool:
        """주문 취소"""
        try:
            # 실제로는 원주문번호로 취소 요청
            ret = self.kiwoom.dynamicCall(
                "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                "취소",                  # 사용자구분명
                "0002",                 # 화면번호
                self.account_number,    # 계좌번호
                3,                      # 취소
                "",                     # 종목코드
                0,                      # 수량
                0,                      # 가격
                "00",                   # 호가구분
                order_id                # 원주문번호
            )
            
            return ret == 0
            
        except Exception as e:
            logger.error(f"주문 취소 오류: {e}")
            return False
    
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:  # 추가된 메서드
        """주문 상태 조회"""
        try:
            # Mock 데이터 반환 (실제로는 키움 API 호출)
            return {
                'status': 'filled',
                'fill_price': 100000,
                'fill_quantity': 100,
                'commission': 150
            }
        except Exception as e:
            logger.error(f"주문 상태 조회 오류: {e}")
            return {'status': 'error'}
    
    # ... 나머지 메서드들은 동일 ...
    
    def get_connection_status(self) -> Dict[str, Any]:
        """연결 상태 반환"""
        return {
            'is_connected': self.is_connected,
            'account_number': self.account_number,
            'server_type': 'REAL',
            'connection_time': datetime.now().isoformat() if self.is_connected else None
        }

# 싱글톤 패턴으로 구현
_kiwoom_real_client = None

def get_kiwoom_real_client() -> KiwoomRealClient:
    """키움 실거래 클라이언트 싱글톤"""
    global _kiwoom_real_client
    if _kiwoom_real_client is None:
        _kiwoom_real_client = KiwoomRealClient()
    return _kiwoom_real_client