import telebot
from telebot import types
import yt_dlp
import os
from flask import Flask
from threading import Thread

# --- إعدادات البوت ---
TOKEN = "7954952627:AAEM7OZahtpHnUhUZqM8RBNlYbjUsyOcTng"
bot = telebot.TeleBot(TOKEN)

# --- سيرفر ويب لـ Render ---
app = Flask('')
@app.route('/')
def home(): return "OK"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 1. الرسالة الترحيبية مع الأزرار ---
@bot.message_handler(commands=['start'])
def welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    # إنشاء الأزرار
    btn2 = types.InlineKeyboardButton("📸 إنستغرام", callback_data="inst")
    btn3 = types.InlineKeyboardButton("🎵 تيك توك", callback_data="tk")
    btn4 = types.InlineKeyboardButton("👻 سناب شات", callback_data="snp")
    
    markup.add(btn1, btn2, btn3, btn4)
    
    welcome_text = (
        f"👋 أهلاً بك يا {message.from_user.first_name} في بوت التحميل الشامل!\n\n"
        "🚀 اختر المنصة التي تريد التحميل منها من الأزرار أدناه:"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

# --- 2. معالجة ضغطات الأزرار ---
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):

    elif call.data == "inst":
        bot.edit_message_text("📥 أرسل الآن رابط فيديو الإنستغرام:", call.message.chat.id, call.message.message_id)
    elif call.data == "tk":
        bot.edit_message_text("📥 أرسل الآن رابط فيديو التيك توك:", call.message.chat.id, call.message.message_id)
    elif call.data == "snp":
        bot.edit_message_text("📥 أرسل الآن رابط فيديو السناب شات:", call.message.chat.id, call.message.message_id)

# --- 3. منطق التحميل الشامل ---
@bot.message_handler(func=lambda m: True)
def download_all(message):
    url = message.text
    # التأكد أن الرابط يحتوي على كلمات من المنصات المدعومة
    platforms = [ "youtu.be", "instagram", "tiktok", "snapchat"]
    if not any(p in url.lower() for p in platforms):
        bot.reply_to(message, "⚠️ الرجاء إرسال رابط صحيح من المنصات المدعومة.")
        return

    msg = bot.reply_to(message, "⏳ جاري المعالجة والتحميل... يرجى الانتظار.")
    
    try:
        # إعدادات yt-dlp الذكية (تدعم أغلب المنصات)
        ydl_opts = {
            'format': 'best[filesize<45M]/best', # محاولة البقاء تحت 45 ميجا
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }

       

        with open(file_path, 'rb') as video:
            bot.send_video(message.chat.id, video, caption="✅ تم التحميل بنجاح!")
        
        if os.path.exists(file_path): os.remove(file_path)
        bot.delete_message(message.chat.id, msg.message_id)

    except Exception as e:
        bot.edit_message_text("❌ فشل التحميل. قد يكون الحجم كبيراً جداً أو الرابط خاصاً.", message.chat.id, msg.message_id)
        print(f"Error: {e}")

# --- التشغيل ---
if __name__ == "__main__":
    if not os.path.exists('downloads'): os.makedirs('downloads')
    Thread(target=lambda: bot.infinity_polling(skip_pending=True)).start()

    run()
