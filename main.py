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

# === Flask App for Render (keeps service alive) ===
app = Flask(__name__)

@app.route('/')
def home():
    return "Crypto Alert Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# === Get Top 20 USDT Pairs by Volume ===
def get_top_20_pairs():
    url = 'https://api.binance.com/api/v3/ticker/24hr'
    try:
        response = requests.get(url, timeout=10)
        tickers = response.json()
        usdt_pairs = [t for t in tickers if t['symbol'].endswith('USDT') and not t['symbol'].endswith('BUSD')]
        sorted_pairs = sorted(usdt_pairs, key=lambda x: float(x['quoteVolume']), reverse=True)
        top_20 = [t['symbol'] for t in sorted_pairs[:20]]
        return top_20
    except:
        return ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']  # fallback

# === Fetch historical Klines ===
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

# === RSI Calculation ===
def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# === MACD Calculation ===
def calculate_macd(data, fast=12, slow=26, signal=9):
    ema_fast = data.ewm(span=fast, adjust=False).mean()
    ema_slow = data.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line

# === Alert Logic ===
def check_conditions(pair):
    df = fetch_klines(pair)
    if df is None or df.empty:
        return

    close = df['close']
    rsi = calculate_rsi(close).iloc[-1]
    macd, signal = calculate_macd(close)
    macd_curr, signal_curr = macd.iloc[-1], signal.iloc[-1]

    if rsi < 30 and macd_curr > signal_curr:
        alert = f"📊 {pair}\n✅ RSI: {rsi:.2f} (oversold)\n✅ MACD Bullish Crossover"
        send_alert(alert)

def send_alert(message):
    try:
        bot.send_message(chat_id=CHAT_ID, text=message)
        print(f"Sent alert: {message}")
    except Exception as e:
        print(f"Failed to send alert: {e}")

# === Main Bot Loop ===
def main_loop():
    while True:
        top_pairs = get_top_20_pairs()
        print(f"Checking top 20 pairs: {top_pairs}")
        for pair in top_pairs:
            check_conditions(pair)
        time.sleep(300)  # Wait 5 minutes

# === Start Bot + Flask ===
if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    main_loop()
