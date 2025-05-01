from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import os

# استدعاء التوكن من متغير البيئة
TOKEN = os.getenv("TOKEN")

# إنشاء الخطوات والبيانات المؤقتة
user_step = {}
user_data = {}

# رسالة الترحيب
def start(update: Update, context: CallbackContext):
    keyboard = [['أضف عرض'], ['شاهد العروض'], ['ابدأ من جديد']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text(
        "أهلاً وسهلاً بكم في السوق المفتوح في كردستان والعراق!\n"
        "يمكنك إضافة عرض جديد أو مشاهدة العروض الحالية.",
        reply_markup=reply_markup
    )
    user_step[update.message.chat_id] = None

# التعامل مع الرسائل العامة
def handle_message(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    text = update.message.text

    if text == "أضف عرض":
        user_step[chat_id] = "product_name"
        user_data[chat_id] = {}
        update.message.reply_text("يرجى كتابة اسم المنتج:")
    
    elif text == "شاهد العروض":
        update.message.reply_text("سيتم عرض العروض قريباً...")
    
    elif text == "ابدأ من جديد":
        user_step[chat_id] = None
        user_data[chat_id] = {}
        update.message.reply_text("تمت إعادة التهيئة. يمكنك البدء من جديد باستخدام الأزرار.")

    else:
        step = user_step.get(chat_id)
        if step == "product_name":
            user_data[chat_id]["product"] = text
            update.message.reply_text("المنتج تم تسجيله. سيتم الآن استكمال باقي البيانات...")
            # الخطوات التالية ستضاف لاحقًا

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
