import telebot
from telebot import types
import yt_dlp
import os
import json
from flask import Flask
from threading import Thread

# --- إعدادات البوت ---
TOKEN = "7954952627:AAEM7OZahtpHnUhUZqM8RBNlYbjUsyOcTng"
ADMIN_ID = 5524416062 # !!! استبدل هذا الرقم بـ ID حسابك في تليجرام !!!
bot = telebot.TeleBot(TOKEN)

# ملف بسيط لتخزين البيانات (كبديل مؤقت لقاعدة البيانات)
DATA_FILE = "bot_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f: return json.load(f)
    return {"users": [], "groups": []}

def save_data(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f)

# --- سيرفر ويب لـ Render ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Running"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- تسجيل المستخدمين والمجموعات ---
def register(message):
    data = load_data()
    chat_id = message.chat.id
    if message.chat.type == 'private':
        if chat_id not in data["users"]:
            data["users"].append(chat_id)
            save_data(data)
    else:
        if chat_id not in data["groups"]:
            data["groups"].append(chat_id)
            save_data(data)

# --- لوحة التحكم (للمطور فقط) ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        data = load_data()
        stats = (f"📊 **إحصائيات البوت:**\n\n"
                 f"👤 عدد المستخدمين: {len(data['users'])}\n"
                 f"👥 عدد المجموعات: {len(data['groups'])}\n"
                 f"📁 إجمالي النشاط: {len(data['users']) + len(data['groups'])}")
        bot.reply_to(message, stats, parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ هذا الأمر خاص بالمطور فقط.")

# --- القائمة الرئيسية ---
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("📸 إنستغرام", callback_data="inst")
    btn2 = types.InlineKeyboardButton("🎵 تيك توك", callback_data="tk")
    btn3 = types.InlineKeyboardButton("👻 سناب شات", callback_data="snp")
    markup.add(btn1, btn2, btn3)
    return markup

@bot.message_handler(commands=['start'])
def welcome(message):
    register(message)
    welcome_text = f"👋 أهلاً بك يا {message.from_user.first_name}!\n🚀 اختر المنصة للتحميل:"
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu())

# --- معالجة الروابط واختيار النوع ---
@bot.message_handler(func=lambda m: m.text.startswith("http"))
def handle_link(message):
    register(message)
    url = message.text
    if "youtube" in url.lower() or "youtu.be" in url.lower():
        bot.reply_to(message, "⚠️ اليوتيوب غير مدعوم.")
        return

    markup = types.InlineKeyboardMarkup()
    btn_vid = types.InlineKeyboardButton("📹 فيديو", callback_data=f"vid|{url}")
    btn_aud = types.InlineKeyboardButton("🎵 صوت (MP3)", callback_data=f"aud|{url}")
    markup.add(btn_vid, btn_aud)
    
    bot.reply_to(message, "اختر الصيغة المطلوبة:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if "|" in call.data:
        action, url = call.data.split("|")
        bot.edit_message_text("⏳ جاري المعالجة... يرجى الانتظار.", call.message.chat.id, call.message.message_id)
        download_and_send(call.message, url, action)
    elif call.data == "main_menu":
        bot.edit_message_text("🚀 اختر المنصة:", call.message.chat.id, call.message.message_id, reply_markup=main_menu())

# --- دالة التحميل والإرسال ---
def download_and_send(message, url, mode):
    try:
        ydl_opts = {
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'quiet': True,
            'max_filesize': 48 * 1024 * 1024 # 48MB
        }
        
        if mode == "aud":
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]
        else:
            ydl_opts['format'] = 'best'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            if mode == "aud": file_path = file_path.rsplit('.', 1)[0] + ".mp3"

        with open(file_path, 'rb') as f:
            if mode == "vid":
                bot.send_video(message.chat.id, f, caption="✅ تم تحميل الفيديو بنجاح!")
            else:
                bot.send_audio(message.chat.id, f, caption="✅ تم تحميل الصوت بنجاح!")

        if os.path.exists(file_path): os.remove(file_path)
        bot.delete_message(message.chat.id, message.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ خطأ: قد يكون الملف كبيراً جداً أو الرابط غير مدعوم.", message.chat.id, message.message_id)

if __name__ == "__main__":
    if not os.path.exists('downloads'): os.makedirs('downloads')
    Thread(target=lambda: bot.infinity_polling(skip_pending=True)).start()
    run()
