# services/__init__.py - 서비스 패키지 초기화
"""
KIS API 서비스 패키지

이 패키지는 한국투자증권 OpenAPI와의 통신을 담당하는 서비스들을 포함합니다.
- kis_auth: API 인증 관리
- kis_websocket: 실시간 WebSocket 연결
- kis_api: REST API 클라이언트
- data_processor: 실시간 데이터 처리
- trading_strategy: 거래 전략 실행
"""

__version__ = "1.0.0"
__author__ = "KIS Quant Team"

# 패키지 레벨에서 주요 클래스들을 임포트하지 않음 (순환 임포트 방지)
# 대신 각 모듈에서 직접 임포트하여 사용 
