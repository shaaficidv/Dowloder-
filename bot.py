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
    conn = psycopg2.connect(DATABASE_URL)
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
    user = update.effective_user
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("INSERT INTO users (user_id, username) VALUES (%s, %s) ON CONFLICT (user_id) DO UPDATE SET username = EXCLUDED.username", (user.id, user.first_name))
    conn.commit()
    cur.close()
    conn.close()
    await update.message.reply_text(f"Hi {user.first_name} Send Only Link ; 🔗")

async def lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT lang_selected FROM users WHERE user_id = %s", (user_id,))
    res = cur.fetchone()
    if res and res[0]:
        await update.message.reply_text("Hore ayaad wadan u dooratay, looma oggola mar kale! ⚠️")
        return

    countries = [
        "Somalia 🇸🇴", "USA 🇺🇸", "UK 🇬🇧", "Kenya 🇰🇪", "Ethiopia 🇪🇹", "Turkey 🇹🇷", "UAE 🇦🇪", "Egypt 🇪🇬", "Canada 🇨🇦", "Norway 🇳🇴",
        "Sweden 🇸🇪", "Germany 🇩🇪", "France 🇫🇷", "India 🇮🇳", "China 🇨🇳", "Brazil 🇧🇷", "Qatar 🇶🇦", "S.Arabia 🇸🇦", "Djibouti 🇩🇯", "Italy 🇮🇹",
        "Spain 🇪🇸", "Russia 🇷🇺", "Japan 🇯🇵", "S.Korea 🇰🇷", "Australia 🇦🇺", "Nigeria 🇳🇬", "S.Africa 🇿🇦", "Uganda 🇺🇬", "Tanzania 🇹🇿", "Sudan 🇸🇩",
        "Pakistan 🇵🇰", "Mexico 🇲🇽", "Finland 🇫🇮", "Denmark 🇩🇰", "Oman 🇴🇲", "Kuwait 🇰🇼", "Yemen 🇾🇪", "Libya 🇱🇾", "Morocco 🇲🇦", "Netherlands 🇳🇱"
    ]
    keyboard = [[InlineKeyboardButton(countries[i], callback_data=f"ln_{countries[i]}"), 
                  InlineKeyboardButton(countries[i+1], callback_data=f"ln_{countries[i+1]}")] for i in range(0, len(countries), 2)]
    await update.message.reply_text("Dooro Wadankaaga (Hal mar kaliya):", reply_markup=InlineKeyboardMarkup(keyboard))

async def rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # 1. Total Video Upload (Global)
    cur.execute("SELECT total_downloads FROM global_stats")
    total_dl = cur.fetchone()[0]
    
    # 2. Total Users
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]
    
    # 3. User Stats & Rank
    cur.execute("""
        SELECT user_downloads, country, 
        (SELECT COUNT(*) + 1 FROM users u2 WHERE u2.user_downloads > u1.user_downloads) as my_rank
        FROM users u1 WHERE user_id = %s
    """, (update.effective_user.id,))
    res = cur.fetchone()
    
    # 4. Top 10 Countries
    cur.execute("SELECT country, COUNT(*) FROM users WHERE country != 'Unknown' GROUP BY country ORDER BY COUNT(*) DESC LIMIT 10")
    top_c = cur.fetchall()
    country_list = "\n".join([f"{i+1}. {c[0]}: {c[1]}" for i, c in enumerate(top_c)])
    
    cur.close()
    conn.close()
    
    rank_text = (
        f"📊 **University Downloader Rank**\n\n"
        f"🎥 Total Video Upload: {total_dl}\n"
        f"👤 Total Users: {total_users}\n"
        f"📥 Your Downloads: {res[0] if res else 0}\n"
        f"🏆 Your Rank: #{res[2] if res else '?'}\n"
        f"📍 Country: {res[1] if res else 'Unknown'}\n\n"
        f"🌍 **Top 10 Countries:**\n{country_list if country_list else 'Data is coming...'}"
    )
    await update.message.reply_text(rank_text, parse_mode='Markdown')

# --- CALLBACKS ---
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith('ln_'):
        c = query.data.split('_')[1]
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("UPDATE users SET country = %s, lang_selected = TRUE WHERE user_id = %s", (c, query.from_user.id))
        conn.commit()
        cur.close()
        conn.close()
        await query.edit_message_text(f"Wadankaaga waxaa loo daray: {c} ✅")

# --- CORE DOWNLOADER ---
async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"):
        kb = [[InlineKeyboardButton("Developers - @Guspirrr", url="https://t.me/Guspirrr")]]
        await update.message.reply_text(f"Hi {update.effective_user.first_name} I accepted Only Link 🖤", reply_markup=InlineKeyboardMarkup(kb))
        return

    wait = await update.message.reply_text("🫦")
    kb = [[InlineKeyboardButton("Audio 🎙️", callback_data=f"au_{url}")], [InlineKeyboardButton("Community 🌋", url="https://t.me/cummunutry1")]]

    try:
        if "tiktok.com" in url:
            data = requests.get(f"https://www.tikwm.com/api/?url={url}").json().get('data')
            if 'images' in data:
                imgs = [InputMediaPhoto(i) for i in data['images'][:10]]
                await update.message.reply_media_group(media=imgs, caption="For You 🎁")
            else:
                await update.message.reply_video(video=data.get('play'), caption="For You 🔥", reply_markup=InlineKeyboardMarkup(kb))
        else:
            ydl_opts = {'format': 'best', 'outtmpl': 'downloads/%(id)s.%(ext)s', 'quiet': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                path = ydl.prepare_filename(info)
                await update.message.reply_video(video=open(path, 'rb'), caption="For You 🔥", reply_markup=InlineKeyboardMarkup(kb))
                os.remove(path)
        
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("UPDATE users SET user_downloads = user_downloads + 1 WHERE user_id = %s", (update.effective_user.id,))
        cur.execute("UPDATE global_stats SET total_downloads = total_downloads + 1")
        conn.commit()
        cur.close()
        conn.close()
        await wait.delete()
    except:
        await wait.edit_text("Ist Brok Link ! 🤥")

def main():
    if not os.path.exists('downloads'): os.makedirs('downloads')
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("lang", lang))
    app.add_handler(CommandHandler("rank", rank))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_media))
    app.run_polling()

if __name__ == '__main__': main()
    
