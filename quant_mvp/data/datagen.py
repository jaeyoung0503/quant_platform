#!/usr/bin/env python3
"""
샘플 데이터 생성 스크립트
독립적으로 실행하여 샘플 데이터를 생성할 수 있습니다.
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import logging

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data_loader import generate_sample_data

def setup_logging():
    """로깅 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def create_extended_sample_data():
    """확장된 샘플 데이터 생성"""
    logger = logging.getLogger(__name__)
    
    try:
        # 기본 샘플 데이터 생성
        logger.info("기본 샘플 데이터 생성 중...")
        generate_sample_data()
        
        # 추가 데이터 생성
        logger.info("추가 샘플 데이터 생성 중...")
        
        data_dir = Path("data/sample_data")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # 더 많은 종목 추가
        additional_symbols = {
            'V': {'name': 'Visa Inc.', 'sector': 'Financial Services', 'base_price': 220},
            'UNH': {'name': 'UnitedHealth Group', 'sector': 'Healthcare', 'base_price': 480},
            'HD': {'name': 'Home Depot', 'sector': 'Consumer Discretionary', 'base_price': 320},
            'MA': {'name': 'Mastercard Inc.', 'sector': 'Financial Services', 'base_price': 380},
            'DIS': {'name': 'Walt Disney Co.', 'sector': 'Communication Services', 'base_price': 110},
            'ADBE': {'name': 'Adobe Inc.', 'sector': 'Technology', 'base_price': 550},
            'NFLX': {'name': 'Netflix Inc.', 'sector': 'Communication Services', 'base_price': 420},
            'CRM': {'name': 'Salesforce Inc.', 'sector': 'Technology', 'base_price': 220},
            'PYPL': {'name': 'PayPal Holdings', 'sector': 'Financial Services', 'base_price': 80},
            'INTC': {'name': 'Intel Corp.', 'sector': 'Technology', 'base_price': 45}
        }
        
        # 날짜 범위 설정
        start_date = datetime(2020, 1, 1)
        end_date = datetime(2024, 12, 31)
        business_days = pd.bdate_range(start=start_date, end=end_date)
        
        # 기존 데이터 로드
        existing_price_data = pd.read_csv(data_dir / "market_prices.csv")
        existing_financial_data = pd.read_csv(data_dir / "financials.csv")
        
        # 추가 가격 데이터 생성
        new_price_data = []
        np.random.seed(123)  # 재현 가능한 결과
        
        for symbol, info in additional_symbols.items():
            prices = generate_price_series(info['base_price'], len(business_days))
            volumes = generate_volume_series(len(business_days))
            
            for i, date in enumerate(business_days):
                new_price_data.append({
                    'date': date,
                    'symbol': symbol,
                    'open': prices[i] * (0.995 + np.random.random() * 0.01),
                    'high': prices[i] * (1.0 + np.random.random() * 0.02),
                    'low': prices[i] * (0.98 + np.random.random() * 0.01),
                    'close': prices[i],
                    'volume': volumes[i],
                    'sector': info['sector']
                })
        
        # 기존 데이터와 병합
        if new_price_data:
            new_price_df = pd.DataFrame(new_price_data)
            combined_price_df = pd.concat([existing_price_data, new_price_df], ignore_index=True)
            combined_price_df.to_csv(data_dir / "market_prices.csv", index=False)
            logger.info(f"추가된 가격 데이터: {len(additional_symbols)}개 종목")
        
        # 추가 재무 데이터 생성
        new_financial_data = []
        quarters = pd.date_range(start=start_date, end=end_date, freq='Q')
        
        for symbol, info in additional_symbols.items():
            base_market_cap = np.random.uniform(100_000, 1_500_000)  # 백만 달러
            base_revenue = np.random.uniform(20_000, 300_000)  # 백만 달러
            
            for quarter in quarters:
                growth_factor = 1 + np.random.normal(0.02, 0.08)
                market_cap = base_market_cap * growth_factor
                revenue = base_revenue * growth_factor
                
                new_financial_data.append({
                    'symbol': symbol,
                    'date': quarter,
                    'market_cap': market_cap * 1_000_000,
                    'pe_ratio': np.random.uniform(10, 40),
                    'pb_ratio': np.random.uniform(1, 8),
                    'roe': np.random.uniform(8, 35),
                    'roa': np.random.uniform(3, 25),
                    'debt_to_equity': np.random.uniform(0.1, 1.8),
                    'dividend_yield': np.random.uniform(0, 4) if info['sector'] != 'Technology' else np.random.uniform(0, 1.5),
                    'revenue_growth': np.random.uniform(-3, 30),
                    'earnings_growth': np.random.uniform(-8, 40),
                    'sector': info['sector']
                })
                
                base_market_cap = market_cap
                base_revenue = revenue
        
        # 재무 데이터 병합
        if new_financial_data:
            new_financial_df = pd.DataFrame(new_financial_data)
            combined_financial_df = pd.concat([existing_financial_data, new_financial_df], ignore_index=True)
            combined_financial_df.to_csv(data_dir / "financials.csv", index=False)
            logger.info(f"추가된 재무 데이터: {len(additional_symbols)}개 종목")
        
        # 데이터 품질 리포트 생성
        generate_data_quality_report(data_dir)
        
        logger.info("확장 샘플 데이터 생성 완료!")
        
    except Exception as e:
        logger.error(f"샘플 데이터 생성 중 오류: {e}")
        raise

def generate_price_series(base_price: float, length: int) -> np.ndarray:
    """주가 시계열 생성 (기하 브라운 운동)"""
    returns = np.random.normal(0.0005, 0.018, length)  # 일일 수익률
    prices = [base_price]
    
    for i in range(1, length):
        new_price = prices[-1] * (1 + returns[i])
        prices.append(max(new_price, 1.0))  # 최소 1달러
    
    return np.array(prices)

def generate_volume_series(length: int) -> np.ndarray:
    """거래량 시계열 생성"""
    base_volume = np.random.uniform(2_000_000, 80_000_000)
    volumes = []
    
    for i in range(length):
        volume = base_volume * np.random.lognormal(0, 0.4)
        volumes.append(int(volume))
    
    return np.array(volumes)

def generate_data_quality_report(data_dir: Path):
    """데이터 품질 리포트 생성"""
    logger = logging.getLogger(__name__)
    
    try:
        # 데이터 로드
        price_data = pd.read_csv(data_dir / "market_prices.csv")
        financial_data = pd.read_csv(data_dir / "financials.csv")
        market_data = pd.read_csv(data_dir / "market_data.csv")
        
        # 리포트 작성
        report_lines = [
            "# 샘플 데이터 품질 리포트",
            f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 가격 데이터",
            f"- 총 레코드 수: {len(price_data):,}",
            f"- 종목 수: {price_data['symbol'].nunique()}",
            f"- 기간: {price_data['date'].min()} ~ {price_data['date'].max()}",
            f"- 섹터 수: {price_data['sector'].nunique()}",
            "",
            "### 종목별 통계",
        ]
        
        # 종목별 통계
        for symbol in sorted(price_data['symbol'].unique()):
            symbol_data = price_data[price_data['symbol'] == symbol]
            start_price = symbol_data.iloc[0]['close']
            end_price = symbol_data.iloc[-1]['close']
            total_return = (end_price / start_price - 1) * 100
            
            report_lines.append(f"- {symbol}: {len(symbol_data)}일, 수익률 {total_return:+.1f}%")
        
        report_lines.extend([
            "",
            "## 재무 데이터", 
            f"- 총 레코드 수: {len(financial_data):,}",
            f"- 종목 수: {financial_data['symbol'].nunique()}",
            f"- 평균 PER: {financial_data['pe_ratio'].mean():.1f}",
            f"- 평균 PBR: {financial_data['pb_ratio'].mean():.1f}",
            f"- 평균 ROE: {financial_data['roe'].mean():.1f}%",
            "",
            "## 시장 데이터",
            f"- 총 레코드 수: {len(market_data):,}",
            f"- 기간: {market_data['date'].min()} ~ {market_data['date'].max()}",
        ])
        
        # 리포트 파일 저장
        report_path = data_dir / "data_quality_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        logger.info(f"데이터 품질 리포트 생성: {report_path}")
        
    except Exception as e:
        logger.error(f"데이터 품질 리포트 생성 중 오류: {e}")

def clean_existing_data():
    """기존 데이터 정리"""
    logger = logging.getLogger(__name__)
    
    try:
        data_dir = Path("data/sample_data")
        
        if not data_dir.exists():
            logger.info("data/sample_data 디렉토리가 존재하지 않습니다.")
            return
        
        csv_files = list(data_dir.glob("*.csv"))
        
        if not csv_files:
            logger.info("삭제할 CSV 파일이 없습니다.")
            return
        
        for file_path in csv_files:
            file_path.unlink()
            logger.info(f"삭제됨: {file_path}")
        
        logger.info("기존 샘플 데이터 정리 완료")
        
    except Exception as e:
        logger.error(f"데이터 정리 중 오류: {e}")

def main():
    """메인 함수"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    import argparse
    parser = argparse.ArgumentParser(description='샘플 데이터 생성 도구')
    parser.add_argument('--clean', action='store_true', 
                       help='기존 데이터를 삭제하고 새로 생성')
    parser.add_argument('--extended', action='store_true',
                       help='확장 데이터 세트 생성 (더 많은 종목)')
    
    args = parser.parse_args()
    
    try:
        logger.info("샘플 데이터 생성 시작")
        
        if args.clean:
            logger.info("기존 데이터 정리 중...")
            clean_existing_data()
        
        if args.extended:
            logger.info("확장 샘플 데이터 생성...")
            create_extended_sample_data()
        else:
            logger.info("기본 샘플 데이터 생성...")
            generate_sample_data()
            
            # 품질 리포트 생성
            data_dir = Path("data/sample_data")
            if data_dir.exists():
                generate_data_quality_report(data_dir)
        
        logger.info("샘플 데이터 생성 완료!")
        
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단됨")
    except Exception as e:
        logger.error(f"샘플 데이터 생성 실패: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)