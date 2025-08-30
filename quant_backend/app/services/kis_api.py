# services/kis_api.py - KIS REST API 클라이언트 완성본
import aiohttp
import asyncio
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class KISAPI:
    """KIS REST API 클라이언트 완성본"""
    
    def __init__(self, auth_service, base_url: str):
        self.auth = auth_service
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        
        # API 호출 제한 관리
        self.call_count = 0
        self.last_call_time = datetime.now()
        self.daily_call_count = 0
        self.last_reset_date = datetime.now().date()
        
        # 호출 통계
        self.success_count = 0
        self.error_count = 0
        self.total_response_time = 0
    
    async def __aenter__(self):
        if not self.session or self.session.closed:
            connector = aiohttp.TCPConnector(limit=100, limit_per_host=10)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=30, connect=10),
                headers={"User-Agent": "KIS-Quant-Backend/1.0"}
            )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def _rate_limit_check(self):
        """API 호출 제한 관리"""
        now = datetime.now()
        
        # 일일 카운터 리셋
        if now.date() > self.last_reset_date:
            self.daily_call_count = 0
            self.last_reset_date = now.date()
            print(f"\n[API 제한] 일일 카운터 리셋 - 새로운 날: {now.date()}")
        
        # 분당 제한 체크 (20회/분)
        time_since_last = (now - self.last_call_time).total_seconds()
        if time_since_last < 60:
            if self.call_count >= 18:  # 안전 마진 2회
                wait_time = 60 - time_since_last
                print(f"API 분당 제한 도달 - {wait_time:.1f}초 대기 중...")
                print(f"   현재: {self.call_count}/20회")
                await asyncio.sleep(wait_time)
                self.call_count = 0
        else:
            self.call_count = 0
        
        # 일일 제한 체크 (10,000회/일)
        if self.daily_call_count >= 9500:
            print(f"일일 API 호출 제한 근접: {self.daily_call_count}/10,000회")
            if self.daily_call_count >= 9900:
                raise Exception("일일 API 호출 제한 초과")
        
        self.call_count += 1
        self.daily_call_count += 1
        self.last_call_time = now
    
    async def _make_request(self, method: str, url: str, headers: Dict, params: Dict = None, data: Dict = None, retries: int = 3) -> Dict:
        """공통 API 요청 메서드 (재시도 로직 포함)"""
        if not self.session:
            await self.__aenter__()
        
        for attempt in range(retries):
            try:
                await self._rate_limit_check()
                
                start_time = datetime.now()
                
                if method.upper() == "GET":
                    async with self.session.get(url, headers=headers, params=params) as response:
                        result = await self._handle_response(response)
                elif method.upper() == "POST":
                    async with self.session.post(url, headers=headers, json=data) as response:
                        result = await self._handle_response(response)
                else:
                    raise ValueError(f"지원하지 않는 HTTP 메서드: {method}")
                
                # 성공 통계 업데이트
                response_time = (datetime.now() - start_time).total_seconds()
                self.success_count += 1
                self.total_response_time += response_time
                
                return result
                
            except Exception as e:
                self.error_count += 1
                
                if "토큰 만료" in str(e) and attempt < retries - 1:
                    print(f"토큰 만료로 재시도 {attempt + 1}/{retries}")
                    await asyncio.sleep(1)
                    continue
                elif "API 호출 제한" in str(e) and attempt < retries - 1:
                    wait_time = 60 * (attempt + 1)
                    print(f"API 제한으로 {wait_time}초 대기 후 재시도 {attempt + 1}/{retries}")
                    await asyncio.sleep(wait_time)
                    continue
                elif attempt < retries - 1:
                    wait_time = 2 ** attempt
                    print(f"요청 실패로 {wait_time}초 대기 후 재시도 {attempt + 1}/{retries}: {e}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(f"API 요청 최종 실패: {e}")
                    raise e
    
    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict:
        """응답 처리"""
        if response.status == 200:
            result = await response.json()
            
            # 응답 코드 체크
            rt_cd = result.get("rt_cd", "")
            if rt_cd != "0":
                msg1 = result.get("msg1", "")
                logger.warning(f"API 경고: {rt_cd} - {msg1}")
                
            return result
            
        elif response.status == 401:
            # 토큰 만료 - 재발급 시도
            print("토큰 만료 감지 - 자동 갱신 중...")
            await self.auth._refresh_token()
            raise Exception("토큰 만료 - 재시도 필요")
            
        elif response.status == 429:
            print("API 호출 제한 - 1분 대기 중...")
            await asyncio.sleep(60)
            raise Exception("API 호출 제한 - 재시도 필요")
            
        else:
            error_text = await response.text()
            logger.error(f"API 오류: {response.status} - {error_text}")
            raise Exception(f"API 오류: {response.status} - {error_text}")
    
    async def get_current_price(self, stock_code: str) -> Dict:
        """현재가 상세 조회"""
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
        headers = self.auth.get_headers("FHKST01010100")
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": stock_code
        }
        
        try:
            result = await self._make_request("GET", url, headers, params)
            data = result.get("output", {})
            
            if data:
                # 응답 데이터 정규화
                normalized_data = self._normalize_price_data(data)
                self._print_detailed_price_info(stock_code, normalized_data)
                return normalized_data
            else:
                print(f"[경고] {stock_code} 현재가 데이터가 비어있음")
                return {}
            
        except Exception as e: