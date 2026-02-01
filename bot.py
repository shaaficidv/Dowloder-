import telebot
import os
import psycopg2
from telebot import types

# CONFIG
DB_URL = os.environ.get('DATABASE_URL')
API_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

def setup_db():
    """Abuurista table-ka iyo khaanadda lang"""
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                uid BIGINT PRIMARY KEY, 
                name TEXT, 
                lang TEXT DEFAULT NULL
            )
        """)
        # Kani wuxuu dhab ahaan u darayaa 'lang' haddii ay maqan tahay
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS lang TEXT DEFAULT NULL")
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Database Setup Error: {e}")

def get_user_data(user_id):
    """Soo saarista xogta user-ka haddii ay jirto"""
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT lang FROM users WHERE uid = %s", (user_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (uid, name) VALUES (%s, %s) ON CONFLICT (uid) DO NOTHING", (user_id, user_name))
    conn.commit()
    cursor.close()
    conn.close()
    
    bot.reply_to(message, f"Asc {user_name}! 🔥 Isticmaal /lang si aad wadanka u doorato (Hal mar kaliya).")

@bot.message_handler(commands=['lang'])
def lang_cmd(message):
    user_data = get_user_data(message.from_user.id)
    
    # Hubi haddii dalka horay loogu keydiyey (Haddii aysan None ahayn)
    if user_data and user_data[0] is not None:
        bot.reply_to(message, f"❌ Horay ayaad u dooratay wadanka: **{user_data[0]}**. Ma beddeli kartid.")
        return

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Somalia 🇸🇴", callback_data="lang_Somalia"),
               types.InlineKeyboardButton("Global 🌎", callback_data="lang_Global"))
    bot.send_message(message.chat.id, "Dooro wadankaaga (Fursaddu waa hal mar):", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def callback_lang(call):
    user_data = get_user_data(call.from_user.id)
    
    if user_data and user_data[0] is not None:
        bot.answer_callback_query(call.id, "Diiwaangelintaadu way dhammaatay!")
        return

    selected = call.data.split('_')[1]
    
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET lang = %s WHERE uid = %s", (selected, call.from_user.id))
    conn.commit()
    cursor.close()
    conn.close()
    
    bot.edit_message_text(f"✅ Wadankaaga waxaa loo kaydiyey: **{selected}**. Ma beddeli kartid hadda ka dib.", call.message.chat.id, call.message.message_id)

if __name__ == "__main__":
    setup_db()
    bot.infinity_polling()
    
