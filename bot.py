import telebot
import os
import psycopg2
import yt_dlp
from telebot import types

# CONFIG
DB_URL = os.environ.get('DATABASE_URL')
API_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

# MEDIA ENGINE
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
        if 'entries' in info: # Haddii uu yahay TikTok Slide
            paths = [ydl.prepare_filename(e) for e in info['entries']]
            return paths, 'images'
        path = ydl.prepare_filename(info)
        return [path], info.get('ext', 'mp4')

# HANDLING LINKS
@bot.message_handler(func=lambda message: "http" in message.text)
def handle_all(message):
    url = message.text
    sent_msg = bot.send_message(message.chat.id, "💣")
    try:
        paths, m_type = download_media(url)
        bot.delete_message(message.chat.id, sent_msg.message_id)
        for p in paths:
            if m_type == 'images' or any(ext in p for ext in ['.jpg', '.png', '.webp']):
                with open(p, 'rb') as photo:
                    bot.send_photo(message.chat.id, photo, caption="Injoy 🔥 - @Shaaficibot")
            else:
                with open(p, 'rb') as video:
                    bot.send_video(message.chat.id, video, caption="Injoy 🇸🇴🖤 - @Shaaficibot")
            os.remove(p)
    except:
        bot.edit_message_text("Ist Brok Link Send Another 💔", message.chat.id, sent_msg.message_id)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Asc! Ii soo dir link-ga video ama sawir kasta. 🎯")

if __name__ == "__main__":
    bot.remove_webhook() # Xalka Conflict-ka 409
    bot.infinity_polling(skip_pending=True)
    
