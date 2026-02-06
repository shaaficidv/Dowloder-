import os
import yt_dlp
import psycopg2
from telegram import Update, InputMediaPhoto
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# --- DATABASE SETUP ---
def init_db():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS users (user_id BIGINT PRIMARY KEY, count INT DEFAULT 0)')
    conn.commit()
    cur.close()
    conn.close()

# --- SOO DEJINTA ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"): return
    
    msg = await update.message.reply_text("🔄 Baaritaan ayaan ku jiraa...")

    # Folder ku-meel-gaar ah
    download_dir = f"downloads/{update.effective_user.id}"
    if not os.path.exists(download_dir): os.makedirs(download_dir)

    ydl_opts = {
        'outtmpl': f'{download_dir}/%(id)s_%(now)s.%(ext)s',
        'quiet': True,
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Soo qaado dhammaan faylasha galka ku jira
            files = [os.path.join(download_dir, f) for f in os.listdir(download_dir)]
            
            if not files:
                await msg.edit_text("❌ Waxba lama helin.")
                return

            # Haddii ay yihiin sawirro badan (TikTok Slideshow)
            if len(files) > 1:
                media_group = []
                for f in files[:10]: # Telegram wuxuu ogol yahay 10 sawir hal mar
                    if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                        media_group.append(InputMediaPhoto(open(f, 'rb')))
                
                await update.message.reply_media_group(media=media_group)
                await msg.delete()
            
            # Haddii uu yahay hal Video ama hal Sawir
            else:
                file_path = files[0]
                with open(file_path, 'rb') as f:
                    if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                        await update.message.reply_photo(photo=f)
                    else:
                        await update.message.reply_video(video=f)
                await msg.delete()

            # Nadiifi galka (Delete files)
            for f in files: os.remove(f)
            os.rmdir(download_dir)

    except Exception as e:
        await msg.edit_text(f"❌ Khalad: {str(e)}")

def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()
    
