import os
import yt_dlp
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Ka soo qaado Token-ka Railway Variables
TOKEN = os.getenv("BOT_TOKEN")

async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    await update.message.reply_text("Waan guda jiraa soo dejinta... fadlan sug.")

    try:
        # Habaynta soo dejinta
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'noplaylist': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # U dir qofka faylka
            with open(filename, 'rb') as f:
                await update.message.reply_document(document=f)
            
            # Iska tirtir faylka markuu diro ka dib si uusan booska uga buuxin Railway
            os.remove(filename)

    except Exception as e:
        await update.message.reply_text(f"Khalad ayaa dhacay: {str(e)}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_media))
    print("Bot-kii waa kiciyey...")
    app.run_polling()

if __name__ == '__main__':
    main()
    
