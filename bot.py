import telebot
import os
import psycopg2
import yt_dlp
from telebot import types

# 1. CONFIG
DB_URL = os.environ.get('DATABASE_URL')
API_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

# 2. ADVANCED MEDIA ENGINE
def download_media(url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'file_%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        },
        'extract_flat': False, # Muhiim u ah inuu sawirada dhex galo
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        
        # Haddii uu yahay TikTok Photo/Slide
        if 'entries' in info:
            files = []
            for entry in info['entries']:
                files.append(ydl.prepare_filename(entry))
            return files, 'images'
            
        file_path = ydl.prepare_filename(info)
        ext = info.get('ext', 'mp4')
        return [file_path], ext

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

# 4. PROCESSING LOGIC
@bot.message_handler(func=lambda message: "http" in message.text)
def handle_media(message):
    url = message.text
    sent_msg = bot.send_message(message.chat.id, "📸") # Jawaabta sawirada
    
    try:
        paths, type_ext = download_media(url)
        bot.delete_message(message.chat.id, sent_msg.message_id)

        # Haddii ay yihiin sawiro badan (TikTok Slide)
        if type_ext == 'images' or type_ext in ['jpg', 'png', 'webp']:
            for p in paths:
                with open(p, 'rb') as photo:
                    bot.send_photo(message.chat.id, photo, caption="Injoy 🔥 - @Shaaficibot")
                os.remove(p)
        else:
            # Video caadi ah
            for p in paths:
                with open(p, 'rb') as video:
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton("Audio 🎙️", callback_data=f"audio_{p}"))
                    bot.send_video(message.chat.id, video, caption="Injoy 🇸🇴🖤 - @Shaaficibot", reply_markup=markup)
        
        # Update DB Stats
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET downloads = downloads + 1 WHERE uid = %s", (message.from_user.id,))
        conn.commit()
        cursor.close()
        conn.close()

    except Exception:
        bot.edit_message_text("Ist Brok Link Send Another 💔", message.chat.id, sent_msg.message_id)

if __name__ == "__main__":
    setup_db()
    # Waxaan ku daray kuwan si looga hortago Conflict-ka logs-kaaga ku jira
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)
    
