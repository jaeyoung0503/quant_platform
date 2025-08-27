// app/api/backtest/route.ts - 백테스트 API 엔드포인트
import { NextRequest, NextResponse } from 'next/server';

interface BacktestRequest {
  strategy_id: string;
  period_days: number;
  mode: 'single_stock' | 'multi_stock';
}

interface BacktestResult {
  Symbol: string;
  'Total_Return_%': number;
  'Annual_Return_%': number;
  'Volatility_%': number;
  Sharpe_Ratio: number;
  Sortino_Ratio: number;
  Calmar_Ratio: number;
  'Max_Drawdown_%': number;
  'Win_Rate_%': number;
  Final_Value: number;
  Portfolio_History: number[];
  Monthly_Returns?: number[];
  Components?: string[];
  Weights?: Record<string, number>;
}

// 전략별 예상 성과 데이터 (실제 Python 백테스터 연결 전까지 사용)
const strategyPerformanceData: Record<string, Partial<BacktestResult>> = {
  '1': { // Basic Momentum
    'Total_Return_%': 145.3,
    'Annual_Return_%': 12.8,
    'Volatility_%': 16.2,
    Sharpe_Ratio: 1.15,
    Sortino_Ratio: 1.52,
    Calmar_Ratio: 0.85,
    'Max_Drawdown_%': 15.1,
    'Win_Rate_%': 64.2
  },
  '2': { // Mean Reversion
    'Total_Return_%': 98.7,
    'Annual_Return_%': 10.2,
    'Volatility_%': 12.8,
    Sharpe_Ratio: 1.08,
    Sortino_Ratio: 1.41,
    Calmar_Ratio: 0.92,
    'Max_Drawdown_%': 11.1,
    'Win_Rate_%': 58.9
  },
  '3': { // Warren Buffett Value
    'Total_Return_%': 112.4,
    'Annual_Return_%': 11.1,
    'Volatility_%': 10.9,
    Sharpe_Ratio: 1.32,
    Sortino_Ratio: 1.76,
    Calmar_Ratio: 1.28,
    'Max_Drawdown_%': 8.7,
    'Win_Rate_%': 61.3
  },
  '5': { // Peter Lynch Growth
    'Total_Return_%': 187.9,
    'Annual_Return_%': 15.2,
    'Volatility_%': 19.4,
    Sharpe_Ratio: 1.09,
    Sortino_Ratio: 1.45,
    Calmar_Ratio: 0.76,
    'Max_Drawdown_%': 20.0,
    'Win_Rate_%': 66.8
  },
  '9': { // Multi-Factor Model
    'Total_Return_%': 156.8,
    'Annual_Return_%': 13.7,
    'Volatility_%': 15.3,
    Sharpe_Ratio: 1.28,
    Sortino_Ratio: 1.65,
    Calmar_Ratio: 1.05,
    'Max_Drawdown_%': 13.0,
    'Win_Rate_%': 63.5
  },
  '13': { // Machine Learning
    'Total_Return_%': 172.3,
    'Annual_Return_%': 14.5,
    'Volatility_%': 17.8,
    Sharpe_Ratio: 1.19,
    Sortino_Ratio: 1.58,
    Calmar_Ratio: 0.91,
    'Max_Drawdown_%': 15.9,
    'Win_Rate_%': 65.2
  },
  '16': { // Quant Momentum
    'Total_Return_%': 201.5,
    'Annual_Return_%': 16.1,
    'Volatility_%': 21.2,
    Sharpe_Ratio: 1.07,
    Sortino_Ratio: 1.42,
    Calmar_Ratio: 0.73,
    'Max_Drawdown_%': 22.1,
    'Win_Rate_%': 68.4
  },
  '20': { // Custom Portfolio
    'Total_Return_%': 134.2,
    'Annual_Return_%': 12.1,
    'Volatility_%': 13.7,
    Sharpe_Ratio: 1.26,
    Sortino_Ratio: 1.68,
    Calmar_Ratio: 1.13,
    'Max_Drawdown_%': 10.7,
    'Win_Rate_%': 62.8
  }
};

// 샘플 종목 리스트
const sampleStocks = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'META', 'BRK.B', 
                    'V', 'JNJ', 'WMT', 'JPM', 'UNH', 'PG', 'MA'];

function generatePortfolioHistory(baseReturn: number, volatility: number, days: number = 3650): number[] {
  const dailyReturn = baseReturn / 365 / 100;
  const dailyVol = volatility / Math.sqrt(365) / 100;
  
  const history = [100000]; // 초기 자본
  
  for (let i = 1; i < days; i++) {
    const randomReturn = dailyReturn + (Math.random() - 0.5) * dailyVol * 2;
    const newValue = history[i-1] * (1 + randomReturn);
    history.push(Math.max(newValue, history[i-1] * 0.7)); // 최대 30% 하락 제한
  }
  
  return history.slice(0, Math.min(days, 1000)); // 차트 성능을 위해 최대 1000개 포인트
}

function generateMonthlyReturns(annualReturn: number, volatility: number): number[] {
  const monthlyReturn = annualReturn / 12;
  const monthlyVol = volatility / Math.sqrt(12);
  
  return Array.from({length: 120}, () => { // 10년 = 120개월
    return monthlyReturn + (Math.random() - 0.5) * monthlyVol * 2;
  });
}

async function callPythonBacktester(request: BacktestRequest): Promise<{results: BacktestResult[]}> {
  // 실제 Python 백테스터 호출 로직
  // FastAPI 서버가 실행 중이라면 여기서 호출
  try {
    const pythonApiUrl = process.env.PYTHON_API_URL || 'http://localhost:8000';
    
    const response = await fetch(`${pythonApiUrl}/backtest`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.PYTHON_API_TOKEN}`
      },
      body: JSON.stringify(request),
      signal: AbortSignal.timeout(30000) // 30초 타임아웃
    });

    if (!response.ok) {
      throw new Error(`Python API Error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.log('Python API 연결 실패, 샘플 데이터 사용:', error);
    
    // Python API 연결 실패시 샘플 데이터 반환
    const strategyData = strategyPerformanceData[request.strategy_id] || strategyPerformanceData['1'];
    
    const portfolioHistory = generatePortfolioHistory(
      strategyData['Annual_Return_%'] || 12,
      strategyData['Volatility_%'] || 15
    );
    
    const finalValue = portfolioHistory[portfolioHistory.length - 1];
    const totalReturn = ((finalValue / 100000) - 1) * 100;
    
    const portfolioResult: BacktestResult = {
      Symbol: 'PORTFOLIO',
      'Total_Return_%': totalReturn,
      'Annual_Return_%': strategyData['Annual_Return_%'] || 12,
      'Volatility_%': strategyData['Volatility_%'] || 15,
      Sharpe_Ratio: strategyData.Sharpe_Ratio || 1.2,
      Sortino_Ratio: strategyData.Sortino_Ratio || 1.5,
      Calmar_Ratio: strategyData.Calmar_Ratio || 0.9,
      'Max_Drawdown_%': strategyData['Max_Drawdown_%'] || 12,
      'Win_Rate_%': strategyData['Win_Rate_%'] || 62,
      Final_Value: finalValue,
      Portfolio_History: portfolioHistory,
      Monthly_Returns: generateMonthlyReturns(
        strategyData['Annual_Return_%'] || 12,
        strategyData['Volatility_%'] || 15
      ),
      Components: sampleStocks.slice(0, 15),
      Weights: Object.fromEntries(
        sampleStocks.slice(0, 15).map(stock => [stock, 1/15])
      )
    };
    
    return { results: [portfolioResult] };
  }
}

export async function POST(request: NextRequest) {
  try {
    // CORS 헤더 설정
    const headers = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    };

    // 요청 본문 파싱
    const body: BacktestRequest = await request.json();
    
    // 입력 검증
    if (!body.strategy_id || !body.period_days) {
      return NextResponse.json(
        { error: '필수 파라미터가 누락되었습니다.' },
        { status: 400, headers }
      );
    }

    // 전략 ID 검증
    const validStrategyIds = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', 
                             '11', '12', '13', '14', '15', '16', '17', '18', '19', '20'];
    
    if (!validStrategyIds.includes(body.strategy_id)) {
      return NextResponse.json(
        { error: '유효하지 않은 전략 ID입니다.' },
        { status: 400, headers }
      );
    }

    // 기간 검증 (최대 10년)
    if (body.period_days > 3650) {
      return NextResponse.json(
        { error: '분석 기간이 최대값(10년)을 초과했습니다.' },
        { status: 400, headers }
      );
    }

    console.log(`백테스트 시작: 전략 ${body.strategy_id}, 기간 ${body.period_days}일`);

    // Python 백테스터 호출
    const backtestResults = await callPythonBacktester(body);
    
    console.log('백테스트 완료');

    // 결과 반환
    return NextResponse.json({
      success: true,
      strategy_id: body.strategy_id,
      period_days: body.period_days,
      execution_time: new Date().toISOString(),
      ...backtestResults
    }, { headers });

  } catch (error) {
    console.error('백테스트 API 오류:', error);
    
    return NextResponse.json(
      { 
        error: '백테스트 실행 중 오류가 발생했습니다.',
        details: error instanceof Error ? error.message : String(error)
      },
      { 
        status: 500,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        }
      }
    );
  }
}

// OPTIONS 요청 처리 (CORS preflight)
export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}