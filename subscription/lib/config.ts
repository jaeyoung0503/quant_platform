 // lib/config.ts - MVP 설정값
import { Plan } from './types';

export const PLANS: Plan[] = [
  {
    id: 'basic',
    name: 'Basic',
    price: 9900,
    features: [
      '기본 기능 이용',
      '월 100회 사용 제한',
      '이메일 지원',
      '기본 템플릿 제공'
    ],
  },
  {
    id: 'advanced',
    name: 'Advanced',
    price: 19900,
    popular: true,
    features: [
      '모든 기능 이용',
      '무제한 사용',
      '우선 고객지원',
      '프리미엄 템플릿',
      '고급 분석 도구',
      'API 접근 권한'
    ],
  },
];

export const TOSS_CONFIG = {
  clientKey: process.env.NEXT_PUBLIC_TOSS_CLIENT_KEY || '',
  secretKey: process.env.TOSS_SECRET_KEY || '',
  apiUrl: 'https://api.tosspayments.com',
};

export const APP_CONFIG = {
  baseUrl: process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000',
  currency: 'KRW',
};

// 테스트용 사용자 정보 (MVP에서만 사용)
export const TEST_USER = {
  id: 'user_123',
  name: '김고객',
  email: 'customer@example.com',
};