"""
유틸리티 함수 모듈
"""

import os
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

def format_currency(amount: int) -> str:
    """금액 포맷팅"""
    try:
        return f"{amount:,}원"
    except:
        return "0원"

def format_percentage(rate: float) -> str:
    """퍼센트 포맷팅"""
    try:
        return f"{rate:+.2f}%"
    except:
        return "0.00%"

def format_datetime(dt_string: str, format_type: str = "short") -> str:
    """날짜시간 포맷팅"""
    try:
        if not dt_string:
            return "-"
        
        # ISO 형식 파싱
        dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        
        if format_type == "short":
            return dt.strftime("%m-%d %H:%M")
        elif format_type == "long":
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return dt.strftime("%H:%M:%S")
    except:
        return dt_string[:16] if len(dt_string) > 16 else dt_string

def validate_stock_code(stock_code: str) -> bool:
    """종목코드 유효성 검사"""
    try:
        if not stock_code:
            return False
        
        # 6자리 숫자인지 확인
        if len(stock_code) == 6 and stock_code.isdigit():
            return True
        
        return False
    except:
        return False

def calculate_profit_loss(quantity: int, avg_price: int, current_price: int) -> Dict[str, Any]:
    """손익 계산"""
    try:
        if quantity <= 0 or avg_price <= 0 or current_price <= 0:
            return {
                'profit_loss': 0,
                'profit_rate': 0.0,
                'market_value': 0
            }
        
        market_value = quantity * current_price
        cost_value = quantity * avg_price
        profit_loss = market_value - cost_value
        profit_rate = (current_price - avg_price) / avg_price * 100
        
        return {
            'profit_loss': profit_loss,
            'profit_rate': profit_rate,
            'market_value': market_value,
            'cost_value': cost_value
        }
    except:
        return {
            'profit_loss': 0,
            'profit_rate': 0.0,
            'market_value': 0
        }

def get_trading_fee(amount: int, fee_rate: float = 0.00015) -> int:
    """거래 수수료 계산"""
    try:
        fee = int(amount * fee_rate)
        return max(fee, 100)  # 최소 수수료 100원
    except:
        return 100

def validate_order_params(stock_code: str, quantity: int, price: int) -> Dict[str, Any]:
    """주문 파라미터 검증"""
    try:
        errors = []
        
        # 종목코드 검증
        if not validate_stock_code(stock_code):
            errors.append("종목코드는 6자리 숫자여야 합니다")
        
        # 수량 검증
        if quantity <= 0:
            errors.append("수량은 양수여야 합니다")
        elif quantity > 1000000:
            errors.append("수량이 너무 많습니다 (최대 100만주)")
        
        # 가격 검증
        if price <= 0:
            errors.append("가격은 양수여야 합니다")
        elif price > 10000000:
            errors.append("가격이 너무 높습니다 (최대 1천만원)")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    except Exception as e:
        return {
            'valid': False,
            'errors': [f"검증 오류: {str(e)}"]
        }

def export_portfolio_to_json(portfolio: List[Dict], filename: str = None) -> bool:
    """포트폴리오를 JSON으로 내보내기"""
    try:
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"portfolio_export_{timestamp}.json"
        
        # 데이터 정리
        export_data = {
            'export_time': datetime.now().isoformat(),
            'portfolio': []
        }
        
        for item in portfolio:
            export_item = {
                'stock_code': item['stock_code'],
                'stock_name': item.get('stock_name', ''),
                'quantity': item['quantity'],
                'avg_price': item['avg_price'],
                'current_price': item.get('current_price', 0),
                'market_value': item.get('market_value', 0),
                'profit_loss': item.get('profit_loss', 0),
                'profit_rate': item.get('profit_rate', 0.0)
            }
            export_data['portfolio'].append(export_item)
        
        # 파일 저장
        os.makedirs('exports', exist_ok=True)
        filepath = os.path.join('exports', filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return True
        
    except Exception as e:
        logging.error(f"포트폴리오 내보내기 오류: {e}")
        return False

def import_portfolio_from_json(filename: str) -> Optional[List[Dict]]:
    """JSON에서 포트폴리오 가져오기"""
    try:
        if not os.path.exists(filename):
            return None
        
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        portfolio = data.get('portfolio', [])
        
        # 데이터 유효성 검사
        valid_portfolio = []
        for item in portfolio:
            if all(key in item for key in ['stock_code', 'quantity', 'avg_price']):
                valid_portfolio.append(item)
        
        return valid_portfolio
        
    except Exception as e:
        logging.error(f"포트폴리오 가져오기 오류: {e}")
        return None

def backup_database(source_path: str, backup_dir: str = "backups") -> bool:
    """데이터베이스 백업"""
    try:
        if not os.path.exists(source_path):
            return False
        
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"trading_backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        import shutil
        shutil.copy2(source_path, backup_path)
        
        logging.info(f"데이터베이스 백업 완료: {backup_path}")
        return True
        
    except Exception as e:
        logging.error(f"데이터베이스 백업 오류: {e}")
        return False

def cleanup_old_backups(backup_dir: str = "backups", keep_days: int = 30) -> int:
    """오래된 백업 파일 정리"""
    try:
        if not os.path.exists(backup_dir):
            return 0
        
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        deleted_count = 0
        
        for filename in os.listdir(backup_dir):
            if filename.startswith("trading_backup_") and filename.endswith(".db"):
                filepath = os.path.join(backup_dir, filename)
                
                # 파일 생성 시간 확인
                file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                
                if file_time < cutoff_date:
                    os.remove(filepath)
                    deleted_count += 1
                    logging.info(f"오래된 백업 파일 삭제: {filename}")
        
        return deleted_count
        
    except Exception as e:
        logging.error(f"백업 파일 정리 오류: {e}")
        return 0

def check_system_requirements() -> Dict[str, Any]:
    """시스템 요구사항 확인"""
    try:
        requirements = {
            'python_version': sys.version_info >= (3, 7),
            'pyqt5_available': False,
            'pandas_available': False,
            'sqlite3_available': True,
            'disk_space': True
        }
        
        # PyQt5 확인
        try:
            from PyQt5.QtWidgets import QApplication
            requirements['pyqt5_available'] = True
        except ImportError:
            pass
        
        # pandas 확인
        try:
            import pandas
            requirements['pandas_available'] = True
        except ImportError:
            pass
        
        # 디스크 공간 확인 (100MB)
        try:
            import shutil
            free_space = shutil.disk_usage('.').free
            requirements['disk_space'] = free_space > 100 * 1024 * 1024
        except:
            pass
        
        # 전체 상태
        all_good = all(requirements.values())
        
        return {
            'all_requirements_met': all_good,
            'details': requirements,
            'missing_packages': [
                pkg for pkg, available in [
                    ('PyQt5', requirements['pyqt5_available']),
                    ('pandas', requirements['pandas_available'])
                ] if not available
            ]
        }
        
    except Exception as e:
        logging.error(f"시스템 건전성 확인 오류: {e}")
        return {'healthy': False, 'error': str(e)}요구사항 확인 오류: {e}")
        return {'all_requirements_met': False, 'error': str(e)}

def generate_trade_report(transactions: List[Dict], start_date: str = None) -> Dict[str, Any]:
    """거래 리포트 생성"""
    try:
        if not transactions:
            return {'success': False, 'error': '거래 내역이 없습니다'}
        
        # 기간 필터링
        if start_date:
            filtered_transactions = []
            for transaction in transactions:
                trans_date = transaction.get('transaction_time', '')[:10]
                if trans_date >= start_date:
                    filtered_transactions.append(transaction)
            transactions = filtered_transactions
        
        if not transactions:
            return {'success': False, 'error': '해당 기간 거래 내역이 없습니다'}
        
        # 통계 계산
        total_trades = len(transactions)
        buy_trades = [t for t in transactions if t['transaction_type'] == '매수']
        sell_trades = [t for t in transactions if t['transaction_type'] == '매도']
        
        total_buy_amount = sum(t['amount'] for t in buy_trades)
        total_sell_amount = sum(t['amount'] for t in sell_trades)
        total_fees = sum(t.get('fee', 0) for t in transactions)
        
        # 종목별 거래 횟수
        stock_trades = {}
        for transaction in transactions:
            stock_code = transaction['stock_code']
            if stock_code not in stock_trades:
                stock_trades[stock_code] = {'buy': 0, 'sell': 0, 'amount': 0}
            
            if transaction['transaction_type'] == '매수':
                stock_trades[stock_code]['buy'] += 1
            else:
                stock_trades[stock_code]['sell'] += 1
            
            stock_trades[stock_code]['amount'] += transaction['amount']
        
        # 가장 활발한 종목
        most_active_stock = max(stock_trades.items(), 
                               key=lambda x: x[1]['buy'] + x[1]['sell'])[0] if stock_trades else None
        
        return {
            'success': True,
            'period': f"{start_date or '전체'} ~ {datetime.now().strftime('%Y-%m-%d')}",
            'total_trades': total_trades,
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'total_buy_amount': total_buy_amount,
            'total_sell_amount': total_sell_amount,
            'net_amount': total_sell_amount - total_buy_amount,
            'total_fees': total_fees,
            'stock_trades': stock_trades,
            'most_active_stock': most_active_stock,
            'avg_trade_amount': (total_buy_amount + total_sell_amount) // (2 * total_trades) if total_trades > 0 else 0
        }
        
    except Exception as e:
        logging.error(f"거래 리포트 생성 오류: {e}")
        return {'success': False, 'error': str(e)}

def optimize_database(db_path: str) -> bool:
    """데이터베이스 최적화"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # VACUUM으로 데이터베이스 압축
        cursor.execute("VACUUM")
        
        # 통계 정보 업데이트
        cursor.execute("ANALYZE")
        
        conn.close()
        
        logging.info("데이터베이스 최적화 완료")
        return True
        
    except Exception as e:
        logging.error(f"데이터베이스 최적화 오류: {e}")
        return False

def get_file_size(filepath: str) -> str:
    """파일 크기 포맷팅"""
    try:
        if not os.path.exists(filepath):
            return "파일 없음"
        
        size = os.path.getsize(filepath)
        
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"
    except:
        return "크기 알 수 없음"

def create_config_backup() -> bool:
    """설정 백업"""
    try:
        from config import Config
        
        config_data = {
            'backup_time': datetime.now().isoformat(),
            'database_path': Config.DATABASE_PATH,
            'default_account': Config.DEFAULT_ACCOUNT,
            'initial_balance': Config.INITIAL_BALANCE,
            'max_position_size': Config.MAX_POSITION_SIZE,
            'stop_loss_rate': Config.STOP_LOSS_RATE,
            'take_profit_rate': Config.TAKE_PROFIT_RATE,
            'popular_stocks': Config.POPULAR_STOCKS
        }
        
        os.makedirs('backups', exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"backups/config_backup_{timestamp}.json"
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        logging.info(f"설정 백업 완료: {backup_file}")
        return True
        
    except Exception as e:
        logging.error(f"설정 백업 오류: {e}")
        return False

def log_system_info():
    """시스템 정보 로깅"""
    try:
        import platform
        import psutil
        
        info = {
            'python_version': platform.python_version(),
            'platform': platform.platform(),
            'cpu_count': os.cpu_count(),
            'memory_total': f"{psutil.virtual_memory().total / (1024**3):.1f} GB",
            'memory_available': f"{psutil.virtual_memory().available / (1024**3):.1f} GB",
            'disk_free': f"{psutil.disk_usage('.').free / (1024**3):.1f} GB"
        }
        
        logging.info("시스템 정보:")
        for key, value in info.items():
            logging.info(f"  {key}: {value}")
        
        return True
        
    except Exception as e:
        logging.error(f"시스템 정보 로깅 오류: {e}")
        return False

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """안전한 나눗셈"""
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except:
        return default

def round_price(price: float, unit: int = 100) -> int:
    """가격 반올림 (호가 단위)"""
    try:
        return int(round(price / unit) * unit)
    except:
        return int(price)

def get_market_status() -> Dict[str, Any]:
    """시장 상태 정보"""
    try:
        from config import Config
        
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        is_weekend = now.weekday() >= 5
        is_market_time = Config.MARKET_OPEN_TIME <= current_time <= Config.MARKET_CLOSE_TIME
        is_market_open = not is_weekend and is_market_time
        
        # 다음 개장 시간 계산
        if is_weekend:
            # 다음 월요일
            days_until_monday = 7 - now.weekday()
            next_open = now.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=days_until_monday)
        elif current_time > Config.MARKET_CLOSE_TIME:
            # 다음 날
            next_open = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
        else:
            # 오늘
            next_open = now.replace(hour=9, minute=0, second=0, microsecond=0)
        
        return {
            'is_open': is_market_open,
            'is_weekend': is_weekend,
            'current_time': current_time,
            'market_open_time': Config.MARKET_OPEN_TIME,
            'market_close_time': Config.MARKET_CLOSE_TIME,
            'next_open_time': next_open.strftime("%Y-%m-%d %H:%M"),
            'status_text': '개장' if is_market_open else '폐장'
        }
        
    except Exception as e:
        logging.error(f"시장 상태 조회 오류: {e}")
        return {'is_open': False, 'status_text': '확인 불가'}

def calculate_portfolio_metrics(portfolio: List[Dict]) -> Dict[str, Any]:
    """포트폴리오 지표 계산"""
    try:
        if not portfolio:
            return {
                'total_stocks': 0,
                'total_value': 0,
                'total_profit_loss': 0,
                'avg_profit_rate': 0.0,
                'best_stock': None,
                'worst_stock': None
            }
        
        total_value = 0
        total_profit_loss = 0
        total_investment = 0
        
        best_stock = None
        worst_stock = None
        best_rate = float('-inf')
        worst_rate = float('inf')
        
        for item in portfolio:
            market_value = item.get('market_value', 0)
            profit_loss = item.get('profit_loss', 0)
            profit_rate = item.get('profit_rate', 0.0)
            investment = item['quantity'] * item['avg_price']
            
            total_value += market_value
            total_profit_loss += profit_loss
            total_investment += investment
            
            # 최고/최악 종목 찾기
            if profit_rate > best_rate:
                best_rate = profit_rate
                best_stock = {
                    'stock_code': item['stock_code'],
                    'stock_name': item.get('stock_name', ''),
                    'profit_rate': profit_rate
                }
            
            if profit_rate < worst_rate:
                worst_rate = profit_rate
                worst_stock = {
                    'stock_code': item['stock_code'],
                    'stock_name': item.get('stock_name', ''),
                    'profit_rate': profit_rate
                }
        
        avg_profit_rate = (total_profit_loss / total_investment * 100) if total_investment > 0 else 0.0
        
        return {
            'total_stocks': len(portfolio),
            'total_value': total_value,
            'total_profit_loss': total_profit_loss,
            'total_investment': total_investment,
            'avg_profit_rate': avg_profit_rate,
            'best_stock': best_stock,
            'worst_stock': worst_stock
        }
        
    except Exception as e:
        logging.error(f"포트폴리오 지표 계산 오류: {e}")
        return {}

def validate_system_health() -> Dict[str, Any]:
    """시스템 건전성 확인"""
    try:
        health_checks = {
            'database_accessible': False,
            'logs_writable': False,
            'config_valid': False,
            'memory_sufficient': False
        }
        
        # 데이터베이스 접근성
        try:
            from config import Config
            conn = sqlite3.connect(Config.DATABASE_PATH)
            conn.close()
            health_checks['database_accessible'] = True
        except:
            pass
        
        # 로그 쓰기 가능성
        try:
            test_log_file = 'logs/health_check.log'
            os.makedirs('logs', exist_ok=True)
            with open(test_log_file, 'w') as f:
                f.write('health check')
            os.remove(test_log_file)
            health_checks['logs_writable'] = True
        except:
            pass
        
        # 설정 유효성
        try:
            from config import Config
            if hasattr(Config, 'DATABASE_PATH') and hasattr(Config, 'DEFAULT_ACCOUNT'):
                health_checks['config_valid'] = True
        except:
            pass
        
        # 메모리 충분성
        try:
            import psutil
            available_memory = psutil.virtual_memory().available
            health_checks['memory_sufficient'] = available_memory > 500 * 1024 * 1024  # 500MB
        except:
            health_checks['memory_sufficient'] = True  # psutil 없으면 충분하다고 가정
        
        overall_health = all(health_checks.values())
        
        return {
            'healthy': overall_health,
            'checks': health_checks,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logging.error(f"시스템
