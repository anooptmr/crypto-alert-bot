import requests
import time
import os
import telegram
import threading
from flask import Flask
import pandas as pd

# === Telegram Setup ===
TELEGRAM_TOKEN = '7935117230:AAFF6FrTTXUP30LXWcoOicKf82S2lkEx_5A'
CHAT_ID = '383365285'
bot = telegram.Bot(token=TELEGRAM_TOKEN)

# === Flask Web Server to keep Render Free Tier alive ===
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# === Crypto Alert Logic ===
def fetch_klines(symbol, interval='1h', limit=100):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base', 'taker_buy_quote', 'ignore'
        ])
        df['close'] = df['close'].astype(float)
        return df
    except:
        return None

def calculate_rsi(data, period=9):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(data, fast=12, slow=26, signal=9):
    ema_fast = data.ewm(span=fast, adjust=False).mean()
    ema_slow = data.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line

def check_conditions(pair):
    df = fetch_klines(pair)
    if df is None or df.empty:
        return

    close = df['close']
    rsi = calculate_rsi(close).iloc[-1]
    macd, signal = calculate_macd(close)
    macd_curr, signal_curr = macd.iloc[-1], signal.iloc[-1]

    if rsi < 30 and macd_curr > signal_curr:
        alert = f"📈 {pair} - RSI: {rsi:.2f}, MACD Bullish Crossover!"
        send_alert(alert)

def send_alert(message):
    try:
        bot.send_message(chat_id=CHAT_ID, text=message)
        print(f"Sent alert: {message}")
    except Exception as e:
        print(f"Failed to send alert: {e}")

def main_loop():
    pairs = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    while True:
        for pair in pairs:
            check_conditions(pair)
        time.sleep(300)  # 5 minutes

# === Start Everything ===
if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    main_loop()
