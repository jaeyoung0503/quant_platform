#file: /quant_platform/setup_payment.py
"""
Payment System Auto Setup Script
토스페이먼츠 결제 시스템 자동 설치 스크립트 (Python)
"""

import os
import json
import subprocess
import sys
from pathlib import Path

class PaymentSetup:
    def __init__(self):
        self.project_root = Path.cwd()
        self.src_path = self.project_root / "src"
        self.app_path = self.src_path / "app"
        
    def print_step(self, message, emoji="🔧"):
        """단계별 메시지 출력"""
        print(f"{emoji} {message}")
        
    def print_success(self, message):
        """성공 메시지 출력"""
        print(f"✅ {message}")
        
    def print_error(self, message):
        """에러 메시지 출력"""
        print(f"❌ {message}")
        
    def check_project_structure(self):
        """프로젝트 구조 확인"""
        self.print_step("Checking project structure...")
        
        if not (self.project_root / "package.json").exists():
            self.print_error("package.json not found. Please run this script from the project root.")
            sys.exit(1)
            
        # 필요한 디렉토리 생성
        directories = [
            self.src_path,
            self.app_path,
            self.app_path / "api" / "payment" / "confirm",
            self.app_path / "api" / "payment" / "cancel", 
            self.app_path / "api" / "payment" / "webhook",
            self.app_path / "member_payment",
            self.src_path / "types"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
        self.print_success("Project structure validated!")
        
    def install_dependencies(self):
        """필수 패키지 설치"""
        self.print_step("Installing required dependencies...", "📦")
        
        packages = [
            "@tosspayments/payment-sdk",
            "@types/node"
        ]
        
        try:
            # npm install 실행
            for package in packages:
                if package == "@types/node":
                    subprocess.run(["npm", "install", package, "--save-dev"], 
                                 check=True, capture_output=True)
                else:
                    subprocess.run(["npm", "install", package], 
                                 check=True, capture_output=True)
            
            self.print_success("Dependencies installed successfully!")
            
        except subprocess.CalledProcessError as e:
            self.print_error(f"Failed to install dependencies: {e}")
            sys.exit(1)
            
    def setup_environment_variables(self):
        """환경변수 설정"""
        self.print_step("Setting up environment variables...")
        
        env_file = self.project_root / ".env.local"
        
        # .env.local 파일 생성 또는 읽기
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            content = ""
            
        # 토스페이먼츠 환경변수 추가
        if "NEXT_PUBLIC_TOSS_CLIENT_KEY" not in content:
            env_vars = """
# TossPayments Configuration
NEXT_PUBLIC_TOSS_CLIENT_KEY=test_ck_D5GePWvyJnrK0W0k6q8gLzN97Eoq
TOSS_SECRET_KEY=test_sk_zXLkKEypNArWmo50nX3lmeaxYG5R
"""
            content += env_vars
            
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
            self.print_success("Added TossPayments environment variables")
        else:
            self.print_step("TossPayments environment variables already exist", "ℹ️")
            
    def create_api_routes(self):
        """API 라우트 생성"""
        self.print_step("Creating payment APIs...", "🔌")
        
        # 결제 승인 API
        confirm_api = """import { NextRequest, NextResponse } from 'next/server'

const TOSS_SECRET_KEY = process.env.TOSS_SECRET_KEY || 'test_sk_zXLkKEypNArWmo50nX3lmeaxYG5R'
const TOSS_PAYMENTS_BASE_URL = 'https://api.tosspayments.com/v1/payments'

export async function POST(request: NextRequest) {
  try {
    const { paymentKey, orderId, amount } = await request.json()

    if (!paymentKey || !orderId || !amount) {
      return NextResponse.json({
        success: false,
        error: '필수 파라미터가 누락되었습니다.'
      }, { status: 400 })
    }

    // 토스페이먼츠 결제 승인 요청
    const response = await fetch(`${TOSS_PAYMENTS_BASE_URL}/confirm`, {
      method: 'POST',
      headers: {
        'Authorization': `Basic ${Buffer.from(TOSS_SECRET_KEY + ':').toString('base64')}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        paymentKey,
        orderId,
        amount
      })
    })

    const paymentData = await response.json()

    if (!response.ok) {
      console.error('토스페이먼츠 결제 승인 실패:', paymentData)
      return NextResponse.json({
        success: false,
        error: paymentData.message || '결제 승인에 실패했습니다.'
      }, { status: response.status })
    }

    // 여기에서 데이터베이스에 결제 정보 저장 등의 비즈니스 로직 처리
    // TODO: 실제 서비스에서는 데이터베이스에 결제 정보 저장
    console.log('결제 승인 완료:', {
      orderId: paymentData.orderId,
      amount: paymentData.totalAmount,
      status: paymentData.status
    })

    return NextResponse.json({
      success: true,
      data: paymentData
    })

  } catch (error) {
    console.error('결제 승인 API 오류:', error)
    return NextResponse.json({
      success: false,
      error: '서버 오류가 발생했습니다.'
    }, { status: 500 })
  }
}"""

        # 결제 취소 API
        cancel_api = """import { NextRequest, NextResponse } from 'next/server'

const TOSS_SECRET_KEY = process.env.TOSS_SECRET_KEY || 'test_sk_zXLkKEypNArWmo50nX3lmeaxYG5R'
const TOSS_PAYMENTS_BASE_URL = 'https://api.tosspayments.com/v1/payments'

export async function POST(request: NextRequest) {
  try {
    const { paymentKey, cancelReason } = await request.json()

    if (!paymentKey) {
      return NextResponse.json({
        success: false,
        error: 'paymentKey가 필요합니다.'
      }, { status: 400 })
    }

    // 토스페이먼츠 결제 취소 요청
    const response = await fetch(`${TOSS_PAYMENTS_BASE_URL}/${paymentKey}/cancel`, {
      method: 'POST',
      headers: {
        'Authorization': `Basic ${Buffer.from(TOSS_SECRET_KEY + ':').toString('base64')}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        cancelReason: cancelReason || '고객 요청'
      })
    })

    const cancelData = await response.json()

    if (!response.ok) {
      console.error('토스페이먼츠 결제 취소 실패:', cancelData)
      return NextResponse.json({
        success: false,
        error: cancelData.message || '결제 취소에 실패했습니다.'
      }, { status: response.status })
    }

    // 여기에서 데이터베이스에서 결제 정보 업데이트 등의 비즈니스 로직 처리
    console.log('결제 취소 완료:', {
      paymentKey: cancelData.paymentKey,
      status: cancelData.status,
      cancelAmount: cancelData.cancelAmount
    })

    return NextResponse.json({
      success: true,
      data: cancelData
    })

  } catch (error) {
    console.error('결제 취소 API 오류:', error)
    return NextResponse.json({
      success: false,
      error: '서버 오류가 발생했습니다.'
    }, { status: 500 })
  }
}"""

        # 결제 조회 API
        inquiry_api = """import { NextRequest, NextResponse } from 'next/server'

const TOSS_SECRET_KEY = process.env.TOSS_SECRET_KEY || 'test_sk_zXLkKEypNArWmo50nX3lmeaxYG5R'
const TOSS_PAYMENTS_BASE_URL = 'https://api.tosspayments.com/v1/payments'

export async function GET(
  request: NextRequest,
  { params }: { params: { paymentKey: string } }
) {
  try {
    const { paymentKey } = params

    if (!paymentKey) {
      return NextResponse.json({
        success: false,
        error: 'paymentKey가 필요합니다.'
      }, { status: 400 })
    }

    // 토스페이먼츠 결제 조회 요청
    const response = await fetch(`${TOSS_PAYMENTS_BASE_URL}/${paymentKey}`, {
      method: 'GET',
      headers: {
        'Authorization': `Basic ${Buffer.from(TOSS_SECRET_KEY + ':').toString('base64')}`,
        'Content-Type': 'application/json',
      }
    })

    const paymentData = await response.json()

    if (!response.ok) {
      console.error('토스페이먼츠 결제 조회 실패:', paymentData)
      return NextResponse.json({
        success: false,
        error: paymentData.message || '결제 조회에 실패했습니다.'
      }, { status: response.status })
    }

    return NextResponse.json({
      success: true,
      data: paymentData
    })

  } catch (error) {
    console.error('결제 조회 API 오류:', error)
    return NextResponse.json({
      success: false,
      error: '서버 오류가 발생했습니다.'
    }, { status: 500 })
  }
}"""

        # 웹훅 API
        webhook_api = """import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const webhookData = await request.json()
    
    console.log('토스페이먼츠 웹훅 수신:', webhookData)

    // 웹훅 데이터 검증
    const { eventType, data } = webhookData

    switch (eventType) {
      case 'PAYMENT_STATUS_CHANGED':
        // 결제 상태 변경 처리
        await handlePaymentStatusChange(data)
        break
      
      case 'PAYMENT_WAITING_FOR_DEPOSIT':
        // 가상계좌 입금 대기
        await handleVirtualAccountWaiting(data)
        break
        
      case 'PAYMENT_EXPIRED':
        // 결제 만료
        await handlePaymentExpired(data)
        break
        
      default:
        console.log(`처리되지 않은 웹훅 이벤트: ${eventType}`)
    }

    return NextResponse.json({ success: true })

  } catch (error) {
    console.error('웹훅 처리 오류:', error)
    return NextResponse.json({
      success: false,
      error: '웹훅 처리 중 오류가 발생했습니다.'
    }, { status: 500 })
  }
}

async function handlePaymentStatusChange(data: any) {
  // TODO: 결제 상태 변경 처리 로직
  console.log('결제 상태 변경:', data)
}

async function handleVirtualAccountWaiting(data: any) {
  // TODO: 가상계좌 입금 대기 처리 로직
  console.log('가상계좌 입금 대기:', data)
}

async function handlePaymentExpired(data: any) {
  // TODO: 결제 만료 처리 로직
  console.log('결제 만료:', data)
}"""

        # API 파일들 생성
        api_files = [
            (self.app_path / "api" / "payment" / "confirm" / "route.ts", confirm_api),
            (self.app_path / "api" / "payment" / "cancel" / "route.ts", cancel_api),
            (self.app_path / "api" / "payment" / "webhook" / "route.ts", webhook_api)
        ]
        
        for file_path, content in api_files:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
        # 동적 라우트용 디렉토리 생성 및 파일 작성
        dynamic_route_dir = self.app_path / "api" / "payment" / "[paymentKey]"
        dynamic_route_dir.mkdir(exist_ok=True)
        
        with open(dynamic_route_dir / "route.ts", 'w', encoding='utf-8') as f:
            f.write(inquiry_api)
            
        self.print_success("Payment APIs created successfully!")
        
    def create_css_styles(self):
        """CSS 스타일 생성"""
        self.print_step("Creating payment CSS...", "🎨")
        
        css_content = """/* Payment specific styles */

.payment-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
}

.payment-card {
  background: rgba(31, 41, 55, 0.8);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(75, 85, 99, 0.3);
  transition: all 0.3s ease;
}

.payment-card:hover {
  border-color: rgba(34, 197, 94, 0.5);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

.payment-input {
  background: rgba(55, 65, 81, 0.8);
  border: 1px solid rgba(75, 85, 99, 0.5);
  transition: all 0.2s ease;
}

.payment-input:focus {
  border-color: #22c55e;
  box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.1);
}

.payment-button {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.payment-button:hover {
  background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
  transform: translateY(-1px);
  box-shadow: 0 10px 25px rgba(59, 130, 246, 0.3);
}

.payment-button:active {
  transform: translateY(0);
}

.payment-success {
  animation: fadeInUp 0.6s ease-out;
}

.payment-error {
  animation: shake 0.5s ease-in-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
  20%, 40%, 60%, 80% { transform: translateX(5px); }
}

/* Loading spinner */
.payment-loading {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 2px solid #ffffff33;
  border-top: 2px solid #ffffff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Responsive design */
@media (max-width: 768px) {
  .payment-grid {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .payment-card {
    padding: 1rem;
  }
}"""

        css_file = self.app_path / "member_payment" / "payment.css"
        with open(css_file, 'w', encoding='utf-8') as f:
            f.write(css_content)
            
        self.print_success("Payment CSS created!")
        
    def create_typescript_types(self):
        """TypeScript 타입 정의 생성"""
        self.print_step("Creating TypeScript types...", "📝")
        
        types_content = """// Payment related TypeScript types

export interface PaymentRequest {
  planName: string
  period: 'monthly' | 'quarterly'
  price: number
  billingCycle: number
}

export interface TossPaymentRequest {
  amount: number
  orderId: string
  orderName: string
  customerName?: string
  customerEmail?: string
  successUrl: string
  failUrl: string
}

export interface PaymentResult {
  success: boolean
  data?: TossPaymentData
  error?: string
}

export interface TossPaymentData {
  paymentKey: string
  orderId: string
  orderName: string
  method: string
  totalAmount: number
  status: 'READY' | 'IN_PROGRESS' | 'WAITING_FOR_DEPOSIT' | 'DONE' | 'CANCELED' | 'PARTIAL_CANCELED' | 'ABORTED' | 'EXPIRED'
  approvedAt: string
  requestedAt: string
  receiptUrl?: string
  card?: {
    company: string
    number: string
    installmentPlanMonths: number
    isInterestFree: boolean
    interestPayer?: string
    approveNo: string
    useCardPoint: boolean
    cardType: string
    ownerType: string
    acquireStatus: string
    receiptUrl?: string
  }
  virtualAccount?: {
    accountType: string
    accountNumber: string
    bankCode: string
    customerName: string
    dueDate: string
    refundStatus: string
    expired: boolean
    settlementStatus: string
    refundReceiveAccount?: {
      bankCode: string
      accountNumber: string
      holderName: string
    }
  }
  receipt?: {
    url: string
  }
}

export interface PaymentError {
  code: string
  message: string
}

export interface CustomerInfo {
  email: string
  phone: string
  customerName: string
  agreeTerms: boolean
  agreePrivacy: boolean
}

export interface PlanInfo {
  name: string
  subtitle: string
  price: number
  popular: boolean
  headerColor: string
}

export interface FeatureInfo {
  name: string
  basic: string
  advanced: string
  premium: string
}"""

        types_file = self.src_path / "types" / "payment.ts"
        with open(types_file, 'w', encoding='utf-8') as f:
            f.write(types_content)
            
        self.print_success("TypeScript types created!")
        
    def update_package_scripts(self):
        """package.json 스크립트 업데이트"""
        self.print_step("Updating package.json scripts...", "📋")
        
        try:
            # npm 명령어로 스크립트 추가
            scripts = [
                ("payment:dev", "next dev --port 3001"),
                ("payment:build", "next build"),
                ("payment:start", "next start --port 3001")
            ]
            
            for script_name, script_command in scripts:
                subprocess.run([
                    "npm", "pkg", "set", f"scripts.{script_name}={script_command}"
                ], check=True, capture_output=True)
                
            self.print_success("Package.json scripts updated!")
            
        except subprocess.CalledProcessError as e:
            self.print_error(f"Failed to update package.json: {e}")
            
    def create_documentation(self):
        """문서 생성"""
        self.print_step("Creating payment documentation...", "📚")
        
        readme_content = """# Payment System Documentation

## 설치 및 설정

### 1. 환경변수 설정
`.env.local` 파일에 다음 환경변수들이 추가되었습니다:

```env
# TossPayments Configuration
NEXT_PUBLIC_TOSS_CLIENT_KEY=test_ck_D5GePWvyJnrK0W0k6q8gLzN97Eoq
TOSS_SECRET_KEY=test_sk_zXLkKEypNArWmo50nX3lmeaxYG5R
```

### 2. API 엔드포인트

- `POST /api/payment/confirm` - 결제 승인
- `POST /api/payment/cancel` - 결제 취소
- `GET /api/payment/[paymentKey]` - 결제 조회
- `POST /api/payment/webhook` - 웹훅 처리

### 3. 결제 플로우

1. 사용자가 멤버십 플랜 선택
2. 결제 정보 입력
3. 토스페이먼츠 결제 요청
4. 결제 승인/실패 처리
5. 결과 페이지 표시

### 4. 테스트 카드 정보

```
카드번호: 4330-1234-1234-1234
유효기간: 12/25
CVC: 123
비밀번호: 1234
```

### 5. 운영 환경 설정

실제 서비스 운영시 다음을 변경해야 합니다:

1. 토스페이먼츠 실제 클라이언트 키 및 시크릿 키로 변경
2. 웹훅 URL 설정 (https://yourdomain.com/api/payment/webhook)
3. 데이터베이스 연동 로직 추가
4. 보안 강화 (CSRF, 입력값 검증 등)

### 6. 보안 고려사항

- API 키는 환경변수로 관리
- 클라이언트 측에서는 절대 시크릿 키 노출 금지
- 결제 금액 검증 로직 필수
- 웹훅 검증 로직 구현 권장

### 7. 에러 처리

결제 실패시 공통 에러 코드:
- `CARD_COMPANY_NOT_AVAILABLE`: 카드사 서비스 중단
- `EXCEED_MAX_CARD_INSTALLMENT_PLAN`: 할부 한도 초과
- `INVALID_CARD_EXPIRATION`: 유효기간 오류
- `INVALID_STOPPED_CARD`: 정지된 카드
- `LIMIT_EXCEEDED`: 한도 초과

### 8. 모니터링

결제 관련 로그는 다음 위치에서 확인:
- 서버 콘솔 로그
- 토스페이먼츠 개발자센터
- 브라우저 개발자도구 (클라이언트)

### 9. Python 스크립트 사용법

```bash
# 스크립트 실행 권한 부여
chmod +x setup_payment.py

# 스크립트 실행
python3 setup_payment.py
```
"""

        readme_file = self.project_root / "PAYMENT_README.md"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
            
        self.print_success("Documentation created!")
        
    def print_completion_summary(self):
        """완료 요약 출력"""
        print("\n" + "="*50)
        print("✅ Payment System Setup Complete!")
        print("="*50)
        print("📁 Created files:")
        print("  - API Routes: src/app/api/payment/")
        print("  - Payment CSS: src/app/member_payment/payment.css")
        print("  - TypeScript types: src/types/payment.ts")
        print("  - Documentation: PAYMENT_README.md")
        print("")
        print("🔧 Configuration:")
        print("  - Environment variables added to .env.local")
        print("  - Dependencies installed: @tosspayments/payment-sdk")
        print("")
        print("🚀 Next Steps:")
        print("  1. Run 'npm run dev' to start development server")
        print("  2. Visit http://localhost:3000/member_payment")
        print("  3. Test payment flow with test card information")
        print("  4. Check PAYMENT_README.md for detailed documentation")
        print("")
        print("⚠️  Important:")
        print("  - Update TOSS_CLIENT_KEY and TOSS_SECRET_KEY for production")
        print("  - Implement database integration for payment records")
        print("  - Set up webhook URL in TossPayments dashboard")
        print("")
        print("Happy coding! 🎉")
        
    def run(self):
        """메인 실행 함수"""
        print("🚀 Payment System Setup Starting...")
        print("="*50)
        
        try:
            self.check_project_structure()
            self.install_dependencies()
            self.setup_environment_variables()
            self.create_api_routes()
            self.create_css_styles()
            self.create_typescript_types()
            self.update_package_scripts()
            self.create_documentation()
            self.print_completion_summary()
            
        except KeyboardInterrupt:
            print("\n❌ Setup cancelled by user")
            sys.exit(1)
        except Exception as e:
            self.print_error(f"Setup failed: {str(e)}")
            sys.exit(1)

def main():
    """메인 함수"""
    setup = PaymentSetup()
    setup.run()

if __name__ == "__main__":
    main()