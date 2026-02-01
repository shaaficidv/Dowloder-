import telebot
import os
import psycopg2
import yt_dlp
from telebot import types

# 1. CONFIGURATION
DB_URL = os.environ.get('DATABASE_URL') #
API_TOKEN = os.environ.get('BOT_TOKEN') #
bot = telebot.TeleBot(API_TOKEN)

# 2. MEDIA DOWNLOADER (TikTok Slideshow & Video Fix)
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
        # Haddii uu yahay TikTok Slide (sawiro badan)
        if 'entries' in info:
            paths = [ydl.prepare_filename(e) for e in info['entries']]
            return paths, 'images'
        
        path = ydl.prepare_filename(info)
        ext = info.get('ext', 'mp4')
        return [path], ext

# 3. MESSAGE HANDLER
@bot.message_handler(func=lambda message: "http" in message.text)
def handle_links(message):
    url = message.text
    # Jawabta aad codsatay (💣)
    sent_msg = bot.send_message(message.chat.id, "💣")
    
    try:
        paths, media_type = download_media(url)
        bot.delete_message(message.chat.id, sent_msg.message_id)

        for p in paths:
            if media_type == 'images' or any(ext in p for ext in ['.jpg', '.png', '.webp', '.jpeg']):
                with open(p, 'rb') as photo:
                    bot.send_photo(message.chat.id, photo, caption="Injoy 🔥 - @Shaaficibot")
            else:
                with open(p, 'rb') as video:
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton("Audio 🎙️", callback_data=f"audio_{p}"))
                    bot.send_video(message.chat.id, video, caption="Injoy 🇸🇴🖤 - @Shaaficibot", reply_markup=markup)
            
            # Tirtir file-ka markuu diro ka dib
            if os.path.exists(p):
                os.remove(p)
                
    except Exception:
        bot.edit_message_text("Ist Brok Link Send Another 💔", message.chat.id, sent_msg.message_id)

# 4. START COMMAND
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Asc! Ii soo dir link-ga video ama sawirada TikTok. 🎯")

# 5. AUDIO CALLBACK
@bot.callback_query_handler(func=lambda call: call.data.startswith('audio_'))
def send_audio(call):
    # Fiiro gaar ah: Audio-gu wuxuu u baahan yahay in file-ka la hayo ama dib loo soo dejiyo
    bot.answer_callback_query(call.id, "Processing Audio...")

if __name__ == "__main__":
    # Ka hortaga Conflict 409
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)
    
