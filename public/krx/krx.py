from pykrx import stock
import pandas as pd
import time
from datetime import datetime, timedelta
from multiprocessing import Pool, cpu_count
import os
import logging
from typing import Optional, List, Dict
import sys

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stock_data_collection.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class StockDataCollector:
    def __init__(self, base_filename: str = "korea_stock_data", max_retries: int = 3, delay_between_requests: float = 0.1):
        self.base_filename = base_filename
        self.today = datetime.now().strftime("%Y%m%d")
        self.current_year = int(self.today[:4])
        self.max_retries = max_retries
        self.delay = delay_between_requests
        
    def get_filename(self, year: int) -> str:
        """연도별 파일명 생성"""
        return f"{self.base_filename}_{year}.csv"
        
    def get_stock_codes_by_market(self) -> Dict[str, List[str]]:
        """시장별 주식 코드 목록 가져오기"""
        try:
            kospi_codes = stock.get_market_ticker_list(self.today, market="KOSPI")
            kosdaq_codes = stock.get_market_ticker_list(self.today, market="KOSDAQ")
            
            logger.info(f"코스피: {len(kospi_codes)}개, 코스닥: {len(kosdaq_codes)}개 종목 조회 완료")
            
            return {
                "KOSPI": kospi_codes,
                "KOSDAQ": kosdaq_codes
            }
        except Exception as e:
            logger.error(f"종목 코드 조회 실패: {e}")
            return {"KOSPI": [], "KOSDAQ": []}

    def get_market_type(self, ticker: str, market_codes: Dict[str, List[str]]) -> str:
        """종목코드로 시장 구분 판별"""
        if ticker in market_codes["KOSPI"]:
            return "KOSPI"
        elif ticker in market_codes["KOSDAQ"]:
            return "KOSDAQ"
        else:
            return "UNKNOWN"

    def fetch_stock_data(self, ticker: str, start_date: str, end_date: str, market_type: str) -> Optional[pd.DataFrame]:
        """종목별 데이터 수집 (재시도 로직 포함)"""
        for attempt in range(self.max_retries):
            try:
                time.sleep(self.delay)  # API 호출 제한 방지
                
                name = stock.get_market_ticker_name(ticker)
                df = stock.get_market_ohlcv(start_date, end_date, ticker)
                
                if df.empty:
                    logger.warning(f"{ticker}({name}): 데이터 없음")
                    return None
                
                # 데이터 전처리
                df = df.reset_index()
                df = df.rename(columns={
                    '날짜': 'date',
                    '시가': 'open', 
                    '고가': 'high',
                    '저가': 'low',
                    '종가': 'close',
                    '거래량': 'volume'
                })
                df['ticker'] = ticker
                df['name'] = name
                df['market'] = market_type  # 시장 구분 추가
                df['date'] = pd.to_datetime(df['date'])
                df['year'] = df['date'].dt.year  # 연도 컬럼 추가
                
                # 컬럼 순서 재정렬
                df = df[['date', 'year', 'ticker', 'name', 'market', 'open', 'high', 'low', 'close', 'volume']]
                
                # 데이터 검증
                if self._validate_data(df):
                    logger.info(f"{ticker}({name}) [{market_type}]: {len(df)}개 데이터 수집 완료")
                    return df
                else:
                    logger.warning(f"{ticker}({name}): 데이터 검증 실패")
                    return None
                    
            except Exception as e:
                logger.warning(f"{ticker} 시도 {attempt + 1}/{self.max_retries} 실패: {e}")
                if attempt == self.max_retries - 1:
                    logger.error(f"{ticker}: 모든 재시도 실패")
                time.sleep(1)  # 재시도 전 대기
                
        return None

    def _validate_data(self, df: pd.DataFrame) -> bool:
        """데이터 유효성 검증"""
        if df.empty:
            return False
        
        # 필수 컬럼 체크
        required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_columns):
            return False
        
        # 가격 데이터 유효성 체크
        price_columns = ['open', 'high', 'low', 'close']
        for col in price_columns:
            if (df[col] <= 0).any():
                return False
        
        # 고가 >= 저가 체크
        if (df['high'] < df['low']).any():
            return False
            
        return True

    def get_user_date_input(self) -> tuple:
        """사용자로부터 날짜 입력 받기"""
        while True:
            try:
                start_year = int(input("시작 연도를 입력하세요 (예: 2015): "))
                end_year = int(input("종료 연도를 입력하세요 (예: 2025): "))
                
                if not (1980 <= start_year <= self.current_year):
                    print(f"시작 연도는 1980~{self.current_year} 범위에서 입력하세요.")
                    continue
                    
                if not (start_year <= end_year <= self.current_year):
                    print(f"종료 연도는 시작 연도~{self.current_year} 범위에서 입력하세요.")
                    continue
                    
                break
            except ValueError:
                print("올바른 숫자를 입력하세요.")
        
        return start_year, end_year

    def collect_data_for_year(self, year: int, market_codes: Dict[str, List[str]]) -> pd.DataFrame:
        """특정 연도 데이터 수집"""
        start_date = f"{year}0101"
        end_date = f"{year}1231"
        
        logger.info(f"{year}년 데이터 수집 시작")
        
        # 모든 종목 코드와 시장 정보 준비
        all_tickers = []
        for market, codes in market_codes.items():
            for ticker in codes:
                all_tickers.append((ticker, start_date, end_date, market))
        
        # 병렬 처리
        num_processes = min(cpu_count() // 2, 8)
        logger.info(f"{num_processes}개 프로세스로 {len(all_tickers)}개 종목 처리")
        
        year_data = pd.DataFrame()
        successful_count = 0
        
        try:
            with Pool(processes=num_processes) as pool:
                results = pool.starmap(self.fetch_stock_data, all_tickers)
            
            # 결과 병합
            for df in results:
                if df is not None:
                    year_data = pd.concat([year_data, df], ignore_index=True)
                    successful_count += 1
            
            logger.info(f"{year}년: {successful_count}/{len(all_tickers)}개 종목 수집 완료")
            
        except Exception as e:
            logger.error(f"{year}년 데이터 수집 중 오류: {e}")
        
        return year_data

    def initial_fetch(self):
        """초기 데이터 수집 (연도별 파일 생성)"""
        logger.info("초기 데이터 수집 시작")
        
        start_year, end_year = self.get_user_date_input()
        market_codes = self.get_stock_codes_by_market()
        
        if not any(market_codes.values()):
            logger.error("종목 코드를 가져올 수 없습니다.")
            return
        
        total_start_time = time.time()
        
        for year in range(start_year, end_year + 1):
            year_start_time = time.time()
            
            # 연도별 데이터 수집
            year_data = self.collect_data_for_year(year, market_codes)
            
            if not year_data.empty:
                # 연도별 파일로 저장
                filename = self.get_filename(year)
                year_data = year_data.sort_values(['market', 'ticker', 'date']).reset_index(drop=True)
                self._save_data(year_data, filename)
                
                year_elapsed = (time.time() - year_start_time) / 60
                logger.info(f"{year}년 데이터 저장 완료: {len(year_data)}행, 소요시간: {year_elapsed:.2f}분")
            else:
                logger.warning(f"{year}년: 수집된 데이터가 없습니다.")
        
        total_elapsed = (time.time() - total_start_time) / 60
        logger.info(f"전체 초기 데이터 수집 완료! 총 소요시간: {total_elapsed:.2f}분")

    def update_stock_data_for_year(self, year: int, ticker: str, market_type: str) -> Optional[pd.DataFrame]:
        """연도별 파일에서 개별 종목 업데이트"""
        try:
            filename = self.get_filename(year)
            
            if os.path.exists(filename):
                existing_data = pd.read_csv(filename, parse_dates=['date'])
                ticker_data = existing_data[existing_data['ticker'] == ticker]
                
                if not ticker_data.empty:
                    last_date = ticker_data['date'].max()
                    start_date = (last_date + timedelta(days=1)).strftime("%Y%m%d")
                    
                    # 해당 연도 범위 내에서만 업데이트
                    year_end = f"{year}1231"
                    if start_date > year_end or start_date > self.today:
                        return None  # 업데이트 불필요
                    
                    end_date = min(year_end, self.today)
                else:
                    # 신규 종목: 해당 연도 전체
                    start_date = f"{year}0101"
                    end_date = min(f"{year}1231", self.today)
            else:
                # 파일 없음: 해당 연도 전체
                start_date = f"{year}0101"
                end_date = min(f"{year}1231", self.today)
            
            return self.fetch_stock_data(ticker, start_date, end_date, market_type)
            
        except Exception as e:
            logger.error(f"{year}년 {ticker} 업데이트 실패: {e}")
            return None

    def update_data(self):
        """데이터 업데이트 (연도별 파일)"""
        logger.info("데이터 업데이트 시작")
        
        # 업데이트할 연도 입력
        while True:
            try:
                update_year = int(input(f"업데이트할 연도를 입력하세요 (1980-{self.current_year}): "))
                if 1980 <= update_year <= self.current_year:
                    break
                print(f"1980~{self.current_year} 범위에서 입력하세요.")
            except ValueError:
                print("올바른 숫자를 입력하세요.")
        
        market_codes = self.get_stock_codes_by_market()
        if not any(market_codes.values()):
            logger.error("종목 코드를 가져올 수 없습니다.")
            return
        
        filename = self.get_filename(update_year)
        start_time = time.time()
        updated_count = 0
        
        try:
            # 기존 데이터 로드 (없으면 빈 DataFrame)
            if os.path.exists(filename):
                all_data = pd.read_csv(filename, parse_dates=['date'])
            else:
                all_data = pd.DataFrame()
            
            # 모든 종목에 대해 업데이트
            all_tickers = []
            for market, codes in market_codes.items():
                for ticker in codes:
                    all_tickers.append((update_year, ticker, market))
            
            # 병렬 처리로 업데이트
            num_processes = min(cpu_count() // 2, 8)
            with Pool(processes=num_processes) as pool:
                results = pool.starmap(self.update_stock_data_for_year, all_tickers)
            
            # 새 데이터 병합
            for df_new in results:
                if df_new is not None:
                    ticker = df_new['ticker'].iloc[0]
                    # 기존 종목 데이터 제거 후 새 데이터 추가
                    all_data = all_data[all_data['ticker'] != ticker]
                    all_data = pd.concat([all_data, df_new], ignore_index=True)
                    updated_count += 1
            
            # 정렬 및 저장
            if not all_data.empty:
                all_data = all_data.sort_values(['market', 'ticker', 'date']).reset_index(drop=True)
                self._save_data(all_data, filename)
            
            elapsed_time = (time.time() - start_time) / 60
            logger.info(f"{update_year}년 데이터 업데이트 완료! 업데이트: {updated_count}개, "
                      f"소요시간: {elapsed_time:.2f}분")
                      
        except Exception as e:
            logger.error(f"데이터 업데이트 중 오류: {e}")

    def _save_data(self, data: pd.DataFrame, filename: str):
        """데이터 저장 (백업 포함)"""
        try:
            # 기존 파일 백업
            if os.path.exists(filename):
                backup_file = f"{filename}.backup"
                os.rename(filename, backup_file)
                logger.info(f"기존 파일을 {backup_file}로 백업")
            
            # 새 데이터 저장
            data.to_csv(filename, encoding="utf-8-sig", index=False)
            logger.info(f"데이터 저장 완료: {filename}, {len(data)}행")
            
        except Exception as e:
            logger.error(f"데이터 저장 실패: {e}")
            # 백업 파일 복원
            backup_file = f"{filename}.backup"
            if os.path.exists(backup_file):
                os.rename(backup_file, filename)
                logger.info("백업 파일 복원 완료")

    def get_data_summary(self):
        """데이터 요약 정보 (모든 연도별 파일)"""
        # 존재하는 연도별 파일 찾기
        year_files = []
        for year in range(1980, self.current_year + 1):
            filename = self.get_filename(year)
            if os.path.exists(filename):
                year_files.append((year, filename))
        
        if not year_files:
            print("데이터 파일이 없습니다.")
            return
        
        print(f"\n=== 데이터 요약 ===")
        print(f"존재하는 연도별 파일: {len(year_files)}개")
        
        total_rows = 0
        total_size = 0
        all_tickers = set()
        
        for year, filename in year_files:
            try:
                data = pd.read_csv(filename, parse_dates=['date'])
                file_size = os.path.getsize(filename) / 1024 / 1024  # MB
                
                total_rows += len(data)
                total_size += file_size
                all_tickers.update(data['ticker'].unique())
                
                # 시장별 통계
                market_stats = data['market'].value_counts()
                kospi_count = market_stats.get('KOSPI', 0)
                kosdaq_count = market_stats.get('KOSDAQ', 0)
                
                print(f"\n{year}년 ({filename}):")
                print(f"  - 총 데이터: {len(data):,}행")
                print(f"  - 종목 수: {data['ticker'].nunique()}개")
                print(f"  - 코스피: {kospi_count:,}행, 코스닥: {kosdaq_count:,}행")
                print(f"  - 기간: {data['date'].min().date()} ~ {data['date'].max().date()}")
                print(f"  - 파일 크기: {file_size:.2f}MB")
                
            except Exception as e:
                logger.error(f"{filename} 요약 생성 실패: {e}")
        
        print(f"\n=== 전체 통계 ===")
        print(f"총 데이터 수: {total_rows:,}행")
        print(f"전체 종목 수: {len(all_tickers)}개")
        print(f"총 파일 크기: {total_size:.2f}MB")

    def merge_years_data(self):
        """연도별 파일을 하나로 병합"""
        print("\n연도별 파일 병합 기능")
        
        # 존재하는 연도별 파일 찾기
        year_files = []
        for year in range(1980, self.current_year + 1):
            filename = self.get_filename(year)
            if os.path.exists(filename):
                year_files.append((year, filename))
        
        if not year_files:
            print("병합할 데이터 파일이 없습니다.")
            return
        
        print(f"병합 가능한 파일: {len(year_files)}개")
        for year, filename in year_files:
            print(f"  - {filename}")
        
        # 병합할 연도 범위 입력
        while True:
            try:
                start_year = int(input("병합 시작 연도: "))
                end_year = int(input("병합 종료 연도: "))
                
                available_years = [year for year, _ in year_files]
                if start_year in available_years and end_year in available_years and start_year <= end_year:
                    break
                print("유효한 연도 범위를 입력하세요.")
            except ValueError:
                print("올바른 숫자를 입력하세요.")
        
        # 병합 실행
        merged_filename = f"{self.base_filename}_{start_year}_{end_year}_merged.csv"
        merged_data = pd.DataFrame()
        
        try:
            for year in range(start_year, end_year + 1):
                filename = self.get_filename(year)
                if os.path.exists(filename):
                    year_data = pd.read_csv(filename, parse_dates=['date'])
                    merged_data = pd.concat([merged_data, year_data], ignore_index=True)
                    print(f"{year}년 데이터 병합 완료: {len(year_data)}행")
            
            if not merged_data.empty:
                merged_data = merged_data.sort_values(['market', 'ticker', 'date']).reset_index(drop=True)
                merged_data.to_csv(merged_filename, encoding="utf-8-sig", index=False)
                print(f"\n병합 완료: {merged_filename}")
                print(f"총 {len(merged_data):,}행 저장")
            else:
                print("병합할 데이터가 없습니다.")
                
        except Exception as e:
            logger.error(f"파일 병합 중 오류: {e}")

def main():
    collector = StockDataCollector()
    
    while True:
        print("\n=== 한국 주식 데이터 수집기 (연도별 파일 버전) ===")
        print("1. 초기 데이터 수집 (연도별 파일 생성)")
        print("2. 데이터 업데이트 (특정 연도)") 
        print("3. 데이터 요약 보기")
        print("4. 연도별 파일 병합")
        print("5. 종료")
        
        choice = input("선택하세요 (1-5): ").strip()
        
        if choice == "1":
            collector.initial_fetch()
        elif choice == "2":
            collector.update_data()
        elif choice == "3":
            collector.get_data_summary()
        elif choice == "4":
            collector.merge_years_data()
        elif choice == "5":
            print("프로그램을 종료합니다.")
            break
        else:
            print("올바른 선택지를 입력하세요.")

if __name__ == "__main__":
    main()