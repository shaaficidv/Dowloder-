import telebot
import os
import psycopg2
import yt_dlp
from telebot import types

# 1. CONFIG
DB_URL = os.environ.get('DATABASE_URL') #
API_TOKEN = os.environ.get('BOT_TOKEN') #
bot = telebot.TeleBot(API_TOKEN)

# 2. DOWNLOAD LOGIC
def download_video(url):
    """Waxay soo dejisaa video-ga waxayna u bixisaa 'myvideo.mp4'"""
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloaded_video.mp4',
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return 'downloaded_video.mp4'

# 3. COMMANDS (Start, Help, Lang, Rank)
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, f"Asc {message.from_user.first_name}! 🔥\n\nIi soo dir link-ga video-ga aad rabto (TikTok, YT, IG).")

@bot.message_handler(commands=['rank'])
def rank(message):
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    bot.reply_to(message, f"📊 Wadajir waxaan nahay: {total} Users!")

# 4. HANDLING VIDEO LINKS
@bot.message_handler(func=lambda message: "http" in message.text)
def handle_links(message):
    url = message.text
    sent_msg = bot.reply_to(message, "⏳ Video-ga ayaan kuu diyaarinayaa, fadlan sug xoogaa...")
    
    try:
        # Soo dejinta video-ga
        file_path = download_video(url)
        
        # U dirista user-ka
        with open(file_path, 'rb') as video:
            bot.send_video(message.chat.id, video, caption="Halkan waa video-gaagii! ✅\n\n@Botkaaga_User")
        
        # Tirtir video-ga si uusan boos u qaadan Railway
        os.remove(file_path)
        bot.delete_message(message.chat.id, sent_msg.message_id)
        
    except Exception as e:
        bot.edit_message_text(f"❌ Khalad: Link-gan lama soo dejin karo. Hubi inuu yahay mid sax ah.", 
                              message.chat.id, sent_msg.message_id)

if __name__ == "__main__":
    print("Downloader Bot is running... 🔥")
    bot.infinity_polling()
    
