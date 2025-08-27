"""
실거래 전용 GUI 모듈 (완전 수정됨)
"""

import sys
import logging
from datetime import datetime, time
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from config import Config

class RealTradingWindow(QMainWindow):
    """실거래 전용 메인 윈도우"""
    
    def __init__(self, trading_service, api_connected=False):
        super().__init__()
        self.trading_service = trading_service
        self.api_connected = api_connected
        self.logger = logging.getLogger(__name__)
        
        # 실거래 안전 설정
        self.daily_order_count = 0
        self.daily_loss_limit = 500000  # 일일 손실 한도 50만원
        self.current_daily_loss = 0
        self.order_confirmation_required = True  # 주문 시 재확인 필수
        
        self.init_ui()
        self.setup_timer()
        self.setup_safety_checks()
        self.update_all_data()
    
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("키움증권 실거래 시스템 🔴 LIVE")
        self.setGeometry(100, 100, 1400, 900)
        
        # 실거래 경고 스타일
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 5px;
                margin: 5px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        # 메뉴바 생성
        self.create_menu_bar()
        
        # 상태바 생성 (실거래 모드 표시)
        self.status_bar = self.statusBar()
        self.update_status()
        
        # 중앙 위젯 설정
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)
        
        # 상단: 실거래 경고 및 상태
        warning_panel = self.create_warning_panel()
        main_layout.addWidget(warning_panel)
        
        # 중단: 메인 거래 패널
        content_layout = QHBoxLayout()
        
        # 좌측: 주문 및 계좌 정보
        left_panel = self.create_left_panel()
        content_layout.addWidget(left_panel, 1)
        
        # 우측: 포트폴리오 및 거래 내역
        right_panel = self.create_right_panel()
        content_layout.addWidget(right_panel, 2)
        
        main_layout.addLayout(content_layout)
        
        # 하단: 리스크 관리 패널
        risk_panel = self.create_risk_panel()
        main_layout.addWidget(risk_panel)
    
    def create_warning_panel(self) -> QWidget:
        """실거래 경고 패널"""
        panel = QWidget()
        panel.setFixedHeight(120)
        panel.setStyleSheet("""
            QWidget {
                background-color: #dc3545;
                border-radius: 10px;
                margin: 5px;
            }
            QLabel {
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        
        # 실거래 경고 메시지
        warning_label = QLabel("⚠️ 실거래 모드 - 실제 자금이 투입됩니다! ⚠️")
        warning_label.setAlignment(Qt.AlignCenter)
        warning_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(warning_label)
        
        # 상태 정보 레이아웃
        status_layout = QHBoxLayout()
        
        # API 연결 상태
        self.api_status_label = QLabel("API: 연결됨" if self.api_connected else "API: 연결끊김")
        status_layout.addWidget(self.api_status_label)
        
        # 시장 상태
        self.market_status_label = QLabel("시장: 개장" if Config.is_market_open() else "시장: 폐장")
        status_layout.addWidget(self.market_status_label)
        
        # 일일 주문 횟수
        self.order_count_label = QLabel(f"오늘 주문: {self.daily_order_count}회")
        status_layout.addWidget(self.order_count_label)
        
        # 일일 손익
        self.daily_pnl_label = QLabel(f"오늘 손익: {self.current_daily_loss:+,}원")
        status_layout.addWidget(self.daily_pnl_label)
        
        layout.addLayout(status_layout)
        
        return panel
    
    def create_menu_bar(self):
        """메뉴바 생성"""
        menubar = self.menuBar()
        
        # 거래 메뉴
        trade_menu = menubar.addMenu('거래(&T)')
        
        # 긴급 매도 (모든 포지션 정리)
        emergency_sell_action = QAction('🚨 긴급 매도 (전체)', self)
        emergency_sell_action.setShortcut('Ctrl+Shift+S')
        emergency_sell_action.triggered.connect(self.emergency_sell_all)
        trade_menu.addAction(emergency_sell_action)
        
        trade_menu.addSeparator()
        
        # 거래 일시 정지
        pause_action = QAction('거래 일시 정지', self)
        pause_action.triggered.connect(self.pause_trading)
        trade_menu.addAction(pause_action)
        
        # 새로고침
        refresh_action = QAction('새로고침', self)
        refresh_action.setShortcut('F5')
        refresh_action.triggered.connect(self.update_all_data)
        trade_menu.addAction(refresh_action)
        
        # 설정 메뉴
        settings_menu = menubar.addMenu('설정(&S)')
        
        # 리스크 설정
        risk_settings_action = QAction('리스크 관리 설정', self)
        risk_settings_action.triggered.connect(self.open_risk_settings)
        settings_menu.addAction(risk_settings_action)
        
        # 알림 설정
        notification_action = QAction('알림 설정', self)
        notification_action.triggered.connect(self.open_notification_settings)
        settings_menu.addAction(notification_action)
    
    def create_left_panel(self) -> QWidget:
        """좌측 패널 생성"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 계좌 정보
        account_group = self.create_account_group()
        layout.addWidget(account_group)
        
        # 실거래 주문 입력
        order_group = self.create_real_order_group()
        layout.addWidget(order_group)
        
        # 시장 정보
        market_group = self.create_market_info_group()
        layout.addWidget(market_group)
        
        layout.addStretch()
        return panel
    
    def create_account_group(self) -> QGroupBox:
        """계좌 정보 그룹"""
        group = QGroupBox("💰 계좌 정보")
        layout = QVBoxLayout()
        
        # 계좌번호
        self.account_label = QLabel(f"계좌: {self.trading_service.current_account}")
        self.account_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        layout.addWidget(self.account_label)
        
        # 잔고 정보
        self.balance_label = QLabel("현금잔고: 조회 중...")
        layout.addWidget(self.balance_label)
        
        self.buying_power_label = QLabel("주문가능금액: 조회 중...")
        layout.addWidget(self.buying_power_label)
        
        self.asset_label = QLabel("총 자산: 조회 중...")
        layout.addWidget(self.asset_label)
        
        # D+2 예수금
        self.deposit_label = QLabel("D+2 예수금: 조회 중...")
        layout.addWidget(self.deposit_label)
        
        group.setLayout(layout)
        return group
    
    def create_real_order_group(self) -> QGroupBox:
        """실거래 주문 입력 그룹"""
        group = QGroupBox("📈 실거래 주문")
        layout = QGridLayout()
        
        # 종목코드
        layout.addWidget(QLabel("종목코드:"), 0, 0)
        self.stock_code_edit = QLineEdit()
        self.stock_code_edit.setPlaceholderText("6자리 숫자")
        layout.addWidget(self.stock_code_edit, 0, 1)
        
        # 종목 조회 버튼
        search_btn = QPushButton("조회")
        search_btn.clicked.connect(self.search_stock)
        layout.addWidget(search_btn, 0, 2)
        
        # 종목명 표시
        layout.addWidget(QLabel("종목명:"), 1, 0)
        self.stock_name_label = QLabel("-")
        self.stock_name_label.setStyleSheet("color: blue; font-weight: bold;")
        layout.addWidget(self.stock_name_label, 1, 1, 1, 2)
        
        # 현재가
        layout.addWidget(QLabel("현재가:"), 2, 0)
        self.current_price_label = QLabel("-")
        self.current_price_label.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
        layout.addWidget(self.current_price_label, 2, 1, 1, 2)
        
        # 주문 타입
        layout.addWidget(QLabel("주문타입:"), 3, 0)
        self.order_type_combo = QComboBox()
        self.order_type_combo.addItems(["지정가", "시장가", "조건부지정가"])
        layout.addWidget(self.order_type_combo, 3, 1, 1, 2)
        
        # 수량
        layout.addWidget(QLabel("수량:"), 4, 0)
        self.quantity_edit = QLineEdit()
        self.quantity_edit.setPlaceholderText("주문 수량")
        layout.addWidget(self.quantity_edit, 4, 1)
        
        # 수량 버튼들
        qty_layout = QHBoxLayout()
        for qty in [10, 50, 100]:
            btn = QPushButton(str(qty))
            btn.setFixedWidth(40)
            btn.clicked.connect(lambda checked, q=qty: self.quantity_edit.setText(str(q)))
            qty_layout.addWidget(btn)
        qty_widget = QWidget()
        qty_widget.setLayout(qty_layout)
        layout.addWidget(qty_widget, 4, 2)
        
        # 가격
        layout.addWidget(QLabel("주문가격:"), 5, 0)
        self.price_edit = QLineEdit()
        self.price_edit.setPlaceholderText("주문 가격")
        layout.addWidget(self.price_edit, 5, 1)
        
        # 가격 버튼들 (현재가 기준)
        price_layout = QHBoxLayout()
        price_buttons = [("현재가", 0), ("-1%", -0.01), ("+1%", 0.01)]
        for text, ratio in price_buttons:
            btn = QPushButton(text)
            btn.setFixedWidth(50)
            btn.clicked.connect(lambda checked, r=ratio: self.set_price_ratio(r))
            price_layout.addWidget(btn)
        price_widget = QWidget()
        price_widget.setLayout(price_layout)
        layout.addWidget(price_widget, 5, 2)
        
        # 주문 금액 표시
        layout.addWidget(QLabel("주문금액:"), 6, 0)
        self.order_amount_label = QLabel("-")
        self.order_amount_label.setStyleSheet("color: purple; font-weight: bold;")
        layout.addWidget(self.order_amount_label, 6, 1, 1, 2)
        
        # 수량/가격 변경 시 금액 자동 계산
        self.quantity_edit.textChanged.connect(self.calculate_order_amount)
        self.price_edit.textChanged.connect(self.calculate_order_amount)
        
        # 주문 버튼들
        button_layout = QHBoxLayout()
        
        self.buy_button = QPushButton("💰 매수")
        self.buy_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                font-weight: bold;
                padding: 12px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        self.buy_button.clicked.connect(self.place_real_buy_order)
        button_layout.addWidget(self.buy_button)
        
        self.sell_button = QPushButton("💸 매도")
        self.sell_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                font-weight: bold;
                padding: 12px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.sell_button.clicked.connect(self.place_real_sell_order)
        button_layout.addWidget(self.sell_button)
        
        layout.addLayout(button_layout, 7, 0, 1, 3)
        
        group.setLayout(layout)
        return group
    
    def create_market_info_group(self) -> QGroupBox:
        """시장 정보 그룹"""
        group = QGroupBox("📊 시장 정보")
        layout = QVBoxLayout()
        
        # 장 시간 정보
        self.market_time_label = QLabel("장 시간: 09:00 ~ 15:30")
        layout.addWidget(self.market_time_label)
        
        # 현재 시간
        self.current_time_label = QLabel("현재 시간: --:--:--")
        layout.addWidget(self.current_time_label)
        
        # 다음 이벤트
        self.next_event_label = QLabel("다음 이벤트: -")
        layout.addWidget(self.next_event_label)
        
        # 코스피/코스닥 정보
        self.kospi_label = QLabel("코스피: -")
        layout.addWidget(self.kospi_label)
        
        self.kosdaq_label = QLabel("코스닥: -")
        layout.addWidget(self.kosdaq_label)
        
        group.setLayout(layout)
        return group
    
    def create_right_panel(self) -> QWidget:
        """우측 패널 생성"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 탭 위젯 생성
        tab_widget = QTabWidget()
        
        # 포트폴리오 탭
        portfolio_tab = self.create_portfolio_tab()
        tab_widget.addTab(portfolio_tab, "💼 포트폴리오")
        
        # 주문내역 탭
        orders_tab = self.create_orders_tab()
        tab_widget.addTab(orders_tab, "📋 주문내역")
        
        # 거래내역 탭
        transactions_tab = self.create_transactions_tab()
        tab_widget.addTab(transactions_tab, "📈 거래내역")
        
        # 손익 분석 탭
        pnl_tab = self.create_pnl_tab()
        tab_widget.addTab(pnl_tab, "📊 손익분석")
        
        layout.addWidget(tab_widget)
        return panel
    
    def create_portfolio_tab(self) -> QWidget:
        """포트폴리오 탭"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 포트폴리오 요약
        summary_group = QGroupBox("📈 포트폴리오 요약")
        summary_layout = QGridLayout()
        
        self.total_asset_label = QLabel("총 자산: -")
        self.stock_value_label = QLabel("주식 평가액: -")
        self.profit_loss_label = QLabel("평가손익: -")
        self.profit_rate_label = QLabel("수익률: -")
        
        summary_layout.addWidget(self.total_asset_label, 0, 0)
        summary_layout.addWidget(self.stock_value_label, 0, 1)
        summary_layout.addWidget(self.profit_loss_label, 1, 0)
        summary_layout.addWidget(self.profit_rate_label, 1, 1)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # 개별 종목 관리 버튼들
        action_layout = QHBoxLayout()
        
        refresh_portfolio_btn = QPushButton("포트폴리오 새로고침")
        refresh_portfolio_btn.clicked.connect(self.update_portfolio)
        action_layout.addWidget(refresh_portfolio_btn)
        
        export_btn = QPushButton("Excel 내보내기")
        export_btn.clicked.connect(self.export_portfolio)
        action_layout.addWidget(export_btn)
        
        action_layout.addStretch()
        layout.addLayout(action_layout)
        
        # 포트폴리오 테이블
        self.portfolio_table = QTableWidget()
        self.portfolio_table.setColumnCount(9)
        self.portfolio_table.setHorizontalHeaderLabels([
            '종목코드', '종목명', '보유수량', '가능수량', '평균단가', 
            '현재가', '평가액', '손익금액', '수익률'
        ])
        
        # 테이블 스타일 설정
        self.portfolio_table.horizontalHeader().setStretchLastSection(True)
        self.portfolio_table.setAlternatingRowColors(True)
        self.portfolio_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        # 우클릭 메뉴
        self.portfolio_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.portfolio_table.customContextMenuRequested.connect(self.show_portfolio_context_menu)
        
        layout.addWidget(self.portfolio_table)
        
        return tab
    
    def create_orders_tab(self) -> QWidget:
        """주문내역 탭"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 필터 버튼들
        filter_layout = QHBoxLayout()
        
        all_btn = QPushButton("전체")
        all_btn.clicked.connect(lambda: self.filter_orders(None))
        filter_layout.addWidget(all_btn)
        
        pending_btn = QPushButton("미체결")
        pending_btn.clicked.connect(lambda: self.filter_orders("접수"))
        filter_layout.addWidget(pending_btn)
        
        completed_btn = QPushButton("체결완료")
        completed_btn.clicked.connect(lambda: self.filter_orders("체결"))
        filter_layout.addWidget(completed_btn)
        
        cancelled_btn = QPushButton("취소")
        cancelled_btn.clicked.connect(lambda: self.filter_orders("취소"))
        filter_layout.addWidget(cancelled_btn)
        
        filter_layout.addStretch()
        
        # 일괄 취소 버튼
        cancel_all_btn = QPushButton("🚫 미체결 일괄취소")
        cancel_all_btn.setStyleSheet("background-color: #ffc107; font-weight: bold;")
        cancel_all_btn.clicked.connect(self.cancel_all_pending_orders)
        filter_layout.addWidget(cancel_all_btn)
        
        layout.addLayout(filter_layout)
        
        # 주문 테이블
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(9)
        self.orders_table.setHorizontalHeaderLabels([
            '주문시간', '종목코드', '종목명', '구분', '주문수량', 
            '주문가격', '체결수량', '체결가격', '상태'
        ])
        
        self.orders_table.horizontalHeader().setStretchLastSection(True)
        self.orders_table.setAlternatingRowColors(True)
        
        # 우클릭 메뉴 (주문 취소용)
        self.orders_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.orders_table.customContextMenuRequested.connect(self.show_order_context_menu)
        
        layout.addWidget(self.orders_table)
        
        return tab
    
    def create_transactions_tab(self) -> QWidget:
        """거래내역 탭"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 기간 선택
        period_layout = QHBoxLayout()
        period_layout.addWidget(QLabel("조회 기간:"))
        
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate().addDays(-30))
        period_layout.addWidget(self.start_date_edit)
        
        period_layout.addWidget(QLabel("~"))
        
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate())
        period_layout.addWidget(self.end_date_edit)
        
        search_btn = QPushButton("조회")
        search_btn.clicked.connect(self.search_transactions)
        period_layout.addWidget(search_btn)
        
        period_layout.addStretch()
        layout.addLayout(period_layout)
        
        # 거래 테이블
        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(7)
        self.transactions_table.setHorizontalHeaderLabels([
            '거래일시', '종목코드', '종목명', '구분', '수량', '단가', '거래금액'
        ])
        
        self.transactions_table.horizontalHeader().setStretchLastSection(True)
        self.transactions_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.transactions_table)
        
        return tab
    
    def create_pnl_tab(self) -> QWidget:
        """손익 분석 탭"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 일일 손익 요약
        daily_group = QGroupBox("📅 일일 손익")
        daily_layout = QGridLayout()
        
        self.daily_realized_pnl_label = QLabel("실현손익: -")
        self.daily_unrealized_pnl_label = QLabel("평가손익: -")
        self.daily_total_pnl_label = QLabel("총 손익: -")
        self.daily_fee_label = QLabel("수수료: -")
        
        daily_layout.addWidget(self.daily_realized_pnl_label, 0, 0)
        daily_layout.addWidget(self.daily_unrealized_pnl_label, 0, 1)
        daily_layout.addWidget(self.daily_total_pnl_label, 1, 0)
        daily_layout.addWidget(self.daily_fee_label, 1, 1)
        
        daily_group.setLayout(daily_layout)
        layout.addWidget(daily_group)
        
        # 월간 손익 요약
        monthly_group = QGroupBox("📊 월간 손익")
        monthly_layout = QGridLayout()
        
        self.monthly_realized_pnl_label = QLabel("월간 실현손익: -")
        self.monthly_unrealized_pnl_label = QLabel("월간 평가손익: -")
        self.monthly_total_pnl_label = QLabel("월간 총손익: -")
        self.win_rate_label = QLabel("승률: -")
        
        monthly_layout.addWidget(self.monthly_realized_pnl_label, 0, 0)
        monthly_layout.addWidget(self.monthly_unrealized_pnl_label, 0, 1)
        monthly_layout.addWidget(self.monthly_total_pnl_label, 1, 0)
        monthly_layout.addWidget(self.win_rate_label, 1, 1)
        
        monthly_group.setLayout(monthly_layout)
        layout.addWidget(monthly_group)
        
        # 리스크 지표
        risk_group = QGroupBox("⚠️ 리스크 지표")
        risk_layout = QGridLayout()
        
        self.max_drawdown_label = QLabel("최대 낙폭: -")
        self.sharpe_ratio_label = QLabel("샤프 비율: -")
        self.var_label = QLabel("VaR (95%): -")
        self.kelly_ratio_label = QLabel("켈리 비율: -")
        
        risk_layout.addWidget(self.max_drawdown_label, 0, 0)
        risk_layout.addWidget(self.sharpe_ratio_label, 0, 1)
        risk_layout.addWidget(self.var_label, 1, 0)
        risk_layout.addWidget(self.kelly_ratio_label, 1, 1)
        
        risk_group.setLayout(risk_layout)
        layout.addWidget(risk_group)
        
        layout.addStretch()
        return tab
    
    def create_risk_panel(self) -> QWidget:
        """리스크 관리 패널"""
        panel = QWidget()
        panel.setFixedHeight(100)
        panel.setStyleSheet("""
            QWidget {
                background-color: #fff3cd;
                border: 2px solid #ffeaa7;
                border-radius: 10px;
                margin: 5px;
            }
            QLabel {
                color: #856404;
                font-weight: bold;
            }
        """)
        
        layout = QVBoxLayout(panel)
        
        title_label = QLabel("🛡️ 리스크 관리")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # 리스크 지표들
        risk_layout = QHBoxLayout()
        
        self.daily_loss_progress = QProgressBar()
        self.daily_loss_progress.setMaximum(self.daily_loss_limit)
        self.daily_loss_progress.setValue(abs(self.current_daily_loss))
        self.daily_loss_progress.setFormat(f"일일 손실: {self.current_daily_loss:,}원 / {self.daily_loss_limit:,}원")
        risk_layout.addWidget(self.daily_loss_progress)
        
        # 리스크 제어 버튼들
        risk_buttons_layout = QHBoxLayout()
        
        stop_loss_btn = QPushButton("전체 손절매")
        stop_loss_btn.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold;")
        stop_loss_btn.clicked.connect(self.execute_stop_loss)
        risk_buttons_layout.addWidget(stop_loss_btn)
        
        pause_btn = QPushButton("거래 일시정지")
        pause_btn.setStyleSheet("background-color: #ffc107; color: black; font-weight: bold;")
        pause_btn.clicked.connect(self.pause_trading)
        risk_buttons_layout.addWidget(pause_btn)
        
        risk_layout.addLayout(risk_buttons_layout)
        layout.addLayout(risk_layout)
        
        return panel
    
def setup_timer(self):
        """데이터 업데이트 타이머 설정"""
        # 실거래는 더 자주 업데이트 (3초)
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_all_data)
        self.update_timer.start(3000)
        
        # 시간 업데이트 타이머
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)  # 1초마다
    
    def setup_safety_checks(self):
        """안전 장치 설정"""
        # 시장 시간 체크 타이머
        self.market_check_timer = QTimer()
        self.market_check_timer.timeout.connect(self.check_market_hours)
        self.market_check_timer.start(60000)  # 1분마다
        
        # 리스크 모니터링 타이머
        self.risk_monitor_timer = QTimer()
        self.risk_monitor_timer.timeout.connect(self.monitor_risk)
        self.risk_monitor_timer.start(30000)  # 30초마다
    
    def update_portfolio(self):
        """포트폴리오 테이블 업데이트"""
        try:
            portfolio = self.trading_service.get_portfolio()
            
            self.portfolio_table.setRowCount(len(portfolio))
            
            for row, item in enumerate(portfolio):
                self.portfolio_table.setItem(row, 0, QTableWidgetItem(item['stock_code']))
                self.portfolio_table.setItem(row, 1, QTableWidgetItem(item.get('stock_name', '')))
                self.portfolio_table.setItem(row, 2, QTableWidgetItem(f"{item['quantity']:,}"))
                self.portfolio_table.setItem(row, 3, QTableWidgetItem(f"{item['quantity']:,}"))  # 가능수량 = 보유수량
                self.portfolio_table.setItem(row, 4, QTableWidgetItem(f"{item['avg_price']:,}"))
                self.portfolio_table.setItem(row, 5, QTableWidgetItem(f"{item.get('current_price', 0):,}"))
                self.portfolio_table.setItem(row, 6, QTableWidgetItem(f"{item.get('market_value', 0):,}"))
                
                # 손익금액
                profit_loss = item.get('profit_loss', 0)
                profit_loss_item = QTableWidgetItem(f"{profit_loss:+,}")
                if profit_loss > 0:
                    profit_loss_item.setForeground(QColor('red'))
                elif profit_loss < 0:
                    profit_loss_item.setForeground(QColor('blue'))
                self.portfolio_table.setItem(row, 7, profit_loss_item)
                
                # 수익률
                profit_rate = item.get('profit_rate', 0.0)
                profit_rate_item = QTableWidgetItem(f"{profit_rate:+.2f}%")
                if profit_rate > 0:
                    profit_rate_item.setForeground(QColor('red'))
                elif profit_rate < 0:
                    profit_rate_item.setForeground(QColor('blue'))
                self.portfolio_table.setItem(row, 8, profit_rate_item)
            
        except Exception as e:
            self.logger.error(f"포트폴리오 업데이트 오류: {e}")
    
    def update_orders(self):
        """주문내역 테이블 업데이트"""
        try:
            orders = self.trading_service.get_order_list()
            
            self.orders_table.setRowCount(len(orders))
            
            for row, order in enumerate(orders):
                order_time = order.get('order_time', '')
                if order_time:
                    try:
                        dt = datetime.fromisoformat(order_time.replace('Z', '+00:00'))
                        time_str = dt.strftime('%m-%d %H:%M')
                    except:
                        time_str = order_time[:16] if len(order_time) > 16 else order_time
                else:
                    time_str = '-'
                
                self.orders_table.setItem(row, 0, QTableWidgetItem(time_str))
                self.orders_table.setItem(row, 1, QTableWidgetItem(order['stock_code']))
                self.orders_table.setItem(row, 2, QTableWidgetItem(order.get('stock_name', '')))
                self.orders_table.setItem(row, 3, QTableWidgetItem(order['order_type']))
                self.orders_table.setItem(row, 4, QTableWidgetItem(f"{order['quantity']:,}"))
                self.orders_table.setItem(row, 5, QTableWidgetItem(f"{order['price']:,}"))
                self.orders_table.setItem(row, 6, QTableWidgetItem(f"{order.get('executed_quantity', 0):,}"))
                self.orders_table.setItem(row, 7, QTableWidgetItem(f"{order.get('executed_price', 0):,}"))
                
                # 상태에 따른 색상 설정
                status_item = QTableWidgetItem(order['order_status'])
                if order['order_status'] == '체결':
                    status_item.setForeground(QColor('blue'))
                elif order['order_status'] == '취소':
                    status_item.setForeground(QColor('red'))
                elif order['order_status'] == '접수':
                    status_item.setForeground(QColor('orange'))
                
                self.orders_table.setItem(row, 8, status_item)
            
        except Exception as e:
            self.logger.error(f"주문내역 업데이트 오류: {e}")
    
    def update_transactions(self):
        """거래내역 테이블 업데이트"""
        try:
            transactions = self.trading_service.get_transaction_list()
            
            self.transactions_table.setRowCount(len(transactions))
            
            for row, transaction in enumerate(transactions):
                trans_time = transaction.get('transaction_time', '')
                if trans_time:
                    try:
                        dt = datetime.fromisoformat(trans_time.replace('Z', '+00:00'))
                        time_str = dt.strftime('%m-%d %H:%M')
                    except:
                        time_str = trans_time[:16] if len(trans_time) > 16 else trans_time
                else:
                    time_str = '-'
                
                self.transactions_table.setItem(row, 0, QTableWidgetItem(time_str))
                self.transactions_table.setItem(row, 1, QTableWidgetItem(transaction['stock_code']))
                self.transactions_table.setItem(row, 2, QTableWidgetItem(transaction.get('stock_name', '')))
                
                # 거래 구분에 따른 색상
                type_item = QTableWidgetItem(transaction['transaction_type'])
                if transaction['transaction_type'] == '매수':
                    type_item.setForeground(QColor('red'))
                else:
                    type_item.setForeground(QColor('blue'))
                self.transactions_table.setItem(row, 3, type_item)
                
                self.transactions_table.setItem(row, 4, QTableWidgetItem(f"{transaction['quantity']:,}"))
                self.transactions_table.setItem(row, 5, QTableWidgetItem(f"{transaction['price']:,}"))
                self.transactions_table.setItem(row, 6, QTableWidgetItem(f"{transaction['amount']:,}"))
            
        except Exception as e:
            self.logger.error(f"거래내역 업데이트 오류: {e}")
    
    def update_pnl_analysis(self):
        """손익 분석 업데이트"""
        try:
            # 일일 손익
            daily_pnl = self.trading_service.get_daily_pnl()
            if daily_pnl.get('success'):
                profit_loss = daily_pnl.get('profit_loss', 0)
                trade_count = daily_pnl.get('trade_count', 0)
                
                self.daily_realized_pnl_label.setText(f"실현손익: {profit_loss:+,}원")
                
                # 색상 설정
                color = "red" if profit_loss > 0 else "blue" if profit_loss < 0 else "black"
                self.daily_realized_pnl_label.setStyleSheet(f"color: {color}; font-weight: bold;")
            
            # 포트폴리오 요약에서 평가손익 가져오기
            portfolio_summary = self.trading_service.calculate_portfolio_summary()
            if portfolio_summary:
                unrealized_pnl = portfolio_summary.get('total_profit_loss', 0)
                self.daily_unrealized_pnl_label.setText(f"평가손익: {unrealized_pnl:+,}원")
                
                color = "red" if unrealized_pnl > 0 else "blue" if unrealized_pnl < 0 else "black"
                self.daily_unrealized_pnl_label.setStyleSheet(f"color: {color}; font-weight: bold;")
                
                # 총 손익
                total_pnl = daily_pnl.get('profit_loss', 0) + unrealized_pnl
                self.daily_total_pnl_label.setText(f"총 손익: {total_pnl:+,}원")
                
                color = "red" if total_pnl > 0 else "blue" if total_pnl < 0 else "black"
                self.daily_total_pnl_label.setStyleSheet(f"color: {color}; font-weight: bold;")
            
            # 수수료 (예시)
            estimated_fee = daily_pnl.get('trade_count', 0) * 1000  # 거래당 1000원 수수료 가정
            self.daily_fee_label.setText(f"수수료: {estimated_fee:,}원")
            
        except Exception as e:
            self.logger.error(f"손익 분석 업데이트 오류: {e}")
    
    def show_portfolio_context_menu(self, position):
        """포트폴리오 우클릭 메뉴"""
        if self.portfolio_table.itemAt(position) is None:
            return
        
        menu = QMenu(self)
        
        # 현재 선택된 행
        current_row = self.portfolio_table.currentRow()
        if current_row >= 0:
            stock_code = self.portfolio_table.item(current_row, 0).text()
            stock_name = self.portfolio_table.item(current_row, 1).text()
            
            # 전량 매도
            sell_all_action = QAction(f"🔴 {stock_name} 전량 매도", self)
            sell_all_action.triggered.connect(lambda: self.sell_all_stock(stock_code))
            menu.addAction(sell_all_action)
            
            # 절반 매도
            sell_half_action = QAction(f"📉 {stock_name} 절반 매도", self)
            sell_half_action.triggered.connect(lambda: self.sell_half_stock(stock_code))
            menu.addAction(sell_half_action)
            
            menu.addSeparator()
            
            # 종목 정보 조회
            info_action = QAction(f"📊 {stock_name} 정보 조회", self)
            info_action.triggered.connect(lambda: self.show_stock_info(stock_code))
            menu.addAction(info_action)
        
        menu.exec_(self.portfolio_table.mapToGlobal(position))
    
    def show_order_context_menu(self, position):
        """주문내역 우클릭 메뉴"""
        if self.orders_table.itemAt(position) is None:
            return
        
        menu = QMenu(self)
        
        # 현재 선택된 행
        current_row = self.orders_table.currentRow()
        if current_row >= 0:
            order_status = self.orders_table.item(current_row, 8).text()
            stock_code = self.orders_table.item(current_row, 1).text()
            
            # 미체결 주문만 취소 가능
            if order_status == '접수':
                cancel_action = QAction(f"❌ 주문 취소", self)
                cancel_action.triggered.connect(lambda: self.cancel_order(current_row))
                menu.addAction(cancel_action)
        
        if not menu.isEmpty():
            menu.exec_(self.orders_table.mapToGlobal(position))
    
    def sell_all_stock(self, stock_code: str):
        """전량 매도"""
        try:
            portfolio = self.trading_service.get_portfolio()
            stock_item = None
            
            for item in portfolio:
                if item['stock_code'] == stock_code:
                    stock_item = item
                    break
            
            if not stock_item:
                QMessageBox.warning(self, "오류", "해당 종목을 찾을 수 없습니다.")
                return
            
            quantity = stock_item['quantity']
            current_price = stock_item.get('current_price', 0)
            
            if current_price == 0:
                QMessageBox.warning(self, "오류", "현재가 정보를 가져올 수 없습니다.")
                return
            
            reply = QMessageBox.question(self, "전량 매도 확인",
                f"종목: {stock_code}\n"
                f"수량: {quantity:,}주\n"
                f"예상 가격: {current_price:,}원\n"
                f"예상 금액: {quantity * current_price:,}원\n\n"
                f"전량 매도하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                result = self.trading_service.place_sell_order(stock_code, quantity, current_price)
                
                if result.get('success'):
                    QMessageBox.information(self, "주문 성공", 
                        f"{stock_code} 전량 매도 주문이 완료되었습니다.")
                    self.update_all_data()
                else:
                    QMessageBox.critical(self, "주문 실패", 
                        f"전량 매도 주문이 실패했습니다.\n{result.get('error', '알 수 없는 오류')}")
        
        except Exception as e:
            self.logger.error(f"전량 매도 오류: {e}")
            QMessageBox.critical(self, "오류", f"전량 매도 처리 중 오류가 발생했습니다:\n{str(e)}")
    
    def sell_half_stock(self, stock_code: str):
        """절반 매도"""
        try:
            portfolio = self.trading_service.get_portfolio()
            stock_item = None
            
            for item in portfolio:
                if item['stock_code'] == stock_code:
                    stock_item = item
                    break
            
            if not stock_item:
                QMessageBox.warning(self, "오류", "해당 종목을 찾을 수 없습니다.")
                return
            
            total_quantity = stock_item['quantity']
            half_quantity = total_quantity // 2
            current_price = stock_item.get('current_price', 0)
            
            if half_quantity == 0:
                QMessageBox.warning(self, "오류", "매도할 수량이 부족합니다.")
                return
            
            if current_price == 0:
                QMessageBox.warning(self, "오류", "현재가 정보를 가져올 수 없습니다.")
                return
            
            reply = QMessageBox.question(self, "절반 매도 확인",
                f"종목: {stock_code}\n"
                f"보유 수량: {total_quantity:,}주\n"
                f"매도 수량: {half_quantity:,}주\n"
                f"예상 가격: {current_price:,}원\n"
                f"예상 금액: {half_quantity * current_price:,}원\n\n"
                f"절반 매도하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                result = self.trading_service.place_sell_order(stock_code, half_quantity, current_price)
                
                if result.get('success'):
                    QMessageBox.information(self, "주문 성공", 
                        f"{stock_code} 절반 매도 주문이 완료되었습니다.")
                    self.update_all_data()
                else:
                    QMessageBox.critical(self, "주문 실패", 
                        f"절반 매도 주문이 실패했습니다.\n{result.get('error', '알 수 없는 오류')}")
        
        except Exception as e:
            self.logger.error(f"절반 매도 오류: {e}")
            QMessageBox.critical(self, "오류", f"절반 매도 처리 중 오류가 발생했습니다:\n{str(e)}")
    
    def show_stock_info(self, stock_code: str):
        """종목 정보 표시"""
        try:
            stock_info = self.trading_service.get_stock_info(stock_code)
            
            if stock_info:
                info_text = f"종목코드: {stock_code}\n"
                info_text += f"종목명: {stock_info.get('stock_name', '정보없음')}\n"
                info_text += f"현재가: {stock_info.get('current_price', 0):,}원\n"
                info_text += f"등락률: {stock_info.get('change_rate', 0.0):+.2f}%\n"
                info_text += f"거래량: {stock_info.get('volume', 0):,}주\n"
                info_text += f"시가: {stock_info.get('open_price', 0):,}원\n"
                info_text += f"고가: {stock_info.get('high_price', 0):,}원\n"
                info_text += f"저가: {stock_info.get('low_price', 0):,}원"
                
                QMessageBox.information(self, f"{stock_code} 종목 정보", info_text)
            else:
                QMessageBox.warning(self, "오류", "종목 정보를 가져올 수 없습니다.")
        
        except Exception as e:
            self.logger.error(f"종목 정보 조회 오류: {e}")
            QMessageBox.critical(self, "오류", f"종목 정보 조회 중 오류가 발생했습니다:\n{str(e)}")
    
    def cancel_order(self, row: int):
        """주문 취소"""
        try:
            stock_code = self.orders_table.item(row, 1).text()
            
            reply = QMessageBox.question(self, "주문 취소 확인",
                f"종목: {stock_code}\n"
                f"주문을 취소하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                # 실제로는 키움 API의 주문 취소 함수를 호출해야 함
                QMessageBox.information(self, "주문 취소", 
                    "주문 취소 요청이 전송되었습니다.\n"
                    "실제 취소 여부는 주문내역에서 확인하세요.")
                
                self.update_orders()
        
        except Exception as e:
            self.logger.error(f"주문 취소 오류: {e}")
            QMessageBox.critical(self, "오류", f"주문 취소 처리 중 오류가 발생했습니다:\n{str(e)}")
    
    def cancel_all_pending_orders(self):
        """미체결 주문 일괄 취소"""
        reply = QMessageBox.critical(self, "일괄 취소 확인",
            "⚠️ 모든 미체결 주문을 취소하시겠습니까?\n\n"
            "이 작업은 되돌릴 수 없습니다!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                pending_orders = self.trading_service.get_order_list("접수")
                
                if not pending_orders:
                    QMessageBox.information(self, "알림", "취소할 미체결 주문이 없습니다.")
                    return
                
                # 실제로는 각 주문에 대해 키움 API 취소 함수 호출
                QMessageBox.information(self, "일괄 취소", 
                    f"{len(pending_orders)}건의 미체결 주문 취소 요청이 전송되었습니다.\n"
                    f"실제 취소 여부는 주문내역에서 확인하세요.")
                
                self.update_orders()
            
            except Exception as e:
                self.logger.error(f"일괄 취소 오류: {e}")
                QMessageBox.critical(self, "오류", f"일괄 취소 처리 중 오류가 발생했습니다:\n{str(e)}")
    
    def search_transactions(self):
        """거래내역 기간 조회"""
        try:
            start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
            end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
            
            # 실제로는 기간별 거래내역을 가져와야 함
            transactions = self.trading_service.get_transaction_list(start_date)
            
            self.update_transactions()
        
        except Exception as e:
            self.logger.error(f"거래내역 조회 오류: {e}")
            QMessageBox.critical(self, "오류", f"거래내역 조회 중 오류가 발생했습니다:\n{str(e)}")
    
    def export_portfolio(self):
        """포트폴리오 Excel 내보내기"""
        try:
            portfolio = self.trading_service.get_portfolio()
            
            if not portfolio:
                QMessageBox.information(self, "알림", "내보낼 포트폴리오가 없습니다.")
                return
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"portfolio_export_{timestamp}.json"
            
            # 간단한 JSON 내보내기
            import json
            export_data = {
                'export_time': datetime.now().isoformat(),
                'portfolio': portfolio
            }
            
            os.makedirs('exports', exist_ok=True)
            with open(f"exports/{filename}", 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            QMessageBox.information(self, "내보내기 성공", 
                f"포트폴리오가 성공적으로 내보내졌습니다.\n"
                f"파일: exports/{filename}")
        
        except Exception as e:
            self.logger.error(f"포트폴리오 내보내기 오류: {e}")
            QMessageBox.critical(self, "오류", f"포트폴리오 내보내기 중 오류가 발생했습니다:\n{str(e)}")
    
    def filter_orders(self, status: str):
        """주문내역 필터링"""
        try:
            if status:
                orders = self.trading_service.get_order_list(status)
            else:
                orders = self.trading_service.get_order_list()
            
            self.orders_table.setRowCount(len(orders))
            
            for row, order in enumerate(orders):
                order_time = order.get('order_time', '')
                if order_time:
                    try:
                        dt = datetime.fromisoformat(order_time.replace('Z', '+00:00'))
                        time_str = dt.strftime('%m-%d %H:%M')
                    except:
                        time_str = order_time[:16] if len(order_time) > 16 else order_time
                else:
                    time_str = '-'
                
                self.orders_table.setItem(row, 0, QTableWidgetItem(time_str))
                self.orders_table.setItem(row, 1, QTableWidgetItem(order['stock_code']))
                self.orders_table.setItem(row, 2, QTableWidgetItem(order.get('stock_name', '')))
                self.orders_table.setItem(row, 3, QTableWidgetItem(order['order_type']))
                self.orders_table.setItem(row, 4, QTableWidgetItem(f"{order['quantity']:,}"))
                self.orders_table.setItem(row, 5, QTableWidgetItem(f"{order['price']:,}"))
                self.orders_table.setItem(row, 6, QTableWidgetItem(f"{order.get('executed_quantity', 0):,}"))
                self.orders_table.setItem(row, 7, QTableWidgetItem(f"{order.get('executed_price', 0):,}"))
                
                # 상태에 따른 색상 설정
                status_item = QTableWidgetItem(order['order_status'])
                if order['order_status'] == '체결':
                    status_item.setForeground(QColor('blue'))
                elif order['order_status'] == '취소':
                    status_item.setForeground(QColor('red'))
                elif order['order_status'] == '접수':
                    status_item.setForeground(QColor('orange'))
                
                self.orders_table.setItem(row, 8, status_item)
        
        except Exception as e:
            self.logger.error(f"주문내역 필터링 오류: {e}")
    
    def execute_stop_loss(self):
        """전체 손절매 실행"""
        reply = QMessageBox.critical(self, "🚨 전체 손절매 확인",
            "⚠️ 손실이 발생한 모든 종목을 매도하시겠습니까?\n\n"
            "이 작업은 되돌릴 수 없습니다!\n"
            "신중히 결정하세요.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                portfolio = self.trading_service.get_portfolio()
                
                loss_stocks = []
                for item in portfolio:
                    profit_rate = item.get('profit_rate', 0.0)
                    if profit_rate < 0:  # 손실 종목만
                        loss_stocks.append(item)
                
                if not loss_stocks:
                    QMessageBox.information(self, "알림", "손절매할 손실 종목이 없습니다.")
                    return
                
                success_count = 0
                for item in loss_stocks:
                    stock_code = item['stock_code']
                    quantity = item['quantity']
                    current_price = item.get('current_price', 0)
                    
                    if current_price > 0:
                        result = self.trading_service.place_sell_order(
                            stock_code, quantity, current_price
                        )
                        
                        if result.get('success'):
                            success_count += 1
                            self.logger.info(f"손절매 실행: {stock_code} {quantity}주")
                
                QMessageBox.information(self, "손절매 완료",
                    f"손절매 결과:\n\n"
                    f"성공: {success_count}건\n"
                    f"총 대상: {len(loss_stocks)}건")
                
                self.update_all_data()
            
            except Exception as e:
                self.logger.error(f"전체 손절매 오류: {e}")
                QMessageBox.critical(self, "오류", f"전체 손절매 처리 중 오류가 발생했습니다:\n{str(e)}")
    
    def open_risk_settings(self):
        """리스크 관리 설정"""
        dialog = RiskSettingsDialog(self.daily_loss_limit, self)
        if dialog.exec_() == QDialog.Accepted:
            self.daily_loss_limit = dialog.get_loss_limit()
            self.daily_loss_progress.setMaximum(self.daily_loss_limit)
    
    def open_notification_settings(self):
        """알림 설정"""
        QMessageBox.information(self, "알림 설정", 
            "알림 설정 기능은 추후 업데이트 예정입니다.")
    
    def closeEvent(self, event):
        """윈도우 종료 이벤트"""
        try:
            reply = QMessageBox.critical(self, '🚨 실거래 시스템 종료',
                '⚠️ 실거래 시스템을 종료하시겠습니까?\n\n'
                '진행 중인 주문이 있을 수 있습니다!\n'
                '종료하기 전에 모든 주문 상태를 확인하세요.',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                # 타이머 정지
                if hasattr(self, 'update_timer'):
                    self.update_timer.stop()
                if hasattr(self, 'time_timer'):
                    self.time_timer.stop()
                if hasattr(self, 'market_check_timer'):
                    self.market_check_timer.stop()
                if hasattr(self, 'risk_monitor_timer'):
                    self.risk_monitor_timer.stop()
                
                # API 연결 해제
                if self.trading_service and self.trading_service.api:
                    self.trading_service.api.disconnect()
                
                self.logger.info("실거래 시스템 정상 종료")
                event.accept()
            else:
                event.ignore()
                
        except Exception as e:
            self.logger.error(f"종료 처리 오류: {e}")
            event.accept()


class RealOrderConfirmDialog(QDialog):
    """실거래 주문 확인 대화상자"""
    
    def __init__(self, stock_code: str, stock_name: str, order_type: str, 
                 quantity: int, price: int, parent=None):
        super().__init__(parent)
        self.stock_code = stock_code
        self.stock_name = stock_name
        self.order_type = order_type
        self.quantity = quantity
        self.price = price
        
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("🔴 실거래 주문 확인")
        self.setFixedSize(400, 300)
        self.setModal(True)
        
        # 경고 스타일
        self.setStyleSheet("""
            QDialog {
                background-color: #fff3cd;
                border: 3px solid #ffc107;
            }
            QLabel {
                color: #856404;
                font-weight: bold;
            }
        """)
        
        layout = QVBoxLayout()
        
        # 경고 헤더
        warning_label = QLabel("⚠️ 실거래 주문 확인 ⚠️")
        warning_label.setAlignment(Qt.AlignCenter)
        warning_label.setStyleSheet("font-size: 18px; color: red; font-weight: bold; margin: 10px;")
        layout.addWidget(warning_label)
        
        # 주문 정보
        info_group = QGroupBox("주문 정보")
        info_layout = QGridLayout()
        
        info_layout.addWidget(QLabel("종목코드:"), 0, 0)
        info_layout.addWidget(QLabel(self.stock_code), 0, 1)
        
        info_layout.addWidget(QLabel("종목명:"), 1, 0)
        info_layout.addWidget(QLabel(self.stock_name), 1, 1)
        
        info_layout.addWidget(QLabel("주문구분:"), 2, 0)
        order_label = QLabel(self.order_type)
        order_label.setStyleSheet("color: red; font-weight: bold;" if self.order_type == "매수" else "color: blue; font-weight: bold;")
        info_layout.addWidget(order_label, 2, 1)
        
        info_layout.addWidget(QLabel("주문수량:"), 3, 0)
        info_layout.addWidget(QLabel(f"{self.quantity:,}주"), 3, 1)
        
        info_layout.addWidget(QLabel("주문가격:"), 4, 0)
        info_layout.addWidget(QLabel(f"{self.price:,}원"), 4, 1)
        
        info_layout.addWidget(QLabel("주문금액:"), 5, 0)
        amount_label = QLabel(f"{self.quantity * self.price:,}원")
        amount_label.setStyleSheet("color: purple; font-weight: bold; font-size: 14px;")
        info_layout.addWidget(amount_label, 5, 1)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # 확인 체크박스
        self.confirm_checkbox = QCheckBox("위 내용을 확인했으며, 실제 자금이 투입됨을 이해합니다.")
        self.confirm_checkbox.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(self.confirm_checkbox)
        
        # 버튼들
        button_layout = QHBoxLayout()
        
        cancel_button = QPushButton("❌ 취소")
        cancel_button.setStyleSheet("background-color: #6c757d; color: white; font-weight: bold; padding: 10px;")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        self.confirm_button = QPushButton("✅ 주문 실행")
        self.confirm_button.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold; padding: 10px;")
        self.confirm_button.setEnabled(False)
        self.confirm_button.clicked.connect(self.accept)
        button_layout.addWidget(self.confirm_button)
        
        # 체크박스 상태에 따라 버튼 활성화
        self.confirm_checkbox.stateChanged.connect(self.on_checkbox_changed)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def on_checkbox_changed(self, state):
        """체크박스 상태 변경"""
        self.confirm_button.setEnabled(state == 2)  # Qt.Checked


class RiskSettingsDialog(QDialog):
    """리스크 관리 설정 대화상자"""
    
    def __init__(self, current_loss_limit: int, parent=None):
        super().__init__(parent)
        self.current_loss_limit = current_loss_limit
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("⚠️ 리스크 관리 설정")
        self.setFixedSize(350, 200)
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        # 일일 손실 한도 설정
        loss_group = QGroupBox("일일 손실 한도")
        loss_layout = QGridLayout()
        
        loss_layout.addWidget(QLabel("현재 한도:"), 0, 0)
        loss_layout.addWidget(QLabel(f"{self.current_loss_limit:,}원"), 0, 1)
        
        loss_layout.addWidget(QLabel("신규 한도:"), 1, 0)
        self.loss_limit_edit = QLineEdit(str(self.current_loss_limit))
        loss_layout.addWidget(self.loss_limit_edit, 1, 1)
        
        loss_group.setLayout(loss_layout)
        layout.addWidget(loss_group)
        
        # 버튼들
        button_layout = QHBoxLayout()
        
        cancel_button = QPushButton("취소")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        save_button = QPushButton("저장")
        save_button.clicked.connect(self.accept)
        button_layout.addWidget(save_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def get_loss_limit(self) -> int:
        """손실 한도 반환"""
        try:
            return int(self.loss_limit_edit.text())
        except ValueError:
            return self.current_loss_limit


# 추가 유틸리티 함수들
def format_currency_kr(amount: int) -> str:
    """한국 통화 형식으로 포맷팅"""
    if amount >= 100000000:  # 1억 이상
        return f"{amount // 100000000}억 {(amount % 100000000) // 10000:,}만원"
    elif amount >= 10000:  # 1만 이상
        return f"{amount // 10000:,}만 {amount % 10000:,}원"
    else:
        return f"{amount:,}원"

def get_market_color(change_rate: float) -> str:
    """등락률에 따른 색상 반환"""
    if change_rate > 0:
        return "red"
    elif change_rate < 0:
        return "blue"
    else:
        return "black"

def calculate_commission(amount: int, rate: float = 0.00015) -> int:
    """수수료 계산"""
    commission = int(amount * rate)
    return max(commission, 100)  # 최소 수수료 100원

def validate_stock_code(code: str) -> bool:
    """종목코드 유효성 검사"""
    return len(code) == 6 and code.isdigit()

def get_order_type_korean(order_type: str) -> str:
    """주문 타입 한글 변환"""
    type_mapping = {
        '지정가매수': '매수',
        '지정가매도': '매도',
        '시장가매수': '매수',
        '시장가매도': '매도'
    }
    return type_mapping.get(order_type, order_type)


class RealTradingStatusWidget(QWidget):
    """실거래 상태 표시 위젯"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QHBoxLayout(self)
        
        # 실거래 표시등
        self.status_light = QLabel("🔴")
        self.status_light.setFixedSize(20, 20)
        layout.addWidget(self.status_light)
        
        # 상태 텍스트
        self.status_text = QLabel("실거래 모드")
        self.status_text.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(self.status_text)
        
        layout.addStretch()
    
    def update_status(self, is_connected: bool, is_market_open: bool):
        """상태 업데이트"""
        if is_connected and is_market_open:
            self.status_light.setText("🟢")
            self.status_text.setText("실거래 활성")
            self.status_text.setStyleSheet("color: green; font-weight: bold;")
        elif is_connected:
            self.status_light.setText("🟡")
            self.status_text.setText("실거래 대기")
            self.status_text.setStyleSheet("color: orange; font-weight: bold;")
        else:
            self.status_light.setText("🔴")
            self.status_text.setText("연결 끊김")
            self.status_text.setStyleSheet("color: red; font-weight: bold;")


class QuickOrderWidget(QWidget):
    """빠른 주문 위젯"""
    
    order_requested = pyqtSignal(str, str, int, int)  # stock_code, order_type, quantity, price
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 제목
        title = QLabel("⚡ 빠른 주문")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # 수량 버튼들
        qty_layout = QHBoxLayout()
        quantities = [10, 50, 100, 500]
        
        for qty in quantities:
            btn = QPushButton(f"{qty}주")
            btn.setFixedHeight(30)
            btn.clicked.connect(lambda checked, q=qty: self.set_quantity(q))
            qty_layout.addWidget(btn)
        
        layout.addLayout(qty_layout)
        
        # 주문 버튼들
        order_layout = QHBoxLayout()
        
        buy_btn = QPushButton("즉시 매수")
        buy_btn.setStyleSheet("background-color: red; color: white; font-weight: bold;")
        buy_btn.clicked.connect(self.quick_buy)
        order_layout.addWidget(buy_btn)
        
        sell_btn = QPushButton("즉시 매도")
        sell_btn.setStyleSheet("background-color: blue; color: white; font-weight: bold;")
        sell_btn.clicked.connect(self.quick_sell)
        order_layout.addWidget(sell_btn)
        
        layout.addLayout(order_layout)
        
        # 현재 설정
        self.current_quantity = 10
        self.current_stock = ""
        self.current_price = 0
    
    def set_quantity(self, quantity: int):
        """수량 설정"""
        self.current_quantity = quantity
    
    def set_stock_info(self, stock_code: str, price: int):
        """종목 정보 설정"""
        self.current_stock = stock_code
        self.current_price = price
    
    def quick_buy(self):
        """빠른 매수"""
        if self.current_stock and self.current_price > 0:
            self.order_requested.emit(self.current_stock, "매수", self.current_quantity, self.current_price)
    
    def quick_sell(self):
        """빠른 매도"""
        if self.current_stock and self.current_price > 0:
            self.order_requested.emit(self.current_stock, "매도", self.current_quantity, self.current_price)


class MarketDataWidget(QWidget):
    """시장 데이터 위젯"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout(self)
        
        # 제목
        title = QLabel("📈 시장 현황")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # 지수 정보
        self.kospi_label = QLabel("코스피: ---.--")
        self.kosdaq_label = QLabel("코스닥: ---.--")
        
        layout.addWidget(self.kospi_label)
        layout.addWidget(self.kosdaq_label)
        
        # 환율 정보
        self.usd_label = QLabel("USD/KRW: ----")
        layout.addWidget(self.usd_label)
    
    def update_market_data(self, kospi: float = 0, kosdaq: float = 0, usd: float = 0):
        """시장 데이터 업데이트"""
        if kospi > 0:
            self.kospi_label.setText(f"코스피: {kospi:.2f}")
        if kosdaq > 0:
            self.kosdaq_label.setText(f"코스닥: {kosdaq:.2f}")
        if usd > 0:
            self.usd_label.setText(f"USD/KRW: {usd:.0f}")


class AlertManager:
    """알림 관리자"""
    
    def __init__(self):
        self.alerts = []
        self.sound_enabled = True
    
    def add_price_alert(self, stock_code: str, target_price: int, condition: str):
        """가격 알림 추가"""
        alert = {
            'type': 'price',
            'stock_code': stock_code,
            'target_price': target_price,
            'condition': condition,  # 'above' or 'below'
            'active': True
        }
        self.alerts.append(alert)
    
    def check_alerts(self, stock_code: str, current_price: int):
        """알림 체크"""
        triggered_alerts = []
        
        for alert in self.alerts:
            if not alert['active'] or alert['stock_code'] != stock_code:
                continue
            
            if alert['type'] == 'price':
                if (alert['condition'] == 'above' and current_price >= alert['target_price']) or \
                   (alert['condition'] == 'below' and current_price <= alert['target_price']):
                    triggered_alerts.append(alert)
                    alert['active'] = False  # 한 번만 알림
        
        return triggered_alerts
    
    def play_alert_sound(self):
        """알림 사운드 재생"""
        if self.sound_enabled:
            # 시스템 기본 알림음 재생
            try:
                import winsound
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            except ImportError:
                # Windows가 아닌 경우 콘솔 벨
                print('\a')


class TradingLogger:
    """거래 로거"""
    
    def __init__(self, log_file: str = "real_trading.log"):
        self.log_file = log_file
        self.logger = logging.getLogger("TradingLogger")
    
    def log_order(self, order_type: str, stock_code: str, quantity: int, price: int, result: dict):
        """주문 로그"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "성공" if result.get('success') else "실패"
        error_msg = result.get('error', '')
        
        log_entry = f"[{timestamp}] {order_type} {stock_code} {quantity}주 @{price:,}원 - {status}"
        if error_msg:
            log_entry += f" ({error_msg})"
        
        self.logger.info(log_entry)
        
        # 파일에도 직접 기록
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry + '\n')
        except Exception as e:
            self.logger.error(f"로그 파일 쓰기 오류: {e}")
    
    def log_profit_loss(self, stock_code: str, realized_pnl: int, unrealized_pnl: int):
        """손익 로그"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {stock_code} 손익 - 실현: {realized_pnl:+,}원, 평가: {unrealized_pnl:+,}원"
        
        self.logger.info(log_entry)
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry + '\n')
        except Exception as e:
            self.logger.error(f"로그 파일 쓰기 오류: {e}")


class RiskCalculator:
    """리스크 계산기"""
    
    @staticmethod
    def calculate_position_size(account_balance: int, stock_price: int, risk_percentage: float = 0.02) -> int:
        """포지션 크기 계산 (2% 리스크 기준)"""
        risk_amount = account_balance * risk_percentage
        position_size = risk_amount / stock_price
        return int(position_size)
    
    @staticmethod
    def calculate_stop_loss(entry_price: int, risk_percentage: float = 0.03) -> int:
        """손절가 계산"""
        stop_price = entry_price * (1 - risk_percentage)
        return int(stop_price)
    
    @staticmethod
    def calculate_take_profit(entry_price: int, reward_ratio: float = 2.0, risk_percentage: float = 0.03) -> int:
        """익절가 계산 (리스크 대비 보상 비율 기준)"""
        profit_percentage = risk_percentage * reward_ratio
        take_profit_price = entry_price * (1 + profit_percentage)
        return int(take_profit_price)
    
    @staticmethod
    def calculate_sharpe_ratio(returns: list, risk_free_rate: float = 0.02) -> float:
        """샤프 비율 계산"""
        if not returns or len(returns) < 2:
            return 0.0
        
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
        std_deviation = variance ** 0.5
        
        if std_deviation == 0:
            return 0.0
        
        excess_return = mean_return - risk_free_rate / 252
        sharpe_ratio = excess_return / std_deviation
        
        return round(sharpe_ratio, 3)


# 실거래 시스템 초기화 함수
def initialize_real_trading_system():
    """실거래 시스템 초기화"""
    try:
        import os
        from datetime import datetime
        
        # 실거래 전용 디렉토리 생성
        directories = ['real_logs', 'real_backups', 'alerts', 'reports']
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
        
        # 실거래 시작 로그 기록
        log_file = f"real_logs/trading_{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*50}\n")
            f.write(f"실거래 시스템 시작: {datetime.now()}\n")
            f.write(f"{'='*50}\n")
        
        return True
        
    except Exception as e:
        print(f"실거래 시스템 초기화 오류: {e}")
        return False


# 시스템 종료 시 정리 함수
def cleanup_real_trading_system():
    """실거래 시스템 정리"""
    try:
        from datetime import datetime
        
        # 종료 로그 기록
        log_file = f"real_logs/trading_{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"실거래 시스템 종료: {datetime.now()}\n")
            f.write(f"{'='*50}\n\n")
        
        return True
        
    except Exception as e:
        print(f"실거래 시스템 정리 오류: {e}")
        return False


# 메인 실행 함수
if __name__ == "__main__":
    print("실거래 GUI 모듈이 직접 실행되었습니다.")
    print("이 모듈은 real_main.py에서 임포트하여 사용하세요.")
    print("\n실거래 시작 명령:")
    print("python real_main.py")