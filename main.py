import requests
import pandas as pd
import telegram
import time
import ta

# Your Telegram bot token and chat ID
TELEGRAM_TOKEN = "7935117230:AAFF6FrTTXUP30LXWcoOicKf82S2lkEx_5A"
CHAT_ID = "383365285"

bot = telegram.Bot(token=TELEGRAM_TOKEN)

# List of pairs you want to monitor
PAIRS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT"]

# Binance API parameters
INTERVAL = "15m"      # 15 minutes
LIMIT = 100           # candles to fetch

# Indicators parameters
RSI_PERIOD = 9
RSI_OVERSOLD = 30
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

def fetch_klines(symbol, interval, limit):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None

def analyze_pair(symbol):
    data = fetch_klines(symbol, INTERVAL, LIMIT)
    if not data:
        print(f"No data for {symbol}")
        return None

    df = pd.DataFrame(data, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "number_of_trades",
        "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
    ])

    df["close"] = df["close"].astype(float)

    # Calculate RSI
    df['rsi'] = ta.momentum.rsi(df['close'], window=RSI_PERIOD)

    # Calculate MACD
    macd = ta.trend.MACD(df['close'], window_slow=MACD_SLOW, window_fast=MACD_FAST, window_sign=MACD_SIGNAL)
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    rsi = latest['rsi']
    macd_val = latest['macd']
    macd_signal = latest['macd_signal']
    prev_macd = prev['macd']
    prev_macd_signal = prev['macd_signal']

    # Debug prints to console
    print(f"{symbol} - RSI: {rsi:.2f}, MACD: {macd_val:.4f}, Signal: {macd_signal:.4f}")
    print(f"Previous MACD: {prev_macd:.4f}, Previous Signal: {prev_macd_signal:.4f}")

    # Condition: RSI oversold and MACD bullish crossover
    if rsi < RSI_OVERSOLD and prev_macd < prev_macd_signal and macd_val > macd_signal:
        return f"📈 *{symbol}* is oversold (RSI={rsi:.2f}) and MACD bullish crossover detected."

    return None

def send_telegram_alert(message):
    try:
        bot.send_message(chat_id=CHAT_ID, text=message, parse_mode=telegram.ParseMode.MARKDOWN)
        print("Sent alert:", message)
    except Exception as e:
        print("Error sending Telegram alert:", e)

def main():
    while True:
        for pair in PAIRS:
            print(f"Checking {pair}...")
            alert_msg = analyze_pair(pair)
            if alert_msg:
                send_telegram_alert(alert_msg)
            else:
                print(f"No alert for {pair}")

        print("Waiting for next check (15 minutes)...")
        time.sleep(900)  # wait 15 minutes before next check

if __name__ == "__main__":
    main()
