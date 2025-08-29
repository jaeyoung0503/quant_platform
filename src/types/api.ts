// ===== 1. API 타입 정의 (types/api.ts) =====
export interface BacktestRequest {
  strategies: {
    id: string;
    weight: number;
    params: Record<string, any>;
  }[];
  year: number;
  outputCount: number;
}

export interface BacktestResult {
  rank: number;
  stockCode: string;
  stockName: string;
  compositeScore: number;
  grade: string;
  strengthArea: string;
  strategyValues: Record<string, number>;
  selected: boolean;
}

export interface BacktestResponse {
  success: boolean;
  data?: {
    results: BacktestResult[];
    totalAnalyzed: number;
    conditionMet: number;
    reliability: {
      dataQuality: number;
      coverage: number;
      completedAt: string;
    };
  };
  error?: string;
}

export interface Strategy {
  id: string;
  name: string;
  description: string;
  selected: boolean;
  weight: number;
  params: Record<string, any>;
  defaultParams: Record<string, any>;
  paramSchema?: Record<string, {
    type: string;
    min?: number;
    max?: number;
    description: string;
  }>;
}

export interface StrategyResponse {
  success: boolean;
  strategies?: {
    id: string;
    name: string;
    description: string;
    defaultParams: Record<string, any>;
    paramSchema?: Record<string, any>;
  }[];
  error?: string;
}

export interface PortfolioStock {
  stockCode: string;
  stockName: string;
  score: number;
  grade: string;
  weight: number;
}





