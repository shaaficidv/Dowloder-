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

# --- UNIVERSAL DOWNLOADER (FOR ALL PLATFORMS) ---
async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"): return

    wait = await update.message.reply_text("⚡ Labo ilbiriqsi sug... waxaan dagsanayaa muuqaalkaaga.")
    kb = [[InlineKeyboardButton("Audio 🎙️", callback_data=f"au_{url}")], [InlineKeyboardButton("Community 🌋", url="https://t.me/cummunutry1")]]

    try:
        # 1. TIKTOK IMAGES (Gaar ahaan Slideshow-ga)
        if "tiktok.com" in url:
            try:
                data = requests.get(f"https://www.tikwm.com/api/?url={url}").json().get('data')
                if data and 'images' in data:
                    imgs = [InputMediaPhoto(i) for i in data['images'][:10]]
                    await update.message.reply_media_group(media=imgs, caption="For You 🎁")
                    await wait.delete()
                    return
            except: pass

        # 2. UNIVERSAL DOWNLOADER (YT-DLP) - Kan ayaa dagsanaya link walba
        # Waxaan ka dhignay mid dagsanaya Video-ga ugu tayada fiican ee MP4 ah
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)
            await update.message.reply_video(video=open(path, 'rb'), caption="For You 🔥 - @Fastdowloder1bot", reply_markup=InlineKeyboardMarkup(kb))
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
        await wait.edit_text("❌ Link-gan ma shaqaynayo ama waa xadidan yahay. Hubi inuu sax yahay.")

# --- AUDIO EXTRACTOR (Needs FFmpeg) ---
async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    url = query.data.split('_', 1)[1]
    m = await query.message.reply_text("🎙️ Beddelay codka... Fadlan sug.")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
        'quiet': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info).rsplit('.', 1)[0] + ".mp3"
            await query.message.reply_audio(audio=open(path, 'rb'), caption="🎙️ Audio Extracted - @Fastdowloder1bot")
            os.remove(path)
        await m.delete()
    except: await m.edit_text("❌ Audio Error: Ma awoodo inaan codka soo saaro.")

# --- RANK & START COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_db()
    await update.message.reply_text("Hi! Send me ANY link (TikTok, FB, IG, YT, X, etc). 🔗")

def main():
    if not os.path.exists('downloads'): os.makedirs('downloads')
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_audio, pattern="^au_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_media))
    app.run_polling()

if __name__ == '__main__': main()
    
