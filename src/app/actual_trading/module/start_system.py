"""
file: start_system.py
QuanTrade Pro 시스템 시작 스크립트
백엔드와 프론트엔드를 동시에 실행합니다.
"""

import os
import sys
import subprocess
import time
import signal
import threading
import webbrowser
from pathlib import Path

class SystemManager:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.running = True
        
        # 프로젝트 디렉토리 설정
        self.project_dir = Path(__file__).parent
        self.backend_dir = self.project_dir / "backend"
        self.frontend_dir = self.project_dir / "frontend"
        
        # 로그 파일 설정
        self.log_dir = self.project_dir / "logs"
        self.log_dir.mkdir(exist_ok=True)
    
    def check_dependencies(self):
        """시스템 의존성 체크"""
        print("🔍 시스템 의존성 체크 중...")
        
        # Python 버전 체크
        python_version = sys.version_info
        if python_version < (3, 9):
            print(f"❌ Python 3.9+ 필요. 현재 버전: {python_version.major}.{python_version.minor}")
            return False
        
        print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # Node.js 체크
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                node_version = result.stdout.strip()
                print(f"✅ Node.js {node_version}")
            else:
                print("❌ Node.js가 설치되지 않았습니다")
                return False
        except FileNotFoundError:
            print("❌ Node.js가 설치되지 않았습니다")
            return False
        
        # NPM 체크
        try:
            result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                npm_version = result.stdout.strip()
                print(f"✅ NPM {npm_version}")
            else:
                print("❌ NPM이 설치되지 않았습니다")
                return False
        except FileNotFoundError:
            print("❌ NPM이 설치되지 않았습니다")
            return False
        
        # 디렉토리 체크
        if not self.backend_dir.exists():
            print(f"❌ 백엔드 디렉토리가 없습니다: {self.backend_dir}")
            return False
        
        if not self.frontend_dir.exists():
            print(f"❌ 프론트엔드 디렉토리가 없습니다: {self.frontend_dir}")
            return False
        
        # 필수 파일 체크
        if not (self.backend_dir / "main.py").exists():
            print("❌ backend/main.py 파일이 없습니다")
            return False
        
        if not (self.backend_dir / "requirements.txt").exists():
            print("❌ backend/requirements.txt 파일이 없습니다")
            return False
        
        if not (self.frontend_dir / "package.json").exists():
            print("❌ frontend/package.json 파일이 없습니다")
            return False
        
        print("✅ 모든 의존성 체크 완료")
        return True
    
    def install_dependencies(self):
        """의존성 설치"""
        print("\n📦 의존성 설치 중...")
        
        # Python 의존성 설치
        print("🐍 Python 패키지 설치 중...")
        try:
            cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
            result = subprocess.run(
                cmd, 
                cwd=self.backend_dir, 
                capture_output=True, 
                text=True
            )
            
            if result.returncode != 0:
                print(f"❌ Python 패키지 설치 실패:\n{result.stderr}")
                return False
            
            print("✅ Python 패키지 설치 완료")
            
        except Exception as e:
            print(f"❌ Python 패키지 설치 중 오류: {e}")
            return False
        
        # Node.js 의존성 설치
        print("📦 Node.js 패키지 설치 중...")
        try:
            result = subprocess.run(
                ["npm", "install"], 
                cwd=self.frontend_dir, 
                capture_output=True, 
                text=True
            )
            
            if result.returncode != 0:
                print(f"❌ Node.js 패키지 설치 실패:\n{result.stderr}")
                return False
            
            print("✅ Node.js 패키지 설치 완료")
            
        except Exception as e:
            print(f"❌ Node.js 패키지 설치 중 오류: {e}")
            return False
        
        return True
    
    def start_backend(self):
        """백엔드 서버 시작"""
        print("\n🚀 백엔드 서버 시작 중...")
        
        try:
            # 백엔드 로그 파일
            backend_log = self.log_dir / "backend.log"
            
            with open(backend_log, "w") as log_file:
                self.backend_process = subprocess.Popen(
                    [sys.executable, "main.py"],
                    cwd=self.backend_dir,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    text=True
                )
            
            # 서버 시작 대기
            time.sleep(3)
            
            if self.backend_process.poll() is None:
                print("✅ 백엔드 서버 시작됨 (http://localhost:8000)")
                return True
            else:
                print("❌ 백엔드 서버 시작 실패")
                return False
                
        except Exception as e:
            print(f"❌ 백엔드 시작 중 오류: {e}")
            return False
    
    def start_frontend(self):
        """프론트엔드 서버 시작"""
        print("\n🎨 프론트엔드 서버 시작 중...")
        
        try:
            # 프론트엔드 로그 파일
            frontend_log = self.log_dir / "frontend.log"
            
            with open(frontend_log, "w") as log_file:
                self.frontend_process = subprocess.Popen(
                    ["npm", "run", "dev"],
                    cwd=self.frontend_dir,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    text=True
                )
            
            # 서버 시작 대기
            time.sleep(5)
            
            if self.frontend_process.poll() is None:
                print("✅ 프론트엔드 서버 시작됨 (http://localhost:3000)")
                return True
            else:
                print("❌ 프론트엔드 서버 시작 실패")
                return False
                
        except Exception as e:
            print(f"❌ 프론트엔드 시작 중 오류: {e}")
            return False
    
    def check_server_health(self):
        """서버 상태 체크"""
        try:
            import requests
            
            # 백엔드 헬스 체크
            try:
                response = requests.get("http://localhost:8000/health", timeout=5)
                if response.status_code == 200:
                    print("✅ 백엔드 서버 정상 작동")
                else:
                    print(f"⚠️  백엔드 서버 상태 이상: {response.status_code}")
            except requests.RequestException:
                print("❌ 백엔드 서버 연결 실패")
                return False
            
            # 프론트엔드 헬스 체크
            try:
                response = requests.get("http://localhost:3000", timeout=5)
                if response.status_code == 200:
                    print("✅ 프론트엔드 서버 정상 작동")
                else:
                    print(f"⚠️  프론트엔드 서버 상태 이상: {response.status_code}")
            except requests.RequestException:
                print("❌ 프론트엔드 서버 연결 실패")
                return False
            
            return True
            
        except ImportError:
            print("⚠️  requests 모듈이 없어 헬스 체크를 건너뜁니다")
            return True
    
    def open_browser(self):
        """브라우저에서 애플리케이션 열기"""
        try:
            print("\n🌐 브라우저에서 애플리케이션을 엽니다...")
            webbrowser.open("http://localhost:3000")
            time.sleep(2)
        except Exception as e:
            print(f"⚠️  브라우저 열기 실패: {e}")
            print("수동으로 http://localhost:3000 에 접속하세요")
    
    def monitor_processes(self):
        """프로세스 상태 모니터링"""
        while self.running:
            try:
                # 백엔드 프로세스 체크
                if self.backend_process and self.backend_process.poll() is not None:
                    print("❌ 백엔드 프로세스가 종료되었습니다")
                    self.running = False
                    break
                
                # 프론트엔드 프로세스 체크
                if self.frontend_process and self.frontend_process.poll() is not None:
                    print("❌ 프론트엔드 프로세스가 종료되었습니다")
                    self.running = False
                    break
                
                time.sleep(5)
                
            except KeyboardInterrupt:
                break
    
    def cleanup(self):
        """프로세스 정리"""
        print("\n🛑 시스템 종료 중...")
        
        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=5)
                print("✅ 백엔드 서버 종료됨")
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
                print("🔥 백엔드 서버 강제 종료됨")
            except Exception as e:
                print(f"⚠️  백엔드 종료 중 오류: {e}")
        
        if self.frontend_process:
            try:
                self.frontend_process.terminate()
                self.frontend_process.wait(timeout=5)
                print("✅ 프론트엔드 서버 종료됨")
            except subprocess.TimeoutExpired:
                self.frontend_process.kill()
                print("🔥 프론트엔드 서버 강제 종료됨")
            except Exception as e:
                print(f"⚠️  프론트엔드 종료 중 오류: {e}")
    
    def signal_handler(self, signum, frame):
        """시그널 핸들러"""
        print(f"\n📡 시그널 {signum} 수신됨")
        self.running = False
        self.cleanup()
        sys.exit(0)
    
    def start_system(self, install_deps=True, open_browser=True):
        """전체 시스템 시작"""
        print("🚀 QuanTrade Pro 시스템 시작")
        print("=" * 50)
        
        # 시그널 핸들러 등록
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            # 1. 의존성 체크
            if not self.check_dependencies():
                print("❌ 의존성 체크 실패")
                return False
            
            # 2. 의존성 설치 (옵션)
            if install_deps:
                if not self.install_dependencies():
                    print("❌ 의존성 설치 실패")
                    return False
            
            # 3. 백엔드 시작
            if not self.start_backend():
                print("❌ 백엔드 시작 실패")
                return False
            
            # 4. 프론트엔드 시작
            if not self.start_frontend():
                print("❌ 프론트엔드 시작 실패")
                self.cleanup()
                return False
            
            # 5. 서버 상태 체크
            time.sleep(3)
            if not self.check_server_health():
                print("⚠️  서버 상태 체크 실패, 계속 진행합니다")
            
            # 6. 브라우저 열기 (옵션)
            if open_browser:
                self.open_browser()
            
            # 7. 시스템 정보 출력
            self.print_system_info()
            
            # 8. 프로세스 모니터링 시작
            monitor_thread = threading.Thread(target=self.monitor_processes)
            monitor_thread.daemon = True
            monitor_thread.start()
            
            # 9. 메인 루프
            print("\n✅ 시스템이 성공적으로 시작되었습니다!")
            print("Ctrl+C를 눌러 종료하세요")
            
            while self.running:
                try:
                    time.sleep(1)
                except KeyboardInterrupt:
                    break
            
            return True
            
        except Exception as e:
            print(f"❌ 시스템 시작 중 오류: {e}")
            return False
        
        finally:
            self.cleanup()
    
    def print_system_info(self):
        """시스템 정보 출력"""
        print("\n" + "=" * 50)
        print("🎯 QuanTrade Pro 시스템 정보")
        print("=" * 50)
        print(f"📍 프론트엔드: http://localhost:3000")
        print(f"📍 백엔드 API: http://localhost:8000")
        print(f"📍 API 문서: http://localhost:8000/docs")
        print(f"📁 로그 디렉토리: {self.log_dir}")
        print(f"📁 프로젝트 디렉토리: {self.project_dir}")
        print("=" * 50)
        
        print("\n💡 사용법:")
        print("• 웹 브라우저에서 http://localhost:3000 접속")
        print("• 전략을 활성화하고 자동매매 시작 버튼 클릭")
        print("• 실시간 수익 현황 및 주문 내역 모니터링")
        print("• 긴급 상황 시 긴급중단 버튼 사용")
        
        print("\n⚠️  주의사항:")
        print("• 현재는 모의투자 모드로 실행됩니다")
        print("• 실제 거래 전 충분한 테스트를 권장합니다")
        print("• 리스크 관리 설정을 반드시 확인하세요")
        
        print("\n🔧 문제 해결:")
        print(f"• 백엔드 로그: tail -f {self.log_dir}/backend.log")
        print(f"• 프론트엔드 로그: tail -f {self.log_dir}/frontend.log")
        print("• 포트 충돌 시: lsof -i :3000 또는 lsof -i :8000")


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="QuanTrade Pro 시스템 시작 스크립트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python start_system.py              # 전체 시스템 시작
  python start_system.py --no-install # 의존성 설치 건너뛰기
  python start_system.py --no-browser # 브라우저 자동 열기 비활성화
  python start_system.py --check-only # 의존성만 체크하고 종료
        """
    )
    
    parser.add_argument(
        "--no-install", 
        action="store_true",
        help="의존성 설치 건너뛰기"
    )
    
    parser.add_argument(
        "--no-browser", 
        action="store_true",
        help="브라우저 자동 열기 비활성화"
    )
    
    parser.add_argument(
        "--check-only", 
        action="store_true",
        help="의존성만 체크하고 종료"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="상세 로그 출력"
    )
    
    args = parser.parse_args()
    
    # 시스템 매니저 생성
    system_manager = SystemManager()
    
    # 의존성만 체크하고 종료
    if args.check_only:
        print("🔍 의존성 체크 모드")
        if system_manager.check_dependencies():
            print("✅ 모든 의존성이 충족되었습니다")
            sys.exit(0)
        else:
            print("❌ 의존성 문제가 있습니다")
            sys.exit(1)
    
    # 전체 시스템 시작
    success = system_manager.start_system(
        install_deps=not args.no_install,
        open_browser=not args.no_browser
    )
    
    if success:
        print("\n👋 QuanTrade Pro를 이용해 주셔서 감사합니다!")
        sys.exit(0)
    else:
        print("\n❌ 시스템 시작에 실패했습니다")
        sys.exit(1)


if __name__ == "__main__":
    main()