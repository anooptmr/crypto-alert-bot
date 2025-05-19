import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime

# Telegram config
TELEGRAM_TOKEN = "7935117230:AAFF6FrTTXUP30LXWcoOicKf82S2lkEx_5A"
CHAT_ID = "383365285"

# Binance config
BASE_URL = "https://api.binance.com"
INTERVAL = "5m"
LIMIT = 100
RSI_PERIOD = 9
RSI_THRESHOLD = 35
VOLUME_THRESHOLD = 100000
PRICE_THRESHOLD = 0.0001

def send_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

def get_trending_pairs():
    try:
        res = requests.get(f"{BASE_URL}/api/v3/ticker/24hr").json()
        filtered = [x for x in res if x["symbol"].endswith("USDT")]
        sorted_by_volume = sorted(filtered, key=lambda x: float(x["quoteVolume"]), reverse=True)
        return [x["symbol"] for x in sorted_by_volume[:20]]
    except Exception as e:
        print("Error fetching trending:", e)
        return []

def fetch_klines(symbol):
    try:
        url = f"{BASE_URL}/api/v3/klines"
        params = {"symbol": symbol, "interval": INTERVAL, "limit": LIMIT}
        data = requests.get(url, params=params).json()
        return data
    except Exception as e:
        print("Error fetching klines:", e)
        return None

def calculate_rsi(prices, period=RSI_PERIOD):
    delta = np.diff(prices)
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=period).mean()
    avg_loss = pd.Series(loss).rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if not rsi.empty else None

def calculate_macd(prices):
    prices = pd.Series(prices)
    ema12 = prices.ewm(span=12, adjust=False).mean()
    ema26 = prices.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd.iloc[-1], signal.iloc[-1]

def analyze():
    trending = get_trending_pairs()
    for symbol in trending:
        klines = fetch_klines(symbol)
        if not klines or len(klines) < RSI_PERIOD:
            continue

        closes = [float(k[4]) for k in klines]
        volumes = [float(k[5]) * float(k[4]) for k in klines]  # quote volume
        current_price = closes[-1]
        current_volume = volumes[-1]

        if current_volume < VOLUME_THRESHOLD or current_price < PRICE_THRESHOLD:
            continue

        rsi = calculate_rsi(closes)
        if rsi is None or rsi > RSI_THRESHOLD:
            continue

        macd, signal = calculate_macd(closes)
        if macd < signal:
            continue

        msg = (
            f"📢 *Signal Found!*\n"
            f"Symbol: `{symbol}`\n"
            f"Price: ${current_price:.6f}\n"
            f"RSI(9): {rsi:.2f} ✅\n"
            f"MACD: {macd:.5f} > Signal: {signal:.5f} ✅\n"
            f"Volume(5m): ${current_volume:,.0f}"
        )
        send_alert(msg)
        print(f"✅ Alert sent for {symbol}")

if __name__ == "__main__":
    while True:
        print(f"\n🔁 Scanning @ {datetime.now().strftime('%H:%M:%S')}")
        try:
            analyze()
        except Exception as e:
            print("Error:", e)
        time.sleep(300)  # run every 5 mins
