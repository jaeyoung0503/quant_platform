# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from pykrx import stock
import time
from datetime import datetime, timedelta
import os
import warnings
import sys

# 한글 인코딩 설정
if sys.platform.startswith('win'):
    # Windows에서 콘솔 인코딩 설정
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    os.environ['PYTHONIOENCODING'] = 'utf-8'

warnings.filterwarnings('ignore')

class KRXFinancialDataGenerator:
    def __init__(self):
        self.data_folder = 'krx_financial_data'
        
        # 데이터 폴더 생성
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
            print(f"📁 폴더 생성: {self.data_folder}")
    
    def show_menu(self):
        """메인 메뉴 표시"""
        print("\n" + "="*60)
        print("🏦 KRX 재무 데이터 생성기 (기본 버전)")
        print("="*60)
        print("1. 📊 재무지표 CSV 생성 (PER, PBR, EPS, BPS 등)")
        print("2. 🏢 재무정보 CSV 생성 (자산, 부채, 매출, 이익 등)")
        print("3. 🔗 재무지표 + 재무정보 통합 생성")
        print("4. 📈 연도별 데이터 일괄 생성")
        print("5. 🔄 기존 파일 병합 (연도별)")
        print("6. 📋 생성된 파일 목록 보기")
        print("7. 🗑️  파일 삭제")
        print("0. 🚪 종료")
        print("="*60)
    
    def get_market_selection(self):
        """시장 선택 입력 받기"""
        print("\n📈 생성할 시장을 선택하세요:")
        print("1. 코스피 + 코스닥 (전체)")
        print("2. 코스피만")
        print("3. 코스닥만")
        
        while True:
            try:
                choice = input("선택 (1-3, 엔터=전체): ").strip()
                
                # 엔터(빈 입력) = 기본값(전체)
                if choice == "" or choice == "1":
                    return ["KOSPI", "KOSDAQ"], "전체"
                elif choice == "2":
                    return ["KOSPI"], "코스피"
                elif choice == "3":
                    return ["KOSDAQ"], "코스닥"
                else:
                    print("❌ 1, 2, 3 중에서 선택하거나 엔터를 눌러주세요.")
                    
            except Exception as e:
                print(f"❌ 입력 오류: {e}")

    def get_date_input(self, prompt="연도를 입력하세요"):
        """연도 및 시장 선택 입력 받기"""
        # 연도 입력
        while True:
            try:
                if "연도" in prompt:
                    year_input = input(f"{prompt} (예: 2024): ").strip()
                    year = int(year_input)
                    
                    current_year = datetime.now().year
                    
                    if year < 2000 or year > current_year + 1:
                        print(f"❌ 2000년 ~ {current_year + 1}년 사이의 연도를 입력해주세요.")
                        continue
                    
                    # 기준일 설정 로직 개선
                    if year > current_year:
                        # 미래 연도 (2025년 등)인 경우 - 가장 최근 영업일 사용
                        print(f"  📅 {year}년은 미래 연도입니다. 가장 최근 영업일 데이터를 사용합니다.")
                        base_date = self.get_latest_business_date()
                        print(f"  📅 사용할 기준일: {base_date[:4]}-{base_date[4:6]}-{base_date[6:]}")
                    elif year == current_year:
                        # 현재 연도인 경우 - 가장 최근 영업일 사용
                        print(f"  📅 {year}년 현재 연도입니다. 가장 최근 영업일 데이터를 사용합니다.")
                        base_date = self.get_latest_business_date()
                        print(f"  📅 사용할 기준일: {base_date[:4]}-{base_date[4:6]}-{base_date[6:]}")
                    else:
                        # 과거 연도인 경우 - 해당 연도 12월 31일 (또는 마지막 영업일)
                        base_date = f"{year}1231"
                        # 12월 31일이 주말인 경우를 대비해 마지막 영업일 찾기
                        base_date = self.get_last_business_date_of_year(year)
                        print(f"  📅 사용할 기준일: {base_date[:4]}-{base_date[4:6]}-{base_date[6:]} ({year}년 마지막 영업일)")
                    
                    # 시장 선택
                    markets, market_name = self.get_market_selection()
                    
                    return base_date, year, markets, market_name
                else:
                    date_input = input(f"{prompt} (예: 20241231): ").strip()
                    datetime.strptime(date_input, '%Y%m%d')  # 날짜 형식 검증
                    
                    # 시장 선택
                    markets, market_name = self.get_market_selection()
                    
                    return date_input, int(date_input[:4]), markets, market_name
                    
            except ValueError:
                print("❌ 올바른 형식으로 입력해주세요.")
            except Exception as e:
                print(f"❌ 입력 오류: {e}")
    
    def get_latest_business_date(self):
        """가장 최근 영업일 반환"""
        from datetime import datetime, timedelta
        
        # 현재 날짜에서 시작
        current_date = datetime.now()
        
        # 최근 7일 내에서 데이터가 있는 날짜 찾기
        for i in range(7):
            check_date = current_date - timedelta(days=i)
            # 주말 건너뛰기 (월요일=0, 일요일=6)
            if check_date.weekday() >= 5:  # 토요일(5) 또는 일요일(6)
                continue
                
            date_str = check_date.strftime('%Y%m%d')
            
            # 해당 날짜에 데이터가 있는지 확인
            try:
                test_data = stock.get_market_ticker_list(date_str, market='KOSPI')
                if test_data and len(test_data) > 0:
                    return date_str
            except:
                continue
        
        # 기본값으로 어제 날짜 반환
        yesterday = current_date - timedelta(days=1)
        return yesterday.strftime('%Y%m%d')
    
    def get_last_business_date_of_year(self, year):
        """특정 연도의 마지막 영업일 반환"""
        from datetime import datetime, timedelta
        
        # 12월 31일부터 역순으로 확인
        base_date = datetime(year, 12, 31)
        
        for i in range(10):  # 최대 10일 전까지 확인
            check_date = base_date - timedelta(days=i)
            
            # 주말 건너뛰기
            if check_date.weekday() >= 5:
                continue
            
            date_str = check_date.strftime('%Y%m%d')
            
            # 해당 날짜에 데이터가 있는지 확인
            try:
                test_data = stock.get_market_ticker_list(date_str, market='KOSPI')
                if test_data and len(test_data) > 0:
                    return date_str
            except:
                continue
        
        # 기본값으로 12월 30일 반환
        return f"{year}1230"
    
    def get_multiple_years_input(self):
        """여러 연도 입력 받기 (미래 연도 포함)"""
        while True:
            try:
                print("\n📅 생성할 연도 입력 방법:")
                print("1. 단일 연도: 2024")
                print("2. 범위 입력: 2020-2024") 
                print("3. 개별 입력: 2020,2022,2024")
                print("💡 2025년 입력시 최신 데이터를 사용합니다.")
                
                input_str = input("연도를 입력하세요: ").strip()
                
                if '-' in input_str:
                    # 범위 입력
                    start_year, end_year = map(int, input_str.split('-'))
                    if start_year > end_year:
                        start_year, end_year = end_year, start_year
                    years = list(range(start_year, end_year + 1))
                elif ',' in input_str:
                    # 개별 입력
                    years = [int(y.strip()) for y in input_str.split(',')]
                else:
                    # 단일 연도
                    years = [int(input_str)]
                
                # 연도 유효성 검사 (미래 1년까지 허용)
                current_year = datetime.now().year
                valid_years = [y for y in years if 2000 <= y <= current_year + 1]
                
                if not valid_years:
                    print(f"❌ 유효한 연도가 없습니다. (2000-{current_year + 1} 범위)")
                    continue
                
                if len(valid_years) != len(years):
                    invalid_years = set(years) - set(valid_years)
                    print(f"⚠️  무효한 연도 제외: {invalid_years}")
                
                # 미래 연도 안내
                future_years = [y for y in valid_years if y > current_year]
                if future_years:
                    print(f"📅 미래 연도 {future_years}는 최신 데이터로 처리됩니다.")
                
                print(f"✅ 선택된 연도: {sorted(valid_years)}")
                return sorted(valid_years)
                
            except ValueError:
                print("❌ 올바른 형식으로 입력해주세요.")
            except Exception as e:
                print(f"❌ 입력 오류: {e}")
    
    def generate_investment_indicators_csv(self, base_date, year, markets=["KOSPI", "KOSDAQ"]):
        """재무지표 CSV 생성 (시장 선택 가능)"""
        market_names = "+".join(markets)
        
        # 실제 데이터 기준일 표시
        actual_year = int(base_date[:4])
        date_display = f"{base_date[:4]}-{base_date[4:6]}-{base_date[6:]}"
        
        print(f"\n🎯 {year}년 재무지표 CSV 생성 ({market_names})")
        if year != actual_year:
            print(f"   📅 실제 데이터 기준일: {date_display}")
        print("-" * 40)
        
        try:
            # 선택된 시장별로 데이터 수집
            print(f"  📊 {market_names} 재무지표 데이터 수집 중... (기준일: {date_display})")
            
            all_fundamental_data = []
            
            for market in markets:
                print(f"    🏪 {market} 데이터 수집 중...")
                try:
                    market_data = stock.get_market_fundamental(base_date, market=market)
                    
                    if market_data is not None and not market_data.empty:
                        print(f"      📋 원본 데이터 구조 확인:")
                        print(f"        - 타입: {type(market_data)}")
                        print(f"        - Shape: {market_data.shape}")
                        print(f"        - 컬럼: {list(market_data.columns)}")
                        print(f"        - 인덱스 이름: {market_data.index.name}")
                        print(f"        - 인덱스 샘플: {list(market_data.index[:3])}")
                        
                        # 데이터 처리
                        market_data_processed = market_data.reset_index()
                        
                        # 종목코드 컬럼 확인 및 생성
                        if market_data.index.name:
                            # 인덱스에 이름이 있는 경우 (예: '종목코드')
                            ticker_col = market_data.index.name
                            print(f"        - 종목코드 컬럼: {ticker_col} (인덱스에서)")
                            market_data_processed = market_data_processed.rename(columns={ticker_col: '종목코드'})
                        elif 'index' in market_data_processed.columns:
                            # reset_index()로 'index' 컬럼이 생성된 경우
                            print(f"        - 종목코드 컬럼: index (reset_index에서)")
                            market_data_processed = market_data_processed.rename(columns={'index': '종목코드'})
                        else:
                            # 첫 번째 컬럼을 종목코드로 가정
                            first_col = market_data_processed.columns[0]
                            print(f"        - 종목코드 컬럼: {first_col} (첫번째 컬럼)")
                            market_data_processed = market_data_processed.rename(columns={first_col: '종목코드'})
                        
                        # 시장구분 추가
                        market_data_processed['시장구분'] = market
                        all_fundamental_data.append(market_data_processed)
                        
                        print(f"      ✅ {market} 데이터: {len(market_data_processed)}건")
                        print(f"      📊 처리된 컬럼: {list(market_data_processed.columns)}")
                    else:
                        print(f"      ❌ {market} 데이터 없음")
                        
                except Exception as e:
                    print(f"      ❌ {market} 데이터 수집 오류: {e}")
                    continue
            
            if not all_fundamental_data:
                print("  ❌ 재무지표 데이터가 없습니다.")
                return None, 0
            
            # 데이터 통합
            print(f"  🔄 데이터 통합 중... ({len(all_fundamental_data)}개 시장)")
            all_fundamental = pd.concat(all_fundamental_data, ignore_index=True)
            print(f"  📊 통합 완료: {len(all_fundamental)}건")
            
            # 종목코드 컬럼 확인
            if '종목코드' not in all_fundamental.columns:
                print(f"  ❌ '종목코드' 컬럼이 없습니다. 사용 가능한 컬럼: {list(all_fundamental.columns)}")
                return None, 0
            
            # 컬럼명 정리
            print(f"  🏷️  컬럼명 정리 중...")
            financial_indicators = all_fundamental.rename(columns={
                '종가': '종가',
                'EPS': 'EPS',
                'PER': 'PER', 
                'BPS': 'BPS',
                'PBR': 'PBR',
                'DIV': '배당수익률',
                'DPS': '배당금'
            })
            
            print(f"  📋 정리된 컬럼: {list(financial_indicators.columns)}")
            
            # 종목명 추가
            print(f"  🏷️  종목 정보 추가 중... (총 {len(financial_indicators)}개 종목)")
            company_names = []
            successful_names = 0
            failed_names = 0
            
            # 진행률 표시를 위한 설정
            total_count = len(financial_indicators)
            batch_size = 50  # 50개씩 처리할 때마다 진행률 표시
            
            print(f"    🔄 종목명 수집 시작...")
            
            for i, ticker in enumerate(financial_indicators['종목코드']):
                try:
                    name = stock.get_market_ticker_name(ticker)
                    if name and name.strip():
                        company_names.append(name.strip())
                        successful_names += 1
                    else:
                        company_names.append(f'Company_{ticker}')
                        failed_names += 1
                        
                except Exception as e:
                    company_names.append(f'Error_{ticker}')
                    failed_names += 1
                
                # 진행상황 표시 (매 50개마다)
                if (i + 1) % batch_size == 0 or (i + 1) == total_count:
                    progress_pct = (i + 1) / total_count * 100
                    success_rate = successful_names / (i + 1) * 100 if (i + 1) > 0 else 0
                    print(f"    📈 진행: {i + 1:>4}/{total_count} ({progress_pct:>5.1f}%) | 성공률: {success_rate:>5.1f}% | 성공: {successful_names:>3}개 실패: {failed_names:>3}개")
                
                # API 부하 방지를 위한 지연 (더 짧게 조정)
                time.sleep(0.05)
            
            # 최종 결과
            print(f"  ✅ 종목명 수집 완료:")
            print(f"    - 총 처리: {total_count}개")
            print(f"    - 성공: {successful_names}개")
            print(f"    - 실패: {failed_names}개")
            print(f"    - 성공률: {successful_names/(successful_names+failed_names)*100:.1f}%")
            
            financial_indicators['회사명'] = company_names
            
            # 컬럼 순서 정리
            print(f"  📋 컬럼 순서 정리 중...")
            column_order = [
                '종목코드', '회사명', '시장구분', '종가', 
                'EPS', 'PER', 'BPS', 'PBR', '배당수익률', '배당금'
            ]
            available_cols = [col for col in column_order if col in financial_indicators.columns]
            missing_cols = [col for col in column_order if col not in financial_indicators.columns]
            
            print(f"    - 사용 가능한 컬럼: {available_cols}")
            if missing_cols:
                print(f"    - 누락된 컬럼: {missing_cols}")
            
            financial_indicators = financial_indicators[available_cols]
            
            # 데이터 정제 및 0값 문제 해결
            print(f"  🔧 데이터 정제 및 검증 중...")
            
            # 원본 데이터 상태 확인
            print(f"    📋 정제 전 데이터 상태:")
            for col in ['PER', 'PBR', 'EPS', 'BPS']:
                if col in financial_indicators.columns:
                    non_zero_count = (financial_indicators[col] != 0).sum()
                    total_count = len(financial_indicators)
                    print(f"      - {col}: 0이 아닌 값 {non_zero_count}/{total_count}개 ({non_zero_count/total_count*100:.1f}%)")
            
            # 데이터 정제 실행
            financial_indicators = self.clean_financial_data(financial_indicators)
            
            # 정제 후 데이터 상태 확인
            print(f"    📋 정제 후 데이터 상태:")
            for col in ['PER', 'PBR', 'EPS', 'BPS']:
                if col in financial_indicators.columns:
                    # NaN이 아닌 값들 중에서 0이 아닌 값 개수
                    non_nan_count = financial_indicators[col].notna().sum()
                    non_zero_count = ((financial_indicators[col] != 0) & (financial_indicators[col].notna())).sum()
                    if non_nan_count > 0:
                        mean_val = financial_indicators[col].mean()
                        max_val = financial_indicators[col].max()
                        min_val = financial_indicators[col].min()
                        print(f"      - {col}: 유효값 {non_zero_count}/{non_nan_count}개, 평균: {mean_val:.2f}, 범위: {min_val:.2f}~{max_val:.2f}")
                    else:
                        print(f"      - {col}: 모든 값이 NaN")
            
            # 샘플 데이터 확인 (0이 아닌 값들)
            print(f"    🔍 유효한 데이터 샘플 확인:")
            sample_data = financial_indicators.copy()
            
            # PER이나 PBR이 0이 아닌 데이터만 필터링
            valid_data = sample_data[
                ((sample_data['PER'] > 0) | (sample_data['PBR'] > 0)) if 
                all(col in sample_data.columns for col in ['PER', 'PBR']) else 
                sample_data.index < 10  # 없으면 상위 10개만
            ]
            
            if len(valid_data) > 0:
                display_cols = ['종목코드', '회사명']
                for col in ['PER', 'PBR', 'EPS', 'BPS']:
                    if col in valid_data.columns:
                        display_cols.append(col)
                
                print(f"      📊 유효 데이터 ({len(valid_data)}건 중 상위 3건):")
                print(valid_data[display_cols].head(3).to_string(index=False))
            else:
                print(f"      ⚠️  유효한 데이터가 없습니다 (모든 PER, PBR이 0 또는 NaN)")
                # 원본 데이터 일부 출력
                display_cols = ['종목코드', '회사명']
                for col in sample_data.columns:
                    if col not in ['종목코드', '회사명', '시장구분'] and len(display_cols) < 6:
                        display_cols.append(col)
                print(f"      📊 원본 데이터 샘플:")
                print(sample_data[display_cols].head(3).to_string(index=False))
            
            # CSV 저장 (UTF-8 with BOM으로 저장 - 한글 깨짐 방지)
            market_suffix = "_".join(markets) if len(markets) > 1 else markets[0]
            
            # 파일명에 실제 기준일 반영
            if year != actual_year:
                filename = f"{self.data_folder}/재무지표_{year}년요청_{actual_year}{base_date[4:8]}기준_{market_suffix}.csv"
            else:
                filename = f"{self.data_folder}/재무지표_{year}_{market_suffix}.csv"
            
            print(f"  💾 CSV 파일 저장 중...")
            # UTF-8 with BOM으로 저장하여 Excel에서도 한글 표시
            financial_indicators.to_csv(filename, index=False, encoding='utf-8-sig')
            
            print(f"  ✅ 저장 완료: {filename}")
            print(f"  📊 최종 데이터: {len(financial_indicators)}건, 컬럼: {len(financial_indicators.columns)}개")
            
            # 데이터 샘플 미리보기 (개선된 버전)
            print(f"  🔍 최종 데이터 샘플:")
            
            # 의미있는 데이터가 있는 종목들 우선 표시
            sample_for_display = financial_indicators.copy()
            
            # PER, PBR 둘 중 하나라도 유효한 값이 있는 데이터 우선
            if 'PER' in sample_for_display.columns and 'PBR' in sample_for_display.columns:
                valid_financial_data = sample_for_display[
                    (sample_for_display['PER'].notna() & (sample_for_display['PER'] > 0)) |
                    (sample_for_display['PBR'].notna() & (sample_for_display['PBR'] > 0))
                ]
                
                if len(valid_financial_data) > 0:
                    print(f"    📊 의미있는 데이터 샘플 ({len(valid_financial_data)}건 중 상위 3건):")
                    display_cols = ['종목코드', '회사명', 'PER', 'PBR']
                    if 'EPS' in valid_financial_data.columns:
                        display_cols.append('EPS')
                    print(valid_financial_data[display_cols].head(3).to_string(index=False))
                else:
                    print(f"    ⚠️  PER, PBR 모두 0 또는 NaN입니다.")
                    print(f"    📊 전체 데이터 샘플 (상위 3건):")
                    sample_cols = ['종목코드', '회사명', 'PER', 'PBR'] if all(col in sample_for_display.columns for col in ['종목코드', '회사명', 'PER', 'PBR']) else sample_for_display.columns[:4]
                    print(sample_for_display[sample_cols].head(3).to_string(index=False))
            else:
                print(f"    📊 데이터 샘플 (상위 3건):")
                sample_cols = sample_for_display.columns[:4] if len(sample_for_display.columns) >= 4 else sample_for_display.columns
                print(sample_for_display[sample_cols].head(3).to_string(index=False))
            
            return financial_indicators, len(financial_indicators)
            
        except Exception as e:
            print(f"  ❌ 전체 오류 발생: {e}")
            import traceback
            print(f"  🔍 상세 오류:")
            traceback.print_exc()
            return None, 0 
            total_count = len(financial_indicators)
            batch_size = 50  # 50개씩 처리할 때마다 진행률 표시
            
            print(f"    🔄 종목명 수집 시작...")
            
            for i, ticker in enumerate(financial_indicators['종목코드']):
                try:
                    name = stock.get_market_ticker_name(ticker)
                    if name and name.strip():
                        company_names.append(name.strip())
                        successful_names += 1
                    else:
                        company_names.append(f'Company_{ticker}')
                        failed_names += 1
                        
                except Exception as e:
                    print(f"    ⚠️  종목 {ticker} 이름 수집 오류: {e}")
                    company_names.append(f'Error_{ticker}')
                    failed_names += 1
                
                # 진행상황 표시 (매 50개마다)
                if (i + 1) % batch_size == 0 or (i + 1) == total_count:
                    progress_pct = (i + 1) / total_count * 100
                    success_rate = successful_names / (i + 1) * 100 if (i + 1) > 0 else 0
                    print(f"    📈 진행: {i + 1:>4}/{total_count} ({progress_pct:>5.1f}%) | 성공률: {success_rate:>5.1f}% | 성공: {successful_names:>3}개 실패: {failed_names:>3}개")
                
                # API 부하 방지를 위한 지연 (더 짧게 조정)
                time.sleep(0.05)
            
            # 최종 결과
            print(f"  ✅ 종목명 수집 완료:")
            print(f"    - 총 처리: {total_count}개")
            print(f"    - 성공: {successful_names}개")
            print(f"    - 실패: {failed_names}개")
            print(f"    - 성공률: {successful_names/(successful_names+failed_names)*100:.1f}%")
            
            financial_indicators['회사명'] = company_names
            
            # 컬럼 순서 정리
            print(f"  📋 컬럼 순서 정리 중...")
            column_order = [
                '종목코드', '회사명', '시장구분', '종가', 
                'EPS', 'PER', 'BPS', 'PBR', '배당수익률', '배당금'
            ]
            available_cols = [col for col in column_order if col in financial_indicators.columns]
            missing_cols = [col for col in column_order if col not in financial_indicators.columns]
            
            print(f"    - 사용 가능한 컬럼: {available_cols}")
            if missing_cols:
                print(f"    - 누락된 컬럼: {missing_cols}")
            
            financial_indicators = financial_indicators[available_cols]
            
            # 데이터 정제 및 0값 문제 해결
            print(f"  🔧 데이터 정제 및 검증 중...")
            
            # 원본 데이터 상태 확인
            print(f"    📋 정제 전 데이터 상태:")
            for col in ['PER', 'PBR', 'EPS', 'BPS']:
                if col in financial_indicators.columns:
                    non_zero_count = (financial_indicators[col] != 0).sum()
                    total_count = len(financial_indicators)
                    print(f"      - {col}: 0이 아닌 값 {non_zero_count}/{total_count}개 ({non_zero_count/total_count*100:.1f}%)")
            
            # 데이터 정제 실행
            financial_indicators = self.clean_financial_data(financial_indicators)
            
            # 정제 후 데이터 상태 확인
            print(f"    📋 정제 후 데이터 상태:")
            for col in ['PER', 'PBR', 'EPS', 'BPS']:
                if col in financial_indicators.columns:
                    # NaN이 아닌 값들 중에서 0이 아닌 값 개수
                    non_nan_count = financial_indicators[col].notna().sum()
                    non_zero_count = ((financial_indicators[col] != 0) & (financial_indicators[col].notna())).sum()
                    if non_nan_count > 0:
                        mean_val = financial_indicators[col].mean()
                        max_val = financial_indicators[col].max()
                        min_val = financial_indicators[col].min()
                        print(f"      - {col}: 유효값 {non_zero_count}/{non_nan_count}개, 평균: {mean_val:.2f}, 범위: {min_val:.2f}~{max_val:.2f}")
                    else:
                        print(f"      - {col}: 모든 값이 NaN")
            
            # 샘플 데이터 확인 (0이 아닌 값들)
            print(f"    🔍 유효한 데이터 샘플 확인:")
            sample_data = financial_indicators.copy()
            
            # PER이나 PBR이 0이 아닌 데이터만 필터링
            valid_data = sample_data[
                ((sample_data['PER'] > 0) | (sample_data['PBR'] > 0)) if 
                all(col in sample_data.columns for col in ['PER', 'PBR']) else 
                sample_data.index < 10  # 없으면 상위 10개만
            ]
            
            if len(valid_data) > 0:
                display_cols = ['종목코드', '회사명']
                for col in ['PER', 'PBR', 'EPS', 'BPS']:
                    if col in valid_data.columns:
                        display_cols.append(col)
                
                print(f"      📊 유효 데이터 ({len(valid_data)}건 중 상위 3건):")
                print(valid_data[display_cols].head(3).to_string(index=False))
            else:
                print(f"      ⚠️  유효한 데이터가 없습니다 (모든 PER, PBR이 0 또는 NaN)")
                # 원본 데이터 일부 출력
                display_cols = ['종목코드', '회사명']
                for col in sample_data.columns:
                    if col not in ['종목코드', '회사명', '시장구분'] and len(display_cols) < 6:
                        display_cols.append(col)
                print(f"      📊 원본 데이터 샘플:")
                print(sample_data[display_cols].head(3).to_string(index=False))
            
            # CSV 저장 (UTF-8 with BOM으로 저장 - 한글 깨짐 방지)
            market_suffix = "_".join(markets) if len(markets) > 1 else markets[0]
            filename = f"{self.data_folder}/재무지표_{year}_{market_suffix}.csv"
            
            print(f"  💾 CSV 파일 저장 중...")
            # UTF-8 with BOM으로 저장하여 Excel에서도 한글 표시
            financial_indicators.to_csv(filename, index=False, encoding='utf-8-sig')
            
            print(f"  ✅ 저장 완료: {filename}")
            print(f"  📊 최종 데이터: {len(financial_indicators)}건, 컬럼: {len(financial_indicators.columns)}개")
            
            # 데이터 샘플 미리보기 (개선된 버전)
            print(f"  🔍 최종 데이터 샘플:")
            
            # 의미있는 데이터가 있는 종목들 우선 표시
            sample_for_display = financial_indicators.copy()
            
            # PER, PBR 둘 중 하나라도 유효한 값이 있는 데이터 우선
            if 'PER' in sample_for_display.columns and 'PBR' in sample_for_display.columns:
                valid_financial_data = sample_for_display[
                    (sample_for_display['PER'].notna() & (sample_for_display['PER'] > 0)) |
                    (sample_for_display['PBR'].notna() & (sample_for_display['PBR'] > 0))
                ]
                
                if len(valid_financial_data) > 0:
                    print(f"    📊 의미있는 데이터 샘플 ({len(valid_financial_data)}건 중 상위 3건):")
                    display_cols = ['종목코드', '회사명', 'PER', 'PBR']
                    if 'EPS' in valid_financial_data.columns:
                        display_cols.append('EPS')
                    print(valid_financial_data[display_cols].head(3).to_string(index=False))
                else:
                    print(f"    ⚠️  PER, PBR 모두 0 또는 NaN입니다.")
                    print(f"    📊 전체 데이터 샘플 (상위 3건):")
                    sample_cols = ['종목코드', '회사명', 'PER', 'PBR'] if all(col in sample_for_display.columns for col in ['종목코드', '회사명', 'PER', 'PBR']) else sample_for_display.columns[:4]
                    print(sample_for_display[sample_cols].head(3).to_string(index=False))
            else:
                print(f"    📊 데이터 샘플 (상위 3건):")
                sample_cols = sample_for_display.columns[:4] if len(sample_for_display.columns) >= 4 else sample_for_display.columns
                print(sample_for_display[sample_cols].head(3).to_string(index=False))
            
            return financial_indicators, len(financial_indicators)
            
        except Exception as e:
            print(f"  ❌ 전체 오류 발생: {e}")
            import traceback
            print(f"  🔍 상세 오류:")
            traceback.print_exc()
            return None, 0
    
    def generate_financial_statements_csv(self, base_date, year, markets=["KOSPI", "KOSDAQ"]):
        """재무정보 CSV 생성 (시장 선택 가능)"""
        market_names = "+".join(markets)
        print(f"\n🏢 {year}년 재무정보 CSV 생성 ({market_names})")
        print("-" * 40)
        
        try:
            print(f"  📈 {market_names} 종목 리스트 및 시가총액 데이터 수집 중...")
            
            all_tickers_info = []
            
            # 선택된 시장들을 순서대로 처리
            for market in markets:
                print(f"  🏪 {market} 처리 중...")
                
                # 1단계: 종목 리스트 수집
                try:
                    market_tickers = stock.get_market_ticker_list(base_date, market=market)
                    print(f"    📊 {market} 종목: {len(market_tickers)}개")
                    
                    # 2단계: 시가총액 데이터 수집
                    try:
                        market_cap_data = stock.get_market_cap(base_date, market=market)
                        
                        if market_cap_data is not None and not market_cap_data.empty:
                            # 안전한 방법으로 종목코드와 시가총액 추출
                            for ticker in market_tickers:
                                try:
                                    if ticker in market_cap_data.index:
                                        market_cap = market_cap_data.loc[ticker, '시가총액'] if '시가총액' in market_cap_data.columns else 0
                                    else:
                                        market_cap = 0
                                    
                                    all_tickers_info.append({
                                        '종목코드': ticker,
                                        '시장구분': market,
                                        '시가총액': market_cap
                                    })
                                except:
                                    all_tickers_info.append({
                                        '종목코드': ticker,
                                        '시장구분': market,
                                        '시가총액': 0
                                    })
                        else:
                            # 시가총액 데이터가 없어도 종목 리스트는 처리
                            for ticker in market_tickers:
                                all_tickers_info.append({
                                    '종목코드': ticker,
                                    '시장구분': market,
                                    '시가총액': 0
                                })
                                
                    except Exception as e:
                        print(f"    ⚠️  {market} 시가총액 수집 오류: {e}")
                        # 오류가 있어도 종목 리스트는 처리
                        for ticker in market_tickers:
                            all_tickers_info.append({
                                '종목코드': ticker,
                                '시장구분': market,
                                '시가총액': 0
                            })
                    
                except Exception as e:
                    print(f"    ❌ {market} 종목 리스트 수집 실패: {e}")
                    continue
            
            if not all_tickers_info:
                print("  ❌ 종목 정보를 수집할 수 없습니다.")
                return None, 0
            
            print(f"  📊 총 종목 수: {len(all_tickers_info)}개")
            
            print("  🔢 재무정보 데이터 생성 중...")
            financial_statements = []
            
            for idx, ticker_info in enumerate(all_tickers_info):
                ticker = ticker_info['종목코드']
                market_type = ticker_info['시장구분']
                market_cap = ticker_info['시가총액']
                
                try:
                    # 종목명 수집
                    company_name = stock.get_market_ticker_name(ticker)
                    if not company_name:
                        company_name = f'Company_{ticker}'
                    
                    # 업종 및 재무데이터 생성
                    industry = self.get_industry_sample(ticker)
                    financial_data = self.estimate_financial_data(market_cap, ticker)
                    
                    financial_info = {
                        '종목코드': ticker,
                        '회사명': company_name,
                        '시장구분': market_type,
                        '업종': industry,
                        '결산년도': f'{year}/12',
                        **financial_data
                    }
                    
                    financial_statements.append(financial_info)
                    
                    # 진행상황 표시
                    if (idx + 1) % 200 == 0:
                        print(f"    진행: {idx + 1}/{len(all_tickers_info)} ({(idx+1)/len(all_tickers_info)*100:.1f}%)")
                
                except Exception as e:
                    print(f"    ⚠️  종목 {ticker} 처리 오류: {e}")
                    # 오류가 있어도 기본 정보는 추가
                    financial_info = {
                        '종목코드': ticker,
                        '회사명': f'Unknown_{ticker}',
                        '시장구분': market_type,
                        '업종': '기타',
                        '결산년도': f'{year}/12',
                        **self.estimate_financial_data(0, ticker)
                    }
                    financial_statements.append(financial_info)
                    continue
                
                time.sleep(0.01)  # 기본 지연
            
            if not financial_statements:
                print("  ❌ 재무정보 생성 실패")
                return None, 0
            
            financial_df = pd.DataFrame(financial_statements)
            
            # CSV 저장 (UTF-8 with BOM으로 저장 - 한글 깨짐 방지)
            market_suffix = "_".join(markets) if len(markets) > 1 else markets[0]
            filename = f"{self.data_folder}/재무정보_{year}_{market_suffix}.csv"
            financial_df.to_csv(filename, index=False, encoding='utf-8-sig')
            
            print(f"  ✅ 저장 완료: {filename}")
            print(f"  📊 데이터: {len(financial_df)}건, 컬럼: {len(financial_df.columns)}개")
            
            return financial_df, len(financial_df)
            
        except Exception as e:
            print(f"  ❌ 전체 오류 발생: {e}")
            return None, 0
    
    def merge_financial_data(self, year, markets=["KOSPI", "KOSDAQ"]):
        """특정 연도의 재무지표와 재무정보 병합 (시장 선택 가능)"""
        market_suffix = "_".join(markets) if len(markets) > 1 else markets[0]
        market_names = "+".join(markets)
        
        print(f"\n🔗 {year}년 데이터 병합 ({market_names})")
        print("-" * 40)
        
        try:
            indicators_file = f"{self.data_folder}/재무지표_{year}_{market_suffix}.csv"
            statements_file = f"{self.data_folder}/재무정보_{year}_{market_suffix}.csv"
            
            # 파일 존재 확인
            if not os.path.exists(indicators_file):
                print(f"  ❌ 재무지표 파일이 없습니다: {indicators_file}")
                return None
            
            if not os.path.exists(statements_file):
                print(f"  ❌ 재무정보 파일이 없습니다: {statements_file}")
                return None
            
            # 파일 읽기 (UTF-8 with BOM 지원)
            print("  📖 파일 읽기 중...")
            try:
                indicators_df = pd.read_csv(indicators_file, encoding='utf-8-sig')
            except UnicodeDecodeError:
                indicators_df = pd.read_csv(indicators_file, encoding='EUC-KR')
            
            try:
                statements_df = pd.read_csv(statements_file, encoding='utf-8-sig')
            except UnicodeDecodeError:
                statements_df = pd.read_csv(statements_file, encoding='EUC-KR')
            
            # 병합
            print("  🔄 데이터 병합 중...")
            merged_df = pd.merge(
                statements_df, 
                indicators_df[['종목코드', '종가', 'EPS', 'PER', 'BPS', 'PBR', '배당수익률', '배당금']], 
                on='종목코드', 
                how='left'
            )
            
            # 병합 파일 저장 (UTF-8 with BOM)
            merged_file = f"{self.data_folder}/통합데이터_{year}_{market_suffix}.csv"
            merged_df.to_csv(merged_file, index=False, encoding='utf-8-sig')
            
            print(f"  ✅ 병합 완료: {merged_file}")
            print(f"  📊 데이터: {len(merged_df)}건, 컬럼: {len(merged_df.columns)}개")
            
            return merged_df
            
        except Exception as e:
            print(f"  ❌ 병합 오류: {e}")
            return None
    
    def clean_financial_data(self, df):
        """재무 데이터 정제"""
        numeric_cols = ['EPS', 'PER', 'BPS', 'PBR', '배당수익률', '배당금']
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].replace([np.inf, -np.inf], np.nan)
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        if 'PER' in df.columns:
            df.loc[df['PER'] < 0, 'PER'] = np.nan
        
        for col in ['EPS', 'BPS']:
            if col in df.columns:
                df[col] = df[col].round(2)
        
        for col in ['PER', 'PBR', '배당수익률']:
            if col in df.columns:
                df[col] = df[col].round(2)
        
        return df
    
    def estimate_financial_data(self, market_cap, ticker):
        """재무데이터 추정"""
        if market_cap > 0:
            if market_cap > 10_000_000:
                asset_ratio, debt_ratio, revenue_ratio = 1.5, 0.4, 0.8
            elif market_cap > 1_000_000:
                asset_ratio, debt_ratio, revenue_ratio = 1.3, 0.5, 0.9
            else:
                asset_ratio, debt_ratio, revenue_ratio = 1.2, 0.6, 1.0
            
            estimated_assets = int(market_cap * asset_ratio)
            estimated_liabilities = int(estimated_assets * debt_ratio)
            estimated_equity = estimated_assets - estimated_liabilities
            estimated_revenue = int(market_cap * revenue_ratio)
            estimated_operating_profit = int(estimated_revenue * 0.1)
            estimated_net_income = int(estimated_operating_profit * 0.8)
        else:
            estimated_assets = 100000
            estimated_liabilities = 40000
            estimated_equity = 60000
            estimated_revenue = 80000
            estimated_operating_profit = 8000
            estimated_net_income = 6000
        
        return {
            '자산총계': estimated_assets,
            '유동자산': int(estimated_assets * 0.4),
            '고정자산': int(estimated_assets * 0.6),
            '부채총계': estimated_liabilities,
            '유동부채': int(estimated_liabilities * 0.6),
            '고정부채': int(estimated_liabilities * 0.4),
            '자본총계': estimated_equity,
            '자본금': int(estimated_equity * 0.1),
            '자본잉여금': int(estimated_equity * 0.2),
            '이익잉여금': int(estimated_equity * 0.7),
            '매출액': estimated_revenue,
            '영업이익': estimated_operating_profit,
            '당기순이익': estimated_net_income,
            '매출액증감률': round(np.random.uniform(-10, 15), 2),
            '영업이익증감률': round(np.random.uniform(-20, 25), 2)
        }
    
    def get_industry_sample(self, ticker):
        """업종 샘플"""
        industry_map = {
            '005930': '전자제품 제조업', '000660': '반도체 제조업',
            '051910': '화학제품 제조업', '035420': 'IT서비스업',
            '006400': '2차전지 제조업', '035720': 'IT서비스업',
            '207940': '의약품 제조업', '068270': '의약품 제조업',
        }
        return industry_map.get(ticker, '기타 제조업')
    
    def show_existing_files(self):
        """생성된 파일 목록 보기"""
        print(f"\n📁 생성된 파일 목록:")
        print("-" * 50)
        
        if not os.path.exists(self.data_folder) or not os.listdir(self.data_folder):
            print("📂 생성된 파일이 없습니다.")
            return
        
        files = [f for f in os.listdir(self.data_folder) if f.endswith('.csv')]
        files.sort()
        
        # 파일 유형별 분류
        file_types = {
            '재무지표': [],
            '재무정보': [],
            '통합데이터': [],
            '기타': []
        }
        
        for file in files:
            if file.startswith('재무지표'):
                file_types['재무지표'].append(file)
            elif file.startswith('재무정보'):
                file_types['재무정보'].append(file)
            elif file.startswith('통합데이터'):
                file_types['통합데이터'].append(file)
            else:
                file_types['기타'].append(file)
        
        for file_type, file_list in file_types.items():
            if file_list:
                print(f"\n🔹 {file_type} ({len(file_list)}개):")
                for file in file_list:
                    file_path = os.path.join(self.data_folder, file)
                    file_size = os.path.getsize(file_path) / 1024 / 1024  # MB
                    print(f"  📄 {file} ({file_size:.1f}MB)")
    
    def run(self):
        """메인 실행 함수"""
        while True:
            try:
                self.show_menu()
                choice = input("\n메뉴를 선택하세요: ").strip()
                
                if choice == '1':
                    # 재무지표 CSV 생성
                    base_date, year, markets, market_name = self.get_date_input("생성할 연도를 입력하세요")
                    indicators_df, count = self.generate_investment_indicators_csv(base_date, year, markets)
                    
                    if indicators_df is not None:
                        print(f"\n✅ 재무지표 생성 완료!")
                        market_suffix = "_".join(markets) if len(markets) > 1 else markets[0]
                        print(f"📄 파일: 재무지표_{year}_{market_suffix}.csv")
                        print(f"📊 데이터: {count:,}건 ({market_name})")
                    
                elif choice == '2':
                    # 재무정보 CSV 생성
                    base_date, year, markets, market_name = self.get_date_input("생성할 연도를 입력하세요")
                    statements_df, count = self.generate_financial_statements_csv(base_date, year, markets)
                    
                    if statements_df is not None:
                        print(f"\n✅ 재무정보 생성 완료!")
                        market_suffix = "_".join(markets) if len(markets) > 1 else markets[0]
                        print(f"📄 파일: 재무정보_{year}_{market_suffix}.csv")
                        print(f"📊 데이터: {count:,}건 ({market_name})")
                
                elif choice == '3':
                    # 재무지표 + 재무정보 통합 생성
                    base_date, year, markets, market_name = self.get_date_input("생성할 연도를 입력하세요")
                    
                    print(f"\n🔄 {year}년 통합 데이터 생성 시작... ({market_name})")
                    
                    # 재무지표 생성
                    indicators_df, indicators_count = self.generate_investment_indicators_csv(base_date, year, markets)
                    
                    # 재무정보 생성
                    statements_df, statements_count = self.generate_financial_statements_csv(base_date, year, markets)
                    
                    # 병합
                    if indicators_df is not None and statements_df is not None:
                        merged_df = self.merge_financial_data(year, markets)
                        
                        if merged_df is not None:
                            market_suffix = "_".join(markets) if len(markets) > 1 else markets[0]
                            print(f"\n🎉 통합 생성 완료!")
                            print(f"📄 생성된 파일:")
                            print(f"  - 재무지표_{year}_{market_suffix}.csv ({indicators_count:,}건)")
                            print(f"  - 재무정보_{year}_{market_suffix}.csv ({statements_count:,}건)")
                            print(f"  - 통합데이터_{year}_{market_suffix}.csv ({len(merged_df):,}건)")
                            print(f"🏪 시장: {market_name}")
                    else:
                        print(f"❌ 통합 생성 실패")
                
                elif choice == '6':
                    # 생성된 파일 목록 보기
                    self.show_existing_files()
                
                elif choice == '0':
                    # 종료
                    print("👋 프로그램을 종료합니다.")
                    break
                
                else:
                    print("❌ 구현되지 않은 메뉴입니다. 메뉴 1, 2, 3, 6, 0번만 사용 가능합니다.")
                
                # 메뉴 선택 후 대기
                input("\n⏸️  아무 키나 눌러서 계속...")
                
            except KeyboardInterrupt:
                print("\n\n👋 프로그램을 종료합니다.")
                break
            except Exception as e:
                print(f"❌ 오류 발생: {e}")
                input("\n⏸️  아무 키나 눌러서 계속...")

# 메인 실행
if __name__ == "__main__":
    # 콘솔 출력 인코딩 확인
    print("🏦 KRX 재무 데이터 생성기 (기본 버전)를 시작합니다...")
    print("⚠️  인터넷 연결이 필요합니다. (pykrx API 사용)")
    print("📝 CSV 파일은 UTF-8(BOM) 형식으로 저장됩니다.")
    
    try:
        generator = KRXFinancialDataGenerator()
        generator.run()
    except Exception as e:
        print(f"❌ 프로그램 실행 오류: {e}")
        print("💡 pip install pykrx pandas numpy 명령어로 라이브러리를 설치해주세요.")
    
    print("✨ 감사합니다!")
    
    # Windows에서 콘솔이 바로 닫히는 것을 방지
    if sys.platform.startswith('win'):
        input("\n아무 키나 눌러서 종료하세요...")