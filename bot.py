import telebot
import requests
import subprocess
import os
import pymongo
from flask import Flask
from threading import Thread

# --- [1. DATABASE CONNECTION] ---
# Link-gaaga MongoDB ee rasmiga ah
MONGO_LINK = "mongodb+srv://spprtshaafici_db_user:bbVaC28CI5sCffU4@cluster0.33hdtdi.mongodb.net/?appName=Cluster0"
client = pymongo.MongoClient(MONGO_LINK)
db = client['shafici_bot_db']
stats_col = db['global_stats']
users_col = db['registered_users']

# --- [2. WEB SERVER SI RENDER UUSAN U DAMIN] ---
# Render wuxuu u baahan yahay Port 8080 si uu "Live" u noqdo
app = Flask('')

@app.route('/')
def home():
    return "Bot is Online 24/7!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- [3. BOT SETUP] ---
API_TOKEN = os.environ.get('BOT_TOKEN') # Ka soo qaado @BotFather
bot = telebot.TeleBot(API_TOKEN)

def update_stats(lang=None):
    if not stats_col.find_one({"id": "main"}):
        stats_col.insert_one({"id": "main", "total": 0, "countries": {}})
    if lang:
        stats_col.update_one({"id": "main"}, {"$inc": {f"countries.{lang}": 1}})
    else:
        stats_col.update_one({"id": "main"}, {"$inc": {"total": 1}})

# COMMANDS
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, f"Hi {message.from_user.first_name}! 🚀\nI am 24/7 Universal Downloader.\n\nSend me any link (TikTok, FB, Pinterest, etc).")

@bot.message_handler(commands=['lang'])
def lang_cmd(message):
    uid = message.from_user.id
    if users_col.find_one({"uid": uid}):
        return bot.reply_to(message, "❌ Mar hore ayaad dooratay wadan!")
    
    markup = telebot.types.InlineKeyboardMarkup(row_width=3)
    countries = ["🇸🇴 Somali", "🇺🇸 USA", "🇸🇦 Saudi", "🇹🇷 Turkey", "🇰🇪 Kenya", "🇩🇯 Djibouti"]
    btns = [telebot.types.InlineKeyboardButton(c, callback_data=f"set_{c}") for c in countries]
    markup.add(*btns)
    bot.send_message(message.chat.id, "🌍 Choice Your Country (Permanently):", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('set_'))
def set_lang(call):
    uid = call.from_user.id
    lang = call.data.split('_')[1]
    if not users_col.find_one({"uid": uid}):
        users_col.insert_one({"uid": uid, "lang": lang})
        update_stats(lang)
        bot.edit_message_text(f"✅ Your country: {lang}\n(Saved to Cloud! ☁️)", call.message.chat.id, call.message.message_id)

@bot.message_handler(commands=['rank'])
def rank_cmd(message):
    data = stats_col.find_one({"id": "main"})
    if not data or 'countries' not in data:
        return bot.reply_to(message, "No data yet.")
    
    sorted_c = sorted(data['countries'].items(), key=lambda x: x[1], reverse=True)[:10]
    rank_text = "🏆 **Top 10 Active Countries:**\n"
    for i, (c, count) in enumerate(sorted_c, 1):
        rank_text += f"{i}. {c} — {count} users\n"
    bot.reply_to(message, f"{rank_text}\n📊 Total Downloads: {data['total']}")

# DOWNLOADER LOGIC
@bot.message_handler(func=lambda message: message.text.startswith("http"))
def handle_link(message):
    url = message.text
    target = bot.send_message(message.chat.id, "🎯 Downloading...")
    try:
        output = f"vid_{message.from_user.id}.mp4"
        # Pinterest iyo kuwa kale fix
        cmd = f'yt-dlp --no-playlist -f "b" -o "{output}" "{url}"'
        subprocess.run(cmd, shell=True, check=True)
        
        update_stats()
        bot.delete_message(message.chat.id, target.message_id)
        
        with open(output, 'rb') as f:
            bot.send_video(message.chat.id, f, caption="INJOY 🇸🇴 - @Shaaficibot")
        os.remove(output)
    except Exception as e:
        bot.delete_message(message.chat.id, target.message_id)
        bot.send_message(message.chat.id, "It's Brok Link or Unsupported! 💔")

# --- [4. RUNNING THE BOT] ---
if __name__ == "__main__":
    keep_alive() # Kani wuxuu Render u sheegayaa inuu nool yahay
    print("Bot is starting on Cloud...")
    bot.infinity_polling() # Infinity polling si uusan u crash-gareyn
