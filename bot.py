import telebot
import os
import psycopg2
import yt_dlp
from telebot import types

# 1. CONFIGURATION
DB_URL = os.environ.get('DATABASE_URL')
API_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

# 2. DATABASE SETUP
def setup_db():
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            uid BIGINT PRIMARY KEY, 
            name TEXT, 
            lang TEXT DEFAULT NULL,
            downloads INTEGER DEFAULT 0
        )
    """)
    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS lang TEXT DEFAULT NULL")
    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS downloads INTEGER DEFAULT 0")
    conn.commit()
    cursor.close()
    conn.close()

# 3. ADVANCED DOWNLOAD ENGINE (Xallinta TikTok links)
def download_media(url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'file_%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Referer': 'https://www.tiktok.com/',
        }
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info), info.get('ext')

# 4. COMMAND HANDLERS
@bot.message_handler(commands=['start'])
def start(message):
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (uid, name) VALUES (%s, %s) ON CONFLICT (uid) DO NOTHING", 
                   (message.from_user.id, message.from_user.first_name))
    conn.commit()
    cursor.close()
    conn.close()
    bot.reply_to(message, f"Asc **{message.from_user.first_name}**! Ii soo dir link-ga video ama sawir kasta. 🎯", parse_mode="Markdown")

@bot.message_handler(commands=['help'])
def help_msg(message):
    bot.reply_to(message, "📖 **Sida loo isticmaalo:**\n1. Soo dir Link (TikTok, YT, IG).\n2. /lang - Dooro dalkaaga.\n3. /rank - Stats-ka bot-ka.\n\nContact: @Guspirrr", parse_mode="Markdown")

@bot.message_handler(commands=['lang'])
def lang_menu(message):
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT lang FROM users WHERE uid = %s", (message.from_user.id,))
    res = cursor.fetchone()
    cursor.close()
    conn.close()

    if res and res[0]:
        bot.reply_to(message, f"Choice: **{res[0]}** ✅", parse_mode="Markdown")
        return

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Africa 🌍", callback_data="cont_Africa"),
               types.InlineKeyboardButton("Asia 🌏", callback_data="cont_Asia"),
               types.InlineKeyboardButton("Europe 🇪🇺", callback_data="cont_Europe"))
    bot.send_message(message.chat.id, "Dooro Qaaraddaada:", reply_markup=markup)

@bot.message_handler(commands=['rank'])
def rank_cmd(message):
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT lang, COUNT(*) as count FROM users WHERE lang IS NOT NULL GROUP BY lang ORDER BY count DESC LIMIT 10")
    top_countries = cursor.fetchall()
    cursor.execute("SELECT SUM(downloads) FROM users")
    total_dl = cursor.fetchone()[0] or 0
    cursor.close()
    conn.close()
    
    text = "📊 **Top 10 Countries:**\n"
    for i, (c, count) in enumerate(top_countries, 1):
        text += f"{i}. {c}: {count} users\n"
    text += f"\n🔥 Total Downloads: {total_dl}"
    bot.reply_to(message, text, parse_mode="Markdown")

# 5. CALLBACKS (Luuqadda & Codka)
@bot.callback_query_handler(func=lambda call: call.data.startswith('cont_'))
def show_countries(call):
    continent = call.data.split('_')[1]
    markup = types.InlineKeyboardMarkup(row_width=2)
    if continent == "Africa":
        countries = ["Somalia 🇸🇴", "Kenya 🇰🇪", "Egypt 🇪🇬", "Nigeria 🇳🇬", "Ethiopia 🇪🇹", "Djibouti 🇩🇯", "Sudan 🇸🇩", "Uganda 🇺🇬", "Morocco 🇲🇦", "Tanzania 🇹🇿"]
    elif continent == "Asia":
        countries = ["Turkey 🇹🇷", "Saudi Arabia 🇸🇦", "Qatar QA", "UAE 🇦🇪", "China 🇨🇳", "Japan 🇯🇵", "India 🇮🇳", "Pakistan 🇵🇰", "Malaysia 🇲🇾", "Kuwait 🇰🇼"]
    else:
        countries = ["UK 🇬🇧", "Germany 🇩🇪", "France 🇫🇷", "Italy 🇮🇹", "Spain 🇪🇸", "Norway 🇳🇴", "Sweden 🇸🇪", "Finland 🇫🇮", "Netherlands 🇳🇱", "Switzerland 🇨🇭"]
    
    btns = [types.InlineKeyboardButton(c, callback_data=f"set_{c}") for c in countries]
    markup.add(*btns)
    bot.edit_message_text(f"Dooro Wadanka ({continent}):", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('set_'))
def save_country(call):
    country = call.data.split('_')[1]
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET lang = %s WHERE uid = %s", (country, call.from_user.id))
    conn.commit()
    cursor.close()
    conn.close()
    bot.edit_message_text(f"Choice: **{country}** ✅", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

# 6. PROCESSING LINKS
@bot.message_handler(func=lambda message: True)
def handle_all(message):
    url = message.text
    if "http" not in url:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Contact 🎯", url="t.me/Guspirrr"))
        bot.reply_to(message, "I Accepted Only Link Any Help Thap Content 🎯", reply_markup=markup)
        return

    sent_msg = bot.send_message(message.chat.id, "💣")
    
    try:
        file_path, ext = download_media(url)
        bot.delete_message(message.chat.id, sent_msg.message_id)
        
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET downloads = downloads + 1 WHERE uid = %s", (message.from_user.id,))
        conn.commit()
        cursor.close()
        conn.close()

        if ext in ['jpg', 'jpeg', 'png', 'webp']:
            with open(file_path, 'rb') as photo:
                bot.send_photo(message.chat.id, photo, caption="Injoy 🔥 - @Shaaficibot")
        else:
            with open(file_path, 'rb') as video:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("Audio 🎙️", callback_data=f"audio_{file_path}"))
                bot.send_video(message.chat.id, video, caption="Injoy 🇸🇴🖤 - @Shaaficibot", reply_markup=markup)
    except:
        bot.edit_message_text("Ist Brok Link Send Another 💔", message.chat.id, sent_msg.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('audio_'))
def send_audio(call):
    file_path = call.data.split('_', 1)[1]
    try:
        with open(file_path, 'rb') as audio:
            bot.send_audio(call.message.chat.id, audio, caption="Injoy 🇸🇴 🖤 - @Shaaficibot")
    except:
        bot.answer_callback_query(call.id, "Audio error.")

if __name__ == "__main__":
    setup_db()
    bot.infinity_polling()
    
