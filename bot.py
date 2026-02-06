import os
import requests
import yt_dlp
from telegram import Update, InputMediaPhoto, InputMediaVideo
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

# --- 1. TIKTOK API (TikWM) ---
def get_tiktok(url):
    res = requests.get(f"https://www.tikwm.com/api/?url={url}").json()
    return res.get('data')

# --- 2. INSTAGRAM API (VkrDown) ---
def get_instagram(url):
    # API-gan wuxuu dhaafayaa Login-ka (No Login Needed)
    res = requests.get(f"https://api.vkrdown.com/instapost/?url={url}").json()
    return res.get('data')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"): return
    
    msg = await update.message.reply_text("🚀 Jaamacadda Downloader-ka ayaa baaraysa link-ga...")

    # A. TIKTOK LOGIC
    if "tiktok.com" in url:
        data = get_tiktok(url)
        if data and 'images' in data:
            media = [InputMediaPhoto(img) for img in data['images'][:10]]
            await update.message.reply_media_group(media=media)
        elif data and 'play' in data:
            await update.message.reply_video(video=data['play'], caption="✅ TikTok Video!")
        await msg.delete()
        return

    # B. INSTAGRAM LOGIC
    if "instagram.com" in url:
        data = get_instagram(url)
        if data:
            media = []
            for item in data[:10]:
                if item['type'] == 'image': media.append(InputMediaPhoto(item['url']))
                else: media.append(InputMediaVideo(item['url']))
            await update.message.reply_media_group(media=media)
            await msg.delete()
            return

    # C. YOUTUBE / FB / OTHERS (yt-dlp)
    ydl_opts = {'format': 'best', 'outtmpl': 'downloads/%(id)s.%(ext)s', 'quiet': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            f_path = ydl.prepare_filename(info)
            with open(f_path, 'rb') as f:
                await update.message.reply_video(video=f, caption="✅ Soo dejintii waa diyaar!")
            os.remove(f_path)
    except:
        await msg.edit_text("❌ Link-gan lama taageero ama waa Private.")

def main():
    if not os.path.exists('downloads'): os.makedirs('downloads')
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()
    
