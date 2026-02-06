import os
import requests
import yt_dlp
import psycopg2
from telegram import Update, InputMediaPhoto
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# --- DATABASE ---
def update_stats(user_id):
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cur = conn.cursor()
        cur.execute('INSERT INTO users (user_id, count) VALUES (%s, 1) ON CONFLICT (user_id) DO UPDATE SET count = users.count + 1', (user_id,))
        conn.commit()
        cur.close()
        conn.close()
    except: pass

# --- TIKTOK SPECIAL (Slideshow & Video) ---
def get_tiktok(url):
    api_url = f"https://www.tikwm.com/api/?url={url}"
    res = requests.get(api_url).json()
    return res.get('data')

# --- UNIVERSAL DOWNLOADER (YT, IG, FB) ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"): return
    
    msg = await update.message.reply_text("🚀 Jaamacadda Downloader-ka ayaa guda jirta...")
    update_stats(update.effective_user.id)

    # 1. HADDII UU YAHAY TIKTOK
    if "tiktok.com" in url:
        data = get_tiktok(url)
        if data and 'images' in data:
            media = [InputMediaPhoto(img) for img in data['images'][:10]]
            await update.message.reply_media_group(media=media)
            await msg.delete()
            return
        elif data and 'play' in data:
            await update.message.reply_video(video=data['play'], caption="✅ TikTok-gaaga waa diyaar!")
            await msg.delete()
            return

    # 2. HADDII UU YAHAY PLATFORM KALE (YouTube, IG, FB, iwm)
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            
            with open(file_path, 'rb') as f:
                if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    await update.message.reply_photo(photo=f, caption="✅ Sawirkaaga waa diyaar!")
                else:
                    await update.message.reply_video(video=f, caption="✅ Muuqaalkaaga waa diyaar!")
            
            os.remove(file_path)
            await msg.delete()
    except Exception as e:
        await msg.edit_text("❌ Khalad: Link-gan lama taageero ama dhib ayaa jira.")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()
    
