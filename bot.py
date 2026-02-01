import telebot
import os
import psycopg2
from telebot import types

# CONFIG
DB_URL = os.environ.get('DATABASE_URL')
API_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

def setup_db():
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        # Kani wuxuu abuurayaa table-ka isagoo wata 'lang'
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                uid BIGINT PRIMARY KEY, 
                name TEXT, 
                lang TEXT DEFAULT NULL
            )
        """)
        # Haddii table-ku horay u jiray laakiin 'lang' maqneyd, kani waa ku darayaa
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS lang TEXT DEFAULT NULL")
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Database Error: {e}")

def get_user_lang(user_id):
    """Wuxuu soo celinayaa luuqadda haddii ay jirto"""
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT lang FROM users WHERE uid = %s", (user_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else None

def save_user_initial(user_id, name):
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

@bot.message_handler(commands=['start'])
def start(message):
    save_user_initial(message.from_user.id, message.from_user.first_name)
    bot.reply_to(message, "Asc! Bot-ku waa diyaar. Dooro wadankaaga adigoo isticmaalaya /lang")

@bot.message_handler(commands=['lang'])
def lang_cmd(message):
    user_lang = get_user_lang(message.from_user.id)
    
    # Halkan waxay ka hubinaysaa haddii uu horay u doortay
    if user_lang and user_lang != 'Lama dooran':
        bot.reply_to(message, f"❌ Horay ayaad u dooratay: **{user_lang}**. Ma beddeli kartid hadda.", parse_mode="Markdown")
        return

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Somalia 🇸🇴", callback_data="lang_Somalia"),
               types.InlineKeyboardButton("Global 🌎", callback_data="lang_Global"))
    bot.send_message(message.chat.id, "Fadlan dooro wadankaaga (Hal mar kaliya):", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def callback_lang(call):
    user_lang = get_user_lang(call.from_user.id)
    
    if user_lang and user_lang != 'Lama dooran':
        bot.answer_callback_query(call.id, "Horay ayaad u dooratay!")
        bot.edit_message_text("❌ Wadanka waa lagaa diiwangeliyey horay.", call.message.chat.id, call.message.message_id)
        return

    selected = call.data.split('_')[1]
    update_lang(call.from_user.id, selected)
    bot.answer_callback_query(call.id, f"Dalkan {selected} ayaa laguugu daray.")
    bot.edit_message_text(f"✅ Wadankaaga waxaa loo kaydiyey: **{selected}**", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

if __name__ == "__main__":
    setup_db()
    bot.infinity_polling()
    
