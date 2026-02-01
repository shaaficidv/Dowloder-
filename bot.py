import telebot
import os
import psycopg2
import yt_dlp
from telebot import types

# 1. CONFIG
DB_URL = os.environ.get('DATABASE_URL') #
API_TOKEN = os.environ.get('BOT_TOKEN') #
bot = telebot.TeleBot(API_TOKEN)

# 2. DATABASE SETUP
def setup_db():
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        # Abuur table-ka haddii uusan jirin
        cursor.execute("CREATE TABLE IF NOT EXISTS users (uid BIGINT PRIMARY KEY, name TEXT, lang TEXT DEFAULT NULL)")
        # Ku dar lang haddii ay hore u maqneyd
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS lang TEXT DEFAULT NULL")
        conn.commit()
        cursor.close()
        conn.close()
        print("Database structure is ready! ✅")
    except Exception as e:
        print(f"DB Error: {e}")

def get_user_lang(user_id):
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT lang FROM users WHERE uid = %s", (user_id,))
    res = cursor.fetchone()
    cursor.close()
    conn.close()
    return res[0] if res else None

# 3. COMMANDS
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    name = message.from_user.first_name
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (uid, name) VALUES (%s, %s) ON CONFLICT (uid) DO NOTHING", (user_id, name))
    conn.commit()
    cursor.close()
    conn.close()
    bot.reply_to(message, f"Asc {name}! Dooro dalkaaga adigoo isticmaalaya /lang (Fursaddu waa hal mar).")

@bot.message_handler(commands=['lang'])
def lang_cmd(message):
    current_lang = get_user_lang(message.from_user.id)
    if current_lang:
        bot.reply_to(message, f"❌ Horay ayaad u dooratay dalka: **{current_lang}**.")
        return
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Somalia 🇸🇴", callback_data="lang_Somalia"),
               types.InlineKeyboardButton("Global 🌎", callback_data="lang_Global"))
    bot.send_message(message.chat.id, "Dooro dalkaaga (Hal mar oo kaliya):", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def save_lang(call):
    current_lang = get_user_lang(call.from_user.id)
    if current_lang:
        bot.answer_callback_query(call.id, "Horay ayaad u dooratay!")
        return
    
    selected = call.data.split('_')[1]
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET lang = %s WHERE uid = %s", (selected, call.from_user.id))
    conn.commit()
    cursor.close()
    conn.close()
    bot.edit_message_text(f"✅ Dalkaaga waxaa loo kaydiyey: **{selected}**", call.message.chat.id, call.message.message_id)

# 4. DOWNLOADER LOGIC (Basic)
@bot.message_handler(func=lambda message: "http" in message.text)
def handle_download(message):
    bot.reply_to(message, "⏳ Video-ga ayaan kuu soo dejinayaa, fadlan sug...")
    # Halkan waxaa geli doona koodka yt-dlp ee dhabta ah

if __name__ == "__main__":
    setup_db()
    bot.infinity_polling()
    
