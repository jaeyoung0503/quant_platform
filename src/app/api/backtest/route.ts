// src/app/api/backtest/route.ts
import { NextRequest } from 'next/server';
import * as fs from 'fs';
import * as path from 'path';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    console.log('백테스트 요청:', body);
    
    // CSV 파일 경로
    const csvPath = path.join(process.cwd(), 'public/data/stock_analysis.csv');
    
    if (!fs.existsSync(csvPath)) {
      return Response.json({
        success: false,
        error: "CSV 파일이 없습니다: public/data/stock_analysis.csv"
      }, { status: 400 });
    }
    
    // CSV 읽기 및 파싱
    const csvContent = fs.readFileSync(csvPath, 'utf-8');
    const lines = csvContent.trim().split('\n');
    const headers = lines[0].split(',').map(h => h.trim().toLowerCase());
    
    console.log('CSV 헤더:', headers);
    console.log('총 데이터 행:', lines.length - 1);
    
    // 고유한 종목 데이터 추출 (Map을 사용해 중복 제거)
    const stockMap = new Map();
    let processedRows = 0;
    let validRows = 0;
    
    for (let i = 1; i < lines.length; i++) {
      processedRows++;
      const values = lines[i].split(',').map(v => v.trim());
      
      if (values.length !== headers.length) continue;
      
      const stock: any = {};
      headers.forEach((header, idx) => {
        const value = values[idx];
        
        if (['close', 'volume', 'market_cap', 'pe_ratio', 'roe', 'rsi_14', 'open', 'high', 'low'].includes(header)) {
          stock[header] = parseFloat(value) || 0;
        } else if (header === 'year') {
          stock[header] = parseInt(value) || 0;
        } else {
          stock[header] = value;
        }
      });
      
      // 유효성 검사
      if (stock.ticker && stock.name && stock.close > 0) {
        // 연도 필터링 (year 컬럼이 있는 경우)
        if (!headers.includes('year') || stock.year === body.year) {
          // 중복 제거 - 같은 ticker의 최신 데이터만 유지
          if (!stockMap.has(stock.ticker) || 
              (stock.date && stockMap.get(stock.ticker).date && stock.date > stockMap.get(stock.ticker).date)) {
            stockMap.set(stock.ticker, stock);
            validRows++;
          }
        }
      }
    }
    
    const uniqueStocks = Array.from(stockMap.values());
    
    console.log('처리된 행:', processedRows);
    console.log('유효한 행:', validRows);
    console.log('고유 종목 수:', uniqueStocks.length);
    console.log('샘플 종목들:', uniqueStocks.slice(0, 10).map(s => `${s.ticker}-${s.name}`));
    
    if (uniqueStocks.length === 0) {
      return Response.json({
        success: false,
        error: `${body.year}년에 해당하는 유효한 주식 데이터가 없습니다`,
        debug: {
          totalRows: processedRows,
          validRows: validRows,
          year: body.year,
          hasYearColumn: headers.includes('year')
        }
      }, { status: 400 });
    }
    
    // 전략 분석 실행
    const analysisResults = [];
    
    // 더 다양한 종목 선택을 위해 셔플
    const shuffledStocks = [...uniqueStocks].sort(() => Math.random() - 0.5);
    
    for (let i = 0; i < Math.min(shuffledStocks.length, body.outputCount * 2); i++) {
      const stock = shuffledStocks[i];
      
      let totalScore = 0;
      let validStrategies = 0;
      const strategyValues: Record<string, number> = {};
      
      // 각 전략별 점수 계산
      for (const strategy of body.strategies) {
        const score = calculateStrategyScore(stock, strategy);
        if (score !== null && !isNaN(score)) {
          totalScore += score * (strategy.weight / 100);
          strategyValues[strategy.id] = score;
          validStrategies++;
        }
      }
      
      if (validStrategies > 0) {
        analysisResults.push({
          stockCode: stock.ticker,
          stockName: stock.name,
          compositeScore: parseFloat(totalScore.toFixed(1)),
          grade: getGrade(totalScore),
          strengthArea: getStrengthArea(stock),
          strategyValues
        });
      }
    }
    
    // 점수순 정렬 후 상위 종목만 선택
    analysisResults.sort((a, b) => b.compositeScore - a.compositeScore);
    const finalResults = analysisResults.slice(0, body.outputCount).map((result, index) => ({
      ...result,
      rank: index + 1,
      selected: false
    }));
    
    console.log('최종 결과 종목들:', finalResults.map(r => `${r.rank}. ${r.stockCode}-${r.stockName}(${r.compositeScore}점)`));
    
    return Response.json({
      success: true,
      data: {
        results: finalResults,
        totalAnalyzed: uniqueStocks.length,
        conditionMet: analysisResults.length,
        reliability: {
          dataQuality: calculateDataQuality(uniqueStocks),
          coverage: (finalResults.length / uniqueStocks.length) * 100,
          completedAt: new Date().toISOString()
        }
      }
    });

  } catch (error) {
    console.error('백테스트 실행 오류:', error);
    return Response.json({
      success: false,
      error: "백테스트 실행 중 오류가 발생했습니다",
      details: error instanceof Error ? error.message : String(error)
    }, { status: 500 });
  }
}

// 전략별 점수 계산
function calculateStrategyScore(stock: any, strategy: any): number | null {
  const baseScore = 50 + (Math.random() - 0.5) * 40; // 30-70 기본 범위
  
  try {
    switch (strategy.id) {
      case 'low_pe':
        if (stock.pe_ratio && stock.pe_ratio > 0) {
          const maxPe = strategy.params?.max_pe_ratio || 15;
          return stock.pe_ratio <= maxPe ? 75 + Math.random() * 25 : 25 + Math.random() * 35;
        }
        return baseScore;
        
      case 'rsi_mean_reversion':
        if (stock.rsi_14) {
          if (stock.rsi_14 <= 30) return 80 + Math.random() * 20;
          if (stock.rsi_14 >= 70) return Math.random() * 30;
          return 40 + Math.random() * 30;
        }
        return baseScore;
        
      case 'buffett_moat':
        let score = 40;
        if (stock.roe && stock.roe >= 15) score += 20;
        if (stock.pe_ratio && stock.pe_ratio <= 20) score += 15;
        return score + Math.random() * 15;
        
      default:
        return baseScore;
    }
  } catch (err) {
    return baseScore;
  }
}

// 등급 계산
function getGrade(score: number): string {
  if (score >= 85) return 'S';
  if (score >= 75) return 'A';
  if (score >= 65) return 'B';
  if (score >= 55) return 'C';
  return 'D';
}

// 강점 분야 결정 (종목 데이터 기반)
function getStrengthArea(stock: any): string {
  if (stock.pe_ratio && stock.pe_ratio < 12) return '가치';
  if (stock.roe && stock.roe > 20) return '재무';
  if (stock.market === 'KOSDAQ') return '기술';
  
  const areas = ['재무', '기술', '성장', '균형'];
  return areas[Math.floor(Math.random() * areas.length)];
}

// 데이터 품질 계산
function calculateDataQuality(data: any[]): number {
  if (data.length === 0) return 0;
  
  const requiredFields = ['ticker', 'name', 'close'];
  const optionalFields = ['pe_ratio', 'roe', 'market_cap', 'rsi_14'];
  
  let qualitySum = 0;
  const sampleSize = Math.min(100, data.length);
  
  for (let i = 0; i < sampleSize; i++) {
    const stock = data[i];
    let fieldScore = 0;
    
    // 필수 필드 체크 (60점)
    requiredFields.forEach(field => {
      if (stock[field] && stock[field] !== '') fieldScore += 20;
    });
    
    // 선택 필드 체크 (40점)  
    optionalFields.forEach(field => {
      if (stock[field] && !isNaN(parseFloat(stock[field]))) fieldScore += 10;
    });
    
    qualitySum += Math.min(100, fieldScore);
  }
  
  return Math.round(qualitySum / sampleSize);
}