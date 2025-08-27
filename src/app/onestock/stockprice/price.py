# 종목별 백테스트 엔진
#file: stockprice/price.py

import asyncio
import pandas as pd
from datetime import datetime, timedelta
import redis
from typing import Dict, List, Optional
import logging
from dataclasses import dataclass
import time
import json
import yfinance as yf
import FinanceDataReader as fdr
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('quant_system.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

Base = declarative_base()

@dataclass
class StockPrice:
    """주가 데이터 구조"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    adj_close: Optional[float] = None
    currency: str = 'KRW'

class StockPriceDB(Base):
    """SQLAlchemy ORM 모델"""
    __tablename__ = 'stock_prices'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Integer)
    adj_close = Column(Float)
    currency = Column(String(3))

class CompanyListManager:
    """종목코드 관리 전용 클래스"""
    
    def __init__(self, cache_manager=None, force_update: bool = False):
        self.cache_manager = cache_manager
        self.cache_key = "company_list:krx"
        self.cache_timeout = 86400  # 24시간
        self.companies_df = None
        self.symbols = []
        self.csv_file = "company_list.csv"
    
    async def load_companies_from_cache_or_download(self, force_update: bool = False):
        """캐시 또는 CSV에서 종목코드 로드, 없으면 다운로드"""
        try:
            if force_update:
                await self.download_and_cache_companies()
                return

            if self.cache_manager and self.cache_manager.redis_client:
                cached_data = await self.get_cached_companies()
                if cached_data is not None:
                    self.companies_df = cached_data
                    self._set_symbols_from_df()
                    logger.info(f"✓ Loaded {len(self.symbols)} companies from Redis cache")
                    return
            
            if os.path.exists(self.csv_file):
                logger.info("Loading companies from CSV file...")
                self.companies_df = pd.read_csv(self.csv_file, dtype={'Code': str})
                self._set_symbols_from_df()
                logger.info(f"✓ Loaded {len(self.symbols)} companies from CSV")
                if self.cache_manager:
                    await self.cache_companies(self.companies_df)
            else:
                logger.info("No cached data found, downloading fresh company list...")
                await self.download_and_cache_companies()
                
        except Exception as e:
            logger.error(f"Error loading company list: {e}")
            self.symbols = []
            self.companies_df = pd.DataFrame()

    def _set_symbols_from_df(self):
        """DataFrame에서 종목코드 리스트 설정"""
        if self.companies_df is None or 'Code' not in self.companies_df.columns:
            logger.error("DataFrame is not valid or 'Code' column is missing.")
            self.symbols = []
            return
        self.companies_df['Code'] = self.companies_df['Code'].astype(str).str.zfill(6)
        self.symbols = self.companies_df['Code'].tolist()

    async def download_and_cache_companies(self):
        """종목코드 다운로드, CSV 저장 및 캐싱"""
        try:
            logger.info("📡 Downloading KRX company list...")
            krx_list = fdr.StockListing('KRX')
            
            required_cols = ['Code', 'Name', 'Market']
            if not all(col in krx_list.columns for col in required_cols):
                 # 'Symbol' 컬럼을 'Code'로 변경
                if 'Symbol' in krx_list.columns and 'Code' not in krx_list.columns:
                    krx_list.rename(columns={'Symbol': 'Code'}, inplace=True)
                else:
                    raise ValueError(f"Required columns {required_cols} not found in KRX data.")
            
            cleaned_list = krx_list[required_cols + ['Sector']].copy()
            cleaned_list = cleaned_list.dropna(subset=['Code'])
            
            self.companies_df = cleaned_list
            self._set_symbols_from_df()
            
            cleaned_list.to_csv(self.csv_file, index=False, encoding='utf-8-sig')
            logger.info(f"💾 Company list saved to CSV: {self.csv_file}")
            
            if self.cache_manager:
                await self.cache_companies(cleaned_list)
            
            logger.info(f"✅ Downloaded and cached {len(self.symbols)} companies")
            
        except Exception as e:
            logger.error(f"❌ Error downloading company list: {e}")
            self.symbols = []
            self.companies_df = pd.DataFrame()

    async def get_cached_companies(self) -> Optional[pd.DataFrame]:
        """캐시에서 종목코드 조회"""
        if not self.cache_manager or not self.cache_manager.redis_client: return None
        try:
            cached = self.cache_manager.redis_client.get(self.cache_key)
            if cached:
                return pd.DataFrame(json.loads(cached))
            return None
        except Exception as e:
            logger.warning(f"Cache get error for companies: {e}")
            return None

    async def cache_companies(self, df: pd.DataFrame):
        """종목코드를 캐시에 저장"""
        if not self.cache_manager or not self.cache_manager.redis_client: return
        try:
            data = df.to_dict('records')
            self.cache_manager.redis_client.setex(
                self.cache_key, self.cache_timeout, json.dumps(data)
            )
            logger.info(f"📝 Company list cached for {self.cache_timeout/3600:.1f} hours")
        except Exception as e:
            logger.warning(f"Cache set error for companies: {e}")

    def get_test_symbols(self, count: int = 10) -> List[str]:
        """테스트용 종목 반환 (시가총액 상위)"""
        if self.companies_df is None or self.companies_df.empty:
            logger.warning("No company data available, returning default symbols.")
            return ['005930', '000660', '035420', '005935', '005490', 
                   '051910', '006400', '035720', '105560', '055550'][:count]
        
        kospi_companies = self.companies_df[self.companies_df['Market'] == 'KOSPI']
        selected = kospi_companies.head(count) if len(kospi_companies) >= count else self.companies_df.head(count)
        
        test_symbols = selected['Code'].tolist()
        logger.info(f"🔍 Selected {len(test_symbols)} test symbols: {test_symbols}")
        return test_symbols

class DataSourceManager:
    """데이터 소스 관리"""
    
    def _validate_stock_data(self, symbol: str, row: pd.Series) -> bool:
        """주가 데이터 유효성 검사"""
        prices = [row['Open'], row['High'], row['Low'], row['Close']]
        if any(p < 0 for p in prices) or row['Volume'] < 0:
            logger.warning(f"Negative value detected for {symbol}: {row.to_dict()}")
            return False
        if row['High'] < row['Low']:
            logger.warning(f"Invalid high-low range for {symbol}: High={row['High']}, Low={row['Low']}")
            return False
        return True

    async def _get_yfinance_data(self, symbol: str, start_date: str, end_date: str) -> List[StockPrice]:
        """Yahoo Finance 데이터 수집"""
        try:
            symbol_yf = f"{symbol}.KS"
            ticker = yf.Ticker(symbol_yf)
            hist = ticker.history(start=start_date, end=end_date)
            
            if hist.empty: return []
            
            valid_data = []
            for idx, row in hist.iterrows():
                if self._validate_stock_data(symbol, row):
                    valid_data.append(StockPrice(
                        symbol=symbol, timestamp=idx.to_pydatetime(),
                        open=float(row['Open']), high=float(row['High']),
                        low=float(row['Low']), close=float(row['Close']),
                        volume=int(row['Volume']), adj_close=float(row.get('Adj Close', row['Close']))
                    ))
            return valid_data
        except Exception as e:
            logger.error(f"Error fetching yfinance data for {symbol}: {e}")
            return []

    async def _get_fdr_data(self, symbol: str, start_date: str, end_date: str) -> List[StockPrice]:
        """FinanceDataReader 데이터 수집"""
        try:
            df = fdr.DataReader(symbol, start_date, end_date)
            if df.empty: return []
            
            valid_data = []
            for idx, row in df.iterrows():
                if self._validate_stock_data(symbol, row):
                    valid_data.append(StockPrice(
                        symbol=symbol, timestamp=idx.to_pydatetime(),
                        open=float(row['Open']), high=float(row['High']),
                        low=float(row['Low']), close=float(row['Close']),
                        volume=int(row['Volume']), adj_close=float(row.get('Adj Close', row['Close']))
                    ))
            return valid_data
        except Exception as e:
            logger.error(f"Error fetching FDR data for {symbol}: {e}")
            return []

class CacheManager:
    """Redis 캐시 관리"""
    def __init__(self, host='localhost', port=6379, db=0):
        try:
            self.redis_client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            self.redis_client.ping()
            self.cache_timeout = 300  # 5분
            logger.info("✅ Redis cache connected")
        except Exception as e:
            logger.warning(f"⚠️ Redis not available: {e}")
            self.redis_client = None

    async def get_cached_data(self, key: str) -> Optional[List[StockPrice]]:
        if not self.redis_client: return None
        try:
            cached = self.redis_client.get(key)
            if cached:
                data = json.loads(cached)
                return [StockPrice(**item) for item in data]
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    async def cache_data(self, key: str, data: List[StockPrice]):
        if not self.redis_client: return
        try:
            serialized = [item.__dict__ for item in data]
            for item in serialized:
                item['timestamp'] = item['timestamp'].isoformat()
            self.redis_client.setex(key, self.cache_timeout, json.dumps(serialized))
        except Exception as e:
            logger.error(f"Cache set error: {e}")

class DatabaseManager:
    """데이터베이스 관리"""
    def __init__(self, db_url: str = "sqlite:///stock_data.db"):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    async def save_stock_data(self, data: List[StockPrice]):
        session = self.Session()
        try:
            for item in data:
                db_item = StockPriceDB(**item.__dict__)
                session.merge(db_item) # 중복 시 업데이트, 없으면 삽입
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database save error: {e}")
        finally:
            session.close()

class QuantDataManager:
    """통합 데이터 관리 시스템"""
    def __init__(self, db_url: str = "sqlite:///quant_data.db", force_update_companies: bool = False):
        self.data_source = DataSourceManager()
        self.cache_manager = CacheManager()
        self.db_manager = DatabaseManager(db_url)
        self.company_manager = CompanyListManager(self.cache_manager, force_update_companies)
        self.csv_output_dir = "stock_data_csv"
        os.makedirs(self.csv_output_dir, exist_ok=True)
    
    async def initialize_companies(self, force_update: bool = False):
        await self.company_manager.load_companies_from_cache_or_download(force_update)

    def get_test_symbols(self, count: int = 10) -> List[str]:
        return self.company_manager.get_test_symbols(count)
    
    async def get_stock_data(self, symbol: str, start_date: str, end_date: str, use_cache: bool = True) -> List[StockPrice]:
        cache_key = f"stock_data:{symbol}:{start_date}:{end_date}"
        if use_cache and self.cache_manager.redis_client:
            cached_data = await self.cache_manager.get_cached_data(cache_key)
            if cached_data:
                logger.info(f"📋 Cache hit for {symbol}")
                return cached_data
        
        logger.info(f"📡 Fetching data for {symbol} from API...")
        data = await self.data_source._get_yfinance_data(symbol, start_date, end_date)
        
        if not data: # yfinance 실패 시 FDR 시도
            logger.warning(f"yfinance failed for {symbol}. Trying FinanceDataReader...")
            await asyncio.sleep(1) # 짧은 딜레이
            data = await self.data_source._get_fdr_data(symbol, start_date, end_date)

        if data:
            if self.cache_manager.redis_client:
                await self.cache_manager.cache_data(cache_key, data)
            await self.db_manager.save_stock_data(data)
            logger.info(f"✅ Data fetched for {symbol}: {len(data)} records")
        return data
    
    async def collect_test_data(self, test_symbols: List[str], start_date: str, end_date: str) -> Dict[str, List[StockPrice]]:
        logger.info(f"🔄 Starting data collection for {len(test_symbols)} symbols...")
        results = {}
        for i, symbol in enumerate(test_symbols, 1):
            try:
                logger.info(f"[{i}/{len(test_symbols)}] Processing {symbol}...")
                data = await self.get_stock_data(symbol, start_date, end_date)
                if data:
                    results[symbol] = data
                else:
                    logger.warning(f"  ❌ No data for {symbol}")
                await asyncio.sleep(1) # API 요청 간 딜레이
            except Exception as e:
                logger.error(f"  ❌ Error processing {symbol}: {e}")
        logger.info(f"🏁 Test data collection completed: {sum(len(v) for v in results.values())} total records")
        return results

    async def save_data_to_csv(self, data_dict: Dict[str, List[StockPrice]], filename_prefix: str):
        if not data_dict:
            logger.warning("No data to save.")
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"{self.csv_output_dir}/{filename_prefix}_{timestamp}.csv"
        
        all_records = []
        for symbol, stock_data in data_dict.items():
            company_name = self._get_company_name(symbol)
            for price in stock_data:
                record = price.__dict__
                record['company_name'] = company_name
                record['timestamp'] = price.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                all_records.append(record)
        
        if not all_records:
            logger.warning("No valid records to save in CSV.")
            return None

        df_all = pd.DataFrame(all_records)
        df_all.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        logger.info(f"💾 All data saved to CSV: {csv_filename}")
        return csv_filename

    def _get_company_name(self, symbol: str) -> str:
        """종목 코드로 회사 이름 조회"""
        if self.company_manager.companies_df is not None:
            info = self.company_manager.companies_df[self.company_manager.companies_df['Code'] == symbol]
            if not info.empty:
                return info.iloc[0]['Name']
        return "Unknown"

async def main():
    """메인 실행 함수 - 사용자 입력 기반"""
    
    # 1. 종목 개수 입력 받기
    while True:
        try:
            count_str = input("1. 다운로드할 종목 갯수를 입력하세요 (기본값: 10): ")
            if not count_str:
                test_count = 10
                break
            test_count = int(count_str)
            if test_count > 0:
                break
            else:
                logger.warning("❌ 1 이상의 숫자를 입력하세요.")
        except ValueError:
            logger.warning("❌ 유효한 숫자가 아닙니다.")

    # 2. 연도 입력 받기
    while True:
        try:
            year_str = input(f"2. 데이터를 다운로드할 연도를 입력하세요 (YYYY, 예: {datetime.now().year - 1}): ")
            year = int(year_str)
            if 1990 < year <= datetime.now().year:
                start_date = f"{year}-01-01"
                end_date = f"{year}-12-31"
                break
            else:
                logger.warning(f"❌ 1990년과 {datetime.now().year}년 사이의 유효한 연도를 입력하세요.")
        except ValueError:
            logger.warning("❌ 유효한 연도 형식이 아닙니다.")
            
    logger.info("🚀 Initializing Quant Data Management System...")
    quant_manager = QuantDataManager()
    
    try:
        await quant_manager.initialize_companies()
        test_symbols = quant_manager.get_test_symbols(test_count)
        
        if not test_symbols:
            logger.error("No symbols to process. Exiting.")
            return
            
        collected_data = await quant_manager.collect_test_data(test_symbols, start_date, end_date)
        
        if collected_data:
            filename_prefix = f"stock_data_{len(test_symbols)}symbols_{year}"
            await quant_manager.save_data_to_csv(collected_data, filename_prefix)
        else:
            logger.warning("⚠️ No data collected.")
            
    except Exception as e:
        logger.error(f"💥 An unexpected error occurred during execution: {e}")
        import traceback
        traceback.print_exc()
    
    logger.info("🏁 Quant Data Management System finished")

if __name__ == "__main__":
    asyncio.run(main())