import telebot
import os
import yt_dlp
from telebot import types

# CONFIG
API_TOKEN = os.environ.get('BOT_TOKEN') #
bot = telebot.TeleBot(API_TOKEN)

# MEDIA ENGINE (Xallinta Slides-ka iyo Videos-ka)
def download_media(url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'file_%(id)s.%(ext)s',
        'quiet': True,
        'extract_flat': False, # Kani wuxuu muhiim u yahay sawirada slides-ka ah
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        # Haddii uu yahay TikTok Photo Slide
        if 'entries' in info:
            paths = [ydl.prepare_filename(e) for e in info['entries']]
            return paths, 'images'
        # Video caadi ah
        path = ydl.prepare_filename(info)
        return [path], info.get('ext', 'mp4')

# HANDLING ALL LINKS
@bot.message_handler(func=lambda message: "http" in message.text)
def handle_all(message):
    sent_msg = bot.send_message(message.chat.id, "💣") # Jawaabta aad codsatay
    try:
        paths, media_type = download_media(message.text)
        bot.delete_message(message.chat.id, sent_msg.message_id)
        
        for p in paths:
            # Hubi haddii uu yahay sawir ama video
            if media_type == 'images' or any(ext in p.lower() for ext in ['.jpg', '.png', '.webp', '.jpeg']):
                with open(p, 'rb') as f:
                    bot.send_photo(message.chat.id, f, caption="Injoy 🔥 - @Shaaficibot")
            else:
                with open(p, 'rb') as f:
                    bot.send_video(message.chat.id, f, caption="Injoy 🇸🇴🖤 - @Shaaficibot")
            
            # Tirtir file-ka markuu diro ka dib si uusan boosku u buuxsamin
            if os.path.exists(p):
                os.remove(p)
    except Exception:
        bot.edit_message_text("Ist Brok Link Send Another 💔", message.chat.id, sent_msg.message_id)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Asc! Ii soo dir link kasta. 🎯")

if __name__ == "__main__":
    bot.remove_webhook() # Xalka ugu muhiimsan ee Conflict 409
    bot.infinity_polling(skip_pending=True)
    
