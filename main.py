import requests
import re
import matplotlib.pyplot as plt
from io import BytesIO
from pyrogram import Client, filters

# Telegram API Details
API_ID = 21017005
API_HASH = "031173130fa724e7ecded16064724d96"
BOT_TOKEN = "6762861077:AAHw71yggj7d619H-rdMSt-TyGWJcI_jlA4"

app = Client("crypto_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

COINGECKO_API = "https://api.coingecko.com/api/v3"

# Fetch all crypto symbols dynamically
def get_all_crypto_symbols():
    try:
        response = requests.get(f"{COINGECKO_API}/coins/list").json()
        return {coin["symbol"].lower(): (coin["id"], coin["symbol"].upper()) for coin in response}
    except Exception:
        return {}

CRYPTO_SYMBOLS = get_all_crypto_symbols()

# Extract crypto symbol from message (must start with `$`)
def detect_crypto_symbol(text):
    matches = re.findall(r'\$([a-zA-Z0-9]+)', text)
    for match in matches:
        if match.lower() in CRYPTO_SYMBOLS:
            return CRYPTO_SYMBOLS[match.lower()]
    return None

# Fetch crypto price & supply data
def get_crypto_data(crypto_id):
    try:
        response = requests.get(f"{COINGECKO_API}/coins/markets", params={
            "vs_currency": "usd",
            "ids": crypto_id,
            "order": "market_cap_desc",
            "per_page": 1,
            "page": 1,
            "sparkline": "false"
        }).json()

        return response[0] if response and isinstance(response, list) else None
    except Exception:
        return None

# Generate a 24-hour price graph
def generate_graph(symbol):
    try:
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
        plt.title(f"{symbol.upper()} 24H Price Chart")
        plt.legend()
        plt.grid()

        img = BytesIO()
        plt.savefig(img, format="png")
        img.seek(0)
        plt.close()
        return img
    except Exception:
        return None

# Handle messages with `$SYMBOL`
@app.on_message(filters.text & ~filters.command(["start"]))
def crypto_handler(client, message):
    text = message.text.strip()
    detected = detect_crypto_symbol(text)

    if not detected:
        return  # Ignore messages without $SYMBOL

    crypto_id, symbol = detected
    crypto_data = get_crypto_data(crypto_id)

    if not crypto_data:
        message.reply_text(f"❌ Couldn't fetch data for `{symbol}`. Try again later.")
        return

    # Extract data
    name = crypto_data["name"]
    price = crypto_data["current_price"]
    high = crypto_data["high_24h"]
    low = crypto_data["low_24h"]
    volume = crypto_data["total_volume"]
    market_cap = crypto_data["market_cap"]
    change_24h = crypto_data["price_change_percentage_24h"]
    ath = crypto_data["ath"]
    atl = crypto_data["atl"]

    # Supply details
    circulating_supply = crypto_data.get("circulating_supply", "N/A")
    total_supply = crypto_data.get("total_supply", "N/A")
    max_supply = crypto_data.get("max_supply", "N/A")

    # Generate the 24-hour price chart
    graph_image = generate_graph(crypto_id)

    # Caption with crypto details
    caption = (
        f"📌 **{name} ({symbol})**\n"
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

# Start Command
@app.on_message(filters.command("start"))
def start_command(client, message):
    message.reply_text(
        "**Welcome to Crypto Info Bot!** 🚀\n"
        "Send a crypto symbol with `$` (e.g., `$BTC`, `$TON`) to get price details."
    )

# Run the bot
app.run()
