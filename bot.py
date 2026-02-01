import telebot
import os
import pymongo

# 1. DATABASE CONNECTION
# Link-gaagii MongoDB ee IP-giisa la oggolaaday
MONGO_LINK = "mongodb+srv://spprtshaafici_db_user:bbVaC28CI5sCffU4@cluster0.33hdtdi.mongodb.net/?retryWrites=true&w=majority"
client = pymongo.MongoClient(MONGO_LINK)
db = client['shafici_bot_db']
users_col = db['registered_users']

# 2. BOT LOGIC
# Railway-ga waxaad 'BOT_TOKEN' ku daraysaa qaybta "Variables"
API_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    try:
        if not users_col.find_one({"uid": message.from_user.id}):
            users_col.insert_one({"uid": message.from_user.id, "name": message.from_user.first_name})
    except: pass
    bot.reply_to(message, "Bot-kaagu hadda waa Live Railway! 🚀")

# 3. RUNNING
if __name__ == "__main__":
    print("Bot is starting on Railway...")
    bot.infinity_polling()
    
