import ccxt
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD
import telegram
import os

# Telegram config - set these as environment variables on Render or locally
TELEGRAM_TOKEN = os.environ.get('7935117230:AAFF6FrTTXUP30LXWcoOicKf82S2lkEx_5A')
CHAT_ID = os.environ.get('383365285')

bot = telegram.Bot(token=7935117230:AAFF6FrTTXUP30LXWcoOicKf82S2lkEx_5A)

# Exchange config
EXCHANGE = ccxt.binance()

# List of pairs to check
SYMBOLS = ['WIF/USDT', 'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'LINK/USDT']

# RSI and MACD settings
RSI_PERIOD = 9
RSI_OVERSOLD = 30

def fetch_ohlcv(symbol, timeframe='5m', limit=100):
    """Fetch OHLCV data from Binance"""
    data = EXCHANGE.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def calculate_indicators(df):
    """Calculate RSI and MACD"""
    rsi_indicator = RSIIndicator(df['close'], window=RSI_PERIOD)
    df['rsi'] = rsi_indicator.rsi()

    macd_indicator = MACD(df['close'])
    df['macd'] = macd_indicator.macd()
    df['macd_signal'] = macd_indicator.macd_signal()
    return df

def check_signals(df):
    """Check if RSI < 30 and MACD crosses over"""
    latest = df.iloc[-1]
    prev = df.iloc[-2]

    rsi_oversold = latest['rsi'] < RSI_OVERSOLD
    macd_cross = (prev['macd'] < prev['macd_signal']) and (latest['macd'] > latest['macd_signal'])

    return rsi_oversold and macd_cross

def send_telegram_message(text):
    bot.send_message(chat_id=383365285, text=text)

def main():
    for symbol in SYMBOLS:
        print(f"Checking {symbol}...")
        try:
            df = fetch_ohlcv(symbol)
            df = calculate_indicators(df)
            if check_signals(df):
                message = (f"🚨 Signal detected for {symbol}!\n"
                           f"RSI({RSI_PERIOD}): {df.iloc[-1]['rsi']:.2f} (Below {RSI_OVERSOLD})\n"
                           f"MACD: {df.iloc[-1]['macd']:.5f} > Signal: {df.iloc[-1]['macd_signal']:.5f}\n"
                           f"Time: {df.iloc[-1]['timestamp']}")
                send_telegram_message(message)
                print(f"Alert sent for {symbol}")
            else:
                print(f"No signal for {symbol}")
        except Exception as e:
            print(f"Error checking {symbol}: {e}")

if __name__ == "__main__":
    main()
