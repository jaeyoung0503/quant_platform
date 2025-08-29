'use client';

import React, { useState, useCallback } from 'react';
import { Play, Plus, Save, BarChart3, FileText, TrendingUp, AlertCircle, CheckCircle } from 'lucide-react';
import { useBacktest } from '../../hooks/useBacktest';
import { useStrategies } from '../../hooks/useStrategies';
import { usePortfolio } from '../../hooks/usePortfolio';
import type { BacktestRequest, BacktestResult } from '../../types/api';

export default function QuantBacktestPage() {
  // 백테스트 설정
  const [backtestYear, setBacktestYear] = useState(2024);
  const [outputCount, setOutputCount] = useState(20);
  const [selectedStock, setSelectedStock] = useState<BacktestResult | null>(null);
  
  // API Hooks - 백엔드에서 20개 전략 불러오기
  const { strategies, updateStrategy, normalizeWeights, isLoading: strategiesLoading, error: strategiesError } = useStrategies();
  const { 
    isLoading: backtestLoading, 
    error: backtestError, 
    results, 
    reliability, 
    totalAnalyzed, 
    conditionMet,
    runBacktest, 
    updateResults,
    clearError 
  } = useBacktest();
  
  const {
    portfolioStocks,
    addStock,
    removeStock,
    savePortfolio,
    isSaving,
    saveError,
    portfolioStats,
    clearSaveError
  } = usePortfolio();

  // 전략 선택/해제
  const toggleStrategy = useCallback((id: string) => {
    const strategy = strategies.find(s => s.id === id);
    if (!strategy) return;

    updateStrategy(id, {
      selected: !strategy.selected,
      weight: strategy.selected ? 0 : 25
    });
    
    setTimeout(normalizeWeights, 0);
  }, [strategies, updateStrategy, normalizeWeights]);

  // 가중치 조정
  const updateWeight = useCallback((id: string, newWeight: number) => {
    updateStrategy(id, { weight: newWeight });
    setTimeout(normalizeWeights, 0);
  }, [updateStrategy, normalizeWeights]);

  // 파라미터 업데이트
  const updateParam = useCallback((strategyId: string, paramName: string, value: any) => {
    const strategy = strategies.find(s => s.id === strategyId);
    if (!strategy) return;

    updateStrategy(strategyId, {
      params: { ...strategy.params, [paramName]: value }
    });
  }, [strategies, updateStrategy]);

  // 백테스트 실행 - CSV 데이터 처리
  const handleRunBacktest = useCallback(async () => {
    const selectedStrategies = strategies.filter(s => s.selected);
    
    if (selectedStrategies.length === 0) {
      alert('최소 하나의 전략을 선택해주세요.');
      return;
    }

    const totalWeight = selectedStrategies.reduce((sum, s) => sum + s.weight, 0);
    if (Math.abs(totalWeight - 100) > 1) {
      alert('전략의 총 가중치가 100%가 되어야 합니다.');
      return;
    }

    const request: BacktestRequest = {
      strategies: selectedStrategies.map(s => ({
        id: s.id,
        weight: s.weight,
        params: s.params,
      })),
      year: backtestYear,
      outputCount: outputCount,
    };

    clearError();
    await runBacktest(request);
  }, [strategies, backtestYear, outputCount, runBacktest, clearError]);

  // 종목 포트폴리오 추가/제거
  const toggleStockSelection = useCallback((stock: BacktestResult) => {
    const updatedResults = results.map(result => 
      result.stockCode === stock.stockCode 
        ? { ...result, selected: !result.selected }
        : result
    );
    
    updateResults(updatedResults);

    if (stock.selected) {
      removeStock(stock.stockCode);
    } else {
      addStock(stock);
    }
  }, [results, updateResults, addStock, removeStock]);

  // 포트폴리오 저장
  const handleSavePortfolio = useCallback(async () => {
    clearSaveError();
    const success = await savePortfolio(strategies);
    if (success) {
      alert('포트폴리오가 성공적으로 저장되었습니다!');
    }
  }, [savePortfolio, strategies, clearSaveError]);

  // 총 가중치 계산
  const totalWeight = strategies.filter(s => s.selected).reduce((sum, s) => sum + s.weight, 0);

  // 로딩 상태
  if (strategiesLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-400 mx-auto mb-4"></div>
          <div className="text-gray-300">백엔드에서 전략 데이터를 불러오는 중...</div>
          <div className="text-sm text-gray-500 mt-2">API 연결: /backend/quant_engine</div>
        </div>
      </div>
    );
  }

  // 전략 로딩 에러 또는 데이터 없음
  if (strategiesError || strategies.length === 0) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center max-w-2xl">
          <AlertCircle className="w-16 h-16 text-red-400 mx-auto mb-6" />
          <div className="text-2xl font-bold text-gray-100 mb-4">
            {strategiesError ? '백엔드 연결 실패' : '전략 데이터 없음'}
          </div>
          
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 mb-6">
            <div className="text-left space-y-4">
              <div>
                <h3 className="font-semibold text-gray-200 mb-2">필요한 백엔드 설정:</h3>
                <div className="text-sm text-gray-400 space-y-1">
                  <div>• 백엔드 서버: http://localhost:8000</div>
                  <div>• API 엔드포인트: /backend/quant_engine/strategies</div>
                  <div>• 데이터 소스: /public/data/*.csv 파일</div>
                </div>
              </div>
              
              <div>
                <h3 className="font-semibold text-gray-200 mb-2">전략 데이터 형식:</h3>
                <div className="text-xs text-gray-400 bg-gray-700 p-3 rounded font-mono">
                  {`{
  "success": true,
  "strategies": [
    {
      "id": "strategy_name",
      "name": "전략 표시명",
      "description": "전략 설명",
      "defaultParams": {
        "param1": 15,
        "param2": 30
      }
    }
  ]
}`}
                </div>
              </div>

              <div>
                <h3 className="font-semibold text-gray-200 mb-2">CSV 데이터 형식:</h3>
                <div className="text-xs text-gray-400 bg-gray-700 p-3 rounded font-mono">
                  {`date,year,ticker,name,market,open,high,low,close,volume
2024-01-02,2024,005930,삼성전자,KOSPI,71000,72000,70500,71500,1000000`}
                </div>
              </div>
            </div>
          </div>

          <div className="text-gray-300 mb-4">
            {strategiesError ? `오류: ${strategiesError}` : '백엔드에서 전략 데이터를 불러올 수 없습니다'}
          </div>
          
          <div className="flex gap-4 justify-center">
            <button 
              onClick={() => window.location.reload()}
              className="bg-gray-600 text-gray-100 px-6 py-3 rounded-xl hover:bg-gray-500 transition-colors"
            >
              다시 시도
            </button>
            <button 
              onClick={() => {
                const apiUrl = process.env.NEXT_PUBLIC_API_URL || '/api';
                window.open(`${apiUrl}/strategies`, '_blank');
              }}
              className="bg-blue-600 text-white px-6 py-3 rounded-xl hover:bg-blue-700 transition-colors"
            >
              API 직접 테스트
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      {/* 헤더 */}
      <header className="bg-gray-800 border-b border-gray-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gray-600 rounded-lg flex items-center justify-center text-gray-200">
              <TrendingUp />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-100">퀀트 백테스트 전략 분석 시스템</h1>
              <p className="text-gray-400 text-sm">AI 기반 퀀트 투자 전략 백테스트 및 포트폴리오 생성 시스템</p>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 에러 메시지 */}
        {backtestError && (
          <div className="mb-6 bg-red-900/20 border border-red-600 rounded-xl p-4 flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
            <div>
              <div className="font-semibold text-red-300">백테스트 실행 오류</div>
              <div className="text-red-200 text-sm">{backtestError}</div>
            </div>
            <button 
              onClick={clearError}
              className="ml-auto text-red-400 hover:text-red-300"
            >
              ✕
            </button>
          </div>
        )}

        {/* 포트폴리오 저장 에러 */}
        {saveError && (
          <div className="mb-6 bg-orange-900/20 border border-orange-600 rounded-xl p-4 flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-orange-400 flex-shrink-0" />
            <div>
              <div className="font-semibold text-orange-300">포트폴리오 저장 오류</div>
              <div className="text-orange-200 text-sm">{saveError}</div>
            </div>
            <button 
              onClick={clearSaveError}
              className="ml-auto text-orange-400 hover:text-orange-300"
            >
              ✕
            </button>
          </div>
        )}

        <div className="grid grid-cols-12 gap-6">
          {/* 왼쪽 사이드바 - 전략 설정 */}
          <div className="col-span-4 space-y-6">
            {/* 백테스트 설정 */}
            <div className="bg-gray-800 rounded-lg shadow-sm border border-gray-700 p-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2 text-gray-100">
                <span>⚙️</span> 백테스트 설정
              </h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">분석 연도</label>
                  <select 
                    value={backtestYear} 
                    onChange={(e) => setBacktestYear(Number(e.target.value))}
                    className="w-full p-3 bg-gray-700 border border-gray-600 rounded-md text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    disabled={backtestLoading}
                  >

                    <option value={2025}>2025년</option>
                    <option value={2024}>2024년</option>
                    <option value={2023}>2023년</option>
                    <option value={2022}>2022년</option>
                    <option value={2021}>2021년</option>
                    <option value={2020}>2020년</option>
                    <option value={2019}>2019년</option>
                    <option value={2018}>2018년</option>
                    <option value={2017}>2017년</option>
                    <option value={2016}>2016년</option>
                    <option value={2015}>2015년</option>
                    <option value={2014}>2014년</option>
                    <option value={2013}>2013년</option>
                    <option value={2012}>2012년</option>
                    <option value={2011}>2011년</option>
                    <option value={2010}>2010년</option>


                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    출력할 종목 수 (최대 100개)
                  </label>
                  <input 
                    type="number" 
                    value={outputCount}
                    onChange={(e) => setOutputCount(Math.min(100, Math.max(1, Number(e.target.value))))}
                    className="w-full p-3 bg-gray-700 border border-gray-600 rounded-md text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    min={1}
                    max={100}
                    disabled={backtestLoading}
                  />
                </div>
              </div>
            </div>

            {/* 전략 선택 */}
            <div className="bg-gray-800 rounded-lg shadow-sm border border-gray-700 p-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center justify-between text-gray-100">
                <span className="flex items-center gap-2">
                  <span>📊</span> 투자 전략 선택
                </span>
                <span className="text-sm text-gray-400">
                  {strategies.filter(s => s.selected).length}/{strategies.length}개 선택
                </span>
              </h2>
              
              {/* 스크롤 가능한 전략 리스트 - 높이 제한 */}
              <div className="max-h-80 overflow-y-auto space-y-3 pr-2">
                {strategies.map((strategy) => (
                  <div 
                    key={strategy.id} 
                    className={`border rounded-lg p-3 transition-all ${
                      strategy.selected ? 'border-blue-500 bg-blue-900/20' : 'border-gray-600 hover:border-gray-500'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <input 
                          type="checkbox" 
                          checked={strategy.selected}
                          onChange={() => toggleStrategy(strategy.id)}
                          className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                          disabled={backtestLoading}
                        />
                        <div className="flex-1">
                          <div className="font-semibold text-gray-100 text-sm">{strategy.name}</div>
                          <div className="text-xs text-gray-400 leading-relaxed">{strategy.description}</div>
                        </div>
                      </div>
                      {strategy.selected && (
                        <div className="text-xs text-blue-400 font-medium">
                          {strategy.weight.toFixed(0)}%
                        </div>
                      )}
                    </div>
                    
                    {strategy.selected && (
                      <div className="space-y-3 mt-3 pt-3 border-t border-gray-600">
                        <div>
                          <label className="text-xs font-medium text-gray-300 mb-1 block">
                            비율: {strategy.weight.toFixed(1)}%
                          </label>
                          <div className="relative">
                            <div className="h-1.5 bg-gray-600 rounded-full">
                              <div 
                                className="h-full bg-blue-600 rounded-full transition-all duration-300"
                                style={{ width: `${Math.min(100, strategy.weight)}%` }}
                              />
                            </div>
                            <input 
                              type="range"
                              min="0"
                              max="100"
                              value={strategy.weight}
                              onChange={(e) => updateWeight(strategy.id, Number(e.target.value))}
                              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                              disabled={backtestLoading}
                            />
                          </div>
                        </div>
                        
                        {Object.keys(strategy.params).length > 0 && (
                          <div className="space-y-2">
                            <div className="text-xs font-medium text-gray-300">세부 파라미터</div>
                            <div className="grid grid-cols-1 gap-2">
                              {Object.entries(strategy.params).map(([key, value]) => (
                                <div key={key} className="flex items-center gap-2">
                                  <label className="text-xs text-gray-400 text-left flex-1 truncate">
                                    {key}:
                                  </label>
                                  <input 
                                    type="number"
                                    value={value}
                                    onChange={(e) => updateParam(strategy.id, key, Number(e.target.value))}
                                    className="w-16 p-1 text-xs bg-gray-700 border border-gray-600 rounded text-gray-100 focus:ring-1 focus:ring-blue-500"
                                    disabled={backtestLoading}
                                    step={key.includes('rate') || key.includes('Level') ? 0.1 : 1}
                                  />
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              <div className="mt-6 pt-4 border-t border-gray-600 space-y-4">
                {/* 백테스트 실행 버튼을 전략 선택 아래로 이동 */}
                <button 
                  onClick={handleRunBacktest}
                  disabled={backtestLoading || Math.abs(totalWeight - 100) > 1 || strategies.filter(s => s.selected).length === 0}
                  className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-semibold transition-colors"
                >
                  <Play className={`w-4 h-4 ${backtestLoading ? 'animate-spin' : ''}`} />
                  {backtestLoading ? '분석 실행 중...' : '🚀 백테스트 실행'}
                </button>
                
                {strategies.filter(s => s.selected).length === 0 && (
                  <div className="text-xs text-red-400 text-center">
                    최소 하나의 전략을 선택해주세요
                  </div>
                )}

                <button 
                  className="w-full py-3 px-4 border border-dashed border-gray-600 rounded-md text-gray-400 hover:bg-gray-700 flex items-center justify-center gap-2 transition-colors"
                  disabled={backtestLoading}
                >
                  <Plus className="w-4 h-4" />
                  커스텀 전략 추가
                </button>
                
                <div className="text-center">
                  <span className="text-sm font-medium text-gray-300">🎯 총 가중치: </span>
                  <span className={`font-bold ${Math.abs(totalWeight - 100) < 1 ? 'text-green-400' : 'text-red-400'}`}>
                    {totalWeight.toFixed(1)}%
                  </span>
                  {Math.abs(totalWeight - 100) >= 1 && (
                    <div className="text-xs text-red-400 mt-1">
                      가중치 합계가 100%가 되어야 합니다
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* 오른쪽 메인 영역 - 백테스트 결과 */}
          <div className="col-span-8 space-y-6">
            {/* 분석 결과 테이블 */}
            <div className="bg-gray-800 rounded-lg shadow-sm border border-gray-700 p-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center justify-between text-gray-100">
                <span className="flex items-center gap-2">
                  <span>📈</span> 백테스트 분석 결과
                </span>
                {totalAnalyzed > 0 && (
                  <span className="text-sm text-gray-400">
                    총 {totalAnalyzed.toLocaleString()}개 → 조건만족 {conditionMet}개 ({((conditionMet/totalAnalyzed)*100).toFixed(1)}%)
                  </span>
                )}
              </h2>
              
              {backtestLoading ? (
                <div className="flex items-center justify-center py-16">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <div className="text-gray-200 font-medium">AI가 시장을 분석하고 있습니다...</div>
                    <div className="text-sm text-gray-400 mt-2">
                      {backtestYear}년 데이터 기준으로 {strategies.filter(s => s.selected).length}개 전략 실행 중
                    </div>
                  </div>
                </div>
              ) : results.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse border border-gray-600">
                    <thead>
                      <tr className="bg-gray-700">
                        <th className="border border-gray-600 p-3 text-sm font-semibold text-gray-200">순위</th>
                        <th className="border border-gray-600 p-3 text-sm font-semibold text-gray-200">종목코드</th>
                        <th className="border border-gray-600 p-3 text-sm font-semibold text-gray-200">종목명</th>
                        <th className="border border-gray-600 p-3 text-sm font-semibold text-gray-200">종합점수</th>
                        <th className="border border-gray-600 p-3 text-sm font-semibold text-gray-200">등급</th>
                        <th className="border border-gray-600 p-3 text-sm font-semibold text-gray-200">강점분야</th>
                        <th className="border border-gray-600 p-3 text-sm font-semibold text-gray-200">포트폴리오</th>
                      </tr>
                    </thead>
                    <tbody>
                      {results.slice(0, outputCount).map((result) => (
                        <tr 
                          key={result.stockCode} 
                          className={`hover:bg-gray-700 cursor-pointer transition-colors ${
                            selectedStock?.stockCode === result.stockCode ? 'bg-blue-900/30 border-blue-500' : 'bg-gray-800'
                          }`}
                          onClick={() => setSelectedStock(result)}
                        >
                          <td className="border border-gray-600 p-3 text-center text-sm font-medium text-gray-200">
                            {result.rank <= 3 ? (
                              <span className="text-lg">
                                {result.rank === 1 ? '🥇' : result.rank === 2 ? '🥈' : '🥉'}
                              </span>
                            ) : (
                              result.rank
                            )}
                          </td>
                          <td className="border border-gray-600 p-3 text-center text-sm font-mono text-gray-300">
                            {result.stockCode}
                          </td>
                          <td className="border border-gray-600 p-3 text-sm font-medium text-gray-200">
                            {result.stockName}
                          </td>
                          <td className="border border-gray-600 p-3 text-center text-sm font-bold text-gray-100">
                            {result.compositeScore.toFixed(1)}점
                          </td>
                          <td className="border border-gray-600 p-3 text-center text-sm">
                            <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                              result.grade === 'S' ? 'bg-purple-100 text-purple-800' :
                              result.grade === 'A' ? 'bg-blue-100 text-blue-800' :
                              result.grade === 'B' ? 'bg-green-100 text-green-800' :
                              result.grade === 'C' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {result.grade}
                            </span>
                          </td>
                          <td className="border border-gray-600 p-3 text-center text-sm">
                            <span className={`px-2 py-1 rounded text-xs ${
                              result.strengthArea === '재무' ? 'bg-green-100 text-green-700' :
                              result.strengthArea === '기술' ? 'bg-blue-100 text-blue-700' :
                              'bg-gray-100 text-gray-700'
                            }`}>
                              {result.strengthArea}
                            </span>
                          </td>
                          <td className="border border-gray-600 p-3 text-center">
                            <input 
                              type="checkbox"
                              checked={result.selected}
                              onChange={(e) => {
                                e.stopPropagation();
                                toggleStockSelection(result);
                              }}
                              className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-16 text-gray-400">
                  <div className="text-4xl mb-4">📊</div>
                  <div className="text-lg font-medium mb-2 text-gray-200">백테스트 결과가 없습니다</div>
                  <div className="text-sm">왼쪽에서 전략을 선택하고 백테스트를 실행하세요</div>
                </div>
              )}
            </div>

            {/* 선택된 종목 상세보기 */}
            {selectedStock && (
              <div className="bg-gray-800 rounded-lg shadow-sm border border-gray-700 p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2 text-gray-100">
                  <span>🔍</span> 종목 상세 분석
                </h3>
                
                <div className="bg-gradient-to-r from-blue-900/30 to-indigo-900/30 rounded-lg p-6 border border-blue-600/50">
                  <div className="flex items-center gap-4 mb-4">
                    <span className="text-3xl">
                      {selectedStock.rank === 1 ? '🥇' : 
                       selectedStock.rank === 2 ? '🥈' : 
                       selectedStock.rank === 3 ? '🥉' : '📊'}
                    </span>
                    <div>
                      <div className="font-bold text-xl text-gray-100">
                        {selectedStock.stockName} ({selectedStock.compositeScore.toFixed(1)}점)
                      </div>
                      <div className="text-sm text-gray-300">
                        종목코드: {selectedStock.stockCode} | {selectedStock.rank}위 | {selectedStock.grade}급
                      </div>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-3">
                      <h4 className="font-semibold text-gray-200">전략별 수치 분석</h4>
                      {Object.entries(selectedStock.strategyValues).map(([strategyKey, value]) => {
                        const strategy = strategies.find(s => s.id === strategyKey);
                        const strategyName = strategy?.name || strategyKey.toUpperCase();
                        
                        return (
                          <div key={strategyKey} className="bg-gray-800 rounded p-3 border border-gray-600">
                            <div className="flex justify-between items-center">
                              <span className="text-sm font-medium text-gray-300">{strategyName}</span>
                              <span className="font-bold text-gray-100">
                                {typeof value === 'number' ? 
                                  (strategyKey === 'roe' ? `${value.toFixed(1)}%` : value.toFixed(2)) 
                                  : value}
                              </span>
                            </div>
                            <div className="text-xs text-gray-400 mt-1">
                              {strategyKey === 'rsi' && typeof value === 'number' ? 
                                `과매도 기준 30 대비 ${(30 - value).toFixed(1)} ${value < 30 ? '낮음 (매수신호)' : '높음'}` :
                               strategyKey === 'roe' && typeof value === 'number' ?
                                `최소기준 15% 대비 ${(value - 15).toFixed(1)}%p ${value > 15 ? '높음 (우수)' : '낮음'}` :
                                '기준 대비 수치'}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                    
                    <div className="space-y-3">
                      <h4 className="font-semibold text-gray-200">종합 평가</h4>
                      <div className="bg-gray-800 rounded p-3 border border-gray-600">
                        <div className="text-sm text-gray-400">강점 분야</div>
                        <div className="font-semibold text-gray-200">{selectedStock.strengthArea} 지표 중심</div>
                      </div>
                      <div className="bg-gray-800 rounded p-3 border border-gray-600">
                        <div className="text-sm text-gray-400">전체 순위</div>
                        <div className="font-semibold text-gray-200">
                          {totalAnalyzed > 0 ? 
                            `상위 ${((selectedStock.rank / totalAnalyzed) * 100).toFixed(2)}% 위치` : 
                            `${selectedStock.rank}위`}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* 포트폴리오 생성 */}
            <div className="bg-gray-800 rounded-lg shadow-sm border border-gray-700 p-6">
              <h3 className="text-xl font-semibold mb-4 flex items-center gap-2 text-gray-100">
                <span>💼</span> 나만의 포트폴리오
              </h3>
              
              {portfolioStocks.length > 0 ? (
                <div className="space-y-6">
                  <div className="bg-gray-700 rounded-lg p-5">
                    <h4 className="font-semibold mb-4 flex items-center gap-2 text-gray-200">
                      <span>📋</span> 선택된 종목 ({portfolioStocks.length}개)
                    </h4>
                    <div className="space-y-3">
                      {portfolioStocks.map((stock, index) => (
                        <div key={stock.stockCode} className="flex justify-between items-center p-3 bg-gray-800 rounded border border-gray-600">
                          <div className="flex items-center gap-3">
                            <span className="font-medium text-gray-200">{stock.stockName}</span>
                            <span className="text-sm text-gray-400">({stock.stockCode})</span>
                          </div>
                          <div className="flex items-center gap-4">
                            <span className="font-semibold text-gray-200">{stock.score.toFixed(1)}점</span>
                            <span className={`px-2 py-1 rounded text-xs font-bold ${
                              stock.grade === 'S' ? 'bg-purple-100 text-purple-800' :
                              stock.grade === 'A' ? 'bg-blue-100 text-blue-800' :
                              'bg-green-100 text-green-800'
                            }`}>
                              {stock.grade}급
                            </span>
                            <span className="text-sm text-gray-400">{stock.weight.toFixed(1)}%</span>
                            <button 
                              onClick={() => {
                                const result = results.find(r => r.stockCode === stock.stockCode);
                                if (result) toggleStockSelection(result);
                              }}
                              className="text-red-500 hover:text-red-700 text-xs"
                            >
                              제거
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <div className="bg-gradient-to-r from-green-900/20 to-blue-900/20 rounded-lg p-5 border border-green-600/30">
                    <h4 className="font-semibold mb-4 flex items-center gap-2 text-gray-200">
                      <span>📊</span> 포트폴리오 분석
                    </h4>
                    <div className="grid grid-cols-2 gap-6">
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-300">평균 점수</span>
                          <span className="font-bold text-gray-100">{portfolioStats.avgScore.toFixed(1)}점</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-300">종목 수</span>
                          <span className="font-bold text-gray-100">{portfolioStats.totalStocks}개</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-300">리스크 수준</span>
                          <span className="font-bold text-orange-400">중위험</span>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-300">적용 전략</span>
                          <span className="font-bold text-blue-400">
                            {strategies.filter(s => s.selected).length}개 조합
                          </span>
                        </div>
                        <div className="text-xs text-gray-400">
                          {strategies.filter(s => s.selected).map(s => 
                            `${s.name}(${s.weight.toFixed(0)}%)`
                          ).join(' + ')}
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <button 
                      onClick={handleSavePortfolio}
                      disabled={isSaving || portfolioStocks.length === 0}
                      className="w-full bg-green-600 text-white py-3 px-4 rounded-md hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-semibold transition-colors"
                    >
                      {isSaving ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                          저장 중...
                        </>
                      ) : (
                        <>
                          <Save className="w-4 h-4" />
                          저장
                        </>
                      )}
                    </button>
                  </div>
                </div>
              ) : (
                <div className="text-center py-16 text-gray-400">
                  <div className="text-4xl mb-4">💼</div>
                  <div className="text-lg font-medium mb-2 text-gray-200">포트폴리오가 비어있습니다</div>
                  <div className="text-sm">백테스트 결과에서 종목을 선택하여 포트폴리오를 구성하세요</div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 하단 시스템 정보 */}
        {reliability && (
          <div className="mt-6 bg-gray-800 rounded-lg shadow-sm border border-gray-700 p-6">
            <div className="flex flex-wrap justify-between items-center gap-4 text-sm">
              <div className="flex items-center gap-6">
                <span className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <strong className="text-gray-300">분석 신뢰성:</strong> 
                  <span className="font-bold text-green-600">{reliability.dataQuality}/100점</span>
                </span>
                <span className="text-gray-300">
                  <strong>데이터 커버리지:</strong> {reliability.coverage}%
                </span>
                <span className="text-gray-300">
                  <strong>분석 완료:</strong> {new Date(reliability.completedAt).toLocaleString('ko-KR')}
                </span>
              </div>
              <div className="text-xs text-gray-500">
                API 연결: {process.env.NEXT_PUBLIC_API_URL || 'localhost:8000'}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}