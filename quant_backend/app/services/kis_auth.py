# services/kis_auth.py - KIS 인증 서비스 (순환 임포트 해결)
import aiohttp
import asyncio
import json
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class KISAuth:
    """KIS API 인증 관리 클래스"""
    
    def __init__(self, app_key: str, app_secret: str, base_url: str, account_number: str = ""):
        self.app_key = app_key
        self.app_secret = app_secret
        self.base_url = base_url
        self.account_number = account_number
        self.access_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        self.websocket_key: Optional[str] = None
        self._lock = asyncio.Lock()
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def get_access_token(self) -> str:
        """액세스 토큰 반환 (필요시 갱신)"""
        async with self._lock:
            if self._is_token_valid():
                return self.access_token
            
            await self._refresh_token()
            return self.access_token
    
    def _is_token_valid(self) -> bool:
        """토큰 유효성 검사"""
        if not self.access_token or not self.token_expiry:
            return False
        
        # 5분 여유를 두고 갱신
        return self.token_expiry > datetime.now() + timedelta(minutes=5)
    
    async def _refresh_token(self):
        """토큰 갱신"""
        if not self.session:
            await self.__aenter__()
        
        url = f"{self.base_url}/oauth2/tokenP"
        data = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        
        try:
            logger.info("KIS API 토큰 갱신 중...")
            
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    self.access_token = result["access_token"]
                    expires_in = result.get("expires_in", 86400)
                    self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
                    
                    logger.info(f"토큰 갱신 완료 (만료: {self.token_expiry.strftime('%Y-%m-%d %H:%M:%S')})")
                    self._print_token_status()
                    
                else:
                    error_text = await response.text()
                    raise Exception(f"토큰 발급 실패: {response.status} - {error_text}")
                        
        except Exception as error:
            logger.error(f"토큰 갱신 실패: {error}")
            print(f"\n[오류] 토큰 갱신 실패: {error}")
            raise error
    
    async def get_websocket_key(self) -> str:
        """WebSocket 승인키 발급"""
        if not self.session:
            await self.__aenter__()
        
        url = f"{self.base_url}/oauth2/Approval"
        data = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "secretkey": self.app_secret
        }
        
        try:
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    self.websocket_key = result["approval_key"]
                    logger.info("WebSocket 승인키 발급 완료")
                    return self.websocket_key
                else:
                    error_text = await response.text()
                    raise Exception(f"WebSocket 키 발급 실패: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error(f"WebSocket 키 발급 실패: {e}")
            raise e
    
    def get_headers(self, tr_id: str) -> dict:
        """API 호출용 헤더 생성"""
        if not self.access_token:
            raise Exception("액세스 토큰이 없습니다. get_access_token()을 먼저 호출하세요.")
        
        return {
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
            "custtype": "P",
            "content-type": "application/json; charset=utf-8"
        }
    
    def get_websocket_headers(self) -> dict:
        """WebSocket 연결용 헤더 생성"""
        if not self.websocket_key:
            raise Exception("WebSocket 키가 없습니다. get_websocket_key()를 먼저 호출하세요.")
        
        return {
            "approval_key": self.websocket_key,
            "custtype": "P",
            "tr_type": "1",
            "content_type": "utf-8"
        }
    
    def _print_token_status(self):
        """토큰 상태 출력"""
        if not self.access_token:
            print("\n[토큰 상태] 토큰 없음")
            return
        
        remaining_time = self.token_expiry - datetime.now()
        hours = remaining_time.total_seconds() // 3600
        minutes = (remaining_time.total_seconds() % 3600) // 60
        
        print(f"\n[토큰 상태] 새 액세스 토큰 발급 완료")
        print(f"├─ 발급시간: {datetime.now().strftime('%H:%M:%S')}")
        print(f"├─ 만료시간: {self.token_expiry.strftime('%H:%M:%S')}")
        print(f"└─ 잔여시간: {int(hours)}시간 {int(minutes)}분")
    
    def print_status(self):
        """현재 인증 상태 상세 출력"""
        print("\n==================== KIS 인증 상태 ====================")
        print(f"APP KEY: {self.app_key[:8]}{'*' * (len(self.app_key) - 12)}{self.app_key[-4:]}")
        print(f"계좌번호: {self.account_number[:4]}{'*' * 4}{self.account_number[-2:] if len(self.account_number) > 6 else ''}")
        print(f"API URL: {self.base_url}")
        
        if self.access_token:
            print(f"액세스 토큰: {self.access_token[:15]}...")
            print(f"토큰 만료: {self.token_expiry.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"토큰 상태: {'유효' if self._is_token_valid() else '만료'}")
            
            if self._is_token_valid():
                remaining = self.token_expiry - datetime.now()
                print(f"잔여시간: {int(remaining.total_seconds()//3600)}시간 {int((remaining.total_seconds()%3600)//60)}분")
        else:
            print("액세스 토큰: 없음")
        
        if self.websocket_key:
            print(f"WebSocket 키: {self.websocket_key[:15]}...")
        else:
            print("WebSocket 키: 없음")
        
        print("=" * 54)
    
    async def test_connection(self) -> bool:
        """연결 테스트"""
        try:
            print("\n[연결 테스트] KIS API 연결 확인 중...")
            
            # 토큰 발급 테스트
            token = await self.get_access_token()
            print("├─ 토큰 발급: 성공")
            
            # WebSocket 키 발급 테스트
            ws_key = await self.get_websocket_key()
            print("├─ WebSocket 키: 성공")
            
            print("└─ 전체 연결: 성공")
            return True
            
        except Exception as e:
            print(f"└─ 연결 테스트 실패: {e}")
            return False
    
    async def cleanup(self):
        """리소스 정리"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("HTTP 세션 정리 완료")