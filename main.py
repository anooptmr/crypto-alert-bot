import requests
import pandas as pd
import talib
import telegram
import time
from flask import Flask
from threading import Thread

# Your bot token and chat id
TELEGRAM_TOKEN = '7935117230:AAFF6FrTTXUP30LXWcoOicKf82S2lkEx_5A'
CHAT_ID = 383365285

bot = telegram.Bot(token=TELEGRAM_TOKEN)

app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=10000)

def start_flask():
    t = Thread(target=run)
    t.start()

def fetch_binance_klines(symbol, interval='5m', limit=100):
    url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}'
    res = requests.get(url)
    if res.status_code == 200:
        data = res.json()
        df = pd.DataFrame(data, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)
        return df
    else:
        print(f"Failed to fetch klines for {symbol}")
        return None

def get_rsi_macd(df):
    close = df['close'].values
    rsi = talib.RSI(close, timeperiod=9)
    macd, macd_signal, macd_hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
    return rsi[-1], macd[-1], macd_signal[-1]

def send_telegram_message(text):
    try:
        bot.send_message(chat_id=CHAT_ID, text=text)
        print(f"Sent alert: {text}")
    except Exception as e:
        print(f"Telegram send failed: {e}")

def fetch_binance_top_symbols(limit=20):
    # Binance API to get top symbols by volume in last 24h (spot market)
    url = 'https://api.binance.com/api/v3/ticker/24hr'
    res = requests.get(url)
    if res.status_code == 200:
        data = res.json()
        # Filter only USDT pairs & sort by quote volume desc
        usdt_pairs = [d for d in data if d['symbol'].endswith('USDT')]
        sorted_pairs = sorted(usdt_pairs, key=lambda x: float(x['quoteVolume']), reverse=True)
        top_symbols = [d['symbol'] for d in sorted_pairs[:limit]]
        return top_symbols
    else:
        print("Failed to fetch top symbols")
        return []

def main_loop():
    start_flask()  # start flask server for uptime

    while True:
        try:
            symbols = fetch_binance_top_symbols(limit=20)
            for symbol in symbols:
                df = fetch_binance_klines(symbol)
                if df is None or len(df) < 35:
                    continue

                rsi, macd, macd_signal = get_rsi_macd(df)
                price = df['close'].iloc[-1]
                volume = df['volume'].iloc[-1] * price  # volume in USDT approx

                # Filters
                if price < 0.0001:
                    continue
                if volume < 100000:  # volume > $100,000
                    continue
                # RSI oversold condition
                if rsi > 35:
                    continue
                # MACD bullish crossover (macd crosses above signal)
                prev_macd, prev_signal = get_rsi_macd(df[:-1])[1:3]
                if not (prev_macd < prev_signal and macd > macd_signal):
                    continue

                alert_text = (
                    f"🚀 Potential Buy Alert for {symbol}!\n"
                    f"Price: ${price:.6f}\n"
                    f"RSI(9): {rsi:.2f} (Oversold < 35)\n"
                    f"MACD: {macd:.6f} crossed above Signal: {macd_signal:.6f}\n"
                    f"Volume(5m): ${volume:,.2f}\n"
                    f"https://www.binance.com/en/trade/{symbol}"
                )
                send_telegram_message(alert_text)
                time.sleep(3)  # avoid spamming API & telegram too fast
        except Exception as e:
            print(f"Error in main loop: {e}")

        time.sleep(300)  # wait 5 minutes before next check

if __name__ == '__main__':
    main_loop()
