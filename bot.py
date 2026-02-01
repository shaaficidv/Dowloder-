import telebot
import os
import psycopg2

# 1. DATABASE & BOT CONFIG
# Hubi in magaca Variable-ka ee Railway uu yahay 'DATABASE_URL'
DB_URL = os.environ.get('DATABASE_URL')
API_TOKEN = os.environ.get('BOT_TOKEN') #
bot = telebot.TeleBot(API_TOKEN)

def setup_db():
    """Wuxuu abuurayaa table-ka dadka lagu kaydiyo markii ugu horreysay"""
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS users (uid BIGINT PRIMARY KEY, name TEXT)")
        conn.commit()
        cursor.close()
        conn.close()
        print("Database structure is ready! ✅")
    except Exception as e:
        print(f"Database Setup Error: {e}")

def save_user(user_id, name):
    """Wuxuu kaydinayaa ID-ga iyo magaca qofka cusub"""
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        # 'ON CONFLICT DO NOTHING' waxay ka hortageysaa in qofka laba jeer la kaydiyo
        cursor.execute("INSERT INTO users (uid, name) VALUES (%s, %s) ON CONFLICT (uid) DO NOTHING", 
                       (user_id, name))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error saving user: {e}")

# 2. BOT COMMANDS
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    # Kaydi xogta qofka
    save_user(user_id, user_name)
    
    bot.reply_to(message, f"Asc {user_name}! ✅ Xogtaada waa la kaydiyey, waligeedna ma tirtirmayso.")

@bot.message_handler(commands=['users'])
def count_users(message):
    """Wuxuu tusaayaa tirada dadka ku jira Database-ka"""
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        bot.reply_to(message, f"📊 Tirada dadka bot-ka isticmaalay: {count}")
    except Exception as e:
        bot.reply_to(message, "Cillad ayaa dhacday!")

if __name__ == "__main__":
    setup_db()
    print("Bot is starting on Railway with PostgreSQL...")
    bot.infinity_polling()
    
