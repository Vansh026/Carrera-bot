import requests
import os
import csv
from datetime import datetime, timezone, timedelta

# ==========================================
# 🏎️ PROJECT CARRERA: GITHUB ACTIONS EDITION
# ==========================================

# --- SECURE TELEGRAM CONFIGURATION (Loaded from GitHub Secrets) ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# --- TRADING CONFIGURATION ---
SYMBOL_URL = "https://query1.finance.yahoo.com/v8/finance/chart/^NSEI?interval=15m&range=5d"
TARGET_PTS = 40           
SL_PTS = 20               

# --- PURE PYTHON MATH ---
def calculate_ema(prices, period):
    multiplier = 2 / (period + 1)
    ema = [prices[0]]
    for price in prices[1:]:
        ema.append((price - ema[-1]) * multiplier + ema[-1])
    return ema

def calculate_rsi(prices, period=14):
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0: return 100
    return 100 - (100 / (1 + (avg_gain / avg_loss)))

def get_live_data():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(SYMBOL_URL, headers=headers, timeout=10)
        data = response.json()
        closes = [c for c in data['chart']['result'][0]['indicators']['quote'][0]['close'] if c is not None]
        if len(closes) < 20: return None, None, None
        spot = closes[-1]
        ema = calculate_ema(closes, 20)[-1]
        rsi = calculate_rsi(closes)
        return spot, rsi, ema
    except Exception as e:
        print(f"Error: {e}")
        return None, None, None

def send_alert(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram keys missing!")
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"})
        print("📱 Telegram Alert Sent!")
    except Exception as e:
        print(f"Telegram Error: {e}")

# --- MAIN EXECUTION (Runs ONCE per trigger) ---
def run_carrera():
    # Check IST Time (UTC + 5:30)
    ist_now = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
    current_time = ist_now.strftime("%H:%M")
    
    # Market Hours Check (9:15 AM to 3:30 PM IST)
    if current_time < "09:15" or current_time > "15:30":
        print(f"ZZZ Market Closed. Current IST: {current_time}")
        return

    print(f"🏎️ Carrera Cloud Running at {current_time} IST")
    spot, rsi, ema = get_live_data()
    
    if spot is None:
        print("⚠️ No data fetched.")
        return

    print(f"📊 Spot: {spot:.2f} | RSI: {rsi:.2f} | EMA: {ema:.2f}")

    # Simple 1-Trade-Per-Day Logic for Cloud
    if rsi < 30 and spot > ema:
        msg = f"🟢 <b>BUY SIGNAL!</b>\nTime: {current_time}\nRSI: {rsi:.2f}\nSpot: {spot:.2f}"
        send_alert(msg)
    elif rsi > 70 and spot < ema:
        msg = f"🔴 <b>SELL SIGNAL!</b>\nTime: {current_time}\nRSI: {rsi:.2f}\nSpot: {spot:.2f}"
        send_alert(msg)
    else:
        print("⚪ HOLD: No signal.")

if __name__ == "__main__":
    run_carrera()
