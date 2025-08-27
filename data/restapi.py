# file: data/restapi.py
# 키움증권 REST API 연동 모듈

import requests
import json
import pandas as pd
from dotenv import load_dotenv
import os
from datetime import datetime
from pathlib import Path

# .env.local 파일에서 환경 변수 로드
load_dotenv('.env.local')

# 환경 변수에서 appkey, secretkey, 저장 경로 가져오기
APPKEY = os.getenv('KIWOOM_APPKEY')
SECRETKEY = os.getenv('KIWOOM_SECRETKEY')
CSV_SAVE_PATH = os.getenv('CSV_SAVE_PATH', 'data')  # 기본값은 'data' 디렉토리

# CSV 저장 디렉토리 생성
def ensure_directory(save_path):
    """지정된 경로가 없으면 디렉토리를 생성"""
    path = Path(save_path)
    path.mkdir(parents=True, exist_ok=True)
    return path

# 토큰 발급 함수
def fn_au10001():
    # 1. 요청할 API URL
    host = 'https://api.kiwoom.com'  # 실전투자
    endpoint = '/oauth2/token'
    url = host + endpoint

    # 2. 요청 데이터
    data = {
        'grant_type': 'client_credentials',
        'appkey': APPKEY,
        'secretkey': SECRETKEY
    }

    # 3. 헤더 데이터
    headers = {
        'Content-Type': 'application/json;charset=UTF-8'
    }

    # 4. HTTP POST 요청
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # HTTP 오류 발생 시 예외 처리
        print('Token Request - Code:', response.status_code)
        print('Token Request - Header:', json.dumps({key: response.headers.get(key) for key in ['next-key', 'cont-yn', 'api-id']}, indent=4, ensure_ascii=False))
        print('Token Request - Body:', json.dumps(response.json(), indent=4, ensure_ascii=False))
        # 'token' 키를 사용하여 토큰 추출
        return response.json().get('token')
    except requests.RequestException as e:
        print(f"Token Request Failed: {e}")
        return None

# 일별 주가 요청 함수
def fn_ka10086(token, data, cont_yn='N', next_key=''):
    # 1. 요청할 API URL
    host = 'https://api.kiwoom.com'  # 실전투자
    endpoint = '/api/dostk/mrkcond'
    url = host + endpoint

    # 2. 헤더 데이터
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': cont_yn,
        'next-key': next_key,
        'api-id': 'ka10086'
    }

    # 3. HTTP POST 요청
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # HTTP 오류 발생 시 예외 처리
        print('Stock Data Request - Code:', response.status_code)
        print('Stock Data Request - Header:', json.dumps({key: response.headers.get(key) for key in ['next-key', 'cont-yn', 'api-id']}, indent=4, ensure_ascii=False))
        print('Stock Data Request - Body:', json.dumps(response.json(), indent=4, ensure_ascii=False))
        return response.json()
    except requests.RequestException as e:
        print(f"Stock Data Request Failed: {e}")
        return None

# 주가 데이터를 CSV로 저장하는 함수
def save_to_csv(data, filename, save_path=CSV_SAVE_PATH):
    try:
        # 저장 경로 확인 및 생성
        save_dir = ensure_directory(save_path)
        full_path = save_dir / filename

        # API 응답 데이터 디버깅 출력
        print("Debug - API Response Structure:", json.dumps(data, indent=4, ensure_ascii=False))

        # 'daly_stkpc' 키 아래 리스트 데이터 확인
        if 'daly_stkpc' in data and isinstance(data['daly_stkpc'], list):
            df = pd.DataFrame(data['daly_stkpc'])
            # 숫자 필드에서 '+' 또는 '-' 접두어 제거 및 숫자로 변환 (필요 시)
            for col in ['open_pric', 'high_pric', 'low_pric', 'close_pric', 'pred_rt', 'flu_rt', 'trde_qty', 'amt_mn', 'crd_rt', 'ind', 'orgn', 'for_qty', 'frgn', 'prm', 'for_rt', 'for_poss', 'for_wght', 'for_netprps', 'orgn_netprps', 'ind_netprps', 'crd_remn_rt']:
                if col in df.columns:
                    df[col] = df[col].replace(r'[\+\-]', '', regex=True).replace('', '0').astype(float)
            df.to_csv(full_path, index=False, encoding='utf-8')
            print(f"Data saved to {full_path}")
        else:
            print("No valid list data found in 'daly_stkpc'. Check API response structure.")
    except Exception as e:
        print(f"Error saving to CSV: {e}")

# 실행 구간
if __name__ == '__main__':
    # 1. 토큰 발급
    access_token = fn_au10001()
    if not access_token:
        print("Failed to obtain access token. Exiting...")
        exit()

    # 2. 요청 데이터 (삼성전자, 동적 날짜)
    current_date = datetime.now().strftime('%Y%m%d')  # 현재 날짜를 YYYYMMDD 형식으로 설정
    params = {
        'stk_cd': '005930',  # 삼성전자 종목코드
        'qry_dt': current_date,  # 동적으로 설정된 조회일자
        'indc_tp': '0'  # 수량 기준
    }

    # 3. 일별 주가 요청
    stock_data = fn_ka10086(token=access_token, data=params)
    if stock_data:
        # 4. 데이터를 CSV로 저장 (파일명에 날짜 포함)
        csv_filename = f'samsung_stock_{current_date}.csv'
        save_to_csv(stock_data, filename=csv_filename)

        # 5. 연속 조회 처리 (next-key가 있는 경우)
        while stock_data.get('cont_yn') == 'Y' and stock_data.get('next_key'):
            stock_data = fn_ka10086(
                token=access_token,
                data=params,
                cont_yn='Y',
                next_key=stock_data.get('next_key')
            )
            if stock_data:
                csv_filename = f'samsung_stock_{current_date}_cont_{stock_data.get("next_key")}.csv'
                save_to_csv(stock_data, filename=csv_filename)

                