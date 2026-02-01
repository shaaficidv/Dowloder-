import telebot
import os
import yt_dlp
from telebot import types

# 1. CONFIG
API_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

# 2. MEDIA ENGINE (Si gaar ah loogu habeeyey Sawirada Slides-ka ah)
def download_media(url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'file_%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        # Kani waa sirta lagu soo dejiyo sawirada slides-ka ah
        'extract_flat': False, 
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        
        # Haddii uu yahay TikTok Slide (Sawirro badan)
        if 'entries' in info:
            paths = []
            for entry in info['entries']:
                # Hubi in sawirka la soo dejiyey ka hor intaan liiska lagu darin
                paths.append(ydl.prepare_filename(entry))
            return paths, 'images'
        
        # Haddii uu yahay Video caadi ah
        path = ydl.prepare_filename(info)
        return [path], info.get('ext', 'mp4')

# 3. MESSAGE HANDLER
@bot.message_handler(func=lambda message: "http" in message.text)
def handle_all(message):
    sent_msg = bot.send_message(message.chat.id, "💣")
    
    try:
        paths, media_type = download_media(message.text)
        bot.delete_message(message.chat.id, sent_msg.message_id)

        for p in paths:
            # Hubi haddii file-ka uu dhamaadkiisu yahay sawir
            if media_type == 'images' or any(p.lower().endswith(ext) for ext in ['.jpg', '.png', '.webp', '.jpeg']):
                with open(p, 'rb') as photo:
                    bot.send_photo(message.chat.id, photo, caption="Injoy 🔥 - @Shaaficibot")
            else:
                with open(p, 'rb') as video:
                    bot.send_video(message.chat.id, video, caption="Injoy 🇸🇴🖤 - @Shaaficibot")
            
            # Tirtir file-ka markuu diro ka dib si uusan boosku u buuxsamin
            if os.path.exists(p):
                os.remove(p)
                
    except Exception as e:
        print(f"Error: {e}") # Kani wuxuu kuu tusayaa dhibka jira
        bot.edit_message_text("Ist Brok Link Send Another 💔", message.chat.id, sent_msg.message_id)

if __name__ == "__main__":
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)
    
