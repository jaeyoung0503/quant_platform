# file name: onestock/trading_strategies.py

import pandas as pd
import numpy as np

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
        
        # 거래량 가중 평균가격 (VWAP)
        self.data['VWAP'] = (self.data['Close'] * self.data['Volume']).rolling(window=20).sum() / self.data['Volume'].rolling(window=20).sum()
        
        # Williams %R
        self.data['Williams_R'] = ((high14 - self.data['Close']) / (high14 - low14)) * -100
        
        # ATR (Average True Range)
        high_low = self.data['High'] - self.data['Low']
        high_close = np.abs(self.data['High'] - self.data['Close'].shift())
        low_close = np.abs(self.data['Low'] - self.data['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        self.data['ATR'] = true_range.rolling(window=14).mean()
    
    def golden_cross_strategy(self):
        """골든크로스/데드크로스 전략"""
        signals = {'Buy_Signal': [], 'Sell_Signal': [], 'dates': self.data.index}
        
        for i in range(1, len(self.data)):
            buy_signal = 0
            sell_signal = 0
            
            if (not pd.isna(self.data['MA5'].iloc[i]) and not pd.isna(self.data['MA20'].iloc[i]) and
                not pd.isna(self.data['MA5'].iloc[i-1]) and not pd.isna(self.data['MA20'].iloc[i-1])):
                
                # 골든크로스: MA5가 MA20을 상향돌파
                if (self.data['MA5'].iloc[i] > self.data['MA20'].iloc[i] and 
                    self.data['MA5'].iloc[i-1] <= self.data['MA20'].iloc[i-1]):
                    buy_signal = 1
                
                # 데드크로스: MA5가 MA20을 하향돌파
                elif (self.data['MA5'].iloc[i] < self.data['MA20'].iloc[i] and 
                      self.data['MA5'].iloc[i-1] >= self.data['MA20'].iloc[i-1]):
                    sell_signal = 1
            
            signals['Buy_Signal'].append(buy_signal)
            signals['Sell_Signal'].append(sell_signal)
        
        # 첫 번째 값 추가 (비교할 이전 값이 없으므로 0)
        signals['Buy_Signal'].insert(0, 0)
        signals['Sell_Signal'].insert(0, 0)
        
        return signals
    
    def rsi_strategy(self):
        """RSI 전략"""
        signals = {'Buy_Signal': [], 'Sell_Signal': [], 'dates': self.data.index}
        
        for i in range(1, len(self.data)):
            buy_signal = 0
            sell_signal = 0
            
            if (not pd.isna(self.data['RSI'].iloc[i]) and not pd.isna(self.data['RSI'].iloc[i-1])):
                # RSI < 30에서 상승 시 매수
                if (self.data['RSI'].iloc[i] > 30 and 
                    self.data['RSI'].iloc[i-1] <= 30):
                    buy_signal = 1
                
                # RSI > 70에서 하락 시 매도
                elif (self.data['RSI'].iloc[i] < 70 and 
                      self.data['RSI'].iloc[i-1] >= 70):
                    sell_signal = 1
            
            signals['Buy_Signal'].append(buy_signal)
            signals['Sell_Signal'].append(sell_signal)
        
        signals['Buy_Signal'].insert(0, 0)
        signals['Sell_Signal'].insert(0, 0)
        
        return signals
    
    def bollinger_bands_strategy(self):
        """볼린저밴드 전략"""
        signals = {'Buy_Signal': [], 'Sell_Signal': [], 'dates': self.data.index}
        
        for i in range(1, len(self.data)):
            buy_signal = 0
            sell_signal = 0
            
            if (not pd.isna(self.data['BB_lower'].iloc[i]) and not pd.isna(self.data['BB_upper'].iloc[i]) and
                not pd.isna(self.data['Close'].iloc[i]) and not pd.isna(self.data['Close'].iloc[i-1])):
                
                # 하단밴드 터치 후 반등 시 매수
                if (self.data['Close'].iloc[i] > self.data['BB_lower'].iloc[i] and 
                    self.data['Close'].iloc[i-1] <= self.data['BB_lower'].iloc[i-1]):
                    buy_signal = 1
                
                # 상단밴드 터치 후 하락 시 매도
                elif (self.data['Close'].iloc[i] < self.data['BB_upper'].iloc[i] and 
                      self.data['Close'].iloc[i-1] >= self.data['BB_upper'].iloc[i-1]):
                    sell_signal = 1
            
            signals['Buy_Signal'].append(buy_signal)
            signals['Sell_Signal'].append(sell_signal)
        
        signals['Buy_Signal'].insert(0, 0)
        signals['Sell_Signal'].insert(0, 0)
        
        return signals
    
    def macd_strategy(self):
        """MACD 교차 전략"""
        signals = {'Buy_Signal': [], 'Sell_Signal': [], 'dates': self.data.index}
        
        for i in range(1, len(self.data)):
            buy_signal = 0
            sell_signal = 0
            
            if (not pd.isna(self.data['MACD'].iloc[i]) and not pd.isna(self.data['MACD_signal'].iloc[i]) and
                not pd.isna(self.data['MACD'].iloc[i-1]) and not pd.isna(self.data['MACD_signal'].iloc[i-1])):
                
                # MACD가 Signal을 상향돌파
                if (self.data['MACD'].iloc[i] > self.data['MACD_signal'].iloc[i] and 
                    self.data['MACD'].iloc[i-1] <= self.data['MACD_signal'].iloc[i-1]):
                    buy_signal = 1
                
                # MACD가 Signal을 하향돌파
                elif (self.data['MACD'].iloc[i] < self.data['MACD_signal'].iloc[i] and 
                      self.data['MACD'].iloc[i-1] >= self.data['MACD_signal'].iloc[i-1]):
                    sell_signal = 1
            
            signals['Buy_Signal'].append(buy_signal)
            signals['Sell_Signal'].append(sell_signal)
        
        signals['Buy_Signal'].insert(0, 0)
        signals['Sell_Signal'].insert(0, 0)
        
        return signals
    
    def combined_strategy(self):
        """복합 전략 (RSI + MACD)"""
        signals = {'Buy_Signal': [], 'Sell_Signal': [], 'dates': self.data.index}
        
        for i in range(1, len(self.data)):
            buy_signal = 0
            sell_signal = 0
            
            # RSI와 MACD 조건 확인
            rsi_valid = not pd.isna(self.data['RSI'].iloc[i])
            macd_valid = (not pd.isna(self.data['MACD'].iloc[i]) and 
                         not pd.isna(self.data['MACD_signal'].iloc[i]) and
                         not pd.isna(self.data['MACD'].iloc[i-1]) and 
                         not pd.isna(self.data['MACD_signal'].iloc[i-1]))
            
            if rsi_valid and macd_valid:
                # 매수 조건: RSI < 50이고 MACD 상향돌파
                if (self.data['RSI'].iloc[i] < 50 and
                    self.data['MACD'].iloc[i] > self.data['MACD_signal'].iloc[i] and 
                    self.data['MACD'].iloc[i-1] <= self.data['MACD_signal'].iloc[i-1]):
                    buy_signal = 1
                
                # 매도 조건: RSI > 50이고 MACD 하향돌파
                elif (self.data['RSI'].iloc[i] > 50 and
                      self.data['MACD'].iloc[i] < self.data['MACD_signal'].iloc[i] and 
                      self.data['MACD'].iloc[i-1] >= self.data['MACD_signal'].iloc[i-1]):
                    sell_signal = 1
            
            signals['Buy_Signal'].append(buy_signal)
            signals['Sell_Signal'].append(sell_signal)
        
        signals['Buy_Signal'].insert(0, 0)
        signals['Sell_Signal'].insert(0, 0)
        
        return signals
    
    def get_strategy_signals(self, strategy_name):
        """전략별 신호 반환"""
        strategy_map = {
            'golden_cross': self.golden_cross_strategy,
            'rsi_divergence': self.rsi_strategy,
            'bollinger_bands': self.bollinger_bands_strategy,
            'macd_crossover': self.macd_strategy,
            'combined': self.combined_strategy
        }
        
        if strategy_name in strategy_map:
            return strategy_map[strategy_name]()
        else:
            return self.golden_cross_strategy()  # 기본값