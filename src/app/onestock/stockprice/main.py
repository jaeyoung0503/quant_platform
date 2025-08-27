#file name: onestock/main.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 폰트 에러 해결
import matplotlib
matplotlib.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

# 전략 모듈 import (같은 폴더에 trading_strategies.py가 있어야 함)
try:
    from trading_strategies import TradingStrategies
except ImportError:
    print("trading_strategies.py 파일이 필요합니다. 같은 폴더에 있는지 확인하세요.")
    
    # trading_strategies.py가 없으면 여기서 직접 정의
    class TradingStrategies:
        """매매전략 클래스"""
        
        def __init__(self, data):
            self.data = data
        
        def calculate_technical_indicators(self):
            """기술적 지표 계산"""
            if self.data is None:
                return
            
            # 이동평균선
            self.data['MA5'] = self.data['Close'].rolling(window=5).mean()
            self.data['MA20'] = self.data['Close'].rolling(window=20).mean()
            self.data['MA60'] = self.data['Close'].rolling(window=60).mean()
            
            # 볼린저 밴드
            self.data['BB_middle'] = self.data['Close'].rolling(window=20).mean()
            bb_std = self.data['Close'].rolling(window=20).std()
            self.data['BB_upper'] = self.data['BB_middle'] + (bb_std * 2)
            self.data['BB_lower'] = self.data['BB_middle'] - (bb_std * 2)
            
            # RSI
            delta = self.data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            self.data['RSI'] = 100 - (100 / (1 + rs))
            
            # MACD
            exp1 = self.data['Close'].ewm(span=12).mean()
            exp2 = self.data['Close'].ewm(span=26).mean()
            self.data['MACD'] = exp1 - exp2
            self.data['MACD_signal'] = self.data['MACD'].ewm(span=9).mean()
            self.data['MACD_histogram'] = self.data['MACD'] - self.data['MACD_signal']
            
            # 스토캐스틱
            high14 = self.data['High'].rolling(window=14).max()
            low14 = self.data['Low'].rolling(window=14).min()
            self.data['Stoch_K'] = ((self.data['Close'] - low14) / (high14 - low14)) * 100
            self.data['Stoch_D'] = self.data['Stoch_K'].rolling(window=3).mean()
        
        def get_strategy_signals(self, strategy_name):
            """전략별 신호 반환"""
            signals = {'Buy_Signal': [0] * len(self.data), 'Sell_Signal': [0] * len(self.data)}
            
            if strategy_name == 'golden_cross':
                for i in range(1, len(self.data)):
                    if (not pd.isna(self.data['MA5'].iloc[i]) and not pd.isna(self.data['MA20'].iloc[i])):
                        if (self.data['MA5'].iloc[i] > self.data['MA20'].iloc[i] and 
                            self.data['MA5'].iloc[i-1] <= self.data['MA20'].iloc[i-1]):
                            signals['Buy_Signal'][i] = 1
                        elif (self.data['MA5'].iloc[i] < self.data['MA20'].iloc[i] and 
                              self.data['MA5'].iloc[i-1] >= self.data['MA20'].iloc[i-1]):
                            signals['Sell_Signal'][i] = 1
            
            elif strategy_name == 'rsi_divergence':
                for i in range(1, len(self.data)):
                    if not pd.isna(self.data['RSI'].iloc[i]):
                        if (self.data['RSI'].iloc[i] > 30 and self.data['RSI'].iloc[i-1] <= 30):
                            signals['Buy_Signal'][i] = 1
                        elif (self.data['RSI'].iloc[i] < 70 and self.data['RSI'].iloc[i-1] >= 70):
                            signals['Sell_Signal'][i] = 1
            
            elif strategy_name == 'bollinger_bands':
                for i in range(1, len(self.data)):
                    if (not pd.isna(self.data['BB_lower'].iloc[i]) and not pd.isna(self.data['Close'].iloc[i])):
                        if (self.data['Close'].iloc[i] > self.data['BB_lower'].iloc[i] and 
                            self.data['Close'].iloc[i-1] <= self.data['BB_lower'].iloc[i-1]):
                            signals['Buy_Signal'][i] = 1
                        elif (self.data['Close'].iloc[i] < self.data['BB_upper'].iloc[i] and 
                              self.data['Close'].iloc[i-1] >= self.data['BB_upper'].iloc[i-1]):
                            signals['Sell_Signal'][i] = 1
            
            elif strategy_name == 'macd_crossover':
                for i in range(1, len(self.data)):
                    if (not pd.isna(self.data['MACD'].iloc[i]) and not pd.isna(self.data['MACD_signal'].iloc[i])):
                        if (self.data['MACD'].iloc[i] > self.data['MACD_signal'].iloc[i] and 
                            self.data['MACD'].iloc[i-1] <= self.data['MACD_signal'].iloc[i-1]):
                            signals['Buy_Signal'][i] = 1
                        elif (self.data['MACD'].iloc[i] < self.data['MACD_signal'].iloc[i] and 
                              self.data['MACD'].iloc[i-1] >= self.data['MACD_signal'].iloc[i-1]):
                            signals['Sell_Signal'][i] = 1
            
            return signals

class MockDataGenerator:
    """Mock Stock Data Generator"""
    
    @staticmethod
    def generate_stock_data(symbol, days=252, initial_price=100000, volatility=0.02):
        """Generate stock data using Geometric Brownian Motion"""
        np.random.seed(42)  # For reproducible results
        
        # Generate dates
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days+100)  # Add buffer for weekends
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        dates = dates[dates.weekday < 5][:days]  # Exclude weekends, limit to requested days
        
        # Generate stock prices (Geometric Brownian Motion)
        returns = np.random.normal(0.0005, volatility, len(dates))  # Daily returns
        prices = [initial_price]
        
        for i in range(1, len(dates)):
            price = prices[-1] * (1 + returns[i])
            prices.append(max(price, initial_price * 0.3))  # Minimum price limit
        
        # Generate OHLCV data
        data = []
        for i, (date, close) in enumerate(zip(dates, prices)):
            # Generate High, Low, Open
            daily_volatility = abs(np.random.normal(0, volatility/2))
            high = close * (1 + daily_volatility)
            low = close * (1 - daily_volatility)
            
            if i == 0:
                open_price = close
            else:
                open_price = prices[i-1] * (1 + np.random.normal(0, volatility/3))
            
            # Generate Volume (inversely related to price change)
            price_change = abs((close - prices[i-1]) / prices[i-1]) if i > 0 else 0
            base_volume = 1000000
            volume = int(base_volume * (1 + price_change * 5) * np.random.uniform(0.5, 2.0))
            
            data.append({
                'Date': date,
                'Open': open_price,
                'High': max(open_price, high, close),
                'Low': min(open_price, low, close),
                'Close': close,
                'Volume': volume
            })
        
        df = pd.DataFrame(data)
        df.set_index('Date', inplace=True)
        return df

class StockAnalyzer:
    def __init__(self):
        self.data = None
        self.symbol = None
        self.selected_strategies = []
        self.all_signals = {}
        
    def load_mock_data(self, symbol, days=252):
        """Generate and load mock data"""
        try:
            self.symbol = symbol
            
            # Stock-specific configurations
            stock_configs = {
                'AAPL': {'initial_price': 180, 'volatility': 0.025},
                'GOOGL': {'initial_price': 130, 'volatility': 0.022},
                'TSLA': {'initial_price': 250, 'volatility': 0.045},
                'MSFT': {'initial_price': 350, 'volatility': 0.020},
                'NVDA': {'initial_price': 500, 'volatility': 0.035},
                'AMZN': {'initial_price': 150, 'volatility': 0.025},
                'SAMSUNG': {'initial_price': 75000, 'volatility': 0.018},
                'SK_HYNIX': {'initial_price': 130000, 'volatility': 0.030},
                'NAVER': {'initial_price': 200000, 'volatility': 0.025},
                'KAKAO': {'initial_price': 55000, 'volatility': 0.035},
            }
            
            config = stock_configs.get(symbol, {'initial_price': 100000, 'volatility': 0.025})
            self.data = MockDataGenerator.generate_stock_data(
                symbol, days, config['initial_price'], config['volatility']
            )
            
            print(f"\n✅ {symbol} Mock data generated successfully.")
            print(f"📅 Data period: {self.data.index[0].strftime('%Y-%m-%d')} ~ {self.data.index[-1].strftime('%Y-%m-%d')}")
            print(f"📊 Total {len(self.data)} trading days")
            return True
        except Exception as e:
            print(f"❌ Data generation failed: {e}")
            return False
    
    def plot_basic_chart(self):
        """Plot basic stock chart immediately after data loading"""
        if self.data is None:
            return
        
        # Calculate basic indicators
        strategy_calc = TradingStrategies(self.data)
        strategy_calc.calculate_technical_indicators()
        self.data = strategy_calc.data
        
        fig = plt.figure(figsize=(16, 10))
        
        # 1. Price Chart + Moving Averages (Top)
        ax1 = plt.subplot(2, 2, (1, 2))
        ax1.plot(self.data.index, self.data['Close'], label='Close', linewidth=2, color='black')
        ax1.plot(self.data.index, self.data['MA5'], label='MA5', alpha=0.7, color='red', linewidth=1)
        ax1.plot(self.data.index, self.data['MA20'], label='MA20', alpha=0.7, color='blue', linewidth=1)
        ax1.plot(self.data.index, self.data['MA60'], label='MA60', alpha=0.7, color='green', linewidth=1)
        
        ax1.set_title(f'{self.symbol} Price & Moving Averages', fontsize=12, fontweight='bold')
        ax1.legend(fontsize=9, loc='upper left')
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', labelsize=8)
        ax1.tick_params(axis='y', labelsize=8)
        
        # Rotate x-axis labels to prevent overlap
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        
        # 2. Bollinger Bands
        ax2 = plt.subplot(2, 2, 3)
        ax2.plot(self.data.index, self.data['Close'], label='Close', color='black', linewidth=1.5)
        ax2.plot(self.data.index, self.data['BB_upper'], label='Upper Band', alpha=0.7, color='red', linewidth=1)
        ax2.plot(self.data.index, self.data['BB_middle'], label='Middle', alpha=0.7, color='orange', linewidth=1)
        ax2.plot(self.data.index, self.data['BB_lower'], label='Lower Band', alpha=0.7, color='green', linewidth=1)
        ax2.fill_between(self.data.index, self.data['BB_upper'], self.data['BB_lower'], alpha=0.1, color='gray')
        
        ax2.set_title('Bollinger Bands', fontsize=12)
        ax2.legend(fontsize=8, loc='upper left')
        ax2.grid(True, alpha=0.3)
        ax2.tick_params(axis='x', labelsize=8)
        ax2.tick_params(axis='y', labelsize=8)
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        
        # 3. RSI
        ax3 = plt.subplot(2, 2, 4)
        ax3.plot(self.data.index, self.data['RSI'], label='RSI', color='purple', linewidth=1.5)
        ax3.axhline(y=70, color='r', linestyle='--', alpha=0.7, label='Overbought(70)', linewidth=1)
        ax3.axhline(y=30, color='g', linestyle='--', alpha=0.7, label='Oversold(30)', linewidth=1)
        ax3.fill_between(self.data.index, 70, 100, alpha=0.1, color='red')
        ax3.fill_between(self.data.index, 0, 30, alpha=0.1, color='green')
        
        ax3.set_title('RSI Indicator', fontsize=12)
        ax3.set_ylim(0, 100)
        ax3.legend(fontsize=8, loc='upper left')
        ax3.grid(True, alpha=0.3)
        ax3.tick_params(axis='x', labelsize=8)
        ax3.tick_params(axis='y', labelsize=8)
        plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout(pad=2.0)
        plt.show()
    
    def select_strategies(self):
        """Allow user to select multiple strategies"""
        print(f"\n{'='*60}")
        print("📈 SELECT TECHNICAL ANALYSIS STRATEGIES (Multiple Selection)")
        print(f"{'='*60}")
        print("Available Strategies:")
        print("1. Golden Cross/Dead Cross (MA5 vs MA20)")
        print("2. RSI Divergence (Overbought/Oversold)")
        print("3. Bollinger Bands (Band Touch Strategy)")
        print("4. MACD Crossover (Signal Line Cross)")
        
        while True:
            selection = input("\nEnter strategy numbers (e.g., 1,2,3 or 1 2 3): ").strip()
            
            if not selection:
                print("❌ Please enter at least one strategy number.")
                continue
            
            # Parse selection (handle both comma and space separated)
            try:
                if ',' in selection:
                    strategy_nums = [int(x.strip()) for x in selection.split(',')]
                else:
                    strategy_nums = [int(x.strip()) for x in selection.split()]
                
                # Validate numbers
                valid_nums = [n for n in strategy_nums if 1 <= n <= 4]
                if not valid_nums:
                    print("❌ Please enter valid strategy numbers (1-4).")
                    continue
                
                # Convert to strategy names
                strategy_map = {
                    1: 'golden_cross',
                    2: 'rsi_divergence', 
                    3: 'bollinger_bands',
                    4: 'macd_crossover'
                }
                
                strategy_names_map = {
                    1: 'Golden Cross/Dead Cross',
                    2: 'RSI Divergence',
                    3: 'Bollinger Bands',
                    4: 'MACD Crossover'
                }
                
                self.selected_strategies = [strategy_map[n] for n in valid_nums]
                
                print(f"\n✅ Selected strategies:")
                for num in valid_nums:
                    print(f"   • {strategy_names_map[num]}")
                
                return True
                
            except ValueError:
                print("❌ Invalid input. Please enter numbers only (e.g., 1,2,3).")
                continue
    
    def analyze_strategies(self):
        """Analyze selected strategies and show signals"""
        if not self.selected_strategies or self.data is None:
            return
        
        strategy_calc = TradingStrategies(self.data)
        strategy_calc.calculate_technical_indicators()
        self.data = strategy_calc.data
        
        strategy_names = {
            'golden_cross': 'Golden Cross/Dead Cross',
            'rsi_divergence': 'RSI Divergence',
            'bollinger_bands': 'Bollinger Bands',
            'macd_crossover': 'MACD Crossover'
        }
        
        print(f"\n{'='*80}")
        print(f"🔍 TECHNICAL ANALYSIS RESULTS FOR {self.symbol}")
        print(f"{'='*80}")
        
        for strategy in self.selected_strategies:
            signals = strategy_calc.get_strategy_signals(strategy)
            self.all_signals[strategy] = signals
            
            # Collect all signals with dates
            all_signals = []
            
            for i, (buy, sell) in enumerate(zip(signals['Buy_Signal'], signals['Sell_Signal'])):
                if buy == 1:
                    all_signals.append({
                        'Date': self.data.index[i],
                        'Price': self.data['Close'].iloc[i],
                        'MA5': self.data['MA5'].iloc[i] if 'MA5' in self.data.columns else None,
                        'MA20': self.data['MA20'].iloc[i] if 'MA20' in self.data.columns else None,
                        'RSI': self.data['RSI'].iloc[i] if 'RSI' in self.data.columns else None,
                        'Signal_Type': 'BUY'
                    })
                elif sell == 1:
                    all_signals.append({
                        'Date': self.data.index[i],
                        'Price': self.data['Close'].iloc[i],
                        'MA5': self.data['MA5'].iloc[i] if 'MA5' in self.data.columns else None,
                        'MA20': self.data['MA20'].iloc[i] if 'MA20' in self.data.columns else None,
                        'RSI': self.data['RSI'].iloc[i] if 'RSI' in self.data.columns else None,
                        'Signal_Type': 'SELL'
                    })
            
            # Sort by date
            all_signals.sort(key=lambda x: x['Date'])
            
            # Display strategy results
            print(f"\n📊 {strategy_names[strategy]} Strategy Results:")
            print("-" * 80)
            
            if all_signals:
                # Create DataFrame for better formatting
                signal_data = []
                for signal in all_signals:
                    ma5_str = f"{signal['MA5']:.2f}" if signal['MA5'] is not None and not pd.isna(signal['MA5']) else "N/A"
                    ma20_str = f"{signal['MA20']:.2f}" if signal['MA20'] is not None and not pd.isna(signal['MA20']) else "N/A"
                    rsi_str = f"{signal['RSI']:.1f}" if signal['RSI'] is not None and not pd.isna(signal['RSI']) else "N/A"
                    
                    signal_data.append({
                        'Date': signal['Date'].strftime('%Y-%m-%d'),
                        'Price': f"${signal['Price']:.2f}",
                        'MA5': ma5_str,
                        'MA20': ma20_str,
                        'RSI': rsi_str,
                        'Signal': signal['Signal_Type']
                    })
                
                # Convert to DataFrame and display
                df = pd.DataFrame(signal_data)
                
                print(f"📋 Trading Signals Table (Total: {len(all_signals)} signals)")
                print("=" * 80)
                
                # Custom table formatting
                print(f"{'Date':<12} {'Price':<12} {'MA5':<10} {'MA20':<10} {'RSI':<8} {'Signal':<6}")
                print("-" * 80)
                
                for _, row in df.iterrows():
                    signal_icon = "🟢 BUY " if row['Signal'] == 'BUY' else "🔴 SELL"
                    print(f"{row['Date']:<12} {row['Price']:<12} {row['MA5']:<10} {row['MA20']:<10} {row['RSI']:<8} {signal_icon}")
                
                # Summary statistics
                buy_count = len([s for s in all_signals if s['Signal_Type'] == 'BUY'])
                sell_count = len([s for s in all_signals if s['Signal_Type'] == 'SELL'])
                
                print("-" * 80)
                print(f"📊 Summary: 🟢 {buy_count} BUY signals | 🔴 {sell_count} SELL signals")
                
            else:
                print("❌ No trading signals found for this strategy")
            
            print()
    
    def run_backtests(self):
        """Run backtests for all selected strategies"""
        if not self.selected_strategies or self.data is None:
            return
        
        print(f"\n{'='*80}")
        print(f"📈 BACKTESTING RESULTS FOR {self.symbol}")
        print(f"{'='*80}")
        
        initial_capital = 10000000  # Default $10M
        
        strategy_names = {
            'golden_cross': 'Golden Cross/Dead Cross',
            'rsi_divergence': 'RSI Divergence',
            'bollinger_bands': 'Bollinger Bands',
            'macd_crossover': 'MACD Crossover'
        }
        
        # Calculate Buy & Hold performance for comparison
        buy_hold_return = ((self.data['Close'].iloc[-1] - self.data['Close'].iloc[0]) 
                          / self.data['Close'].iloc[0] * 100)
        
        backtest_results = {}
        
        for strategy in self.selected_strategies:
            print(f"\n🔍 {strategy_names[strategy]} Strategy Backtest:")
            print("-" * 50)
            
            signals = self.all_signals[strategy]
            
            # Simulate trading
            capital = initial_capital
            position = 0
            trades = []
            portfolio_values = []
            max_portfolio_value = initial_capital
            max_drawdown = 0
            
            for i, (date, row) in enumerate(self.data.iterrows()):
                current_price = row['Close']
                
                if signals['Buy_Signal'][i] == 1 and position == 0:
                    # Buy
                    position = capital / current_price
                    capital = 0
                    trades.append({
                        'Date': date,
                        'Action': 'BUY',
                        'Price': current_price,
                        'Shares': position,
                        'Value': position * current_price
                    })
                
                elif signals['Sell_Signal'][i] == 1 and position > 0:
                    # Sell
                    capital = position * current_price
                    trades.append({
                        'Date': date,
                        'Action': 'SELL',
                        'Price': current_price,
                        'Shares': position,
                        'Value': capital
                    })
                    position = 0
                
                # Calculate portfolio value
                current_value = position * current_price if position > 0 else capital
                portfolio_values.append(current_value)
                
                # Update max drawdown
                if current_value > max_portfolio_value:
                    max_portfolio_value = current_value
                
                drawdown = (max_portfolio_value - current_value) / max_portfolio_value * 100
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            # Close final position
            if position > 0:
                final_price = self.data['Close'].iloc[-1]
                capital = position * final_price
                trades.append({
                    'Date': self.data.index[-1],
                    'Action': 'SELL',
                    'Price': final_price,
                    'Shares': position,
                    'Value': capital
                })
            
            final_value = capital if capital > 0 else portfolio_values[-1]
            total_return = (final_value - initial_capital) / initial_capital * 100
            
            # Calculate win rate
            buy_trades = [t for t in trades if t['Action'] == 'BUY']
            sell_trades = [t for t in trades if t['Action'] == 'SELL']
            profitable_trades = 0
            
            for i in range(min(len(buy_trades), len(sell_trades))):
                if sell_trades[i]['Value'] > buy_trades[i]['Value']:
                    profitable_trades += 1
            
            win_rate = (profitable_trades / min(len(buy_trades), len(sell_trades))) * 100 if min(len(buy_trades), len(sell_trades)) > 0 else 0
            
            # Annual return
            days = (self.data.index[-1] - self.data.index[0]).days
            annual_return = (((final_value / initial_capital) ** (365/days)) - 1) * 100 if days > 0 else 0
            
            # Store results
            backtest_results[strategy] = {
                'total_return': total_return,
                'annual_return': annual_return,
                'max_drawdown': max_drawdown,
                'win_rate': win_rate,
                'total_trades': len(trades),
                'final_value': final_value
            }
            
            # Print results
            print(f"💰 Initial Capital: ${initial_capital:,.0f}")
            print(f"💰 Final Capital: ${final_value:,.0f}")
            print(f"📊 Total Return: {total_return:.2f}%")
            print(f"📊 Annual Return: {annual_return:.2f}%")
            print(f"📉 Max Drawdown: {max_drawdown:.2f}%")
            print(f"🎯 Win Rate: {win_rate:.1f}%")
            print(f"🔄 Total Trades: {len(trades)}")
            print(f"⚡ vs Buy & Hold: {total_return - buy_hold_return:+.2f}%")
            
            # Performance rating
            score = 0
            if total_return > buy_hold_return: score += 2
            if max_drawdown < 20: score += 1
            if win_rate > 50: score += 1
            if total_return > 0: score += 1
            
            ratings = {5: "🌟 Excellent", 4: "✅ Good", 3: "📊 Average", 2: "⚠️ Below Average", 1: "❌ Poor", 0: "💀 Very Poor"}
            print(f"🏆 Performance Rating: {ratings.get(score, '❌ Poor')} ({score}/5)")
        
        # Summary comparison
        if len(self.selected_strategies) > 1:
            print(f"\n{'='*60}")
            print("📊 STRATEGY COMPARISON SUMMARY")
            print(f"{'='*60}")
            print(f"Buy & Hold Return: {buy_hold_return:.2f}%")
            print("-" * 60)
            
            for strategy in self.selected_strategies:
                result = backtest_results[strategy]
                status = "🚀" if result['total_return'] > buy_hold_return else "📉"
                print(f"{status} {strategy_names[strategy]}: {result['total_return']:.2f}% "
                      f"(Trades: {result['total_trades']}, Win Rate: {result['win_rate']:.1f}%)")

def main():
    """Main function"""
    analyzer = StockAnalyzer()
    
    print("=" * 80)
    print("🚀 AUTOMATED STOCK TECHNICAL ANALYSIS & BACKTESTING SYSTEM")
    print("=" * 80)
    print("📋 Available Stocks:")
    print("   • US Stocks: AAPL, GOOGL, MSFT, TSLA, NVDA, AMZN")
    print("   • Korean Stocks: SAMSUNG, SK_HYNIX, NAVER, KAKAO")
    
    while True:
        # Step 1: Stock input
        symbol = input(f"\n📈 Enter stock symbol to analyze (q to quit): ").strip().upper()
        if symbol == 'Q':
            print("👋 Thank you for using the analysis system!")
            break
        
        # Step 2: Period selection
        print(f"\n📅 Select Analysis Period:")
        print("1. 3 months (63 days)")
        print("2. 6 months (126 days)")
        print("3. 1 year (252 days)")
        print("4. 3 years (756 days)")
        print("5. 5 years (1260 days)")
        print("6. 10 years (2520 days)")
        
        period_choice = input("Select period (1-6): ")
        period_map = {'1': 63, '2': 126, '3': 252, '4': 756, '5': 1260, '6': 2520}
        days = period_map.get(period_choice, 252)
        
        # Step 3: Load data and show basic chart
        if not analyzer.load_mock_data(symbol, days):
            continue
        
        print(f"\n📊 Displaying basic chart for {symbol}...")
        analyzer.plot_basic_chart()
        
        # Step 4: Strategy selection
        if not analyzer.select_strategies():
            continue
        
        # Step 5: Analyze strategies and show signals
        print(f"\n🔄 Analyzing selected strategies...")
        analyzer.analyze_strategies()
        
        # Step 6: Run backtests
        print(f"\n🔄 Running backtests...")
        analyzer.run_backtests()
        
        # Ask if user wants to analyze another stock
        print(f"\n{'='*60}")
        continue_choice = input("🔄 Analyze another stock? (y/n): ").strip().lower()
        if continue_choice != 'y':
            print("👋 Thank you for using the analysis system!")
            break

if __name__ == "__main__":
    main()