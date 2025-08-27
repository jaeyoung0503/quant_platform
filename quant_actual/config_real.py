"""
file: config_real.py

실거래용 설정 파일
주의: 실제 계좌 정보와 비밀번호가 필요합니다
"""

import os
from typing import Dict, Any
from datetime import datetime

# 환경변수에서 실제 계좌 정보 로드
KIWOOM_ACCOUNT = os.getenv("KIWOOM_ACCOUNT", "")  # 실제 계좌번호
KIWOOM_PASSWORD = os.getenv("KIWOOM_PASSWORD", "")  # 실제 비밀번호
KIWOOM_CERT_PASSWORD = os.getenv("KIWOOM_CERT_PASSWORD", "")  # 공인인증서 비밀번호

# 실거래 모드 설정
TRADING_CONFIG = {
    "mode": "REAL",  # DEMO → REAL 변경
    "server_type": "REAL",
    "auto_login": True,
    "save_password": False,  # 보안상 비추천
    
    # 실거래 안전장치
    "daily_loss_limit": -50000,    # 일일 최대 손실 (5만원)
    "max_position_size": 100000,   # 최대 포지션 크기 (10만원)
    "max_positions": 3,            # 최대 보유 종목 (3개)
    "emergency_stop_loss": -100000,  # 긴급중단 손실액 (10만원)
    
    # 거래 시간 제한
    "trading_start_time": "09:30",  # 거래 시작
    "trading_end_time": "15:00",    # 거래 종료
    "lunch_break_start": "12:00",   # 점심시간 시작
    "lunch_break_end": "13:00",     # 점심시간 종료
}

# 실거래용 전략 설정 (보수적)
REAL_STRATEGY_CONFIG = {
    "bollinger_bands": {
        "enabled": True,
        "investment_amount": 50000,  # 5만원만 투자
        "target_stocks": ["005930"],  # 삼성전자만
        "parameters": {
            "period": 20,
            "std_multiplier": 2.5,  # 더 보수적
            "stop_loss": 0.02,      # 2% 손절
            "take_profit": 0.03,    # 3% 익절
        }
    },
    "rsi_reversal": {
        "enabled": False,  # 처음에는 1개 전략만
        "investment_amount": 30000,
        "target_stocks": ["035720"],
        "parameters": {
            "period": 14,
            "oversold": 25,  # 더 보수적
            "overbought": 75,
            "stop_loss": 0.03
        }
    }
}

# 리스크 알림 설정
RISK_ALERTS = {
    "email_enabled": True,
    "email_recipients": ["your-email@gmail.com"],
    "slack_enabled": False,
    
    "alert_conditions": {
        "daily_loss": -10000,      # 일일 손실 1만원 시 알림
        "position_loss": -5000,    # 포지션 손실 5천원 시 알림
        "system_error": True,      # 시스템 오류 시 알림
        "connection_lost": True    # 연결 끊김 시 알림
    }
}

# 백업 및 로깅 설정
BACKUP_CONFIG = {
    "auto_backup": True,
    "backup_interval": 3600,  # 1시간마다 백업
    "max_backups": 24,        # 24시간분 보관
    "backup_location": "backups/real_trading/",
    
    "detailed_logging": True,
    "log_all_api_calls": True,
    "log_sensitive_data": False  # 비밀번호 등 로그에 기록 안함
}

def validate_real_trading_config():
    """실거래 설정 검증"""
    errors = []
    warnings = []
    
    # 필수 정보 체크
    if not KIWOOM_ACCOUNT:
        errors.append("KIWOOM_ACCOUNT 환경변수가 설정되지 않음")
    
    if not KIWOOM_PASSWORD:
        errors.append("KIWOOM_PASSWORD 환경변수가 설정되지 않음")
    
    # 안전장치 체크
    total_investment = sum(
        config.get("investment_amount", 0) 
        for config in REAL_STRATEGY_CONFIG.values() 
        if config.get("enabled", False)
    )
    
    if total_investment > 100000:  # 10만원 초과
        warnings.append(f"총 투자금액이 {total_investment:,}원으로 권장액(10만원)을 초과")
    
    # 손절 설정 체크
    for strategy_name, config in REAL_STRATEGY_CONFIG.items():
        if config.get("enabled") and not config.get("parameters", {}).get("stop_loss"):
            warnings.append(f"{strategy_name} 전략에 손절 설정이 없음")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }

def get_real_trading_disclaimer():
    """실거래 면책 고지"""
    return """
    ⚠️  실거래 모드 경고 ⚠️
    
    1. 이 소프트웨어는 실제 돈으로 거래합니다
    2. 투자 손실 위험이 있습니다
    3. 시스템 오류로 인한 손실 가능성이 있습니다
    4. 반드시 소액으로 시작하시기 바랍니다
    5. 충분한 테스트 후 사용하시기 바랍니다
    
    계속하시겠습니까? (yes/no): 
    """

# 실거래 체크리스트
REAL_TRADING_CHECKLIST = [
    "✅ 키움증권 계좌 개설 완료",
    "✅ 키움 Open API+ 설치 완료", 
    "✅ 모의투자로 충분한 테스트 완료",
    "✅ 손절/익절 설정 확인",
    "✅ 일일 손실 한도 설정 확인",
    "✅ 긴급연락처 설정 완료",
    "✅ 백업 시스템 동작 확인",
    "✅ 인터넷 연결 안정성 확인",
    "✅ 투자 가능 금액 확인",
    "✅ 가족/지인에게 자동매매 사실 고지"
]

def print_real_trading_checklist():
    """실거래 체크리스트 출력"""
    print("\n" + "="*50)
    print("🚨 실거래 전 필수 체크리스트")
    print("="*50)
    
    for item in REAL_TRADING_CHECKLIST:
        print(item)
    
    print("="*50)
    print("모든 항목을 확인하신 후 실거래를 시작하세요!")
    print("="*50)

# 실거래 시작 함수
def start_real_trading():
    """실거래 모드 시작"""
    
    # 1. 면책 고지
    disclaimer = get_real_trading_disclaimer()
    response = input(disclaimer).lower().strip()
    
    if response not in ['yes', 'y', '네', 'ㅇ']:
        print("실거래 시작이 취소되었습니다.")
        return False
    
    # 2. 설정 검증
    validation = validate_real_trading_config()
    
    if not validation["valid"]:
        print("❌ 설정 오류:")
        for error in validation["errors"]:
            print(f"  - {error}")
        return False
    
    if validation["warnings"]:
        print("⚠️  경고사항:")
        for warning in validation["warnings"]:
            print(f"  - {warning}")
        
        proceed = input("경고사항을 무시하고 계속하시겠습니까? (yes/no): ").lower().strip()
        if proceed not in ['yes', 'y', '네', 'ㅇ']:
            print("실거래 시작이 취소되었습니다.")
            return False
    
    # 3. 체크리스트 확인
    print_real_trading_checklist()
    checklist_ok = input("\n모든 체크리스트를 확인하셨나요? (yes/no): ").lower().strip()
    
    if checklist_ok not in ['yes', 'y', '네', 'ㅇ']:
        print("체크리스트를 먼저 확인해주세요.")
        return False
    
    # 4. 최종 확인
    print("\n" + "🔥" * 20)
    print("최종 확인: 실제 돈으로 자동매매를 시작합니다!")
    print("🔥" * 20)
    
    final_confirm = input("정말로 시작하시겠습니까? 'START REAL TRADING' 을 입력하세요: ")
    
    if final_confirm != "START REAL TRADING":
        print("실거래 시작이 취소되었습니다.")
        return False
    
    print("\n✅ 실거래 모드로 시스템을 시작합니다...")
    return True

# 환경변수 설정 예시 파일 생성
def create_env_example():
    """실거래용 .env.example 파일 생성"""
    env_content = """
# 키움증권 계좌 정보 (실제 정보로 변경 필요)
KIWOOM_ACCOUNT=8012345-01
KIWOOM_PASSWORD=your_password
KIWOOM_CERT_PASSWORD=your_cert_password

# 실거래 모드 설정
TRADING_MODE=REAL
SERVER_TYPE=REAL

# 보안 설정
SECRET_KEY=your-very-secure-secret-key-here

# 알림 설정
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-email-password
EMAIL_RECIPIENTS=your-email@gmail.com,backup-email@gmail.com

# 슬랙 알림 (선택사항)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
SLACK_CHANNEL=#trading-alerts

# 데이터베이스 (실거래용 별도 DB)
DATABASE_URL=sqlite:///./data/quantrade_real.db

# 로깅 설정
LOG_LEVEL=INFO
LOG_FILE=logs/real_trading.log
"""
    
    with open(".env.real.example", "w", encoding="utf-8") as f:
        f.write(env_content)
    
    print("✅ .env.real.example 파일이 생성되었습니다.")
    print("이 파일을 .env.real로 복사하고 실제 정보로 수정하세요.")

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

if __name__ == "__main__":
    # 실거래 설정 파일 실행 시
    print("🔧 실거래 설정 도구")
    print("-" * 30)
    
    choice = input("""
선택하세요:
1. 실거래 시작
2. 설정 검증만
3. 체크리스트 출력
4. .env 예시 파일 생성
5. 종료

선택 (1-5): """).strip()
    
    if choice == "1":
        if start_real_trading():
            print("실거래 모드가 승인되었습니다.")
        else:
            print("실거래 시작이 취소되었습니다.")
    
    elif choice == "2":
        validation = validate_real_trading_config()
        if validation["valid"]:
            print("✅ 설정이 올바릅니다.")
        else:
            print("❌ 설정 오류가 있습니다:")
            for error in validation["errors"]:
                print(f"  - {error}")
        
        if validation["warnings"]:
            print("⚠️  경고사항:")
            for warning in validation["warnings"]:
                print(f"  - {warning}")
    
    elif choice == "3":
        print_real_trading_checklist()
    
    elif choice == "4":
        create_env_example()
    
    elif choice == "5":
        print("종료합니다.")
    
    else:
        print("잘못된 선택입니다.")