import telebot
import os
import psycopg2 # Aad u muhiim ah

# Waxay ka akhrinaysaa Railway Variables
DB_URL = os.environ.get('DATABASE_URL')
API_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

def setup_db():
    """Tani waxay dhab ahaan ka dhex dhisaysaa table-ka gudaha Railway"""
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (uid BIGINT PRIMARY KEY, name TEXT)")
    conn.commit()
    cursor.close()
    conn.close()

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    try:
        # Xiriirka dhabta ah ee database-ka
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (uid, name) VALUES (%s, %s) ON CONFLICT (uid) DO NOTHING", 
                       (user_id, user_name))
        conn.commit()
        cursor.close()
        conn.close()
        
        bot.reply_to(message, f"Asc {user_name}! ✅ Xogtaada hadda waxay si dhab ah ugu jirtaa PostgreSQL.")
    except Exception as e:
        bot.reply_to(message, f"❌ Khalad xiriirka ah: {e}")

if __name__ == "__main__":
    setup_db()
    bot.infinity_polling()
    
