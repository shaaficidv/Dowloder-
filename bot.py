import telebot
import psycopg2
import os
import yt_dlp
import requests
from telebot import types

# CONFIGURATION
# Token-ka halkan haku qorin, ku dar Railway Variables ahaan: BOT_TOKEN
API_TOKEN = os.environ.get('BOT_TOKEN') 
DB_URL = os.environ.get('DATABASE_URL') 
bot = telebot.TeleBot(API_TOKEN)

# --- [DATABASE CONNECTION - XALKA KAYDKA] ---
def init_db():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    # Waxaan sameyneynaa miisaska xogta (Users iyo Stats)
    cur.execute('''CREATE TABLE IF NOT EXISTS users 
                   (uid TEXT PRIMARY KEY, lang TEXT, last_url TEXT)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS stats 
                   (id INT PRIMARY KEY, total_downloads INT DEFAULT 0)''')
    cur.execute('INSERT INTO stats (id, total_downloads) SELECT 1, 0 WHERE NOT EXISTS (SELECT 1 FROM stats WHERE id = 1)')
    conn.commit()
    cur.close()
    conn.close()

# --- [DOWNLOAD ENGINE - XALKA SAWIRRADA] ---
def download_media(url):
    ydl_opts = {
        'extract_flat': False, # Kani waa xalka sawirrada TikTok Slideshow
        'outtmpl': 'file_%(id)s_%(index)s.%(ext)s',
        'quiet': True,
        'http_headers': {'User-Agent': 'Mozilla/5.0'}
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if 'entries' in info:
            paths = [ydl.prepare_filename(e) for e in info['entries']]
            return paths, 'images'
        path = ydl.prepare_filename(info)
        return [path], 'video'

# --- [HANDLERS] ---
@bot.message_handler(func=lambda message: message.text.startswith("http"))
def handle_link(message):
    uid = str(message.from_user.id)
    sent_msg = bot.send_message(message.chat.id, "💣")
    
    try:
        paths, media_type = download_media(message.text)
        bot.delete_message(message.chat.id, sent_msg.message_id)
        
        for p in paths:
            with open(p, 'rb') as f:
                if media_type == 'images' or any(p.lower().endswith(x) for x in ['.jpg', '.png', '.jpeg', '.webp']):
                    bot.send_photo(message.chat.id, f)
                else:
                    bot.send_video(message.chat.id, f, caption="INJOY 🇸🇴 - @Shaaficibot")
            if os.path.exists(p):
                os.remove(p)
        
        # Update Stats gudaha PostgreSQL
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute('UPDATE stats SET total_downloads = total_downloads + 1 WHERE id = 1')
        conn.commit()
        cur.close()
        conn.close()

    except Exception:
        bot.edit_message_text("It's Brok Link ! 💔", message.chat.id, sent_msg.message_id)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Asc! Ii soo dir Link si aan kuugu soo dejiyo Video ama Sawirro. 🎯")

if __name__ == "__main__":
    init_db() 
    bot.remove_webhook() # Si looga badbaado Conflict 409
    bot.infinity_polling(skip_pending=True)
    
