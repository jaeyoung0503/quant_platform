// src/app/api/strategies/route.ts

export async function GET() {
  return Response.json({
    success: true,
    strategies: [
      {
        id: "low_pe",
        name: "저PER 전략",
        description: "PER 15배 이하 종목 선별하는 가치투자 전략",
        defaultParams: { max_pe_ratio: 15, min_market_cap: 1000 }
      },
      {
        id: "rsi_mean_reversion", 
        name: "RSI 평균회귀 전략",
        description: "RSI 30 이하 매수, 70 이상 매도",
        defaultParams: { rsi_period: 14, oversold: 30, overbought: 70 }
      },
      {
        id: "buffett_moat",
        name: "워렌 버핏의 해자 전략", 
        description: "경제적 해자가 있는 기업을 합리적 가격에 장기 보유",
        defaultParams: { max_pe: 20, min_roe: 15, min_roic: 12 }
      },
      {
        id: "peter_lynch_peg",
        name: "피터 린치의 PEG 전략",
        description: "PEG 비율 1.0 이하 성장주 발굴",
        defaultParams: { max_peg: 1.0, min_growth_rate: 10, max_pe: 30 }
      },
      {
        id: "william_oneil_canslim",
        name: "윌리엄 오닐의 CAN SLIM",
        description: "7가지 기준으로 고성장주 발굴",
        defaultParams: { min_current_earnings: 25, min_relative_strength: 80 }
      },
      {
        id: "bollinger_band",
        name: "볼린저 밴드 역발상 전략",
        description: "하단선 터치시 매수, 상단선 터치시 매도", 
        defaultParams: { bb_period: 20, bb_std: 2 }
      },
      {
        id: "dividend_aristocrats",
        name: "배당 귀족주 전략",
        description: "20년 이상 연속 배당 증가 기업",
        defaultParams: { min_dividend_years: 20, min_dividend_yield: 2 }
      },
      {
        id: "joel_greenblatt_magic",
        name: "조엘 그린블라트의 마법공식",
        description: "ROE + 수익수익률 결합한 체계적 가치투자",
        defaultParams: { min_market_cap: 1000, top_stocks: 30 }
      },
      {
        id: "benjamin_graham_defensive",
        name: "벤저민 그레이엄의 방어적 투자",
        description: "안정성과 배당 중심의 보수적 가치투자",
        defaultParams: { max_pe: 15, min_dividend_yield: 3, debt_to_equity: 0.5 }
      },
      {
        id: "momentum_growth",
        name: "모멘텀 성장주 전략",
        description: "주가 상승 추세와 실적 성장 동반 종목",
        defaultParams: { min_price_momentum: 20, min_earnings_growth: 15 }
      },
      {
        id: "contrarian_value",
        name: "역발상 가치투자 전략",
        description: "시장에서 외면받는 저평가 우량주 발굴",
        defaultParams: { max_pb: 1.0, min_roe: 10, max_pe: 12 }
      },
      {
        id: "quality_at_reasonable_price",
        name: "합리적 가격의 우량주 전략",
        description: "재무건전성 우수한 기업을 적정가에 매수",
        defaultParams: { min_roe: 15, max_pe: 18, min_current_ratio: 1.5 }
      },
      {
        id: "small_cap_value",
        name: "소형주 가치투자 전략",
        description: "시가총액 작은 저평가 종목 발굴",
        defaultParams: { max_market_cap: 5000, max_pb: 1.2, min_roe: 12 }
      },
      {
        id: "dividend_growth",
        name: "배당 성장주 전략",
        description: "배당을 꾸준히 늘리는 성장 기업",
        defaultParams: { min_dividend_growth: 5, min_dividend_yield: 2, max_payout_ratio: 60 }
      },
      {
        id: "net_net_working_capital",
        name: "그레이엄의 Net-Net 전략",
        description: "청산가치보다 낮은 가격의 종목",
        defaultParams: { max_price_to_ncav: 0.67, min_working_capital: 0 }
      },
      {
        id: "earnings_momentum",
        name: "실적 모멘텀 전략",
        description: "분기 실적이 연속 개선되는 종목",
        defaultParams: { min_eps_growth: 20, consecutive_quarters: 2 }
      },
      {
        id: "low_debt_high_roe",
        name: "저부채 고ROE 전략",
        description: "부채비율 낮고 자기자본이익률 높은 종목",
        defaultParams: { max_debt_ratio: 30, min_roe: 20 }
      },
      {
        id: "turnaround_story",
        name: "턴어라운드 전략",
        description: "실적 회복 국면의 종목 발굴",
        defaultParams: { min_eps_change: 50, max_pe: 25 }
      },
      {
        id: "high_margin_business",
        name: "고마진 비즈니스 전략",
        description: "영업이익률 높은 수익성 우수 기업",
        defaultParams: { min_operating_margin: 15, min_net_margin: 10 }
      },
      {
        id: "asset_growth_momentum",
        name: "자산 성장 모멘텀 전략", 
        description: "자산 규모와 매출이 동반 성장하는 기업",
        defaultParams: { min_asset_growth: 10, min_revenue_growth: 12 }
      }
    ]
  });
}