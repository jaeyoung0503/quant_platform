/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  
  // 환경변수 설정
  env: {
    CUSTOM_KEY: 'subscription-payment-system',
  },

  // API 라우트 및 페이지에 대한 헤더 설정
  async headers() {
    return [
      {
        // API 라우트에 CORS 헤더 적용
        source: '/api/:path*',
        headers: [
          {
            key: 'Access-Control-Allow-Origin',
            value: process.env.NODE_ENV === 'production' 
              ? (process.env.NEXT_PUBLIC_BASE_URL || 'https://yourdomain.com')
              : '*',
          },
          {
            key: 'Access-Control-Allow-Methods',
            value: 'GET, POST, PUT, DELETE, OPTIONS',
          },
          {
            key: 'Access-Control-Allow-Headers',
            value: 'Content-Type, Authorization, x-tosspayments-signature',
          },
          {
            key: 'Access-Control-Max-Age',
            value: '86400', // 24시간
          },
        ],
      },
      {
        // 보안 헤더 설정
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'Permissions-Policy',
            value: 'payment=*, camera=(), microphone=(), geolocation=()',
          },
        ],
      },
    ];
  },

  // 리다이렉트 설정
  async redirects() {
    return [
      {
        source: '/payment',
        destination: '/pricing',
        permanent: false,
      },
      {
        source: '/subscribe',
        destination: '/pricing',
        permanent: false,
      },
      {
        source: '/plans',
        destination: '/pricing',
        permanent: true,
      },
    ];
  },

  // 이미지 최적화 설정
  images: {
    domains: ['localhost'],
    formats: ['image/webp', 'image/avif'],
  },

  // 웹팩 설정 - 브라우저에서 Node.js 모듈 오류 방지
  webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
    // 클라이언트 사이드에서 Node.js 모듈 fallback 설정
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
        crypto: false,
        stream: false,
        url: false,
        zlib: false,
        http: false,
        https: false,
        assert: false,
        os: false,
        path: false,
      };
    }

    return config;
  },

  // 실험적 기능 설정
  experimental: {
    // 서버리스 함수 최적화
    serverComponentsExternalPackages: [],
  },

  // 트레일링 슬래시 설정
  trailingSlash: false,

  // 압축 설정
  compress: true,

  // 개발 환경 설정
  ...(process.env.NODE_ENV === 'development' && {
    // 개발 환경에서만 적용되는 설정
    typescript: {
      // 타입 에러가 있어도 빌드 계속 진행 (개발 중에만)
      ignoreBuildErrors: false,
    },
    eslint: {
      // ESLint 에러가 있어도 빌드 계속 진행 (개발 중에만)  
      ignoreDuringBuilds: false,
    },
  }),

  // 운영 환경 설정
  ...(process.env.NODE_ENV === 'production' && {
    // 운영 환경에서만 적용되는 설정
    typescript: {
      ignoreBuildErrors: false,
    },
    eslint: {
      ignoreDuringBuilds: false,
    },
    // 성능 최적화
    swcMinify: true,
    compiler: {
      removeConsole: {
        exclude: ['error'],
      },
    },
  }),
};

module.exports = nextConfig; 
