from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import os, json

TOKEN = os.getenv("TOKEN")

user_step = {}
user_data = {}

def start(update: Update, context: CallbackContext):
    keyboard = [['أضف عرض'], ['شاهد العروض'], ['ابدأ من جديد']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text(
        "أهلاً وسهلاً بكم في السوق المفتوح في كردستان والعراق!\nاختر من الخيارات التالية:",
        reply_markup=reply_markup
    )
    user_step[update.message.chat_id] = None

def handle_message(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    text = update.message.text

    if text == "أضف عرض":
        user_step[chat_id] = "product"
        user_data[chat_id] = {}
        update.message.reply_text("يرجى كتابة اسم المنتج (مثلاً: كاز، طحين، بيت للإيجار):")
    elif text == "ابدأ من جديد":
        user_step[chat_id] = None
        user_data[chat_id] = {}
        update.message.reply_text("تمت إعادة التهيئة. يمكنك البدء من جديد.")
    elif text == "شاهد العروض":
        show_offers(update)
    else:
        step = user_step.get(chat_id)
        if step == "product":
            user_data[chat_id]["product"] = text
            user_step[chat_id] = "unit"
            keyboard = [["طن", "كغم", "عدد"], ["لتر", "متر", "أخرى"]]
            update.message.reply_text("اختر وحدة الكمية:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        elif step == "unit":
            user_data[chat_id]["unit"] = text
            user_step[chat_id] = "quantity"
            update.message.reply_text("أدخل الكمية:")
        elif step == "quantity":
            user_data[chat_id]["quantity"] = text
            user_step[chat_id] = "currency"
            keyboard = [["دولار", "دينار", "أخرى"]]
            update.message.reply_text("اختر العملة:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        elif step == "currency":
            user_data[chat_id]["currency"] = text
            user_step[chat_id] = "price"
            update.message.reply_text("أدخل السعر:")
        elif step == "price":
            user_data[chat_id]["price"] = text
            user_step[chat_id] = "phone"
            update.message.reply_text("أدخل رقم الهاتف:")
        elif step == "phone":
            user_data[chat_id]["phone"] = text
            user_step[chat_id] = "photo"
            update.message.reply_text("إذا كنت تريد إضافة صورة، أرسلها الآن، أو أرسل 'تخطي'.")
        elif step == "photo":
            if text.lower() == "تخطي":
                save_offer(chat_id, None)
                update.message.reply_text("تم حفظ العرض بدون صورة.")
                reset_user(chat_id)
            else:
                update.message.reply_text("يرجى إرسال الصورة كملف صورة أو اكتب 'تخطي'.")
        else:
            update.message.reply_text("يرجى اختيار أحد الخيارات من القائمة أو الضغط على 'ابدأ من جديد'.")

def handle_photo(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if user_step.get(chat_id) == "photo":
        file_id = update.message.photo[-1].file_id
        save_offer(chat_id, file_id)
        update.message.reply_text("تم حفظ العرض مع الصورة بنجاح.")
        reset_user(chat_id)

def save_offer(chat_id, file_id):
    data = user_data.get(chat_id, {})
    if file_id:
        data["photo"] = file_id
    try:
        with open("offers.json", "r") as f:
            offers = json.load(f)
    except:
        offers = []
    offers.append(data)
    with open("offers.json", "w") as f:
        json.dump(offers, f, ensure_ascii=False, indent=2)

def show_offers(update: Update):
    try:
        with open("offers.json", "r") as f:
            offers = json.load(f)
    except:
        offers = []

    if not offers:
        update.message.reply_text("لا توجد عروض حالياً.")
        return

    for offer in offers[-5:]:
        msg = f"المنتج: {offer.get('product')}\nالكمية: {offer.get('quantity')} {offer.get('unit')}\nالسعر: {offer.get('price')} {offer.get('currency')}\nالهاتف: {offer.get('phone')}"
        if "photo" in offer:
            update.message.bot.send_photo(chat_id=update.message.chat_id, photo=offer["photo"], caption=msg)
        else:
            update.message.reply_text(msg)

def reset_user(chat_id):
    user_step[chat_id] = None
    user_data[chat_id] = {}

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.photo, handle_photo))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
