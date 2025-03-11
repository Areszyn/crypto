import requests
import matplotlib.pyplot as plt
from io import BytesIO
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Telegram API Details (No need to manually add tokens)
API_ID = 21017005
API_HASH = "031173130fa724e7ecded16064724d96"
BOT_TOKEN = "6762861077:AAHw71yggj7d619H-rdMSt-TyGWJcI_jlA4"

app = Client("crypto_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

COINGECKO_API = "https://api.coingecko.com/api/v3"

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

    if response and isinstance(response, list):
        return response[0]
    return None

# Function to generate candlestick graph
def generate_graph(symbol):
    url = f"{COINGECKO_API}/coins/{symbol.lower()}/market_chart"
    response = requests.get(url, params={"vs_currency": "usd", "days": "7"}).json()
    
    if "prices" not in response:
        return None
    
    prices = response["prices"]
    timestamps = [p[0] for p in prices]
    values = [p[1] for p in prices]

    plt.figure(figsize=(8, 4))
    plt.plot(timestamps, values, label=symbol.upper(), color="blue")
    plt.xlabel("Time")
    plt.ylabel("Price (USD)")
    plt.title(f"{symbol.upper()} 7-Day Price Chart")
    plt.legend()
    plt.grid()

    img = BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    plt.close()
    return img

# Start Command
@app.on_message(filters.command("start"))
def start(client, message):
    client.send_message(
        message.chat.id,
        "**Welcome to Crypto Bot!**\n\n"
        "🔹 Send any **crypto symbol** (e.g., `BTC`, `ETH`, `DOGE`) to get real-time data.\n"
        "🔹 Click buttons to switch between USD, INR, and EUR.\n"
        "🔹 Get **graphs & detailed stats** for each coin.\n\n"
        "🚀 *Powered by CoinGecko API*",
    )

# Handle crypto requests
@app.on_message(filters.text & ~filters.command(["start"]))
def crypto_handler(client, message):
    symbol = message.text.strip().lower()
    crypto_data = get_crypto_data(symbol, "usd")

    if not crypto_data:
        message.reply("❌ Invalid Crypto Symbol! Try again.")
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

    # Inline Buttons (Currency Conversion)
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇺🇸 USD", callback_data=f"{symbol}_usd"),
         InlineKeyboardButton("🇮🇳 INR", callback_data=f"{symbol}_inr"),
         InlineKeyboardButton("🇪🇺 EUR", callback_data=f"{symbol}_eur")]
    ])

    msg_text = (
        f"📌 **{name} (${symbol.upper()})**\n"
        f"💰 **Price:** ${price:,.2f} USD\n"
        f"📈 **High 24H:** ${high:,.2f}\n"
        f"📉 **Low 24H:** ${low:,.2f}\n"
        f"📊 **Volume 24H:** ${volume:,.2f}\n"
        f"💎 **Market Cap:** ${market_cap:,.2f}\n"
        f"📉 **24H Change:** {change_24h:.2f}%\n"
        f"🏆 **All-Time High:** ${ath:,.2f}\n"
        f"📅 **All-Time Low:** ${atl:,.4f}\n"
    )

    message.reply(msg_text, reply_markup=buttons)

# Handle Currency Conversion
@app.on_callback_query()
def callback_handler(client, callback_query):
    data = callback_query.data.split("_")
    symbol, currency = data[0], data[1]

    crypto_data = get_crypto_data(symbol, currency)

    if not crypto_data:
        callback_query.answer("❌ Failed to convert!", show_alert=True)
        return

    # Fetch converted price
    price = crypto_data["current_price"]
    high = crypto_data["high_24h"]
    low = crypto_data["low_24h"]
    volume = crypto_data["total_volume"]
    market_cap = crypto_data["market_cap"]
    change_24h = crypto_data["price_change_percentage_24h"]

    currency_symbol = {"usd": "$", "inr": "₹", "eur": "€"}[currency]

    msg_text = (
        f"📌 **{crypto_data['name']} (${symbol.upper()})**\n"
        f"💰 **Price:** {currency_symbol}{price:,.2f} {currency.upper()}\n"
        f"📈 **High 24H:** {currency_symbol}{high:,.2f}\n"
        f"📉 **Low 24H:** {currency_symbol}{low:,.2f}\n"
        f"📊 **Volume 24H:** {currency_symbol}{volume:,.2f}\n"
        f"💎 **Market Cap:** {currency_symbol}{market_cap:,.2f}\n"
        f"📉 **24H Change:** {change_24h:.2f}%\n"
    )

    callback_query.message.edit_text(msg_text, reply_markup=callback_query.message.reply_markup)

# Run the bot
app.run()
