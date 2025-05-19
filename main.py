import requests

# --- CONFIGURATION ---
TELEGRAM_TOKEN = "7935117230:AAFF6FrTTXUP30LXWcoOicKf82S2lkEx_5A"
CHAT_ID = "383365285"
DEX_SCREENER_URL = "https://api.dexscreener.com/latest/dex/pairs"

# --- SAFETY THRESHOLDS ---
MIN_VOLUME_USD = 500_000
MIN_MARKET_CAP_USD = 1_000_000

# --- ALERT FUNCTION ---
def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    res = requests.post(url, data=payload)
    print(f"Sent alert: {res.status_code}")

# --- MAIN SCRIPT ---
def check_tokens():
    response = requests.get(DEX_SCREENER_URL)
    if response.status_code != 200:
        print("Failed to fetch data")
        return

    data = response.json()

    for token in data.get("pairs", []):
        name = token.get("baseToken", {}).get("name", "Unknown")
        symbol = token.get("baseToken", {}).get("symbol", "???")
        volume_24h = float(token.get("volume", {}).get("h24", 0))
        market_cap = float(token.get("fdv", 0))

        # --- SAFETY FILTERS ---
        if volume_24h < MIN_VOLUME_USD or market_cap < MIN_MARKET_CAP_USD:
            continue

        # --- PLACEHOLDER INDICATOR CHECKS ---
        # Replace these with actual RSI and MACD logic
        rsi = 28  # sample test value
        macd_signal = True  # sample trigger

        if rsi < 30 and macd_signal:
            message = f"""
📈 *Trade Signal!*
Token: {name} ({symbol})
RSI: {rsi}
Volume (24h): ${volume_24h:,.0f}
Market Cap: ${market_cap:,.0f}
👉 Meets RSI & MACD condition.
"""
            send_telegram_alert(message)

# --- TEST MESSAGE ON STARTUP ---
send_telegram_alert("✅ Test alert from your crypto bot! Deployment is working.")

# --- RUN MAIN FUNCTION ---
check_tokens()
