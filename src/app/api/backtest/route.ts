
// src/app/api/backtest/route.ts  
export async function POST(request: Request) {
  try {
    const body = await request.json();
    
    // 2초 지연 (실제 분석하는 것처럼)
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // 선택된 전략에 따른 결과 생성
    const selectedStrategyIds = body.strategies.map((s: any) => s.id);
    
    const mockResults = [
      {
        rank: 1, stockCode: "005930", stockName: "삼성전자",
        compositeScore: 94.2, grade: "S", strengthArea: "재무",
        strategyValues: generateStrategyValues("005930", selectedStrategyIds)
      },
      {
        rank: 2, stockCode: "000660", stockName: "SK하이닉스",
        compositeScore: 91.8, grade: "S", strengthArea: "균형", 
        strategyValues: generateStrategyValues("000660", selectedStrategyIds)
      },
      {
        rank: 3, stockCode: "035420", stockName: "NAVER",
        compositeScore: 89.3, grade: "A", strengthArea: "기술",
        strategyValues: generateStrategyValues("035420", selectedStrategyIds)
      },
      {
        rank: 4, stockCode: "005380", stockName: "현대차",
        compositeScore: 87.6, grade: "A", strengthArea: "기술",
        strategyValues: generateStrategyValues("005380", selectedStrategyIds)
      },
      {
        rank: 5, stockCode: "051910", stockName: "LG화학",
        compositeScore: 85.1, grade: "A", strengthArea: "재무",
        strategyValues: generateStrategyValues("051910", selectedStrategyIds)
      },
      {
        rank: 6, stockCode: "006400", stockName: "삼성SDI", 
        compositeScore: 83.4, grade: "A", strengthArea: "균형",
        strategyValues: generateStrategyValues("006400", selectedStrategyIds)
      },
      {
        rank: 7, stockCode: "028260", stockName: "삼성물산",
        compositeScore: 81.7, grade: "A", strengthArea: "가치",
        strategyValues: generateStrategyValues("028260", selectedStrategyIds)
      },
      {
        rank: 8, stockCode: "012330", stockName: "현대모비스",
        compositeScore: 79.8, grade: "B", strengthArea: "기술",
        strategyValues: generateStrategyValues("012330", selectedStrategyIds)
      },
      {
        rank: 9, stockCode: "066570", stockName: "LG전자",
        compositeScore: 78.2, grade: "B", strengthArea: "균형",
        strategyValues: generateStrategyValues("066570", selectedStrategyIds)
      },
      {
        rank: 10, stockCode: "003550", stockName: "LG", 
        compositeScore: 76.5, grade: "B", strengthArea: "재무",
        strategyValues: generateStrategyValues("003550", selectedStrategyIds)
      }
    ];

    return Response.json({
      success: true,
      data: {
        results: mockResults.slice(0, body.outputCount),
        totalAnalyzed: 2847,
        conditionMet: 127,
        reliability: {
          dataQuality: 94.2,
          coverage: 96.1,
          completedAt: new Date().toISOString()
        }
      }
    });

  } catch (error) {
    return Response.json({
      success: false,
      error: "백테스트 실행 중 오류가 발생했습니다."
    }, { status: 500 });
  }
}

// 전략별 수치 생성 함수
function generateStrategyValues(stockCode: string, strategyIds: string[]) {
  const stockData: Record<string, Record<string, number>> = {
    "005930": { rsi: 28.5, pe: 12.3, roe: 22.1, peg: 0.8, momentum: 15.2 },
    "000660": { rsi: 31.2, pe: 8.9, roe: 18.9, peg: 0.6, momentum: 22.1 },
    "035420": { rsi: 29.8, pe: 18.2, roe: 16.2, peg: 0.9, momentum: 18.4 },
    "005380": { rsi: 25.4, pe: 6.8, roe: 15.8, peg: 0.5, momentum: 12.3 },
    "051910": { rsi: 32.1, pe: 9.2, roe: 14.5, peg: 0.7, momentum: 8.7 },
    "006400": { rsi: 35.2, pe: 11.1, roe: 16.8, peg: 0.8, momentum: 14.5 },
    "028260": { rsi: 33.8, pe: 10.5, roe: 13.2, peg: 0.9, momentum: 11.2 },
    "012330": { rsi: 36.1, pe: 8.4, roe: 12.8, peg: 0.6, momentum: 9.8 },
    "066570": { rsi: 34.5, pe: 9.8, roe: 11.9, peg: 0.7, momentum: 10.5 },
    "003550": { rsi: 31.7, pe: 7.9, roe: 10.2, peg: 0.8, momentum: 7.9 }
  };

  const data = stockData[stockCode] || { rsi: 30.0, pe: 15.0, roe: 15.0, peg: 1.0, momentum: 10.0 };
  const values: Record<string, number> = {};

  strategyIds.forEach(strategyId => {
    if (strategyId.includes("rsi")) {
      values[strategyId] = data.rsi;
    } else if (strategyId.includes("pe") || strategyId.includes("low_pe")) {
      values[strategyId] = data.pe;
    } else if (strategyId.includes("buffett") || strategyId.includes("roe")) {
      values[strategyId] = data.roe;
    } else if (strategyId.includes("peg") || strategyId.includes("lynch")) {
      values[strategyId] = data.peg;
    } else if (strategyId.includes("momentum") || strategyId.includes("canslim")) {
      values[strategyId] = data.momentum;
    } else {
      values[strategyId] = data.roe;
    }
  });

  return values;
}
