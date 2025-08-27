"""
file: trading_mode_api.py
거래 모드 전환 API
Mock ↔ Real 모드 전환을 위한 엔드포인트
"""

import os
import platform
import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from utils.config import get_settings
from database import get_db_session

logger = logging.getLogger(__name__)

# 전역 변수로 현재 모드 저장
CURRENT_TRADING_MODE = "DEMO"  # DEMO or REAL
KIWOOM_CLIENT_INSTANCE = None

class TradingModeRequest(BaseModel):
    mode: str  # "DEMO" or "REAL"

class SystemStatusResponse(BaseModel):
    current_mode: str
    is_windows: bool
    kiwoom_api_available: bool
    account_connected: bool
    account_info: Dict[str, Any] = None

router = APIRouter()

def check_windows_environment() -> bool:
    """Windows 환경 체크"""
    return platform.system() == "Windows"

def check_kiwoom_api_available() -> bool:
    """키움 API 사용 가능성 체크"""
    if not check_windows_environment():
        return False
    
    try:
        # PyQt5와 pythoncom 모듈 체크
        import PyQt5
        import pythoncom
        
        # 키움 API 파일 존재 체크 (일반적인 설치 경로)
        kiwoom_paths = [
            "C:\\OpenAPI\\",
            "C:\\Program Files\\OpenAPI\\",
            "C:\\Program Files (x86)\\OpenAPI\\"
        ]
        
        for path in kiwoom_paths:
            if os.path.exists(path):
                return True
        
        # 레지스트리에서 키움 API 확인 (선택적)
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "KHOPENAPI.KHOpenAPICtrl.1")
            winreg.CloseKey(key)
            return True
        except:
            pass
        
        return False
        
    except ImportError:
        return False

async def get_account_info():
    """계좌 정보 조회"""
    global KIWOOM_CLIENT_INSTANCE
    
    if CURRENT_TRADING_MODE == "REAL" and KIWOOM_CLIENT_INSTANCE:
        try:
            account_info = await KIWOOM_CLIENT_INSTANCE.get_account_info()
            return account_info
        except Exception as e:
            logger.error(f"실거래 계좌 정보 조회 실패: {e}")
            return None
    else:
        # Mock 모드 계좌 정보
        return {
            "account_number": "8012345-01",
            "server_type": "DEMO",
            "available_cash": 50000000,
            "total_cash": 50000000
        }

@router.get("/system/trading-mode", response_model=SystemStatusResponse)
async def get_trading_mode_status():
    """현재 거래 모드 상태 조회"""
    try:
        is_windows = check_windows_environment()
        kiwoom_available = check_kiwoom_api_available()
        
        # 계좌 연결 상태 체크
        account_connected = False
        account_info = None
        
        if CURRENT_TRADING_MODE == "REAL" and KIWOOM_CLIENT_INSTANCE:
            account_connected = KIWOOM_CLIENT_INSTANCE.is_connected
            if account_connected:
                account_info = await get_account_info()
        elif CURRENT_TRADING_MODE == "DEMO":
            account_connected = True  # Mock 모드에서는 항상 연결됨
            account_info = await get_account_info()
        
        return SystemStatusResponse(
            current_mode=CURRENT_TRADING_MODE,
            is_windows=is_windows,
            kiwoom_api_available=kiwoom_available,
            account_connected=account_connected,
            account_info=account_info
        )
        
    except Exception as e:
        logger.error(f"거래 모드 상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="Failed to get trading mode status")

@router.post("/system/change-trading-mode")
async def change_trading_mode(request: TradingModeRequest):
    """거래 모드 변경"""
    global CURRENT_TRADING_MODE, KIWOOM_CLIENT_INSTANCE
    
    try:
        new_mode = request.mode.upper()
        
        if new_mode not in ["DEMO", "REAL"]:
            raise HTTPException(status_code=400, detail="Invalid trading mode")
        
        if new_mode == CURRENT_TRADING_MODE:
            return {"success": True, "message": f"이미 {new_mode} 모드입니다."}
        
        # 실거래 모드 전환 시 추가 검증
        if new_mode == "REAL":
            if not check_windows_environment():
                raise HTTPException(
                    status_code=400, 
                    detail="실거래 모드는 Windows 환경에서만 사용 가능합니다."
                )
            
            if not check_kiwoom_api_available():
                raise HTTPException(
                    status_code=400, 
                    detail="키움 Open API가 설치되지 않았습니다."
                )
            
            # 환경변수 체크
            if not os.getenv("KIWOOM_ACCOUNT"):
                raise HTTPException(
                    status_code=400, 
                    detail="KIWOOM_ACCOUNT 환경변수가 설정되지 않았습니다."
                )
            
            if not os.getenv("KIWOOM_PASSWORD"):
                raise HTTPException(
                    status_code=400, 
                    detail="KIWOOM_PASSWORD 환경변수가 설정되지 않았습니다."
                )
        
        # 기존 연결 해제
        if KIWOOM_CLIENT_INSTANCE:
            try:
                await KIWOOM_CLIENT_INSTANCE.disconnect()
            except:
                pass
            KIWOOM_CLIENT_INSTANCE = None
        
        # 새로운 모드로 전환
        if new_mode == "REAL":
            # 실거래 클라이언트 초기화
            from data.kiwoom_real import KiwoomRealClient
            KIWOOM_CLIENT_INSTANCE = KiwoomRealClient()
            
            # 연결 시도
            if not await KIWOOM_CLIENT_INSTANCE.initialize():
                raise HTTPException(status_code=500, detail="키움 API 초기화 실패")
            
            if not await KIWOOM_CLIENT_INSTANCE.connect():
                raise HTTPException(status_code=500, detail="키움 API 연결 실패")
            
            logger.warning("실거래 모드로 전환됨")
            
        else:  # DEMO 모드
            # Mock 클라이언트 초기화
            from data.kiwoom_mock import KiwoomClient
            KIWOOM_CLIENT_INSTANCE = KiwoomClient()
            await KIWOOM_CLIENT_INSTANCE.connect()
            
            logger.info("모의투자 모드로 전환됨")
        
        # 모드 변경
        CURRENT_TRADING_MODE = new_mode
        
        # 트레이딩 엔진에 새로운 클라이언트 적용
        from main import get_trading_engine
        trading_engine = get_trading_engine()
        trading_engine.kiwoom_client = KIWOOM_CLIENT_INSTANCE
        
        # 데이터베이스에 모드 변경 기록
        with get_db_session() as db:
            # 실제로는 SystemLog 테이블에 기록
            pass
        
        return {
            "success": True,
            "message": f"{new_mode} 모드로 변경되었습니다.",
            "mode": new_mode,
            "account_connected": KIWOOM_CLIENT_INSTANCE.is_connected if KIWOOM_CLIENT_INSTANCE else False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"거래 모드 변경 실패: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to change trading mode: {str(e)}")

@router.get("/system/environment-check")
async def check_environment():
    """환경 체크 및 설치 가이드"""
    try:
        checks = {
            "operating_system": {
                "name": platform.system(),
                "version": platform.version(),
                "is_windows": check_windows_environment(),
                "status": "✅" if check_windows_environment() else "❌"
            },
            "python_version": {
                "version": platform.python_version(),
                "is_compatible": platform.python_version() >= "3.9",
                "status": "✅" if platform.python_version() >= "3.9" else "❌"
            },
            "required_packages": {},
            "kiwoom_api": {
                "available": check_kiwoom_api_available(),
                "status": "✅" if check_kiwoom_api_available() else "❌"
            },
            "environment_variables": {
                "kiwoom_account": bool(os.getenv("KIWOOM_ACCOUNT")),
                "kiwoom_password": bool(os.getenv("KIWOOM_PASSWORD")),
                "status": "✅" if (os.getenv("KIWOOM_ACCOUNT") and os.getenv("KIWOOM_PASSWORD")) else "❌"
            }
        }
        
        # Python 패키지 체크
        required_packages = ["PyQt5", "pythoncom", "fastapi", "sqlalchemy", "pandas", "numpy"]
        
        for package in required_packages:
            try:
                __import__(package.lower())
                checks["required_packages"][package] = {"installed": True, "status": "✅"}
            except ImportError:
                checks["required_packages"][package] = {"installed": False, "status": "❌"}
        
        # 전체 상태 판정
        overall_status = "READY" if all([
            checks["operating_system"]["is_windows"],
            checks["python_version"]["is_compatible"],
            all(pkg["installed"] for pkg in checks["required_packages"].values()),
            checks["kiwoom_api"]["available"]
        ]) else "NOT_READY"
        
        return {
            "overall_status": overall_status,
            "checks": checks,
            "recommendations": get_installation_recommendations(checks)
        }
        
    except Exception as e:
        logger.error(f"환경 체크 실패: {e}")
        raise HTTPException(status_code=500, detail="Failed to check environment")

def get_installation_recommendations(checks: Dict) -> list[str]:
    """설치 권장사항 생성"""
    recommendations = []
    
    if not checks["operating_system"]["is_windows"]:
        recommendations.append("실거래를 위해서는 Windows 환경이 필요합니다.")
    
    if not checks["python_version"]["is_compatible"]:
        recommendations.append("Python 3.9 이상으로 업그레이드가 필요합니다.")
    
    missing_packages = [
        pkg for pkg, info in checks["required_packages"].items() 
        if not info["installed"]
    ]
    
    if missing_packages:
        recommendations.append(f"다음 패키지 설치 필요: {', '.join(missing_packages)}")
        recommendations.append("pip install " + " ".join(missing_packages))
    
    if not checks["kiwoom_api"]["available"]:
        recommendations.extend([
            "키움 Open API+ 설치가 필요합니다:",
            "1. 키움증권 홈페이지 → 고객지원 → API",
            "2. Open API+ 다운로드 및 설치",
            "3. 시스템 재부팅 후 재시도"
        ])
    
    if not checks["environment_variables"]["kiwoom_account"]:
        recommendations.extend([
            "환경변수 설정이 필요합니다:",
            "KIWOOM_ACCOUNT=실제계좌번호",
            "KIWOOM_PASSWORD=실제비밀번호"
        ])
    
    if not recommendations:
        recommendations.append("모든 요구사항이 충족되었습니다. 실거래 준비 완료!")
    
    return recommendations

@router.post("/system/test-connection")
async def test_connection(request: TradingModeRequest):
    """연결 테스트"""
    try:
        mode = request.mode.upper()
        
        if mode == "DEMO":
            # Mock 연결 테스트
            from data.kiwoom_mock import KiwoomClient
            test_client = KiwoomClient()
            
            if await test_client.connect():
                await test_client.disconnect()
                return {
                    "success": True,
                    "message": "모의투자 연결 테스트 성공",
                    "details": {
                        "mode": "DEMO",
                        "connection_time": "< 1초",
                        "account": "모의계좌"
                    }
                }
            else:
                raise HTTPException(status_code=500, detail="모의투자 연결 실패")
        
        elif mode == "REAL":
            # 실거래 연결 테스트
            if not check_windows_environment():
                raise HTTPException(status_code=400, detail="Windows 환경이 아닙니다")
            
            if not check_kiwoom_api_available():
                raise HTTPException(status_code=400, detail="키움 API가 설치되지 않았습니다")
            
            from data.kiwoom_real import KiwoomRealClient
            test_client = KiwoomRealClient()
            
            if await test_client.initialize():
                if await test_client.connect():
                    account_info = await test_client.get_account_info()
                    await test_client.disconnect()
                    
                    return {
                        "success": True,
                        "message": "실거래 연결 테스트 성공",
                        "details": {
                            "mode": "REAL",
                            "account": account_info.get("account_number", "확인불가"),
                            "server_type": account_info.get("server_type", "REAL"),
                            "available_cash": account_info.get("available_cash", 0)
                        }
                    }
                else:
                    raise HTTPException(status_code=500, detail="키움 API 로그인 실패")
            else:
                raise HTTPException(status_code=500, detail="키움 API 초기화 실패")
        
        else:
            raise HTTPException(status_code=400, detail="잘못된 모드입니다")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"연결 테스트 실패: {e}")
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")

@router.get("/system/trading-mode-guide")
async def get_trading_mode_guide():
    """거래 모드 가이드"""
    return {
        "modes": {
            "DEMO": {
                "name": "모의투자 모드",
                "description": "가상의 돈으로 안전하게 거래 연습",
                "pros": [
                    "실제 돈 손실 위험 없음",
                    "모든 플랫폼에서 실행 가능",
                    "무제한 테스트 가능",
                    "전략 개발 및 검증에 최적"
                ],
                "cons": [
                    "실제 수익 불가능",
                    "시뮬레이션 데이터 사용",
                    "실제 시장과 미세한 차이 가능"
                ],
                "recommended_for": [
                    "퀀트 트레이딩 초보자",
                    "새로운 전략 테스트",
                    "시스템 안정성 확인",
                    "교육 목적"
                ]
            },
            "REAL": {
                "name": "실거래 모드",
                "description": "실제 돈으로 진짜 거래 실행",
                "pros": [
                    "실제 수익 가능",
                    "진짜 시장 데이터 사용",
                    "완전한 거래 경험"
                ],
                "cons": [
                    "투자 손실 위험",
                    "Windows 환경 필수",
                    "키움증권 계좌 필요",
                    "시스템 오류 시 실제 손실 가능"
                ],
                "recommended_for": [
                    "충분한 경험자",
                    "모의투자 검증 완료자",
                    "소액 투자 가능자",
                    "실시간 모니터링 가능자"
                ],
                "requirements": [
                    "Windows 10 이상",
                    "키움증권 계좌",
                    "키움 Open API+ 설치",
                    "Python 3.9+",
                    "안정적인 인터넷 연결"
                ]
            }
        },
        "transition_guide": {
            "step1": "모의투자로 최소 1개월 테스트",
            "step2": "모든 전략의 수익성 검증",
            "step3": "리스크 관리 설정 최적화",
            "step4": "Windows 환경 및 키움 API 설치",
            "step5": "실거래 환경변수 설정",
            "step6": "소액(5-10만원)으로 실거래 시작",
            "step7": "안정성 확인 후 점진적 증액"
        },
        "safety_tips": [
            "항상 손절선을 설정하세요",
            "일일 손실 한도를 설정하세요",
            "투자 가능한 돈으로만 거래하세요",
            "시스템을 실시간 모니터링하세요",
            "정기적으로 백업을 생성하세요",
            "네트워크 연결 상태를 확인하세요",
            "긴급상황 시 수동 개입 방법을 숙지하세요"
        ]
    }

def get_current_trading_mode():
    """현재 거래 모드 반환"""
    return CURRENT_TRADING_MODE

def get_current_kiwoom_client():
    """현재 키움 클라이언트 반환"""
    return KIWOOM_CLIENT_INSTANCE

# 의존성 주입용 함수들
def get_trading_mode():
    """거래 모드 의존성"""
    return CURRENT_TRADING_MODE

def get_kiwoom_client():
    """키움 클라이언트 의존성"""
    if KIWOOM_CLIENT_INSTANCE is None:
        raise HTTPException(status_code=503, detail="키움 클라이언트가 초기화되지 않았습니다")
    return KIWOOM_CLIENT_INSTANCE