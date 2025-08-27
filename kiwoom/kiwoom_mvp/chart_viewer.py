"""
file: kiwoom_mvp/chart_viewer.py
키움증권 주식 데이터 수집기 - 차트 시각화
Phase 1 MVP
Plotly를 이용한 캔들스틱 차트 생성 및 표시
HTML 파일 저장, 브라우저 자동 열기 기능
"""

import os
import webbrowser
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio

from config import get_config

class ChartViewer:
    """주식 차트 생성 및 표시 클래스"""
    
    def __init__(self):
        """차트 뷰어 초기화"""
        self.config = get_config()
        self.logger = logging.getLogger(__name__)
        
        # 차트 저장 경로
        self.chart_path = self.config.CHART_SAVE_PATH
        
        # Plotly 기본 설정
        self._setup_plotly_config()
        
        # 차트 테마 및 색상 설정
        self._setup_chart_themes()
    
    def _setup_plotly_config(self):
        """Plotly 기본 설정"""
        # 기본 템플릿 설정
        pio.templates.default = self.config.CHART_THEME
        
        # 한글 폰트 설정 (Windows 기준)
        chart_font_family = "Malgun Gothic, Arial, sans-serif"
        
        # 기본 레이아웃 설정
        self.default_layout = {
            'font': {
                'family': chart_font_family,
                'size': 12
            },
            'title': {
                'font': {'size': 18, 'family': chart_font_family},
                'x': 0.5,  # 제목 중앙 정렬
                'xanchor': 'center'
            },
            'width': self.config.CHART_WIDTH,
            'height': self.config.CHART_HEIGHT,
            'margin': {'l': 80, 'r': 80, 't': 80, 'b': 80},
            'showlegend': True,
            'legend': {
                'x': 0,
                'y': 1,
                'bgcolor': 'rgba(255,255,255,0.8)',
                'bordercolor': 'rgba(0,0,0,0.2)',
                'borderwidth': 1
            }
        }
    
    def _setup_chart_themes(self):
        """차트 테마 및 색상 설정"""
        self.colors = {
            'up': '#FF4444',      # 상승 - 빨강
            'down': '#4444FF',    # 하락 - 파랑
            'volume': '#888888',  # 거래량 - 회색
            'ma5': '#FF8800',     # 5일선 - 주황
            'ma20': '#00AA00',    # 20일선 - 녹색
            'ma60': '#AA00AA',    # 60일선 - 보라
            'background': '#FFFFFF',  # 배경 - 흰색
            'grid': '#E0E0E0'     # 격자 - 연회색
        }
        
        # 다크 테마일 경우 색상 조정
        if 'dark' in self.config.CHART_THEME.lower():
            self.colors.update({
                'background': '#2F2F2F',
                'grid': '#404040'
            })
    
    def create_candlestick_chart(self, data: pd.DataFrame, stock_code: str, stock_name: str,
                                show_volume: bool = True, show_ma: bool = True) -> Optional[go.Figure]:
        """캔들스틱 차트 생성"""
        try:
            if data is None or data.empty:
                self.logger.error("❌ 차트 생성용 데이터가 없습니다.")
                return None
            
            # 데이터 검증
            required_columns = ['날짜', '시가', '고가', '저가', '종가', '거래량']
            if not all(col in data.columns for col in required_columns):
                self.logger.error(f"❌ 필수 컬럼 누락: {required_columns}")
                return None
            
            # 날짜 컬럼을 datetime으로 변환
            chart_data = data.copy()
            chart_data['날짜'] = pd.to_datetime(chart_data['날짜'], format='%Y%m%d')
            chart_data = chart_data.sort_values('날짜')
            
            # 서브플롯 생성 (가격 차트 + 거래량 차트)
            if show_volume:
                fig = make_subplots(
                    rows=2, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.05,
                    subplot_titles=('주가', '거래량'),
                    row_heights=[0.7, 0.3]
                )
            else:
                fig = go.Figure()
            
            # 캔들스틱 차트 추가
            candlestick = go.Candlestick(
                x=chart_data['날짜'],
                open=chart_data['시가'],
                high=chart_data['고가'],
                low=chart_data['저가'],
                close=chart_data['종가'],
                name='주가',
                increasing_line_color=self.colors['up'],
                decreasing_line_color=self.colors['down'],
                increasing_fillcolor=self.colors['up'],
                decreasing_fillcolor=self.colors['down']
            )
            
            if show_volume:
                fig.add_trace(candlestick, row=1, col=1)
            else:
                fig.add_trace(candlestick)
            
            # 이동평균선 추가
            if show_ma and len(chart_data) >= 5:
                ma_periods = []
                
                # 데이터 길이에 따라 이동평균 기간 결정
                if len(chart_data) >= 5:
                    ma_periods.append(('MA5', 5, self.colors['ma5']))
                if len(chart_data) >= 20:
                    ma_periods.append(('MA20', 20, self.colors['ma20']))
                if len(chart_data) >= 60:
                    ma_periods.append(('MA60', 60, self.colors['ma60']))
                
                for ma_name, period, color in ma_periods:
                    ma_values = chart_data['종가'].rolling(window=period).mean()
                    
                    ma_line = go.Scatter(
                        x=chart_data['날짜'],
                        y=ma_values,
                        mode='lines',
                        name=f'{ma_name}({period}일)',
                        line=dict(color=color, width=1.5),
                        opacity=0.8
                    )
                    
                    if show_volume:
                        fig.add_trace(ma_line, row=1, col=1)
                    else:
                        fig.add_trace(ma_line)
            
            # 거래량 차트 추가
            if show_volume:
                # 거래량 막대 색상 (주가 등락에 따라)
                colors = []
                for i in range(len(chart_data)):
                    if chart_data.iloc[i]['종가'] >= chart_data.iloc[i]['시가']:
                        colors.append(self.colors['up'])
                    else:
                        colors.append(self.colors['down'])
                
                volume_bar = go.Bar(
                    x=chart_data['날짜'],
                    y=chart_data['거래량'],
                    name='거래량',
                    marker_color=colors,
                    opacity=0.7
                )
                
                fig.add_trace(volume_bar, row=2, col=1)
            
            # 레이아웃 설정
            title = f"{stock_name}({stock_code}) - 일봉 차트"
            
            layout_updates = {
                'title': title,
                'xaxis': {
                    'title': '날짜',
                    'rangeslider': {'visible': False},  # 하단 범위 슬라이더 숨김
                    'type': 'date'
                },
                'yaxis': {
                    'title': '주가 (원)',
                    'side': 'right'
                },
                'plot_bgcolor': self.colors['background'],
                'paper_bgcolor': self.colors['background']
            }
            
            if show_volume:
                layout_updates.update({
                    'xaxis2': {
                        'title': '날짜',
                        'type': 'date'
                    },
                    'yaxis2': {
                        'title': '거래량 (주)',
                        'side': 'right'
                    }
                })
            
            # 기본 레이아웃과 업데이트 병합
            final_layout = {**self.default_layout, **layout_updates}
            fig.update_layout(**final_layout)
            
            # 격자 설정
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor=self.colors['grid'])
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor=self.colors['grid'])
            
            self.logger.info(f"✅ {stock_name}({stock_code}) 캔들스틱 차트 생성 완료")
            return fig
            
        except Exception as e:
            self.logger.error(f"❌ 캔들스틱 차트 생성 실패: {e}")
            return None
    
    def create_line_chart(self, data: pd.DataFrame, stock_code: str, stock_name: str) -> Optional[go.Figure]:
        """단순 선 차트 생성 (종가 기준)"""
        try:
            if data is None or data.empty:
                self.logger.error("❌ 차트 생성용 데이터가 없습니다.")
                return None
            
            # 데이터 준비
            chart_data = data.copy()
            chart_data['날짜'] = pd.to_datetime(chart_data['날짜'], format='%Y%m%d')
            chart_data = chart_data.sort_values('날짜')
            
            # 선 차트 생성
            fig = go.Figure()
            
            # 종가 선 추가
            fig.add_trace(go.Scatter(
                x=chart_data['날짜'],
                y=chart_data['종가'],
                mode='lines+markers',
                name='종가',
                line=dict(color=self.colors['up'], width=2),
                marker=dict(size=4)
            ))
            
            # 레이아웃 설정
            title = f"{stock_name}({stock_code}) - 종가 추이"
            
            layout_updates = {
                'title': title,
                'xaxis': {
                    'title': '날짜',
                    'type': 'date'
                },
                'yaxis': {
                    'title': '주가 (원)',
                    'side': 'right'
                },
                'plot_bgcolor': self.colors['background'],
                'paper_bgcolor': self.colors['background']
            }
            
            final_layout = {**self.default_layout, **layout_updates}
            fig.update_layout(**final_layout)
            
            # 격자 설정
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor=self.colors['grid'])
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor=self.colors['grid'])
            
            self.logger.info(f"✅ {stock_name}({stock_code}) 선 차트 생성 완료")
            return fig
            
        except Exception as e:
            self.logger.error(f"❌ 선 차트 생성 실패: {e}")
            return None
    
    def save_chart(self, fig: go.Figure, stock_code: str, stock_name: str, 
                   chart_type: str = '캔들차트') -> Optional[str]:
        """차트를 HTML 파일로 저장"""
        try:
            if fig is None:
                self.logger.error("❌ 저장할 차트가 없습니다.")
                return None
            
            # 파일명 생성
            filename = self.config.get_chart_filename(stock_code, stock_name, chart_type)
            filepath = self.chart_path / filename
            
            # 디렉토리 생성
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # HTML 파일로 저장
            fig.write_html(
                str(filepath),
                config={
                    'displayModeBar': True,
                    'displaylogo': False,
                    'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d']
                },
                div_id="chart-div",
                include_plotlyjs=True
            )
            
            self.logger.info(f"✅ 차트 저장 완료: {filename}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"❌ 차트 저장 실패: {e}")
            return None
    
    def show_chart(self, filepath: str) -> bool:
        """브라우저에서 차트 열기"""
        try:
            if not os.path.exists(filepath):
                self.logger.error(f"❌ 파일이 존재하지 않습니다: {filepath}")
                return False
            
            # 자동 열기 옵션 확인
            if not self.config.AUTO_OPEN_CHART:
                self.logger.info("📊 자동 차트 열기가 비활성화되었습니다.")
                return True
            
            # 브라우저에서 열기
            webbrowser.open('file://' + os.path.abspath(filepath))
            self.logger.info(f"🌐 브라우저에서 차트 열기: {os.path.basename(filepath)}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 차트 열기 실패: {e}")
            return False
    
    def create_and_save_chart(self, data: pd.DataFrame, stock_code: str, stock_name: str,
                             chart_type: str = 'candlestick', show_volume: bool = True, 
                             show_ma: bool = True, auto_open: bool = None) -> Optional[str]:
        """차트 생성, 저장, 열기 통합 함수"""
        try:
            # 차트 생성
            if chart_type.lower() == 'candlestick':
                fig = self.create_candlestick_chart(data, stock_code, stock_name, show_volume, show_ma)
                chart_type_kr = '캔들차트'
            elif chart_type.lower() == 'line':
                fig = self.create_line_chart(data, stock_code, stock_name)
                chart_type_kr = '선차트'
            else:
                self.logger.error(f"❌ 지원하지 않는 차트 타입: {chart_type}")
                return None
            
            if fig is None:
                return None
            
            # 차트 저장
            filepath = self.save_chart(fig, stock_code, stock_name, chart_type_kr)
            if not filepath:
                return None
            
            # 브라우저 열기
            if auto_open is None:
                auto_open = self.config.AUTO_OPEN_CHART
            
            if auto_open:
                self.show_chart(filepath)
            
            return filepath
            
        except Exception as e:
            self.logger.error(f"❌ 통합 차트 생성 실패: {e}")
            return None
    
    def get_chart_list(self, stock_code: str = None) -> List[Dict]:
        """저장된 차트 파일 목록 조회"""
        try:
            chart_list = []
            
            # 검색 패턴 설정
            if stock_code:
                pattern = f"{stock_code}_*.html"
            else:
                pattern = "*.html"
            
            chart_files = list(self.chart_path.glob(pattern))
            
            for chart_file in chart_files:
                try:
                    # 파일명에서 정보 추출
                    parts = chart_file.stem.split('_')
                    if len(parts) >= 4:
                        code = parts[0]
                        name = parts[1]
                        chart_type = parts[2]
                        date = parts[3]
                        
                        # 파일 정보 구성
                        stat = chart_file.stat()
                        chart_info = {
                            'code': code,
                            'name': name,
                            'chart_type': chart_type,
                            'date': date,
                            'filepath': str(chart_file),
                            'filename': chart_file.name,
                            'size': stat.st_size,
                            'created': datetime.fromtimestamp(stat.st_ctime),
                            'modified': datetime.fromtimestamp(stat.st_mtime)
                        }
                        chart_list.append(chart_info)
                except:
                    continue
            
            # 생성 시간 기준 최신순 정렬
            chart_list.sort(key=lambda x: x['created'], reverse=True)
            
            return chart_list
            
        except Exception as e:
            self.logger.error(f"❌ 차트 목록 조회 실패: {e}")
            return []
    
    def delete_chart(self, filepath: str) -> bool:
        """차트 파일 삭제"""
        try:
            if not os.path.exists(filepath):
                self.logger.warning(f"⚠️ 파일이 존재하지 않습니다: {filepath}")
                return False
            
            os.remove(filepath)
            self.logger.info(f"🗑️ 차트 파일 삭제: {os.path.basename(filepath)}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 차트 파일 삭제 실패: {e}")
            return False
    
    def cleanup_old_charts(self, days_to_keep: int = 7):
        """오래된 차트 파일 정리"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            deleted_count = 0
            
            chart_files = list(self.chart_path.glob("*.html"))
            
            for chart_file in chart_files:
                try:
                    file_time = datetime.fromtimestamp(chart_file.stat().st_mtime)
                    
                    if file_time < cutoff_date:
                        chart_file.unlink()
                        deleted_count += 1
                        self.logger.debug(f"🗑️ 차트 파일 정리: {chart_file.name}")
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ 차트 파일 삭제 실패 ({chart_file.name}): {e}")
            
            if deleted_count > 0:
                self.logger.info(f"🧹 오래된 차트 파일 정리: {deleted_count}개 삭제")
            
        except Exception as e:
            self.logger.error(f"❌ 차트 파일 정리 실패: {e}")
    
    def get_chart_stats(self) -> Dict:
        """차트 통계 정보"""
        try:
            all_charts = self.get_chart_list()
            
            stats = {
                'total_charts': len(all_charts),
                'total_size': sum(chart['size'] for chart in all_charts),
                'by_stock': {},
                'by_type': {},
                'by_date': {}
            }
            
            for chart in all_charts:
                # 종목별 통계
                code = chart['code']
                if code not in stats['by_stock']:
                    stats['by_stock'][code] = {'name': chart['name'], 'count': 0}
                stats['by_stock'][code]['count'] += 1
                
                # 타입별 통계
                chart_type = chart['chart_type']
                stats['by_type'][chart_type] = stats['by_type'].get(chart_type, 0) + 1
                
                # 날짜별 통계
                date = chart['date']
                stats['by_date'][date] = stats['by_date'].get(date, 0) + 1
            
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ 차트 통계 생성 실패: {e}")
            return {}
    
    def add_technical_indicators(self, fig: go.Figure, data: pd.DataFrame) -> go.Figure:
        """기술적 지표 추가 (확장 기능)"""
        try:
            chart_data = data.copy()
            chart_data['날짜'] = pd.to_datetime(chart_data['날짜'], format='%Y%m%d')
            
            # RSI (Relative Strength Index) 계산
            if len(chart_data) >= 14:
                delta = chart_data['종가'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                
                # RSI는 별도 subplot에 추가 (현재는 주석 처리)
                # fig.add_trace(go.Scatter(x=chart_data['날짜'], y=rsi, name='RSI'))
            
            # 볼린저 밴드 추가 (20일 기준)
            if len(chart_data) >= 20:
                ma20 = chart_data['종가'].rolling(window=20).mean()
                std20 = chart_data['종가'].rolling(window=20).std()
                
                upper_band = ma20 + (std20 * 2)
                lower_band = ma20 - (std20 * 2)
                
                # 볼린저 밴드 추가
                fig.add_trace(go.Scatter(
                    x=chart_data['날짜'],
                    y=upper_band,
                    mode='lines',
                    name='볼린저 상한',
                    line=dict(color='gray', width=1, dash='dash'),
                    opacity=0.6
                ))
                
                fig.add_trace(go.Scatter(
                    x=chart_data['날짜'],
                    y=lower_band,
                    mode='lines',
                    name='볼린저 하한',
                    line=dict(color='gray', width=1, dash='dash'),
                    fill='tonexty',
                    fillcolor='rgba(128,128,128,0.1)',
                    opacity=0.6
                ))
            
            return fig
            
        except Exception as e:
            self.logger.error(f"❌ 기술적 지표 추가 실패: {e}")
            return fig

# 전역 차트 뷰어 인스턴스
_chart_viewer = None

def get_chart_viewer() -> ChartViewer:
    """차트 뷰어 싱글톤 인스턴스 반환"""
    global _chart_viewer
    if _chart_viewer is None:
        _chart_viewer = ChartViewer()
    return _chart_viewer

if __name__ == "__main__":
    # 테스트 코드
    import logging
    from datetime import timedelta
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🧪 차트 뷰어 테스트 시작...")
    print("=" * 50)
    
    # 차트 뷰어 생성
    viewer = get_chart_viewer()
    
    # 테스트 데이터 생성 (30일치)
    base_date = datetime.now() - timedelta(days=30)
    dates = [(base_date + timedelta(days=i)).strftime('%Y%m%d') for i in range(30)]
    
    # 가상의 주가 데이터 생성 (무작위 워크)
    import random
    random.seed(42)
    
    price = 85000
    test_data = []
    
    for date in dates:
        # 무작위 주가 변동
        change = random.randint(-3000, 3000)
        price = max(price + change, 50000)  # 최소 5만원
        
        # OHLC 데이터 생성
        open_price = price + random.randint(-1000, 1000)
        high_price = max(open_price, price) + random.randint(0, 2000)
        low_price = min(open_price, price) - random.randint(0, 2000)
        close_price = price
        volume = random.randint(1000000, 5000000)
        
        test_data.append({
            '날짜': date,
            '시가': open_price,
            '고가': high_price,
            '저가': low_price,
            '종가': close_price,
            '거래량': volume
        })
    
    test_df = pd.DataFrame(test_data)
    
    print("📊 테스트 데이터 생성 완료:")
    print(f"   - 데이터 개수: {len(test_df)}개")
    print(f"   - 기간: {test_df['날짜'].min()} ~ {test_df['날짜'].max()}")
    print(f"   - 가격 범위: {test_df['종가'].min():,}원 ~ {test_df['종가'].max():,}원")
    
    # 캔들스틱 차트 생성 및 저장
    print("\n🕯️ 캔들스틱 차트 테스트:")
    candlestick_path = viewer.create_and_save_chart(
        data=test_df,
        stock_code='000000',
        stock_name='테스트종목',
        chart_type='candlestick',
        show_volume=True,
        show_ma=True,
        auto_open=False  # 테스트에서는 자동 열기 비활성화
    )
    
    if candlestick_path:
        print(f"✅ 캔들스틱 차트 생성: {os.path.basename(candlestick_path)}")
    else:
        print("❌ 캔들스틱 차트 생성 실패")
    
    # 선 차트 생성 및 저장
    print("\n📈 선 차트 테스트:")
    line_path = viewer.create_and_save_chart(
        data=test_df,
        stock_code='000000',
        stock_name='테스트종목',
        chart_type='line',
        auto_open=False
    )
    
    if line_path:
        print(f"✅ 선 차트 생성: {os.path.basename(line_path)}")
    else:
        print("❌ 선 차트 생성 실패")
    
    # 차트 통계
    print("\n📊 차트 통계:")
    stats = viewer.get_chart_stats()
    print(f"   - 총 차트 수: {stats.get('total_charts', 0)}개")
    print(f"   - 총 크기: {stats.get('total_size', 0):,} bytes")
    print(f"   - 종목별: {stats.get('by_stock', {})}")
    print(f"   - 타입별: {stats.get('by_type', {})}")
    
    print("\n" + "=" * 50)
    print("🎉 차트 뷰어 테스트 완료!")