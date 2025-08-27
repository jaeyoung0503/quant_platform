"""
file: main.py
키움증권 주식 데이터 수집기 - 데이터 관리자
Phase 1 MVP

CSV 파일 저장/로드, 데이터 검증, 파일 관리 기능
수집된 주식 데이터의 저장소 역할
"""

import os
import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from config import get_config

class DataManager:
    """주식 데이터 관리 클래스"""
    
    def __init__(self):
        """데이터 매니저 초기화"""
        self.config = get_config()
        self.logger = logging.getLogger(__name__)
        
        # 파일 경로 설정
        self.csv_base_path = self.config.CSV_SAVE_PATH
        self.daily_path = self.csv_base_path / 'daily'
        self.minute_path = self.csv_base_path / 'minute'
        self.backup_path = self.csv_base_path / 'backup'
        
        # 디렉토리 생성
        self._create_directories()
        
        # 데이터 캐시
        self.data_cache: Dict[str, pd.DataFrame] = {}
        self.cache_timestamps: Dict[str, datetime] = {}
        self.cache_max_age = timedelta(minutes=30)  # 30분 캐시
    
    def _create_directories(self):
        """필요한 디렉토리 생성"""
        directories = [
            self.csv_base_path,
            self.daily_path,
            self.minute_path,
            self.backup_path
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        self.logger.debug(f"📁 디렉토리 생성 완료: {len(directories)}개")
    
    def save_daily_data(self, stock_code: str, stock_name: str, data: pd.DataFrame,
                       start_date: str = None, end_date: str = None) -> Optional[str]:
        """일봉 데이터를 CSV 파일로 저장"""
        try:
            if data is None or data.empty:
                self.logger.warning(f"⚠️ {stock_code} 저장할 데이터가 없습니다.")
                return None
            
            # 날짜 범위 자동 계산 (데이터에서 추출)
            if start_date is None or end_date is None:
                dates = data['날짜'].tolist()
                start_date = min(dates)
                end_date = max(dates)
            
            # 파일명 생성
            filename = self.config.get_csv_filename(
                stock_code, stock_name, start_date, end_date, 'daily'
            )
            filepath = self.daily_path / filename
            
            # 데이터 검증
            validated_data = self._validate_daily_data(data)
            if validated_data is None:
                self.logger.error(f"❌ {stock_code} 데이터 검증 실패")
                return None
            
            # 기존 파일 백업 (덮어쓰기 전)
            if filepath.exists():
                self._backup_file(filepath)
            
            # CSV 저장
            validated_data.to_csv(
                filepath,
                index=False,
                encoding=self.config.CSV_ENCODING
            )
            
            # 저장 후 검증
            if self._verify_saved_file(filepath):
                self.logger.info(f"✅ {stock_name}({stock_code}) 일봉 데이터 저장: {filename}")
                
                # 캐시 업데이트
                cache_key = f"daily_{stock_code}"
                self.data_cache[cache_key] = validated_data.copy()
                self.cache_timestamps[cache_key] = datetime.now()
                
                return str(filepath)
            else:
                self.logger.error(f"❌ {stock_code} 파일 저장 검증 실패")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ {stock_code} 일봉 데이터 저장 실패: {e}")
            return None
    
    def load_daily_data(self, stock_code: str, use_cache: bool = True) -> Optional[pd.DataFrame]:
        """일봉 데이터 로드"""
        try:
            # 캐시 확인
            if use_cache:
                cached_data = self._get_cached_data(f"daily_{stock_code}")
                if cached_data is not None:
                    self.logger.debug(f"📊 {stock_code} 캐시에서 일봉 데이터 로드")
                    return cached_data
            
            # 최신 파일 찾기
            latest_file = self._find_latest_daily_file(stock_code)
            if not latest_file:
                self.logger.warning(f"⚠️ {stock_code} 일봉 데이터 파일을 찾을 수 없습니다.")
                return None
            
            # CSV 파일 로드
            data = pd.read_csv(latest_file, encoding=self.config.CSV_ENCODING)
            
            # 데이터 검증
            validated_data = self._validate_daily_data(data)
            if validated_data is None:
                self.logger.error(f"❌ {stock_code} 로드된 데이터 검증 실패")
                return None
            
            # 캐시 저장
            cache_key = f"daily_{stock_code}"
            self.data_cache[cache_key] = validated_data.copy()
            self.cache_timestamps[cache_key] = datetime.now()
            
            self.logger.info(f"✅ {stock_code} 일봉 데이터 로드: {len(validated_data)}개")
            return validated_data
            
        except Exception as e:
            self.logger.error(f"❌ {stock_code} 일봉 데이터 로드 실패: {e}")
            return None
    
    def _validate_daily_data(self, data: pd.DataFrame) -> Optional[pd.DataFrame]:
        """일봉 데이터 검증 및 정리"""
        if data is None or data.empty:
            return None
        
        try:
            # 필수 컬럼 확인
            required_columns = ['날짜', '시가', '고가', '저가', '종가', '거래량']
            missing_columns = [col for col in required_columns if col not in data.columns]
            
            if missing_columns:
                self.logger.error(f"❌ 필수 컬럼 누락: {missing_columns}")
                return None
            
            # 데이터 복사
            validated_data = data.copy()
            
            # 날짜 형식 통일 (YYYY-MM-DD 또는 YYYYMMDD)
            validated_data['날짜'] = validated_data['날짜'].astype(str)
            validated_data['날짜'] = validated_data['날짜'].apply(self._normalize_date_format)
            
            # 숫자형 컬럼 변환
            numeric_columns = ['시가', '고가', '저가', '종가', '거래량']
            for col in numeric_columns:
                validated_data[col] = pd.to_numeric(validated_data[col], errors='coerce')
            
            # 결측값 확인
            null_counts = validated_data[required_columns].isnull().sum()
            if null_counts.sum() > 0:
                self.logger.warning(f"⚠️ 결측값 발견: {null_counts[null_counts > 0].to_dict()}")
                
                # 결측값이 있는 행 제거
                validated_data = validated_data.dropna(subset=required_columns)
            
            # 데이터 정합성 검증
            invalid_rows = []
            
            # 가격 데이터 검증 (시가, 고가, 저가, 종가 > 0)
            price_cols = ['시가', '고가', '저가', '종가']
            for idx, row in validated_data.iterrows():
                # 음수 가격 확인
                if any(row[col] <= 0 for col in price_cols):
                    invalid_rows.append(idx)
                    continue
                
                # 고가 >= 저가 확인
                if row['고가'] < row['저가']:
                    invalid_rows.append(idx)
                    continue
                
                # 시가, 종가가 고가-저가 범위 내에 있는지 확인
                if not (row['저가'] <= row['시가'] <= row['고가']):
                    invalid_rows.append(idx)
                    continue
                
                if not (row['저가'] <= row['종가'] <= row['고가']):
                    invalid_rows.append(idx)
                    continue
                
                # 거래량 검증 (음수 불가)
                if row['거래량'] < 0:
                    invalid_rows.append(idx)
                    continue
            
            # 잘못된 데이터 제거
            if invalid_rows:
                self.logger.warning(f"⚠️ 잘못된 데이터 {len(invalid_rows)}개 제거")
                validated_data = validated_data.drop(invalid_rows)
            
            # 날짜순 정렬 (과거 → 현재)
            validated_data = validated_data.sort_values('날짜').reset_index(drop=True)
            
            # 중복 날짜 제거 (최신 데이터 유지)
            before_count = len(validated_data)
            validated_data = validated_data.drop_duplicates(subset=['날짜'], keep='last').reset_index(drop=True)
            after_count = len(validated_data)
            
            if before_count != after_count:
                self.logger.warning(f"⚠️ 중복 날짜 {before_count - after_count}개 제거")
            
            if len(validated_data) == 0:
                self.logger.error("❌ 검증 후 유효한 데이터가 없습니다.")
                return None
            
            return validated_data
            
        except Exception as e:
            self.logger.error(f"❌ 데이터 검증 중 오류: {e}")
            return None
    
    def _normalize_date_format(self, date_str: str) -> str:
        """날짜 형식 정규화 (YYYYMMDD)"""
        try:
            # 공백 제거
            date_str = str(date_str).strip()
            
            # 이미 YYYYMMDD 형식인 경우
            if len(date_str) == 8 and date_str.isdigit():
                return date_str
            
            # YYYY-MM-DD 형식인 경우
            if len(date_str) == 10 and '-' in date_str:
                return date_str.replace('-', '')
            
            # 기타 형식 시도
            from datetime import datetime
            parsed_date = datetime.strptime(date_str, '%Y%m%d')
            return parsed_date.strftime('%Y%m%d')
            
        except:
            # 파싱 실패시 원본 반환
            return date_str
    
    def _find_latest_daily_file(self, stock_code: str) -> Optional[Path]:
        """특정 종목의 최신 일봉 파일 찾기"""
        try:
            # 해당 종목의 모든 일봉 파일 검색
            pattern = f"{stock_code}_*_daily_*.csv"
            files = list(self.daily_path.glob(pattern))
            
            if not files:
                return None
            
            # 파일 생성 시간 기준 최신 파일 선택
            latest_file = max(files, key=lambda f: f.stat().st_mtime)
            
            self.logger.debug(f"📁 {stock_code} 최신 일봉 파일: {latest_file.name}")
            return latest_file
            
        except Exception as e:
            self.logger.error(f"❌ {stock_code} 최신 파일 검색 실패: {e}")
            return None
    
    def _backup_file(self, filepath: Path):
        """파일 백업"""
        try:
            if not filepath.exists():
                return
            
            # 백업 파일명 생성 (원본명_YYYYMMDD_HHMMSS.csv)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{filepath.stem}_{timestamp}{filepath.suffix}"
            backup_filepath = self.backup_path / backup_name
            
            # 백업 복사
            shutil.copy2(filepath, backup_filepath)
            
            self.logger.debug(f"💾 파일 백업: {backup_name}")
            
        except Exception as e:
            self.logger.warning(f"⚠️ 파일 백업 실패: {e}")
    
    def _verify_saved_file(self, filepath: Path) -> bool:
        """저장된 파일 검증"""
        try:
            if not filepath.exists():
                return False
            
            # 파일 크기 확인
            if filepath.stat().st_size == 0:
                return False
            
            # CSV 파일 로드 테스트
            test_data = pd.read_csv(filepath, encoding=self.config.CSV_ENCODING, nrows=1)
            if test_data.empty:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 파일 검증 실패: {e}")
            return False
    
    def _get_cached_data(self, cache_key: str) -> Optional[pd.DataFrame]:
        """캐시된 데이터 조회"""
        if cache_key not in self.data_cache:
            return None
        
        # 캐시 만료 확인
        if cache_key in self.cache_timestamps:
            cache_age = datetime.now() - self.cache_timestamps[cache_key]
            if cache_age > self.cache_max_age:
                # 만료된 캐시 제거
                del self.data_cache[cache_key]
                del self.cache_timestamps[cache_key]
                return None
        
        return self.data_cache[cache_key].copy()
    
    def clear_cache(self):
        """캐시 초기화"""
        self.data_cache.clear()
        self.cache_timestamps.clear()
        self.logger.info("🧹 데이터 캐시 초기화 완료")
    
    def get_stock_file_list(self, stock_code: str = None) -> List[Dict]:
        """종목별 파일 목록 조회"""
        try:
            file_list = []
            
            # 검색 패턴 설정
            if stock_code:
                patterns = [f"{stock_code}_*_daily_*.csv"]
            else:
                patterns = ["*_daily_*.csv"]
            
            for pattern in patterns:
                files = list(self.daily_path.glob(pattern))
                
                for file_path in files:
                    try:
                        # 파일명에서 정보 추출
                        parts = file_path.stem.split('_')
                        if len(parts) >= 5:
                            code = parts[0]
                            name = parts[1]
                            data_type = parts[2]
                            start_date = parts[3]
                            end_date = parts[4]
                            
                            # 파일 정보 구성
                            stat = file_path.stat()
                            file_info = {
                                'code': code,
                                'name': name,
                                'data_type': data_type,
                                'start_date': start_date,
                                'end_date': end_date,
                                'filepath': str(file_path),
                                'filename': file_path.name,
                                'size': stat.st_size,
                                'created': datetime.fromtimestamp(stat.st_ctime),
                                'modified': datetime.fromtimestamp(stat.st_mtime)
                            }
                            file_list.append(file_info)
                    except:
                        continue
            
            # 수정 시간 기준 최신순 정렬
            file_list.sort(key=lambda x: x['modified'], reverse=True)
            
            return file_list
            
        except Exception as e:
            self.logger.error(f"❌ 파일 목록 조회 실패: {e}")
            return []
    
    def delete_stock_data(self, stock_code: str, backup: bool = True) -> bool:
        """종목 데이터 파일 삭제"""
        try:
            deleted_count = 0
            
            # 해당 종목의 모든 파일 찾기
            patterns = [
                f"{stock_code}_*_daily_*.csv",
                f"{stock_code}_*_minute_*.csv"
            ]
            
            for pattern in patterns:
                files = list(self.csv_base_path.rglob(pattern))
                
                for file_path in files:
                    try:
                        if backup:
                            self._backup_file(file_path)
                        
                        file_path.unlink()  # 파일 삭제
                        deleted_count += 1
                        self.logger.debug(f"🗑️ 파일 삭제: {file_path.name}")
                        
                    except Exception as e:
                        self.logger.warning(f"⚠️ 파일 삭제 실패 ({file_path.name}): {e}")
            
            # 캐시에서도 제거
            cache_keys_to_remove = [key for key in self.data_cache.keys() if stock_code in key]
            for key in cache_keys_to_remove:
                del self.data_cache[key]
                if key in self.cache_timestamps:
                    del self.cache_timestamps[key]
            
            if deleted_count > 0:
                self.logger.info(f"✅ {stock_code} 데이터 파일 삭제 완료: {deleted_count}개")
                return True
            else:
                self.logger.warning(f"⚠️ {stock_code} 삭제할 파일이 없습니다.")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ {stock_code} 데이터 삭제 실패: {e}")
            return False
    
    def cleanup_old_backups(self, days_to_keep: int = 30):
        """오래된 백업 파일 정리"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            deleted_count = 0
            
            backup_files = list(self.backup_path.glob("*.csv"))
            
            for backup_file in backup_files:
                try:
                    file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                    
                    if file_time < cutoff_date:
                        backup_file.unlink()
                        deleted_count += 1
                        self.logger.debug(f"🗑️ 백업 파일 정리: {backup_file.name}")
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ 백업 파일 삭제 실패 ({backup_file.name}): {e}")
            
            if deleted_count > 0:
                self.logger.info(f"🧹 오래된 백업 파일 정리: {deleted_count}개 삭제")
            
        except Exception as e:
            self.logger.error(f"❌ 백업 파일 정리 실패: {e}")
    
    def get_data_summary(self) -> Dict:
        """데이터 요약 정보"""
        try:
            summary = {
                'total_files': 0,
                'total_size': 0,
                'stocks': {},
                'date_range': {},
                'cache_status': {
                    'cached_items': len(self.data_cache),
                    'cache_size': sum(df.memory_usage(deep=True).sum() for df in self.data_cache.values()) if self.data_cache else 0
                }
            }
            
            # 파일 정보 수집
            all_files = self.get_stock_file_list()
            summary['total_files'] = len(all_files)
            
            for file_info in all_files:
                code = file_info['code']
                
                # 종목별 통계
                if code not in summary['stocks']:
                    summary['stocks'][code] = {
                        'name': file_info['name'],
                        'file_count': 0,
                        'total_size': 0,
                        'latest_data': None
                    }
                
                summary['stocks'][code]['file_count'] += 1
                summary['stocks'][code]['total_size'] += file_info['size']
                summary['total_size'] += file_info['size']
                
                # 최신 데이터 일자
                if summary['stocks'][code]['latest_data'] is None or file_info['end_date'] > summary['stocks'][code]['latest_data']:
                    summary['stocks'][code]['latest_data'] = file_info['end_date']
            
            return summary
            
        except Exception as e:
            self.logger.error(f"❌ 데이터 요약 생성 실패: {e}")
            return {}
    
    def export_to_excel(self, stock_code: str, output_path: str = None) -> Optional[str]:
        """데이터를 Excel 파일로 내보내기"""
        try:
            # 데이터 로드
            data = self.load_daily_data(stock_code)
            if data is None or data.empty:
                self.logger.warning(f"⚠️ {stock_code} 내보낼 데이터가 없습니다.")
                return None
            
            # 출력 파일 경로 설정
            if output_path is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{stock_code}_주식데이터_{timestamp}.xlsx"
                output_path = self.csv_base_path / filename
            
            # Excel 파일로 저장
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                data.to_excel(writer, sheet_name='일봉데이터', index=False)
                
                # 요약 정보 시트 추가
                summary_data = {
                    '항목': ['종목코드', '데이터 개수', '기간 시작', '기간 종료', '최고가', '최저가'],
                    '값': [
                        stock_code,
                        len(data),
                        data['날짜'].min(),
                        data['날짜'].max(),
                        data['고가'].max(),
                        data['저가'].min()
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='요약정보', index=False)
            
            self.logger.info(f"✅ {stock_code} Excel 내보내기 완료: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"❌ {stock_code} Excel 내보내기 실패: {e}")
            return None

# 전역 데이터 매니저 인스턴스
_data_manager = None

def get_data_manager() -> DataManager:
    """데이터 매니저 싱글톤 인스턴스 반환"""
    global _data_manager
    if _data_manager is None:
        _data_manager = DataManager()
    return _data_manager

if __name__ == "__main__":
    # 테스트 코드
    import logging
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🧪 데이터 매니저 테스트 시작...")
    print("=" * 50)
    
    # 데이터 매니저 생성
    manager = get_data_manager()
    
    # 테스트 데이터 생성
    test_data = pd.DataFrame({
        '날짜': ['20240801', '20240802', '20240803'],
        '시가': [84000, 84500, 85000],
        '고가': [85000, 85500, 86000],
        '저가': [83500, 84000, 84500],
        '종가': [84500, 85000, 85500],
        '거래량': [1000000, 1100000, 1200000]
    })
    
    print("📊 테스트 데이터:")
    print(test_data)
    
    # 저장 테스트
    print("\n💾 저장 테스트:")
    save_path = manager.save_daily_data('000000', '테스트종목', test_data)
    if save_path:
        print(f"✅ 저장 성공: {save_path}")
    else:
        print("❌ 저장 실패")
    
    # 로드 테스트
    print("\n📂 로드 테스트:")
    loaded_data = manager.load_daily_data('000000')
    if loaded_data is not None:
        print(f"✅ 로드 성공: {len(loaded_data)}개 레코드")
        print(loaded_data.head())
    else:
        print("❌ 로드 실패")
    
    # 데이터 요약
    print("\n📈 데이터 요약:")
    summary = manager.get_data_summary()
    print(f"   - 총 파일 수: {summary.get('total_files', 0)}개")
    print(f"   - 총 크기: {summary.get('total_size', 0):,} bytes")
    print(f"   - 캐시된 항목: {summary.get('cache_status', {}).get('cached_items', 0)}개")
    
    print("\n" + "=" * 50)
    print("🎉 데이터 매니저 테스트 완료!")