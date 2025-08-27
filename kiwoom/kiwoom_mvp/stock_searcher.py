"""
file: kiwoom_mvp/stock_searcher.py
키움증권 주식 데이터 수집기 - 종목 검색 엔진
Phase 1 MVP

종목명/코드 검색, 부분검색, 자동완성 기능 제공
종목 리스트 관리 및 캐싱
"""

import os
import csv
import logging
import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import pandas as pd
from config import get_config

class StockSearcher:
    """종목 검색 엔진 클래스"""
    
    def __init__(self):
        """종목 검색기 초기화"""
        self.config = get_config()
        self.logger = logging.getLogger(__name__)
        
        # 종목 데이터 저장소
        self.stock_list: List[Dict] = []
        self.stock_code_map: Dict[str, Dict] = {}  # 코드로 빠른 검색
        self.stock_name_map: Dict[str, Dict] = {}  # 이름으로 빠른 검색
        
        # 종목 리스트 파일 경로
        self.stock_list_file = self.config.BASE_DIR / 'data' / 'stock_list.csv'
        
        # 초기화
        self._load_stock_list()
    
    def _load_stock_list(self):
        """종목 리스트 로드 (파일 또는 기본 데이터)"""
        try:
            if self.stock_list_file.exists():
                self._load_from_file()
                self.logger.info(f"✅ 종목 리스트 파일 로드: {len(self.stock_list)}개")
            else:
                self._create_default_stock_list()
                self.logger.info(f"✅ 기본 종목 리스트 생성: {len(self.stock_list)}개")
            
            # 검색 인덱스 구축
            self._build_search_index()
            
        except Exception as e:
            self.logger.error(f"❌ 종목 리스트 로드 실패: {e}")
            self._create_default_stock_list()
    
    def _load_from_file(self):
        """CSV 파일에서 종목 리스트 로드"""
        try:
            df = pd.read_csv(self.stock_list_file, encoding='utf-8-sig')
            self.stock_list = df.to_dict('records')
            
        except Exception as e:
            self.logger.error(f"❌ 종목 리스트 파일 읽기 오류: {e}")
            raise
    
    def _create_default_stock_list(self):
        """기본 종목 리스트 생성 (주요 종목들)"""
        self.stock_list = [
            # 대형주
            {'code': '005930', 'name': '삼성전자', 'market': 'KOSPI', 'sector': 'IT'},
            {'code': '000660', 'name': 'SK하이닉스', 'market': 'KOSPI', 'sector': 'IT'},
            {'code': '035420', 'name': 'NAVER', 'market': 'KOSPI', 'sector': 'IT'},
            {'code': '035720', 'name': '카카오', 'market': 'KOSPI', 'sector': 'IT'},
            {'code': '005380', 'name': '현대차', 'market': 'KOSPI', 'sector': '자동차'},
            {'code': '000270', 'name': '기아', 'market': 'KOSPI', 'sector': '자동차'},
            {'code': '051910', 'name': 'LG화학', 'market': 'KOSPI', 'sector': '화학'},
            {'code': '066570', 'name': 'LG전자', 'market': 'KOSPI', 'sector': '전자'},
            {'code': '003550', 'name': 'LG', 'market': 'KOSPI', 'sector': '지주회사'},
            {'code': '034220', 'name': 'LG디스플레이', 'market': 'KOSPI', 'sector': '디스플레이'},
            
            # 금융주
            {'code': '055550', 'name': '신한지주', 'market': 'KOSPI', 'sector': '금융'},
            {'code': '105560', 'name': 'KB금융', 'market': 'KOSPI', 'sector': '금융'},
            {'code': '086790', 'name': '하나금융지주', 'market': 'KOSPI', 'sector': '금융'},
            {'code': '323410', 'name': '카카오뱅크', 'market': 'KOSPI', 'sector': '금융'},
            
            # 바이오/제약
            {'code': '068270', 'name': '셀트리온', 'market': 'KOSPI', 'sector': '바이오'},
            {'code': '207940', 'name': '삼성바이오로직스', 'market': 'KOSPI', 'sector': '바이오'},
            {'code': '196170', 'name': '알테오젠', 'market': 'KOSDAQ', 'sector': '바이오'},
            {'code': '302440', 'name': '에이치엘비', 'market': 'KOSDAQ', 'sector': '바이오'},
            
            # 에너지/소재
            {'code': '005490', 'name': 'POSCO홀딩스', 'market': 'KOSPI', 'sector': '철강'},
            {'code': '003670', 'name': '포스코퓨처엠', 'market': 'KOSPI', 'sector': '소재'},
            {'code': '373220', 'name': 'LG에너지솔루션', 'market': 'KOSPI', 'sector': '배터리'},
            {'code': '006400', 'name': '삼성SDI', 'market': 'KOSPI', 'sector': '배터리'},
            
            # 통신
            {'code': '017670', 'name': 'SK텔레콤', 'market': 'KOSPI', 'sector': '통신'},
            {'code': '030200', 'name': 'KT', 'market': 'KOSPI', 'sector': '통신'},
            {'code': '032640', 'name': 'LG유플러스', 'market': 'KOSPI', 'sector': '통신'},
            
            # 게임/엔터테인먼트
            {'code': '036570', 'name': '엔씨소프트', 'market': 'KOSPI', 'sector': '게임'},
            {'code': '251270', 'name': '넷마블', 'market': 'KOSPI', 'sector': '게임'},
            {'code': '122870', 'name': '와이지엔터테인먼트', 'market': 'KOSDAQ', 'sector': '엔터'},
            
            # 유통/소비재
            {'code': '011170', 'name': '롯데케미칼', 'market': 'KOSPI', 'sector': '화학'},
            {'code': '097950', 'name': 'CJ제일제당', 'market': 'KOSPI', 'sector': '식품'},
            {'code': '271560', 'name': '오리온', 'market': 'KOSPI', 'sector': '식품'},
            
            # 우선주
            {'code': '005935', 'name': '삼성전자우', 'market': 'KOSPI', 'sector': 'IT'},
            {'code': '005385', 'name': '현대차우', 'market': 'KOSPI', 'sector': '자동차'},
        ]
        
        # 기본 종목 리스트 파일로 저장
        self._save_to_file()
    
    def _save_to_file(self):
        """종목 리스트를 CSV 파일로 저장"""
        try:
            # 디렉토리 생성
            self.stock_list_file.parent.mkdir(parents=True, exist_ok=True)
            
            # CSV로 저장
            df = pd.DataFrame(self.stock_list)
            df.to_csv(self.stock_list_file, index=False, encoding='utf-8-sig')
            
            self.logger.info(f"✅ 종목 리스트 파일 저장 완료: {self.stock_list_file}")
            
        except Exception as e:
            self.logger.error(f"❌ 종목 리스트 저장 실패: {e}")
    
    def _build_search_index(self):
        """검색 인덱스 구축"""
        self.stock_code_map.clear()
        self.stock_name_map.clear()
        
        for stock in self.stock_list:
            code = stock['code']
            name = stock['name']
            
            # 코드별 인덱스
            self.stock_code_map[code] = stock
            
            # 이름별 인덱스 (대소문자 무시)
            name_key = name.lower()
            if name_key not in self.stock_name_map:
                self.stock_name_map[name_key] = []
            self.stock_name_map[name_key].append(stock)
        
        self.logger.debug(f"📊 검색 인덱스 구축 완료: {len(self.stock_code_map)}개 종목")
    
    def search_by_code(self, code: str) -> Optional[Dict]:
        """종목코드로 정확 검색"""
        if not code:
            return None
        
        # 6자리 숫자 형태로 변환
        clean_code = self._clean_stock_code(code)
        if not clean_code:
            return None
        
        return self.stock_code_map.get(clean_code)
    
    def search_by_name(self, name: str) -> List[Dict]:
        """종목명으로 정확 검색"""
        if not name:
            return []
        
        name_key = name.lower().strip()
        return self.stock_name_map.get(name_key, [])
    
    def search_partial(self, query: str, max_results: int = 10) -> List[Dict]:
        """부분 검색 (종목명 부분 일치)"""
        if not query or len(query) < 1:
            return []
        
        query_lower = query.lower().strip()
        results = []
        
        # 종목명에서 부분 검색
        for stock in self.stock_list:
            stock_name_lower = stock['name'].lower()
            
            # 부분 일치 검사
            if query_lower in stock_name_lower:
                # 매칭 점수 계산 (정확도 순 정렬용)
                if stock_name_lower.startswith(query_lower):
                    score = 100  # 시작 일치
                elif stock_name_lower == query_lower:
                    score = 200  # 완전 일치
                else:
                    score = 50   # 부분 일치
                
                results.append({
                    'stock': stock,
                    'score': score
                })
        
        # 점수 순으로 정렬 (높은 점수 우선)
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # 최대 결과 개수만큼 반환
        return [item['stock'] for item in results[:max_results]]
    
    def search_smart(self, query: str, max_results: int = 10) -> List[Dict]:
        """스마트 검색 (코드/이름 자동 판별)"""
        if not query:
            return []
        
        query = query.strip()
        
        # 1. 숫자만 있으면 종목코드로 판단
        if query.isdigit():
            if len(query) == 6:
                # 정확한 6자리 코드
                result = self.search_by_code(query)
                return [result] if result else []
            else:
                # 부분 코드 검색
                return self._search_partial_code(query, max_results)
        
        # 2. 종목명으로 검색
        # 정확 일치 우선
        exact_results = self.search_by_name(query)
        if exact_results:
            return exact_results[:max_results]
        
        # 부분 일치
        return self.search_partial(query, max_results)
    
    def _search_partial_code(self, partial_code: str, max_results: int = 10) -> List[Dict]:
        """부분 종목코드 검색"""
        results = []
        
        for code, stock in self.stock_code_map.items():
            if code.startswith(partial_code):
                results.append(stock)
                if len(results) >= max_results:
                    break
        
        return results
    
    def _clean_stock_code(self, code: str) -> Optional[str]:
        """종목코드 정리 (6자리 숫자 형태로 변환)"""
        if not code:
            return None
        
        # 숫자만 추출
        clean_code = re.sub(r'[^0-9]', '', code)
        
        # 6자리가 아니면 None
        if len(clean_code) != 6:
            return None
        
        return clean_code
    
    def get_stock_info(self, code: str) -> Optional[Dict]:
        """종목 상세 정보 조회"""
        stock = self.search_by_code(code)
        if not stock:
            return None
        
        return {
            'code': stock['code'],
            'name': stock['name'],
            'market': stock.get('market', '알 수 없음'),
            'sector': stock.get('sector', '알 수 없음'),
            'display_name': f"{stock['name']}({stock['code']})"
        }
    
    def add_stock(self, code: str, name: str, market: str = '', sector: str = '') -> bool:
        """새 종목 추가"""
        try:
            # 종목코드 검증
            if not self.config.validate_stock_code(code):
                self.logger.warning(f"⚠️ 잘못된 종목코드: {code}")
                return False
            
            # 중복 확인
            if self.search_by_code(code):
                self.logger.warning(f"⚠️ 이미 존재하는 종목: {code}")
                return False
            
            # 새 종목 추가
            new_stock = {
                'code': code,
                'name': name.strip(),
                'market': market.strip(),
                'sector': sector.strip()
            }
            
            self.stock_list.append(new_stock)
            
            # 검색 인덱스 재구축
            self._build_search_index()
            
            # 파일 저장
            self._save_to_file()
            
            self.logger.info(f"✅ 새 종목 추가: {name}({code})")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 종목 추가 실패: {e}")
            return False
    
    def remove_stock(self, code: str) -> bool:
        """종목 제거"""
        try:
            # 종목 찾기
            stock = self.search_by_code(code)
            if not stock:
                self.logger.warning(f"⚠️ 종목을 찾을 수 없음: {code}")
                return False
            
            # 리스트에서 제거
            self.stock_list = [s for s in self.stock_list if s['code'] != code]
            
            # 검색 인덱스 재구축
            self._build_search_index()
            
            # 파일 저장
            self._save_to_file()
            
            self.logger.info(f"✅ 종목 제거: {stock['name']}({code})")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 종목 제거 실패: {e}")
            return False
    
    def get_all_stocks(self) -> List[Dict]:
        """전체 종목 리스트 반환"""
        return self.stock_list.copy()
    
    def get_stocks_by_market(self, market: str) -> List[Dict]:
        """시장별 종목 리스트"""
        return [stock for stock in self.stock_list if stock.get('market', '').upper() == market.upper()]
    
    def get_stocks_by_sector(self, sector: str) -> List[Dict]:
        """섹터별 종목 리스트"""
        return [stock for stock in self.stock_list if sector.lower() in stock.get('sector', '').lower()]
    
    def get_search_suggestions(self, query: str, max_suggestions: int = 5) -> List[str]:
        """검색 자동완성 제안"""
        if not query or len(query) < 1:
            return []
        
        query_lower = query.lower()
        suggestions = set()
        
        for stock in self.stock_list:
            name = stock['name']
            name_lower = name.lower()
            
            # 시작 문자가 일치하는 경우
            if name_lower.startswith(query_lower):
                suggestions.add(name)
            # 부분 일치하는 경우
            elif query_lower in name_lower:
                suggestions.add(name)
            
            if len(suggestions) >= max_suggestions:
                break
        
        return list(suggestions)[:max_suggestions]
    
    def validate_and_format_display(self, query: str) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """검색 결과 검증 및 표시용 포맷팅"""
        if not query:
            return False, None, None
        
        # 스마트 검색
        results = self.search_smart(query.strip(), 1)
        
        if not results:
            return False, f"❌ '{query}' 검색 결과가 없습니다.", None
        
        if len(results) == 1:
            stock = results[0]
            display = f"✅ {stock['name']} ({stock['code']})"
            return True, display, stock
        else:
            return False, f"⚠️ '{query}' 검색 결과가 여러 개입니다.", None
    
    def get_stats(self) -> Dict:
        """종목 검색기 통계"""
        market_stats = {}
        sector_stats = {}
        
        for stock in self.stock_list:
            market = stock.get('market', '알 수 없음')
            sector = stock.get('sector', '알 수 없음')
            
            market_stats[market] = market_stats.get(market, 0) + 1
            sector_stats[sector] = sector_stats.get(sector, 0) + 1
        
        return {
            'total_stocks': len(self.stock_list),
            'markets': market_stats,
            'sectors': sector_stats
        }

# 전역 검색기 인스턴스
_searcher = None

def get_stock_searcher() -> StockSearcher:
    """종목 검색기 싱글톤 인스턴스 반환"""
    global _searcher
    if _searcher is None:
        _searcher = StockSearcher()
    return _searcher

if __name__ == "__main__":
    # 테스트 코드
    import logging
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🧪 종목 검색기 테스트 시작...")
    print("=" * 50)
    
    # 검색기 생성
    searcher = get_stock_searcher()
    
    # 통계 출력
    stats = searcher.get_stats()
    print(f"📊 종목 검색기 통계:")
    print(f"   - 총 종목 수: {stats['total_stocks']}개")
    print(f"   - 시장별: {stats['markets']}")
    print(f"   - 섹터별: {stats['sectors']}")
    
    # 검색 테스트
    print(f"\n🔍 검색 테스트:")
    
    test_queries = [
        "005930",      # 정확한 코드
        "삼성전자",     # 정확한 이름
        "삼성",        # 부분 검색
        "LG",          # 부분 검색 (여러 결과)
        "99999",       # 없는 코드
        "없는회사",     # 없는 이름
    ]
    
    for query in test_queries:
        print(f"\n'{query}' 검색:")
        results = searcher.search_smart(query, 5)
        
        if results:
            for i, stock in enumerate(results, 1):
                print(f"   {i}. {stock['name']} ({stock['code']}) - {stock.get('market', 'N/A')}")
        else:
            print("   검색 결과 없음")
    
    # 자동완성 테스트
    print(f"\n💡 자동완성 테스트:")
    suggestions = searcher.get_search_suggestions("삼성", 3)
    print(f"   '삼성' 자동완성: {suggestions}")
    
    print("\n" + "=" * 50)
    print("🎉 종목 검색기 테스트 완료!")