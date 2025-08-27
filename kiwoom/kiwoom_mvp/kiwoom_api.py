# -*- coding: utf-8 -*-
"""
키움증권 주식 데이터 수집기 - 키움 OpenAPI+ 클라이언트
Phase 1 MVP

키움증권 OpenAPI+를 통한 로그인, 데이터 요청/수신 처리
이벤트 기반 비동기 통신 관리
"""

import sys
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
import pandas as pd

# PyQt5 및 키움 API 모듈
try:
    from PyQt5.QtCore import QEventLoop, QTimer, QObject, pyqtSignal
    from PyQt5.QAxContainer import QAxWidget
    from PyQt5.QtWidgets import QApplication
except ImportError as e:
    print("❌ PyQt5가 설치되지 않았습니다. pip install PyQt5를 실행하세요.")
    sys.exit(1)

from config import get_config

class KiwoomAPI(QAxWidget):
    """키움증권 OpenAPI+ 클라이언트 클래스"""
    
    # 시그널 정의 (이벤트 통신용)
    login_event_signal = pyqtSignal(int)
    tr_event_signal = pyqtSignal(str, str, str, str, str)
    
    def __init__(self):
        """키움 API 초기화"""
        super().__init__()
        
        # 설정 로드
        self.config = get_config()
        
        # 로깅 설정
        self.logger = logging.getLogger(__name__)
        
        # 연결 상태 관리
        self.connected = False
        self.login_status = False
        self.account_list = []
        self.account_number = ""
        
        # 데이터 수신 관리
        self.tr_data = {}
        self.tr_event_loop = None
        self.tr_request_count = 0
        self.last_tr_time = 0
        
        # TR 코드 정의
        self.TR_CODES = {
            'OPT10081': '일봉차트조회',
            'OPT10080': '주식분봉차트조회',
            'OPT10001': '주식기본정보요청',
            'OPTKWFID': '관심종목정보요청'
        }
        
        # 에러 코드 정의
        self.ERROR_CODES = {
            0: "정상처리",
            -100: "사용자정보교환실패", -101: "서버접속실패", -102: "버전처리실패",
            -103: "개인방화벽실패", -104: "메모리보호실패", -105: "함수입력값오류",
            -106: "통신연결종료", -107: "보안모듈오류", -108: "공인인증로그인필요",
            -200: "시세조회과부하", -201: "REQUEST_INPUT_st입력오류", -202: "요청전문작성오류",
            -203: "조회가능한종목수초과", -300: "주문입력오류", -301: "계좌비밀번호없음",
            -302: "타인계좌사용오류", -303: "주문가격이상오류", -304: "주문수량이상오류",
            -305: "주문전송오류", -306: "계좌정보없음"
        }
        
        try:
            # 키움 OpenAPI+ ActiveX 컨트롤 생성
            self.setControl("KHOPENAPI.KHOpenAPICtrl.1")
            
            # 이벤트 연결
            self.OnEventConnect.connect(self._on_event_connect)
            self.OnReceiveTrData.connect(self._on_receive_tr_data)
            self.OnReceiveRealData.connect(self._on_receive_real_data)
            self.OnReceiveMsg.connect(self._on_receive_msg)
            self.OnReceiveChejanData.connect(self._on_receive_chejan_data)
            
            self.logger.info("✅ 키움 OpenAPI+ 초기화 완료")
            self.connected = True
            
        except Exception as e:
            self.logger.error(f"❌ 키움 OpenAPI+ 초기화 실패: {e}")
            self.connected = False
    
    def connect_to_server(self) -> bool:
        """키움 서버에 로그인"""
        if not self.connected:
            self.logger.error("❌ OpenAPI+ 초기화가 완료되지 않았습니다.")
            return False
        
        self.logger.info("🔄 키움증권 로그인 시도 중...")
        
        try:
            # 이벤트 루프 생성
            login_event_loop = QEventLoop()
            
            # 로그인 이벤트 시그널 연결
            def on_login_slot(err_code):
                self.logger.debug(f"로그인 응답 수신: {err_code}")
                login_event_loop.exit()
            
            self.login_event_signal.connect(on_login_slot)
            
            # 로그인 요청
            result = self.dynamicCall("CommConnect()")
            
            if result == 0:
                self.logger.info("🔄 로그인 요청 전송 완료, 응답 대기 중...")
                
                # 30초 타임아웃으로 응답 대기
                timer = QTimer()
                timer.timeout.connect(login_event_loop.quit)
                timer.start(30000)  # 30초
                
                login_event_loop.exec_()
                timer.stop()
                
                # 로그인 상태 확인
                if self.login_status:
                    self.logger.info("✅ 키움증권 로그인 성공")
                    self._get_account_info()
                    return True
                else:
                    self.logger.error("❌ 키움증권 로그인 실패 (타임아웃 또는 오류)")
                    return False
            else:
                self.logger.error(f"❌ 로그인 요청 실패: {result}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 로그인 과정에서 오류 발생: {e}")
            return False
    
    def _on_event_connect(self, err_code):
        """로그인 이벤트 처리"""
        if err_code == 0:
            self.login_status = True
            self.logger.info("✅ 로그인 성공")
        else:
            self.login_status = False
            error_msg = self.ERROR_CODES.get(err_code, f"알 수 없는 오류 ({err_code})")
            self.logger.error(f"❌ 로그인 실패: {error_msg}")
        
        # 시그널 발생
        self.login_event_signal.emit(err_code)
    
    def _get_account_info(self):
        """계좌 정보 조회"""
        try:
            # 계좌번호 목록 조회
            account_list = self.dynamicCall("GetLoginInfo(QString)", "ACCNO")
            self.account_list = account_list.split(';')[:-1]  # 마지막 빈 문자열 제거
            
            if self.account_list:
                self.account_number = self.account_list[0]  # 첫 번째 계좌 사용
                self.logger.info(f"📊 계좌 정보 조회 완료: {len(self.account_list)}개 계좌")
                self.logger.info(f"📊 사용 계좌: {self.account_number}")
            else:
                self.logger.warning("⚠️ 사용 가능한 계좌가 없습니다.")
            
            # 사용자 정보 조회
            user_id = self.dynamicCall("GetLoginInfo(QString)", "USER_ID")
            user_name = self.dynamicCall("GetLoginInfo(QString)", "USER_NAME")
            self.logger.info(f"👤 사용자 정보: {user_name} ({user_id})")
            
        except Exception as e:
            self.logger.error(f"❌ 계좌 정보 조회 실패: {e}")
    
    def get_stock_basic_info(self, stock_code: str) -> Optional[Dict]:
        """종목 기본 정보 조회"""
        if not self.login_status:
            self.logger.error("❌ 로그인이 필요합니다.")
            return None
        
        try:
            # TR 요청 간격 조절
            self._wait_for_tr_limit()
            
            # TR 데이터 초기화
            self.tr_data.clear()
            
            # 이벤트 루프 생성
            self.tr_event_loop = QEventLoop()
            
            # 입력값 설정
            self.dynamicCall("SetInputValue(QString, QString)", "종목코드", stock_code)
            
            # TR 요청
            request_name = "주식기본정보요청"
            screen_no = "0001"
            
            result = self.dynamicCall(
                "CommRqData(QString, QString, int, QString)",
                request_name, "OPT10001", 0, screen_no
            )
            
            if result == 0:
                self.logger.debug(f"🔄 {stock_code} 기본정보 요청 전송")
                
                # 응답 대기 (최대 15초)
                timer = QTimer()
                timer.timeout.connect(self.tr_event_loop.quit)
                timer.start(15000)
                
                self.tr_event_loop.exec_()
                timer.stop()
                
                # 응답 데이터 확인
                if "OPT10001" in self.tr_data:
                    data = self.tr_data["OPT10001"]
                    self.logger.info(f"✅ {stock_code} 기본정보 조회 완료")
                    return data
                else:
                    self.logger.warning(f"⚠️ {stock_code} 기본정보 응답 없음")
                    return None
            else:
                error_msg = self.ERROR_CODES.get(result, f"알 수 없는 오류 ({result})")
                self.logger.error(f"❌ 기본정보 요청 실패: {error_msg}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ 기본정보 조회 중 오류: {e}")
            return None
    
    def get_daily_stock_data(self, stock_code: str, period_days: int = 30) -> Optional[pd.DataFrame]:
        """일봉 데이터 조회"""
        if not self.login_status:
            self.logger.error("❌ 로그인이 필요합니다.")
            return None
        
        try:
            # 날짜 계산
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=period_days * 2)).strftime('%Y%m%d')  # 여유분 포함
            
            self.logger.info(f"📊 {stock_code} 일봉 데이터 수집 시작 (최근 {period_days}일)")
            
            all_data = []
            next_code = ""
            request_count = 0
            max_requests = 5  # 최대 요청 횟수 제한
            
            while request_count < max_requests:
                # TR 요청 간격 조절
                self._wait_for_tr_limit()
                
                # TR 데이터 초기화
                self.tr_data.clear()
                
                # 이벤트 루프 생성
                self.tr_event_loop = QEventLoop()
                
                # 입력값 설정
                self.dynamicCall("SetInputValue(QString, QString)", "종목코드", stock_code)
                self.dynamicCall("SetInputValue(QString, QString)", "기준일자", end_date)
                self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")  # 수정주가
                
                # TR 요청 (연속조회 여부)
                prev_next = 2 if next_code else 0
                screen_no = "0081"
                
                result = self.dynamicCall(
                    "CommRqData(QString, QString, int, QString)",
                    "일봉차트조회", "OPT10081", prev_next, screen_no
                )
                
                if result != 0:
                    error_msg = self.ERROR_CODES.get(result, f"알 수 없는 오류 ({result})")
                    self.logger.error(f"❌ 일봉데이터 요청 실패: {error_msg}")
                    break
                
                # 응답 대기
                timer = QTimer()
                timer.timeout.connect(self.tr_event_loop.quit)
                timer.start(15000)
                
                self.tr_event_loop.exec_()
                timer.stop()
                
                # 응답 데이터 처리
                if "OPT10081" not in self.tr_data:
                    self.logger.warning("⚠️ 일봉데이터 응답 없음")
                    break
                
                data_info = self.tr_data["OPT10081"]
                current_data = data_info.get('data', [])
                next_code = data_info.get('next_code', "")
                
                if not current_data:
                    self.logger.info("📊 더 이상 데이터가 없습니다.")
                    break
                
                all_data.extend(current_data)
                request_count += 1
                
                self.logger.info(f"📈 수집된 데이터: {len(current_data)}개 (총 {len(all_data)}개)")
                
                # 목표 개수 달성시 종료
                if len(all_data) >= period_days:
                    self.logger.info(f"✅ 목표 데이터 개수 달성: {len(all_data)}개")
                    break
                
                # 연속조회 여부 확인
                if not next_code or next_code.strip() == "":
                    self.logger.info("📊 연속조회할 데이터가 없습니다.")
                    break
            
            if not all_data:
                self.logger.warning(f"⚠️ {stock_code} 일봉 데이터 없음")
                return None
            
            # 데이터프레임 생성
            df = pd.DataFrame(all_data)
            
            # 날짜순 정렬 (과거 → 현재)
            df = df.sort_values('날짜').reset_index(drop=True)
            
            # 기간 필터링
            if len(df) > period_days:
                df = df.tail(period_days).reset_index(drop=True)
            
            self.logger.info(f"✅ {stock_code} 일봉 데이터 수집 완료: {len(df)}개")
            return df
            
        except Exception as e:
            self.logger.error(f"❌ 일봉 데이터 조회 중 오류: {e}")
            return None
    
    def _on_receive_tr_data(self, screen_no, rq_name, tr_code, record_name, prev_next):
        """TR 데이터 수신 이벤트 처리"""
        try:
            self.logger.debug(f"📥 TR 데이터 수신: {tr_code} ({rq_name})")
            
            if tr_code == "OPT10001":  # 주식기본정보
                self._parse_basic_info(tr_code)
            elif tr_code == "OPT10081":  # 일봉차트
                self._parse_daily_data(tr_code, prev_next)
            
        except Exception as e:
            self.logger.error(f"❌ TR 데이터 처리 중 오류: {e}")
        finally:
            # 이벤트 루프 종료
            if self.tr_event_loop:
                self.tr_event_loop.exit()
    
    def _parse_basic_info(self, tr_code):
        """기본정보 데이터 파싱"""
        try:
            stock_name = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, "", 0, "종목명").strip()
            current_price = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, "", 0, "현재가").strip())
            volume = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, "", 0, "거래량").strip())
            
            self.tr_data[tr_code] = {
                '종목명': stock_name,
                '현재가': current_price,
                '거래량': volume
            }
            
            self.logger.debug(f"📊 기본정보 파싱: {stock_name} {current_price:,}원")
            
        except Exception as e:
            self.logger.error(f"❌ 기본정보 파싱 오류: {e}")
    
    def _parse_daily_data(self, tr_code, prev_next):
        """일봉 데이터 파싱"""
        try:
            data_count = self.dynamicCall("GetRepeatCnt(QString, QString)", tr_code, "")
            self.logger.debug(f"📊 일봉 데이터 개수: {data_count}")
            
            data_list = []
            for i in range(data_count):
                date = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, "", i, "일자").strip()
                open_price = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, "", i, "시가").strip())
                high_price = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, "", i, "고가").strip())
                low_price = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, "", i, "저가").strip())
                close_price = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, "", i, "현재가").strip())
                volume = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, "", i, "거래량").strip())
                
                data_list.append({
                    '날짜': date,
                    '시가': open_price,
                    '고가': high_price,
                    '저가': low_price,
                    '종가': close_price,
                    '거래량': volume
                })
            
            # 연속조회 코드
            next_code = self.dynamicCall("GetCommData(QString, QString, int, QString)", tr_code, "", 0, "연속조회검색조건").strip()
            
            self.tr_data[tr_code] = {
                'data': data_list,
                'next_code': next_code
            }
            
            self.logger.debug(f"📈 일봉 데이터 파싱 완료: {len(data_list)}개")
            
        except Exception as e:
            self.logger.error(f"❌ 일봉 데이터 파싱 오류: {e}")
    
    def _wait_for_tr_limit(self):
        """TR 요청 제한 준수 (초당 5회 제한)"""
        current_time = time.time()
        time_diff = current_time - self.last_tr_time
        
        if time_diff < self.config.TR_REQUEST_INTERVAL:
            wait_time = self.config.TR_REQUEST_INTERVAL - time_diff
            self.logger.debug(f"⏱️ TR 제한 대기: {wait_time:.2f}초")
            time.sleep(wait_time)
        
        self.last_tr_time = time.time()
        self.tr_request_count += 1
    
    def _on_receive_real_data(self, stock_code, real_type, real_data):
        """실시간 데이터 수신 (현재 사용 안함)"""
        pass
    
    def _on_receive_msg(self, screen_no, rq_name, tr_code, msg):
        """메시지 수신"""
        self.logger.debug(f"📨 메시지: {msg}")
    
    def _on_receive_chejan_data(self, gubun, item_cnt, fid_list):
        """체결잔고 데이터 수신 (Phase 2에서 사용 예정)"""
        pass
    
    def disconnect(self):
        """연결 종료"""
        if self.login_status:
            self.dynamicCall("CommTerminate()")
            self.login_status = False
            self.logger.info("🔌 키움 API 연결 종료")
    
    def is_connected(self) -> bool:
        """연결 상태 확인"""
        return self.login_status
    
    def get_connection_info(self) -> Dict:
        """연결 정보 반환"""
        return {
            'connected': self.connected,
            'login_status': self.login_status,
            'account_count': len(self.account_list),
            'account_number': self.account_number,
            'tr_request_count': self.tr_request_count
        }

class KiwoomManager:
    """키움 API 관리자 클래스 (QApplication 관리)"""
    
    def __init__(self):
        """매니저 초기화"""
        self.app = None
        self.api = None
        self.logger = logging.getLogger(__name__)
    
    def initialize(self) -> bool:
        """키움 API 초기화"""
        try:
            # QApplication 생성 (이미 존재하면 재사용)
            if not QApplication.instance():
                self.app = QApplication(sys.argv)
                self.logger.info("✅ QApplication 생성 완료")
            else:
                self.app = QApplication.instance()
                self.logger.info("✅ 기존 QApplication 사용")
            
            # 키움 API 인스턴스 생성
            self.api = KiwoomAPI()
            
            if self.api.connected:
                self.logger.info("✅ 키움 API 매니저 초기화 완료")
                return True
            else:
                self.logger.error("❌ 키움 API 초기화 실패")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 키움 API 매니저 초기화 오류: {e}")
            return False
    
    def connect(self) -> bool:
        """키움 서버 연결"""
        if not self.api:
            self.logger.error("❌ API가 초기화되지 않았습니다.")
            return False
        
        return self.api.connect_to_server()
    
    def get_api(self) -> Optional[KiwoomAPI]:
        """API 인스턴스 반환"""
        return self.api
    
    def cleanup(self):
        """정리 작업"""
        if self.api:
            self.api.disconnect()
        
        if self.app:
            self.app.quit()
        
        self.logger.info("🧹 키움 API 매니저 정리 완료")

# 전역 매니저 인스턴스
_manager = None

def get_kiwoom_manager() -> KiwoomManager:
    """키움 매니저 싱글톤 인스턴스 반환"""
    global _manager
    if _manager is None:
        _manager = KiwoomManager()
    return _manager

if __name__ == "__main__":
    # 테스트 코드
    import logging
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🧪 키움 API 테스트 시작...")
    
    # 매니저 생성 및 초기화
    manager = get_kiwoom_manager()
    
    if manager.initialize():
        print("✅ 키움 API 초기화 성공")
        
        if manager.connect():
            print("✅ 키움 서버 연결 성공")
            
            api = manager.get_api()
            if api:
                # 연결 정보 출력
                info = api.get_connection_info()
                print(f"📊 연결 정보: {info}")
                
                # 기본정보 조회 테스트 (삼성전자)
                print("🔍 삼성전자 기본정보 조회 테스트...")
                basic_info = api.get_stock_basic_info("005930")
                if basic_info:
                    print(f"✅ 기본정보: {basic_info}")
                
                # 일봉 데이터 조회 테스트
                print("📈 삼성전자 일봉 데이터 조회 테스트...")
                daily_data = api.get_daily_stock_data("005930", 5)  # 최근 5일
                if daily_data is not None:
                    print(f"✅ 일봉 데이터: {len(daily_data)}개")
                    print(daily_data.head())
        else:
            print("❌ 키움 서버 연결 실패")
    else:
        print("❌ 키움 API 초기화 실패")
    
    # 정리
    manager.cleanup()
    print("🎉 키움 API 테스트 완료")