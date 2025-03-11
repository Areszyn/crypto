import requests
import matplotlib.pyplot as plt
import datetime
import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Load configuration
def load_config():
    with open("config.env", "r") as file:
        lines = file.readlines()
        config = {}
        for line in lines:
            key, value = line.strip().split("=")
            config[key] = value
        return config

config = load_config()

BOT_TOKEN = config["BOT_TOKEN"]
API_ID = config["API_ID"]
API_HASH = config["API_HASH"]

# Initialize bot
app = Client("CryptoBot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

COINGECKO_API = "https://api.coingecko.com/api/v3"

# Function to get crypto details
def get_crypto_data(symbol, currency="usd"):
    url = f"{COINGECKO_API}/coins/markets"
    params = {
        "vs_currency": currency,
        "ids": symbol.lower(),
        "order": "market_cap_desc",
        "per_page": 1,
        "page": 1,
        "sparkline": False
    }
    response = requests.get(url).json()
    if response:
        return response[0]
    return None

# Function to get candlestick graph
def get_candlestick(symbol):
    url = f"{COINGECKO_API}/coins/{symbol.lower()}/market_chart"
    params = {"vs_currency": "usd", "days": "7", "interval": "daily"}
    response = requests.get(url).json()

    if "prices" in response:
        dates = [datetime.datetime.fromtimestamp(x[0] / 1000).strftime('%Y-%m-%d') for x in response["prices"]]
        prices = [x[1] for x in response["prices"]]

        plt.figure(figsize=(8, 4))
        plt.plot(dates, prices, marker="o", linestyle="-", color="blue")
        plt.xlabel("Date")
        plt.ylabel("Price (USD)")
        plt.title(f"{symbol.upper()} 7-Day Price Chart")
        plt.xticks(rotation=45)
        plt.grid()

        graph_path = f"{symbol}_chart.png"
        plt.savefig(graph_path)
        plt.close()
        return graph_path
    return None

# Handler to auto-detect crypto name/symbol
@app.on_message(filters.text & filters.private)
def send_crypto_info(client, message):
    symbol = message.text.strip().lower()
    crypto_data = get_crypto_data(symbol)

    if crypto_data:
        price = crypto_data["current_price"]
        high = crypto_data["high_24h"]
        low = crypto_data["low_24h"]
        market_cap = crypto_data["market_cap"]
        volume = crypto_data["total_volume"]
        ath = crypto_data["ath"]
        atl = crypto_data["atl"]

        # Inline keyboard for currency conversion
        buttons = [
            [
                InlineKeyboardButton("🇮🇳 INR", callback_data=f"convert_{symbol}_inr"),
                InlineKeyboardButton("🇪🇺 EUR", callback_data=f"convert_{symbol}_eur"),
            ]
        ]

        message_text = (
            f"📌 **{crypto_data['name']} ($ {symbol.upper()})**\n"
            f"💰 **Price:** ${price}\n"
            f"📈 **High (24H):** ${high}\n"
            f"📉 **Low (24H):** ${low}\n"
            f"💎 **Market Cap:** ${market_cap}\n"
            f"📊 **Volume (24H):** ${volume}\n"
            f"🏆 **All-Time High:** ${ath}\n"
            f"📅 **All-Time Low:** ${atl}"
        )

        chart_path = get_candlestick(symbol)
        if chart_path:
            message.reply_photo(photo=chart_path, caption=message_text, reply_markup=InlineKeyboardMarkup(buttons))
            os.remove(chart_path)
        else:
            message.reply_text(message_text, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        message.reply_text("❌ Invalid cryptocurrency symbol! Please try again.")

# Handler for currency conversion
@app.on_callback_query(filters.regex(r"convert_(.+)_(.+)"))
def convert_currency(client, query):
    symbol, currency = query.data.split("_")[1:]
    crypto_data = get_crypto_data(symbol, currency)
    
    if crypto_data:
        price = crypto_data["current_price"]
        currency_symbol = "₹" if currency == "inr" else "€"

        query.message.edit_text(
            f"📌 **{crypto_data['name']} ($ {symbol.upper()})**\n"
            f"💰 **Price:** {currency_symbol}{price}\n"
            f"(Updated in {currency.upper()})"
        )

# Start bot
app.run()
