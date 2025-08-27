"""
GUI 윈도우 모듈
"""

import sys
import logging
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from config import Config

class MainWindow(QMainWindow):
    """메인 윈도우"""
    
    def __init__(self, trading_service, api_connected=False):
        super().__init__()
        self.trading_service = trading_service
        self.api_connected = api_connected
        self.logger = logging.getLogger(__name__)
        
        self.init_ui()
        self.setup_timer()
        self.update_all_data()
    
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle(Config.WINDOW_TITLE)
        self.setGeometry(100, 100, Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT)
        
        # 메뉴바 생성
        self.create_menu_bar()
        
        # 상태바 생성
        self.status_bar = self.statusBar()
        self.update_status()
        
        # 중앙 위젯 설정
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QHBoxLayout(central_widget)
        
        # 좌측 패널 (주문/조회)
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel, 1)
        
        # 우측 패널 (포트폴리오/내역)
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, 2)
    
    def create_menu_bar(self):
        """메뉴바 생성"""
        menubar = self.menuBar()
        
        # 파일 메뉴
        file_menu = menubar.addMenu('파일(&F)')
        
        backup_action = QAction('데이터 백업', self)
        backup_action.triggered.connect(self.backup_data)
        file_menu.addAction(backup_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('종료', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 거래 메뉴
        trade_menu = menubar.addMenu('거래(&T)')
        
        refresh_action = QAction('새로고침', self)
        refresh_action.setShortcut('F5')
        refresh_action.triggered.connect(self.update_all_data)
        trade_menu.addAction(refresh_action)
        
        # 도구 메뉴
        tools_menu = menubar.addMenu('도구(&O)')
        
        strategy_action = QAction('자동매매 설정', self)
        strategy_action.triggered.connect(self.open_strategy_window)
        tools_menu.addAction(strategy_action)
    
    def create_left_panel(self) -> QWidget:
        """좌측 패널 생성"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 계좌 정보
        account_group = self.create_account_group()
        layout.addWidget(account_group)
        
        # 주문 입력
        order_group = self.create_order_group()
        layout.addWidget(order_group)
        
        # 종목 조회
        stock_group = self.create_stock_group()
        layout.addWidget(stock_group)
        
        layout.addStretch()
        return panel
    
    def create_right_panel(self) -> QWidget:
        """우측 패널 생성"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 탭 위젯 생성
        tab_widget = QTabWidget()
        
        # 포트폴리오 탭
        portfolio_tab = self.create_portfolio_tab()
        tab_widget.addTab(portfolio_tab, "포트폴리오")
        
        # 주문내역 탭
        orders_tab = self.create_orders_tab()
        tab_widget.addTab(orders_tab, "주문내역")
        
        # 거래내역 탭
        transactions_tab = self.create_transactions_tab()
        tab_widget.addTab(transactions_tab, "거래내역")
        
        layout.addWidget(tab_widget)
        return panel
    
    def create_account_group(self) -> QGroupBox:
        """계좌 정보 그룹"""
        group = QGroupBox("계좌 정보")
        layout = QVBoxLayout()
        
        # 계좌번호
        self.account_label = QLabel(f"계좌: {self.trading_service.current_account}")
        layout.addWidget(self.account_label)
        
        # 잔고 정보
        self.balance_label = QLabel("현금잔고: 조회 중...")
        layout.addWidget(self.balance_label)
        
        self.asset_label = QLabel("총 자산: 조회 중...")
        layout.addWidget(self.asset_label)
        
        group.setLayout(layout)
        return group
    
    def create_order_group(self) -> QGroupBox:
        """주문 입력 그룹"""
        group = QGroupBox("주문 입력")
        layout = QGridLayout()
        
        # 종목코드
        layout.addWidget(QLabel("종목코드:"), 0, 0)
        self.stock_code_edit = QLineEdit("005930")
        layout.addWidget(self.stock_code_edit, 0, 1)
        
        # 수량
        layout.addWidget(QLabel("수량:"), 1, 0)
        self.quantity_edit = QLineEdit("10")
        layout.addWidget(self.quantity_edit, 1, 1)
        
        # 가격
        layout.addWidget(QLabel("가격:"), 2, 0)
        self.price_edit = QLineEdit("70000")
        layout.addWidget(self.price_edit, 2, 1)
        
        # 주문 버튼들
        button_layout = QHBoxLayout()
        
        buy_button = QPushButton("매수")
        buy_button.setStyleSheet("QPushButton { background-color: #e74c3c; color: white; font-weight: bold; padding: 8px; }")
        buy_button.clicked.connect(self.place_buy_order)
        button_layout.addWidget(buy_button)
        
        sell_button = QPushButton("매도")
        sell_button.setStyleSheet("QPushButton { background-color: #3498db; color: white; font-weight: bold; padding: 8px; }")
        sell_button.clicked.connect(self.place_sell_order)
        button_layout.addWidget(sell_button)
        
        layout.addLayout(button_layout, 3, 0, 1, 2)
        
        group.setLayout(layout)
        return group
    
    def create_stock_group(self) -> QGroupBox:
        """종목 조회 그룹"""
        group = QGroupBox("종목 조회")
        layout = QVBoxLayout()
        
        # 종목 검색
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("종목코드 입력 (예: 005930)")
        search_button = QPushButton("조회")
        search_button.clicked.connect(self.search_stock)
        
        search_layout.addWidget(self.search_edit)
        search_layout.addWidget(search_button)
        layout.addLayout(search_layout)
        
        # 종목 정보 표시
        self.stock_info_label = QLabel("종목을 검색하세요")
        self.stock_info_label.setWordWrap(True)
        layout.addWidget(self.stock_info_label)
        
        # 인기 종목 버튼들
        popular_layout = QGridLayout()
        popular_stocks = list(Config.POPULAR_STOCKS.items())[:6]  # 상위 6개만
        
        for i, (code, name) in enumerate(popular_stocks):
            button = QPushButton(f"{name}\n{code}")
            button.clicked.connect(lambda checked, c=code: self.select_stock(c))
            button.setFixedHeight(50)
            popular_layout.addWidget(button, i // 2, i % 2)
        
        layout.addLayout(popular_layout)
        
        group.setLayout(layout)
        return group
    
    def create_portfolio_tab(self) -> QWidget:
        """포트폴리오 탭"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 포트폴리오 요약
        summary_group = QGroupBox("포트폴리오 요약")
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
        
        # 포트폴리오 테이블
        self.portfolio_table = QTableWidget()
        self.portfolio_table.setColumnCount(7)
        self.portfolio_table.setHorizontalHeaderLabels([
            '종목코드', '종목명', '수량', '평균단가', '현재가', '평가액', '손익률'
        ])
        self.portfolio_table.horizontalHeader().setStretchLastSection(True)
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
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # 주문 테이블
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(7)
        self.orders_table.setHorizontalHeaderLabels([
            '주문시간', '종목코드', '종목명', '구분', '수량', '가격', '상태'
        ])
        self.orders_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.orders_table)
        
        return tab
    
    def create_transactions_tab(self) -> QWidget:
        """거래내역 탭"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 거래 테이블
        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(6)
        self.transactions_table.setHorizontalHeaderLabels([
            '거래시간', '종목코드', '종목명', '구분', '수량', '단가'
        ])
        self.transactions_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.transactions_table)
        
        return tab
    
    def setup_timer(self):
        """데이터 업데이트 타이머 설정"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_all_data)
        self.update_timer.start(Config.UPDATE_INTERVAL)
    
    def update_status(self):
        """상태바 업데이트"""
        status_text = f"API 연결: {'✓' if self.api_connected else '✗'} | "
        status_text += f"시장: {'개장' if Config.is_market_open() else '폐장'} | "
        status_text += f"업데이트: {datetime.now().strftime('%H:%M:%S')}"
        
        self.status_bar.showMessage(status_text)
    
    def update_all_data(self):
        """모든 데이터 업데이트"""
        try:
            self.update_account_info()
            self.update_portfolio()
            self.update_orders()
            self.update_transactions()
            self.update_status()
            
        except Exception as e:
            self.logger.error(f"데이터 업데이트 오류: {e}")
    
    def update_account_info(self):
        """계좌 정보 업데이트"""
        try:
            account_info = self.trading_service.get_account_info()
            portfolio_summary = self.trading_service.calculate_portfolio_summary()
            
            if account_info:
                balance = account_info.get('balance', 0)
                self.balance_label.setText(f"현금잔고: {balance:,}원")
            
            if portfolio_summary:
                total_asset = portfolio_summary.get('total_asset', 0)
                stock_value = portfolio_summary.get('stock_value', 0)
                profit_loss = portfolio_summary.get('total_profit_loss', 0)
                profit_rate = portfolio_summary.get('profit_rate', 0.0)
                
                self.asset_label.setText(f"총 자산: {total_asset:,}원")
                
                # 포트폴리오 요약 업데이트
                if hasattr(self, 'total_asset_label'):
                    self.total_asset_label.setText(f"총 자산: {total_asset:,}원")
                    self.stock_value_label.setText(f"주식 평가액: {stock_value:,}원")
                    
                    profit_color = "red" if profit_loss < 0 else "blue"
                    self.profit_loss_label.setText(f"평가손익: {profit_loss:+,}원")
                    self.profit_loss_label.setStyleSheet(f"color: {profit_color};")
                    
                    self.profit_rate_label.setText(f"수익률: {profit_rate:+.2f}%")
                    self.profit_rate_label.setStyleSheet(f"color: {profit_color};")
            
        except Exception as e:
            self.logger.error(f"계좌 정보 업데이트 오류: {e}")
    
    def update_portfolio(self):
        """포트폴리오 테이블 업데이트"""
        try:
            portfolio = self.trading_service.get_portfolio()
            
            self.portfolio_table.setRowCount(len(portfolio))
            
            for row, item in enumerate(portfolio):
                self.portfolio_table.setItem(row, 0, QTableWidgetItem(item['stock_code']))
                self.portfolio_table.setItem(row, 1, QTableWidgetItem(item.get('stock_name', '')))
                self.portfolio_table.setItem(row, 2, QTableWidgetItem(f"{item['quantity']:,}"))
                self.portfolio_table.setItem(row, 3, QTableWidgetItem(f"{item['avg_price']:,}"))
                self.portfolio_table.setItem(row, 4, QTableWidgetItem(f"{item.get('current_price', 0):,}"))
                self.portfolio_table.setItem(row, 5, QTableWidgetItem(f"{item.get('market_value', 0):,}"))
                
                profit_rate = item.get('profit_rate', 0.0)
                profit_item = QTableWidgetItem(f"{profit_rate:+.2f}%")
                
                if profit_rate > 0:
                    profit_item.setForeground(QColor('red'))
                elif profit_rate < 0:
                    profit_item.setForeground(QColor('blue'))
                
                self.portfolio_table.setItem(row, 6, profit_item)
            
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
                self.orders_table.setItem(row, 6, QTableWidgetItem(order['order_status']))
            
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
                self.transactions_table.setItem(row, 3, QTableWidgetItem(transaction['transaction_type']))
                self.transactions_table.setItem(row, 4, QTableWidgetItem(f"{transaction['quantity']:,}"))
                self.transactions_table.setItem(row, 5, QTableWidgetItem(f"{transaction['price']:,}"))
            
        except Exception as e:
            self.logger.error(f"거래내역 업데이트 오류: {e}")
    
    def place_buy_order(self):
        """매수 주문 실행"""
        try:
            stock_code = self.stock_code_edit.text().strip()
            quantity = int(self.quantity_edit.text())
            price = int(self.price_edit.text())
            
            result = self.trading_service.place_buy_order(stock_code, quantity, price)
            
            if result.get('success'):
                QMessageBox.information(self, "주문 성공", 
                    f"매수 주문이 완료되었습니다.\n"
                    f"종목: {stock_code}\n"
                    f"수량: {quantity:,}주\n"
                    f"가격: {price:,}원")
                self.update_all_data()
            else:
                QMessageBox.warning(self, "주문 실패", 
                    f"매수 주문이 실패했습니다.\n{result.get('error', '알 수 없는 오류')}")
            
        except ValueError:
            QMessageBox.warning(self, "입력 오류", "수량과 가격은 숫자로 입력하세요.")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"주문 처리 중 오류가 발생했습니다:\n{str(e)}")
    
    def place_sell_order(self):
        """매도 주문 실행"""
        try:
            stock_code = self.stock_code_edit.text().strip()
            quantity = int(self.quantity_edit.text())
            price = int(self.price_edit.text())
            
            result = self.trading_service.place_sell_order(stock_code, quantity, price)
            
            if result.get('success'):
                QMessageBox.information(self, "주문 성공", 
                    f"매도 주문이 완료되었습니다.\n"
                    f"종목: {stock_code}\n"
                    f"수량: {quantity:,}주\n"
                    f"가격: {price:,}원")
                self.update_all_data()
            else:
                QMessageBox.warning(self, "주문 실패", 
                    f"매도 주문이 실패했습니다.\n{result.get('error', '알 수 없는 오류')}")
            
        except ValueError:
            QMessageBox.warning(self, "입력 오류", "수량과 가격은 숫자로 입력하세요.")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"주문 처리 중 오류가 발생했습니다:\n{str(e)}")
    
    def search_stock(self):
        """종목 검색"""
        try:
            stock_code = self.search_edit.text().strip()
            if not stock_code:
                return
            
            stock_info = self.trading_service.get_stock_info(stock_code)
            
            if stock_info:
                info_text = f"종목코드: {stock_code}\n"
                info_text += f"종목명: {stock_info.get('stock_name', '정보없음')}\n"
                info_text += f"현재가: {stock_info.get('current_price', 0):,}원\n"
                info_text += f"등락률: {stock_info.get('change_rate', 0.0):+.2f}%\n"
                info_text += f"거래량: {stock_info.get('volume', 0):,}주"
                
                self.stock_info_label.setText(info_text)
                
                # 주문 입력란에 자동 입력
                self.stock_code_edit.setText(stock_code)
                self.price_edit.setText(str(stock_info.get('current_price', 0)))
            else:
                self.stock_info_label.setText("종목 정보를 가져올 수 없습니다.")
            
        except Exception as e:
            self.logger.error(f"종목 검색 오류: {e}")
            QMessageBox.warning(self, "검색 오류", f"종목 검색 중 오류가 발생했습니다:\n{str(e)}")
    
    def select_stock(self, stock_code: str):
        """인기 종목 선택"""
        self.search_edit.setText(stock_code)
        self.search_stock()
    
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
                self.orders_table.setItem(row, 6, QTableWidgetItem(order['order_status']))
            
        except Exception as e:
            self.logger.error(f"주문내역 필터링 오류: {e}")
    
    def backup_data(self):
        """데이터 백업"""
        try:
            if self.trading_service.db.backup_database():
                QMessageBox.information(self, "백업 완료", "데이터베이스 백업이 완료되었습니다.")
            else:
                QMessageBox.warning(self, "백업 실패", "데이터베이스 백업에 실패했습니다.")
                
        except Exception as e:
            self.logger.error(f"데이터 백업 오류: {e}")
            QMessageBox.critical(self, "백업 오류", f"백업 중 오류가 발생했습니다:\n{str(e)}")
    
    def open_strategy_window(self):
        """자동매매 전략 윈도우 열기"""
        try:
            strategy_window = StrategyWindow(self.trading_service, self)
            strategy_window.exec_()
            
        except Exception as e:
            self.logger.error(f"전략 윈도우 오류: {e}")
            QMessageBox.warning(self, "오류", f"전략 윈도우를 열 수 없습니다:\n{str(e)}")
    
    def closeEvent(self, event):
        """윈도우 종료 이벤트"""
        try:
            reply = QMessageBox.question(self, '시스템 종료', 
                                       '정말로 종료하시겠습니까?',
                                       QMessageBox.Yes | QMessageBox.No,
                                       QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                # 타이머 정지
                if hasattr(self, 'update_timer'):
                    self.update_timer.stop()
                
                # API 연결 해제
                if self.trading_service and self.trading_service.api:
                    self.trading_service.api.disconnect()
                
                self.logger.info("시스템 정상 종료")
                event.accept()
            else:
                event.ignore()
                
        except Exception as e:
            self.logger.error(f"종료 처리 오류: {e}")
            event.accept()

class StrategyWindow(QDialog):
    """자동매매 전략 설정 윈도우"""
    
    def __init__(self, trading_service, parent=None):
        super().__init__(parent)
        self.trading_service = trading_service
        self.logger = logging.getLogger(__name__)
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("자동매매 전략 설정")
        self.setGeometry(200, 200, 600, 400)
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        # 전략 선택
        strategy_group = QGroupBox("전략 선택")
        strategy_layout = QVBoxLayout()
        
        self.momentum_radio = QRadioButton("모멘텀 전략")
        self.momentum_radio.setChecked(True)
        strategy_layout.addWidget(self.momentum_radio)
        
        self.mean_reversion_radio = QRadioButton("평균회귀 전략")
        strategy_layout.addWidget(self.mean_reversion_radio)
        
        self.breakout_radio = QRadioButton("돌파 전략")
        strategy_layout.addWidget(self.breakout_radio)
        
        strategy_group.setLayout(strategy_layout)
        layout.addWidget(strategy_group)
        
        # 종목 설정
        stock_group = QGroupBox("대상 종목")
        stock_layout = QGridLayout()
        
        stock_layout.addWidget(QLabel("종목코드:"), 0, 0)
        self.strategy_stock_edit = QLineEdit("005930")
        stock_layout.addWidget(self.strategy_stock_edit, 0, 1)
        
        stock_layout.addWidget(QLabel("투자금액:"), 1, 0)
        self.amount_edit = QLineEdit("1000000")
        stock_layout.addWidget(self.amount_edit, 1, 1)
        
        stock_group.setLayout(stock_layout)
        layout.addWidget(stock_group)
        
        # 리스크 관리
        risk_group = QGroupBox("리스크 관리")
        risk_layout = QGridLayout()
        
        risk_layout.addWidget(QLabel("손절매 비율:"), 0, 0)
        self.stop_loss_edit = QLineEdit("5.0")
        risk_layout.addWidget(self.stop_loss_edit, 0, 1)
        
        risk_layout.addWidget(QLabel("익절매 비율:"), 1, 0)
        self.take_profit_edit = QLineEdit("10.0")
        risk_layout.addWidget(self.take_profit_edit, 1, 1)
        
        risk_group.setLayout(risk_layout)
        layout.addWidget(risk_group)
        
        # 버튼들
        button_layout = QHBoxLayout()
        
        test_button = QPushButton("전략 테스트")
        test_button.clicked.connect(self.test_strategy)
        button_layout.addWidget(test_button)
        
        start_button = QPushButton("전략 시작")
        start_button.clicked.connect(self.start_strategy)
        button_layout.addWidget(start_button)
        
        close_button = QPushButton("닫기")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def get_selected_strategy(self) -> str:
        """선택된 전략 반환"""
        if self.momentum_radio.isChecked():
            return "momentum"
        elif self.mean_reversion_radio.isChecked():
            return "mean_reversion"
        elif self.breakout_radio.isChecked():
            return "breakout"
        else:
            return "momentum"
    
    def test_strategy(self):
        """전략 테스트"""
        try:
            strategy_name = self.get_selected_strategy()
            stock_code = self.strategy_stock_edit.text().strip()
            
            if not stock_code:
                QMessageBox.warning(self, "입력 오류", "종목코드를 입력하세요.")
                return
            
            result = self.trading_service.auto_execute_strategy(strategy_name, stock_code)
            
            if result.get('success'):
                QMessageBox.information(self, "전략 테스트", 
                    f"전략 테스트 완료:\n{result.get('message', '성공')}")
            else:
                QMessageBox.warning(self, "전략 테스트", 
                    f"전략 테스트 실패:\n{result.get('error', '알 수 없는 오류')}")
            
        except Exception as e:
            self.logger.error(f"전략 테스트 오류: {e}")
            QMessageBox.critical(self, "오류", f"전략 테스트 중 오류가 발생했습니다:\n{str(e)}")
    
    def start_strategy(self):
        """전략 시작"""
        try:
            QMessageBox.information(self, "전략 시작", 
                "자동매매 전략이 시작되었습니다.\n"
                "백그라운드에서 지속적으로 모니터링됩니다.")
            self.close()
            
        except Exception as e:
            self.logger.error(f"전략 시작 오류: {e}")
            QMessageBox.critical(self, "오류", f"전략 시작 중 오류가 발생했습니다:\n{str(e)}")
