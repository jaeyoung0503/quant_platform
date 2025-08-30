# test_setup.py - 설정 및 연결 테스트 스크립트
import asyncio
import sys
import os
from pathlib import Path

# 현재 디렉토리를 Python 경로에 추가
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

async def test_imports():
    """모듈 임포트 테스트"""
    print("=" * 50)
    print("모듈 임포트 테스트")
    print("=" * 50)
    
    try:
        print("1. config 모듈 테스트...")
        from config import EnvironmentSelector, KISSettings
        print("   ✅ config 모듈 임포트 성공")
        
        print("2. kis_auth 모듈 테스트...")
        from services.kis_auth import KISAuth
        print("   ✅ kis_auth 모듈 임포트 성공")
        
        print("3. kis_websocket 모듈 테스트...")
        from services.kis_websocket import KISWebSocket
        print("   ✅ kis_websocket 모듈 임포트 성공")
        
        print("4. data_processor 모듈 테스트...")
        from services.data_processor import TickDataProcessor, TechnicalIndicators
        print("   ✅ data_processor 모듈 임포트 성공")
        
        print("5. kis_api 모듈 테스트...")
        from services.kis_api import KISAPI
        print("   ✅ kis_api 모듈 임포트 성공")
        
        print("\n✅ 모든 모듈 임포트 성공!")
        return True
        
    except ImportError as e:
        print(f"   ❌ 임포트 실패: {e}")
        return False
    except Exception as e:
        print(f"   ❌ 예상치 못한 오류: {e}")
        return False

async def test_environment_setup():
    """환경 설정 테스트"""
    print("\n" + "=" * 50)
    print("환경 설정 테스트")
    print("=" * 50)
    
    try:
        from config import EnvironmentSelector, ConfigValidator
        
        # .env 파일 존재 확인
        env_file = Path(".env")
        print(f"1. .env 파일 존재: {'✅' if env_file.exists() else '❌'}")
        
        if not env_file.exists():
            print("   .env 파일을 생성하세요:")
            print("   cp .env.template .env")
            return False
        
        # 설정 유효성 검사
        print("2. 설정 유효성 검사...")
        validation = ConfigValidator.validate_env_file()
        
        if validation['has_mock_config']:
            print("   ✅ 모의투자 설정 완료")
        else:
            print("   ❌ 모의투자 설정 누락")
        
        if validation['has_real_config']:
            print("   ✅ 실전투자 설정 완료")
        else:
            print("   ⚠️  실전투자 설정 누락 (선택사항)")
        
        # 환경 선택기 테스트
        print("3. 환경 선택기 테스트...")
        env_selector = EnvironmentSelector()
        environments = env_selector.get_available_environments()
        
        print(f"   사용 가능한 환경: {len(environments)}개")
        for key, env in environments.items():
            print(f"   ├─ {env.name} ({key})")
        
        if environments:
            print("   ✅ 환경 설정 성공")
            return True
        else:
            print("   ❌ 사용 가능한 환경 없음")
            return False
        
    except Exception as e:
        print(f"   ❌ 환경 설정 테스트 실패: {e}")
        return False

async def test_kis_connection():
    """KIS API 연결 테스트"""
    print("\n" + "=" * 50)
    print("KIS API 연결 테스트")
    print("=" * 50)
    
    try:
        from config import EnvironmentSelector
        from services.kis_auth import KISAuth
        
        # 환경 선택
        env_selector = EnvironmentSelector()
        environments = env_selector.get_available_environments()
        
        if not environments:
            print("❌ 설정된 환경이 없습니다")
            return False
        
        # 모의투자 환경으로 테스트
        test_env = None
        if "mock" in environments:
            test_env = environments["mock"]
        else:
            test_env = list(environments.values())[0]
        
        print(f"테스트 환경: {test_env.name}")
        
        # 인증 서비스 초기화
        auth = KISAuth(
            app_key=test_env.app_key,
            app_secret=test_env.app_secret,
            base_url=test_env.base_url,
            account_number=test_env.account_number
        )
        
        # 연결 테스트
        success = await auth.test_connection()
        
        if success:
            print("✅ KIS API 연결 성공!")
            return True
        else:
            print("❌ KIS API 연결 실패")
            return False
            
    except Exception as e:
        print(f"❌ 연결 테스트 실패: {e}")
        return False

async def main():
    """메인 테스트 함수"""
    print("KIS 퀀트 시스템 설정 테스트")
    print("=" * 50)
    
    # 1. 모듈 임포트 테스트
    import_success = await test_imports()
    
    if not import_success:
        print("\n❌ 모듈 임포트 실패 - 패키지 설치를 확인하세요")
        print("pip install -r requirements.txt")
        return
    
    # 2. 환경 설정 테스트
    env_success = await test_environment_setup()
    
    if not env_success:
        print("\n❌ 환경 설정 실패 - .env 파일을 확인하세요")
        return
    
    # 3. KIS API 연결 테스트
    print("\nKIS API 연결을 테스트하시겠습니까? (y/N): ", end="")
    test_api = input().strip().lower()
    
    if test_api in ['y', 'yes', 'ㅇ']:
        api_success = await test_kis_connection()
        
        if api_success:
            print("\n🎉 모든 테스트 성공! 시스템 실행 준비 완료")
            print("\n다음 명령으로 시스템을 시작할 수 있습니다:")
            print("python main.py")
        else:
            print("\n❌ API 연결 실패 - API 키와 네트워크를 확인하세요")
    else:
        print("\n✅ 기본 설정 테스트 완료")
        print("시스템을 실행하여 API 연결을 확인하세요")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n테스트 중단됨")
    except Exception as e:
        print(f"\n테스트 실행 오류: {e}")
        sys.exit(1)