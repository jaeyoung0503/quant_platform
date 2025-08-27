// utils.ts

import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// 숫자 포맷팅 함수들
export function formatCurrency(amount: number): string {
  if (amount === 0) return '₩0'
  
  const isNegative = amount < 0
  const absAmount = Math.abs(amount)
  
  let formatted: string
  
  if (absAmount >= 100000000) {
    // 1억 이상
    formatted = `₩${(absAmount / 100000000).toFixed(1)}억`
  } else if (absAmount >= 10000) {
    // 1만 이상
    formatted = `₩${(absAmount / 10000).toFixed(1)}만`
  } else {
    // 1만 미만
    formatted = `₩${absAmount.toLocaleString()}`
  }
  
  return isNegative ? `-${formatted}` : formatted
}

export function formatNumber(num: number): string {
  return num.toLocaleString()
}

export function formatPercentage(percentage: number): string {
  const sign = percentage >= 0 ? '+' : ''
  return `${sign}${percentage.toFixed(2)}%`
}

export function formatDecimal(num: number, decimals: number = 2): string {
  return num.toFixed(decimals)
}

// 시간 포맷팅 함수들
export function formatTime(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return d.toLocaleTimeString('ko-KR', { 
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

export function formatDate(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return d.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

export function formatDateTime(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return `${formatDate(d)} ${formatTime(d)}`
}

export function getCurrentTime(): string {
  return formatTime(new Date())
}

export function getTimeAgo(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHour = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHour / 24)
  
  if (diffSec < 60) return `${diffSec}초 전`
  if (diffMin < 60) return `${diffMin}분 전`
  if (diffHour < 24) return `${diffHour}시간 전`
  if (diffDay < 7) return `${diffDay}일 전`
  
  return formatDate(d)
}

// 데이터 검증 함수들
export function isValidPrice(price: number): boolean {
  return price > 0 && price < 1000000000 && Number.isFinite(price)
}

export function isValidQuantity(quantity: number): boolean {
  return Number.isInteger(quantity) && quantity > 0 && quantity <= 10000000
}

export function isValidPercentage(percentage: number): boolean {
  return Number.isFinite(percentage) && percentage >= -100 && percentage <= 1000
}

// 색상 관련 함수들
export function getPnLColor(value: number): string {
  if (value > 0) return 'text-green-400'
  if (value < 0) return 'text-red-400'
  return 'text-gray-400'
}

export function getPnLBgColor(value: number): string {
  if (value > 0) return 'bg-green-900'
  if (value < 0) return 'bg-red-900'
  return 'bg-gray-700'
}

export function getChangeColor(current: number, previous: number): string {
  if (current > previous) return 'text-green-400'
  if (current < previous) return 'text-red-400'
  return 'text-gray-400'
}

// 계산 관련 함수들
export function calculatePnL(currentPrice: number, avgPrice: number, quantity: number): number {
  return (currentPrice - avgPrice) * quantity
}

export function calculatePnLPercentage(currentPrice: number, avgPrice: number): number {
  return ((currentPrice - avgPrice) / avgPrice) * 100
}

export function calculateTotalValue(positions: Array<{current_price: number, quantity: number}>): number {
  return positions.reduce((total, pos) => total + (pos.current_price * pos.quantity), 0)
}

export function calculateWeightedAverage(prices: number[], weights: number[]): number {
  if (prices.length !== weights.length || prices.length === 0) return 0
  
  const totalWeight = weights.reduce((sum, w) => sum + w, 0)
  if (totalWeight === 0) return 0
  
  const weightedSum = prices.reduce((sum, price, i) => sum + (price * weights[i]), 0)
  return weightedSum / totalWeight
}

// 배열 유틸리티 함수들
export function sortByField<T>(array: T[], field: keyof T, ascending: boolean = true): T[] {
  return [...array].sort((a, b) => {
    const aVal = a[field]
    const bVal = b[field]
    
    if (aVal < bVal) return ascending ? -1 : 1
    if (aVal > bVal) return ascending ? 1 : -1
    return 0
  })
}

export function groupBy<T>(array: T[], keyFn: (item: T) => string): Record<string, T[]> {
  return array.reduce((groups, item) => {
    const key = keyFn(item)
    if (!groups[key]) groups[key] = []
    groups[key].push(item)
    return groups
  }, {} as Record<string, T[]>)
}

export function uniqueBy<T>(array: T[], keyFn: (item: T) => any): T[] {
  const seen = new Set()
  return array.filter(item => {
    const key = keyFn(item)
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
}

// 문자열 유틸리티
export function truncateString(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str
  return str.slice(0, maxLength - 3) + '...'
}

export function capitalizeFirst(str: string): string {
  if (!str) return str
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase()
}

export function formatStockCode(code: string): string {
  // 종목코드를 6자리로 포맷 (예: 5930 -> 005930)
  return code.padStart(6, '0')
}

// API 관련 유틸리티
export function buildQueryString(params: Record<string, any>): string {
  const searchParams = new URLSearchParams()
  
  Object.entries(params).forEach(([key, value]) => {
    if (value != null && value !== '') {
      searchParams.append(key, String(value))
    }
  })
  
  const queryString = searchParams.toString()
  return queryString ? `?${queryString}` : ''
}

export function handleApiError(error: any): string {
  if (error?.response?.data?.detail) {
    return error.response.data.detail
  }
  if (error?.message) {
    return error.message
  }
  return '알 수 없는 오류가 발생했습니다'
}

// 로컬 스토리지 유틸리티 (브라우저 환경에서만 사용)
export function setLocalStorage(key: string, value: any): void {
  if (typeof window !== 'undefined') {
    try {
      localStorage.setItem(key, JSON.stringify(value))
    } catch (error) {
      console.warn('localStorage 저장 실패:', error)
    }
  }
}

export function getLocalStorage<T>(key: string, defaultValue: T): T {
  if (typeof window !== 'undefined') {
    try {
      const item = localStorage.getItem(key)
      return item ? JSON.parse(item) : defaultValue
    } catch (error) {
      console.warn('localStorage 읽기 실패:', error)
      return defaultValue
    }
  }
  return defaultValue
}

export function removeLocalStorage(key: string): void {
  if (typeof window !== 'undefined') {
    try {
      localStorage.removeItem(key)
    } catch (error) {
      console.warn('localStorage 삭제 실패:', error)
    }
  }
}

// 디바운싱 함수
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null
  
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout)
    
    timeout = setTimeout(() => {
      func(...args)
    }, wait)
  }
}

// 쓰로틀링 함수
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean = false
  
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args)
      inThrottle = true
      setTimeout(() => inThrottle = false, limit)
    }
  }
}

// 랜덤 유틸리티
export function randomBetween(min: number, max: number): number {
  return Math.random() * (max - min) + min
}

export function randomInt(min: number, max: number): number {
  return Math.floor(randomBetween(min, max + 1))
}

export function generateId(): string {
  return Math.random().toString(36).substring(2) + Date.now().toString(36)
}

// 상태 관리 유틸리티
export function createInitialState<T>(defaults: T): T {
  return { ...defaults }
}

export function updateState<T>(currentState: T, updates: Partial<T>): T {
  return { ...currentState, ...updates }
}

// 타입 가드
export function isNumber(value: any): value is number {
  return typeof value === 'number' && !isNaN(value) && isFinite(value)
}

export function isString(value: any): value is string {
  return typeof value === 'string'
}

export function isArray<T>(value: any): value is T[] {
  return Array.isArray(value)
}

export function isObject(value: any): value is Record<string, any> {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
}

// 에러 처리 유틸리티
export function createError(message: string, code?: string): Error {
  const error = new Error(message)
  if (code) {
    ;(error as any).code = code
  }
  return error
}

export function isApiError(error: any): boolean {
  return error?.response?.status !== undefined
}

// 성능 측정 유틸리티
export function measureTime<T>(fn: () => T, label?: string): T {
  const start = performance.now()
  const result = fn()
  const end = performance.now()
  
  if (label) {
    console.log(`${label}: ${end - start}ms`)
  }
  
  return result
}

export async function measureAsyncTime<T>(fn: () => Promise<T>, label?: string): Promise<T> {
  const start = performance.now()
  const result = await fn()
  const end = performance.now()
  
  if (label) {
    console.log(`${label}: ${end - start}ms`)
  }
  
  return result
}

// 환경 감지
export function isBrowser(): boolean {
  return typeof window !== 'undefined'
}

export function isDevelopment(): boolean {
  return process.env.NODE_ENV === 'development'
}

export function isProduction(): boolean {
  return process.env.NODE_ENV === 'production'
}

// CSS 클래스 유틸리티
export function conditionalClass(condition: boolean, trueClass: string, falseClass: string = ''): string {
  return condition ? trueClass : falseClass
}

export function joinClasses(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ')
}0 
