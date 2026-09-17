import json
import time
import urllib.request

# ----------------- কনফিগারেশন -----------------
BOT_TOKEN = "8986849845:AAFD1POqeCt8VfPY6nHiXkipx7qjjcpFwBg"
CHAT_ID = "7312115541"

PAIRS = {
    "EUR/USD": "EUR",
    "GBP/USD": "GBP",
    "AUD/USD": "AUD"
}
# -----------------------------------------------

def send_telegram_msg(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = json.dumps({"chat_id": CHAT_ID, "text": message}).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Telegram error: {e}")

def get_live_price(base_currency):
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{base_currency}"
        req = urllib.request.urlopen(url)
        data = json.loads(req.read().decode('utf-8'))
        return data['rates']['USD']
    except:
        return None

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50
    gains, losses = [], []
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
            
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100
        
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# টেলিগ্রামের আপডেট/মেসেজ চেক করার ফাংশন
def get_updates(offset=None):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?timeout=5"
        if offset:
            url += f"&offset={offset}"
        req = urllib.request.urlopen(url)
        data = json.loads(req.read().decode('utf-8'))
        return data.get("result", [])
    except:
        return []

history = {pair: [] for pair in PAIRS}

print("Command-based Bot Started...")
send_telegram_msg("🤖 Bot is Online!\n\nযখনই সিগন্যাল চান, টেলিগ্রামে পাঠান: /signal")

last_update_id = None

while True:
    # প্রাইজ ডাটা ব্যাকগ্রাউন্ডে জমে থাকবে
    for pair_name, base_curr in PAIRS.items():
        price = get_live_price(base_curr)
        if price:
            history[pair_name].append(price)
            if len(history[pair_name]) > 20:
                history[pair_name].pop(0)

    # আপনার মেসেজ চেক করবে
    updates = get_updates(last_update_id)
    for update in updates:
        last_update_id = update["update_id"] + 1
        message = update.get("message", {})
        text = message.get("text", "").strip()

        # আপনি /signal বা signal লিখলেই উত্তর দেবে
        if text.lower() in ["/signal", "signal", "সিগন্যাল"]:
            send_telegram_msg("⏳Analyzing live market... Please wait.")
            
            signals_text = "📊 LIVE MARKET SIGNALS 📊\n\n"
            found_any = False
            
            for pair_name in PAIRS:
                prices = history[pair_name]
                if len(prices) > 2:
                    price = prices[-1]
                    rsi = calculate_rsi(prices)
                    moving_avg = sum(prices) / len(prices)
                    
                    if price > moving_avg and rsi < 40:
                        sig = "STRONG CALL (BUY) 🟢"
                    elif price < moving_avg and rsi > 60:
                        sig = "STRONG PUT (SELL) 🔴"
                    else:
                        sig = "NEUTRAL ⚪ (Wait)"
                    
                    signals_text += f"🔹 Asset: {pair_name}\nPrice: {price:.5f} | RSI: {rsi:.1f}\nSignal: {sig}\n\n"
                    found_any = True

            if found_any:
                send_telegram_msg(signals_text)
            else:
                send_telegram_msg("⚠️ এখনো পর্যাপ্ত ডাটা লোড হয়নি, ১০ সেকেন্ড পর আবার /signal দিন।")

    time.sleep(2)
