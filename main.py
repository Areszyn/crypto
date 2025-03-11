import requests
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Telegram Bot API Details
API_ID = 21017005  # Replace with your API ID
API_HASH = "031173130fa724e7ecded16064724d96"  # Replace with your API Hash
BOT_TOKEN = "7882550530:AAHGbNRtsM5uGYDYwuxbrLyfWeOYpIRolGk"  # Replace with your Bot Token

# Initialize Pyrogram Client
app = Client("crypto_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Function to fetch crypto data from CoinGecko
def get_crypto_data(symbol, currency="usd"):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": currency,
        "ids": symbol.lower(),
        "order": "market_cap_desc",
        "per_page": 1,
        "page": 1,
        "sparkline": False
    }

    response = requests.get(url, params=params).json()
    
    if not response or isinstance(response, dict) and "error" in response:
        return None
    
    return response[0]

# Start Command
@app.on_message(filters.command("start"))
async def start(client, message):
    start_msg = """👋 **Welcome to Crypto Info Bot! 🚀**

🔹 Get **real-time crypto stats**  
🔹 Just type any **crypto name** (e.g., `bitcoin`, `dogecoin`)  
🔹 View **charts, high/low, market cap, supply & more**  
🔹 **Click buttons** to switch currency (USD, INR, EUR)  

📊 **Send a coin name now to get started!**"""
    
    await message.reply(start_msg)

# Crypto Price Handler (No Command Needed)
@app.on_message(filters.text & ~filters.command)
async def crypto_info(client, message):
    symbol = message.text.strip().lower()
    data = get_crypto_data(symbol)

    if not data:
        await message.reply("❌ Crypto not found. Please enter a valid name (e.g., `bitcoin`, `ethereum`).")
        return

    price = data["current_price"]
    high = data["high_24h"]
    low = data["low_24h"]
    market_cap = data["market_cap"]
    volume = data["total_volume"]
    
    response_text = f"""
📊 **{data['name']} ({data['symbol'].upper()}) Stats**
💰 **Price:** ${price}
📈 **24H High:** ${high}
📉 **24H Low:** ${low}
🏦 **Market Cap:** ${market_cap}
📊 **24H Volume:** ${volume}
🌎 **Total Supply:** {data['total_supply'] if data['total_supply'] else "N/A"}
"""

    # Currency conversion buttons
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🇺🇸 USD", callback_data=f"convert_{symbol}_usd"),
         InlineKeyboardButton("🇮🇳 INR", callback_data=f"convert_{symbol}_inr"),
         InlineKeyboardButton("🇪🇺 EUR", callback_data=f"convert_{symbol}_eur")]
    ])
    
    await message.reply(response_text, reply_markup=keyboard)

# Handle Currency Conversion Button Clicks
@app.on_callback_query()
async def convert_currency(client, callback_query):
    _, symbol, currency = callback_query.data.split("_")
    data = get_crypto_data(symbol, currency)

    if not data:
        await callback_query.answer("❌ Failed to fetch updated price.", show_alert=True)
        return
    
    price = data["current_price"]
    high = data["high_24h"]
    low = data["low_24h"]
    market_cap = data["market_cap"]
    volume = data["total_volume"]

    response_text = f"""
📊 **{data['name']} ({data['symbol'].upper()}) Stats**
💰 **Price:** {price} {currency.upper()}
📈 **24H High:** {high} {currency.upper()}
📉 **24H Low:** {low} {currency.upper()}
🏦 **Market Cap:** {market_cap} {currency.upper()}
📊 **24H Volume:** {volume} {currency.upper()}
🌎 **Total Supply:** {data['total_supply'] if data['total_supply'] else "N/A"}
"""
    
    await callback_query.message.edit(response_text)

# Run the bot
app.run()
