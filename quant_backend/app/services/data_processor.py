# services/data_processor.py - 실시간 데이터 처리 및 틱차트 서비스 완성본
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio
import json
from collections import deque
import logging

logger = logging.getLogger(__name__)

class TickDataProcessor:
    """실시간 틱 데이터 처리기"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.tick_buffers: Dict[str, deque] = {}
        self.chart_data: Dict[str, Dict] = {}
        self.max_ticks = 1000  # 최대 저장 틱 수
        self.price_alerts: Dict[str, Dict] = {}  # 가격 알림 설정
        
    async def process_tick(self, tick_data: Dict) -> Dict:
        """틱 데이터 처리 메인 함수"""
        stock_code = tick_data['code']
        
        # 틱 버퍼 초기화
        if stock_code not in self.tick_buffers:
            self.tick_buffers[stock_code] = deque(maxlen=self.max_ticks)
            self.chart_data[stock_code] = {
                'minute_bars': [],
                'volume_profile': {},
                'tick_stats': {},
                'indicators': {}
            }
        
        # 데이터 유효성 검사
        if not self._validate_tick_data(tick_data):
            logger.warning(f"유효하지 않은 틱 데이터: {stock_code}")
            return tick_data
        
        # 틱 데이터 추가
        self.tick_buffers[stock_code].append(tick_data)
        
        # 분봉 데이터 업데이트
        await self._update_minute_bar(stock_code, tick_data)
        
        # 볼륨 프로파일 업데이트
        self._update_volume_profile(stock_code, tick_data)
        
        # 틱 통계 업데이트
        self._update_tick_stats(stock_code)
        
        # 기술적 지표 계산
        await self._calculate_indicators(stock_code)
        
        # 가격 알림 체크
        await self._check_price_alerts(stock_code, tick_data)
        
        # Redis에 저장 (설정된 경우)
        if self.redis:
            await self._save_to_redis(stock_code, tick_data)
        
        # 실시간 출력
        self._print_realtime_analysis(stock_code, tick_data)
        
        return tick_data
    
    def _validate_tick_data(self, tick_data: Dict) -> bool:
        """틱 데이터 유효성 검사"""
        required_fields = ['code', 'price', 'volume', 'timestamp']
        
        for field in required_fields:
            if field not in tick_data:
                return False
        
        # 가격과 거래량이 양수인지 확인
        if tick_data['price'] <= 0 or tick_data['volume'] < 0:
            return False
        
        return True
    
    async def _update_minute_bar(self, stock_code: str, tick_data: Dict):
        """1분봉 데이터 업데이트"""
        current_minute = tick_data['timestamp'].replace(second=0, microsecond=0)
        chart_data = self.chart_data[stock_code]
        
        # 현재 분봉이 없거나 새로운 분이면 생성
        if not chart_data['minute_bars'] or chart_data['minute_bars'][-1]['timestamp'] != current_minute:
            new_bar = {
                'timestamp': current_minute,
                'open': tick_data['price'],
                'high': tick_data['price'],
                'low': tick_data['price'],
                'close': tick_data['price'],
                'volume': tick_data['volume'],
                'tick_count': 1,
                'vwap': tick_data['price']  # 가중평균가격
            }
            chart_data['minute_bars'].append(new_bar)
            
            # 최대 480개 (8시간) 분봉 유지
            if len(chart_data['minute_bars']) > 480:
                chart_data['minute_bars'] = chart_data['minute_bars'][-480:]
        else:
            # 기존 분봉 업데이트
            current_bar = chart_data['minute_bars'][-1]
            current_bar['high'] = max(current_bar['high'], tick_data['price'])
            current_bar['low'] = min(current_bar['low'], tick_data['price'])
            current_bar['close'] = tick_data['price']
            current_bar['volume'] += tick_data['volume']
            current_bar['tick_count'] += 1
            
            # VWAP 업데이트
            total_value = (current_bar['vwap'] * (current_bar['volume'] - tick_data['volume'])) + (tick_data['price'] * tick_data['volume'])
            current_bar['vwap'] = total_value / current_bar['volume'] if current_bar['volume'] > 0 else tick_data['price']
    
    def _update_volume_profile(self, stock_code: str, tick_data: Dict):
        """볼륨 프로파일 업데이트"""
        price = tick_data['price']
        volume = tick_data['volume']
        
        volume_profile = self.chart_data[stock_code]['volume_profile']
        
        # 100원 단위로 그룹핑
        price_level = (price // 100) * 100
        
        if price_level not in volume_profile:
            volume_profile[price_level] = {
                'volume': 0,
                'tick_count': 0,
                'first_time': tick_data['timestamp'],
                'last_time': tick_data['timestamp']
            }
        
        volume_profile[price_level]['volume'] += volume
        volume_profile[price_level]['tick_count'] += 1
        volume_profile[price_level]['last_time'] = tick_data['timestamp']
    
    def _update_tick_stats(self, stock_code: str):
        """틱 통계 업데이트"""
        ticks = list(self.tick_buffers[stock_code])
        if len(ticks) < 2:
            return
        
        # 최근 1분간 데이터
        now = datetime.now()
        recent_ticks = [t for t in ticks if (now - t['timestamp']).total_seconds() <= 60]
        
        if recent_ticks:
            prices = [t['price'] for t in recent_ticks]
            volumes = [t['volume'] for t in recent_ticks]
            
            # 가격 변동성 계산
            price_changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
            volatility = np.std(price_changes) if len(price_changes) > 1 else 0
            
            stats = {
                'tick_count_1min': len(recent_ticks),
                'avg_price_1min': np.mean(prices),
                'price_volatility_1min': volatility,
                'total_volume_1min': sum(volumes),
                'avg_volume_1min': np.mean(volumes),
                'max_tick_volume': max(volumes) if volumes else 0,
                'min_price_1min': min(prices),
                'max_price_1min': max(prices),
                'price_range_1min': max(prices) - min(prices) if prices else 0,
                'last_update': now
            }
            
            self.chart_data[stock_code]['tick_stats'] = stats
    
    async def _calculate_indicators(self, stock_code: str):
        """기술적 지표 계산"""
        ticks = list(self.tick_buffers[stock_code])
        if len(ticks) < 20:
            return
        
        prices = [t['price'] for t in ticks[-50:]]  # 최근 50틱
        volumes = [t['volume'] for t in ticks[-50:]]
        
        indicators = {}
        
        # 이동평균
        if len(prices) >= 5:
            indicators['sma5'] = TechnicalIndicators.calculate_sma(prices, 5)
        if len(prices) >= 20:
            indicators['sma20'] = TechnicalIndicators.calculate_sma(prices, 20)
            indicators['rsi'] = TechnicalIndicators.calculate_rsi(prices, 14)
        
        # EMA
        if len(prices) >= 12:
            indicators['ema12'] = TechnicalIndicators.calculate_ema(prices, 12)
        if len(prices) >= 26:
            indicators['ema26'] = TechnicalIndicators.calculate_ema(prices, 26)
            
        # MACD
        if 'ema12' in indicators and 'ema26' in indicators:
            indicators['macd'] = indicators['ema12'] - indicators['ema26']
        
        # 볼린저 밴드
        if len(prices) >= 20:
            bb_result = TechnicalIndicators.calculate_bollinger_bands(prices, 20)
            indicators.update(bb_result)
        
        self.chart_data[stock_code]['indicators'] = indicators
    
    async def _check_price_alerts(self, stock_code: str, tick_data: Dict):
        """가격 알림 체크"""
        if stock_code not in self.price_alerts:
            return
        
        price = tick_data['price']
        alerts = self.price_alerts[stock_code]
        
        # 상한선 알림
        if 'upper_limit' in alerts and price >= alerts['upper_limit']:
            print(f"가격 알림! {stock_code} 상한선 돌파: {price:,}원")
            
        # 하한선 알림  
        if 'lower_limit' in alerts and price <= alerts['lower_limit']:
            print(f"가격 알림! {stock_code} 하한선 돌파: {price:,}원")
    
    def set_price_alert(self, stock_code: str, upper_limit: float = None, lower_limit: float = None):
        """가격 알림 설정"""
        if stock_code not in self.price_alerts:
            self.price_alerts[stock_code] = {}
        
        if upper_limit:
            self.price_alerts[stock_code]['upper_limit'] = upper_limit
        if lower_limit:
            self.price_alerts[stock_code]['lower_limit'] = lower_limit
        
        print(f"[알림 설정] {stock_code} - 상한: {upper_limit:,}원, 하한: {lower_limit:,}원")
    
    def _print_realtime_analysis(self, stock_code: str, tick_data: Dict):
        """실시간 분석 결과 출력"""
        stats = self.chart_data[stock_code].get('tick_stats', {})
        indicators = self.chart_data[stock_code].get('indicators', {})
        timestamp = tick_data['timestamp'].strftime('%H:%M:%S')
        
        # 기본 틱 정보
        print(f"\n╔═══ 실시간 틱 분석 [{stock_code}] {timestamp} ═══╗")
        print(f"║ 현재가: {tick_data['price']:,}원                            ║")
        print(f"║ 거래량: {tick_data['volume']:,}주                             ║")
        print(f"║ 전일대비: {tick_data['change']:+,}원 ({tick_data['change_rate']:+.2f}%)        ║")
        print(f"╠═══════════════════════════════════════════════════════════╣")
        
        # 1분간 통계
        if stats:
            print(f"║ [1분간 통계]                                           ║")
            print(f"║ 틱 수: {stats.get('tick_count_1min', 0):,}개                                    ║")
            print(f"║ 평균가: {stats.get('avg_price_1min', 0):,.0f}원                              ║")
            print(f"║ 변동성: {stats.get('price_volatility_1min', 0):.1f}                                 ║")
            print(f"║ 거래량: {stats.get('total_volume_1min', 0):,}주                             ║")
            print(f"║ 가격범위: {stats.get('price_range_1min', 0):,}원                             ║")
        
        # 기술적 지표
        if indicators:
            print(f"║ [기술적 지표]                                          ║")
            if 'sma5' in indicators:
                sma5_signal = "상승세" if tick_data['price'] > indicators['sma5'] else "하락세"
                print(f"║ SMA5: {indicators['sma5']:,.0f}원 ({sma5_signal})                        ║")
            if 'rsi' in indicators:
                rsi = indicators['rsi']
                rsi_signal = "과매수" if rsi > 70 else "과매도" if rsi < 30 else "중립"
                print(f"║ RSI: {rsi:.1f} ({rsi_signal})                                    ║")
        
        print(f"╚═══════════════════════════════════════════════════════════╝")
        
        # 거래량 분석
        if stats and stats.get('max_tick_volume', 0) > stats.get('avg_volume_1min', 0) * 3:
            avg_vol = stats.get('avg_volume_1min', 1)
            max_vol = stats.get('max_tick_volume', 0)
            ratio = max_vol / max(avg_vol, 1)
            print(f"대량 거래 감지! (평균 대비 {ratio:.1f}배)")
    
    async def _save_to_redis(self, stock_code: str, tick_data: Dict):
        """Redis에 틱 데이터 저장"""
        try:
            # 틱 데이터 저장
            tick_key = f"ticks:{stock_code}"
            tick_json = json.dumps(tick_data, default=str)
            
            await self.redis.lpush(tick_key, tick_json)
            await self.redis.ltrim(tick_key, 0, 999)  # 최대 1000개 유지
            await self.redis.expire(tick_key, 86400)  # 1일 TTL
            
            # 통계 데이터 저장
            stats_key = f"stats:{stock_code}"
            stats = self.chart_data[stock_code].get('tick_stats', {})
            if stats:
                await self.redis.hset(stats_key, mapping=stats)
                await self.redis.expire(stats_key, 3600)  # 1시간 TTL
            
        except Exception as e:
            logger.error(f"Redis 저장 실패: {e}")
    
    def get_tick_chart_data(self, stock_code: str, minutes: int = 60) -> List[Dict]:
        """틱차트 데이터 반환"""
        if stock_code not in self.tick_buffers:
            return []
        
        # 지정된 시간만큼의 틱 데이터 필터링
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        ticks = [
            tick for tick in self.tick_buffers[stock_code] 
            if tick['timestamp'] >= cutoff_time
        ]
        
        return ticks
    
    def get_minute_chart_data(self, stock_code: str) -> List[Dict]:
        """분봉 차트 데이터 반환"""
        if stock_code not in self.chart_data:
            return []
        return self.chart_data[stock_code]['minute_bars']
    
    def get_volume_profile(self, stock_code: str) -> Dict[int, Dict]:
        """볼륨 프로파일 반환"""
        if stock_code not in self.chart_data:
            return {}
        return self.chart_data[stock_code]['volume_profile']
    
    def get_indicators(self, stock_code: str) -> Dict:
        """기술적 지표 반환"""
        if stock_code not in self.chart_data:
            return {}
        return self.chart_data[stock_code].get('indicators', {})
    
    def print_tick_summary(self, stock_code: str):
        """틱 데이터 요약 출력"""
        if stock_code not in self.tick_buffers:
            print(f"{stock_code} 데이터가 없습니다")
            return
        
        ticks = list(self.tick_buffers[stock_code])
        if not ticks:
            return
        
        # 통계 계산
        prices = [t['price'] for t in ticks]
        volumes = [t['volume'] for t in ticks]
        
        print(f"\n============ {stock_code} 틱 데이터 요약 ============")
        print(f"데이터 기간: {ticks[0]['timestamp'].strftime('%H:%M:%S')} ~ {ticks[-1]['timestamp'].strftime('%H:%M:%S')}")
        print(f"총 틱 수: {len(ticks):,}개")
        print(f"가격 범위: {min(prices):,}원 ~ {max(prices):,}원")
        print(f"평균 가격: {np.mean(prices):,.0f}원")
        print(f"총 거래량: {sum(volumes):,}주")
        print(f"평균 틱 거래량: {np.mean(volumes):,.0f}주")
        print(f"최대 틱 거래량: {max(volumes):,}주")
        print("=" * 48)

class TechnicalIndicators:
    """기술적 지표 계산 클래스"""
    
    @staticmethod
    def calculate_sma(prices: List[float], period: int) -> float:
        """단순이동평균"""
        if len(prices) < period:
            return prices[-1] if prices else 0
        return sum(prices[-period:]) / period
    
    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> float:
        """지수이동평균"""
        if len(prices) < period:
            return prices[-1] if prices else 0
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        """RSI 계산"""
        if len(prices) < period + 1:
            return 50
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2) -> Dict:
        """볼린저 밴드 계산"""
        if len(prices) < period:
            return {}
        
        recent_prices = prices[-period:]
        sma = np.mean(recent_prices)
        std = np.std(recent_prices)
        
        return {
            'bb_upper': sma + (std * std_dev),
            'bb_middle': sma,
            'bb_lower': sma - (std * std_dev),
            'bb_width': (std * std_dev * 2) / sma * 100  # 밴드폭 백분율
        }
    
    @staticmethod
    def print_indicators(stock_code: str, prices: List[float]):
        """기술적 지표 출력"""
        if len(prices) < 20:
            return
        
        sma5 = TechnicalIndicators.calculate_sma(prices, 5)
        sma20 = TechnicalIndicators.calculate_sma(prices, 20)
        ema12 = TechnicalIndicators.calculate_ema(prices, 12)
        ema26 = TechnicalIndicators.calculate_ema(prices, 26)
        rsi = TechnicalIndicators.calculate_rsi(prices, 14)
        bb = TechnicalIndicators.calculate_bollinger_bands(prices, 20)
        
        current_price = prices[-1]
        
        print(f"\n[기술적 지표] {stock_code}")
        print(f"├─ 현재가: {current_price:,.0f}원")
        print(f"├─ SMA5: {sma5:,.0f}원 ({'상승' if current_price > sma5 else '하락'})")
        print(f"├─ SMA20: {sma20:,.0f}원 ({'상승' if current_price > sma20 else '하락'})")
        print(f"├─ EMA12: {ema12:,.0f}원")
        print(f"├─ EMA26: {ema26:,.0f}원")
        print(f"├─ RSI(14): {rsi:.1f} ({'과매수' if rsi > 70 else '과매도' if rsi < 30 else '중립'})")
        
        if bb:
            bb_position = "상단" if current_price > bb['bb_upper'] else "하단" if current_price < bb['bb_lower'] else "중간"
            print(f"└─ 볼린저밴드: {bb_position} (폭: {bb['bb_width']:.1f}%)")
        
        # MACD 계산
        macd = ema12 - ema26
        signal = TechnicalIndicators.calculate_ema([macd], 9)
        
        if macd > signal:
            print(f"MACD 매수 신호 (MACD: {macd:.1f} > Signal: {signal:.1f})")
        elif macd < signal:
            print(f"MACD 매도 신호 (MACD: {macd:.1f} < Signal: {signal:.1f})")

class RealTimeChartManager:
    """실시간 차트 매니저"""
    
    def __init__(self, data_processor: TickDataProcessor):
        self.processor = data_processor
        self.chart_subscribers: Dict[str, List] = {}
        self.update_interval = 1  # 1초마다 업데이트
        self.last_update: Dict[str, datetime] = {}
        
    async def add_chart_subscriber(self, stock_code: str, websocket):
        """차트 구독자 추가"""
        if stock_code not in self.chart_subscribers:
            self.chart_subscribers[stock_code] = []
        self.chart_subscribers[stock_code].append(websocket)
        
        print(f"차트 구독자 추가: {stock_code}")
        
        # 초기 차트 데이터 전송
        await self._send_initial_chart_data(stock_code, websocket)
    
    async def _send_initial_chart_data(self, stock_code: str, websocket):
        """초기 차트 데이터 전송"""
        try:
            chart_data = await self.generate_tick_chart_json(stock_code, 30)
            initial_message = {
                'type': 'initial_chart',
                'data': chart_data
            }
            await websocket.send_text(json.dumps(initial_message, default=str))
        except Exception as e:
            logger.error(f"초기 차트 데이터 전송 실패: {e}")
    
    async def remove_chart_subscriber(self, stock_code: str, websocket):
        """차트 구독자 제거"""
        if stock_code in self.chart_subscribers:
            try:
                self.chart_subscribers[stock_code].remove(websocket)
                if not self.chart_subscribers[stock_code]:
                    del self.chart_subscribers[stock_code]
                print(f"차트 구독자 제거: {stock_code}")
            except ValueError:
                pass
    
    async def broadcast_chart_update(self, stock_code: str, tick_data: Dict):
        """차트 업데이트 브로드캐스트"""
        if stock_code not in self.chart_subscribers:
            return
        
        # 업데이트 빈도 제한
        now = datetime.now()
        last_update = self.last_update.get(stock_code, datetime.min)
        if (now - last_update).total_seconds() < self.update_interval:
            return
        
        self.last_update[stock_code] = now
        
        # 차트 데이터 준비
        indicators = self.processor.get_indicators(stock_code)
        stats = self.processor.chart_data.get(stock_code, {}).get('tick_stats', {})
        
        chart_update = {
            'type': 'tick_update',
            'code': stock_code,
            'timestamp': tick_data['timestamp'].isoformat(),
            'price': tick_data['price'],
            'volume': tick_data['volume'],
            'change': tick_data['change'],
            'change_rate': tick_data['change_rate'],
            'indicators': indicators,
            'stats': stats
        }
        
        # 구독자들에게 전송
        message = json.dumps(chart_update, default=str)
        disconnected = []
        
        for websocket in self.chart_subscribers[stock_code]:
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.warning(f"차트 업데이트 전송 실패: {e}")
                disconnected.append(websocket)
        
        # 끊어진 연결 제거
        for ws in disconnected:
            await self.remove_chart_subscriber(stock_code, ws)
    
    def print_chart_status(self):
        """차트 상태 출력"""
        print(f"\n================== 실시간 차트 상태 ==================")
        print(f"활성 차트 수: {len(self.chart_subscribers)}개")
        print(f"업데이트 간격: {self.update_interval}초")
        
        for stock_code, subscribers in self.chart_subscribers.items():
            tick_count = len(self.processor.tick_buffers.get(stock_code, []))
            minute_bars = len(self.processor.chart_data.get(stock_code, {}).get('minute_bars', []))
            last_update = self.last_update.get(stock_code, datetime.min)
            
            print(f"\n[{stock_code}]")
            print(f"├─ 구독자: {len(subscribers)}명")
            print(f"├─ 틱 데이터: {tick_count:,}개")
            print(f"├─ 분봉 데이터: {minute_bars}개")
            print(f"└─ 마지막 업데이트: {last_update.strftime('%H:%M:%S')}")
        
        print("=" * 54)
    
    async def generate_tick_chart_json(self, stock_code: str, minutes: int = 30) -> Dict:
        """틱차트 JSON 데이터 생성"""
        tick_data = self.processor.get_tick_chart_data(stock_code, minutes)
        minute_data = self.processor.get_minute_chart_data(stock_code)
        volume_profile = self.processor.get_volume_profile(stock_code)
        indicators = self.processor.get_indicators(stock_code)
        stats = self.processor.chart_data.get(stock_code, {}).get('tick_stats', {})
        
        return {
            'stock_code': stock_code,
            'timestamp': datetime.now().isoformat(),
            'tick_data': [
                {
                    'time': tick['timestamp'].isoformat(),
                    'price': tick['price'],
                    'volume': tick['volume'],
                    'change': tick.get('change', 0),
                    'change_rate': tick.get('change_rate', 0)
                } for tick in tick_data
            ],
            'minute_bars': [
                {
                    'time': bar['timestamp'].isoformat(),
                    'open': bar['open'],
                    'high': bar['high'],
                    'low': bar['low'],
                    'close': bar['close'],
                    'volume': bar['volume'],
                    'vwap': bar.get('vwap', bar['close'])
                } for bar in minute_data
            ],
            'volume_profile': volume_profile,
            'indicators': indicators,
            'stats': stats
        }
    
    def export_chart_data(self, stock_code: str, format: str = 'json') -> Optional[str]:
        """차트 데이터 내보내기"""
        try:
            chart_data = asyncio.run(self.generate_tick_chart_json(stock_code))
            
            if format.lower() == 'json':
                return json.dumps(chart_data, indent=2, default=str)
            elif format.lower() == 'csv':
                # CSV 형태로 변환
                tick_df = pd.DataFrame(chart_data['tick_data'])
                return tick_df.to_csv(index=False)
            else:
                raise ValueError(f"지원하지 않는 형식: {format}")
                
        except Exception as e:
            logger.error(f"차트 데이터 내보내기 실패: {e}")
            return None