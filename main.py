import requests
import re
import time
import threading
import matplotlib.pyplot as plt
from io import BytesIO
from pyrogram import Client, filters

# Telegram API Details
API_ID = 21017005
API_HASH = "031173130fa724e7ecded16064724d96"
BOT_TOKEN = "7882550530:AAHGbNRtsM5uGYDYwuxbrLyfWeOYpIRolGk"

app = Client("crypto_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

COINGECKO_API = "https://api.coingecko.com/api/v3"
tracked_coins = {}
vip_tracked_coins = {}

# Function to get crypto data
def get_crypto_data(symbol, currency="usd"):
    response = requests.get(f"{COINGECKO_API}/coins/markets", params={
        "vs_currency": currency,
        "ids": symbol.lower(),
        "order": "market_cap_desc",
        "per_page": 1,
        "page": 1,
        "sparkline": "false"
    }).json()
    
    if response and isinstance(response, list) and len(response) > 0:
        return response[0]
    return None

# Function to generate a 24-hour price chart
def generate_graph(symbol):
    url = f"{COINGECKO_API}/coins/{symbol}/market_chart"
    response = requests.get(url, params={"vs_currency": "usd", "days": "1"}).json()
    
    if "prices" not in response:
        return None
    
    prices = response["prices"]
    timestamps = [p[0] for p in prices]
    values = [p[1] for p in prices]

    plt.figure(figsize=(8, 4))
    plt.plot(timestamps, values, label=f"{symbol.upper()} Price", color="blue")
    plt.xlabel("Time")
    plt.ylabel("Price (USD)")
    plt.title(f"{symbol.upper()} 24-Hour Price Chart")
    plt.legend()
    plt.grid()

    img = BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    plt.close()
    return img

# Handle crypto requests
@app.on_message(filters.text & ~filters.command(["start", "track", "track1", "stop"]))
def crypto_handler(client, message):
    text = message.text.strip()
    match = re.search(r"\$([a-zA-Z0-9]+)", text)  # Detect $SYMBOL
    if not match:
        return  # Ignore messages without $

    symbol = match.group(1).lower()  # Extract the symbol and convert to lowercase
    crypto_data = get_crypto_data(symbol, "usd")
    
    if not crypto_data:
        message.reply_text(f"❌ Couldn't fetch data for {symbol.upper()}. Try again later.")
        return

    # Extract data safely
    name = crypto_data.get("name", "Unknown")
    price = crypto_data.get("current_price", 0)
    high = crypto_data.get("high_24h", 0)
    low = crypto_data.get("low_24h", 0)
    volume = crypto_data.get("total_volume", 0)
    market_cap = crypto_data.get("market_cap", 0)
    change_24h = crypto_data.get("price_change_percentage_24h", 0)
    ath = crypto_data.get("ath", 0)
    atl = crypto_data.get("atl", 0)
    circulating_supply = crypto_data.get("circulating_supply", "N/A")
    total_supply = crypto_data.get("total_supply", "N/A")
    max_supply = crypto_data.get("max_supply", "N/A")

    graph_image = generate_graph(symbol)

    caption = (
        f"📌 **{name} (${symbol.upper()})**\n"
        f"💰 **Price:** ${price:,.2f} USD\n"
        f"📈 **High 24H:** ${high:,.2f}\n"
        f"📉 **Low 24H:** ${low:,.2f}\n"
        f"📊 **Volume 24H:** ${volume:,.2f}\n"
        f"💎 **Market Cap:** ${market_cap:,.2f}\n"
        f"📉 **24H Change:** {change_24h:.2f}%\n"
        f"🏆 **All-Time High:** ${ath:,.2f}\n"
        f"📅 **All-Time Low:** ${atl:,.4f}\n"
        f"🔄 **Circulating Supply:** {circulating_supply:,.0f}\n"
        f"📦 **Total Supply:** {total_supply:,.0f}\n"
        f"🚀 **Max Supply:** {max_supply:,.0f}\n"
    )

    if graph_image:
        message.reply_photo(graph_image, caption=caption)
    else:
        message.reply_text(caption)

# Track function for normal users (only alerts on ±5% changes)
@app.on_message(filters.command("track"))
def track_crypto(client, message):
    args = message.text.split()
    if len(args) < 2:
        message.reply_text("Usage: `/track $SYMBOL`")
        return

    symbol = args[1].lower().replace("$", "")  # Normalize symbol
    tracked_coins[symbol] = {"user_id": message.chat.id, "last_price": None}
    message.reply_text(f"✅ Tracking **{symbol.upper()}**. You will be notified on ±5% price changes.")

# Track1 function for VIP users (updates every 60 seconds)
@app.on_message(filters.command("track1"))
def track1_crypto(client, message):
    args = message.text.split()
    if len(args) < 2:
        message.reply_text("Usage: `/track1 $SYMBOL`")
        return

    symbol = args[1].lower().replace("$", "")  # Normalize symbol
    vip_tracked_coins[symbol] = {"user_id": message.chat.id}
    message.reply_text(f"✅ VIP tracking **{symbol.upper()}**. You will receive updates every 60 seconds.")

# Stop tracking
@app.on_message(filters.command("stop"))
def stop_tracking(client, message):
    user_id = message.chat.id
    for symbol in list(tracked_coins.keys()):
        if tracked_coins[symbol]["user_id"] == user_id:
            del tracked_coins[symbol]
    for symbol in list(vip_tracked_coins.keys()):
        if vip_tracked_coins[symbol]["user_id"] == user_id:
            del vip_tracked_coins[symbol]
    message.reply_text("❌ Tracking stopped.")

# Background tracking loop
def track_prices():
    while True:
        for symbol in list(tracked_coins.keys()):
            data = get_crypto_data(symbol)
            if data:
                price = data["current_price"]
                last_price = tracked_coins[symbol]["last_price"]
                if last_price and abs((price - last_price) / last_price) >= 0.05:
                    app.send_message(tracked_coins[symbol]["user_id"], f"⚡ {symbol.upper()} Price Alert: ${price:.2f}")
                tracked_coins[symbol]["last_price"] = price
        
        for symbol in vip_tracked_coins.keys():
            data = get_crypto_data(symbol)
            if data:
                price = data["current_price"]
                app.send_message(vip_tracked_coins[symbol]["user_id"], f"🔔 {symbol.upper()} Price Update: ${price:.2f}")

        time.sleep(60)

# Start tracking in a separate thread
threading.Thread(target=track_prices, daemon=True).start()

# Start Command
@app.on_message(filters.command("start"))
def start_command(client, message):
    message.reply_text("Send `$BTC`, `$ETH`, etc. to get price details.")

app.run()
