# config.py - 환경 설정 관리 완성본
import os
from typing import Optional, Dict, List
from dataclasses import dataclass
import json
from pathlib import Path
from datetime import datetime

try:
    from pydantic_settings import BaseSettings
except ImportError:
    try:
        from pydantic import BaseSettings
    except ImportError:
        print("pydantic를 설치해주세요: pip install pydantic")
        exit(1)

@dataclass
class KISEnvironment:
    """KIS API 환경 설정"""
    name: str
    app_key: str
    app_secret: str
    base_url: str
    ws_url: str
    account_number: str
    account_product_code: str = "01"
    is_mock: bool = True
    
    def __post_init__(self):
        """초기화 후 검증"""
        if not self.app_key or not self.app_secret:
            raise ValueError(f"{self.name} 환경의 API 키가 설정되지 않았습니다")
        
        if len(self.app_key) < 10 or len(self.app_secret) < 10:
            raise ValueError(f"{self.name} 환경의 API 키 형식이 올바르지 않습니다")
    
    def get_masked_info(self) -> Dict:
        """마스킹된 정보 반환 (보안용)"""
        return {
            'name': self.name,
            'app_key_preview': f"{self.app_key[:4]}****{self.app_key[-4:]}" if len(self.app_key) >= 8 else "****",
            'account_preview': f"{self.account_number[:4]}****{self.account_number[-2:]}" if len(self.account_number) >= 6 else "****",
            'base_url': self.base_url,
            'is_mock': self.is_mock
        }

class KISSettings(BaseSettings):
    """KIS API 설정 (환경별 분리)"""
    
    # 모의투자 환경
    MOCK_APP_KEY: str = ""
    MOCK_APP_SECRET: str = ""
    MOCK_ACCOUNT_NUMBER: str = ""
    MOCK_BASE_URL: str = "https://openapi.koreainvestment.com:9443"
    MOCK_WS_URL: str = "wss://openapi.koreainvestment.com:9443"
    
    # 실전투자 환경
    REAL_APP_KEY: str = ""
    REAL_APP_SECRET: str = ""
    REAL_ACCOUNT_NUMBER: str = ""
    REAL_BASE_URL: str = "https://openapi.koreainvestment.com:9443"
    REAL_WS_URL: str = "wss://openapi.koreainvestment.com:9443"
    
    # 공통 설정
    ACCOUNT_PRODUCT_CODE: str = "01"
    
    # 현재 선택된 환경
    CURRENT_ENVIRONMENT: str = "mock"  # "mock" 또는 "real"
    
    # 로깅 설정
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "kis_quant.log"
    
    # Redis 설정 (선택사항)
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_PASSWORD: str = ""
    
    # 전략 설정
    DEFAULT_STOCKS: List[str] = ["005930", "000660", "035420"]  # 삼성전자, SK하이닉스, NAVER
    MAX_MONITORING_STOCKS: int = 10
    TICK_BUFFER_SIZE: int = 1000
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = 'utf-8'

class EnvironmentSelector:
    """환경 선택 및 관리 클래스"""
    
    def __init__(self, config_file: str = "kis_config.json"):
        self.settings = KISSettings()
        self.current_env: Optional[KISEnvironment] = None
        self.config_file = config_file
        self._load_saved_config()
    
    def _load_saved_config(self):
        """저장된 설정 로드"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.settings.CURRENT_ENVIRONMENT = config.get('current_environment', 'mock')
        except Exception as e:
            print(f"설정 파일 로드 실패: {e}")
    
    def _save_config(self):
        """현재 설정 저장"""
        try:
            config = {
                'current_environment': self.settings.CURRENT_ENVIRONMENT,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"설정 파일 저장 실패: {e}")
    
    def get_available_environments(self) -> Dict[str, KISEnvironment]:
        """사용 가능한 환경 목록 반환"""
        environments = {}
        
        # 모의투자 환경 체크
        if self.settings.MOCK_APP_KEY and self.settings.MOCK_APP_SECRET:
            try:
                environments["mock"] = KISEnvironment(
                    name="모의투자",
                    app_key=self.settings.MOCK_APP_KEY,
                    app_secret=self.settings.MOCK_APP_SECRET,
                    base_url=self.settings.MOCK_BASE_URL,
                    ws_url=self.settings.MOCK_WS_URL,
                    account_number=self.settings.MOCK_ACCOUNT_NUMBER,
                    account_product_code=self.settings.ACCOUNT_PRODUCT_CODE,
                    is_mock=True
                )
            except ValueError as e:
                print(f"모의투자 환경 설정 오류: {e}")
        
        # 실전투자 환경 체크
        if self.settings.REAL_APP_KEY and self.settings.REAL_APP_SECRET:
            try:
                environments["real"] = KISEnvironment(
                    name="실전투자",
                    app_key=self.settings.REAL_APP_KEY,
                    app_secret=self.settings.REAL_APP_SECRET,
                    base_url=self.settings.REAL_BASE_URL,
                    ws_url=self.settings.REAL_WS_URL,
                    account_number=self.settings.REAL_ACCOUNT_NUMBER,
                    account_product_code=self.settings.ACCOUNT_PRODUCT_CODE,
                    is_mock=False
                )
            except ValueError as e:
                print(f"실전투자 환경 설정 오류: {e}")
        
        return environments
    
    def select_environment_interactive(self) -> KISEnvironment:
        """대화형 환경 선택"""
        environments = self.get_available_environments()
        
        if not environments:
            self._print_setup_guide()
            raise ValueError("사용 가능한 환경이 없습니다")
        
        print(f"\n" + "="*60)
        print(f"KIS API 환경 선택")
        print(f"="*60)
        
        # 환경 목록 출력
        env_list = list(environments.items())
        for i, (key, env) in enumerate(env_list, 1):
            masked_info = env.get_masked_info()
            
            print(f"{i}. {env.name}")
            print(f"   ├─ 앱키: {masked_info['app_key_preview']}")
            print(f"   ├─ 계좌: {masked_info['account_preview']}")
            print(f"   ├─ URL: {env.base_url}")
            print(f"   └─ 타입: {'모의투자' if env.is_mock else '실전투자'}")
        
        # 사용자 선택 입력
        while True:
            try:
                print(f"\n환경을 선택하세요 (1-{len(env_list)}): ", end="")
                choice = input().strip()
                
                if choice.isdigit() and 1 <= int(choice) <= len(env_list):
                    selected_key, selected_env = env_list[int(choice) - 1]
                    
                    # 확인 메시지
                    warning = ""
                    if not selected_env.is_mock:
                        warning = "\n실전투자 환경입니다. 실제 거래가 발생할 수 있습니다!"
                    
                    print(f"\n'{selected_env.name}' 환경 선택됨{warning}")
                    print(f"계속 진행하시겠습니까? (y/N): ", end="")
                    confirm = input().strip().lower()
                    
                    if confirm in ['y', 'yes', 'ㅇ']:
                        self.current_env = selected_env
                        self.settings.CURRENT_ENVIRONMENT = selected_key
                        self._save_config()
                        return selected_env
                    else:
                        print("선택을 취소합니다.")
                        continue
                        
                else:
                    print(f"잘못된 선택입니다. 1-{len(env_list)} 중에서 선택하세요.")
                    
            except KeyboardInterrupt:
                print("\n\n사용자가 취소했습니다.")
                exit(1)
            except Exception as e:
                print(f"입력 오류: {e}")
    
    def select_environment_auto(self, env_type: str = "mock") -> KISEnvironment:
        """자동 환경 선택 (명령행 인수용)"""
        environments = self.get_available_environments()
        
        if env_type not in environments:
            available = list(environments.keys())
            raise ValueError(f"환경 '{env_type}'를 찾을 수 없습니다. 사용 가능: {available}")
        
        selected_env = environments[env_type]
        self.current_env = selected_env
        self.settings.CURRENT_ENVIRONMENT = env_type
        self._save_config()
        
        print(f"자동 선택: {selected_env.name} 환경")
        return selected_env
    
    def get_current_environment(self) -> Optional[KISEnvironment]:
        """현재 선택된 환경 반환"""
        return self.current_env
    
    def print_environment_info(self):
        """현재 환경 정보 출력"""
        if not self.current_env:
            print("선택된 환경이 없습니다.")
            return
        
        env = self.current_env
        masked_info = env.get_masked_info()
        
        print(f"\n" + "="*50)
        print(f"현재 KIS API 환경")
        print(f"="*50)
        print(f"환경: {env.name}")
        print(f"타입: {'모의투자' if env.is_mock else '실전투자'}")
        print(f"URL: {env.base_url}")
        print(f"WebSocket: {env.ws_url}")
        print(f"계좌: {masked_info['account_preview']}")
        print(f"앱키: {masked_info['app_key_preview']}")
        print(f"="*50)
        
        if not env.is_mock:
            print("경고: 실전투자 환경에서는 실제 거래가 발생할 수 있습니다!")
    
    def _print_setup_guide(self):
        """설정 가이드 출력"""
        print("\n" + "="*60)
        print("KIS API 환경 설정이 필요합니다")
        print("="*60)
        print("\n.env 파일을 생성하고 다음 내용을 추가하세요:")
        print("\n# 모의투자 환경")
        print("MOCK_APP_KEY=your_mock_app_key_here")
        print("MOCK_APP_SECRET=your_mock_app_secret_here")
        print("MOCK_ACCOUNT_NUMBER=your_mock_account_number")
        print("\n# 실전투자 환경 (선택사항)")
        print("REAL_APP_KEY=your_real_app_key_here")
        print("REAL_APP_SECRET=your_real_app_secret_here")
        print("REAL_ACCOUNT_NUMBER=your_real_account_number")
        print("\n한국투자증권 OpenAPI 사이트에서 API 키를 발급받으세요:")
        print("https://apiportal.koreainvestment.com")
        print("="*60)
    
    def validate_environment(self, env_type: str) -> bool:
        """환경 설정 유효성 검사"""
        environments = self.get_available_environments()
        
        if env_type not in environments:
            return False
        
        env = environments[env_type]
        
        # 필수 필드 체크
        required_fields = ['app_key', 'app_secret', 'account_number']
        for field in required_fields:
            if not getattr(env, field):
                print(f"{env.name} 환경의 {field}가 설정되지 않았습니다")
                return False
        
        return True
    
    def switch_environment(self, new_env_type: str) -> bool:
        """환경 전환"""
        try:
            if not self.validate_environment(new_env_type):
                return False
            
            old_env = self.current_env.name if self.current_env else "없음"
            new_env = self.select_environment_auto(new_env_type)
            
            print(f"환경 전환: {old_env} → {new_env.name}")
            return True
            
        except Exception as e:
            print(f"환경 전환 실패: {e}")
            return False
    
    def get_environment_list(self) -> List[Dict]:
        """환경 목록 반환 (API용)"""
        environments = self.get_available_environments()
        
        env_list = []
        for key, env in environments.items():
            env_info = env.get_masked_info()
            env_info['key'] = key
            env_info['is_current'] = (self.current_env and self.current_env.name == env.name)
            env_list.append(env_info)
        
        return env_list

class ConfigValidator:
    """설정 유효성 검사 클래스"""
    
    @staticmethod
    def validate_env_file() -> Dict[str, bool]:
        """환경 파일 유효성 검사"""
        env_path = Path(".env")
        
        validation_result = {
            'file_exists': env_path.exists(),
            'readable': False,
            'has_mock_config': False,
            'has_real_config': False,
            'errors': []
        }
        
        if not validation_result['file_exists']:
            validation_result['errors'].append(".env 파일이 존재하지 않습니다")
            return validation_result
        
        try:
            # 파일 읽기 테스트
            with open(env_path, 'r', encoding='utf-8') as f:
                content = f.read()
            validation_result['readable'] = True
            
            # 필수 키 존재 여부 확인
            mock_keys = ['MOCK_APP_KEY', 'MOCK_APP_SECRET', 'MOCK_ACCOUNT_NUMBER']
            real_keys = ['REAL_APP_KEY', 'REAL_APP_SECRET', 'REAL_ACCOUNT_NUMBER']
            
            validation_result['has_mock_config'] = all(key in content for key in mock_keys)
            validation_result['has_real_config'] = all(key in content for key in real_keys)
            
            if not validation_result['has_mock_config'] and not validation_result['has_real_config']:
                validation_result['errors'].append("모의투자 또는 실전투자 설정이 필요합니다")
            
        except Exception as e:
            validation_result['errors'].append(f"파일 읽기 오류: {e}")
        
        return validation_result
    
    @staticmethod
    def print_validation_report():
        """유효성 검사 보고서 출력"""
        result = ConfigValidator.validate_env_file()
        
        print(f"\n================== 설정 유효성 검사 ==================")
        print(f"파일 존재: {'✅' if result['file_exists'] else '❌'}")
        print(f"파일 읽기: {'✅' if result['readable'] else '❌'}")
        print(f"모의투자 설정: {'✅' if result['has_mock_config'] else '❌'}")
        print(f"실전투자 설정: {'✅' if result['has_real_config'] else '❌'}")
        
        if result['errors']:
            print(f"\n[오류 목록]")
            for i, error in enumerate(result['errors'], 1):
                print(f"{i}. {error}")
        else:
            print(f"\n모든 설정이 올바릅니다!")
        
        print("=" * 54)
        
        return result

class TradingConfig:
    """거래 전략 설정"""
    
    def __init__(self):
        self.strategies = {
            'momentum': {
                'name': '모멘텀 전략',
                'rsi_oversold': 30,
                'rsi_overbought': 70,
                'volume_threshold': 2.0,  # 평균 대비 배수
                'price_change_threshold': 3.0  # 변동률 %
            },
            'reversal': {
                'name': '역모멘텀 전략',
                'rsi_oversold': 25,
                'rsi_overbought': 75,
                'bollinger_threshold': 0.1,  # 밴드폭 기준
                'support_resistance_ratio': 0.02  # 지지/저항 범위 %
            },
            'scalping': {
                'name': '스캘핑 전략',
                'tick_count_threshold': 10,  # 1분간 최소 틱 수
                'spread_threshold': 0.5,  # 매수/매도 스프레드 %
                'quick_profit_target': 1.0  # 목표 수익률 %
            }
        }
        
        self.risk_management = {
            'max_position_size': 1000000,  # 최대 포지션 크기 (원)
            'stop_loss_percentage': 2.0,   # 손절 비율 %
            'take_profit_percentage': 3.0, # 익절 비율 %
            'max_daily_loss': 100000,      # 일일 최대 손실 (원)
            'position_timeout': 300        # 포지션 타임아웃 (초)
        }
    
    def get_strategy_config(self, strategy_name: str) -> Dict:
        """전략 설정 반환"""
        return self.strategies.get(strategy_name, {})
    
    def update_strategy_config(self, strategy_name: str, config: Dict):
        """전략 설정 업데이트"""
        if strategy_name in self.strategies:
            self.strategies[strategy_name].update(config)
    
    def print_strategy_configs(self):
        """전략 설정 출력"""
        print(f"\n================== 거래 전략 설정 ==================")
        
        for name, config in self.strategies.items():
            print(f"\n[{config['name']}]")
            for key, value in config.items():
                if key != 'name':
                    print(f"├─ {key}: {value}")
        
        print(f"\n[위험 관리]")
        for key, value in self.risk_management.items():
            print(f"├─ {key}: {value}")
        
        print("=" * 54)

# 전역 설정 인스턴스
def get_environment_selector() -> EnvironmentSelector:
    """환경 선택기 인스턴스 반환"""
    return EnvironmentSelector()

def get_trading_config() -> TradingConfig:
    """거래 설정 인스턴스 반환"""
    return TradingConfig()

def check_setup() -> bool:
    """초기 설정 확인"""
    print("KIS API 설정 확인 중...")
    
    # 환경 파일 검사
    validation_result = ConfigValidator.validate_env_file()
    ConfigValidator.print_validation_report()
    
    if validation_result['errors']:
        return False
    
    # 환경 설정 검사
    try:
        env_selector = get_environment_selector()
        environments = env_selector.get_available_environments()
        
        if not environments:
            print("\n사용 가능한 환경이 없습니다.")
            return False
        
        print(f"\n사용 가능한 환경: {len(environments)}개")
        for key, env in environments.items():
            print(f"├─ {env.name} ({key})")
        
        return True
        
    except Exception as e:
        print(f"설정 확인 실패: {e}")
        return False

if __name__ == "__main__":
    """설정 확인 스크립트"""
    print("KIS API 설정 확인 도구")
    print("="*50)
    
    if check_setup():
        print("\n모든 설정이 올바릅니다!")
        
        # 환경 선택 테스트
        env_selector = get_environment_selector()
        try:
            test_env = env_selector.select_environment_interactive()
            print(f"\n테스트 완료: {test_env.name} 환경 선택됨")
        except KeyboardInterrupt:
            print("\n테스트 취소됨")
    else:
        print("\n설정을 확인하고 다시 시도하세요.")