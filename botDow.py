import telebot
from telebot import types
import yt_dlp
import os
import pymongo
from flask import Flask
from threading import Thread

# --- إعدادات البوت وقاعدة البيانات ---
TOKEN = "7954952627:AAETV9wdZFQSmNAfZYpbKg8RiGu1OW-yreI"
MONGO_URI = "mongodb+srv://abdalrzagDB:10010207966##@cluster0.fighoyv.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
ADMIN_ID = 5524416062 

bot = telebot.TeleBot(TOKEN)

# الاتصال بـ MongoDB مع معالجة الأخطاء
try:
    client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client["VideoDownloader_Bot"] 
    users_col = db["users"]
    groups_col = db["groups"]
except Exception as e:
    print(f"MongoDB Error: {e}")

# --- سيرفر ويب لـ Render لضمان بقاء البوت حياً ---
app = Flask('')
@app.route('/')
def home(): return "البوت يعمل بنجاح ✅"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- نظام تسجيل المستخدمين (محسن) ---
def register(message):
    try:
        chat_id = message.chat.id
        if message.chat.type == 'private':
            if not users_col.find_one({"user_id": chat_id}):
                users_col.insert_one({
                    "user_id": chat_id, 
                    "first_name": message.from_user.first_name,
                    "username": message.from_user.username
                })
    except:
        pass # لضمان استمرار البوت حتى لو تعطلت قاعدة البيانات

# --- لوحة تحكم المطور ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        try:
            u_count = users_col.count_documents({})
            g_count = groups_col.count_documents({})
            stats = (f"📊 إحصائيات البوت:\n\n👤 المستخدمين: {u_count}\n👥 المجموعات: {g_count}")
            bot.reply_to(message, stats)
        except:
            bot.reply_to(message, "خطأ في الاتصال بقاعدة البيانات.")
    else:
        bot.reply_to(message, "❌ هذا الأمر للمطور فقط.")

# --- القائمة الترحيبية (تعمل للجميع) ---
@bot.message_handler(commands=['start'])
def welcome(message):
    register(message)
    welcome_text = f"👋 أهلاً بك يا {message.from_user.first_name}!\n\n🚀 أنا بوت تحميل المقاطع، أرسل لي رابطاً من (تيك توك، إنستقرام، سناب) وسأقوم بمعالجته فوراً."
    bot.send_message(message.chat.id, welcome_text)

# --- رد فوري للفحص ---
@bot.message_handler(func=lambda m: m.text == "فحص")
def test_bot(message):
    bot.reply_to(message, "أنا أسمعك! البوت شغال تمام ويرد على الجميع ✅")

# --- معالجة الروابط واختيار النوع ---
@bot.message_handler(func=lambda m: m.text and (m.text.startswith("http") or "www." in m.text))
def handle_link(message):
    register(message)
    url = message.text.strip()
    
    if "youtube" in url.lower() or "youtu.be" in url.lower():
        bot.reply_to(message, "⚠️ اليوتيوب محظور حالياً لتجنب حظر السيرفر.")
        return

    markup = types.InlineKeyboardMarkup()
    btn_vid = types.InlineKeyboardButton("📹 تحميل فيديو", callback_data=f"vid|{url}")
    btn_aud = types.InlineKeyboardButton("🎵 تحميل صوت", callback_data=f"aud|{url}")
    markup.add(btn_vid, btn_aud)
    
    bot.reply_to(message, "ممتاز! ماذا تريد أن أفعل بهذا الرابط؟", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: "|" in call.data)
def download_callback(call):
    mode, url = call.data.split("|")
    bot.edit_message_text("⏳ جاري التحميل... قد يستغرق الأمر دقيقة حسب حجم الملف.", call.message.chat.id, call.message.message_id)
    
    ydl_opts = {
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    if mode == "aud":
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]
        })
    else:
        ydl_opts['format'] = 'best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            if mode == "aud": 
                file_path = file_path.rsplit('.', 1)[0] + ".mp3"
            
            with open(file_path, 'rb') as f:
                if mode == "vid":
                    bot.send_video(call.message.chat.id, f, caption="✅ تم التحميل بنجاح!")
                else:
                    bot.send_audio(call.message.chat.id, f, caption="✅ تم تحويل الصوت!")

        if os.path.exists(file_path): 
            os.remove(file_path)
        bot.delete_message(call.message.chat.id, call.message.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ حدث خطأ غير متوقع. جرب رابطاً آخر.", call.message.chat.id, call.message.message_id)

# --- تشغيل البوت النهائي ---
if __name__ == "__main__":
    if not os.path.exists('downloads'): 
        os.makedirs('downloads')
    
    # حذف أي ويب هوك قديم يسبب التعليق
    bot.remove_webhook()
    
    Thread(target=run).start()
    print("البوت بدأ العمل...")
    bot.infinity_polling(skip_pending=True)
