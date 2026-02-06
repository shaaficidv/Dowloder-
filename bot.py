import os
import yt_dlp
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Token-kaaga ka soo qaado Railway Environment Variables
TOKEN = os.getenv("BOT_TOKEN")

async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    # Hubi inuu yahay link sax ah
    if not url.startswith("http"):
        return

    msg = await update.message.reply_text("🔎 Baaritaan ayaan ku jiraa... fadlan sug.")

    # Habaynta yt-dlp
    ydl_opts = {
        'format': 'best', # Wuxuu soo dejinayaa tayada ugu fiican
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Soo saar macluumaadka link-ga
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            
            await msg.edit_text("🚀 Soo dejintii waa dhammaatay, hadda ayaan kuu soo dirayaa...")

            # Hubi haddii uu yahay Video ama Sawir
            ext = info.get('ext', '').lower()
            
            if ext in ['jpg', 'jpeg', 'png', 'webp']:
                with open(file_path, 'rb') as photo:
                    await update.message.reply_photo(photo=photo, caption="Halkan waa sawirkaagii ✅")
            else:
                with open(file_path, 'rb') as video:
                    await update.message.reply_video(video=video, caption="Halkan waa muuqaalkaagii ✅")

            # Iska tirtir faylka si uusan Railway u buuxismin
            if os.path.exists(file_path):
                os.remove(file_path)
            await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ Khalad: Link-gan lama taageero ama dhib ayaa ka jira meesha laga soo dejinayo.")
        print(f"Error: {e}")

def main():
    # Hubi in galka downloads uu jiro
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
        
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_media))
    
    print("Bot-ku hadda waa shaqaynayaa...")
    app.run_polling()

if __name__ == '__main__':
    main()
    
