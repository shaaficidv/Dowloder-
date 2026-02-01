import telebot
import os
import psycopg2
from telebot import types

# 1. CONFIG
DB_URL = os.environ.get('DATABASE_URL')
API_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

# 2. DATABASE SETUP
def setup_db():
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                uid BIGINT PRIMARY KEY, 
                name TEXT, 
                lang TEXT DEFAULT 'Lama dooran'
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Database Error: {e}")

# 3. HELPER FUNCTIONS
def save_user(user_id, name):
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (uid, name) VALUES (%s, %s) ON CONFLICT (uid) DO NOTHING", (user_id, name))
        conn.commit()
        cursor.close()
        conn.close()
    except: pass

def update_lang(user_id, lang):
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET lang = %s WHERE uid = %s", (lang, user_id))
        conn.commit()
        cursor.close()
        conn.close()
    except: pass

# 4. COMMAND HANDLERS
@bot.message_handler(commands=['start'])
def start(message):
    save_user(message.from_user.id, message.from_user.first_name)
    bot.reply_to(message, f"Asc {message.from_user.first_name}! Kusoo dhawaaw Dowloder- Bot. 🔥\nIsticmaal /Help si aad u ogaato sida aan u shaqeeyo.")

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message, "📖 **Amarrada Bot-ka:**\n\n1. /Lang - Dooro dalkaaga\n2. /Rank - Arag tirada user-ka\n3. /Help - Caawinaad\n4. Ii soo dir link-ga video-ga aad rabto.", parse_mode="Markdown")

@bot.message_handler(commands=['lang'])
def lang_cmd(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Somalia 🇸🇴", callback_data="lang_Somalia"),
               types.InlineKeyboardButton("Global 🌎", callback_data="lang_Global"))
    bot.send_message(message.chat.id, "Fadlan dooro wadankaaga:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def callback_lang(call):
    selected = call.data.split('_')[1]
    update_lang(call.from_user.id, selected)
    bot.edit_message_text(f"✅ Dookhaaga waxaa lagu kaydiyey: **{selected}**", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(commands=['rank'])
def rank_cmd(message):
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    bot.reply_to(message, f"📊 **Bot Rank:**\n\nWaxaa bot-ka isticmaalay **{total}** qof dhab ah. ✅")

if __name__ == "__main__":
    setup_db()
    bot.infinity_polling()
    
