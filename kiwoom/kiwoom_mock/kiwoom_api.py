"""
file: kiwoom_mock/kiwoom_api.py
키움증권 OpenAPI 연동 모듈
"""

import sys
import logging
import time
import random
from typing import Dict, List, Optional, Any
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from config import Config

# 크로스 플랫폼 호환성
KIWOOM_AVAILABLE = False
QAxWidget = None

try:
    if sys.platform == "win32":
        from PyQt5.QAxContainer import QAxWidget
        KIWOOM_AVAILABLE = True
    else:
        # Windows가 아닌 경우 모의 모드
        KIWOOM_AVAILABLE = False
        QAxWidget = None
except ImportError:
    KIWOOM_AVAILABLE = False
    QAxWidget = None

class KiwoomAPI(QObject):
    """키움증권 OpenAPI 클래스"""
    
    # 시그널 정의
    login_completed = pyqtSignal(bool)
    data_received = pyqtSignal(str, dict)
    order_completed = pyqtSignal(str, dict)
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.connected = False
        self.account_list = []
        self.ocx = None
        
        # 키움 API 사용 가능한 경우에만 초기화
        if KIWOOM_AVAILABLE:
            try:
                self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
                if self.ocx:
                    self.setup_signals()
                    self.logger.info("키움 API 컨트롤 생성 성공")
                else:
                    self.logger.warning("키움 API 컨트롤 생성 실패 - 모의 모드로 전환")
                    self.ocx = None
            except Exception as e:
                self.logger.warning(f"키움 API 초기화 실패: {e} - 모의 모드로 전환")
                self.ocx = None
        
        if not KIWOOM_AVAILABLE or not self.ocx:
            self.logger.info("키움 API 사용 불가 - 모의 모드로 실행")
    
    def setup_signals(self):
        """키움 API 이벤트 시그널 연결"""
        try:
            if self.ocx and hasattr(self.ocx, 'OnEventConnect'):
                self.ocx.OnEventConnect.connect(self.on_event_connect)
                self.ocx.OnReceiveTrData.connect(self.on_receive_tr_data)
                self.ocx.OnReceiveChejanData.connect(self.on_receive_chejan_data)
                self.logger.info("키움 API 시그널 연결 완료")
            else:
                self.logger.warning("키움 API 시그널 연결 실패")
        except Exception as e:
            self.logger.error(f"키움 API 시그널 설정 오류: {e}")
    
    def initialize(self) -> bool:
        """API 초기화"""
        try:
            if not KIWOOM_AVAILABLE or not self.ocx:
                # 모의 모드
                self.connected = True
                self.account_list = [Config.DEFAULT_ACCOUNT]
                self.logger.info("모의 모드로 API 초기화 완료")
                return True
            
            # 실제 키움 API 초기화
            try:
                result = self.ocx.dynamicCall("CommConnect()")
                
                if result == 0:
                    self.logger.info("키움 API 연결 요청 성공")
                    return True
                else:
                    self.logger.error(f"키움 API 연결 실패: {result}")
                    # 실패 시 모의 모드로 전환
                    self.connected = True
                    self.account_list = [Config.DEFAULT_ACCOUNT]
                    return True
            except Exception as e:
                self.logger.error(f"키움 API 호출 오류: {e} - 모의 모드로 전환")
                self.connected = True
                self.account_list = [Config.DEFAULT_ACCOUNT]
                return True
                
        except Exception as e:
            self.logger.error(f"API 초기화 오류: {e}")
            # 모든 실패 시에도 모의 모드로 작동
            self.connected = True
            self.account_list = [Config.DEFAULT_ACCOUNT]
            return True
    
    def is_connected(self) -> bool:
        """연결 상태 확인"""
        if not KIWOOM_AVAILABLE or not self.ocx:
            return self.connected
        
        try:
            state = self.ocx.dynamicCall("GetConnectState()")
            return state == 1
        except:
            return self.connected
    
    def on_event_connect(self, err_code):
        """로그인 이벤트 처리"""
        if err_code == 0:
            self.connected = True
            self.account_list = self.get_account_list()
            self.logger.info("키움 API 로그인 성공")
            self.login_completed.emit(True)
        else:
            self.connected = False
            self.logger.error(f"키움 API 로그인 실패: {err_code}")
            self.login_completed.emit(False)
    
    def get_account_list(self) -> List[str]:
        """계좌 목록 조회"""
        if not KIWOOM_AVAILABLE or not self.ocx:
            return [Config.DEFAULT_ACCOUNT]
        
        try:
            accounts = self.ocx.dynamicCall("GetLoginInfo(String)", "ACCNO")
            return accounts.split(';')[:-1] if accounts else [Config.DEFAULT_ACCOUNT]
        except:
            return [Config.DEFAULT_ACCOUNT]
    
    def get_stock_price(self, stock_code: str) -> Dict[str, Any]:
        """주식 현재가 조회 (모의 데이터)"""
        try:
            if not KIWOOM_AVAILABLE or not self.ocx or Config.MOCK_MODE:
                # 모의 데이터 생성
                base_price = self.get_mock_price(stock_code)
                return {
                    'stock_code': stock_code,
                    'current_price': base_price,
                    'open_price': base_price + random.randint(-1000, 1000),
                    'high_price': base_price + random.randint(0, 2000),
                    'low_price': base_price - random.randint(0, 2000),
                    'volume': random.randint(100000, 10000000),
                    'change_rate': round(random.uniform(-5.0, 5.0), 2)
                }
            
            # 실제 API 호출 로직은 여기에 추가
            return self.request_stock_price(stock_code)
            
        except Exception as e:
            self.logger.error(f"주식 현재가 조회 오류: {e}")
            return {}
    
    def get_mock_price(self, stock_code: str) -> int:
        """모의 주가 생성"""
        # 종목별 기준 가격
        base_prices = {
            '005930': 70000,  # 삼성전자
            '000660': 120000, # SK하이닉스
            '035420': 180000, # NAVER
            '051910': 400000, # LG화학
            '006400': 150000, # 삼성SDI
            '035720': 50000,  # 카카오
            '207940': 800000, # 삼성바이오로직스
            '373220': 400000  # LG에너지솔루션
        }
        
        base = base_prices.get(stock_code, 10000)
        # ±5% 범위에서 랜덤 변동
        variation = random.uniform(-0.05, 0.05)
        return int(base * (1 + variation))
    
    def place_order(self, account_no: str, stock_code: str, order_type: str,
                   quantity: int, price: int) -> Dict[str, Any]:
        """주문 실행"""
        try:
            if not KIWOOM_AVAILABLE or not self.ocx or Config.MOCK_MODE:
                # 모의 주문 처리
                return self.mock_place_order(account_no, stock_code, order_type, quantity, price)
            
            # 실제 API 주문 로직
            return self.real_place_order(account_no, stock_code, order_type, quantity, price)
            
        except Exception as e:
            self.logger.error(f"주문 실행 오류: {e}")
            return {'success': False, 'error': str(e)}
    
    def mock_place_order(self, account_no: str, stock_code: str, order_type: str,
                        quantity: int, price: int) -> Dict[str, Any]:
        """모의 주문 처리"""
        try:
            # 모의 주문 성공률 95%
            if random.random() < 0.95:
                order_id = f"M{int(time.time())}{random.randint(1000, 9999)}"
                
                result = {
                    'success': True,
                    'order_id': order_id,
                    'account_no': account_no,
                    'stock_code': stock_code,
                    'order_type': order_type,
                    'quantity': quantity,
                    'price': price,
                    'status': '체결',
                    'message': '모의 주문 체결 완료'
                }
                
                self.logger.info(f"모의 주문 성공: {stock_code} {order_type} {quantity}주")
                return result
            else:
                return {
                    'success': False,
                    'error': '모의 주문 실패 (랜덤)',
                    'message': '주문이 거부되었습니다'
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def real_place_order(self, account_no: str, stock_code: str, order_type: str,
                        quantity: int, price: int) -> Dict[str, Any]:
        """실제 API 주문 처리"""
        try:
            if not self.ocx:
                return {'success': False, 'error': 'API 연결되지 않음'}
            
            # 키움 API 주문 함수 호출
            order_type_code = Config.ORDER_TYPES.get(order_type, '00')
            
            result = self.ocx.dynamicCall(
                "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                ["주문", "0101", account_no, 1, stock_code, quantity, price, order_type_code, ""]
            )
            
            if result == 0:
                return {
                    'success': True,
                    'message': '주문 전송 성공',
                    'order_type': order_type,
                    'quantity': quantity,
                    'price': price
                }
            else:
                return {
                    'success': False,
                    'error': f'주문 전송 실패: {result}'
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def request_stock_price(self, stock_code: str) -> Dict[str, Any]:
        """실제 주식 현재가 요청"""
        try:
            if not self.ocx:
                return {}
            
            # TR 요청
            self.ocx.dynamicCall("SetInputValue(QString, QString)", "종목코드", stock_code)
            result = self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", 
                                        "주식기본정보", "opt10001", 0, "0101")
            
            if result == 0:
                return {'success': True, 'message': '현재가 요청 성공'}
            else:
                return {'success': False, 'error': f'현재가 요청 실패: {result}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def on_receive_tr_data(self, screen_no, rqname, trcode, record_name, next):
        """TR 데이터 수신 이벤트"""
        try:
            if rqname == "주식기본정보":
                data = self.parse_stock_data(trcode)
                self.data_received.emit(rqname, data)
                
        except Exception as e:
            self.logger.error(f"TR 데이터 처리 오류: {e}")
    
    def parse_stock_data(self, trcode: str) -> Dict[str, Any]:
        """주식 데이터 파싱"""
        try:
            if not self.ocx:
                return {}
            
            data = {
                'current_price': self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", 
                                                    trcode, "주식기본정보", 0, "현재가"),
                'stock_name': self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", 
                                                 trcode, "주식기본정보", 0, "종목명"),
                'volume': self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", 
                                             trcode, "주식기본정보", 0, "거래량")
            }
            
            # 문자열을 정수로 변환
            for key in ['current_price', 'volume']:
                if data[key]:
                    data[key] = abs(int(data[key].strip()))
            
            return data
            
        except Exception as e:
            self.logger.error(f"주식 데이터 파싱 오류: {e}")
            return {}
    
    def on_receive_chejan_data(self, gubun, item_cnt, fid_list):
        """체결 데이터 수신 이벤트"""
        try:
            if gubun == "0":  # 주문체결
                order_data = self.parse_order_data(fid_list)
                self.order_completed.emit("주문체결", order_data)
            elif gubun == "1":  # 잔고변경
                balance_data = self.parse_balance_data(fid_list)
                self.data_received.emit("잔고변경", balance_data)
                
        except Exception as e:
            self.logger.error(f"체결 데이터 처리 오류: {e}")
    
    def parse_order_data(self, fid_list: str) -> Dict[str, Any]:
        """주문 데이터 파싱"""
        try:
            if not self.ocx:
                return {}
            
            data = {
                'stock_code': self.ocx.dynamicCall("GetChejanData(int)", 9001),
                'order_quantity': self.ocx.dynamicCall("GetChejanData(int)", 900),
                'order_price': self.ocx.dynamicCall("GetChejanData(int)", 901),
                'executed_quantity': self.ocx.dynamicCall("GetChejanData(int)", 911),
                'executed_price': self.ocx.dynamicCall("GetChejanData(int)", 910)
            }
            
            return data
            
        except Exception as e:
            self.logger.error(f"주문 데이터 파싱 오류: {e}")
            return {}
    
    def parse_balance_data(self, fid_list: str) -> Dict[str, Any]:
        """잔고 데이터 파싱"""
        try:
            if not self.ocx:
                return {}
            
            data = {
                'stock_code': self.ocx.dynamicCall("GetChejanData(int)", 9001),
                'quantity': self.ocx.dynamicCall("GetChejanData(int)", 930),
                'available_quantity': self.ocx.dynamicCall("GetChejanData(int)", 933),
                'avg_price': self.ocx.dynamicCall("GetChejanData(int)", 931)
            }
            
            return data
            
        except Exception as e:
            self.logger.error(f"잔고 데이터 파싱 오류: {e}")
            return {}
    
    def get_balance(self, account_no: str) -> Dict[str, Any]:
        """계좌 잔고 조회"""
        try:
            if not KIWOOM_AVAILABLE or not self.ocx or Config.MOCK_MODE:
                # 모의 잔고 반환
                return {
                    'balance': Config.INITIAL_BALANCE,
                    'buying_power': Config.INITIAL_BALANCE,
                    'total_asset': Config.INITIAL_BALANCE
                }
            
            # 실제 API 잔고 조회 로직
            return self.request_balance(account_no)
            
        except Exception as e:
            self.logger.error(f"잔고 조회 오류: {e}")
            return {
                'balance': Config.INITIAL_BALANCE,
                'buying_power': Config.INITIAL_BALANCE,
                'total_asset': Config.INITIAL_BALANCE
            }
    
    def request_balance(self, account_no: str) -> Dict[str, Any]:
        """실제 잔고 요청"""
        try:
            if not self.ocx:
                return {}
            
            self.ocx.dynamicCall("SetInputValue(QString, QString)", "계좌번호", account_no)
            result = self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", 
                                        "계좌평가잔고내역요청", "opw00018", 0, "0102")
            
            if result == 0:
                return {'success': True, 'message': '잔고 요청 성공'}
            else:
                return {'success': False, 'error': f'잔고 요청 실패: {result}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_stock_info(self, stock_code: str) -> Dict[str, Any]:
        """종목 정보 조회"""
        try:
            if not KIWOOM_AVAILABLE or not self.ocx or Config.MOCK_MODE:
                # 모의 종목 정보
                stock_name = Config.get_stock_name(stock_code)
                current_price = self.get_mock_price(stock_code)
                
                return {
                    'stock_code': stock_code,
                    'stock_name': stock_name,
                    'current_price': current_price,
                    'open_price': current_price + random.randint(-1000, 1000),
                    'high_price': current_price + random.randint(0, 2000),
                    'low_price': current_price - random.randint(0, 2000),
                    'volume': random.randint(100000, 5000000),
                    'change_rate': round(random.uniform(-5.0, 5.0), 2),
                    'market_cap': current_price * random.randint(1000000, 10000000)
                }
            
            # 실제 API 조회
            return self.get_stock_price(stock_code)
            
        except Exception as e:
            self.logger.error(f"종목 정보 조회 오류: {e}")
            # 에러 시에도 기본 모의 데이터 반환
            stock_name = Config.get_stock_name(stock_code)
            return {
                'stock_code': stock_code,
                'stock_name': stock_name,
                'current_price': self.get_mock_price(stock_code),
                'change_rate': 0.0,
                'volume': 0
            }
    
    def disconnect(self):
        """API 연결 해제"""
        try:
            if self.ocx and KIWOOM_AVAILABLE:
                self.ocx.dynamicCall("CommTerminate()")
            
            self.connected = False
            self.logger.info("키움 API 연결 해제 완료")
            
        except Exception as e:
            self.logger.error(f"API 연결 해제 오류: {e}")
    
    def __del__(self):
        """소멸자"""
        try:
            self.disconnect()
        except:
            pass