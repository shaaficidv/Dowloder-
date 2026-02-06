import os
import requests
import yt_dlp
from telegram import Update, InputMediaPhoto
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

# --- TIKTOK API (Xalka Sawirrada iyo Video-ga) ---
def get_tiktok_data(url):
    try:
        # API-gan wuxuu soo saaraa sawirrada haddii ay jiraan
        res = requests.get(f"https://www.tikwm.com/api/?url={url}").json()
        return res.get('data')
    except:
        return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"): return
    
    msg = await update.message.reply_text("⏳ Guda jiraa soo dejinta...")

    # 1. TIKTOK LOGIC (API-ga ayaa xallinaya sawirrada iyo video-ga)
    if "tiktok.com" in url:
        data = get_tiktok_data(url)
        if data:
            # Haddii uu yahay Slideshow (Sawirro)
            if 'images' in data:
                media_group = [InputMediaPhoto(img) for img in data['images'][:10]]
                await update.message.reply_media_group(media=media_group)
                await msg.delete()
                return
            # Haddii uu yahay Video caadi ah
            elif 'play' in data:
                await update.message.reply_video(video=data['play'], caption="✅ TikTok Video!")
                await msg.delete()
                return

    # 2. UNIVERSAL LOGIC (Instagram Reels, YouTube, FB)
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            f_path = ydl.prepare_filename(info)
            
            with open(f_path, 'rb') as f:
                await update.message.reply_video(video=f, caption="✅ Video-gaaga waa diyaar!")
            
            os.remove(f_path)
            await msg.delete()
    except Exception as e:
        await msg.edit_text("❌ Khalad: Ma awoodo inaan soo dejiyo. Hubi in link-gu sax yahay.")

def main():
    if not os.path.exists('downloads'): os.makedirs('downloads')
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()
    
