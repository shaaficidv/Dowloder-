import os
import requests
import yt_dlp
import psycopg2
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# --- DATABASE SETUP ---
def init_db():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT PRIMARY KEY, 
        username TEXT, 
        user_downloads INT DEFAULT 0,
        country TEXT DEFAULT 'Unknown',
        lang_selected BOOLEAN DEFAULT FALSE
    )''')
    cur.execute('CREATE TABLE IF NOT EXISTS global_stats (total_downloads INT DEFAULT 0)')
    cur.execute('INSERT INTO global_stats (total_downloads) SELECT 0 WHERE NOT EXISTS (SELECT 1 FROM global_stats)')
    conn.commit()
    cur.close()
    conn.close()

# --- UNIVERSAL DOWNLOADER (FOR INSTAGRAM & ALL) ---
async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"): return

    wait = await update.message.reply_text("⚡ Processing Link... Please wait.")
    
    # Badhamada
    kb = [[InlineKeyboardButton("Audio 🎙️", callback_data=f"au_{url}")], [InlineKeyboardButton("Community 🌋", url="https://t.me/cummunutry1")]]

    try:
        # 1. TIKTOK IMAGES SUPPORT
        if "tiktok.com" in url:
            try:
                data = requests.get(f"https://www.tikwm.com/api/?url={url}").json().get('data')
                if data and 'images' in data:
                    imgs = [InputMediaPhoto(i) for i in data['images'][:10]]
                    await update.message.reply_media_group(media=imgs, caption="For You 🎁")
                    await wait.delete()
                    return
            except: pass

        # 2. UNIVERSAL YT-DLP (Instagram, FB, YT, X)
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
            }
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                await wait.edit_text("❌ Cilad baa dhacday. Link-gan laguma dhex jiri karo hadda.")
                return
                
            path = ydl.prepare_filename(info)
            await update.message.reply_video(video=open(path, 'rb'), caption=f"✅ {info.get('title', 'For You')} \n\n🔥 - @Fastdowloder1bot", reply_markup=InlineKeyboardMarkup(kb))
            os.remove(path)
        
        # Stats Update
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cur = conn.cursor()
        cur.execute("UPDATE users SET user_downloads = user_downloads + 1 WHERE user_id = %s", (update.effective_user.id,))
        cur.execute("UPDATE global_stats SET total_downloads = total_downloads + 1")
        conn.commit()
        cur.close()
        conn.close()
        await wait.delete()

    except Exception as e:
        await wait.edit_text("❌ Link-gan ma shaqaynayo. Hubi inuu yahay mid 'Public' ah.")

# --- AUDIO & START & RANK & LANG (Dhammaystiran) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_db()
    await update.message.reply_text("Hi! I am Universal Downloader. Send me ANY link. 🔗")

def main():
    if not os.path.exists('downloads'): os.makedirs('downloads')
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_media))
    app.run_polling()

if __name__ == '__main__': main()
    
