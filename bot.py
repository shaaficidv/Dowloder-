import telebot
import os
import pymongo
from flask import Flask
from threading import Thread

# DATABASE CONNECTION
# Link-gan wuxuu ka hortagaa DNS Error-ka kugu dhacay
MONGO_LINK = "mongodb+srv://spprtshaafici_db_user:bbVaC28CI5sCffU4@cluster0.33hdtdi.mongodb.net/?retryWrites=true&w=majority"
client = pymongo.MongoClient(MONGO_LINK)
db = client['shafici_bot_db']
users_col = db['registered_users']

# WEB SERVER SI PORT-KA LOO FURO
app = Flask('')

@app.route('/')
def home():
    return "Bot is Online!"

def run():
    # Render wuxuu u baahan yahay Port-kan
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# BOT LOGIC
API_TOKEN = os.environ.get('BOT_TOKEN') # Hubi inuu Render Environment ugu jiro
bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    try:
        if not users_col.find_one({"uid": message.from_user.id}):
            users_col.insert_one({"uid": message.from_user.id, "name": message.from_user.first_name})
    except: pass
    bot.reply_to(message, "Bot-kaagu waa shaqaynayaa! ✅")

if __name__ == "__main__":
    keep_alive() # Port Binding fix
    print("Bot is starting...")
    bot.infinity_polling()
    
