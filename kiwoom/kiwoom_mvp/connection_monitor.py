# -*- coding: utf-8 -*-
"""
키움증권 주식 데이터 수집기 - 연결 상태 모니터링
Phase 1 MVP

키움 API 연결 상태 실시간 모니터링, 단계별 진단
자동 재연결 시도, 상태 리포트 생성
"""

import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum

from config import get_config

if TYPE_CHECKING:
    pass

class ConnectionStatus(Enum):
    """연결 상태 열거형"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RECONNECTING = "reconnecting"

@dataclass
class ConnectionEvent:
    """연결 이벤트 정보"""
    timestamp: datetime
    status: ConnectionStatus
    message: str
    error_code: Optional[int] = None
    details: Optional[str] = None

@dataclass
class DiagnosticStep:
    """진단 단계 정보"""
    step_name: str
    step_number: int
    status: str  # "pending", "running", "success", "failed", "skipped"
    message: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_details: Optional[str] = None

class ConnectionMonitor:
    """키움 API 연결 상태 모니터링 클래스"""
    
    def __init__(self):
        """연결 모니터 초기화"""
        self.config = get_config()
        self.logger = logging.getLogger(__name__)
        
        # 연결 상태 관리
        self.current_status = ConnectionStatus.DISCONNECTED
        self.last_connection_time: Optional[datetime] = None
        self.total_connection_time = timedelta(0)
        self.connection_attempts = 0
        self.successful_connections = 0
        
        # 이벤트 히스토리
        self.connection_events: List[ConnectionEvent] = []
        self.max_events = 1000  # 최대 이벤트 저장 개수
        
        # 진단 정보
        self.diagnostic_steps: List[DiagnosticStep] = []
        self.current_diagnostic_step = 0
        
        # 모니터링 스레드
        self.monitoring_thread: Optional[threading.Thread] = None
        self.monitoring_active = False
        self.monitor_interval = 5  # 5초 간격 모니터링
        
        # 통계 정보
        self.stats = {
            'heartbeat_count': 0,
            'error_count': 0,
            'reconnect_count': 0,
            'data_requests': 0,
            'successful_requests': 0
        }
        
        # 콜백 함수들
        self.status_change_callbacks: List[Callable] = []
        
        # 진단 단계 정의
        self._init_diagnostic_steps()
    
    def _init_diagnostic_steps(self):
        """진단 단계 초기화"""
        self.diagnostic_steps = [
            DiagnosticStep(
                step_name="환경 확인",
                step_number=1,
                status="pending",
                message="Python 32bit, PyQt5, 키움 OpenAPI+ 확인"
            ),
            DiagnosticStep(
                step_name="COM 객체 생성",
                step_number=2,
                status="pending",
                message="CLSID 등록, 객체 생성, 이벤트 연결"
            ),
            DiagnosticStep(
                step_name="로그인 시도",
                step_number=3,
                status="pending",
                message="로그인 요청, 서버 응답, 인증 완료"
            ),
            DiagnosticStep(
                step_name="계좌 정보 조회",
                step_number=4,
                status="pending",
                message="계좌 번호 조회, 사용자 정보 확인"
            ),
            DiagnosticStep(
                step_name="시장 데이터 준비",
                step_number=5,
                status="pending",
                message="시세 서버 연결, TR 요청 준비"
            )
        ]
    
    def start_monitoring(self):
        """모니터링 시작"""
        if self.monitoring_active:
            self.logger.warning("⚠️ 모니터링이 이미 실행 중입니다.")
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitoring_thread.start()
        
        self.logger.info("🔍 연결 상태 모니터링 시작")
    
    def stop_monitoring(self):
        """모니터링 중지"""
        self.monitoring_active = False
        
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=2)
        
        self.logger.info("⏹️ 연결 상태 모니터링 중지")
    
    def _monitoring_loop(self):
        """모니터링 루프"""
        while self.monitoring_active:
            try:
                # 주기적 상태 확인
                self._check_connection_health()
                
                # 하트비트 카운트 증가
                self.stats['heartbeat_count'] += 1
                
                # 대기
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                self.logger.error(f"❌ 모니터링 루프 오류: {e}")
                time.sleep(self.monitor_interval)
    
    def _check_connection_health(self):
        """연결 상태 건강성 확인"""
        try:
            # 현재 상태에 따른 처리
            if self.current_status == ConnectionStatus.CONNECTED:
                # 연결 시간 업데이트
                if self.last_connection_time:
                    current_session = datetime.now() - self.last_connection_time
                    # 총 연결 시간은 별도로 추적 (연결이 끊어지면 누적)
            
            elif self.current_status == ConnectionStatus.ERROR:
                # 에러 상태가 일정 시간 지속되면 자동 재연결 시도
                self._consider_auto_reconnect()
            
        except Exception as e:
            self.logger.error(f"❌ 연결 건강성 확인 실패: {e}")
    
    def _consider_auto_reconnect(self):
        """자동 재연결 고려"""
        # 현재 MVP에서는 자동 재연결 미구현
        # Phase 2에서 추가 예정
        pass
    
    def set_status(self, status: ConnectionStatus, message: str = "", 
                   error_code: Optional[int] = None, details: Optional[str] = None):
        """연결 상태 설정"""
        old_status = self.current_status
        self.current_status = status
        
        # 이벤트 기록
        event = ConnectionEvent(
            timestamp=datetime.now(),
            status=status,
            message=message,
            error_code=error_code,
            details=details
        )
        
        self._add_event(event)
        
        # 상태별 특별 처리
        if status == ConnectionStatus.CONNECTED:
            if old_status != ConnectionStatus.CONNECTED:
                self.last_connection_time = datetime.now()
                self.successful_connections += 1
                self.logger.info(f"✅ 연결 성공: {message}")
        
        elif status == ConnectionStatus.ERROR:
            self.stats['error_count'] += 1
            self.logger.error(f"❌ 연결 오류: {message}")
        
        elif status == ConnectionStatus.CONNECTING:
            self.connection_attempts += 1
            self.logger.info(f"🔄 연결 시도: {message}")
        
        elif status == ConnectionStatus.RECONNECTING:
            self.stats['reconnect_count'] += 1
            self.logger.info(f"🔄 재연결 시도: {message}")
        
        # 콜백 호출
        self._notify_status_change(old_status, status, message)
    
    def _add_event(self, event: ConnectionEvent):
        """이벤트 추가"""
        self.connection_events.append(event)
        
        # 최대 개수 초과시 오래된 이벤트 제거
        if len(self.connection_events) > self.max_events:
            self.connection_events = self.connection_events[-self.max_events:]
    
    def _notify_status_change(self, old_status: ConnectionStatus, 
                            new_status: ConnectionStatus, message: str):
        """상태 변경 콜백 호출"""
        for callback in self.status_change_callbacks:
            try:
                callback(old_status, new_status, message)
            except Exception as e:
                self.logger.error(f"❌ 상태 변경 콜백 오류: {e}")
    
    def add_status_change_callback(self, callback: Callable):
        """상태 변경 콜백 추가"""
        if callback not in self.status_change_callbacks:
            self.status_change_callbacks.append(callback)
    
    def remove_status_change_callback(self, callback: Callable):
        """상태 변경 콜백 제거"""
        if callback in self.status_change_callbacks:
            self.status_change_callbacks.remove(callback)
    
    def start_diagnostic(self, steps_to_run: Optional[List[int]] = None):
        """진단 시작"""
        if steps_to_run is None:
            steps_to_run = [1, 2, 3, 4, 5]  # 모든 단계
        
        self.logger.info("🔍 연결 진단 시작")
        
        # 모든 단계를 pending으로 초기화
        for step in self.diagnostic_steps:
            if step.step_number in steps_to_run:
                step.status = "pending"
                step.start_time = None
                step.end_time = None
                step.error_details = None
            else:
                step.status = "skipped"
        
        self.current_diagnostic_step = 0
    
    def update_diagnostic_step(self, step_number: int, status: str, 
                              message: str = "", error_details: str = None):
        """진단 단계 업데이트"""
        for step in self.diagnostic_steps:
            if step.step_number == step_number:
                old_status = step.status
                step.status = status
                step.message = message or step.message
                step.error_details = error_details
                
                if status == "running" and old_status == "pending":
                    step.start_time = datetime.now()
                elif status in ["success", "failed"] and step.start_time:
                    step.end_time = datetime.now()
                
                self.logger.debug(f"📊 진단 단계 {step_number}: {status} - {message}")
                break
    
    def get_diagnostic_report(self) -> Dict:
        """진단 리포트 생성"""
        report = {
            'start_time': None,
            'end_time': None,
            'total_duration': None,
            'overall_status': 'pending',
            'steps': [],
            'summary': {
                'total_steps': len(self.diagnostic_steps),
                'completed_steps': 0,
                'failed_steps': 0,
                'success_rate': 0
            }
        }
        
        completed_steps = []
        failed_steps = []
        
        for step in self.diagnostic_steps:
            step_info = {
                'step_number': step.step_number,
                'step_name': step.step_name,
                'status': step.status,
                'message': step.message,
                'start_time': step.start_time,
                'end_time': step.end_time,
                'duration': None,
                'error_details': step.error_details
            }
            
            if step.start_time and step.end_time:
                step_info['duration'] = (step.end_time - step.start_time).total_seconds()
            
            report['steps'].append(step_info)
            
            if step.status == "success":
                completed_steps.append(step)
            elif step.status == "failed":
                failed_steps.append(step)
        
        # 전체 시간 계산
        if self.diagnostic_steps:
            start_times = [s.start_time for s in self.diagnostic_steps if s.start_time]
            end_times = [s.end_time for s in self.diagnostic_steps if s.end_time]
            
            if start_times:
                report['start_time'] = min(start_times)
            if end_times:
                report['end_time'] = max(end_times)
            
            if report['start_time'] and report['end_time']:
                report['total_duration'] = (report['end_time'] - report['start_time']).total_seconds()
        
        # 요약 정보
        report['summary']['completed_steps'] = len(completed_steps)
        report['summary']['failed_steps'] = len(failed_steps)
        
        total_attempted = len([s for s in self.diagnostic_steps if s.status != "skipped"])
        if total_attempted > 0:
            report['summary']['success_rate'] = (len(completed_steps) / total_attempted) * 100
        
        # 전체 상태 결정
        if failed_steps:
            report['overall_status'] = 'failed'
        elif len(completed_steps) == total_attempted and total_attempted > 0:
            report['overall_status'] = 'success'
        elif any(s.status == "running" for s in self.diagnostic_steps):
            report['overall_status'] = 'running'
        else:
            report['overall_status'] = 'pending'
        
        return report
    
    def get_connection_info(self) -> Dict:
        """연결 정보 조회"""
        info = {
            'current_status': self.current_status.value,
            'status_message': self._get_status_message(),
            'connection_attempts': self.connection_attempts,
            'successful_connections': self.successful_connections,
            'last_connection_time': self.last_connection_time,
            'total_connection_time': self._calculate_total_connection_time(),
            'current_session_time': self._calculate_current_session_time(),
            'success_rate': self._calculate_success_rate(),
            'stats': self.stats.copy()
        }
        
        return info
    
    def _get_status_message(self) -> str:
        """현재 상태 메시지"""
        status_messages = {
            ConnectionStatus.DISCONNECTED: "연결 해제됨",
            ConnectionStatus.CONNECTING: "연결 시도 중",
            ConnectionStatus.CONNECTED: "정상 연결됨",
            ConnectionStatus.ERROR: "연결 오류 발생",
            ConnectionStatus.RECONNECTING: "재연결 시도 중"
        }
        return status_messages.get(self.current_status, "알 수 없는 상태")
    
    def _calculate_total_connection_time(self) -> timedelta:
        """총 연결 시간 계산"""
        total_time = self.total_connection_time
        
        # 현재 연결 중이면 현재 세션 시간 추가
        if (self.current_status == ConnectionStatus.CONNECTED and 
            self.last_connection_time):
            current_session = datetime.now() - self.last_connection_time
            total_time += current_session
        
        return total_time
    
    def _calculate_current_session_time(self) -> Optional[timedelta]:
        """현재 세션 연결 시간 계산"""
        if (self.current_status == ConnectionStatus.CONNECTED and 
            self.last_connection_time):
            return datetime.now() - self.last_connection_time
        return None
    
    def _calculate_success_rate(self) -> float:
        """연결 성공률 계산"""
        if self.connection_attempts == 0:
            return 0.0
        return (self.successful_connections / self.connection_attempts) * 100
    
    def get_recent_events(self, count: int = 10) -> List[ConnectionEvent]:
        """최근 이벤트 조회"""
        return self.connection_events[-count:] if self.connection_events else []
    
    def get_events_by_status(self, status: ConnectionStatus, 
                           since: Optional[datetime] = None) -> List[ConnectionEvent]:
        """상태별 이벤트 조회"""
        filtered_events = [e for e in self.connection_events if e.status == status]
        
        if since:
            filtered_events = [e for e in filtered_events if e.timestamp >= since]
        
        return filtered_events
    
    def record_data_request(self, successful: bool = True):
        """데이터 요청 기록"""
        self.stats['data_requests'] += 1
        if successful:
            self.stats['successful_requests'] += 1
    
    def clear_events(self):
        """이벤트 히스토리 클리어"""
        self.connection_events.clear()
        self.logger.info("🧹 연결 이벤트 히스토리 클리어")
    
    def reset_stats(self):
        """통계 초기화"""
        self.stats = {
            'heartbeat_count': 0,
            'error_count': 0,
            'reconnect_count': 0,
            'data_requests': 0,
            'successful_requests': 0
        }
        self.connection_attempts = 0
        self.successful_connections = 0
        self.total_connection_time = timedelta(0)
        self.logger.info("🧹 연결 통계 초기화")
    
    def generate_status_report(self) -> str:
        """상태 리포트 생성 (텍스트 형태)"""
        info = self.get_connection_info()
        report_lines = []
        
        report_lines.append("=" * 50)
        report_lines.append("📊 키움 API 연결 상태 리포트")
        report_lines.append("=" * 50)
        
        # 현재 상태
        status_emoji = {
            'connected': '✅',
            'connecting': '🔄',
            'disconnected': '❌',
            'error': '❌',
            'reconnecting': '🔄'
        }
        
        emoji = status_emoji.get(info['current_status'], '❓')
        report_lines.append(f"{emoji} 현재 상태: {info['status_message']}")
        
        # 연결 통계
        report_lines.append(f"📈 연결 시도: {info['connection_attempts']}회")
        report_lines.append(f"✅ 성공 연결: {info['successful_connections']}회")
        report_lines.append(f"📊 성공률: {info['success_rate']:.1f}%")
        
        # 시간 정보
        if info['last_connection_time']:
            report_lines.append(f"🕐 마지막 연결: {info['last_connection_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        if info['current_session_time']:
            session_time = str(info['current_session_time']).split('.')[0]  # 초 단위까지만
            report_lines.append(f"⏱️  현재 세션: {session_time}")
        
        total_time = str(info['total_connection_time']).split('.')[0]
        report_lines.append(f"⏳ 총 연결 시간: {total_time}")
        
        # 활동 통계
        report_lines.append("\n📊 활동 통계:")
        stats = info['stats']
        report_lines.append(f"   - 하트비트: {stats['heartbeat_count']}회")
        report_lines.append(f"   - 데이터 요청: {stats['data_requests']}회")
        report_lines.append(f"   - 성공 요청: {stats['successful_requests']}회")
        report_lines.append(f"   - 오류 발생: {stats['error_count']}회")
        report_lines.append(f"   - 재연결 시도: {stats['reconnect_count']}회")
        
        # 최근 이벤트
        recent_events = self.get_recent_events(5)
        if recent_events:
            report_lines.append("\n📝 최근 이벤트:")
            for event in reversed(recent_events):  # 최신순
                time_str = event.timestamp.strftime('%H:%M:%S')
                status_emoji = {
                    ConnectionStatus.CONNECTED: '✅',
                    ConnectionStatus.CONNECTING: '🔄',
                    ConnectionStatus.DISCONNECTED: '❌',
                    ConnectionStatus.ERROR: '❌',
                    ConnectionStatus.RECONNECTING: '🔄'
                }
                emoji = status_emoji.get(event.status, '❓')
                report_lines.append(f"   [{time_str}] {emoji} {event.message}")
        
        report_lines.append("=" * 50)
        
        return "\n".join(report_lines)
    
    def export_diagnostic_log(self, filepath: str) -> bool:
        """진단 로그 내보내기"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # 리포트 헤더
                f.write(f"키움 API 연결 진단 로그\n")
                f.write(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n\n")
                
                # 진단 리포트
                diagnostic_report = self.get_diagnostic_report()
                f.write("📊 진단 요약:\n")
                f.write(f"   - 전체 상태: {diagnostic_report['overall_status']}\n")
                f.write(f"   - 총 단계: {diagnostic_report['summary']['total_steps']}\n")
                f.write(f"   - 완료 단계: {diagnostic_report['summary']['completed_steps']}\n")
                f.write(f"   - 실패 단계: {diagnostic_report['summary']['failed_steps']}\n")
                f.write(f"   - 성공률: {diagnostic_report['summary']['success_rate']:.1f}%\n\n")
                
                # 단계별 상세 정보
                f.write("📋 단계별 진단 결과:\n")
                for step in diagnostic_report['steps']:
                    f.write(f"\n단계 {step['step_number']}: {step['step_name']}\n")
                    f.write(f"   상태: {step['status']}\n")
                    f.write(f"   메시지: {step['message']}\n")
                    if step['duration']:
                        f.write(f"   소요 시간: {step['duration']:.2f}초\n")
                    if step['error_details']:
                        f.write(f"   오류 상세: {step['error_details']}\n")
                
                # 연결 상태 정보
                f.write("\n" + "=" * 80 + "\n")
                f.write(self.generate_status_report())
                
                # 이벤트 히스토리
                f.write("\n\n📝 전체 이벤트 히스토리:\n")
                for event in self.connection_events:
                    f.write(f"[{event.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] ")
                    f.write(f"{event.status.value}: {event.message}")
                    if event.error_code:
                        f.write(f" (오류코드: {event.error_code})")
                    if event.details:
                        f.write(f" - {event.details}")
                    f.write("\n")
            
            self.logger.info(f"✅ 진단 로그 내보내기 완료: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 진단 로그 내보내기 실패: {e}")
            return False


# 전역 연결 모니터 인스턴스
_connection_monitor = None

def get_connection_monitor():
    """연결 모니터 싱글톤 인스턴스 반환"""
    global _connection_monitor
    if _connection_monitor is None:
        _connection_monitor = ConnectionMonitor()
    return _connection_monitor

if __name__ == "__main__":
    # 테스트 코드
    import logging
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🧪 연결 모니터 테스트 시작...")
    print("=" * 50)
    
    # 연결 모니터 생성
    monitor = get_connection_monitor()
    
    # 상태 변경 콜백 테스트
    def status_callback(old_status, new_status, message):
        print(f"🔄 상태 변경: {old_status.value} → {new_status.value} ({message})")
    
    monitor.add_status_change_callback(status_callback)
    
    # 모니터링 시작
    monitor.start_monitoring()
    
    # 진단 시뮬레이션
    print("\n🔍 진단 시뮬레이션:")
    monitor.start_diagnostic()
    
    # 단계별 진단 시뮬레이션
    steps = [
        (1, "running", "환경 확인 중..."),
        (1, "success", "환경 확인 완료"),
        (2, "running", "COM 객체 생성 중..."),
        (2, "success", "COM 객체 생성 완료"),
        (3, "running", "로그인 시도 중..."),
        (3, "failed", "로그인 실패", "사용자 정보 오류"),
    ]
    
    for step_num, status, message, *error in steps:
        error_details = error[0] if error else None
        monitor.update_diagnostic_step(step_num, status, message, error_details)
        time.sleep(0.5)  # 시뮬레이션용 딜레이
    
    # 연결 상태 변경 시뮬레이션
    print("\n📡 연결 상태 시뮬레이션:")
    
    monitor.set_status(ConnectionStatus.CONNECTING, "키움 서버 연결 시도")
    time.sleep(1)
    
    monitor.set_status(ConnectionStatus.ERROR, "로그인 실패", error_code=-100)
    time.sleep(1)
    
    monitor.set_status(ConnectionStatus.RECONNECTING, "재연결 시도 중")
    time.sleep(1)
    
    monitor.set_status(ConnectionStatus.CONNECTED, "연결 성공")
    time.sleep(2)
    
    # 데이터 요청 시뮬레이션
    for i in range(5):
        monitor.record_data_request(successful=True)
    monitor.record_data_request(successful=False)
    
    # 리포트 생성
    print("\n📊 연결 정보:")
    info = monitor.get_connection_info()
    print(f"   현재 상태: {info['current_status']}")
    print(f"   연결 시도: {info['connection_attempts']}회")
    print(f"   성공률: {info['success_rate']:.1f}%")
    
    print("\n📋 진단 리포트:")
    diagnostic_report = monitor.get_diagnostic_report()
    print(f"   전체 상태: {diagnostic_report['overall_status']}")
    print(f"   성공률: {diagnostic_report['summary']['success_rate']:.1f}%")
    
    print("\n📝 상태 리포트:")
    print(monitor.generate_status_report())
    
    # 모니터링 중지
    monitor.stop_monitoring()
    
    print("\n" + "=" * 50)
    print("🎉 연결 모니터 테스트 완료!")


class ConnectionStatus(Enum):
    """연결 상태 열거형"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RECONNECTING = "reconnecting"

@dataclass
class ConnectionEvent:
    """연결 이벤트 정보"""
    timestamp: datetime
    status: ConnectionStatus
    message: str
    error_code: Optional[int] = None
    details: Optional[str] = None

@dataclass
class DiagnosticStep:
    """진단 단계 정보"""
    step_name: str
    step_number: int
    status: str  # "pending", "running", "success", "failed", "skipped"
    message: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_details: Optional[str] = None

class ConnectionMonitor:
    """키움 API 연결 상태 모니터링 클래스"""
    
    def __init__(self):
        """연결 모니터 초기화"""
        self.config = get_config()
        self.logger = logging.getLogger(__name__)
        
        # 연결 상태 관리
        self.current_status = ConnectionStatus.DISCONNECTED
        self.last_connection_time: Optional[datetime] = None
        self.total_connection_time = timedelta(0)
        self.connection_attempts = 0
        self.successful_connections = 0
        
        # 이벤트 히스토리
        self.connection_events: List[ConnectionEvent] = []
        self.max_events = 1000  # 최대 이벤트 저장 개수
        
        # 진단 정보
        self.diagnostic_steps: List[DiagnosticStep] = []
        self.current_diagnostic_step = 0
        
        # 모니터링 스레드
        self.monitoring_thread: Optional[threading.Thread] = None
        self.monitoring_active = False
        self.monitor_interval = 5  # 5초 간격 모니터링
        
        # 통계 정보
        self.stats = {
            'heartbeat_count': 0,
            'error_count': 0,
            'reconnect_count': 0,
            'data_requests': 0,
            'successful_requests': 0
        }
        
        # 콜백 함수들
        self.status_change_callbacks: List[Callable] = []
        
        # 진단 단계 정의
        self._init_diagnostic_steps()
    
    def _init_diagnostic_steps(self):
        """진단 단계 초기화"""
        self.diagnostic_steps = [
            DiagnosticStep(
                step_name="환경 확인",
                step_number=1,
                status="pending",
                message="Python 32bit, PyQt5, 키움 OpenAPI+ 확인"
            ),
            DiagnosticStep(
                step_name="COM 객체 생성",
                step_number=2,
                status="pending",
                message="CLSID 등록, 객체 생성, 이벤트 연결"
            ),
            DiagnosticStep(
                step_name="로그인 시도",
                step_number=3,
                status="pending",
                message="로그인 요청, 서버 응답, 인증 완료"
            ),
            DiagnosticStep(
                step_name="계좌 정보 조회",
                step_number=4,
                status="pending",
                message="계좌 번호 조회, 사용자 정보 확인"
            ),
            DiagnosticStep(
                step_name="시장 데이터 준비",
                step_number=5,
                status="pending",
                message="시세 서버 연결, TR 요청 준비"
            )
        ]
    
    def start_monitoring(self):
        """모니터링 시작"""
        if self.monitoring_active:
            self.logger.warning("⚠️ 모니터링이 이미 실행 중입니다.")
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitoring_thread.start()
        
        self.logger.info("🔍 연결 상태 모니터링 시작")
    
    def stop_monitoring(self):
        """모니터링 중지"""
        self.monitoring_active = False
        
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=2)
        
        self.logger.info("⏹️ 연결 상태 모니터링 중지")
    
    def _monitoring_loop(self):
        """모니터링 루프"""
        while self.monitoring_active:
            try:
                # 주기적 상태 확인
                self._check_connection_health()
                
                # 하트비트 카운트 증가
                self.stats['heartbeat_count'] += 1
                
                # 대기
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                self.logger.error(f"❌ 모니터링 루프 오류: {e}")
                time.sleep(self.monitor_interval)
    
    def _check_connection_health(self):
        """연결 상태 건강성 확인"""
        try:
            # 현재 상태에 따른 처리
            if self.current_status == ConnectionStatus.CONNECTED:
                # 연결 시간 업데이트
                if self.last_connection_time:
                    current_session = datetime.now() - self.last_connection_time
                    # 총 연결 시간은 별도로 추적 (연결이 끊어지면 누적)
            
            elif self.current_status == ConnectionStatus.ERROR:
                # 에러 상태가 일정 시간 지속되면 자동 재연결 시도
                self._consider_auto_reconnect()
            
        except Exception as e:
            self.logger.error(f"❌ 연결 건강성 확인 실패: {e}")
    
    def _consider_auto_reconnect(self):
        """자동 재연결 고려"""
        # 현재 MVP에서는 자동 재연결 미구현
        # Phase 2에서 추가 예정
        pass
    
    def set_status(self, status: ConnectionStatus, message: str = "", 
                   error_code: Optional[int] = None, details: Optional[str] = None):
        """연결 상태 설정"""
        old_status = self.current_status
        self.current_status = status
        
        # 이벤트 기록
        event = ConnectionEvent(
            timestamp=datetime.now(),
            status=status,
            message=message,
            error_code=error_code,
            details=details
        )
        
        self._add_event(event)
        
        # 상태별 특별 처리
        if status == ConnectionStatus.CONNECTED:
            if old_status != ConnectionStatus.CONNECTED:
                self.last_connection_time = datetime.now()
                self.successful_connections += 1
                self.logger.info(f"✅ 연결 성공: {message}")
        
        elif status == ConnectionStatus.ERROR:
            self.stats['error_count'] += 1
            self.logger.error(f"❌ 연결 오류: {message}")
        
        elif status == ConnectionStatus.CONNECTING:
            self.connection_attempts += 1
            self.logger.info(f"🔄 연결 시도: {message}")
        
        elif status == ConnectionStatus.RECONNECTING:
            self.stats['reconnect_count'] += 1
            self.logger.info(f"🔄 재연결 시도: {message}")
        
        # 콜백 호출
        self._notify_status_change(old_status, status, message)
    
    def _add_event(self, event: ConnectionEvent):
        """이벤트 추가"""
        self.connection_events.append(event)
        
        # 최대 개수 초과시 오래된 이벤트 제거
        if len(self.connection_events) > self.max_events:
            self.connection_events = self.connection_events[-self.max_events:]
    
    def _notify_status_change(self, old_status: ConnectionStatus, 
                            new_status: ConnectionStatus, message: str):
        """상태 변경 콜백 호출"""
        for callback in self.status_change_callbacks:
            try:
                callback(old_status, new_status, message)
            except Exception as e:
                self.logger.error(f"❌ 상태 변경 콜백 오류: {e}")
    
    def add_status_change_callback(self, callback: Callable):
        """상태 변경 콜백 추가"""
        if callback not in self.status_change_callbacks:
            self.status_change_callbacks.append(callback)
    
    def remove_status_change_callback(self, callback: Callable):
        """상태 변경 콜백 제거"""
        if callback in self.status_change_callbacks:
            self.status_change_callbacks.remove(callback)
    
    def start_diagnostic(self, steps_to_run: Optional[List[int]] = None):
        """진단 시작"""
        if steps_to_run is None:
            steps_to_run = [1, 2, 3, 4, 5]  # 모든 단계
        
        self.logger.info("🔍 연결 진단 시작")
        
        # 모든 단계를 pending으로 초기화
        for step in self.diagnostic_steps:
            if step.step_number in steps_to_run:
                step.status = "pending"
                step.start_time = None
                step.end_time = None
                step.error_details = None
            else:
                step.status = "skipped"
        
        self.current_diagnostic_step = 0
    
    def update_diagnostic_step(self, step_number: int, status: str, 
                              message: str = "", error_details: str = None):
        """진단 단계 업데이트"""
        for step in self.diagnostic_steps:
            if step.step_number == step_number:
                old_status = step.status
                step.status = status
                step.message = message or step.message
                step.error_details = error_details
                
                if status == "running" and old_status == "pending":
                    step.start_time = datetime.now()
                elif status in ["success", "failed"] and step.start_time:
                    step.end_time = datetime.now()
                
                self.logger.debug(f"📊 진단 단계 {step_number}: {status} - {message}")
                break
    
    def get_diagnostic_report(self) -> Dict:
        """진단 리포트 생성"""
        report = {
            'start_time': None,
            'end_time': None,
            'total_duration': None,
            'overall_status': 'pending',
            'steps': [],
            'summary': {
                'total_steps': len(self.diagnostic_steps),
                'completed_steps': 0,
                'failed_steps': 0,
                'success_rate': 0
            }
        }
        
        completed_steps = []
        failed_steps = []
        
        for step in self.diagnostic_steps:
            step_info = {
                'step_number': step.step_number,
                'step_name': step.step_name,
                'status': step.status,
                'message': step.message,
                'start_time': step.start_time,
                'end_time': step.end_time,
                'duration': None,
                'error_details': step.error_details
            }
            
            if step.start_time and step.end_time:
                step_info['duration'] = (step.end_time - step.start_time).total_seconds()
            
            report['steps'].append(step_info)
            
            if step.status == "success":
                completed_steps.append(step)
            elif step.status == "failed":
                failed_steps.append(step)
        
        # 전체 시간 계산
        if self.diagnostic_steps:
            start_times = [s.start_time for s in self.diagnostic_steps if s.start_time]
            end_times = [s.end_time for s in self.diagnostic_steps if s.end_time]
            
            if start_times:
                report['start_time'] = min(start_times)
            if end_times:
                report['end_time'] = max(end_times)
            
            if report['start_time'] and report['end_time']:
                report['total_duration'] = (report['end_time'] - report['start_time']).total_seconds()
        
        # 요약 정보
        report['summary']['completed_steps'] = len(completed_steps)
        report['summary']['failed_steps'] = len(failed_steps)
        
        total_attempted = len([s for s in self.diagnostic_steps if s.status != "skipped"])
        if total_attempted > 0:
            report['summary']['success_rate'] = (len(completed_steps) / total_attempted) * 100
        
        # 전체 상태 결정
        if failed_steps:
            report['overall_status'] = 'failed'
        elif len(completed_steps) == total_attempted and total_attempted > 0:
            report['overall_status'] = 'success'
        elif any(s.status == "running" for s in self.diagnostic_steps):
            report['overall_status'] = 'running'
        else:
            report['overall_status'] = 'pending'
        
        return report
    
    def get_connection_info(self) -> Dict:
        """연결 정보 조회"""
        info = {
            'current_status': self.current_status.value,
            'status_message': self._get_status_message(),
            'connection_attempts': self.connection_attempts,
            'successful_connections': self.successful_connections,
            'last_connection_time': self.last_connection_time,
            'total_connection_time': self._calculate_total_connection_time(),
            'current_session_time': self._calculate_current_session_time(),
            'success_rate': self._calculate_success_rate(),
            'stats': self.stats.copy()
        }
        
        return info
    
    def _get_status_message(self) -> str:
        """현재 상태 메시지"""
        status_messages = {
            ConnectionStatus.DISCONNECTED: "연결 해제됨",
            ConnectionStatus.CONNECTING: "연결 시도 중",
            ConnectionStatus.CONNECTED: "정상 연결됨",
            ConnectionStatus.ERROR: "연결 오류 발생",
            ConnectionStatus.RECONNECTING: "재연결 시도 중"
        }
        return status_messages.get(self.current_status, "알 수 없는 상태")
    
    def _calculate_total_connection_time(self) -> timedelta:
        """총 연결 시간 계산"""
        total_time = self.total_connection_time
        
        # 현재 연결 중이면 현재 세션 시간 추가
        if (self.current_status == ConnectionStatus.CONNECTED and 
            self.last_connection_time):
            current_session = datetime.now() - self.last_connection_time
            total_time += current_session
        
        return total_time
    
    def _calculate_current_session_time(self) -> Optional[timedelta]:
        """현재 세션 연결 시간 계산"""
        if (self.current_status == ConnectionStatus.CONNECTED and 
            self.last_connection_time):
            return datetime.now() - self.last_connection_time
        return None
    
    def _calculate_success_rate(self) -> float:
        """연결 성공률 계산"""
        if self.connection_attempts == 0:
            return 0.0
        return (self.successful_connections / self.connection_attempts) * 100
    
    def get_recent_events(self, count: int = 10) -> List[ConnectionEvent]:
        """최근 이벤트 조회"""
        return self.connection_events[-count:] if self.connection_events else []
    
    def get_events_by_status(self, status: ConnectionStatus, 
                           since: Optional[datetime] = None) -> List[ConnectionEvent]:
        """상태별 이벤트 조회"""
        filtered_events = [e for e in self.connection_events if e.status == status]
        
        if since:
            filtered_events = [e for e in filtered_events if e.timestamp >= since]
        
        return filtered_events
    
    def record_data_request(self, successful: bool = True):
        """데이터 요청 기록"""
        self.stats['data_requests'] += 1
        if successful:
            self.stats['successful_requests'] += 1
    
    def clear_events(self):
        """이벤트 히스토리 클리어"""
        self.connection_events.clear()
        self.logger.info("🧹 연결 이벤트 히스토리 클리어")
    
    def reset_stats(self):
        """통계 초기화"""
        self.stats = {
            'heartbeat_count': 0,
            'error_count': 0,
            'reconnect_count': 0,
            'data_requests': 0,
            'successful_requests': 0
        }
        self.connection_attempts = 0
        self.successful_connections = 0
        self.total_connection_time = timedelta(0)
        self.logger.info("🧹 연결 통계 초기화")
    
    def generate_status_report(self) -> str:
        """상태 리포트 생성 (텍스트 형태)"""
        info = self.get_connection_info()
        report_lines = []
        
        report_lines.append("=" * 50)
        report_lines.append("📊 키움 API 연결 상태 리포트")
        report_lines.append("=" * 50)
        
        # 현재 상태
        status_emoji = {
            'connected': '✅',
            'connecting': '🔄',
            'disconnected': '❌',
            'error': '❌',
            'reconnecting': '🔄'
        }
        
        emoji = status_emoji.get(info['current_status'], '❓')
        report_lines.append(f"{emoji} 현재 상태: {info['status_message']}")
        
        # 연결 통계
        report_lines.append(f"📈 연결 시도: {info['connection_attempts']}회")
        report_lines.append(f"✅ 성공 연결: {info['successful_connections']}회")
        report_lines.append(f"📊 성공률: {info['success_rate']:.1f}%")
        
        # 시간 정보
        if info['last_connection_time']:
            report_lines.append(f"🕐 마지막 연결: {info['last_connection_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        if info['current_session_time']:
            session_time = str(info['current_session_time']).split('.')[0]  # 초 단위까지만
            report_lines.append(f"⏱️  현재 세션: {session_time}")
        
        total_time = str(info['total_connection_time']).split('.')[0]
        report_lines.append(f"⏳ 총 연결 시간: {total_time}")
        
        # 활동 통계
        report_lines.append("\n📊 활동 통계:")
        stats = info['stats']
        report_lines.append(f"   - 하트비트: {stats['heartbeat_count']}회")
        report_lines.append(f"   - 데이터 요청: {stats['data_requests']}회")
        report_lines.append(f"   - 성공 요청: {stats['successful_requests']}회")
        report_lines.append(f"   - 오류 발생: {stats['error_count']}회")
        report_lines.append(f"   - 재연결 시도: {stats['reconnect_count']}회")
        
        # 최근 이벤트
        recent_events = self.get_recent_events(5)
        if recent_events:
            report_lines.append("\n📝 최근 이벤트:")
            for event in reversed(recent_events):  # 최신순
                time_str = event.timestamp.strftime('%H:%M:%S')
                status_emoji = {
                    ConnectionStatus.CONNECTED: '✅',
                    ConnectionStatus.CONNECTING: '🔄',
                    ConnectionStatus.DISCONNECTED: '❌',
                    ConnectionStatus.ERROR: '❌',
                    ConnectionStatus.RECONNECTING: '🔄'
                }
                emoji = status_emoji.get(event.status, '❓')
                report_lines.append(f"   [{time_str}] {emoji} {event.message}")
        
        report_lines.append("=" * 50)
        
        return "\n".join(report_lines)
    
    def export_diagnostic_log(self, filepath: str) -> bool:
        """진단 로그 내보내기"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # 리포트 헤더
                f.write(f"키움 API 연결 진단 로그\n")
                f.write(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n\n")
                
                # 진단 리포트
                diagnostic_report = self.get_diagnostic_report()
                f.write("📊 진단 요약:\n")
                f.write(f"   - 전체 상태: {diagnostic_report['overall_status']}\n")
                f.write(f"   - 총 단계: {diagnostic_report['summary']['total_steps']}\n")
                f.write(f"   - 완료 단계: {diagnostic_report['summary']['completed_steps']}\n")
                f.write(f"   - 실패 단계: {diagnostic_report['summary']['failed_steps']}\n")
                f.write(f"   - 성공률: {diagnostic_report['summary']['success_rate']:.1f}%\n\n")
                
                # 단계별 상세 정보
                f.write("📋 단계별 진단 결과:\n")
                for step in diagnostic_report['steps']:
                    f.write(f"\n단계 {step['step_number']}: {step['step_name']}\n")
                    f.write(f"   상태: {step['status']}\n")
                    f.write(f"   메시지: {step['message']}\n")
                    if step['duration']:
                        f.write(f"   소요 시간: {step['duration']:.2f}초\n")
                    if step['error_details']:
                        f.write(f"   오류 상세: {step['error_details']}\n")
                
                # 연결 상태 정보
                f.write("\n" + "=" * 80 + "\n")
                f.write(self.generate_status_report())
                
                # 이벤트 히스토리
                f.write("\n\n📝 전체 이벤트 히스토리:\n")
                for event in self.connection_events:
                    f.write(f"[{event.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] ")
                    f.write(f"{event.status.value}: {event.message}")
                    if event.error_code:
                        f.write(f" (오류코드: {event.error_code})")
                    if event.details:
                        f.write(f" - {event.details}")
                    f.write("\n")
            
            self.logger.info(f"✅ 진단 로그 내보내기 완료: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 진단 로그 내보내기 실패: {e}")
            return False

# 전역 연결 모니터 인스턴스
_connection_monitor = None

def get_connection_monitor() -> ConnectionMonitor:
    """연결 모니터 싱글톤 인스턴스 반환"""
    global _connection_monitor
    if _connection_monitor is None:
        _connection_monitor = ConnectionMonitor()
    return _connection_monitor

if __name__ == "__main__":
    # 테스트 코드
    import logging
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🧪 연결 모니터 테스트 시작...")
    print("=" * 50)
    
    # 연결 모니터 생성
    monitor = get_connection_monitor()
    
    # 상태 변경 콜백 테스트
    def status_callback(old_status, new_status, message):
        print(f"🔄 상태 변경: {old_status.value} → {new_status.value} ({message})")
    
    monitor.add_status_change_callback(status_callback)
    
    # 모니터링 시작
    monitor.start_monitoring()
    
    # 진단 시뮬레이션
    print("\n🔍 진단 시뮬레이션:")
    monitor.start_diagnostic()
    
    # 단계별 진단 시뮬레이션
    steps = [
        (1, "running", "환경 확인 중..."),
        (1, "success", "환경 확인 완료"),
        (2, "running", "COM 객체 생성 중..."),
        (2, "success", "COM 객체 생성 완료"),
        (3, "running", "로그인 시도 중..."),
        (3, "failed", "로그인 실패", "사용자 정보 오류"),
    ]
    
    for step_num, status, message, *error in steps:
        error_details = error[0] if error else None
        monitor.update_diagnostic_step(step_num, status, message, error_details)
        time.sleep(0.5)  # 시뮬레이션용 딜레이
    
    # 연결 상태 변경 시뮬레이션
    print("\n📡 연결 상태 시뮬레이션:")
    
    monitor.set_status(ConnectionStatus.CONNECTING, "키움 서버 연결 시도")
    time.sleep(1)
    
    monitor.set_status(ConnectionStatus.ERROR, "로그인 실패", error_code=-100)
    time.sleep(1)
    
    monitor.set_status(ConnectionStatus.RECONNECTING, "재연결 시도 중")
    time.sleep(1)
    
    monitor.set_status(ConnectionStatus.CONNECTED, "연결 성공")
    time.sleep(2)
    
    # 데이터 요청 시뮬레이션
    for i in range(5):
        monitor.record_data_request(successful=True)
    monitor.record_data_request(successful=False)
    
    # 리포트 생성
    print("\n📊 연결 정보:")
    info = monitor.get_connection_info()
    print(f"   현재 상태: {info['current_status']}")
    print(f"   연결 시도: {info['connection_attempts']}회")
    print(f"   성공률: {info['success_rate']:.1f}%")
    
    print("\n📋 진단 리포트:")
    diagnostic_report = monitor.get_diagnostic_report()
    print(f"   전체 상태: {diagnostic_report['overall_status']}")
    print(f"   성공률: {diagnostic_report['summary']['success_rate']:.1f}%")
    
    print("\n📝 상태 리포트:")
    print(monitor.generate_status_report())
    
    # 모니터링 중지
    monitor.stop_monitoring()
    
    print("\n" + "=" * 50)
    print("🎉 연결 모니터 테스트 완료!")