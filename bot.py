import telebot
import os
import pymongo
from telebot import types

# --- [1. DATABASE CONNECTION] ---
# Waxaan isticmaalaynaa link-ga Standard si looga fogaado DNS Error-ka
MONGO_LINK = "mongodb://spprtshaafici_db_user:BbVaC28CI5oCfFU4@cluster0-shard-00-00.33hdtdi.mongodb.net:27017,cluster0-shard-00-01.33hdtdi.mongodb.net:27017,cluster0-shard-00-02.33hdtdi.mongodb.net:27017/?ssl=true&replicaSet=atlas-m0-shard-0&authSource=admin&retryWrites=true&w=majority"

try:
    client = pymongo.MongoClient(MONGO_LINK, serverSelectionTimeoutMS=5000)
    db = client['shafici_bot_db']
    users_col = db['registered_users']
    # Hubi xiriirka
    client.server_info()
    print("✅ MongoDB Connected Successfully!")
except Exception as e:
    print(f"❌ MongoDB Connection Error: {e}")

# --- [2. BOT CONFIGURATION] ---
# Token-ka wuxuu ka imaanayaa Railway Variables
API_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

# --- [3. BOT COMMANDS] ---

# Command-ga /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    # Is-diiwaangelin otomaatik ah
    try:
        if not users_col.find_one({"uid": user_id}):
            users_col.insert_one({"uid": user_id, "name": user_name})
            print(f"New User Registered: {user_name}")
    except:
        pass
        
    welcome_text = (
        f"Asc {user_name}! 👋\n\n"
        "Kusoo dhawoow Bot-ka 24/7 Downloader-ka ah.\n"
        "Fariintaada waa la helay, Database-kana waa lagu kaydiyey! ✅"
    )
    bot.reply_to(message, welcome_text)

# Command-ga /users (Admin kaliya ayaa arki kara nambarada dadka diiwaangashan)
@bot.message_handler(commands=['users'])
def show_users(message):
    try:
        count = users_col.count_documents({})
        bot.reply_to(message, f"📊 Tirada dadka isticmaalay bot-ka: {count}")
    except Exception as e:
        bot.reply_to(message, "Error ma heli karo tirada dadka.")

# --- [4. MESSAGE HANDLER] ---
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "Fariintaada waa la helay! Bot-kaagu hadda waa Live Railway. 🚀")

# --- [5. RUNNING THE BOT] ---
if __name__ == "__main__":
    print("Bot is starting on Railway...")
    # Infinity polling wuxuu ka dhigayaa bot-ka mid aan damin
    bot.infinity_polling()
    
