import telebot
import requests
import subprocess
import os
import time
import json
import psycopg2
from telebot import types

# 🔑 CONFIGURATION (Isticmaal Railway Variables)
API_TOKEN = os.environ.get('BOT_TOKEN') # Token-ka dhex geli Railway Settings
DB_URL = os.environ.get('DATABASE_URL') 
bot = telebot.TeleBot(API_TOKEN)

# --- [DATABASE LOGIC - POSTGRESQL] ---
def init_db():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users 
                   (uid TEXT PRIMARY KEY, lang TEXT, last_url TEXT, api_audio TEXT)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS stats 
                   (id INT PRIMARY KEY, total_downloads INT DEFAULT 0)''')
    cur.execute('INSERT INTO stats (id, total_downloads) SELECT 1, 0 WHERE NOT EXISTS (SELECT 1 FROM stats WHERE id = 1)')
    cur.execute('''CREATE TABLE IF NOT EXISTS countries 
                   (country TEXT PRIMARY KEY, count INT DEFAULT 0)''')
    conn.commit()
    cur.close()
    conn.close()

# --- [COMMANDS SYSTEM] ---

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, f"Hi {message.from_user.first_name} I Accepted Only Link (: If You Need Help Thap Content ⭐",
                 reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("Content ⭐", url="https://t.me/Guspirrr")))

@bot.message_handler(commands=['lang'])
def lang_cmd(message):
    uid = str(message.from_user.id)
    # Hubi haddii uu mar hore doortay (Database Query)
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT lang FROM users WHERE uid = %s", (uid,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user and user[0]:
        return bot.reply_to(message, "❌ Mar hore ayaad dooratay wadan! Ma beddeli kartid.")

    markup = types.InlineKeyboardMarkup(row_width=3)
    countries = ["🇸🇴 Somali", "🇺🇸 USA", "🇸🇦 Saudi", "🇹🇷 Turkey", "🇰🇪 Kenya", "🇪🇹 Ethiopia", "🇩🇯 Djibouti", "🇬🇧 UK", "🇮🇹 Italy", "🇫🇷 France"]
    btns = [types.InlineKeyboardButton(c, callback_data=f"set_{c}") for c in countries]
    markup.add(*btns)
    bot.send_message(message.chat.id, "🌍 Choice / County (Permanently):", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('set_'))
def set_lang(call):
    uid = str(call.from_user.id)
    lang = call.data.split('_')[1]
    
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("INSERT INTO users (uid, lang) VALUES (%s, %s) ON CONFLICT (uid) DO UPDATE SET lang = %s", (uid, lang, lang))
    cur.execute("INSERT INTO countries (country, count) VALUES (%s, 1) ON CONFLICT (country) DO UPDATE SET count = countries.count + 1", (lang,))
    conn.commit()
    cur.close()
    conn.close()

    bot.edit_message_text(f"✅ Your country: {lang}\n(Saved Forever!)", call.message.chat.id, call.message.message_id)

@bot.message_handler(commands=['rank'])
def rank_cmd(message):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT country, count FROM countries ORDER BY count DESC LIMIT 10")
    rows = cur.fetchall()
    cur.execute("SELECT total_downloads FROM stats WHERE id = 1")
    total = cur.fetchone()[0]
    cur.close()
    conn.close()

    leaderboard = "🏆Top 10 Active Countries:\n"
    for i, (country, count) in enumerate(rows, 1):
        leaderboard += f"{i}. {country} — {count} users\n"

    bot.reply_to(message, f"{leaderboard}\n📊Global Bot Stats:\n📥 Total Downloads: {total}")

# --- [DOWNLOAD LOGIC] ---

@bot.message_handler(func=lambda message: message.text.startswith("http"))
def handle_link(message):
    url = message.text
    uid = str(message.from_user.id)
    target_msg = bot.send_message(message.chat.id, "💣")

    try:
        res = requests.get(f"https://www.tikwm.com/api/?url={url}", timeout=15).json()
        if res.get('code') == 0:
            data = res['data']
            
            conn = psycopg2.connect(DB_URL)
            cur = conn.cursor()
            cur.execute("INSERT INTO users (uid, last_url, api_audio) VALUES (%s, %s, %s) ON CONFLICT (uid) DO UPDATE SET last_url = %s, api_audio = %s", 
                        (uid, url, data.get('music'), url, data.get('music')))
            cur.execute("UPDATE stats SET total_downloads = total_downloads + 1 WHERE id = 1")
            conn.commit()
            cur.close()
            conn.close()

            try: bot.delete_message(message.chat.id, target_msg.message_id)
            except: pass

            if 'images' in data:
                for img in data['images']: bot.send_photo(message.chat.id, img)
            else:
                markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🎙️ Audio MP3", callback_data="get_audio"))
                bot.send_video(message.chat.id, data['play'], caption="INJOY 🇸🇴 - @Shaaficibot", reply_markup=markup)
            return

        # Fallback for others
        output = f"file_{uid}.mp4"
        subprocess.run(f'yt-dlp --no-playlist -f "b" -o "{output}" "{url}"', shell=True, check=True)
        
        with open(output, 'rb') as f:
            bot.send_video(message.chat.id, f, caption="INJOY 🇸🇴 - @Shaaficibot")
        os.remove(output)

    except Exception:
        bot.edit_message_text("It's Brok Link ! 💔", message.chat.id, target_msg.message_id)

if __name__ == "__main__":
    init_db()
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)
    
