"""
File: backtester/graph/chart_utils.py
Chart Utilities - 공통 유틸리티 함수들
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import os

class ChartUtils:
    """차트 생성을 위한 공통 유틸리티 클래스"""
    
    @staticmethod
    def setup_korean_font():
        """한글 폰트 설정"""
        try:
            # 한글 폰트 설정 시도
            import matplotlib.font_manager as fm
            
            # 시스템에서 사용 가능한 한글 폰트 찾기
            font_list = fm.findSystemFonts(fontpaths=None, fontext='ttf')
            korean_fonts = ['NanumGothic', 'Malgun Gothic', 'AppleGothic', 'DejaVu Sans']
            
            for font_name in korean_fonts:
                try:
                    plt.rcParams['font.family'] = font_name
                    # 테스트
                    fig, ax = plt.subplots()
                    ax.text(0.5, 0.5, '한글 테스트', ha='center')
                    plt.close(fig)
                    print(f"✅ 한글 폰트 설정 완료: {font_name}")
                    return True
                except:
                    continue
            
            # 기본 폰트 사용
            plt.rcParams['font.family'] = 'DejaVu Sans'
            print("⚠️ 한글 폰트를 찾을 수 없어 기본 폰트를 사용합니다.")
            return False
            
        except Exception as e:
            print(f"⚠️ 폰트 설정 실패: {str(e)}")
            return False
    
    @staticmethod
    def create_output_directory(output_dir: str) -> bool:
        """출력 디렉토리 생성"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            return True
        except Exception as e:
            print(f"❌ 디렉토리 생성 실패: {str(e)}")
            return False
    
    @staticmethod
    def validate_chart_data(chart_data: Dict) -> Tuple[bool, str]:
        """차트 데이터 유효성 검사"""
        try:
            # 필수 필드 확인
            required_fields = ['portfolio_history']
            for field in required_fields:
                if field not in chart_data:
                    return False, f"필수 필드 누락: {field}"
            
            # 포트폴리오 히스토리 검사
            portfolio_history = chart_data['portfolio_history']
            if portfolio_history is None or len(portfolio_history) == 0:
                return False, "포트폴리오 히스토리가 비어있습니다."
            
            # 데이터 타입 확인
            if not isinstance(portfolio_history, (list, pd.Series, np.ndarray)):
                return False, f"포트폴리오 히스토리 타입 오류: {type(portfolio_history)}"
            
            return True, "유효한 데이터"
            
        except Exception as e:
            return False, f"데이터 검증 오류: {str(e)}"
    
    @staticmethod
    def normalize_portfolio_data(portfolio_history) -> pd.Series:
        """포트폴리오 데이터 정규화"""
        try:
            # pandas Series로 변환
            if isinstance(portfolio_history, list):
                portfolio_history = pd.Series(portfolio_history)
            elif isinstance(portfolio_history, np.ndarray):
                portfolio_history = pd.Series(portfolio_history)
            
            # 인덱스가 날짜가 아닌 경우 가상 날짜 생성
            if not isinstance(portfolio_history.index, pd.DatetimeIndex):
                start_date = datetime.now() - timedelta(days=len(portfolio_history))
                portfolio_history.index = pd.date_range(
                    start=start_date, 
                    periods=len(portfolio_history), 
                    freq='D'
                )
            
            return portfolio_history
            
        except Exception as e:
            print(f"⚠️ 데이터 정규화 실패: {str(e)}")
            # 기본 Series 반환
            return pd.Series([100] * len(portfolio_history) if hasattr(portfolio_history, '__len__') else [100])
    
    @staticmethod
    def calculate_performance_metrics(portfolio_history: pd.Series) -> Dict:
        """성과 지표 계산"""
        try:
            if len(portfolio_history) < 2:
                return {}
            
            # 기본 수익률 계산
            total_return = (portfolio_history.iloc[-1] / portfolio_history.iloc[0] - 1) * 100
            
            # 일간 수익률
            daily_returns = portfolio_history.pct_change().dropna()
            
            # 연간화 계산 (252 거래일 기준)
            trading_days_per_year = 252
            years = len(portfolio_history) / trading_days_per_year
            annual_return = (portfolio_history.iloc[-1] / portfolio_history.iloc[0]) ** (1/years) - 1
            annual_return_pct = annual_return * 100
            
            # 변동성 (연간화)
            volatility = daily_returns.std() * np.sqrt(trading_days_per_year) * 100
            
            # 샤프 비율 (무위험 수익률 0% 가정)
            sharpe_ratio = annual_return / (volatility / 100) if volatility > 0 else 0
            
            # 최대 낙폭
            peak = portfolio_history.cummax()
            drawdown = (portfolio_history - peak) / peak
            max_drawdown = drawdown.min() * 100
            
            # 승률 계산
            win_rate = (daily_returns > 0).sum() / len(daily_returns) * 100
            
            # 칼마 비율
            calmar_ratio = annual_return_pct / abs(max_drawdown) if max_drawdown != 0 else 0
            
            return {
                'total_return': total_return,
                'annual_return': annual_return_pct,
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'win_rate': win_rate,
                'calmar_ratio': calmar_ratio,
                'trading_days': len(portfolio_history),
                'years': years
            }
            
        except Exception as e:
            print(f"⚠️ 성과 지표 계산 실패: {str(e)}")
            return {
                'total_return': 0,
                'annual_return': 0,
                'volatility': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'win_rate': 50,
                'calmar_ratio': 0,
                'trading_days': 0,
                'years': 0
            }
    
    @staticmethod
    def format_currency(value: float, currency: str = "$") -> str:
        """통화 형식 포매팅"""
        try:
            if abs(value) >= 1e9:
                return f"{currency}{value/1e9:.1f}B"
            elif abs(value) >= 1e6:
                return f"{currency}{value/1e6:.1f}M"
            elif abs(value) >= 1e3:
                return f"{currency}{value/1e3:.1f}K"
            else:
                return f"{currency}{value:,.0f}"
        except:
            return f"{currency}0"
    
    @staticmethod
    def format_percentage(value: float, decimal_places: int = 1) -> str:
        """퍼센트 형식 포매팅"""
        try:
            return f"{value:.{decimal_places}f}%"
        except:
            return "0.0%"
    
    @staticmethod
    def get_color_palette(num_colors: int = 5) -> List[str]:
        """색상 팔레트 반환"""
        base_colors = [
            '#1f77b4',  # 파랑
            '#ff7f0e',  # 주황
            '#2ca02c',  # 초록
            '#d62728',  # 빨강
            '#9467bd',  # 보라
            '#8c564b',  # 갈색
            '#e377c2',  # 분홍
            '#7f7f7f',  # 회색
            '#bcbd22',  # 올리브
            '#17becf'   # 청록
        ]
        
        if num_colors <= len(base_colors):
            return base_colors[:num_colors]
        else:
            # 더 많은 색상이 필요한 경우 반복
            return (base_colors * ((num_colors // len(base_colors)) + 1))[:num_colors]
    
    @staticmethod
    def save_chart_metadata(filepath: str, chart_data: Dict, chart_type: str):
        """차트 메타데이터 저장"""
        try:
            metadata = {
                'chart_type': chart_type,
                'created_at': datetime.now().isoformat(),
                'strategy_name': chart_data.get('strategy_name', 'Unknown'),
                'symbol': chart_data.get('symbol', 'Unknown'),
                'data_points': len(chart_data.get('portfolio_history', [])),
                'file_path': filepath
            }
            
            # 메타데이터 파일 저장 (JSON)
            import json
            metadata_path = filepath.replace('.png', '_metadata.json')
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"⚠️ 메타데이터 저장 실패: {str(e)}")
            return False
    
    @staticmethod
    def create_watermark(ax, text: str = "Quant Backtester MVP", alpha: float = 0.1):
        """워터마크 추가"""
        try:
            ax.text(0.5, 0.5, text, transform=ax.transAxes,
                   fontsize=20, color='gray', alpha=alpha,
                   ha='center', va='center', rotation=45)
        except Exception as e:
            print(f"⚠️ 워터마크 추가 실패: {str(e)}")
    
    @staticmethod
    def apply_chart_style(style_name: str = "seaborn-v0_8"):
        """차트 스타일 적용"""
        try:
            # 사용 가능한 스타일 확인
            available_styles = plt.style.available
            
            if style_name in available_styles:
                plt.style.use(style_name)
            else:
                # 대안 스타일 시도
                alternative_styles = ['seaborn', 'ggplot', 'default']
                for alt_style in alternative_styles:
                    if alt_style in available_styles:
                        plt.style.use(alt_style)
                        print(f"⚠️ {style_name} 스타일을 찾을 수 없어 {alt_style}을 사용합니다.")
                        break
            
            # 기본 설정
            plt.rcParams.update({
                'figure.figsize': (12, 8),
                'font.size': 10,
                'axes.grid': True,
                'grid.alpha': 0.3,
                'lines.linewidth': 2,
                'axes.spines.top': False,
                'axes.spines.right': False
            })
            
            return True
            
        except Exception as e:
            print(f"⚠️ 차트 스타일 적용 실패: {str(e)}")
            return False


class DataValidator:
    """데이터 검증 전용 클래스"""
    
    @staticmethod
    def validate_portfolio_history(data) -> Tuple[bool, str]:
        """포트폴리오 히스토리 데이터 검증"""
        try:
            if data is None:
                return False, "데이터가 None입니다."
            
            if len(data) == 0:
                return False, "데이터가 비어있습니다."
            
            if len(data) < 10:
                return False, f"데이터가 너무 적습니다. (최소 10개 필요, 현재 {len(data)}개)"
            
            # 숫자 데이터 확인
            if isinstance(data, (list, np.ndarray)):
                numeric_data = [x for x in data if isinstance(x, (int, float)) and not np.isnan(x)]
                if len(numeric_data) < len(data) * 0.9:  # 90% 이상이 유효한 숫자여야 함
                    return False, "유효하지 않은 숫자 데이터가 너무 많습니다."
            
            return True, "유효한 데이터"
            
        except Exception as e:
            return False, f"검증 중 오류: {str(e)}"
    
    @staticmethod
    def validate_chart_config(config: Dict) -> Tuple[bool, str]:
        """차트 설정 검증"""
        try:
            required_keys = ['portfolio_history']
            for key in required_keys:
                if key not in config:
                    return False, f"필수 설정 누락: {key}"
            
            # 포트폴리오 히스토리 검증
            is_valid, message = DataValidator.validate_portfolio_history(config['portfolio_history'])
            if not is_valid:
                return False, f"포트폴리오 데이터 오류: {message}"
            
            return True, "유효한 설정"
            
        except Exception as e:
            return False, f"설정 검증 오류: {str(e)}"


class ErrorHandler:
    """에러 처리 전용 클래스"""
    
    @staticmethod
    def safe_chart_creation(chart_func, *args, **kwargs):
        """안전한 차트 생성 래퍼"""
        try:
            return chart_func(*args, **kwargs)
        except Exception as e:
            print(f"❌ 차트 생성 중 오류: {str(e)}")
            return False
    
    @staticmethod
    def create_error_chart(ax, error_message: str, chart_title: str = "Chart Error"):
        """에러 차트 생성"""
        try:
            ax.clear()
            ax.text(0.5, 0.5, f"Error: {error_message}", 
                   ha='center', va='center', transform=ax.transAxes,
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='lightcoral', alpha=0.8))
            ax.set_title(f"{chart_title} (Error)", fontweight='bold')
            ax.axis('off')
        except Exception as nested_e:
            print(f"❌ 에러 차트 생성도 실패: {str(nested_e)}")


# 전역 설정 함수
def setup_mvp_chart_environment():
    """MVP 차트 환경 설정"""
    try:
        # 스타일 적용
        ChartUtils.apply_chart_style()
        
        # 한글 폰트 설정
        ChartUtils.setup_korean_font()
        
        # 경고 메시지 억제
        import warnings
        warnings.filterwarnings('ignore')
        
        print("✅ MVP 차트 환경 설정 완료")
        return True
        
    except Exception as e:
        print(f"⚠️ 차트 환경 설정 실패: {str(e)}")
        return False