#!/usr/bin/env python3
"""
전략 목록을 반환하는 스크립트
"""

import json
import sys
import os

# quant_engine 모듈 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'quant_engine'))

try:
    from strategy_factory import strategy_registry, initialize_strategy_system
    
    # 전략 시스템 초기화
    initialize_strategy_system()
    
    strategies = []
    
    # 전략별 메타데이터 수집
    strategy_names = strategy_registry.list_strategies()
    
    for strategy_name in strategy_names:
        try:
            metadata = strategy_registry.get_strategy_metadata(strategy_name)
            
            if 'metadata' in metadata:
                meta = metadata['metadata']
                
                # 카테고리 결정 (기본/고급)
                category = 'advanced' if meta.category.value == 'advanced' else 'basic'
                
                strategy_info = {
                    'id': strategy_name,
                    'name': meta.name,
                    'category': category,
                    'description': meta.description,
                    'riskLevel': meta.risk_level.value,
                    'complexity': meta.complexity.value,
                    'expectedReturn': meta.expected_return,
                    'volatility': meta.volatility,
                    'details': f"{meta.description}. 최소 투자기간: {meta.min_investment_period}, 리밸런싱: {meta.rebalancing_frequency}"
                }
                
                strategies.append(strategy_info)
                
        except Exception as e:
            # 개별 전략 오류는 무시하고 계속 진행
            continue
    
    # JSON 출력
    print(json.dumps(strategies, ensure_ascii=False, indent=2))
    
except Exception as e:
    error_response = {
        'error': str(e),
        'strategies': []  # 빈 배열 반환
    }
    print(json.dumps(error_response, ensure_ascii=False))
    sys.exit(1)