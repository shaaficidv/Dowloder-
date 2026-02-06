import os
import requests
import yt_dlp
from telegram import Update, InputMediaPhoto, InputMediaVideo
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

# --- INSTAGRAM BACKUP API ---
def get_instagram(url):
    # API-gan cusub (SnapInsta type)
    api_url = f"https://api.snapinsta.io/api/ajaxSearch" # Tusaale ahaan
    # Haddii kii hore (vkrdown) uu xumaado, waxaan isticmaalaynaa API kale
    try:
        # Halkan waxaan ku darayaa API kale oo furan
        res = requests.get(f"https://api.socialdownloader.info/instagram/?url={url}", timeout=10)
        return res.json().get('data')
    except Exception as e:
        print(f"Instagram API Error: {e}")
        return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"): return
    
    msg = await update.message.reply_text("🔄 Baaritaan kale ayaan ku jiraa...")

    # 1. INSTAGRAM LOGIC (Xal ka adag kii hore)
    if "instagram.com" in url:
        data = get_instagram(url)
        if data:
            try:
                media = []
                for item in data[:10]:
                    link = item.get('url') or item.get('link')
                    if item.get('type') == 'image' or ".jpg" in link:
                        media.append(InputMediaPhoto(link))
                    else:
                        media.append(InputMediaVideo(link))
                
                if media:
                    await update.message.reply_media_group(media=media)
                    await msg.delete()
                    return
            except: pass
        
        # Haddii API-gu fashilmo, isku day yt-dlp toos ah
        await msg.edit_text("⚠️ API-gii waa mashquul, waxaan isku dayayaa hab kale...")

    # 2. UNIVERSAL (YOUTUBE, FB, & INSTAGRAM BACKUP)
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        # Kani wuxuu caawiyaa inuu dhaafo xannibaadda qaar
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            f_path = ydl.prepare_filename(info)
            with open(f_path, 'rb') as f:
                await update.message.reply_video(video=f, caption="✅ Jaamacadda Downloader: Diyaar!")
            os.remove(f_path)
            await msg.delete()
    except Exception as e:
        await msg.edit_text(f"❌ Khalad: Ma awoodo inaan soo dejiyo link-gan. (API Down)")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()
    
