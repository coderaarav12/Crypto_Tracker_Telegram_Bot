import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand, ReplyKeyboardMarkup, KeyboardButton
import requests
import re
import os
import difflib
import random

import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is missing from .env file!")

bot = telebot.TeleBot(TOKEN)
BACKEND_URL = "http://127.0.0.1:5003"

# Register the commands with Telegram so the Menu button appears!
bot.set_my_commands([
    BotCommand("start", "Wake up the bot"),
    BotCommand("help", "See what I can do"),
    BotCommand("crypto", "Show top 10 cryptocurrencies"),
    BotCommand("news", "Show current best market news"),
    BotCommand("trending", "Show top trending crypto today"),
    BotCommand("feargreed", "Show market sentiment index"),
    BotCommand("about", "About the creator")
])

user_context = {}

KNOWN_COINS = {
    "bitcoin": "bitcoin", "btc": "bitcoin", "ethereum": "ethereum", "eth": "ethereum",
    "solana": "solana", "sol": "solana", "dogecoin": "dogecoin", "doge": "dogecoin",
    "cardano": "cardano", "ada": "cardano", "ripple": "ripple", "xrp": "ripple",
    "polkadot": "polkadot", "dot": "polkadot", "chainlink": "chainlink", "link": "chainlink",
    "litecoin": "litecoin", "ltc": "litecoin", "polygon": "matic-network", "matic": "matic-network",
    "avalanche": "avalanche-2", "avax": "avalanche-2", "shiba": "shiba-inu", "shib": "shiba-inu",
    "pepe": "pepe", "tether": "tether", "usdt": "tether"
}

HUMOROUS_REPLIES = [
    "Bro, are you speaking ancient Sumerian? 📜 I only understand Crypto and Stocks. Try 'bitcoin' or 'tesla'.",
    "I'm an AI, not a mind reader! 🧠 Did your cat walk across the keyboard? Give me a real company or coin.",
    "Error 404: English not found. 🤖 Please ask for a real stock or crypto!",
    "I asked Wall Street about that... they hung up on me. 📉 Try a real asset like 'ethereum' or 'apple'.",
    "Are you inventing new words? 😂 Because that's definitely not a crypto. Try again!"
]

def get_main_keyboard():
    # This creates the persistent keyboard buttons above the text space
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton("🪙 Top 10 Crypto"), KeyboardButton("📰 Market News"))
    markup.add(KeyboardButton("🔥 Trending Crypto"), KeyboardButton("🧭 Fear & Greed"))
    return markup

def append_restart(markup=None):
    if markup is None:
        markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🔄 Main Menu / Restart", callback_data="cmd_restart"))
    return markup

WELCOME_TEXT = """Hi I am Crypto Tracker, how can I help you? 🤖

I am your advanced financial assistant. I track the global crypto markets and Wall Street stocks in real-time.

**💡 Pro Tips - Just talk to me naturally!**
🔹 _"Price of Bitcoin"_
🔹 _"Show me a 30-day graph for Ethereum"_
🔹 _"Latest news about Tesla"_

**⚡ Quick Commands:**
/crypto - Top 10 Coins
/trending - What's hot today
/news - Global Headlines
/feargreed - Market Sentiment
/about - About the developer

_Or simply use the interactive menu buttons below! 👇_"""

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Activating modules...", reply_markup=get_main_keyboard())
    
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🪙 Top 10 Crypto", callback_data="cmd_crypto"),
               InlineKeyboardButton("🔥 Trending", callback_data="cmd_trending"))
    markup.row(InlineKeyboardButton("📰 Market News", callback_data="cmd_news"),
               InlineKeyboardButton("🧭 Fear & Greed", callback_data="cmd_feargreed"))
    markup.row(InlineKeyboardButton("👨‍💻 About Me", callback_data="cmd_about"))
               
    bot.reply_to(message, WELCOME_TEXT, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(commands=['crypto'])
def cmd_crypto(message):
    fetch_top10(message.chat.id)

@bot.message_handler(commands=['news'])
def cmd_news(message):
    fetch_general_news(message.chat.id)

@bot.message_handler(commands=['trending'])
def cmd_trending(message):
    fetch_trending(message.chat.id)

@bot.message_handler(commands=['feargreed'])
def cmd_feargreed(message):
    fetch_fear_greed(message.chat.id)

@bot.message_handler(commands=['about'])
def cmd_about(message):
    text = (
        "🤖 **About Me**\n\n"
        "Hi! I am an advanced AI financial tracking bot, proudly built and engineered by **Aarav Goel**, "
        "a 2nd-year student at SRM Institute of Science and Technology (SRMIST).\n\n"
        "I was designed to bring live market data, interactive charts, and real-time news for "
        "both Wall Street and the Blockchain directly into Telegram! 🚀"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

def fetch_fear_greed(chat_id):
    bot.send_message(chat_id, "🧭 Analyzing Market Sentiment...")
    try:
        resp = requests.get(f"{BACKEND_URL}/api/fear_greed")
        if resp.status_code == 200:
            data = resp.json()
            val = int(data.get('value', 50))
            classif = data.get('value_classification', 'Unknown')
            
            if val <= 25:
                emoji = "🔴"
                advice = "Extreme Fear can be a sign that investors are too worried. That could be a buying opportunity."
            elif val <= 45:
                emoji = "🟠"
                advice = "Fear indicates a bearish market sentiment."
            elif val <= 55:
                emoji = "🟡"
                advice = "Neutral market. Investors are undecided."
            elif val <= 75:
                emoji = "🟢"
                advice = "Greed indicates a bullish market sentiment."
            else:
                emoji = "🔥"
                advice = "Extreme Greed means investors are getting too greedy. The market may be due for a correction."
                
            progress = int(val / 10)
            bar = "█" * progress + "░" * (10 - progress)
            
            text = (
                f"🧭 **Global Fear & Greed Index**\n\n"
                f"{emoji} **Status:** {classif.upper()} ({val}/100)\n"
                f"📊 **Meter:** `{bar}`\n\n"
                f"💡 **Analysis:**\n_{advice}_"
            )
            bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=append_restart())
        else:
            bot.send_message(chat_id, "Could not fetch Fear & Greed Index.")
    except Exception:
        bot.send_message(chat_id, "Backend error.")

def fetch_top10(chat_id):
    bot.send_message(chat_id, "Fetching top 10 cryptocurrencies...")
    try:
        resp = requests.get(f"{BACKEND_URL}/api/top10")
        if resp.status_code == 200:
            coins = resp.json().get("top10", [])
            reply = "🪙 **Top 10 Cryptocurrencies by Market Cap:**\n\n"
            for c in coins:
                name = (c.get('name') or 'Unknown').replace('_', '\\_').replace('*', '')
                symbol = (c.get('symbol', '').upper()).replace('_', '\\_').replace('*', '')
                price = c.get('current_price') or 0.0
                change = c.get('price_change_percentage_24h') or 0.0
                trend = "📈" if change >= 0 else "📉"
                reply += f"🔹 **{name} ({symbol})**: ${price:,.2f} ({change:.2f}% {trend})\n"
            bot.send_message(chat_id, reply, parse_mode="Markdown", reply_markup=append_restart())
        else:
            bot.send_message(chat_id, "Could not fetch top 10.")
    except Exception:
        bot.send_message(chat_id, "Backend error.")

def fetch_general_news(chat_id):
    bot.send_message(chat_id, "📰 Fetching the latest overall market news...")
    try:
        resp = requests.get(f"{BACKEND_URL}/api/general_news")
        if resp.status_code == 200:
            news = resp.json().get("news", [])
            reply = "🔥 **Latest Global Market Headlines:**\n\n"
            for n in news:
                title = n['title'].replace('[', '').replace(']', '').replace('*', '').replace('_', '\\_')
                reply += f"🔹 [{title}]({n['link']})\n\n"
            bot.send_message(chat_id, reply, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=append_restart())
        else:
            bot.send_message(chat_id, "Could not fetch general news.")
    except Exception:
        bot.send_message(chat_id, "Backend error.")

def fetch_trending(chat_id):
    bot.send_message(chat_id, "Fetching trending coins...")
    try:
        resp = requests.get(f"{BACKEND_URL}/api/trending")
        if resp.status_code == 200:
            coins = resp.json().get("coins", [])[:7]
            reply = "🔥 **Top Trending Cryptos Today:**\n\n"
            
            markup = InlineKeyboardMarkup()
            
            for c in coins:
                item = c.get("item", {})
                name = (item.get('name') or 'Unknown').replace('_', '\\_').replace('*', '')
                symbol = (item.get('symbol', '').upper()).replace('_', '\\_').replace('*', '')
                slug = item.get('id') # Using ID to fetch accurately
                
                reply += f"🔹 **{name} ({symbol})** - Rank #{item.get('market_cap_rank')}\n"
                
                # Add an inline button for this specific trending coin
                markup.add(InlineKeyboardButton(f"Check {name} ({symbol})", callback_data=f"price_crypto_{slug}"))
                
                # Add to KNOWN_COINS dynamically so it works in future texts
                KNOWN_COINS[name.lower()] = slug
                KNOWN_COINS[symbol.lower()] = slug
                
            markup = append_restart(markup)
            bot.send_message(chat_id, reply, parse_mode="Markdown", reply_markup=markup)
        else:
            bot.send_message(chat_id, "Could not fetch trending.")
    except Exception:
        bot.send_message(chat_id, "Backend error.")

def send_chart(chat_id, entity_name, entity_type, days=7):
    bot.send_message(chat_id, f"📉 Generating beautiful chart for {entity_name.capitalize()}...")
    try:
        resp = requests.get(f"{BACKEND_URL}/api/chart/{entity_name}?days={days}")
        if resp.status_code == 200:
            chart_path = resp.json().get("chart_path")
            if chart_path and os.path.exists(chart_path):
                with open(chart_path, 'rb') as photo:
                    bot.send_photo(chat_id, photo, caption=f"Here is your {days}-day chart for {entity_name.capitalize()}", reply_markup=append_restart())
            else:
                bot.send_message(chat_id, "Chart generated but file not found.")
        else:
            bot.send_message(chat_id, "I currently only support beautiful charts for Crypto. Company charts coming soon!")
    except Exception:
        bot.send_message(chat_id, "Error connecting to backend.")

def send_info(chat_id, coin):
    bot.send_message(chat_id, f"📚 Fetching developer info for {coin.capitalize()}...")
    try:
        resp = requests.get(f"{BACKEND_URL}/api/info/{coin}")
        if resp.status_code == 200:
            data = resp.json()
            desc = data.get('description', 'No description available.')
            if len(desc) > 800:
                desc = desc[:800] + "..."
            import re
            desc = re.sub('<[^<]+>', '', desc)
            link = data.get('homepage', '#')
            text = f"📚 **About {coin.capitalize()}:**\n\n{desc}\n\n🌐 **Website:** {link}"
            bot.send_message(chat_id, text, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=append_restart())
        else:
            bot.send_message(chat_id, "Could not fetch info.")
    except Exception:
        bot.send_message(chat_id, "Backend error.")

def send_price(chat_id, matched_name, entity_type, raw_query=""):
    try:
        if entity_type == "crypto":
            resp = requests.get(f"{BACKEND_URL}/api/price/{matched_name}")
            if resp.status_code == 200:
                data = resp.json()
                
                # Safe getters for all values
                price = data.get("price") or 0.0
                change = data.get("usd_24h_change") or 0.0
                trend = "📈" if change >= 0 else "📉"
                mc = data.get('market_cap') or 0
                rank = data.get('market_cap_rank') or "N/A"
                vol = data.get('total_volume') or 0
                h24 = data.get('high_24h') or 0.0
                l24 = data.get('low_24h') or 0.0
                cs = data.get('circulating_supply') or 0
                ath = data.get('ath') or 0.0
                ath_c = data.get('ath_change_percentage') or 0.0
                
                name = (data.get('name', 'Unknown')).replace('_', '\\_').replace('*', '')
                symbol = (data.get('symbol', '')).replace('_', '\\_').replace('*', '').upper()
                
                text = (
                    f"🪙 **{name} ({symbol})**\n"
                    f"**Rank:** #{rank}\n\n"
                    f"💵 **Price:** ${price:,.4f}\n"
                    f"📊 **24h Change:** {change:.2f}% {trend}\n\n"
                    f"📈 **24h High:** ${h24:,.4f}\n"
                    f"📉 **24h Low:** ${l24:,.4f}\n"
                    f"💰 **Market Cap:** ${mc:,.0f}\n"
                    f"🌊 **24h Volume:** ${vol:,.0f}\n"
                    f"🔄 **Circ. Supply:** {cs:,.0f}\n"
                    f"🏆 **All-Time High:** ${ath:,.4f} ({ath_c:.2f}%)\n"
                )
                
                markup = InlineKeyboardMarkup()
                markup.row(InlineKeyboardButton("📉 7D Graph", callback_data=f"chart_crypto_{matched_name}"),
                           InlineKeyboardButton("📈 30D Graph", callback_data=f"chart30_crypto_{matched_name}"))
                markup.row(InlineKeyboardButton("📚 What is this?", callback_data=f"info_crypto_{matched_name}"),
                           InlineKeyboardButton("📰 Latest News", callback_data=f"news_crypto_{matched_name}"))
                markup.add(InlineKeyboardButton("🔄 Refresh Price", callback_data=f"price_crypto_{matched_name}"))
                markup = append_restart(markup)
                
                bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)
            else:
                bot.send_message(chat_id, f"Failed to fetch crypto price for {matched_name}.")
                
        elif entity_type == "stock":
            msg = bot.send_message(chat_id, f"🏢 Searching global stock market for '{raw_query}'...")
            resp = requests.get(f"{BACKEND_URL}/api/stock/{raw_query}")
            if resp.status_code == 200:
                data = resp.json()
                price = data.get("price") or 0.0
                change = data.get("change_pct") or 0.0
                trend = "📈" if change >= 0 else "📉"
                mc = data.get('market_cap') or 0
                h24 = data.get('day_high') or 0.0
                l24 = data.get('day_low') or 0.0
                vol = data.get('volume') or 0
                f52 = data.get('fiftyTwoWeekHigh') or 0.0
                
                name = (data.get('name') or 'Unknown').replace('_', '\\_').replace('*', '')
                symbol = (data.get('symbol') or '').replace('_', '\\_').replace('*', '').upper()
                
                text = (
                    f"🏢 **{name} ({symbol})**\n\n"
                    f"💵 **Price:** ${price:,.2f}\n"
                    f"📊 **24h Change:** {change:.2f}% {trend}\n\n"
                    f"📈 **24h High:** ${h24:,.2f}\n"
                    f"📉 **24h Low:** ${l24:,.2f}\n"
                    f"💰 **Market Cap:** ${mc:,.0f}\n"
                    f"🌊 **Volume:** {vol:,.0f}\n"
                    f"🏆 **52-Week High:** ${f52:,.2f}\n"
                )
                
                markup = InlineKeyboardMarkup()
                markup.row(InlineKeyboardButton("🔄 Refresh", callback_data=f"price_stock_{data['symbol']}"),
                           InlineKeyboardButton("📰 Latest News", callback_data=f"news_stock_{data['symbol']}"))
                markup = append_restart(markup)
                bot.edit_message_text(text, chat_id=chat_id, message_id=msg.message_id, parse_mode="Markdown", reply_markup=markup)
            else:
                bot.edit_message_text(f"Bro, I searched Wall Street and couldn't find '{raw_query}'. Are you sure that company exists?", chat_id=chat_id, message_id=msg.message_id)
    except Exception as e:
        bot.send_message(chat_id, "Backend error formatting data.")

def send_news(chat_id, entity_name):
    bot.send_message(chat_id, f"📰 Fetching the latest news for '{entity_name}'...")
    try:
        resp = requests.get(f"{BACKEND_URL}/api/news/{entity_name}")
        if resp.status_code == 200:
            news = resp.json().get("news", [])
            if not news:
                bot.send_message(chat_id, f"No recent news found for {entity_name}.")
                return
            reply = f"🔥 **Latest Headlines for {entity_name.capitalize()}:**\n\n"
            for n in news:
                reply += f"🔹 [{n['title']}]({n['link']})\n\n"
            bot.send_message(chat_id, reply, parse_mode="Markdown", disable_web_page_preview=True)
        else:
            bot.send_message(chat_id, "Could not find any news.")
    except Exception:
        bot.send_message(chat_id, "Backend error while fetching news.")


@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    data = call.data
    
    if data == "trending" or data == "cmd_trending":
        fetch_trending(chat_id)
    elif data == "cmd_crypto":
        fetch_top10(chat_id)
    elif data == "cmd_news":
        fetch_general_news(chat_id)
    elif data == "cmd_feargreed":
        fetch_fear_greed(chat_id)
    elif data == "cmd_about":
        cmd_about(call.message)
    elif data == "cmd_restart":
        send_welcome(call.message)
    elif data.startswith("chart_crypto_"):
        coin = data.split("chart_crypto_")[1]
        send_chart(chat_id, coin, "crypto", days=7)
    elif data.startswith("chart30_crypto_"):
        coin = data.split("chart30_crypto_")[1]
        send_chart(chat_id, coin, "crypto", days=30)
    elif data.startswith("info_crypto_"):
        coin = data.split("info_crypto_")[1]
        send_info(chat_id, coin)
    elif data.startswith("price_crypto_"):
        coin = data.split("price_crypto_")[1]
        send_price(chat_id, coin, "crypto")
    elif data.startswith("price_stock_"):
        symbol = data.split("price_stock_")[1]
        send_price(chat_id, symbol, "stock", raw_query=symbol)
    elif data.startswith("news_"):
        parts = data.split("_")
        entity = parts[2]
        send_news(chat_id, entity)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text.lower()
    chat_id = message.chat.id
    
    # Handle Persistent Keyboard Buttons
    if text == "🪙 top 10 crypto":
        fetch_top10(chat_id)
        return
    elif text == "📰 market news":
        fetch_general_news(chat_id)
        return
    elif text == "🔥 trending crypto":
        fetch_trending(chat_id)
        return
    elif "fear & greed" in text:
        fetch_fear_greed(chat_id)
        return

    # Handle Basic Greetings properly
    greetings = ["hello", "hi", "hey", "whats up", "what's up", "yo", "sup", "howdy"]
    cleaned_text = ''.join(c for c in text if c.isalnum() or c.isspace()).strip()
    
    if cleaned_text in greetings or (any(cleaned_text.startswith(g + " ") for g in greetings) and len(cleaned_text.split()) <= 2):
        bot.reply_to(message, "Hey there! 👋 I'm ready to fetch data. Ask me for the price, chart, or news of any crypto or stock (e.g., 'price of tesla').", reply_markup=get_main_keyboard())
        return
        
    chit_chat = {
        "how are u": "I'm running at peak efficiency! 🤖 My servers are cool and my APIs are connected. How can I help you?",
        "how are you": "I'm running at peak efficiency! 🤖 My servers are cool and my APIs are connected. How can I help you?",
        "how r u": "I'm running at peak efficiency! 🤖 My servers are cool and my APIs are connected. How can I help you?",
        "how r you": "I'm running at peak efficiency! 🤖 My servers are cool and my APIs are connected. How can I help you?",
        "ok": "Got it! Let me know if you need anything else. 📈",
        "okay": "Got it! Let me know if you need anything else. 📈",
        "ok ok got it": "Awesome! I'm here if you want to look up another asset. 💰",
        "got it": "Awesome! I'm here if you want to look up another asset. 💰",
        "thanks": "You're welcome! Happy trading! 🚀",
        "thank you": "You're welcome! Happy trading! 🚀",
        "cool": "Right?! 😎 Hit me up if you need more market data.",
        "awesome": "I know, right?! 🤩 I'm powered by pure code and caffeine. Let's look up another one!",
        "bruh": "Bruh! 🤨 What's on your mind? Tell me a stock or crypto to fetch.",
        "wow": "Mind blown, right? 🤯 The markets are crazy. What should we look at next?",
        "yes": "Awesome. Let's go! What's next?",
        "no": "No problem! Just tell me when you need something.",
        "good": "Good to hear! Let's make some money. 💸"
    }
    
    who_are_you = ["who are u", "who r u", "who are you", "who u", "who you", "what are you", "what r u", "what are u"]
    
    if cleaned_text in who_are_you:
        cmd_about(message)
        return
        
    if cleaned_text in chit_chat:
        bot.reply_to(message, chit_chat[cleaned_text])
        return
    
    if any(k in text for k in ["invest", "trending", "better", "buy", "top"]):
        fetch_trending(chat_id)
        return

    words = [w for w in text.split() if w.isalnum()]
    stop_words = ["what", "is", "the", "price", "of", "show", "me", "a", "graph", "chart", "for", "can", "you", "tell", "how", "much", "crypto", "coin", "today", "now", "please", "company", "stock", "news", "about", "on", "in", "at", "with", "from"]
    
    if "its" in words or "it" in words:
        if chat_id in user_context:
            query_entity = user_context[chat_id]['name']
            entity_type = user_context[chat_id]['type']
        else:
            bot.reply_to(message, random.choice(HUMOROUS_REPLIES))
            return
    else:
        meaningful_words = [w for w in words if w not in stop_words]
        if not meaningful_words:
            bot.reply_to(message, random.choice(HUMOROUS_REPLIES))
            return
        query_entity = " ".join(meaningful_words)
        entity_type = "unknown"

    matched_coin = None
    
    # First, check KNOWN_COINS locally
    close_matches = difflib.get_close_matches(query_entity, KNOWN_COINS.keys(), n=1, cutoff=0.7)
    if close_matches:
        matched_coin = KNOWN_COINS[close_matches[0]]
        entity_type = "crypto"
    else:
        # Intelligent Disambiguation using Yahoo Finance!
        try:
            search_url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query_entity}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            res = requests.get(search_url, headers=headers, timeout=5).json()
            quotes = res.get('quotes', [])
            
            if quotes and quotes[0].get('quoteType') == 'CRYPTOCURRENCY':
                # Yahoo Finance says it's a crypto, so let's hit CoinGecko for the rich Crypto UI
                search_resp = requests.get(f"{BACKEND_URL}/api/search_crypto/{query_entity}")
                if search_resp.status_code == 200:
                    matched_coin = search_resp.json().get('id')
                    entity_type = "crypto"
                else:
                    entity_type = "stock"
            elif quotes and quotes[0].get('quoteType') in ['EQUITY', 'ETF']:
                # It's a real company stock or ETF!
                entity_type = "stock"
            else:
                # If Yahoo didn't find it, check CoinGecko as a last resort
                search_resp = requests.get(f"{BACKEND_URL}/api/search_crypto/{query_entity}")
                if search_resp.status_code == 200:
                    matched_coin = search_resp.json().get('id')
                    entity_type = "crypto"
                else:
                    entity_type = "stock"
        except Exception:
            entity_type = "stock"

    user_context[chat_id] = {'name': matched_coin if entity_type == "crypto" else query_entity, 'type': entity_type}

    if 'news' in text:
        send_news(chat_id, matched_coin if entity_type == "crypto" else query_entity)
    elif 'chart' in text or 'graph' in text:
        send_chart(chat_id, matched_coin if entity_type == "crypto" else query_entity, entity_type)
    else:
        send_price(chat_id, matched_coin if entity_type == "crypto" else query_entity, entity_type, raw_query=query_entity)

if __name__ == "__main__":
    bot.infinity_polling()
