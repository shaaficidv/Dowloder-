import os
import requests
import yt_dlp
import psycopg2
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, InputMediaAudio
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# --- DATABASE SETUP ---
def init_db():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS stats (
        user_id BIGINT PRIMARY KEY, 
        username TEXT, 
        country TEXT DEFAULT 'Unknown',
        user_downloads INT DEFAULT 0
    )''')
    cur.execute('CREATE TABLE IF NOT EXISTS global_stats (total_downloads INT DEFAULT 0)')
    cur.execute('INSERT INTO global_stats (total_downloads) SELECT 0 WHERE NOT EXISTS (SELECT 1 FROM global_stats)')
    conn.commit()
    cur.close()
    conn.close()

def update_download(user_id, username):
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    cur.execute("INSERT INTO stats (user_id, username, user_downloads) VALUES (%s, %s, 1) ON CONFLICT (user_id) DO UPDATE SET user_downloads = stats.user_downloads + 1", (user_id, username))
    cur.execute("UPDATE global_stats SET total_downloads = total_downloads + 1")
    conn.commit()
    cur.close()
    conn.close()

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(f"Hi {user.first_name} Send Only Link ; 🔗")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Sida loo isticmaalo:\n1. Soo koobi link-ga (TikTok, IG, YT).\n2. Halkan ku soo tuur.\n3. Bot-ka ayaa iskiis u soo dejinaya!")

async def rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    cur.execute("SELECT total_downloads FROM global_stats")
    total = cur.fetchone()[0]
    cur.execute("SELECT user_downloads FROM stats WHERE user_id = %s", (update.effective_user.id,))
    user_res = cur.fetchone()
    user_total = user_res[0] if user_res else 0
    
    # Top 10 Countries (Tusaale ahaan maadaama /lang aan hadda dhiseyno)
    cur.execute("SELECT country, COUNT(*) FROM stats GROUP BY country ORDER BY COUNT(*) DESC LIMIT 10")
    top_countries = cur.fetchall()
    country_text = "\n".join([f"{i+1}. {c[0]}: {c[1]}" for i, c in enumerate(top_countries)])

    text = f"📊 **Rank Statistics**\n\nTotal Upload Videos: {total}\nYour Downloads: {user_total}\n\n🌍 **Top 10 Countries:**\n{country_text}"
    await update.message.reply_text(text, parse_mode='Markdown')

async def lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Somalia 🇸🇴", callback_data='lang_Somalia'), InlineKeyboardButton("USA 🇺🇸", callback_data='lang_USA')],
        [InlineKeyboardButton("UK 🇬🇧", callback_data='lang_UK'), InlineKeyboardButton("Kenya 🇰🇪", callback_data='lang_Kenya')]
        # Waxaad halkan ku dari kartaa ilaa 40 wadan
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Dooro Wadankaaga (Hal mar kaliya):", reply_markup=reply_markup)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith('lang_'):
        country = query.data.split('_')[1]
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cur = conn.cursor()
        cur.execute("UPDATE stats SET country = %s WHERE user_id = %s", (country, query.from_user.id))
        conn.commit()
        cur.close()
        conn.close()
        await query.edit_message_text(f"Wadankaaga waxaa loo daray: {country} ✅")

async def download_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"):
        keyboard = [[InlineKeyboardButton("Developers - @Guspirrr", url="https://t.me/Guspirrr")]]
        await update.message.reply_text(f"Hi {update.effective_user.first_name} I accepted Only Link any Help and Problema Content team 🖤", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    wait_msg = await update.message.reply_text("🫦")
    update_download(update.effective_user.id, update.effective_user.username)

    # Keyboard Buttons
    keyboard = [
        [InlineKeyboardButton("Audio 🎙️", callback_data=f"audio_{url}")],
        [InlineKeyboardButton("Community 🌋", url="https://t.me/cummunutry1")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # TIKTOK SPECIAL (SLIDESHOW & VIDEO)
    if "tiktok.com" in url:
        try:
            res = requests.get(f"https://www.tikwm.com/api/?url={url}").json()
            data = res.get('data')
            if 'images' in data:
                media = [InputMediaPhoto(img) for img in data['images'][:10]]
                await update.message.reply_media_group(media=media, caption="For You 🎁")
                if data.get('music'):
                    await update.message.reply_audio(audio=data['music'], caption="For You 🎁")
                await wait_msg.delete()
                return
            else:
                video_url = data.get('play')
                await update.message.reply_video(video=video_url, caption="For You 🔥 - @Fastdowloder1bot", reply_markup=reply_markup)
                await wait_msg.delete()
                return
        except: pass

    # UNIVERSAL (yt-dlp)
    ydl_opts = {'format': 'best', 'outtmpl': 'downloads/%(id)s.%(ext)s', 'quiet': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            f_path = ydl.prepare_filename(info)
            with open(f_path, 'rb') as f:
                await update.message.reply_video(video=f, caption="For You 🔥 - @Fastdowloder1bot", reply_markup=reply_markup)
            os.remove(f_path)
            await wait_msg.delete()
    except:
        await wait_msg.edit_text("Ist Brok Link ! 🤥")

def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("rank", rank))
    app.add_handler(CommandHandler("lang", lang))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_logic))
    app.run_polling()

if __name__ == '__main__':
    main()
    
