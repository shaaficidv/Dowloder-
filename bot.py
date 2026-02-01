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
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    # Waxaan ku darnay 'lang' si dalka ama luuqadda loogu kaydiyo
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

def save_user(user_id, name):
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (uid, name) VALUES (%s, %s) ON CONFLICT (uid) DO NOTHING", (user_id, name))
    conn.commit()
    cursor.close()
    conn.close()

def update_lang(user_id, lang):
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET lang = %s WHERE uid = %s", (lang, user_id))
    conn.commit()
    cursor.close()
    conn.close()

# 3. COMMAND HANDLERS
@bot.message_handler(commands=['start'])
def start(message):
    save_user(message.from_user.id, message.from_user.first_name)
    welcome_text = (f"Asc **{message.from_user.first_name}**! 🔥\n\n"
                    "Kusoo dhawaaw Dowloder- Bot.\n"
                    "Isticmaal /Help si aad u ogaato sida aan u shaqeeyo.")
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(commands=['help'])
def help_cmd(message):
    help_text = ("📖 **Sida loo isticmaalo bot-ka:**\n\n"
                 "1. Ii soo dir link kasta (TikTok, IG, YT).\n"
                 "2. /Lang - Dooro wadankaaga/luuqaddaada.\n"
                 "3. /Rank - Arag tirada dadka isticmaala bot-ka.\n"
                 "4. /Start - Bilow bot-ka mar kale.")
    bot.reply_to(message, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['lang'])
def lang_cmd(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("Somalia 🇸🇴", callback_data="lang_Somalia")
    btn2 = types.InlineKeyboardButton("Global 🌎", callback_data="lang_Global")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, "Fadlan dooro wadankaaga ama luuqaddaada:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def callback_lang(call):
    selected_lang = call.data.split('_')[1]
    update_lang(call.from_user.id, selected_lang)
    bot.answer_callback_query(call.id, f"Waxaad dooratay {selected_lang}")
    bot.edit_message_text(f"✅ Dookhaaga waa la kaydiyey: **{selected_lang}**", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(commands=['rank'])
def rank_cmd(message):
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    bot.reply_to(message, f"📊 **Bot Rank:**\n\nWaxaa bot-ka isticmaalay **{total}** qof dhab ah. ✅", parse_mode="Markdown")

if __name__ == "__main__":
    setup_db()
    print("Bot is running...")
    bot.infinity_polling()
    
