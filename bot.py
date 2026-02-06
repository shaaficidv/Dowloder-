import os
import requests
import yt_dlp
import psycopg2
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

# --- COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_db()
    user = update.effective_user
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    cur.execute("INSERT INTO users (user_id, username) VALUES (%s, %s) ON CONFLICT (user_id) DO UPDATE SET username = EXCLUDED.username", (user.id, user.first_name))
    conn.commit()
    cur.close()
    conn.close()
    await update.message.reply_text(f"Welcome {user.first_name}! Send me any link (Video or Photos) from IG, FB, YT, or TikTok. 🔗")

async def lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    cur.execute("SELECT lang_selected FROM users WHERE user_id = %s", (user_id,))
    res = cur.fetchone()
    if res and res[0]:
        await update.message.reply_text("Hore ayaad wadan u dooratay! ⚠️")
        return

    countries = ["Somalia 🇸🇴", "USA 🇺🇸", "UK 🇬🇧", "Kenya 🇰🇪", "Ethiopia 🇪🇹", "Turkey 🇹🇷", "UAE 🇦🇪", "Egypt 🇪🇬", "Canada 🇨🇦", "Norway 🇳🇴", "Sweden 🇸🇪", "Germany 🇩🇪", "France 🇫🇷", "India 🇮🇳", "China 🇨🇳", "Brazil 🇧🇷", "Qatar 🇶🇦", "S.Arabia 🇸🇦", "Djibouti 🇩🇯", "Italy 🇮🇹", "Spain 🇪🇸", "Russia 🇷🇺", "Japan 🇯🇵", "S.Korea 🇰🇷", "Australia 🇦🇺", "Nigeria 🇳🇬", "S.Africa 🇿🇦", "Uganda 🇺🇬", "Tanzania 🇹🇿", "Sudan 🇸🇩", "Pakistan 🇵🇰", "Mexico 🇲🇽", "Finland 🇫🇮", "Denmark 🇩🇰", "Oman 🇴🇲", "Kuwait 🇰🇼", "Yemen 🇾🇪", "Libya 🇱🇾", "Morocco 🇲🇦", "Netherlands 🇳🇱"]
    keyboard = [[InlineKeyboardButton(countries[i], callback_data=f"ln_{countries[i]}"), InlineKeyboardButton(countries[i+1], callback_data=f"ln_{countries[i+1]}")] for i in range(0, len(countries), 2)]
    await update.message.reply_text("Dooro Wadankaaga:", reply_markup=InlineKeyboardMarkup(keyboard))

async def rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    cur.execute("SELECT total_downloads FROM global_stats")
    total_dl = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]
    cur.execute("SELECT user_downloads, country FROM users WHERE user_id = %s", (update.effective_user.id,))
    res = cur.fetchone()
    cur.close()
    conn.close()
    
    text = f"📊 **Bot Stats**\n\n🎥 Total Downloads: {total_dl}\n👤 Total Users: {total_users}\n📥 Your Downloads: {res[0] if res else 0}\n📍 Your Country: {res[1] if res else 'Unknown'}"
    await update.message.reply_text(text, parse_mode='Markdown')

# --- UNIVERSAL DOWNLOADER ---
async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"): return
    wait = await update.message.reply_text("⚡ Processing...")
    
    kb = [[InlineKeyboardButton("Audio 🎙️", callback_data=f"au_{url}")], [InlineKeyboardButton("Community 🌋", url="https://t.me/cummunutry1")]]

    try:
        # 1. PHOTOS & REELS (API Method - TikTok/Instagram)
        api_res = requests.get(f"https://www.tikwm.com/api/?url={url}").json()
        data = api_res.get('data')
        
        if data and 'images' in data:
            imgs = [InputMediaPhoto(img) for img in data['images'][:10]]
            await update.message.reply_media_group(media=imgs, caption="Downloaded Photos 🎁")
            await wait.delete()
        elif data and (data.get('play') or data.get('wmplay')):
            v_url = data.get('play') or data.get('wmplay')
            await update.message.reply_video(video=v_url, caption="Done ✅", reply_markup=InlineKeyboardMarkup(kb))
            await wait.delete()
        else:
            # 2. YT-DLP Method (For everything else: FB, YT, etc.)
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
            await wait.delete()

        # Update Stats
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cur = conn.cursor()
        cur.execute("UPDATE users SET user_downloads = user_downloads + 1 WHERE user_id = %s", (update.effective_user.id,))
        cur.execute("UPDATE global_stats SET total_downloads = total_downloads + 1")
        conn.commit()
        cur.close()
        conn.close()

    except:
        await wait.edit_text("❌ Link Error or Platform not supported.")

# --- CALLBACKS ---
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
    elif query.data.startswith('au_'):
        url = query.data.split('_', 1)[1]
        m = await query.message.reply_text("🎙️ Extracting Audio...")
        ydl_opts = {'format': 'bestaudio/best', 'outtmpl': 'downloads/%(id)s.%(ext)s', 'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                path = ydl.prepare_filename(info).rsplit('.', 1)[0] + ".mp3"
                await query.message.reply_audio(audio=open(path, 'rb'))
                os.remove(path)
            await m.delete()
        except: await m.edit_text("❌ Audio Error.")

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
    
