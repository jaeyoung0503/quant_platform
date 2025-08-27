# file: backend/utils/logger.py

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
import json
import traceback

class ColoredFormatter(logging.Formatter):
    """컬러 로그 포매터"""
    
    # 색상 코드
    COLORS = {
        'DEBUG': '\033[36m',     # 청록
        'INFO': '\033[32m',      # 녹색
        'WARNING': '\033[33m',   # 노란색
        'ERROR': '\033[31m',     # 빨간색
        'CRITICAL': '\033[35m',  # 자홍색
        'RESET': '\033[0m'       # 리셋
    }
    
    def format(self, record):
        # 기본 포맷팅
        log_message = super().format(record)
        
        # 색상 적용
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        return f"{color}{log_message}{reset}"

class JSONFormatter(logging.Formatter):
    """JSON 로그 포매터"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'process_id': record.process,
            'thread_id': record.thread
        }
        
        # 예외 정보 추가
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # 추가 컨텍스트 정보
        if hasattr(record, 'extra_data'):
            log_data['extra'] = record.extra_data
        
        return json.dumps(log_data, ensure_ascii=False)

class TradingLogFilter(logging.Filter):
    """트레이딩 관련 로그 필터"""
    
    def __init__(self, include_trading_only=False):
        super().__init__()
        self.include_trading_only = include_trading_only
        
        # 트레이딩 관련 모듈 목록
        self.trading_modules = [
            'trading.engine',
            'trading.strategies', 
            'trading.risk_manager',
            'data.kiwoom_mock',
            'api'
        ]
    
    def filter(self, record):
        is_trading_log = any(
            module in record.name 
            for module in self.trading_modules
        )
        
        if self.include_trading_only:
            return is_trading_log
        else:
            return True  # 모든 로그 허용

class DatabaseLogHandler(logging.Handler):
    """데이터베이스 로그 핸들러"""
    
    def __init__(self, db_session_factory=None):
        super().__init__()
        self.db_session_factory = db_session_factory
    
    def emit(self, record):
        try:
            if not self.db_session_factory:
                return
            
            # 로그 레코드를 데이터베이스에 저장
            # 실제 구현에서는 LogEntry 모델 사용
            log_entry = {
                'timestamp': datetime.utcnow(),
                'level': record.levelname,
                'logger_name': record.name,
                'message': record.getMessage(),
                'module': record.module,
                'function_name': record.funcName,
                'line_number': record.lineno,
                'exception_info': self.format(record) if record.exc_info else None
            }
            
            # 실제 DB 저장 로직은 여기에 구현
            # with self.db_session_factory() as session:
            #     session.add(LogEntry(**log_entry))
            #     session.commit()
            
        except Exception as e:
            # 로깅 오류는 무시 (무한 루프 방지)
            print(f"Database logging error: {e}", file=sys.stderr)

def setup_logger(
    name: Optional[str] = None,
    level: str = "INFO",
    log_file: Optional[str] = None,
    max_size: int = 10485760,  # 10MB
    backup_count: int = 5,
    use_colors: bool = True,
    json_format: bool = False,
    include_trading_only: bool = False
) -> logging.Logger:
    """로거 설정"""
    
    logger = logging.getLogger(name)
    
    # 기존 핸들러 제거 (중복 방지)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 로그 레벨 설정
    logger.setLevel(getattr(logging, level.upper()))
    
    # 포매터 선택
    if json_format:
        formatter = JSONFormatter()
    elif use_colors and sys.stderr.isatty():
        formatter = ColoredFormatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # 트레이딩 로그 필터 적용
    if include_trading_only:
        trading_filter = TradingLogFilter(include_trading_only=True)
        console_handler.addFilter(trading_filter)
    
    logger.addHandler(console_handler)
    
    # 파일 핸들러 (선택적)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 로테이팅 파일 핸들러
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=max_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        
        # 파일은 항상 JSON 포맷 사용
        file_formatter = JSONFormatter() if json_format else logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        logger.addHandler(file_handler)
    
    return logger

class LoggerManager:
    """로거 관리자"""
    
    def __init__(self):
        self.loggers = {}
        self.handlers = {}
        
        # 기본 로그 디렉토리 생성
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
    
    def get_logger(
        self, 
        name: str, 
        level: str = "INFO",
        log_file: Optional[str] = None,
        **kwargs
    ) -> logging.Logger:
        """로거 생성 또는 반환"""
        
        if name not in self.loggers:
            if log_file:
                log_file = self.log_dir / log_file
            
            logger = setup_logger(
                name=name,
                level=level,
                log_file=str(log_file) if log_file else None,
                **kwargs
            )
            
            self.loggers[name] = logger
        
        return self.loggers[name]
    
    def get_trading_logger(self) -> logging.Logger:
        """트레이딩 전용 로거"""
        return self.get_logger(
            name="trading",
            level="INFO",
            log_file="trading.log",
            include_trading_only=True
        )
    
    def get_api_logger(self) -> logging.Logger:
        """API 전용 로거"""
        return self.get_logger(
            name="api",
            level="INFO", 
            log_file="api.log"
        )
    
    def get_error_logger(self) -> logging.Logger:
        """오류 전용 로거"""
        error_logger = self.get_logger(
            name="errors",
            level="ERROR",
            log_file="errors.log",
            json_format=True
        )
        
        # 오류 로거는 ERROR 레벨 이상만 기록
        error_logger.setLevel(logging.ERROR)
        
        return error_logger
    
    def setup_application_logging(self, config=None):
        """애플리케이션 전체 로깅 설정"""
        from utils.config import get_settings
        
        settings = get_settings() if not config else config
        
        # 루트 로거 설정
        root_logger = setup_logger(
            name=None,
            level=settings.log_level,
            log_file=settings.log_file,
            max_size=settings.log_max_size,
            backup_count=settings.log_backup_count,
            use_colors=settings.debug,
            json_format=not settings.debug
        )
        
        # 모듈별 로거 설정
        module_loggers = [
            ("trading.engine", "INFO", "trading_engine.log"),
            ("trading.strategies", "INFO", "strategies.log"),
            ("trading.risk_manager", "WARNING", "risk.log"),
            ("data.kiwoom_mock", "INFO", "kiwoom.log"),
            ("database", "WARNING", "database.log"),
            ("api", "INFO", "api.log")
        ]
        
        for module_name, level, log_file in module_loggers:
            self.get_logger(
                name=module_name,
                level=level,
                log_file=log_file
            )
        
        # 외부 라이브러리 로깅 레벨 조정
        logging.getLogger("uvicorn").setLevel(logging.WARNING)
        logging.getLogger("fastapi").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        
        return root_logger
    
    def add_performance_logging(self):
        """성능 로깅 추가"""
        perf_logger = self.get_logger(
            name="performance",
            level="INFO",
            log_file="performance.log",
            json_format=True
        )
        
        return perf_logger
    
    def add_audit_logging(self):
        """감사 로깅 추가 (중요한 거래 활동 기록)"""
        audit_logger = self.get_logger(
            name="audit",
            level="INFO",
            log_file="audit.log",
            json_format=True
        )
        
        # 감사 로그는 별도 포매터 사용
        audit_formatter = logging.Formatter(
            fmt='%(asctime)s [AUDIT] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        for handler in audit_logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.setFormatter(audit_formatter)
        
        return audit_logger

class AuditLogger:
    """감사 로깅 전용 클래스"""
    
    def __init__(self, logger_manager: LoggerManager):
        self.audit_logger = logger_manager.add_audit_logging()
    
    def log_order(self, order_data: dict):
        """주문 로깅"""
        self.audit_logger.info(
            f"ORDER - {order_data.get('action', 'UNKNOWN')} "
            f"{order_data.get('stock_code', 'N/A')} "
            f"{order_data.get('quantity', 0)} shares "
            f"@ {order_data.get('price', 0)} "
            f"({order_data.get('strategy', 'manual')})"
        )
    
    def log_trade(self, trade_data: dict):
        """거래 체결 로깅"""
        self.audit_logger.info(
            f"TRADE - {trade_data.get('action', 'UNKNOWN')} "
            f"{trade_data.get('stock_code', 'N/A')} "
            f"{trade_data.get('quantity', 0)} shares "
            f"@ {trade_data.get('price', 0)} "
            f"PnL: {trade_data.get('pnl', 0)}"
        )
    
    def log_risk_event(self, event_type: str, details: dict):
        """리스크 이벤트 로깅"""
        self.audit_logger.warning(
            f"RISK_EVENT - {event_type}: {details}"
        )
    
    def log_system_event(self, event_type: str, details: dict):
        """시스템 이벤트 로깅"""
        self.audit_logger.info(
            f"SYSTEM - {event_type}: {details}"
        )

class PerformanceLogger:
    """성능 로깅 전용 클래스"""
    
    def __init__(self, logger_manager: LoggerManager):
        self.perf_logger = logger_manager.add_performance_logging()
    
    def log_execution_time(self, function_name: str, execution_time: float, **kwargs):
        """함수 실행 시간 로깅"""
        self.perf_logger.info(
            f"PERFORMANCE - {function_name}: {execution_time:.4f}s",
            extra={'extra_data': {'execution_time': execution_time, **kwargs}}
        )
    
    def log_memory_usage(self, context: str, memory_mb: float):
        """메모리 사용량 로깅"""
        self.perf_logger.info(
            f"MEMORY - {context}: {memory_mb:.2f}MB",
            extra={'extra_data': {'memory_mb': memory_mb}}
        )
    
    def log_api_response_time(self, endpoint: str, response_time: float, status_code: int):
        """API 응답 시간 로깅"""
        self.perf_logger.info(
            f"API - {endpoint}: {response_time:.4f}s (status: {status_code})",
            extra={'extra_data': {
                'endpoint': endpoint,
                'response_time': response_time,
                'status_code': status_code
            }}
        )

def performance_monitor(func):
    """성능 모니터링 데코레이터"""
    import time
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # 성능 로그 기록
            perf_logger = logging.getLogger("performance")
            perf_logger.info(
                f"Function {func.__name__} executed in {execution_time:.4f}s"
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # 오류와 함께 성능 정보 기록
            error_logger = logging.getLogger("errors")
            error_logger.error(
                f"Function {func.__name__} failed after {execution_time:.4f}s: {e}",
                exc_info=True
            )
            
            raise
    
    return wrapper

# 전역 로거 매니저
_logger_manager = None

def get_logger_manager() -> LoggerManager:
    """로거 매니저 싱글톤"""
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = LoggerManager()
    return _logger_manager

def get_logger(name: str = None) -> logging.Logger:
    """편의 함수: 로거 반환"""
    if name:
        return logging.getLogger(name)
    else:
        return logging.getLogger()

# 애플리케이션 시작 시 호출
def initialize_logging():
    """로깅 시스템 초기화"""
    logger_manager = get_logger_manager()
    return logger_manager.setup_application_logging() 
