import os
import yt_dlp
import psycopg2
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# --- UNIVERSAL DOWNLOADER ---
async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"): return

    wait = await update.message.reply_text("⚡ Processing Instagram Reel...")
    
    # 1. YT-DLP OPTS (Universal for IG, FB, YT, TikTok)
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        # Kani wuxuu ka caawinayaa Instagram inaan laga xannibin bot-ka
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)
            
            kb = [[InlineKeyboardButton("Audio 🎙️", callback_data=f"au_{url}")]]
            await update.message.reply_video(
                video=open(path, 'rb'), 
                caption=f"✅ {info.get('title', 'For You')} \n\n🔥 - @Fastdowloder1bot",
                reply_markup=InlineKeyboardMarkup(kb)
            )
            os.remove(path)
        await wait.delete()

    except Exception as e:
        await wait.edit_text("❌ Cilad baa dhacday. Hubi in link-gu yahay mid 'Public' ah.")

# --- START COMMAND ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! Send me any Instagram Reel, TikTok, or YouTube link. 🔗")

def main():
    if not os.path.exists('downloads'): os.makedirs('downloads')
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_media))
    app.run_polling()

if __name__ == '__main__': main()
    
