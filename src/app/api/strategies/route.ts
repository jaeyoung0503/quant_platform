// app/api/strategies/route.ts - 디버깅 버전
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';
import { NextResponse } from 'next/server';

export async function GET() {
  // 먼저 Python 없이 전략 목록 확인
  const pythonDir = path.join(process.cwd(), 'python');
  const quantEngineDir = path.join(process.cwd(), 'quant_engine');
  const getStrategiesScript = path.join(pythonDir, 'get_strategies.py');
  
  console.log('=== Directory Check ===');
  console.log('Python dir exists:', fs.existsSync(pythonDir));
  console.log('Quant engine dir exists:', fs.existsSync(quantEngineDir));
  console.log('Get strategies script exists:', fs.existsSync(getStrategiesScript));
  
  if (fs.existsSync(quantEngineDir)) {
    const files = fs.readdirSync(quantEngineDir);
    console.log('Quant engine files:', files);
  }

  // Python이 없거나 스크립트가 없으면 하드코딩된 20개 전략 반환
  if (!fs.existsSync(getStrategiesScript)) {
    console.log('Python script not found, returning hardcoded strategies');
    return NextResponse.json(getHardcodedStrategies());
  }

  try {
    return new Promise((resolve) => {
      console.log('Executing Python script:', getStrategiesScript);
      const python = spawn('python', [getStrategiesScript], {
        stdio: ['pipe', 'pipe', 'pipe'],
        cwd: process.cwd()
      });
      
      let data = '';
      let error = '';

      python.stdout.on('data', (chunk: Buffer) => {
        data += chunk.toString();
        console.log('Python stdout:', chunk.toString().trim());
      });

      python.stderr.on('data', (chunk: Buffer) => {
        error += chunk.toString();
        console.log('Python stderr:', chunk.toString().trim());
      });

      python.on('close', (code: number | null) => {
        console.log(`Python process exited with code: ${code}`);
        console.log('Full stdout:', data);
        console.log('Full stderr:', error);

        if (code !== 0) {
          console.error('Python script failed, returning hardcoded strategies');
          resolve(NextResponse.json(getHardcodedStrategies()));
          return;
        }

        try {
          const strategies = JSON.parse(data);
          console.log(`Successfully parsed ${strategies.length} strategies`);
          resolve(NextResponse.json(strategies));
        } catch (parseError) {
          console.error('JSON parse error:', parseError);
          console.error('Raw data:', data);
          resolve(NextResponse.json(getHardcodedStrategies()));
        }
      });

      python.on('error', (error) => {
        console.error('Failed to start Python process:', error);
        resolve(NextResponse.json(getHardcodedStrategies()));
      });

      // 타임아웃
      setTimeout(() => {
        python.kill();
        console.log('Python process timeout');
        resolve(NextResponse.json(getHardcodedStrategies()));
      }, 30000);
    });

  } catch (error) {
    console.error('API error:', error);
    return NextResponse.json(getHardcodedStrategies());
  }
}

function getHardcodedStrategies() {
  return [
    // 기본 전략 10개
    {
      id: 'low_pe',
      name: 'Low PE Strategy',
      category: 'basic',
      description: 'PER 15배 이하 종목 선별하는 가치투자 전략',
      riskLevel: 'low',
      complexity: 'simple',
      expectedReturn: '8-12%',
      volatility: '12-18%',
      details: 'PER이 15배 이하인 저평가 종목을 선별하여 투자하는 가치투자 전략입니다.'
    },
    {
      id: 'dividend_aristocrats',
      name: 'Dividend Aristocrats',
      category: 'basic',
      description: '20년 이상 연속 배당 증가 기업 투자',
      riskLevel: 'low',
      complexity: 'simple',
      expectedReturn: '7-10%',
      volatility: '10-15%',
      details: '20년 이상 연속으로 배당을 증가시킨 우량 기업에 투자합니다.'
    },
    {
      id: 'simple_momentum',
      name: 'Simple Momentum',
      category: 'basic',
      description: '최근 성과 상위 종목 투자, 상승 추세 추종',
      riskLevel: 'medium',
      complexity: 'simple',
      expectedReturn: '10-15%',
      volatility: '16-22%',
      details: '최근 3-12개월 수익률이 높은 상위 종목에 투자하는 모멘텀 전략입니다.'
    },
    {
      id: 'moving_average_cross',
      name: 'Moving Average Cross',
      category: 'basic',
      description: '단기 이동평균이 장기 이동평균 상향 돌파시 매수',
      riskLevel: 'medium',
      complexity: 'simple',
      expectedReturn: '8-12%',
      volatility: '14-20%',
      details: '20일 이동평균이 60일 이동평균을 상향 돌파할 때 매수하는 전략입니다.'
    },
    {
      id: 'rsi_mean_reversion',
      name: 'RSI Mean Reversion',
      category: 'basic',
      description: 'RSI 30 이하 매수, 70 이상 매도',
      riskLevel: 'medium',
      complexity: 'simple',
      expectedReturn: '10-13%',
      volatility: '12-18%',
      details: 'RSI 지표를 활용해 과매도 구간에서 매수하는 역발상 전략입니다.'
    },
    {
      id: 'bollinger_band',
      name: 'Bollinger Band',
      category: 'basic',
      description: '하단선 터치시 매수, 상단선 터치시 매도',
      riskLevel: 'medium',
      complexity: 'simple',
      expectedReturn: '9-12%',
      volatility: '13-19%',
      details: '볼린저 밴드 하단선 근처에서 매수하는 역발상 전략입니다.'
    },
    {
      id: 'small_cap',
      name: 'Small Cap Premium',
      category: 'basic',
      description: '시가총액 하위 종목 투자로 초과수익 추구',
      riskLevel: 'high',
      complexity: 'simple',
      expectedReturn: '12-18%',
      volatility: '20-30%',
      details: '소형주의 높은 성장 가능성을 활용하는 전략입니다.'
    },
    {
      id: 'low_volatility',
      name: 'Low Volatility',
      category: 'basic',
      description: '변동성이 낮은 종목으로 안정적 수익 추구',
      riskLevel: 'low',
      complexity: 'simple',
      expectedReturn: '8-11%',
      volatility: '8-12%',
      details: '변동성이 낮은 안정적인 종목들로 포트폴리오를 구성합니다.'
    },
    {
      id: 'quality_factor',
      name: 'Quality Factor',
      category: 'basic',
      description: 'ROE, 부채비율 등 재무 건전성 우수 기업',
      riskLevel: 'low',
      complexity: 'simple',
      expectedReturn: '9-13%',
      volatility: '12-16%',
      details: '재무 건전성이 우수한 품질 좋은 기업들에 투자합니다.'
    },
    {
      id: 'regular_rebalancing',
      name: 'Regular Rebalancing',
      category: 'basic',
      description: '정해진 비율로 정기적 리밸런싱하여 위험 관리',
      riskLevel: 'medium',
      complexity: 'simple',
      expectedReturn: '8-12%',
      volatility: '10-16%',
      details: '정기적으로 포트폴리오를 리밸런싱하여 위험을 관리합니다.'
    },
    // 고급 전략 10개
    {
      id: 'buffett_moat',
      name: 'Buffett Moat Strategy',
      category: 'advanced',
      description: '경쟁우위가 있는 기업을 합리적 가격에 장기 보유',
      riskLevel: 'low',
      complexity: 'medium',
      expectedReturn: '12-16%',
      volatility: '10-15%',
      details: '워렌 버핏의 경제적 해자 개념을 활용한 장기 가치투자 전략입니다.'
    },
    {
      id: 'peter_lynch_peg',
      name: 'Peter Lynch PEG',
      category: 'advanced',
      description: 'PEG 비율 1.0 이하 성장주 발굴, 10배 주식 추구',
      riskLevel: 'medium',
      complexity: 'medium',
      expectedReturn: '13-18%',
      volatility: '16-22%',
      details: '피터 린치의 PEG 전략으로 저평가된 성장주를 발굴합니다.'
    },
    {
      id: 'benjamin_graham_defensive',
      name: 'Graham Defensive',
      category: 'advanced',
      description: '안전성과 수익성을 겸비한 보수적 가치투자',
      riskLevel: 'low',
      complexity: 'medium',
      expectedReturn: '9-13%',
      volatility: '10-16%',
      details: '벤저민 그레이엄의 방어적 투자자 전략을 구현합니다.'
    },
    {
      id: 'joel_greenblatt_magic',
      name: 'Magic Formula',
      category: 'advanced',
      description: 'ROE + 수익수익률(E/P) 결합한 체계적 가치투자',
      riskLevel: 'medium',
      complexity: 'medium',
      expectedReturn: '12-17%',
      volatility: '14-20%',
      details: '조엘 그린블라트의 마법공식으로 체계적 가치투자를 실행합니다.'
    },
    {
      id: 'william_oneil_canslim',
      name: 'CANSLIM Strategy',
      category: 'advanced',
      description: '7가지 기준으로 고성장주 발굴, 모멘텀과 펀더멘털 결합',
      riskLevel: 'high',
      complexity: 'complex',
      expectedReturn: '15-25%',
      volatility: '20-30%',
      details: '윌리엄 오닐의 CAN SLIM 방법론으로 고성장주를 선별합니다.'
    },
    {
      id: 'howard_marks_cycle',
      name: 'Cycle Investment',
      category: 'advanced',
      description: '경기사이클 극단점에서 역발상 기회 포착',
      riskLevel: 'medium',
      complexity: 'complex',
      expectedReturn: '13-18%',
      volatility: '16-24%',
      details: '하워드 막스의 사이클 투자법으로 시장 극단점을 활용합니다.'
    },
    {
      id: 'james_oshaughnessy',
      name: 'What Works Strategy',
      category: 'advanced',
      description: '50년 데이터 검증, 시총+PBR+모멘텀 멀티팩터',
      riskLevel: 'medium',
      complexity: 'medium',
      expectedReturn: '14-19%',
      volatility: '17-23%',
      details: '제임스 오쇼네시의 장기 데이터 검증 전략입니다.'
    },
    {
      id: 'ray_dalio_all_weather',
      name: 'All Weather Portfolio',
      category: 'advanced',
      description: '경제 환경 변화에 관계없이 안정적 수익 추구',
      riskLevel: 'low',
      complexity: 'medium',
      expectedReturn: '8-12%',
      volatility: '8-12%',
      details: '레이 달리오의 올웨더 포트폴리오로 전천후 투자를 실현합니다.'
    },
    {
      id: 'david_dreman_contrarian',
      name: 'Contrarian Investment',
      category: 'advanced',
      description: '시장 공포와 비관론 속에서 저평가 기회 발굴',
      riskLevel: 'medium',
      complexity: 'medium',
      expectedReturn: '12-16%',
      volatility: '16-22%',
      details: '데이비드 드레먼의 역발상 투자 전략으로 공포 속 기회를 포착합니다.'
    },
    {
      id: 'john_neff_low_pe_dividend',
      name: 'Low PE + Dividend',
      category: 'advanced',
      description: '소외받는 업종에서 저PER + 고배당 보석 발굴',
      riskLevel: 'medium',
      complexity: 'medium',
      expectedReturn: '11-15%',
      volatility: '14-18%',
      details: '존 네프의 저PER 고배당 전략으로 소외받는 가치를 발굴합니다.'
    }
  ];
}