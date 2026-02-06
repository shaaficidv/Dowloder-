import os
import requests
import yt_dlp
import psycopg2
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# --- UNIVERSAL AUDIO EXTRACTOR (Needs FFmpeg) ---
async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    url = query.data.split('_', 1)[1]
    m = await query.message.reply_text("🎙️ Beddelay codka... Fadlan sug.")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info).rsplit('.', 1)[0] + ".mp3"
            await query.message.reply_audio(audio=open(path, 'rb'), caption="🎙️ Audio Extracted - @Fastdowloder1bot")
            os.remove(path)
        await m.delete()
    except Exception as e:
        await m.edit_text("❌ Cilad: FFmpeg ma rakibna. Fadlan isticmaal Dockerfile ama nixpacks.toml.")

# --- UNIVERSAL VIDEO/IMAGE DOWNLOADER (All Platforms) ---
async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"): return
    
    wait = await update.message.reply_text("⚡ Processing...")
    kb = [[InlineKeyboardButton("Audio 🎙️", callback_data=f"au_{url}")], 
          [InlineKeyboardButton("Community 🌋", url="https://t.me/cummunutry1")]]

    try:
        # TIKTOK SLIDESHOW SUPPORT
        if "tiktok.com" in url:
            data = requests.get(f"https://www.tikwm.com/api/?url={url}").json().get('data')
            if data and 'images' in data:
                imgs = [InputMediaPhoto(i) for i in data['images'][:10]]
                await update.message.reply_media_group(media=imgs, caption="For You 🎁")
                await wait.delete()
                return

        # YT-DLP UNIVERSAL (FB, IG, YT, X, etc.)
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)
            await update.message.reply_video(video=open(path, 'rb'), caption="For You 🔥 - @Fastdowloder1bot", reply_markup=InlineKeyboardMarkup(kb))
            os.remove(path)
        await wait.delete()

    except Exception:
        await wait.edit_text("❌ Link-gan ma shaqaynayo ama platform-ka looma oggola.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! Send any link (FB, IG, TikTok, YT, X). 🔗")

def main():
    if not os.path.exists('downloads'): os.makedirs('downloads')
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_audio, pattern="^au_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_media))
    app.run_polling()

if __name__ == '__main__': main()
    
