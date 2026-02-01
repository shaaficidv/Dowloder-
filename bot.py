import telebot
import subprocess
import os
import pymongo
from flask import Flask
from threading import Thread

# --- [1. DATABASE CONNECTION] ---
# Link-gaaga MongoDB ee la saxay
MONGO_LINK = "mongodb+srv://spprtshaafici_db_user:bbVaC28CI5sCffU4@cluster0.33hdtdi.mongodb.net/?retryWrites=true&w=majority"
client = pymongo.MongoClient(MONGO_LINK)
db = client['shafici_bot_db']
users_col = db['registered_users']

# --- [2. WEB SERVER SI RENDER UUSAN U DAMIN] ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is Online 24/7!"

def run():
    # Render wuxuu u baahan yahay inuu Port ka helo halkan
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- [3. AMMAANKA TOKEN-KA] ---
# Token-ka ka soo qaado Render Environment Variables
API_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

# Geli ID-gaaga Telegram
ADMIN_ID = 123456789 

# --- [4. COMMANDS] ---
@bot.message_handler(commands=['start'])
def start(message):
    if not users_col.find_one({"uid": message.from_user.id}):
        users_col.insert_one({"uid": message.from_user.id, "name": message.from_user.first_name})
    bot.reply_to(message, f"Hi {message.from_user.first_name}! 🚀\nI am 24/7 Universal Downloader.")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id == ADMIN_ID:
        msg_text = message.text.replace('/broadcast ', '')
        users = users_col.find()
        success = 0
        for user in users:
            try:
                bot.send_message(user['uid'], msg_text)
                success += 1
            except: pass
        bot.send_message(message.chat.id, f"📢 Broadcast Finished: {success} users reached.")

# --- [5. DOWNLOADER LOGIC] ---
@bot.message_handler(func=lambda message: message.text.startswith("http"))
def handle_link(message):
    url = message.text
    target = bot.send_message(message.chat.id, "🎯 Downloading...")
    try:
        output = f"vid_{message.from_user.id}.mp4"
        cmd = f'yt-dlp --no-playlist -f "b" -o "{output}" "{url}"'
        subprocess.run(cmd, shell=True, check=True)
        
        bot.delete_message(message.chat.id, target.message_id)
        with open(output, 'rb') as f:
            bot.send_video(message.chat.id, f, caption="INJOY 🇸🇴 - @Shaaficibot")
        os.remove(output)
    except:
        bot.delete_message(message.chat.id, target.message_id)
        bot.send_message(message.chat.id, "Error: Link-ga waa khaldan yahay! 💔")

# --- [6. RUNNING] ---
if __name__ == "__main__":
    keep_alive() # Kani wuxuu furayaa Port-ka Render uu rabo
    print("Bot is starting on Render...")
    bot.infinity_polling()
    
