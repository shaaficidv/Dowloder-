import os, requests, yt_dlp, psycopg2
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# --- DATABASE SETUP ---
def init_db():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT PRIMARY KEY, 
        username TEXT, 
        user_downloads INT DEFAULT 0,
        country TEXT DEFAULT 'Unknown',
        lang_selected BOOLEAN DEFAULT FALSE
    )''')
    cur.execute('CREATE TABLE IF NOT EXISTS global_stats (total_downloads INT DEFAULT 0)')
    cur.execute('INSERT INTO global_stats (total_downloads) SELECT 0 WHERE NOT EXISTS (SELECT 1 FROM global_stats)')
    conn.commit()
    cur.close()
    conn.close()

# --- THE UNIVERSAL DOWNLOADER (NATIIJO 100%) ---
async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"): return
    wait = await update.message.reply_text("⚡ Processing...")
    
    kb = [[InlineKeyboardButton("Audio 🎙️", callback_data=f"au_{url}")], [InlineKeyboardButton("Community 🌋", url="https://t.me/cummunutry1")]]

    try:
        # 1. SAWIRADA TIKTOK/IG (Hadii ay sawiro yihiin)
        api_data = requests.get(f"https://www.tikwm.com/api/?url={url}").json().get('data')
        if api_data and 'images' in api_data:
            imgs = [InputMediaPhoto(img) for img in api_data['images'][:10]]
            await update.message.reply_media_group(media=imgs, caption="Downloaded ✅")
            await wait.delete()
            return

        # 2. UNIVERSAL VIDEO (Platform Kasta: IG, YT, FB, etc.)
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'quiet': True,
            'headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0 Safari/537.36'}
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)
            await update.message.reply_video(video=open(path, 'rb'), caption="Done ✅", reply_markup=InlineKeyboardMarkup(kb))
            os.remove(path)
        
        # Stats Update
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cur = conn.cursor()
        cur.execute("UPDATE users SET user_downloads = user_downloads + 1 WHERE user_id = %s", (update.effective_user.id,))
        cur.execute("UPDATE global_stats SET total_downloads = total_downloads + 1")
        conn.commit()
        cur.close()
        conn.close()
        await wait.delete()
    except:
        await wait.edit_text("❌ Error: Link-gan lama dagsan karo hadda.")

# --- COMMANDS: START, LANG, RANK ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_db()
    await update.message.reply_text("Hi! I am a Universal Downloader. Send me ANY link. 🔗")

async def lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    countries = ["Somalia 🇸🇴", "USA 🇺🇸", "UK 🇬🇧", "Kenya 🇰🇪", "Ethiopia 🇪🇹", "Turkey 🇹🇷", "UAE 🇦🇪", "Egypt 🇪🇬", "Canada 🇨🇦", "Norway 🇳🇴", "Sweden 🇸🇪", "Germany 🇩🇪", "France 🇫🇷", "India 🇮🇳", "China 🇨🇳", "Brazil 🇧🇷", "Qatar 🇶🇦", "S.Arabia 🇸🇦", "Djibouti 🇩🇯", "Italy 🇮🇹", "Spain 🇪🇸", "Russia 🇷🇺", "Japan 🇯🇵", "S.Korea 🇰🇷", "Australia 🇦🇺", "Nigeria 🇳🇬", "S.Africa 🇿🇦", "Uganda 🇺🇬", "Tanzania 🇹🇿", "Sudan 🇸🇩", "Pakistan 🇵🇰", "Mexico 🇲🇽", "Finland 🇫🇮", "Denmark 🇩🇰", "Oman 🇴🇲", "Kuwait 🇰🇼", "Yemen 🇾🇪", "Libya 🇱🇾", "Morocco 🇲🇦", "Netherlands 🇳🇱"]
    keyboard = [[InlineKeyboardButton(countries[i], callback_data=f"ln_{countries[i]}"), InlineKeyboardButton(countries[i+1], callback_data=f"ln_{countries[i+1]}")] for i in range(0, len(countries), 2)]
    await update.message.reply_text("Dooro Wadankaaga:", reply_markup=InlineKeyboardMarkup(keyboard))

async def rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    cur.execute("SELECT total_downloads FROM global_stats")
    total_dl = cur.fetchone()[0]
    await update.message.reply_text(f"📊 Global Downloads: {total_dl}")
    cur.close()
    conn.close()

def main():
    if not os.path.exists('downloads'): os.makedirs('downloads')
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("lang", lang))
    app.add_handler(CommandHandler("rank", rank))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_media))
    app.run_polling()

if __name__ == '__main__': main()
    
