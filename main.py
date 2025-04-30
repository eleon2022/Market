from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import os, json

TOKEN = os.getenv("TOKEN")  # سيتم إدخاله من Railway كمتغير بيئة

user_step = {}
user_offer = {}

def start(update: Update, context: CallbackContext):
    keyboard = [['أضف عرض'], ['شاهد العروض']]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text("أهلاً بك في سوق النفط والعلف.\nاختر من الخيارات:", reply_markup=markup)

def handle_message(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    text = update.message.text

    if text == 'أضف عرض':
        user_step[chat_id] = 'product'
        user_offer[chat_id] = {}
        update.message.reply_text("أدخل اسم المنتج:")
    
    elif chat_id in user_step:
        step = user_step[chat_id]
        if step == 'product':
            user_offer[chat_id]['product'] = text
            user_step[chat_id] = 'quantity'
            update.message.reply_text("أدخل الكمية:")
        elif step == 'quantity':
            user_offer[chat_id]['quantity'] = text
            user_step[chat_id] = 'price'
            update.message.reply_text("أدخل السعر:")
        elif step == 'price':
            user_offer[chat_id]['price'] = text
            user_step[chat_id] = 'currency'
            update.message.reply_text("أدخل العملة (مثلاً: دينار):")
        elif step == 'currency':
            user_offer[chat_id]['currency'] = text
            user_step[chat_id] = 'phone'
            update.message.reply_text("أدخل رقم الهاتف:")
        elif step == 'phone':
            user_offer[chat_id]['phone'] = text
            save_offer(user_offer[chat_id])
            update.message.reply_text("تم حفظ العرض بنجاح!")
            del user_step[chat_id]
            del user_offer[chat_id]
    elif text == 'شاهد العروض':
        offers = load_offers()
        if not offers:
            update.message.reply_text("لا توجد عروض حالياً.")
        else:
            for offer in offers[-5:]:
                msg = f"المنتج: {offer['product']}\nالكمية: {offer['quantity']}\nالسعر: {offer['price']} {offer['currency']}\nالهاتف: {offer['phone']}"
                update.message.reply_text(msg)
    else:
        update.message.reply_text("اختر خيارًا من القائمة.")

def save_offer(offer):
    try:
        with open('offers.json', 'r') as f:
            offers = json.load(f)
    except:
        offers = []

    offers.append(offer)

    with open('offers.json', 'w') as f:
        json.dump(offers, f, ensure_ascii=False, indent=2)

def load_offers():
    try:
        with open('offers.json', 'r') as f:
            return json.load(f)
    except:
        return []

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
