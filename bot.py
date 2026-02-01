import telebot
import requests
import subprocess
import os
import time
import json
import psycopg2
import yt_dlp
from telebot import types

# 🔑 CONFIGURATION
API_TOKEN = os.environ.get('BOT_TOKEN') # Token-ka geli Railway Settings
DB_URL = os.environ.get('DATABASE_URL') 
bot = telebot.TeleBot(API_TOKEN)

# --- [DATABASE LOGIC - POSTGRESQL] ---
def init_db():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users 
                   (uid TEXT PRIMARY KEY, lang TEXT, last_url TEXT, api_audio TEXT)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS stats 
                   (id INT PRIMARY KEY, total_downloads INT DEFAULT 0)''')
    cur.execute('INSERT INTO stats (id, total_downloads) SELECT 1, 0 WHERE NOT EXISTS (SELECT 1 FROM stats WHERE id = 1)')
    cur.execute('''CREATE TABLE IF NOT EXISTS countries 
                   (country TEXT PRIMARY KEY, count INT DEFAULT 0)''')
    conn.commit()
    cur.close()
    conn.close()

# --- [DOWNLOAD ENGINE - XALKA SAWIRRADA] ---
def download_media(url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'file_%(id)s_%(index)s.%(ext)s',
        'quiet': True,
        'extract_flat': False, # Kani waa xalka sawirrada TikTok Slideshow
        'http_headers': {'User-Agent': 'Mozilla/5.0'}
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if 'entries' in info:
            return [ydl.prepare_filename(e) for e in info['entries']], 'images'
        return [ydl.prepare_filename(info)], 'video'

# --- [COMMANDS & HANDLERS] ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, f"Hi {message.from_user.first_name}! I Accepted TikTok Videos & Slideshows. 🎯")

@bot.message_handler(func=lambda message: message.text.startswith("http"))
def handle_link(message):
    url = message.text
    uid = str(message.from_user.id)
    target_msg = bot.send_message(message.chat.id, "💣")

    try:
        # 1. Isku day API-ga (Wixii Videos ah)
        res = requests.get(f"https://www.tikwm.com/api/?url={url}", timeout=15).json()
        if res.get('code') == 0 and 'images' not in res['data']:
            data = res['data']
            bot.delete_message(message.chat.id, target_msg.message_id)
            bot.send_video(message.chat.id, data['play'], caption="INJOY 🇸🇴 - @Shaaficibot")
        else:
            # 2. Isku day yt-dlp (Xalka Slideshow-ga & Fallback)
            paths, media_type = download_media(url)
            bot.delete_message(message.chat.id, target_msg.message_id)
            for p in paths:
                with open(p, 'rb') as f:
                    if media_type == 'images' or any(p.lower().endswith(x) for x in ['.jpg', '.png', '.jpeg', '.webp']):
                        bot.send_photo(message.chat.id, f)
                    else:
                        bot.send_video(message.chat.id, f, caption="INJOY 🇸🇴 - @Shaaficibot")
                if os.path.exists(p): os.remove(p)

        # Update Database
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("UPDATE stats SET total_downloads = total_downloads + 1 WHERE id = 1")
        conn.commit()
        cur.close()
        conn.close()

    except Exception:
        bot.edit_message_text("It's Brok Link ! 💔", message.chat.id, target_msg.message_id)

if __name__ == "__main__":
    init_db()
    bot.remove_webhook() # Xalka Conflict 409
    bot.infinity_polling(skip_pending=True)
    
