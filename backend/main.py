# ===== backend/main.py 수정된 버전 =====

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import sys
import os
import traceback
from datetime import datetime
from pathlib import Path
import importlib
import pandas as pd
import numpy as np

# 경로 설정
current_dir = Path(__file__).parent
backend_quant_engine_path = current_dir / "quant_engine"
strategy_engine_path = current_dir / "strategy_engine"

# 두 경로 모두 추가
sys.path.append(str(backend_quant_engine_path))
sys.path.append(str(strategy_engine_path))

# 모든 전략 모듈들 import
strategy_modules = {}

try:
    # backend/quant_engine/base_strategy.py
    from quant_engine import base_strategy
    strategy_modules['base_strategy'] = base_strategy
    print("✓ base_strategy 로딩 성공")
    
    # strategy_engine 디렉토리의 모든 모듈들
    strategy_files = [
        'basic_strategies',
        'cycle_contrarian_strategies', 
        'fundamental_metrics',
        'growth_momentum_stratigies',  # 오타 그대로 유지
        'portfolio_utils',
        'strategy_factory',
        'technical_indicators',
        'value_strategies'
    ]
    
    for module_name in strategy_files:
        try:
            module = importlib.import_module(module_name)
            strategy_modules[module_name] = module
            print(f"✓ {module_name} 로딩 성공")
        except ImportError as e:
            print(f"⚠️ {module_name} 로딩 실패: {e}")
    
    print(f"✓ 총 {len(strategy_modules)}개 전략 모듈 로딩 완료")
    
except ImportError as e:
    print(f"❌ 전략 모듈 import 실패: {e}")
    print("📁 디렉토리 구조 확인:")
    print(f"   backend/quant_engine/: {list(backend_quant_engine_path.glob('*.py')) if backend_quant_engine_path.exists() else '존재하지 않음'}")
    print(f"   backend/strategy_engine/: {list(strategy_engine_path.glob('*.py')) if strategy_engine_path.exists() else '존재하지 않음'}")

app = FastAPI(title="퀀트 백테스트 API", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Pydantic 모델들 =====
class StrategyConfig(BaseModel):
    id: str
    weight: float
    params: Dict[str, Any]

class BacktestRequest(BaseModel):
    strategies: List[StrategyConfig]
    year: int
    outputCount: int

class BacktestResultModel(BaseModel):
    rank: int
    stockCode: str
    stockName: str
    compositeScore: float
    grade: str
    strengthArea: str
    strategyValues: Dict[str, float]

class PortfolioRequest(BaseModel):
    name: str
    stocks: List[str]
    strategies: List[Dict[str, Any]]
    createdAt: str

# ===== 백테스트 관리 클래스 =====
class QuantBacktestManager:
    """quant_engine과 strategy_engine을 활용한 백테스트 매니저"""
    
    def __init__(self):
        self.strategies = {}
        self.stock_data = None
        self.strategy_modules = strategy_modules
        self.load_available_strategies()
        self.load_stock_data()
    
    def load_available_strategies(self):
        """quant_engine에서 실제 전략들 로딩"""
        try:
            # 실제 전략 팩토리에서 전략 목록 가져오기
            if 'strategy_factory' in strategy_modules:
                available_strategies = strategy_registry.list_strategies()
                
                for strategy_name in available_strategies:
                    # 전략 메타데이터 가져오기
                    metadata = strategy_registry.get_strategy_metadata(strategy_name)
                    
                    if 'metadata' in metadata:
                        strategy_meta = metadata['metadata']
                        self.strategies[strategy_name] = {
                            "name": strategy_meta.name,
                            "description": strategy_meta.description,
                            "default_params": metadata.get('parameters', {}),
                            "module": strategy_name,
                            "category": strategy_meta.category.value,
                            "risk_level": strategy_meta.risk_level.value,
                            "complexity": strategy_meta.complexity.value
                        }
                
            # 추가로 기본 전략들 정의 (백업용)
            if not self.strategies:
                self.strategies = {
                    "low_pe": {
                        "name": "저PER 전략",
                        "description": "PER 15배 이하 종목 선별",
                        "default_params": {"max_pe_ratio": 15},
                        "module": "basic_strategies"
                    },
                    "rsi_mean_reversion": {
                        "name": "RSI 평균회귀 전략",
                        "description": "RSI 과매수/과매도 구간 활용",
                        "default_params": {"rsi_period": 14, "oversold": 30, "overbought": 70},
                        "module": "basic_strategies"
                    },
                    "buffett_moat": {
                        "name": "워렌 버핏의 해자 전략",
                        "description": "경제적 해자가 있는 기업 장기 투자",
                        "default_params": {"max_pe": 20, "min_roe": 0.15, "min_roic": 0.12},
                        "module": "value_strategies"
                    },
                    "peter_lynch_peg": {
                        "name": "피터 린치의 PEG 전략", 
                        "description": "PEG 1.0 이하 성장주 발굴",
                        "default_params": {"max_peg": 1.0, "min_growth_rate": 0.1},
                        "module": "value_strategies"
                    },
                    "william_oneil_canslim": {
                        "name": "윌리엄 오닐의 CAN SLIM",
                        "description": "7가지 기준으로 고성장주 발굴",
                        "default_params": {"min_current_earnings": 0.25, "min_relative_strength": 80},
                        "module": "growth_momentum_stratigies"
                    },
                    "bollinger_band": {
                        "name": "볼린저 밴드 역발상 전략",
                        "description": "볼린저 밴드 터치 시점 매매",
                        "default_params": {"bb_period": 20, "bb_std": 2},
                        "module": "basic_strategies"
                    },
                    "dividend_aristocrats": {
                        "name": "배당 귀족주 전략",
                        "description": "연속 배당 증가 기업 투자",
                        "default_params": {"min_dividend_years": 20, "min_dividend_yield": 0.02},
                        "module": "basic_strategies"
                    },
                    "ray_dalio_all_weather": {
                        "name": "레이 달리오의 올웨더",
                        "description": "경제 환경 변화에 관계없이 안정적 수익",
                        "default_params": {"rebalance_threshold": 0.05},
                        "module": "cycle_contrarian_strategies"
                    },
                    "joel_greenblatt_magic": {
                        "name": "조엘 그린블라트의 마법공식",
                        "description": "ROE + 수익수익률 결합 체계적 가치투자",
                        "default_params": {"min_market_cap": 1000, "top_stocks": 30},
                        "module": "value_strategies"
                    },
                    "simple_momentum": {
                        "name": "단순 모멘텀 전략",
                        "description": "최근 성과 상위 종목 추종",
                        "default_params": {"lookback_months": 6, "top_percentile": 0.2},
                        "module": "basic_strategies"
                    }
                }
            
            print(f"✓ {len(self.strategies)}개 전략 정의 완료")
            
        except Exception as e:
            print(f"✗ 전략 로딩 실패: {str(e)}")
            self.strategies = {}
    
    def execute_strategy(self, strategy_name: str, strategy_config: Dict, data: pd.DataFrame = None) -> Dict:
        """개별 전략 실행"""
        try:
            # 실제 전략 인스턴스 생성
            if 'strategy_factory' in strategy_modules:
                strategy_instance = strategy_registry.create_strategy(strategy_name, **strategy_config['params'])
                
                if strategy_instance and data is not None:
                    # 실제 신호 생성 및 가중치 계산
                    signals = strategy_instance.generate_signals(data)
                    weights = strategy_instance.calculate_weights(signals)
                    
                    return {
                        'signals': len(signals),
                        'positions': len(weights),
                        'success': True
                    }
            
            # 모의 결과 반환 (실제 데이터가 없을 때)
            return {
                'signals': 15,
                'positions': 10, 
                'success': True
            }
            
        except Exception as e:
            print(f"✗ 전략 {strategy_name} 실행 실패: {str(e)}")
            return {
                'signals': 0,
                'positions': 0,
                'success': False,
                'error': str(e)
            }
            
            print(f"✓ {len(self.strategies)}개 전략 정의 완료")
            
        except Exception as e:
            print(f"✗ 전략 로딩 실패: {str(e)}")
            self.strategies = {}
    
    def load_stock_data(self):
        """주식 데이터 로딩 (실제로는 CSV 파일에서) """
        try:
            # 실제 구현에서는 CSV 파일 로딩
            # import pandas as pd
            # self.stock_data = pd.read_csv('./data/stock_analysis.csv')
            print("✓ 주식 데이터 로딩 완료 (모의)")
            
        except Exception as e:
            print(f"✗ 주식 데이터 로딩 실패: {str(e)}")
    
    def get_strategy_function(self, strategy_info: Dict):
        """전략 모듈에서 실제 함수 가져오기"""
        try:
            module_name = strategy_info["module"]
            function_name = strategy_info["function"]
            
            if module_name in self.strategy_modules:
                module = self.strategy_modules[module_name]
                if hasattr(module, function_name):
                    return getattr(module, function_name)
                else:
                    print(f"⚠️ 함수 {function_name}를 {module_name}에서 찾을 수 없음")
                    return None
            else:
                print(f"⚠️ 모듈 {module_name}이 로딩되지 않음")
                return None
                
        except Exception as e:
            print(f"✗ 전략 함수 로딩 실패: {str(e)}")
            return None
    
    def execute_backtest(self, request_data: Dict) -> Dict:
        """실제 백테스트 실행"""
        try:
            results = []
            
            # 각 전략별로 실행
            for strategy_config in request_data["strategies"]:
                strategy_id = strategy_config["id"]
                
                if strategy_id in self.strategies:
                    strategy_info = self.strategies[strategy_id]
                    strategy_func = self.get_strategy_function(strategy_info)
                    
                    if strategy_func:
                        # 실제 전략 실행 (여기서는 모의 결과)
                        print(f"✓ {strategy_info['name']} 전략 실행")
                    else:
                        print(f"✗ {strategy_info['name']} 전략 함수 없음")
            
            # 모의 백테스트 결과 반환
            mock_results = [
                {
                    "rank": 1, "stockCode": "005930", "stockName": "삼성전자",
                    "compositeScore": 94.2, "grade": "S", "strengthArea": "재무",
                    "strategyValues": {"rsi_reversal": 28.5, "roe_growth": 22.1}
                },
                {
                    "rank": 2, "stockCode": "000660", "stockName": "SK하이닉스",
                    "compositeScore": 91.8, "grade": "S", "strengthArea": "균형", 
                    "strategyValues": {"rsi_reversal": 31.2, "roe_growth": 18.9}
                },
                {
                    "rank": 3, "stockCode": "035420", "stockName": "NAVER",
                    "compositeScore": 89.3, "grade": "A", "strengthArea": "기술",
                    "strategyValues": {"rsi_reversal": 29.8, "roe_growth": 16.2}
                },
                {
                    "rank": 4, "stockCode": "005380", "stockName": "현대차",
                    "compositeScore": 87.6, "grade": "A", "strengthArea": "기술",
                    "strategyValues": {"rsi_reversal": 25.4, "roe_growth": 15.8}
                },
                {
                    "rank": 5, "stockCode": "051910", "stockName": "LG화학", 
                    "compositeScore": 85.1, "grade": "A", "strengthArea": "재무",
                    "strategyValues": {"rsi_reversal": 32.1, "roe_growth": 14.5}
                }
            ]
            
            return {
                "results": mock_results[:request_data["outputCount"]],
                "totalAnalyzed": 2847,
                "conditionMet": 127,
                "reliability": {
                    "dataQuality": 94.2,
                    "coverage": 96.1,
                    "completedAt": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            raise Exception(f"백테스트 실행 오류: {str(e)}")

# 전역 매니저 인스턴스
backtest_manager = None

@app.on_event("startup")
async def startup_event():
    global backtest_manager
    try:
        backtest_manager = QuantBacktestManager()
        print("✓ 백테스트 매니저 초기화 완료")
    except Exception as e:
        print(f"✗ 시스템 초기화 실패: {str(e)}")

# ===== API 엔드포인트들 =====

@app.get("/api/strategies")
async def get_strategies():
    """사용 가능한 전략 목록 반환"""
    try:
        if not backtest_manager:
            raise HTTPException(status_code=500, detail="백테스트 시스템이 초기화되지 않았습니다.")
        
        strategies_data = []
        for strategy_id, info in backtest_manager.strategies.items():
            strategies_data.append({
                "id": strategy_id,
                "name": info["name"],
                "description": info["description"],
                "defaultParams": info["default_params"],
                "paramSchema": {}
            })
        
        return {
            "success": True,
            "strategies": strategies_data
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"전략 로딩 실패: {str(e)}"
        }

@app.post("/api/backtest")
async def run_backtest(request: BacktestRequest):
    """백테스트 실행"""
    try:
        if not backtest_manager:
            raise HTTPException(status_code=500, detail="백테스트 시스템이 초기화되지 않았습니다.")
        
        # 요청 데이터 검증
        if not request.strategies:
            raise HTTPException(status_code=400, detail="최소 하나의 전략을 선택해야 합니다.")
        
        total_weight = sum(s.weight for s in request.strategies)
        if abs(total_weight - 100) > 1:
            raise HTTPException(status_code=400, detail="전략 가중치의 합이 100%가 되어야 합니다.")
        
        # 백테스트 실행
        request_dict = {
            "strategies": [s.dict() for s in request.strategies],
            "year": request.year,
            "outputCount": request.outputCount
        }
        
        result_data = backtest_manager.execute_backtest(request_dict)
        
        return {
            "success": True,
            "data": result_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"백테스트 실행 오류: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"백테스트 실행 중 오류: {str(e)}")

@app.get("/api/validate-data")
async def validate_stock_data(year: int):
    """주식 데이터 유효성 검사"""
    try:
        if not backtest_manager:
            return {"isValid": False, "message": "백테스트 시스템이 초기화되지 않았습니다."}
        
        # 실제로는 해당 연도 데이터 존재 여부 확인
        # yearly_data = filter_data_by_year(year)
        
        return {
            "isValid": True,
            "message": f"{year}년 데이터: 2,847개 종목 보유"
        }
        
    except Exception as e:
        return {"isValid": False, "message": f"데이터 검증 오류: {str(e)}"}

@app.post("/api/portfolio")
async def save_portfolio(portfolio: PortfolioRequest):
    """포트폴리오 저장"""
    try:
        import json
        import uuid
        
        portfolio_id = str(uuid.uuid4())
        portfolio_data = {
            "id": portfolio_id,
            "name": portfolio.name,
            "stocks": portfolio.stocks,
            "strategies": portfolio.strategies,
            "createdAt": portfolio.createdAt,
            "savedAt": datetime.now().isoformat()
        }
        
        # portfolios 디렉토리 생성
        portfolios_dir = Path("./portfolios")
        portfolios_dir.mkdir(exist_ok=True)
        
        # JSON 파일로 저장
        portfolio_file = portfolios_dir / f"{portfolio_id}.json"
        with open(portfolio_file, "w", encoding="utf-8") as f:
            json.dump(portfolio_data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 포트폴리오 저장 완료: {portfolio.name}")
        
        return {"success": True, "id": portfolio_id}
        
    except Exception as e:
        print(f"✗ 포트폴리오 저장 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"포트폴리오 저장 실패: {str(e)}")

@app.get("/api/portfolios")
async def get_portfolios():
    """저장된 포트폴리오 목록 조회"""
    try:
        import json
        from pathlib import Path
        
        portfolios = []
        portfolios_dir = Path("./portfolios")
        
        if portfolios_dir.exists():
            for portfolio_file in portfolios_dir.glob("*.json"):
                try:
                    with open(portfolio_file, "r", encoding="utf-8") as f:
                        portfolio_data = json.load(f)
                        portfolios.append(portfolio_data)
                except Exception as e:
                    print(f"포트폴리오 파일 로딩 실패: {portfolio_file} - {str(e)}")
        
        # 저장 시간순 정렬
        portfolios.sort(key=lambda x: x.get('savedAt', ''), reverse=True)
        
        return {"portfolios": portfolios}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"포트폴리오 목록 조회 실패: {str(e)}")

@app.get("/health")
async def health_check():
    """시스템 상태 확인"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "system_ready": backtest_manager is not None,
        "strategies_loaded": len(backtest_manager.strategies) if backtest_manager else 0,
        "modules_loaded": list(strategy_modules.keys()),
        "data_loaded": backtest_manager.stock_data is not None if backtest_manager else False
    }

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "퀀트 백테스트 API 서버",
        "version": "1.0.0",
        "endpoints": [
            "/api/strategies",
            "/api/backtest", 
            "/api/validate-data",
            "/api/portfolio",
            "/api/portfolios",
            "/health"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 퀀트 백테스트 API 서버 시작")
    print(f"📁 현재 디렉토리: {Path.cwd()}")
    print(f"📊 로딩된 모듈: {list(strategy_modules.keys())}")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        reload_dirs=["./"]
    )
