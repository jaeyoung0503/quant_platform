"""
File: backtester/commands.py
Command Line Interface Functions
"""

import numpy as np
from .core import QuantBacktester
from .strategy_guide import (
    show_strategy_guide, 
    performance_benchmark, 
    calculate_strategy_grade,
    show_market_timing_guide,
    show_risk_management_guide
)

def quick_comparison():
    """빠른 전략 비교 함수"""
    print("🏃‍♂️ 빠른 전략 비교 모드")
    
    backtester = QuantBacktester()
    
    # 인기 전략 8개 자동 비교 (기존 + 새로운 전략 포함)
    popular_strategies = ['1', '3', '5', '6', '9', '13', '16', '18']  # 모멘텀, 버핏, 린치, 달리오, 팩터, ML, 퀀트모멘텀, 리스크패리티
    strategy_names = [backtester.strategies[s][0] for s in popular_strategies]
    
    print(f"📊 인기 전략 {len(popular_strategies)}개를 자동으로 비교합니다...")
    print("비교 대상:", ", ".join(strategy_names))
    
    comparison_results = []
    
    for strategy_num in popular_strategies:
        strategy_name = backtester.strategies[strategy_num][0]
        print(f"🔄 {strategy_name} 분석 중...")
        
        try:
            backtest_data = backtester.run_backtest(strategy_num)
            
            if backtest_data['results']:
                # 상위 15개 종목 평균 성과 계산
                top_results = backtest_data['results'][:15]
                avg_metrics = _calculate_average_performance(top_results)
                
                comparison_results.append({
                    'Strategy': strategy_name,
                    'Annual_Return_%': avg_metrics.get('Annual_Return_%', 0),
                    'Sharpe_Ratio': avg_metrics.get('Sharpe_Ratio', 0),
                    'Max_Drawdown_%': avg_metrics.get('Max_Drawdown_%', 0),
                    'Win_Rate_%': avg_metrics.get('Win_Rate_%', 0),
                    'Sortino_Ratio': avg_metrics.get('Sortino_Ratio', 0)
                })
        except Exception as e:
            print(f"⚠️ {strategy_name} 분석 실패: {str(e)}")
            continue
    
    # 결과 표시
    print(f"\n🏆 전략 비교 결과")
    print("="*90)
    print(f"{'순위':<4} {'전략':<25} {'연수익률%':<10} {'샤프':<8} {'소르티노':<8} {'최대낙폭%':<10} {'승률%':<8}")
    print("-"*90)
    
    # 샤프 비율로 정렬
    comparison_results.sort(key=lambda x: x['Sharpe_Ratio'], reverse=True)
    
    for i, result in enumerate(comparison_results, 1):
        print(f"{i:<4} {result['Strategy']:<25} {result['Annual_Return_%']:<10.2f} "
              f"{result['Sharpe_Ratio']:<8.2f} {result['Sortino_Ratio']:<8.2f} "
              f"{result['Max_Drawdown_%']:<10.2f} {result['Win_Rate_%']:<8.2f}")
    
    if comparison_results:
        best_strategy = comparison_results[0]
        print(f"\n🥇 최고 성과 전략: {best_strategy['Strategy']}")
        print(f"   샤프 비율: {best_strategy['Sharpe_Ratio']:.2f}")
        print(f"   연간 수익률: {best_strategy['Annual_Return_%']:.2f}%")
        print(f"   최대 낙폭: {best_strategy['Max_Drawdown_%']:.2f}%")

def advanced_analytics():
    """고급 분석 도구"""
    print("🔬 고급 분석 모드")
    
    backtester = QuantBacktester()
    
    # 사용자가 선택한 전략들을 비교
    print("비교할 전략들을 선택하세요 (예: 1,3,5,9)")
    strategy_input = input("전략 번호들 (쉼표로 구분): ").strip()
    
    try:
        strategy_numbers = [s.strip() for s in strategy_input.split(',')]
        strategy_numbers = [s for s in strategy_numbers if s in backtester.strategies]
        
        if len(strategy_numbers) < 2:
            print("❌ 최소 2개 이상의 전략을 선택해주세요.")
            return
        
        print(f"📊 선택된 전략 {len(strategy_numbers)}개를 분석합니다...")
        
        comparison_results = []
        
        for strategy_num in strategy_numbers:
            strategy_name = backtester.strategies[strategy_num][0]
            print(f"🔄 {strategy_name} 분석 중...")
            
            try:
                backtest_data = backtester.run_backtest(strategy_num)
                
                if backtest_data['results']:
                    # 상위 15개 종목 평균 성과 계산
                    top_results = backtest_data['results'][:15]
                    avg_metrics = _calculate_average_performance(top_results)
                    
                    comparison_results.append({
                        'Number': strategy_num,
                        'Strategy': strategy_name,
                        'Annual_Return_%': avg_metrics.get('Annual_Return_%', 0),
                        'Sharpe_Ratio': avg_metrics.get('Sharpe_Ratio', 0),
                        'Sortino_Ratio': avg_metrics.get('Sortino_Ratio', 0),
                        'Calmar_Ratio': avg_metrics.get('Calmar_Ratio', 0),
                        'Max_Drawdown_%': avg_metrics.get('Max_Drawdown_%', 0),
                        'Win_Rate_%': avg_metrics.get('Win_Rate_%', 0),
                        'Volatility_%': avg_metrics.get('Volatility_%', 0)
                    })
            except Exception as e:
                print(f"⚠️ {strategy_name} 분석 실패: {str(e)}")
                continue
        
        # 상세 비교 결과 표시
        print(f"\n📊 상세 전략 비교 결과")
        print("="*120)
        print(f"{'번호':<4} {'전략':<25} {'연수익률%':<10} {'샤프':<8} {'소르티노':<8} {'칼마':<8} {'변동성%':<8} {'낙폭%':<8} {'승률%':<8}")
        print("-"*120)
        
        # 샤프 비율로 정렬
        comparison_results.sort(key=lambda x: x['Sharpe_Ratio'], reverse=True)
        
        for result in comparison_results:
            print(f"{result['Number']:<4} {result['Strategy']:<25} {result['Annual_Return_%']:<10.2f} "
                  f"{result['Sharpe_Ratio']:<8.2f} {result['Sortino_Ratio']:<8.2f} "
                  f"{result['Calmar_Ratio']:<8.2f} {result['Volatility_%']:<8.2f} "
                  f"{result['Max_Drawdown_%']:<8.2f} {result['Win_Rate_%']:<8.2f}")
        
        # 등급 매기기
        print(f"\n🏆 전략 등급 평가")
        print("-"*60)
        
        for result in comparison_results:
            grade = calculate_strategy_grade(result)
            print(f"{result['Strategy']:<25} : {grade}")
        
        # 추가 분석 옵션
        print(f"\n📈 추가 분석 옵션:")
        print("1. 시장 상황별 가이드")
        print("2. 리스크 관리 가이드")
        print("3. 초보자 추천 전략")
        
        choice = input("추가 분석을 원하시면 번호를 입력하세요 (1-3, 또는 Enter로 종료): ").strip()
        
        if choice == '1':
            show_market_timing_guide()
        elif choice == '2':
            show_risk_management_guide()
        elif choice == '3':
            show_beginner_guide()
        
    except Exception as e:
        print(f"❌ 분석 중 오류 발생: {str(e)}")

def show_beginner_guide():
    """초보자 가이드 표시"""
    from .strategy_guide import get_beginner_recommendations
    
    recommendations = get_beginner_recommendations()
    
    print("""
👨‍🎓 초보자를 위한 전략 가이드

🎯 시작 추천 전략:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
    
    for strategy_num in recommendations['start_with']:
        reason = recommendations['reasons'][strategy_num]
        print(f"  {strategy_num}번. {reason}")
    
    print(f"""
📚 학습 경로:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
    
    for i, step in enumerate(recommendations['learning_path'], 1):
        print(f"  {i}. {step}")
    
    print(f"""
⚠️ 주의사항:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
    
    for caution in recommendations['cautions']:
        print(f"  • {caution}")
    
    print(f"""
💡 실습 제안:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 먼저 'python main.py'로 1번 전략 테스트
2. 결과 분석하고 성과 지표 이해하기
3. 2번, 3번 전략도 순서대로 테스트
4. 'python main.py compare'로 여러 전략 한번에 비교
5. 가장 적합한 전략 선택하여 실제 투자 고려
    """)

def _calculate_average_performance(results):
    """결과 리스트에서 평균 성과 계산"""
    if not results:
        return {}
    
    metrics = {
        'Annual_Return_%': np.mean([r.get('Annual_Return_%', 0) for r in results]),
        'Sharpe_Ratio': np.mean([r.get('Sharpe_Ratio', 0) for r in results]),
        'Sortino_Ratio': np.mean([r.get('Sortino_Ratio', 0) for r in results]),
        'Calmar_Ratio': np.mean([r.get('Calmar_Ratio', 0) for r in results]),
        'Max_Drawdown_%': np.mean([r.get('Max_Drawdown_%', 0) for r in results]),
        'Win_Rate_%': np.mean([r.get('Win_Rate_%', 0) for r in results]),
        'Volatility_%': np.mean([r.get('Volatility_%', 0) for r in results])
    }
    
    return metrics

def run_strategy_tournament():
    """전략 토너먼트 - 모든 전략 비교"""
    print("🏆 퀀트 전략 토너먼트 - 20개 전략 완전 비교")
    
    backtester = QuantBacktester()
    
    all_strategies = [str(i) for i in range(1, 21)]
    tournament_results = []
    
    print(f"📊 {len(all_strategies)}개 전략을 모두 분석합니다...")
    print("⏱️ 예상 소요시간: 3-5분")
    
    for i, strategy_num in enumerate(all_strategies, 1):
        strategy_name = backtester.strategies[strategy_num][0]
        print(f"🔄 [{i:2d}/20] {strategy_name} 분석 중...")
        
        try:
            backtest_data = backtester.run_backtest(strategy_num)
            
            if backtest_data['results']:
                # 상위 10개 종목 평균 성과 계산
                top_results = backtest_data['results'][:10]
                avg_metrics = _calculate_average_performance(top_results)
                
                tournament_results.append({
                    'Rank': 0,  # 나중에 설정
                    'Number': strategy_num,
                    'Strategy': strategy_name,
                    'Annual_Return_%': avg_metrics.get('Annual_Return_%', 0),
                    'Sharpe_Ratio': avg_metrics.get('Sharpe_Ratio', 0),
                    'Max_Drawdown_%': avg_metrics.get('Max_Drawdown_%', 0),
                    'Win_Rate_%': avg_metrics.get('Win_Rate_%', 0),
                    'Grade': calculate_strategy_grade(avg_metrics)
                })
        except Exception as e:
            print(f"⚠️ {strategy_name} 분석 실패: {str(e)}")
            continue
    
    # 순위 매기기 (샤프 비율 기준)
    tournament_results.sort(key=lambda x: x['Sharpe_Ratio'], reverse=True)
    for i, result in enumerate(tournament_results, 1):
        result['Rank'] = i
    
    # 토너먼트 결과 표시
    print(f"\n🏆 퀀트 전략 토너먼트 최종 결과")
    print("="*100)
    print(f"{'순위':<4} {'번호':<4} {'전략':<25} {'연수익률%':<10} {'샤프':<8} {'낙폭%':<8} {'승률%':<8} {'등급':<15}")
    print("-"*100)
    
    for result in tournament_results:
        print(f"{result['Rank']:<4} {result['Number']:<4} {result['Strategy']:<25} "
              f"{result['Annual_Return_%']:<10.2f} {result['Sharpe_Ratio']:<8.2f} "
              f"{result['Max_Drawdown_%']:<8.2f} {result['Win_Rate_%']:<8.2f} {result['Grade']:<15}")
    
    # 시상식
    if tournament_results:
        print(f"\n🎉 시상식")
        print("="*60)
        
        # 금메달
        if len(tournament_results) >= 1:
            gold = tournament_results[0]
            print(f"🥇 금메달: {gold['Strategy']}")
            print(f"   샤프 비율: {gold['Sharpe_Ratio']:.2f}, 연수익률: {gold['Annual_Return_%']:.1f}%")
        
        # 은메달
        if len(tournament_results) >= 2:
            silver = tournament_results[1]
            print(f"🥈 은메달: {silver['Strategy']}")
            print(f"   샤프 비율: {silver['Sharpe_Ratio']:.2f}, 연수익률: {silver['Annual_Return_%']:.1f}%")
        
        # 동메달
        if len(tournament_results) >= 3:
            bronze = tournament_results[2]
            print(f"🥉 동메달: {bronze['Strategy']}")
            print(f"   샤프 비율: {bronze['Sharpe_Ratio']:.2f}, 연수익률: {bronze['Annual_Return_%']:.1f}%")
        
        # 특별상
        best_return = max(tournament_results, key=lambda x: x['Annual_Return_%'])
        lowest_risk = min(tournament_results, key=lambda x: x['Max_Drawdown_%'])
        
        print(f"\n🏅 특별상")
        print(f"💰 최고수익상: {best_return['Strategy']} ({best_return['Annual_Return_%']:.1f}%)")
        print(f"🛡️ 안정성상: {lowest_risk['Strategy']} (낙폭 {lowest_risk['Max_Drawdown_%']:.1f}%)")
    
    return tournament_results