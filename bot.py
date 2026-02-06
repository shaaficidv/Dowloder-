import os
import requests
import psycopg2
from telegram import Update, InputMediaPhoto
from telegram.ext import Application, MessageHandler, filters, ContextTypes

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
    except: pass

# --- TIKTOK API FUNCTION ---
def get_tiktok_data(url):
    api_url = f"https://www.tikwm.com/api/?url={url}"
    response = requests.get(api_url).json()
    return response.get('data')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "tiktok.com" not in url:
        await update.message.reply_text("Fadlan soo dir link TikTok ah oo sax ah.")
        return
    
    msg = await update.message.reply_text("🚀 Baaritaan ayaan ku jiraa...")

    data = get_tiktok_data(url)
    
    if not data:
        await msg.edit_text("❌ Khalad: Link-ga lama helin ama waa laga saaray TikTok.")
        return

    try:
        # 1. HADDII UU YAHAY SLIDESHOW (SAWIRRO)
        if 'images' in data:
            images = data['images']
            media_group = []
            for img in images[:10]: # Telegram wuxuu ogol yahay 10 sawir
                media_group.append(InputMediaPhoto(img))
            
            await update.message.reply_media_group(media=media_group)
            await msg.delete()

        # 2. HADDII UU YAHAY VIDEO
        else:
            video_url = data.get('play') # Video aan lahayn Watermark
            await update.message.reply_video(video=video_url, caption="✅ Video-gaaga waa diyaar!")
            await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ Khalad ayaa dhacay: {str(e)}")

def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot-kii waa kacay! (TikTok API Mode)")
    app.run_polling()

if __name__ == '__main__':
    main()
    
