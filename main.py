
# -*- coding: utf-8 -*-
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes

BOT_TOKEN = "8190734067:AAFHgihi5tIdoCKiXBxntOgWNBzguCNVzsE"
LANG_SELECT, MENU_SELECT = range(2)

# إعداد السجلّات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    keyboard = [["العربية", "کوردی"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    text = "أهلاً وسهلاً بكم في بورصة نفط كردستان والعراق!\nيرجى اختيار اللغة:"
    await update.message.reply_text(text, reply_markup=reply_markup)
    return LANG_SELECT

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = update.message.text
    if lang not in ["العربية", "کوردی"]:
        return LANG_SELECT
    context.user_data["lang"] = lang
    return await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "العربية")
    if lang == "کوردی":
        keyboard = [["🛒 فرۆشتن", "📝 داواکردنی بەرهەم"],
                    ["📦 پیشکەشەکانم", "📢 پیشکەشەکان"],
                    ["♻️ دەستپێکردنەوە"]]
        msg = "تکایە هەڵبژێرە:"
    else:
        keyboard = [["🛒 بيع", "📝 طلب شراء"],
                    ["📦 عروضي", "📢 العروض"],
                    ["♻️ ابدأ من جديد"]]
        msg = "اختر أحد الخيارات:"
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(msg, reply_markup=reply_markup)
    return MENU_SELECT

async def menu_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم اختيار: " + update.message.text)
    return MENU_SELECT

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANG_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_language)],
            MENU_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu_select)],
        },
        fallbacks=[]
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
