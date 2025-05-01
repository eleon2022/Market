# -*- coding: utf-8 -*-
import logging
import json
import time

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes

# تهيئة السجلّات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8190734067:AAFHgihi5tIdoCKiXBxntOgWNBzguCNVzsE"
OFFERS_FILE = "offers.json"

LANG_SELECT, MENU_SELECT = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء المحادثة مع اختيار اللغة وعرض القائمة الرئيسية."""
    context.user_data.clear()
    lang_keyboard = [["العربية", "کوردی"]]
    reply_markup = ReplyKeyboardMarkup(lang_keyboard, one_time_keyboard=True, resize_keyboard=True)
    text = "أهلاً وسهلاً بكم في بورصة نفط كردستان والعراق!
يرجى اختيار اللغة:"
    await update.message.reply_text(text, reply_markup=reply_markup)
    return LANG_SELECT

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تعيين اللغة المختارة وعرض القائمة الرئيسية."""
    lang = update.message.text
    if lang not in ["العربية", "کوردی"]:
        return LANG_SELECT
    context.user_data["lang"] = lang

    keyboard = [["🛒 بيع", "📝 طلب شراء"], ["📦 عروضي", "📢 العروض"], ["♻️ ابدأ من جديد"]]
    if lang == "کوردی":
        keyboard = [["🛒 فرۆشتن", "📝 داواکردنی بەرهەم"], ["📦 پیشکەشەکانم", "📢 پیشکەشەکان"], ["♻️ دەستپێکردنەوە"]]
        msg = "تکایە هەڵبژێرە:"
    else:
        msg = "اختر أحد الخيارات:"
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return MENU_SELECT

async def menu_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة زر ابدأ من جديد."""
    text = update.message.text
    if text in ["♻️ ابدأ من جديد", "♻️ دەستپێکردنەوە"]:
        return await start(update, context)
    await update.message.reply_text("ميزة لم تُفعّل بعد.")
    return MENU_SELECT

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم الإلغاء.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANG_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_language)],
            MENU_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu_select)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
