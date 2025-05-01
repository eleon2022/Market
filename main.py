# -*- coding: utf-8 -*-
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes

# إعداد السجلات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8190734067:AAFHgihi5tIdoCKiXBxntOgWNBzguCNVzsE"

# حالات المحادثة
LANG_SELECT, MENU_SELECT = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    keyboard = [["العربية", "کوردی"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    text = "أهلاً وسهلاً بكم في بورصة نفط كردستان والعراق!
يرجى اختيار اللغة:"
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
    keyboard = [["🛒 بيع", "📝 طلب شراء"],
                ["📦 عروضي", "📢 العروض"],
                ["♻️ ابدأ من جديد"]]
    if lang == "کوردی":
        keyboard = [["🛒 فرۆشتن", "📝 داواکردنی بەرهەم"],
                    ["📦 پیشکەشەکانم", "📢 پیشکەشەکان"],
                    ["♻️ دەستپێکردنەوە"]]
        msg = "تکایە هەڵبژێرە:"
    else:
        msg = "اختر أحد الخيارات:"
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return MENU_SELECT

async def menu_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "العربية")
    text = update.message.text

    if text in ["♻️ ابدأ من جديد", "♻️ دەستپێکردنەوە"]:
        context.user_data.clear()
        keyboard = [["العربية", "کوردی"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        text = "أهلاً وسهلاً بكم في بورصة نفط كردستان والعراق!
يرجى اختيار اللغة:" if lang == "العربية" else "بەخێربێن بۆ بۆرسەی نەوتی كوردستان و عیراق!
تکایە زمان هەڵبژێرە:"
        await update.message.reply_text(text, reply_markup=reply_markup)
        return LANG_SELECT

    # باقي الأزرار وهمية الآن فقط للعرض
    await update.message.reply_text("قيد التطوير...")
    return MENU_SELECT

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم الإلغاء", reply_markup=ReplyKeyboardRemove())
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
