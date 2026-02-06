import os
import requests
import yt_dlp
import psycopg2
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Railway Variables
TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# --- DATABASE SETUP ---
def init_db():
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cur = conn.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS users (user_id BIGINT PRIMARY KEY, count INT DEFAULT 0)')
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")

# --- TIKTOK VIDEO API (TikWM) ---
def get_tiktok_video(url):
    try:
        res = requests.get(f"https://www.tikwm.com/api/?url={url}").json()
        return res.get('data', {}).get('play') # Wuxuu soo celinayaa Video URL
    except:
        return None

# --- UNIVERSAL DOWNLOADER FUNCTION ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"): return
    
    msg = await update.message.reply_text("⏳ Guda jiraa soo dejinta muuqaalka...")

    # A. TIKTOK LOGIC (API ayaa ugu fiican)
    if "tiktok.com" in url:
        video_url = get_tiktok_video(url)
        if video_url:
            await update.message.reply_video(video=video_url, caption="✅ TikTok Video!")
            await msg.delete()
            return

    # B. UNIVERSAL LOGIC (Instagram Reels, YouTube, FB, iwm)
    # Waxaan isticmaalaynaa yt-dlp oo wata User-Agent si looga dhaafo xannibaadda
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            f_path = ydl.prepare_filename(info)
            
            with open(f_path, 'rb') as f:
                await update.message.reply_video(video=f, caption="✅ Video-gaaga waa diyaar!")
            
            if os.path.exists(f_path):
                os.remove(f_path)
            await msg.delete()
            
    except Exception as e:
        await msg.edit_text("❌ Khalad: Ma awoodo inaan soo dejiyo link-gan. Hubi inuu yahay Public Video.")
        print(f"Error: {e}")

def main():
    # Abuur galka downloads haddii uusan jirin
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
        
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot-kii University Downloader waa shaqaynayaa!")
    app.run_polling()

if __name__ == '__main__':
    main()
    
