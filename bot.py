import os
import requests
import yt_dlp
import psycopg2
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# --- DATABASE ---
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

# --- COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_db()
    await update.message.reply_text(f"Welcome {update.effective_user.first_name}! Send me ANY link from ANY platform (IG, YT, FB, TikTok, X, etc). 🔗")

async def lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    countries = ["Somalia 🇸🇴", "USA 🇺🇸", "UK 🇬🇧", "Kenya 🇰🇪", "Ethiopia 🇪🇹", "Turkey 🇹🇷", "UAE 🇦🇪", "Egypt 🇪🇬", "Canada 🇨🇦", "Norway 🇳🇴", "Sweden 🇸🇪", "Germany 🇩🇪", "France 🇫🇷", "India 🇮🇳", "China 🇨🇳", "Brazil 🇧🇷", "Qatar 🇶🇦", "S.Arabia 🇸🇦", "Djibouti 🇩🇯", "Italy 🇮🇹", "Spain 🇪🇸", "Russia 🇷🇺", "Japan 🇯🇵", "S.Korea 🇰🇷", "Australia 🇦🇺", "Nigeria 🇳🇬", "S.Africa 🇿🇦", "Uganda 🇺🇬", "Tanzania 🇹🇿", "Sudan 🇸🇩", "Pakistan 🇵🇰", "Mexico 🇲🇽", "Finland 🇫🇮", "Denmark 🇩🇰", "Oman 🇴🇲", "Kuwait 🇰🇼", "Yemen 🇾🇪", "Libya 🇱🇾", "Morocco Mma", "Netherlands 🇳🇱"]
    keyboard = [[InlineKeyboardButton(countries[i], callback_data=f"ln_{countries[i]}"), InlineKeyboardButton(countries[i+1], callback_data=f"ln_{countries[i+1]}")] for i in range(0, len(countries), 2)]
    await update.message.reply_text("Dooro Wadankaaga:", reply_markup=InlineKeyboardMarkup(keyboard))

async def rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    cur.execute("SELECT total_downloads FROM global_stats")
    total_dl = cur.fetchone()[0]
    cur.execute("SELECT user_downloads FROM users WHERE user_id = %s", (update.effective_user.id,))
    res = cur.fetchone()
    cur.close()
    conn.close()
    await update.message.reply_text(f"📊 **Global Downloads:** {total_dl}\n📥 **Your Downloads:** {res[0] if res else 0}")

# --- THE UNIVERSAL ENGINE ---
async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"): return
    wait = await update.message.reply_text("⚡ Processing...")

    # 1. API Method for Fast Results (TikTok/IG Photos)
    try:
        api_res = requests.get(f"https://www.tikwm.com/api/?url={url}").json().get('data')
        if api_res and 'images' in api_res:
            imgs = [InputMediaPhoto(img) for img in api_res['images'][:10]]
            await update.message.reply_media_group(media=imgs, caption="Downloaded ✅")
            await wait.delete()
            return
    except: pass

    # 2. YT-DLP Universal Method (For ALL Platforms)
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)
            kb = [[InlineKeyboardButton("Audio 🎙️", callback_data=f"au_{url}")]]
            await update.message.reply_video(video=open(path, 'rb'), caption="Done ✅", reply_markup=InlineKeyboardMarkup(kb))
            os.remove(path)
        
        # Update Stats
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cur = conn.cursor()
        cur.execute("UPDATE users SET user_downloads = user_downloads + 1 WHERE user_id = %s", (update.effective_user.id,))
        cur.execute("UPDATE global_stats SET total_downloads = total_downloads + 1")
        conn.commit()
        cur.close()
        conn.close()
        await wait.delete()
    except Exception:
        await wait.edit_text("❌ Error: Platform-kan lama dagsan karo hadda.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith('ln_'):
        c = query.data.split('_')[1]
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cur = conn.cursor()
        cur.execute("UPDATE users SET country = %s, lang_selected = TRUE WHERE user_id = %s", (c, query.from_user.id))
        conn.commit()
        cur.close()
        conn.close()
        await query.edit_message_text(f"Wadankaaga: {c} ✅")

def main():
    if not os.path.exists('downloads'): os.makedirs('downloads')
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("lang", lang))
    app.add_handler(CommandHandler("rank", rank))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_media))
    app.run_polling()

if __name__ == '__main__': main()
    
