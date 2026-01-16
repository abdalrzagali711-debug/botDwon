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

# --- دالة إنشاء القائمة الرئيسية ---
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    # تم حذف زر اليوتيوب بناءً على طلبك
    btn1 = types.InlineKeyboardButton("📸 إنستغرام", callback_data="inst")
    btn2 = types.InlineKeyboardButton("🎵 تيك توك", callback_data="tk")
    btn3 = types.InlineKeyboardButton("👻 سناب شات", callback_data="snp")
    markup.add(btn1, btn2, btn3)
    return markup

# --- 1. الرسالة الترحيبية ---
@bot.message_handler(commands=['start'])
def welcome(message):
    welcome_text = (
        f"👋 أهلاً بك يا {message.from_user.first_name}!\n\n"
        "🚀 اختر المنصة التي تريد التحميل منها:"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu())

# --- 2. معالجة الأزرار والرجوع ---
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == "main_menu":
        # زر الرجوع للقائمة الرئيسية
        bot.edit_message_text("🚀 اختر المنصة التي تريد التحميل منها:", 
                              call.message.chat.id, call.message.message_id, 
                              reply_markup=main_menu())
    else:
        # عند اختيار منصة، تظهر رسالة طلب الرابط مع زر الرجوع
        back_markup = types.InlineKeyboardMarkup()
        back_markup.add(types.InlineKeyboardButton("⬅️ رجوع للقائمة الرئيسية", callback_data="main_menu"))
        
        platforms = {"inst": "إنستغرام", "tk": "تيك توك", "snp": "سناب شات"}
        bot.edit_message_text(f"📥 أرسل الآن رابط {platforms[call.data]}:", 
                              call.message.chat.id, call.message.message_id, 
                              reply_markup=back_markup)

# --- 3. منطق التحميل الشامل (بدون يوتيوب) ---
@bot.message_handler(func=lambda m: True)
def download_logic(message):
    url = message.text
    # التحقق من أن الرابط ليس يوتيوب
    if "youtube" in url.lower() or "youtu.be" in url.lower():
        bot.reply_to(message, "⚠️ عذراً، تحميل اليوتيوب غير مدعوم في هذا البوت.")
        return

    msg = bot.reply_to(message, "⏳ جاري التحميل... يرجى الانتظار.")
    try:
        ydl_opts = {
            'format': 'best[filesize<48M]/best',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'quiet': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        with open(file_path, 'rb') as video:
            bot.send_video(message.chat.id, video, caption="✅ تم التحميل بنجاح!")
        
        if os.path.exists(file_path): os.remove(file_path)
        bot.delete_message(message.chat.id, msg.message_id)

    except Exception as e:
        bot.edit_message_text("❌ فشل التحميل. تأكد من أن الرابط صحيح وحجمه أقل من 50MB.", 
                              message.chat.id, msg.message_id)

# --- التشغيل ---
if __name__ == "__main__":
    if not os.path.exists('downloads'): os.makedirs('downloads')
    Thread(target=lambda: bot.infinity_polling(skip_pending=True)).start()
    run()
