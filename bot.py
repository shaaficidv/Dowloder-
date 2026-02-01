import telebot
import os
import psycopg2
import yt_dlp
from telebot import types

# 1. CONFIG
DB_URL = os.environ.get('DATABASE_URL')
API_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

# 2. ADVANCED DOWNLOAD ENGINE (Xallinta Sawirada & Link-yada Gaaban)
def download_media(url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'file_%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        }
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        # Hubi haddii uu yahay sawir ama video
        ext = info.get('ext')
        file_name = ydl.prepare_filename(info)
        return file_name, ext

# 3. DATABASE SETUP
def setup_db():
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (uid BIGINT PRIMARY KEY, name TEXT, lang TEXT DEFAULT NULL, downloads INTEGER DEFAULT 0)")
    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS lang TEXT DEFAULT NULL")
    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS downloads INTEGER DEFAULT 0")
    conn.commit()
    cursor.close()
    conn.close()

# 4. HANDLING MESSAGES
@bot.message_handler(func=lambda message: True)
def handle_all(message):
    url = message.text
    if "http" not in url:
        bot.reply_to(message, "I Accepted Only Link Any Help Thap Content 🎯\nContact: @Guspirrr")
        return

    # Jawabta hordhaca ah (💣)
    sent_msg = bot.send_message(message.chat.id, "💣")
    
    try:
        file_path, ext = download_media(url)
        bot.delete_message(message.chat.id, sent_msg.message_id)

        # Halkan waxaa lagu xalliyey link-ga sawirka ah
        image_extensions = ['jpg', 'jpeg', 'png', 'webp', 'heic']
        
        if ext in image_extensions:
            with open(file_path, 'rb') as photo:
                bot.send_photo(message.chat.id, photo, caption="Injoy 🔥 - @Shaaficibot")
        else:
            with open(file_path, 'rb') as video:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("Audio 🎙️", callback_data=f"audio_{file_path}"))
                bot.send_video(message.chat.id, video, caption="Injoy 🇸🇴🖤 - @Shaaficibot", reply_markup=markup)
        
        # Update Database
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET downloads = downloads + 1 WHERE uid = %s", (message.from_user.id,))
        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        bot.edit_message_text("Ist Brok Link Send Another 💔", message.chat.id, sent_msg.message_id)

# 5. COMMANDS (Start, Rank, Lang)
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, f"Asc {message.from_user.first_name}! Ii soo dir link kasta. 🎯")

# (Koodka kale ee Lang/Rank ku dar halkan sidii hore)

if __name__ == "__main__":
    setup_db()
    # Kani wuxuu caawiyaa in laga baxo "Conflict"
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
    
