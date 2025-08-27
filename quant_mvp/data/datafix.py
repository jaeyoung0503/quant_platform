"""
데이터 로딩 문제 해결 가이드
"""

import os
import pandas as pd
from pathlib import Path

def diagnose_data_files():
    """데이터 파일 상태 진단"""
    
    print("🔍 데이터 파일 진단 시작...")
    
    # 1. 데이터 폴더 확인
    data_folders = ['data', 'data/raw', 'data/processed', 'data/stock_data']
    
    for folder in data_folders:
        if os.path.exists(folder):
            print(f"✅ {folder} 폴더 존재")
            files = os.listdir(folder)
            print(f"   파일 목록: {files}")
            
            # CSV 파일들 상세 검사
            for file in files:
                if file.endswith('.csv'):
                    file_path = os.path.join(folder, file)
                    check_csv_file(file_path)
        else:
            print(f"❌ {folder} 폴더 없음")

def check_csv_file(file_path: str):
    """CSV 파일 상세 검사"""
    try:
        print(f"\n📄 파일 검사: {file_path}")
        
        # 파일 크기 확인
        file_size = os.path.getsize(file_path)
        print(f"   파일 크기: {file_size} bytes")
        
        if file_size == 0:
            print("   ⚠️ 빈 파일입니다!")
            return
        
        # 첫 몇 줄 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            first_lines = [f.readline().strip() for _ in range(5)]
            print(f"   첫 5줄:")
            for i, line in enumerate(first_lines, 1):
                if line:
                    print(f"     {i}: {line[:100]}...")  # 첫 100자만
                else:
                    print(f"     {i}: (빈 줄)")
        
        # pandas로 읽기 시도
        try:
            df = pd.read_csv(file_path, nrows=5)
            print(f"   ✅ pandas 읽기 성공")
            print(f"   컬럼: {list(df.columns)}")
            print(f"   형태: {df.shape}")
        except Exception as e:
            print(f"   ❌ pandas 읽기 실패: {e}")
            
            # 다른 구분자로 시도
            separators = [',', ';', '\t', '|']
            for sep in separators:
                try:
                    df = pd.read_csv(file_path, sep=sep, nrows=5)
                    print(f"   ✅ 구분자 '{sep}'로 읽기 성공")
                    print(f"   컬럼: {list(df.columns)}")
                    break
                except:
                    continue
    
    except Exception as e:
        print(f"   ❌ 파일 검사 실패: {e}")

def create_sample_data():
    """샘플 데이터 생성"""
    print("\n🔧 샘플 데이터 생성...")
    
    # data 폴더 생성
    os.makedirs('data', exist_ok=True)
    
    # 샘플 주식 데이터 생성
    import numpy as np
    from datetime import datetime, timedelta
    
    # 날짜 범위 생성
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2023, 12, 31)
    dates = pd.date_range(start_date, end_date, freq='D')
    
    # 샘플 주식들
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']
    
    for symbol in symbols:
        print(f"   📊 {symbol} 데이터 생성 중...")
        
        # 랜덤 가격 데이터 생성
        np.random.seed(42)  # 재현 가능한 결과를 위해
        
        price_data = []
        current_price = 100.0
        
        for date in dates:
            # 랜덤 워크로 가격 생성
            change = np.random.normal(0, 0.02)  # 평균 0, 표준편차 2%
            current_price *= (1 + change)
            
            # 거래량은 랜덤하게
            volume = np.random.randint(1000000, 10000000)
            
            price_data.append({
                'Date': date.strftime('%Y-%m-%d'),
                'Open': round(current_price * 0.99, 2),
                'High': round(current_price * 1.02, 2),
                'Low': round(current_price * 0.98, 2),
                'Close': round(current_price, 2),
                'Volume': volume,
                'Symbol': symbol
            })
        
        # CSV 파일로 저장
        df = pd.DataFrame(price_data)
        file_path = f'data/{symbol}.csv'
        df.to_csv(file_path, index=False)
        print(f"   ✅ {file_path} 저장 완료 ({len(df)} 행)")
    
    # 통합 파일도 생성
    all_data = []
    for symbol in symbols:
        df = pd.read_csv(f'data/{symbol}.csv')
        all_data.append(df)
    
    combined_df = pd.concat(all_data, ignore_index=True)
    combined_df.to_csv('data/stock_data.csv', index=False)
    print(f"   ✅ data/stock_data.csv 저장 완료 ({len(combined_df)} 행)")

def fix_config_file():
    """config.yaml 파일에서 데이터 경로 확인 및 수정"""
    config_files = ['config.yaml', 'config.yml', 'config/config.yaml']
    
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"\n⚙️ {config_file} 설정 확인...")
            
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print("   현재 설정:")
                # 데이터 관련 설정 찾기
                for line in content.split('\n'):
                    if 'data' in line.lower() or 'path' in line.lower():
                        print(f"     {line}")
            
            # 권장 설정
            print("\n   권장 설정:")
            recommended_config = """
data:
  source: "local"  # 또는 "yahoo", "alpha_vantage"
  local_path: "data/"
  file_format: "csv"
  symbols: ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
            """
            print(recommended_config)
            
            break
    else:
        print("\n❌ config 파일을 찾을 수 없습니다.")

# 실행 함수들
if __name__ == "__main__":
    print("🔧 데이터 문제 해결 도구")
    print("="*50)
    
    # 1. 진단
    diagnose_data_files()
    
    # 2. 샘플 데이터 생성 여부 묻기
    response = input("\n샘플 데이터를 생성하시겠습니까? (y/n): ")
    if response.lower() == 'y':
        create_sample_data()
    
    # 3. 설정 파일 확인
    fix_config_file()
    
    print("\n✅ 진단 완료!")
    print("이제 python main.py를 다시 실행해보세요.")