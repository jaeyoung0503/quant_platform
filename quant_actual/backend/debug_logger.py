#file: quant_actual/backend/debug_logger.py

import logging
import sys
from pathlib import Path

def setup_debug_logging():
    """디버깅용 로깅 설정"""
    
    # 로그 디렉토리 생성
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # 기존 핸들러 제거
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 포매터 설정
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 콘솔 핸들러 (DEBUG 레벨)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 파일 핸들러 (INFO 레벨)
    file_handler = logging.FileHandler(log_dir / "debug.log", encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # 중요한 모듈들의 로그 레벨 설정
    logging.getLogger("trading.engine").setLevel(logging.DEBUG)
    logging.getLogger("database").setLevel(logging.DEBUG)
    logging.getLogger("trading.strategies").setLevel(logging.DEBUG)
    logging.getLogger("data.kiwoom_mock").setLevel(logging.DEBUG)
    
    # 외부 라이브러리 로그 레벨 조정
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    
    print("디버깅 로깅 설정 완료 - DEBUG 레벨 활성화")
    return root_logger

if __name__ == "__main__":
    setup_debug_logging()