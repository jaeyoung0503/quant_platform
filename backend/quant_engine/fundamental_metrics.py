"""
file: strategy_engine/fundamental_metrics.py
Fundamental Metrics Module - 재무비율 계산 함수들
PER, PBR, ROE, 부채비율 등 펀더멘털 지표들 200여 라인
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Union, Tuple
import warnings

# 밸류에이션 지표들
def price_to_earnings_ratio(price: float, earnings_per_share: float) -> Optional[float]:
    """주가수익비율 (PER)"""
    if earnings_per_share <= 0:
        return None
    return price / earnings_per_share

def price_to_book_ratio(price: float, book_value_per_share: float) -> Optional[float]:
    """주가순자산비율 (PBR)"""
    if book_value_per_share <= 0:
        return None
    return price / book_value_per_share

def price_to_sales_ratio(market_cap: float, revenue: float) -> Optional[float]:
    """주가매출비율 (PSR)"""
    if revenue <= 0:
        return None
    return market_cap / revenue

def price_earnings_growth_ratio(pe_ratio: float, earnings_growth_rate: float) -> Optional[float]:
    """PEG 비율"""
    if earnings_growth_rate <= 0:
        return None
    return pe_ratio / (earnings_growth_rate * 100)

def enterprise_value_to_ebitda(enterprise_value: float, ebitda: float) -> Optional[float]:
    """EV/EBITDA"""
    if ebitda <= 0:
        return None
    return enterprise_value / ebitda

def enterprise_value_to_sales(enterprise_value: float, revenue: float) -> Optional[float]:
    """EV/Sales"""
    if revenue <= 0:
        return None
    return enterprise_value / revenue

# 수익성 지표들
def return_on_equity(net_income: float, shareholders_equity: float) -> Optional[float]:
    """자기자본수익률 (ROE)"""
    if shareholders_equity <= 0:
        return None
    return net_income / shareholders_equity

def return_on_assets(net_income: float, total_assets: float) -> Optional[float]:
    """총자산수익률 (ROA)"""
    if total_assets <= 0:
        return None
    return net_income / total_assets

def return_on_invested_capital(nopat: float, invested_capital: float) -> Optional[float]:
    """투하자본수익률 (ROIC)"""
    if invested_capital <= 0:
        return None
    return nopat / invested_capital

def gross_profit_margin(gross_profit: float, revenue: float) -> Optional[float]:
    """매출총이익률"""
    if revenue <= 0:
        return None
    return gross_profit / revenue

def operating_profit_margin(operating_income: float, revenue: float) -> Optional[float]:
    """영업이익률"""
    if revenue <= 0:
        return None
    return operating_income / revenue

def net_profit_margin(net_income: float, revenue: float) -> Optional[float]:
    """순이익률"""
    if revenue <= 0:
        return None
    return net_income / revenue

def ebitda_margin(ebitda: float, revenue: float) -> Optional[float]:
    """EBITDA 마진"""
    if revenue <= 0:
        return None
    return ebitda / revenue

# 안정성/레버리지 지표들
def debt_to_equity_ratio(total_debt: float, shareholders_equity: float) -> Optional[float]:
    """부채비율"""
    if shareholders_equity <= 0:
        return None
    return total_debt / shareholders_equity

def debt_to_assets_ratio(total_debt: float, total_assets: float) -> Optional[float]:
    """부채자산비율"""
    if total_assets <= 0:
        return None
    return total_debt / total_assets

def current_ratio(current_assets: float, current_liabilities: float) -> Optional[float]:
    """유동비율"""
    if current_liabilities <= 0:
        return None
    return current_assets / current_liabilities

def quick_ratio(current_assets: float, inventory: float, current_liabilities: float) -> Optional[float]:
    """당좌비율"""
    if current_liabilities <= 0:
        return None
    return (current_assets - inventory) / current_liabilities

def interest_coverage_ratio(ebit: float, interest_expense: float) -> Optional[float]:
    """이자보상비율"""
    if interest_expense <= 0:
        return None
    return ebit / interest_expense

def cash_ratio(cash_and_equivalents: float, current_liabilities: float) -> Optional[float]:
    """현금비율"""
    if current_liabilities <= 0:
        return None
    return cash_and_equivalents / current_liabilities

# 효율성 지표들
def asset_turnover(revenue: float, total_assets: float) -> Optional[float]:
    """자산회전율"""
    if total_assets <= 0:
        return None
    return revenue / total_assets

def inventory_turnover(cost_of_goods_sold: float, average_inventory: float) -> Optional[float]:
    """재고회전율"""
    if average_inventory <= 0:
        return None
    return cost_of_goods_sold / average_inventory

def receivables_turnover(revenue: float, average_receivables: float) -> Optional[float]:
    """매출채권회전율"""
    if average_receivables <= 0:
        return None
    return revenue / average_receivables

def days_sales_outstanding(average_receivables: float, revenue: float) -> Optional[float]:
    """매출채권회수기간 (DSO)"""
    if revenue <= 0:
        return None
    return (average_receivables / revenue) * 365

def days_inventory_outstanding(average_inventory: float, cost_of_goods_sold: float) -> Optional[float]:
    """재고회전기간 (DIO)"""
    if cost_of_goods_sold <= 0:
        return None
    return (average_inventory / cost_of_goods_sold) * 365

def cash_conversion_cycle(dso: float, dio: float, dpo: float) -> float:
    """현금전환주기 (CCC)"""
    return dso + dio - dpo

# 성장률 지표들
def revenue_growth_rate(current_revenue: float, previous_revenue: float) -> Optional[float]:
    """매출 성장률"""
    if previous_revenue <= 0:
        return None
    return (current_revenue - previous_revenue) / previous_revenue

def earnings_growth_rate(current_earnings: float, previous_earnings: float) -> Optional[float]:
    """순이익 성장률"""
    if previous_earnings <= 0:
        return None
    return (current_earnings - previous_earnings) / previous_earnings

def compound_annual_growth_rate(beginning_value: float, ending_value: float, periods: int) -> Optional[float]:
    """연평균성장률 (CAGR)"""
    if beginning_value <= 0 or periods <= 0:
        return None
    return (ending_value / beginning_value) ** (1/periods) - 1

def sustainable_growth_rate(roe: float, dividend_payout_ratio: float) -> float:
    """지속가능성장률"""
    retention_ratio = 1 - dividend_payout_ratio
    return roe * retention_ratio

# 배당 관련 지표들
def dividend_yield(annual_dividend: float, stock_price: float) -> Optional[float]:
    """배당수익률"""
    if stock_price <= 0:
        return None
    return annual_dividend / stock_price

def dividend_payout_ratio(dividend_per_share: float, earnings_per_share: float) -> Optional[float]:
    """배당성향"""
    if earnings_per_share <= 0:
        return None
    return dividend_per_share / earnings_per_share

def dividend_coverage_ratio(earnings_per_share: float, dividend_per_share: float) -> Optional[float]:
    """배당커버리지"""
    if dividend_per_share <= 0:
        return None
    return earnings_per_share / dividend_per_share

# 종합 평가 지표들
def piotroski_f_score(financial_data: Dict[str, float]) -> int:
    """피오트로스키 F-Score (재무건전성 점수)"""
    score = 0
    
    # 수익성 (4점)
    if financial_data.get('net_income', 0) > 0:
        score += 1
    if financial_data.get('roa', 0) > 0:
        score += 1
    if financial_data.get('operating_cash_flow', 0) > 0:
        score += 1
    if financial_data.get('operating_cash_flow', 0) > financial_data.get('net_income', 0):
        score += 1
    
    # 레버리지, 유동성, 자금 조달 (3점)
    if financial_data.get('debt_to_equity_current', 0) < financial_data.get('debt_to_equity_previous', 1):
        score += 1
    if financial_data.get('current_ratio_current', 0) > financial_data.get('current_ratio_previous', 0):
        score += 1
    if financial_data.get('shares_outstanding_current', 0) <= financial_data.get('shares_outstanding_previous', 1):
        score += 1
    
    # 운영 효율성 (2점)
    if financial_data.get('gross_margin_current', 0) > financial_data.get('gross_margin_previous', 0):
        score += 1
    if financial_data.get('asset_turnover_current', 0) > financial_data.get('asset_turnover_previous', 0):
        score += 1
    
    return score

def altman_z_score(financial_data: Dict[str, float]) -> Optional[float]:
    """알트만 Z-Score (파산 위험도)"""
    try:
        working_capital = financial_data['current_assets'] - financial_data['current_liabilities']
        total_assets = financial_data['total_assets']
        market_value_equity = financial_data['market_cap']
        total_liabilities = financial_data['total_liabilities']
        revenue = financial_data['revenue']
        retained_earnings = financial_data['retained_earnings']
        ebit = financial_data['ebit']
        
        if total_assets <= 0:
            return None
        
        z1 = 1.2 * (working_capital / total_assets)
        z2 = 1.4 * (retained_earnings / total_assets)
        z3 = 3.3 * (ebit / total_assets)
        z4 = 0.6 * (market_value_equity / total_liabilities)
        z5 = 1.0 * (revenue / total_assets)
        
        z_score = z1 + z2 + z3 + z4 + z5
        return z_score
        
    except (KeyError, ZeroDivisionError):
        return None

def m_score(financial_data: Dict[str, float]) -> Optional[float]:
    """베니시 M-Score (분식회계 탐지)"""
    try:
        # 간단화된 M-Score 계산
        score = 0.0
        
        # Days Sales Outstanding Index
        dso_current = financial_data.get('dso_current', 0)
        dso_previous = financial_data.get('dso_previous', 1)
        dsri = dso_current / dso_previous if dso_previous != 0 else 1
        
        # Gross Margin Index
        gm_current = financial_data.get('gross_margin_current', 0)
        gm_previous = financial_data.get('gross_margin_previous', 0)
        gmi = gm_previous / gm_current if gm_current != 0 else 1
        
        # Asset Quality Index
        total_assets = financial_data.get('total_assets', 1)
        ppe = financial_data.get('ppe', 0)
        current_assets = financial_data.get('current_assets', 0)
        aqi = (total_assets - current_assets - ppe) / total_assets
        
        # Sales Growth Index
        sales_current = financial_data.get('revenue_current', 1)
        sales_previous = financial_data.get('revenue_previous', 1)
        sgi = sales_current / sales_previous
        
        # Simplified M-Score
        m_score_value = -4.84 + 0.92*dsri + 0.528*gmi + 0.404*aqi + 0.892*sgi
        
        return m_score_value
        
    except (KeyError, ZeroDivisionError):
        return None

# 유틸리티 함수들
def calculate_enterprise_value(market_cap: float, total_debt: float, cash: float) -> float:
    """기업가치 (EV) 계산"""
    return market_cap + total_debt - cash

def calculate_book_value_per_share(shareholders_equity: float, shares_outstanding: float) -> Optional[float]:
    """주당순자산 (BPS)"""
    if shares_outstanding <= 0:
        return None
    return shareholders_equity / shares_outstanding

def calculate_earnings_per_share(net_income: float, shares_outstanding: float) -> Optional[float]:
    """주당순이익 (EPS)"""
    if shares_outstanding <= 0:
        return None
    return net_income / shares_outstanding

def calculate_free_cash_flow(operating_cash_flow: float, capex: float) -> float:
    """잉여현금흐름 (FCF)"""
    return operating_cash_flow - capex

def calculate_fcf_per_share(free_cash_flow: float, shares_outstanding: float) -> Optional[float]:
    """주당잉여현금흐름"""
    if shares_outstanding <= 0:
        return None
    return free_cash_flow / shares_outstanding

def working_capital(current_assets: float, current_liabilities: float) -> float:
    """운전자본"""
    return current_assets - current_liabilities

def normalize_ratio(ratio_value: Optional[float], industry_median: float) -> Optional[float]:
    """업종 대비 정규화"""
    if ratio_value is None or industry_median <= 0:
        return None
    return ratio_value / industry_median

def calculate_quality_score(financial_data: Dict[str, float]) -> float:
    """종합 품질 점수 (0-1)"""
    score = 0.0
    max_score = 0.0
    
    # ROE
    roe = financial_data.get('roe', 0)
    if roe > 0.15:
        score += 0.25
    elif roe > 0.10:
        score += 0.15
    max_score += 0.25
    
    # 부채비율
    debt_ratio = financial_data.get('debt_to_equity', 1.0)
    if debt_ratio < 0.3:
        score += 0.2
    elif debt_ratio < 0.5:
        score += 0.15
    max_score += 0.2
    
    # 유동비율
    current_ratio = financial_data.get('current_ratio', 1.0)
    if current_ratio > 2.0:
        score += 0.15
    elif current_ratio > 1.5:
        score += 0.1
    max_score += 0.15
    
    # 이익 성장률
    earnings_growth = financial_data.get('earnings_growth', 0)
    if earnings_growth > 0.1:
        score += 0.2
    elif earnings_growth > 0.05:
        score += 0.1
    max_score += 0.2
    
    # 매출 성장률
    revenue_growth = financial_data.get('revenue_growth', 0)
    if revenue_growth > 0.1:
        score += 0.2
    elif revenue_growth > 0.05:
        score += 0.1
    max_score += 0.2
    
    return score / max_score if max_score > 0 else 0.0

def calculate_financial_strength_rank(financial_data: Dict[str, float]) -> str:
    """재무 건전성 등급"""
    score = 0
    
    # 수익성
    roe = financial_data.get('roe', 0)
    if roe > 0.2:
        score += 3
    elif roe > 0.15:
        score += 2
    elif roe > 0.1:
        score += 1
    
    # 안정성
    debt_ratio = financial_data.get('debt_to_equity', 1.0)
    if debt_ratio < 0.3:
        score += 3
    elif debt_ratio < 0.5:
        score += 2
    elif debt_ratio < 0.8:
        score += 1
    
    # 유동성
    current_ratio = financial_data.get('current_ratio', 1.0)
    if current_ratio > 3.0:
        score += 3
    elif current_ratio > 2.0:
        score += 2
    elif current_ratio > 1.2:
        score += 1
    
    # 성장성
    revenue_growth = financial_data.get('revenue_growth', 0)
    if revenue_growth > 0.15:
        score += 3
    elif revenue_growth > 0.1:
        score += 2
    elif revenue_growth > 0.05:
        score += 1
    
    # 등급 매핑
    if score >= 10:
        return 'A+'
    elif score >= 8:
        return 'A'
    elif score >= 6:
        return 'B+'
    elif score >= 4:
        return 'B'
    elif score >= 2:
        return 'C'
    else:
        return 'D'
