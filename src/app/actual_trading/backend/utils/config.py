# file: backend/utils/config.py

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic_settings import BaseSettings
from pydantic import Field
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 애플리케이션 기본 설정
    app_name: str = "QuanTrade Pro"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = Field(default="development", description="Environment (development, production)")
    
    # 서버 설정
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    
    # 데이터베이스 설정
    database_url: str = "sqlite:///./data/quantrade.db"
    database_echo: bool = False
    
    # 키움 API 설정
    kiwoom_server_type: str = "DEMO"  # DEMO or REAL
    kiwoom_account: str = ""
    kiwoom_password: str = ""
    kiwoom_cert_password: str = ""
    
    # 트레이딩 설정
    initial_capital: float = 50000000.0  # 5천만원
    max_daily_loss: float = -0.02  # -2%
    max_position_size: float = 0.05  # 5%
    max_positions: int = 10
    emergency_sell_all: bool = False
    
    # 리스크 관리 설정
    risk_daily_loss_limit: float = -0.02
    risk_position_size_limit: float = 0.05
    risk_max_positions: int = 10
    risk_max_single_stock_weight: float = 0.15
    risk_max_sector_weight: float = 0.30
    
    # 알림 설정
    email_enabled: bool = False
    email_smtp_server: str = ""
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_recipients: list = []
    
    slack_enabled: bool = False
    slack_webhook_url: str = ""
    slack_channel: str = "#trading"
    
    # 로깅 설정
    log_level: str = "INFO"
    log_file: str = "logs/quantrade.log"
    log_max_size: int = 10485760  # 10MB
    log_backup_count: int = 5
    
    # 시장 시간 설정
    market_open_time: str = "09:00"
    market_close_time: str = "15:30"
    market_timezone: str = "Asia/Seoul"
    
    # 백테스트 설정
    backtest_initial_capital: float = 10000000.0  # 1천만원
    backtest_commission_rate: float = 0.00015  # 0.015%
    backtest_slippage: float = 0.001  # 0.1%
    
    # 캐시 설정
    redis_url: str = "redis://localhost:6379"
    cache_ttl: int = 300  # 5분
    
    # 보안 설정
    secret_key: str = "your-secret-key-here"
    access_token_expire_minutes: int = 1440  # 24시간
    
    # API 제한 설정
    rate_limit_per_minute: int = 60
    max_concurrent_requests: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = False

class ConfigManager:
    """설정 관리자"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.settings = Settings()
        self.strategy_configs = {}
        self.risk_configs = {}
        
        # 설정 파일 로드
        self.load_all_configs()
    
    def load_all_configs(self):
        """모든 설정 파일 로드"""
        try:
            self.load_strategy_configs()
            self.load_risk_configs()
            logger.info("모든 설정 파일 로드 완료")
        except Exception as e:
            logger.error(f"설정 파일 로드 실패: {e}")
    
    def load_strategy_configs(self):
        """전략 설정 로드"""
        try:
            config_file = self.config_dir / "strategies.json"
            
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.strategy_configs = json.load(f)
            else:
                # 기본 전략 설정 생성
                self.strategy_configs = self.get_default_strategy_configs()
                self.save_strategy_configs()
            
            logger.info(f"전략 설정 로드 완료: {len(self.strategy_configs)}개")
            
        except Exception as e:
            logger.error(f"전략 설정 로드 실패: {e}")
            self.strategy_configs = self.get_default_strategy_configs()
    
    def load_risk_configs(self):
        """리스크 설정 로드"""
        try:
            config_file = self.config_dir / "risk_limits.json"
            
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.risk_configs = json.load(f)
            else:
                # 기본 리스크 설정 생성
                self.risk_configs = self.get_default_risk_configs()
                self.save_risk_configs()
            
            logger.info("리스크 설정 로드 완료")
            
        except Exception as e:
            logger.error(f"리스크 설정 로드 실패: {e}")
            self.risk_configs = self.get_default_risk_configs()
    
    def get_default_strategy_configs(self) -> Dict[str, Any]:
        """기본 전략 설정 반환"""
        return {
            "bollinger_bands": {
                "name": "볼린저밴드 평균회귀",
                "enabled": True,
                "parameters": {
                    "period": 20,
                    "std_multiplier": 2.0,
                    "stop_loss": 0.05,
                    "take_profit": 0.03,
                    "min_volume": 100000
                },
                "target_stocks": ["005930", "000660", "035420"],
                "investment_amount": 10000000,
                "max_position_size": 0.05,
                "confidence_threshold": 0.6
            },
            "rsi_reversal": {
                "name": "RSI 역추세",
                "enabled": True,
                "parameters": {
                    "period": 14,
                    "oversold": 30,
                    "overbought": 70,
                    "stop_loss": 0.04,
                    "min_rsi_change": 2
                },
                "target_stocks": ["035720", "051910"],
                "investment_amount": 8000000,
                "max_position_size": 0.04,
                "confidence_threshold": 0.7
            },
            "momentum": {
                "name": "모멘텀 추세추종",
                "enabled": False,
                "parameters": {
                    "short_period": 12,
                    "long_period": 26,
                    "signal_period": 9,
                    "volume_threshold": 1.2,
                    "trend_strength_min": 0.6
                },
                "target_stocks": ["006400", "207940"],
                "investment_amount": 5000000,
                "max_position_size": 0.03,
                "confidence_threshold": 0.8
            },
            "moving_average": {
                "name": "이동평균 골든크로스",
                "enabled": False,
                "parameters": {
                    "short_ma": 5,
                    "long_ma": 20,
                    "volume_threshold": 1000000,
                    "confirmation_period": 3
                },
                "target_stocks": ["373220"],
                "investment_amount": 3000000,
                "max_position_size": 0.02,
                "confidence_threshold": 0.7
            }
        }
    
    def get_default_risk_configs(self) -> Dict[str, Any]:
        """기본 리스크 설정 반환"""
        return {
            "daily_limits": {
                "max_daily_loss": -0.02,
                "max_daily_trades": 50,
                "max_daily_volume": 100000000
            },
            "position_limits": {
                "max_position_size": 0.05,
                "max_positions": 10,
                "max_single_stock_weight": 0.15,
                "max_sector_weight": 0.30
            },
            "volatility_limits": {
                "max_portfolio_volatility": 0.25,
                "high_volatility_threshold": 0.40,
                "volatility_adjustment": True
            },
            "correlation_limits": {
                "max_correlation": 0.70,
                "correlation_check_enabled": True,
                "correlation_period": 60
            },
            "drawdown_limits": {
                "max_drawdown": 0.15,
                "drawdown_alert_level": 0.10,
                "recovery_time_limit": 30
            },
            "emergency_settings": {
                "auto_stop_on_loss": True,
                "emergency_sell_enabled": False,
                "circuit_breaker_level": -0.08,
                "flash_crash_level": -0.05
            }
        }
    
    def save_strategy_configs(self):
        """전략 설정 저장"""
        try:
            config_file = self.config_dir / "strategies.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.strategy_configs, f, indent=2, ensure_ascii=False)
            logger.info("전략 설정 저장 완료")
        except Exception as e:
            logger.error(f"전략 설정 저장 실패: {e}")
    
    def save_risk_configs(self):
        """리스크 설정 저장"""
        try:
            config_file = self.config_dir / "risk_limits.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.risk_configs, f, indent=2, ensure_ascii=False)
            logger.info("리스크 설정 저장 완료")
        except Exception as e:
            logger.error(f"리스크 설정 저장 실패: {e}")
    
    def get_strategy_config(self, strategy_name: str) -> Optional[Dict[str, Any]]:
        """특정 전략 설정 조회"""
        return self.strategy_configs.get(strategy_name)
    
    def update_strategy_config(self, strategy_name: str, config: Dict[str, Any]):
        """전략 설정 업데이트"""
        try:
            self.strategy_configs[strategy_name] = config
            self.save_strategy_configs()
            logger.info(f"전략 설정 업데이트: {strategy_name}")
        except Exception as e:
            logger.error(f"전략 설정 업데이트 실패: {e}")
    
    def get_risk_config(self, category: str = None) -> Dict[str, Any]:
        """리스크 설정 조회"""
        if category:
            return self.risk_configs.get(category, {})
        return self.risk_configs
    
    def update_risk_config(self, category: str, config: Dict[str, Any]):
        """리스크 설정 업데이트"""
        try:
            self.risk_configs[category] = config
            self.save_risk_configs()
            logger.info(f"리스크 설정 업데이트: {category}")
        except Exception as e:
            logger.error(f"리스크 설정 업데이트 실패: {e}")
    
    def get_market_config(self) -> Dict[str, Any]:
        """시장 설정 조회"""
        return {
            "open_time": self.settings.market_open_time,
            "close_time": self.settings.market_close_time,
            "timezone": self.settings.market_timezone,
            "trading_days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
        }
    
    def get_api_config(self) -> Dict[str, Any]:
        """API 설정 조회"""
        return {
            "kiwoom": {
                "server_type": self.settings.kiwoom_server_type,
                "account": self.settings.kiwoom_account,
                # 비밀번호는 보안상 반환하지 않음
            },
            "rate_limit": self.settings.rate_limit_per_minute,
            "max_concurrent": self.settings.max_concurrent_requests
        }
    
    def get_notification_config(self) -> Dict[str, Any]:
        """알림 설정 조회"""
        return {
            "email": {
                "enabled": self.settings.email_enabled,
                "recipients": self.settings.email_recipients,
                "smtp_server": self.settings.email_smtp_server,
                "smtp_port": self.settings.email_smtp_port
            },
            "slack": {
                "enabled": self.settings.slack_enabled,
                "channel": self.settings.slack_channel
            }
        }
    
    def validate_config(self) -> Dict[str, Any]:
        """설정 유효성 검사"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        try:
            # 필수 설정 체크
            if not self.settings.secret_key or self.settings.secret_key == "your-secret-key-here":
                validation_result["errors"].append("SECRET_KEY가 설정되지 않음")
                validation_result["valid"] = False
            
            # 트레이딩 설정 체크
            if self.settings.max_daily_loss >= 0:
                validation_result["errors"].append("일일 손실 한도는 음수여야 함")
                validation_result["valid"] = False
            
            if self.settings.max_position_size <= 0 or self.settings.max_position_size > 1:
                validation_result["errors"].append("포지션 크기 한도는 0과 1 사이여야 함")
                validation_result["valid"] = False
            
            # 전략 설정 체크
            active_strategies = [name for name, config in self.strategy_configs.items() if config.get("enabled")]
            if not active_strategies:
                validation_result["warnings"].append("활성화된 전략이 없음")
            
            # 투자 금액 체크
            total_investment = sum(
                config.get("investment_amount", 0) 
                for config in self.strategy_configs.values() 
                if config.get("enabled")
            )
            
            if total_investment > self.settings.initial_capital:
                validation_result["warnings"].append(
                    f"전략별 투자금액 합계({total_investment:,})가 초기 자본({self.settings.initial_capital:,})을 초과"
                )
            
            # 리스크 설정 체크
            risk_limits = self.risk_configs.get("position_limits", {})
            if risk_limits.get("max_single_stock_weight", 0) > risk_limits.get("max_sector_weight", 1):
                validation_result["warnings"].append("개별 종목 한도가 섹터 한도보다 큼")
            
        except Exception as e:
            validation_result["errors"].append(f"설정 검증 중 오류: {e}")
            validation_result["valid"] = False
        
        return validation_result
    
    def export_config(self, file_path: str):
        """설정을 파일로 내보내기"""
        try:
            export_data = {
                "app_settings": {
                    "app_name": self.settings.app_name,
                    "version": self.settings.app_version,
                    "environment": self.settings.environment,
                    "initial_capital": self.settings.initial_capital
                },
                "trading_settings": {
                    "max_daily_loss": self.settings.max_daily_loss,
                    "max_position_size": self.settings.max_position_size,
                    "max_positions": self.settings.max_positions,
                    "emergency_sell_all": self.settings.emergency_sell_all
                },
                "market_settings": {
                    "open_time": self.settings.market_open_time,
                    "close_time": self.settings.market_close_time,
                    "timezone": self.settings.market_timezone
                },
                "strategies": self.strategy_configs,
                "risk_limits": self.risk_configs,
                "export_timestamp": datetime.now().isoformat()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"설정 내보내기 완료: {file_path}")
            
        except Exception as e:
            logger.error(f"설정 내보내기 실패: {e}")
            raise
    
    def import_config(self, file_path: str):
        """파일에서 설정 가져오기"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # 설정 복원
            if "strategies" in import_data:
                self.strategy_configs = import_data["strategies"]
                self.save_strategy_configs()
            
            if "risk_limits" in import_data:
                self.risk_configs = import_data["risk_limits"]
                self.save_risk_configs()
            
            logger.info(f"설정 가져오기 완료: {file_path}")
            
        except Exception as e:
            logger.error(f"설정 가져오기 실패: {e}")
            raise
    
    def reset_to_defaults(self):
        """기본 설정으로 초기화"""
        try:
            self.strategy_configs = self.get_default_strategy_configs()
            self.risk_configs = self.get_default_risk_configs()
            
            self.save_strategy_configs()
            self.save_risk_configs()
            
            logger.info("설정이 기본값으로 초기화됨")
            
        except Exception as e:
            logger.error(f"설정 초기화 실패: {e}")
            raise

class EnvironmentManager:
    """환경별 설정 관리"""
    
    def __init__(self):
        self.current_env = os.getenv("ENVIRONMENT", "development")
    
    def get_database_url(self) -> str:
        """환경별 데이터베이스 URL"""
        if self.current_env == "production":
            return os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/quantrade_prod")
        elif self.current_env == "testing":
            return "sqlite:///:memory:"
        else:  # development
            return "sqlite:///./data/quantrade_dev.db"
    
    def get_log_level(self) -> str:
        """환경별 로그 레벨"""
        env_log_levels = {
            "production": "WARNING",
            "development": "DEBUG",
            "testing": "ERROR"
        }
        return env_log_levels.get(self.current_env, "INFO")
    
    def is_debug_mode(self) -> bool:
        """디버그 모드 여부"""
        return self.current_env == "development"
    
    def get_api_rate_limit(self) -> int:
        """환경별 API 요청 제한"""
        if self.current_env == "production":
            return 30  # 분당 30회
        else:
            return 100  # 개발/테스트 환경에서는 더 많이 허용

class ConfigValidator:
    """설정 유효성 검증 클래스"""
    
    @staticmethod
    def validate_strategy_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """전략 설정 유효성 검사"""
        result = {"valid": True, "errors": []}
        
        # 필수 필드 체크
        required_fields = ["name", "parameters", "target_stocks", "investment_amount"]
        for field in required_fields:
            if field not in config:
                result["errors"].append(f"필수 필드 누락: {field}")
                result["valid"] = False
        
        # 투자 금액 체크
        investment_amount = config.get("investment_amount", 0)
        if investment_amount <= 0:
            result["errors"].append("투자 금액은 0보다 커야 함")
            result["valid"] = False
        
        # 대상 종목 체크
        target_stocks = config.get("target_stocks", [])
        if not target_stocks:
            result["errors"].append("대상 종목이 없음")
            result["valid"] = False
        
        return result
    
    @staticmethod
    def validate_risk_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """리스크 설정 유효성 검사"""
        result = {"valid": True, "errors": []}
        
        # 손실 한도 체크
        daily_loss = config.get("daily_limits", {}).get("max_daily_loss", 0)
        if daily_loss >= 0:
            result["errors"].append("일일 손실 한도는 음수여야 함")
            result["valid"] = False
        
        # 포지션 한도 체크
        position_limits = config.get("position_limits", {})
        max_position_size = position_limits.get("max_position_size", 0)
        
        if max_position_size <= 0 or max_position_size > 1:
            result["errors"].append("포지션 크기 한도는 0과 1 사이여야 함")
            result["valid"] = False
        
        return result

# 전역 설정 인스턴스
_config_manager = None
_settings = None

def get_config_manager() -> ConfigManager:
    """설정 관리자 싱글톤"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def get_settings() -> Settings:
    """설정 싱글톤"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

def reload_config():
    """설정 다시 로드"""
    global _config_manager, _settings
    _config_manager = None
    _settings = None
    logger.info("설정이 다시 로드됨")

# 환경별 설정 로드
def load_environment_config():
    """환경별 설정 로드"""
    env_manager = EnvironmentManager()
    settings = get_settings()
    
    # 환경별 설정 적용
    if hasattr(settings, 'database_url'):
        settings.database_url = env_manager.get_database_url()
    
    settings.debug = env_manager.is_debug_mode()
    settings.log_level = env_manager.get_log_level()
    
    return settings 
