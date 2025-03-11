import requests
import re
import matplotlib.pyplot as plt
from io import BytesIO
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Telegram API Details
API_ID = 21017005
API_HASH = "031173130fa724e7ecded16064724d96"
BOT_TOKEN "7882550530:AAHGbNRtsM5uGYDYwuxbrLyfWeOYpIRolGk"

app = Client("crypto_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

COINGECKO_API = "https://api.coingecko.com/api/v3"

# Function to fetch a list of all cryptocurrencies from CoinGecko
def get_all_crypto_symbols():
    response = requests.get(f"{COINGECKO_API}/coins/list").json()
    crypto_symbols = {coin["id"].lower(): coin["id"] for coin in response}
    crypto_symbols.update({coin["symbol"].lower(): coin["id"] for coin in response})
    return crypto_symbols

# Load crypto symbols (ID and symbol mapping)
CRYPTO_SYMBOLS = get_all_crypto_symbols()

# Function to detect crypto symbols in text
def detect_crypto_symbol(text):
    words = re.findall(r'\b[a-zA-Z0-9$]+\b', text.lower())  # Extract words
    for word in words:
        if word.startswith("$"):
            word = word[1:]  # Remove "$" if present
        if word in CRYPTO_SYMBOLS:
            return CRYPTO_SYMBOLS[word]  # Return the actual CoinGecko ID
    return None

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
@app.on_message(filters.text & ~filters.command(["start"]))
def crypto_handler(client, message):
    text = message.text.strip().lower()
    symbol = detect_crypto_symbol(text)

    if not symbol:
        return  # Ignore non-crypto messages

    crypto_data = get_crypto_data(symbol, "usd")
    if not crypto_data:
        return  # Ignore if no data is found

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
    total_supply = crypto_data.get("total_supply", "N/A")
    max_supply = crypto_data.get("max_supply", "N/A")
    circulating_supply = crypto_data.get("circulating_supply", "N/A")

    # Generate the 24-hour price chart
    graph_image = generate_graph(symbol)

    # Inline Buttons (Currency Conversion)
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇺🇸 USD", callback_data=f"{symbol}_usd"),
         InlineKeyboardButton("🇮🇳 INR", callback_data=f"{symbol}_inr"),
         InlineKeyboardButton("🇪🇺 EUR", callback_data=f"{symbol}_eur")]
    ])

    # Caption with all crypto details
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
        message.reply_photo(graph_image, caption=caption, reply_markup=buttons)
    else:
        message.reply(caption, reply_markup=buttons)

# Run the bot
app.run()
