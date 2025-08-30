# KIS 실시간 퀀트 전략 시스템

한국투자증권 OpenAPI를 활용한 실시간 주식 거래 전략 시스템입니다.

## 주요 기능

- **실시간 시세 모니터링**: WebSocket을 통한 실시간 주식 데이터 수신
- **다중 전략 지원**: 모멘텀, 역모멘텀, 스캘핑 전략 동시 실행
- **기술적 지표**: RSI, 이동평균, 볼린저밴드, MACD 실시간 계산
- **환경 분리**: 모의투자/실전투자 환경 선택 가능
- **자동 재연결**: 네트워크 오류 시 자동 재연결
- **포지션 관리**: 실시간 포지션 추적 및 손익 계산
- **백테스팅**: 과거 데이터를 이용한 전략 성과 검증

## 설치 방법

### 1. 저장소 클론
```bash
git clone <repository-url>
cd quant_backend
```

### 2. 가상환경 생성 (권장)
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. 패키지 설치
```bash
pip install -r requirements.txt
```

### 4. 환경 설정
```bash
# .env 파일 생성
cp .env.template .env
# .env 파일을 편집하여 API 키 입력
```

## API 키 발급 방법

1. [한국투자증권 OpenAPI 포털](https://apiportal.koreainvestment.com) 접속
2. 회원가입 및 로그인
3. API 신청서 작성 (모의투자용 또는 실전투자용)
4. 승인 후 앱키(APP KEY)와 앱시크릿(APP SECRET) 발급
5. .env 파일에 발급받은 키와 계좌번호 입력

## 사용 방법

### 기본 실행 (대화형 환경 선택)
```bash
python app/main.py
```

### 모의투자 환경으로 자동 실행
```bash
python app/main.py --env mock
```

### 실전투자 환경으로 자동 실행 (주의!)
```bash
python app/main.py --env real
```

### 특정 종목 모니터링
```bash
python app/main.py --stocks 005930 000660 035720
```

### 자동 거래 실행 모드
```bash
python app/main.py --env mock --auto-execute
```

## 실행 중 명령어

시스템 실행 후 다음 명령어를 사용할 수 있습니다:

- `status` - 시스템 연결 상태 확인
- `chart` - 실시간 차트 상태 확인
- `add` - 새로운 종목 모니터링 추가
- `switch` - 환경 변경 (모의투자 ↔ 실전투자)
- `quit` - 시스템 종료

## 프로젝트 구조

```
quant_backend/
├── app/
│   ├── main.py                 # 메인 실행 파일
│   ├── config.py              # 환경 설정 관리
│   ├── services/
│   │   ├── kis_auth.py        # KIS API 인증
│   │   ├── kis_websocket.py   # 실시간 WebSocket 클라이언트
│   │   ├── kis_api.py         # REST API 클라이언트
│   │   ├── data_processor.py  # 실시간 데이터 처리
│   │   └── trading_strategy.py # 거래 전략 실행
│   └── utils/
├── requirements.txt           # 필요 패키지 목록
├── .env.template             # 환경 변수 템플릿
└── README.md                 # 이 파일
```

## 전략 설명

### 1. 모멘텀 전략
- RSI가 과매도/과매수 구간에서 급격한 가격 변동과 거래량 증가 시 신호 발생
- 상승 모멘텀 포착하여 추세 추종

### 2. 역모멘텀 전략
- 볼린저밴드 상/하단 터치 후 반전 신호 포착
- 과도한 상승/하락 후 되돌림 현상 활용

### 3. 스캘핑 전략
- 짧은 시간 내 활발한 거래량과 빠른 가격 변동 활용
- 소액 다회 거래로 수익 추구

## 위험 관리

- **손절매**: 설정된 손실 비율 도달 시 자동 청산
- **익절매**: 목표 수익률 달성 시 자동 청산
- **포지션 제한**: 최대 보유 금액 제한
- **일일 손실 제한**: 하루 최대 손실액 제한

## 주의사항

1. **실전투자 주의**: 실전투자 환경에서는 실제 자금이 거래됩니다
2. **API 제한**: KIS API 호출 제한(분당 20회, 일일 10,000회)을 준수합니다
3. **시장 시간**: 주식 시장 개장 시간에만 실시간 데이터를 받을 수 있습니다
4. **네트워크 안정성**: 안정한 인터넷 연결이 필요합니다

## 문제 해결

### 연결 오류
- API 키와 계좌번호가 올바른지 확인
- 네트워크 연결 상태 확인
- 한국투자증권 API 서버 상태 확인

### 토큰 오류
- 시스템이 자동으로 토큰을 갱신합니다
- 지속적인 오류 시 API 키 재발급 필요

### 데이터 수신 오류
- WebSocket 연결이 자동으로 재연결됩니다
- 지속적인 문제 시 시스템 재시작

## 로그 확인

시스템 실행 로그는 `kis_quant.log` 파일에 저장됩니다:

```bash
tail -f kis_quant.log
```

## 설정 확인 도구

환경 설정이 올바른지 확인하려면:

```bash
python app/config.py
```

## 라이선스

이 프로젝트는 교육 및 연구 목적으로 제작되었습니다. 실제 투자 시 발생하는 손실에 대해서는 책임지지 않습니다.

## 기술 지원

- KIS OpenAPI 문서: https://apiportal.koreainvestment.com
- 기술적 문의: 한국투자증권 OpenAPI 고객센터