# services/trading_strategy.py - 통합 전략 실행 서비스
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

from services.kis_auth import KISAuth
from services.kis_websocket import KISWebSocket
from services.kis_api import KISAPI
from services.data_processor import TickDataProcessor, TechnicalIndicators, RealTimeChartManager
from config import TradingConfig

logger = logging.getLogger(__name__)

class SignalType(Enum):
    """거래 신호 타입"""
    BUY = "매수"
    SELL = "매도"
    HOLD = "보유"
    NONE = "없음"

@dataclass
class TradingSignal:
    """거래 신호 데이터 클래스"""
    stock_code: str
    signal_type: SignalType
    price: float
    confidence: float  # 신호 신뢰도 (0.0 ~ 1.0)
    reason: str
    timestamp: datetime
    strategy_name: str

class TradingStrategy:
    """통합 거래 전략 클래스"""
    
    def __init__(self, auth_service: KISAuth, ws_url: str):
        self.auth = auth_service
        self.kis_ws = KISWebSocket(auth_service, ws_url)
        self.data_processor = TickDataProcessor()
        self.chart_manager = RealTimeChartManager(self.data_processor)
        self.trading_config = TradingConfig()
        
        # 전략 상태
        self.active_strategies = ['momentum']  # 기본 전략
        self.monitored_stocks = []
        self.positions = {}  # 현재 포지션
        self.signals_history = []  # 신호 이력
        self.auto_execute = False
        
        # 성과 추적
        self.total_profit = 0
        self.total_trades = 0
        self.win_trades = 0
        self.start_time = datetime.now()
    
    async def start_strategy_monitoring(self, stock_codes: List[str]):
        """전략 모니터링 시작"""
        self.monitored_stocks = stock_codes
        
        try:
            # WebSocket 연결
            await self.kis_ws.connect()
            
            # 각 종목 구독
            for stock_code in stock_codes:
                await self._subscribe_stock_with_strategy(stock_code)
                await asyncio.sleep(0.5)  # API 안정성을 위한 지연
            
            print(f"\n전략 모니터링 시작 완료")
            print(f"활성 전략: {', '.join(self.active_strategies)}")
            print(f"대상 종목: {', '.join(stock_codes)}")
            
        except Exception as e:
            print(f"전략 모니터링 시작 실패: {e}")
            raise
    
    async def _subscribe_stock_with_strategy(self, stock_code: str):
        """종목 구독 및 전략 콜백 설정"""
        async def strategy_callback(tick_data: Dict):
            """전략 실행 콜백"""
            try:
                # 데이터 처리
                await self.data_processor.process_tick(tick_data)
                
                # 차트 업데이트
                await self.chart_manager.broadcast_chart_update(stock_code, tick_data)
                
                # 전략 신호 생성
                signals = await self._generate_signals(tick_data)
                
                # 신호 처리
                for signal in signals:
                    await self._handle_signal(signal)
                
            except Exception as e:
                logger.error(f"전략 콜백 오류: {e}")
        
        # WebSocket 구독
        await self.kis_ws.subscribe_realtime_price(stock_code, strategy_callback)
    
    async def _generate_signals(self, tick_data: Dict) -> List[TradingSignal]:
        """거래 신호 생성"""
        signals = []
        stock_code = tick_data['code']
        
        # 각 활성 전략에 대해 신호 생성
        for strategy_name in self.active_strategies:
            if strategy_name == 'momentum':
                signal = await self._momentum_strategy(tick_data)
            elif strategy_name == 'reversal':
                signal = await self._reversal_strategy(tick_data)
            elif strategy_name == 'scalping':
                signal = await self._scalping_strategy(tick_data)
            else:
                continue
            
            if signal and signal.signal_type != SignalType.NONE:
                signals.append(signal)
        
        return signals
    
    async def _momentum_strategy(self, tick_data: Dict) -> Optional[TradingSignal]:
        """모멘텀 전략"""
        stock_code = tick_data['code']
        
        # 충분한 데이터가 있는지 확인
        if len(self.data_processor.tick_buffers.get(stock_code, [])) < 20:
            return None
        
        # 기술적 지표 가져오기
        indicators = self.data_processor.get_indicators(stock_code)
        stats = self.data_processor.chart_data.get(stock_code, {}).get('tick_stats', {})
        
        if not indicators or not stats:
            return None
        
        config = self.trading_config.get_strategy_config('momentum')
        current_price = tick_data['price']
        change_rate = abs(tick_data.get('change_rate', 0))
        
        # 모멘텀 조건 확인
        rsi = indicators.get('rsi', 50)
        volume_ratio = stats.get('max_tick_volume', 0) / max(stats.get('avg_volume_1min', 1), 1)
        
        # 매수 신호 조건
        if (rsi < config['rsi_oversold'] and 
            change_rate > config['price_change_threshold'] and
            volume_ratio > config['volume_threshold'] and
            tick_data.get('change_rate', 0) > 0):
            
            return TradingSignal(
                stock_code=stock_code,
                signal_type=SignalType.BUY,
                price=current_price,
                confidence=min(0.8, (volume_ratio - 1) * 0.2 + 0.5),
                reason=f"모멘텀 매수: RSI={rsi:.1f}, 변동={change_rate:.1f}%, 거래량={volume_ratio:.1f}배",
                timestamp=tick_data['timestamp'],
                strategy_name='momentum'
            )
        
        # 매도 신호 조건  
        elif (rsi > config['rsi_overbought'] and
              change_rate > config['price_change_threshold'] and
              tick_data.get('change_rate', 0) < 0):
            
            return TradingSignal(
                stock_code=stock_code,
                signal_type=SignalType.SELL,
                price=current_price,
                confidence=0.7,
                reason=f"모멘텀 매도: RSI={rsi:.1f}, 변동={change_rate:.1f}%",
                timestamp=tick_data['timestamp'],
                strategy_name='momentum'
            )
        
        return None
    
    async def _reversal_strategy(self, tick_data: Dict) -> Optional[TradingSignal]:
        """역모멘텀 전략"""
        stock_code = tick_data['code']
        
        if len(self.data_processor.tick_buffers.get(stock_code, [])) < 20:
            return None
        
        indicators = self.data_processor.get_indicators(stock_code)
        config = self.trading_config.get_strategy_config('reversal')
        
        if not indicators:
            return None
        
        current_price = tick_data['price']
        rsi = indicators.get('rsi', 50)
        
        # 볼린저 밴드 기반 역전 신호
        bb_upper = indicators.get('bb_upper', 0)
        bb_lower = indicators.get('bb_lower', 0)
        
        if bb_upper > 0 and bb_lower > 0:
            # 하단 밴드 터치 후 반등 (매수)
            if current_price <= bb_lower * 1.01 and rsi < config['rsi_oversold']:
                return TradingSignal(
                    stock_code=stock_code,
                    signal_type=SignalType.BUY,
                    price=current_price,
                    confidence=0.75,
                    reason=f"역전 매수: 볼린저 하단 터치, RSI={rsi:.1f}",
                    timestamp=tick_data['timestamp'],
                    strategy_name='reversal'
                )
            
            # 상단 밴드 터치 후 하락 (매도)
            elif current_price >= bb_upper * 0.99 and rsi > config['rsi_overbought']:
                return TradingSignal(
                    stock_code=stock_code,
                    signal_type=SignalType.SELL,
                    price=current_price,
                    confidence=0.75,
                    reason=f"역전 매도: 볼린저 상단 터치, RSI={rsi:.1f}",
                    timestamp=tick_data['timestamp'],
                    strategy_name='reversal'
                )
        
        return None
    
    async def _scalping_strategy(self, tick_data: Dict) -> Optional[TradingSignal]:
        """스캘핑 전략"""
        stock_code = tick_data['code']
        stats = self.data_processor.chart_data.get(stock_code, {}).get('tick_stats', {})
        
        if not stats:
            return None
        
        config = self.trading_config.get_strategy_config('scalping')
        
        # 활발한 거래 조건 확인
        tick_count = stats.get('tick_count_1min', 0)
        volume_ratio = stats.get('max_tick_volume', 0) / max(stats.get('avg_volume_1min', 1), 1)
        
        if tick_count >= config['tick_count_threshold'] and volume_ratio > 2.0:
            # 간단한 스캘핑 신호 (추세 추종)
            change_rate = tick_data.get('change_rate', 0)
            
            if change_rate > 1.0:  # 1% 이상 상승
                return TradingSignal(
                    stock_code=stock_code,
                    signal_type=SignalType.BUY,
                    price=tick_data['price'],
                    confidence=0.6,
                    reason=f"스캘핑 매수: 빠른 상승 {change_rate:.1f}%, 활발한 거래",
                    timestamp=tick_data['timestamp'],
                    strategy_name='scalping'
                )
            elif change_rate < -1.0:  # 1% 이상 하락
                return TradingSignal(
                    stock_code=stock_code,
                    signal_type=SignalType.SELL,
                    price=tick_data['price'],
                    confidence=0.6,
                    reason=f"스캘핑 매도: 빠른 하락 {change_rate:.1f}%, 활발한 거래",
                    timestamp=tick_data['timestamp'],
                    strategy_name='scalping'
                )
        
        return None
    
    async def _handle_signal(self, signal: TradingSignal):
        """거래 신호 처리"""
        self.signals_history.append(signal)
        
        # 신호 출력
        self._print_signal(signal)
        
        # 자동 실행 모드인 경우 거래 실행
        if self.auto_execute and signal.confidence > 0.7:
            await self._execute_trade(signal)
        else:
            print(f"[수동 모드] 거래 신호 확인 필요")
    
    def _print_signal(self, signal: TradingSignal):
        """거래 신호 출력"""
        timestamp = signal.timestamp.strftime('%H:%M:%S')
        confidence_bar = "█" * int(signal.confidence * 10)
        
        print(f"\n{'='*60}")
        print(f"거래 신호 발생 [{signal.strategy_name}] {timestamp}")
        print(f"{'='*60}")
        print(f"종목: {signal.stock_code}")
        print(f"신호: {signal.signal_type.value}")
        print(f"가격: {signal.price:,}원")
        print(f"신뢰도: {signal.confidence:.1%} {confidence_bar}")
        print(f"근거: {signal.reason}")
        
        if signal.confidence > 0.8:
            print(f"강한 신호!")
        elif signal.confidence < 0.5:
            print(f"약한 신호 - 주의 필요")
        
        print(f"{'='*60}")
    
    async def _execute_trade(self, signal: TradingSignal):
        """실제 거래 실행 (모의)"""
        try:
            # 실제 거래 API 호출은 여기에 구현
            # 현재는 모의 거래로 처리
            
            print(f"\n[거래 실행] {signal.signal_type.value} 주문")
            print(f"├─ 종목: {signal.stock_code}")
            print(f"├─ 가격: {signal.price:,}원")
            print(f"├─ 전략: {signal.strategy_name}")
            print(f"└─ 시간: {signal.timestamp.strftime('%H:%M:%S')}")
            
            # 포지션 업데이트
            await self._update_position(signal)
            
            self.total_trades += 1
            
            # 성과 가정 (실제로는 체결 결과로 계산)
            simulated_profit = signal.price * 0.01  # 1% 수익 가정
            self.total_profit += simulated_profit
            if simulated_profit > 0:
                self.win_trades += 1
            
        except Exception as e:
            logger.error(f"거래 실행 실패: {e}")
            print(f"거래 실행 실패: {e}")
    
    async def _update_position(self, signal: TradingSignal):
        """포지션 업데이트"""
        stock_code = signal.stock_code
        
        if stock_code not in self.positions:
            self.positions[stock_code] = {
                'quantity': 0,
                'avg_price': 0,
                'total_cost': 0,
                'unrealized_pnl': 0,
                'last_update': datetime.now()
            }
        
        position = self.positions[stock_code]
        
        if signal.signal_type == SignalType.BUY:
            # 매수 포지션 업데이트
            quantity = 100  # 임시로 100주 고정
            cost = signal.price * quantity
            
            if position['quantity'] == 0:
                position['avg_price'] = signal.price
            else:
                total_value = position['total_cost'] + cost
                total_quantity = position['quantity'] + quantity
                position['avg_price'] = total_value / total_quantity
            
            position['quantity'] += quantity
            position['total_cost'] += cost
            
        elif signal.signal_type == SignalType.SELL:
            # 매도 포지션 업데이트
            if position['quantity'] > 0:
                sell_quantity = min(100, position['quantity'])
                position['quantity'] -= sell_quantity
                
                if position['quantity'] == 0:
                    position['avg_price'] = 0
                    position['total_cost'] = 0
        
        position['last_update'] = datetime.now()
    
    def add_strategy(self, strategy_name: str):
        """전략 추가"""
        if strategy_name not in self.active_strategies:
            self.active_strategies.append(strategy_name)
            print(f"전략 추가: {strategy_name}")
    
    def remove_strategy(self, strategy_name: str):
        """전략 제거"""
        if strategy_name in self.active_strategies:
            self.active_strategies.remove(strategy_name)
            print(f"전략 제거: {strategy_name}")
    
    def print_strategy_performance(self):
        """전략 성과 출력"""
        runtime = datetime.now() - self.start_time
        win_rate = (self.win_trades / max(self.total_trades, 1)) * 100
        
        print(f"\n================== 전략 성과 ==================")
        print(f"실행 시간: {int(runtime.total_seconds()//3600)}시간 {int((runtime.total_seconds()%3600)//60)}분")
        print(f"활성 전략: {', '.join(self.active_strategies)}")
        print(f"모니터링 종목: {len(self.monitored_stocks)}개")
        print(f"\n[거래 통계]")
        print(f"├─ 총 거래: {self.total_trades}회")
        print(f"├─ 수익 거래: {self.win_trades}회")
        print(f"├─ 승률: {win_rate:.1f}%")
        print(f"├─ 총 수익: {self.total_profit:+,.0f}원")
        print(f"└─ 신호 수: {len(self.signals_history)}개")
        
        # 최근 신호 출력
        if self.signals_history:
            print(f"\n[최근 신호] 최근 5개")
            for signal in self.signals_history[-5:]:
                time_str = signal.timestamp.strftime('%H:%M:%S')
                print(f"├─ {time_str} {signal.stock_code} {signal.signal_type.value} (신뢰도: {signal.confidence:.1%})")
        
        print("=" * 44)
    
    def print_positions(self):
        """현재 포지션 출력"""
        print(f"\n================= 현재 포지션 =================")
        
        if not self.positions:
            print("보유 포지션이 없습니다.")
            print("=" * 44)
            return
        
        print("종목코드 │ 수량   │ 평균단가 │ 현재가   │ 평가손익")
        print("-" * 44)
        
        total_pnl = 0
        for stock_code, position in self.positions.items():
            if position['quantity'] > 0:
                # 현재가는 마지막 틱 데이터에서 가져오기
                current_price = 0
                if stock_code in self.data_processor.tick_buffers:
                    ticks = list(self.data_processor.tick_buffers[stock_code])
                    if ticks:
                        current_price = ticks[-1]['price']
                
                pnl = (current_price - position['avg_price']) * position['quantity']
                total_pnl += pnl
                pnl_symbol = "+" if pnl >= 0 else ""
                
                print(f"{stock_code} │ {position['quantity']:5,}주 │ {position['avg_price']:7,.0f}원 │ {current_price:7,.0f}원 │ {pnl_symbol}{pnl:8,.0f}원")
        
        print("-" * 44)
        print(f"총 평가손익: {total_pnl:+,.0f}원")
        print("=" * 44)
    
    def print_real_time_dashboard(self):
        """실시간 대시보드 출력"""
        print(f"\n" + "="*80)
        print(f"실시간 퀀트 전략 대시보드 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"="*80)
        
        # 시스템 상태
        print(f"[시스템 상태]")
        print(f"├─ WebSocket: {'연결됨' if self.kis_ws.is_connected else '끊어짐'}")
        print(f"├─ 모니터링 종목: {len(self.monitored_stocks)}개")
        print(f"├─ 활성 전략: {len(self.active_strategies)}개")
        print(f"└─ 자동 실행: {'활성' if self.auto_execute else '비활성'}")
        
        # 성과 요약
        runtime = datetime.now() - self.start_time
        win_rate = (self.win_trades / max(self.total_trades, 1)) * 100
        
        print(f"\n[성과 요약]")
        print(f"├─ 실행 시간: {int(runtime.total_seconds()//3600)}:{int((runtime.total_seconds()%3600)//60):02d}")
        print(f"├─ 총 거래: {self.total_trades}회")
        print(f"├─ 승률: {win_rate:.1f}%")
        print(f"└─ 총 수익: {self.total_profit:+,.0f}원")
        
        # 최근 활동
        if self.signals_history:
            recent_signals = self.signals_history[-3:]
            print(f"\n[최근 신호]")
            for signal in recent_signals:
                time_str = signal.timestamp.strftime('%H:%M:%S')
                print(f"├─ {time_str} {signal.stock_code} {signal.signal_type.value}")
        
        print(f"="*80)
    
    async def stop_monitoring(self):
        """모니터링 중지"""
        try:
            print(f"\n전략 모니터링 중지 중...")
            
            # WebSocket 연결 종료
            await self.kis_ws.disconnect()
            
            # 최종 성과 출력
            self.print_strategy_performance()
            self.print_positions()
            
            print(f"전략 모니터링 중지 완료")
            
        except Exception as e:
            logger.error(f"모니터링 중지 오류: {e}")
    
    def get_signal_statistics(self) -> Dict:
        """신호 통계 반환"""
        if not self.signals_history:
            return {}
        
        # 전략별 신호 통계
        strategy_stats = {}
        for signal in self.signals_history:
            strategy = signal.strategy_name
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {'buy': 0, 'sell': 0, 'total': 0}
            
            if signal.signal_type == SignalType.BUY:
                strategy_stats[strategy]['buy'] += 1
            elif signal.signal_type == SignalType.SELL:
                strategy_stats[strategy]['sell'] += 1
            strategy_stats[strategy]['total'] += 1
        
        # 시간별 신호 분포
        hour_stats = {}
        for signal in self.signals_history:
            hour = signal.timestamp.hour
            if hour not in hour_stats:
                hour_stats[hour] = 0
            hour_stats[hour] += 1
        
        return {
            'total_signals': len(self.signals_history),
            'strategy_breakdown': strategy_stats,
            'hourly_distribution': hour_stats,
            'avg_confidence': sum(s.confidence for s in self.signals_history) / len(self.signals_history)
        }
    
    def export_signals_to_json(self, filename: str = None) -> str:
        """신호 이력을 JSON으로 내보내기"""
        if not filename:
            filename = f"signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            export_data = {
                'export_time': datetime.now().isoformat(),
                'total_signals': len(self.signals_history),
                'signals': [
                    {
                        'stock_code': s.stock_code,
                        'signal_type': s.signal_type.value,
                        'price': s.price,
                        'confidence': s.confidence,
                        'reason': s.reason,
                        'timestamp': s.timestamp.isoformat(),
                        'strategy': s.strategy_name
                    } for s in self.signals_history
                ],
                'statistics': self.get_signal_statistics()
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print(f"신호 이력 내보내기 완료: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"신호 내보내기 실패: {e}")
            print(f"신호 내보내기 실패: {e}")
            return ""

class StrategyOptimizer:
    """전략 최적화 클래스"""
    
    def __init__(self, trading_strategy: TradingStrategy):
        self.strategy = trading_strategy
    
    async def backtest_strategy(self, stock_code: str, days: int = 5) -> Dict:
        """전략 백테스팅 (간단 버전)"""
        print(f"\n[백테스팅] {stock_code} - 최근 {days}일")
        
        try:
            # KIS API로 과거 데이터 가져오기
            async with KISAPI(self.strategy.auth, self.strategy.auth.base_url) as api:
                daily_data = await api.get_daily_chart(stock_code, days)
            
            if not daily_data:
                print("백테스팅용 데이터가 없습니다")
                return {}
            
            # 간단한 백테스팅 로직
            signals = 0
            profitable_signals = 0
            total_return = 0
            
            for i, candle in enumerate(daily_data[:-1]):
                # 모의 신호 생성 (RSI 기반)
                if i >= 14:  # RSI 계산을 위한 최소 데이터
                    closes = [int(c['close']) for c in daily_data[i-14:i+1]]
                    rsi = TechnicalIndicators.calculate_rsi(closes, 14)
                    
                    current_price = int(candle['close'])
                    next_price = int(daily_data[i+1]['close'])
                    
                    # 매수 신호 (RSI < 30)
                    if rsi < 30:
                        signals += 1
                        return_rate = (next_price - current_price) / current_price
                        total_return += return_rate
                        if return_rate > 0:
                            profitable_signals += 1
                        
                        print(f"신호 {signals}: RSI {rsi:.1f} 매수 -> 수익률 {return_rate:.2%}")
            
            # 백테스팅 결과
            win_rate = (profitable_signals / max(signals, 1)) * 100
            avg_return = total_return / max(signals, 1)
            
            result = {
                'period': f"{days}일",
                'total_signals': signals,
                'profitable_signals': profitable_signals,
                'win_rate': win_rate,
                'avg_return': avg_return,
                'total_return': total_return
            }
            
            print(f"\n[백테스팅 결과]")
            print(f"├─ 기간: {days}일")
            print(f"├─ 신호 수: {signals}개")
            print(f"├─ 수익 신호: {profitable_signals}개")
            print(f"├─ 승률: {win_rate:.1f}%")
            print(f"├─ 평균 수익률: {avg_return:.2%}")
            print(f"└─ 누적 수익률: {total_return:.2%}")
            
            return result
            
        except Exception as e:
            logger.error(f"백테스팅 실패: {e}")
            print(f"백테스팅 실패: {e}")
            return {}
    
    def optimize_parameters(self, stock_code: str) -> Dict:
        """전략 파라미터 최적화 (기본 버전)"""
        print(f"\n[파라미터 최적화] {stock_code}")
        
        # RSI 기간 최적화 테스트
        rsi_periods = [10, 14, 20, 25]
        best_rsi = 14
        best_performance = 0
        
        for period in rsi_periods:
            # 임시 성과 계산 (실제로는 백테스팅 결과 사용)
            performance = 0.5 + (period - 14) * 0.1  # 임시 공식
            
            if performance > best_performance:
                best_performance = performance
                best_rsi = period
            
            print(f"├─ RSI({period}): 성과 {performance:.2f}")
        
        optimized_params = {
            'best_rsi_period': best_rsi,
            'expected_performance': best_performance
        }
        
        print(f"└─ 최적 RSI 기간: {best_rsi}")
        
        return optimized_params