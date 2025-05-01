# -*- coding: utf-8 -*-
import logging
import json
import time
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ConversationHandler, ContextTypes, CallbackQueryHandler
)

# إعداد السجل
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# توكن البوت (يرجى استبداله بالتوكن الحقيقي)
BOT_TOKEN = "YOUR_BOT_TOKEN"

# ملف تخزين العروض
OFFERS_FILE = "offers.json"

# تعريف مراحل المحادثة
(
    LANG_SELECT, MENU_SELECT,
    PRODUCT_NAME, OCTANE_LEVEL, QUANTITY, UNIT, PRICE, CURRENCY, PHONE, TRADER,
    SULFUR, DENSITY, PHOTO
) = range(13)

# الوحدات والعملات
UNITS = ["لتر", "طن"]
CURRENCIES = ["دينار", "دولار"]
PRODUCTS_AR = ["كاز معمل", "نافتا", "بنزين", "كاز فلاش", "دهن معمل", "فلاوين مواصفات", "فلاوين قرص"]
PRODUCTS_KU = ["کاز کارگە", "نافتا", "بەنزین", "کاز فلاش", "ئۆیل کارگە", "فلاوین تایبەتمەند", "فلاوین قورس"]

LANGUAGES = {"العربية": "ar", "کوردی": "ku"}

def load_offers():
    try:
        with open(OFFERS_FILE, "r", encoding="utf-8") as f:
            offers = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        offers = []
    now = time.time()
    offers = [o for o in offers if now - o.get("timestamp", now) < 86400]
    with open(OFFERS_FILE, "w", encoding="utf-8") as f:
        json.dump(offers, f, ensure_ascii=False, indent=2)
    return offers

def save_offer(offer):
    offers = load_offers()
    offers.append(offer)
    with open(OFFERS_FILE, "w", encoding="utf-8") as f:
        json.dump(offers, f, ensure_ascii=False, indent=2)


# بدء البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [["العربية", "کوردی"]]
    await update.message.reply_text(
        "أهلاً وسهلاً بكم في بورصة نفط كردستان والعراق!
يرجى اختيار اللغة:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return LANG_SELECT

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = update.message.text
    if lang in LANGUAGES:
        context.user_data["lang"] = LANGUAGES[lang]
        context.user_data["offers"] = []
        if lang == "ar":
            keyboard = [["🛢️ بيع", "📝 طلب شراء"], ["📦 العروض", "📦 عروضي"], ["🔁 ابدأ من جديد"]]
            msg = "اختر أحد الخيارات:"
        else:
            keyboard = [["🛢️ فرۆشتن", "📝 داواکاری"], ["📦 پیشکەشەکان", "📦 پێشکەشەکانی من"], ["🔁 دەستپێکردنەوە"]]
            msg = "تکایە یەکێک هەلبژێرە:"
        await update.message.reply_text(
            msg,
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return MENU_SELECT
    else:
        await update.message.reply_text("يرجى اختيار لغة صالحة.")
        return LANG_SELECT

# إعادة إلى القائمة
async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await set_language(update, context)

# بدء عملية البيع أو الشراء (نفس الخطوات)
async def start_offer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_type = "sell" if "بيع" in update.message.text or "فرۆشتن" in update.message.text else "buy"
    context.user_data["current_offer"] = {"type": user_type, "timestamp": time.time()}
    lang = context.user_data.get("lang", "ar")
    products = PRODUCTS_AR if lang == "ar" else PRODUCTS_KU
    keyboard = [[p] for p in products]
    msg = "اختر اسم المنتج:" if lang == "ar" else "ناوی بەرهەم هەلبژێرە:"
    await update.message.reply_text(
        msg,
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return PRODUCT_NAME


async def handle_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["current_offer"]["product"] = update.message.text
    if update.message.text == "بنزين" or update.message.text == "بەنزین":
        context.user_data["ask_octane"] = True
        msg = "ما هي نسبة الأوكتان؟" if context.user_data["lang"] == "ar" else "ڕێژەی ئۆکتان چەندە؟"
        await update.message.reply_text(msg)
        return OCTANE_LEVEL
    return await ask_quantity(update, context)

async def handle_octane(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["current_offer"]["octane"] = update.message.text
    return await ask_quantity(update, context)

async def ask_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    msg = "أدخل الكمية المطلوبة:" if context.user_data["lang"] == "ar" else "بڕی داواکراو بنووسە:"
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardRemove())
    return QUANTITY

async def handle_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["current_offer"]["quantity"] = update.message.text
    units = [["لتر", "طن"]] if context.user_data["lang"] == "ar" else [["لیتر", "تەن"]]
    msg = "اختر الوحدة:" if context.user_data["lang"] == "ar" else "یەکە هەلبژێرە:"
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(units, one_time_keyboard=True, resize_keyboard=True))
    return UNIT

async def handle_unit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["current_offer"]["unit"] = update.message.text
    msg = "أدخل السعر:" if context.user_data["lang"] == "ar" else "نرخ بنووسە:"
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardRemove())
    return PRICE

async def handle_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["current_offer"]["price"] = update.message.text
    currencies = [["دينار", "دولار"]] if context.user_data["lang"] == "ar" else [["دینار", "دۆلار"]]
    msg = "اختر العملة:" if context.user_data["lang"] == "ar" else "دراو هەلبژێرە:"
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(currencies, one_time_keyboard=True, resize_keyboard=True))
    return CURRENCY

async def handle_currency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["current_offer"]["currency"] = update.message.text
    msg = "أدخل رقم الهاتف للتواصل:" if context.user_data["lang"] == "ar" else "ژمارەی تەلەفۆن بنووسە:"
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardRemove())
    return PHONE

async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["current_offer"]["phone"] = update.message.text
    msg = "اسم التاجر أو المعمل:" if context.user_data["lang"] == "ar" else "ناوی تاجەر یان کارگە:"
    await update.message.reply_text(msg)
    return TRADER

async def handle_trader(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["current_offer"]["trader"] = update.message.text
    msg = "سلفر (%):" if context.user_data["lang"] == "ar" else "سلفر (%):"
    await update.message.reply_text(msg)
    return SULFUR

async def handle_sulfur(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["current_offer"]["sulfur"] = update.message.text
    msg = "طواف:" if context.user_data["lang"] == "ar" else "طواف:"
    await update.message.reply_text(msg)
    return DENSITY

async def handle_density(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["current_offer"]["density"] = update.message.text
    msg = "أرسل صورة (اختياري)، أو اكتب /skip لتخطي:" if context.user_data["lang"] == "ar" else "وێنە بنێرە (ئەگەر ناتەوێ، بنووسە /skip):"
    await update.message.reply_text(msg)
    return PHOTO

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    photo_file = update.message.photo[-1].file_id if update.message.photo else None
    context.user_data["current_offer"]["photo"] = photo_file
    return await finalize_offer(update, context)

async def skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["current_offer"]["photo"] = None
    return await finalize_offer(update, context)


async def finalize_offer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    offer = context.user_data["current_offer"]
    offer["user_id"] = update.effective_user.id
    offer["timestamp"] = time.time()
    save_offer(offer)

    lang = context.user_data.get("lang", "ar")
    details = f"📦 {'عرض بيع' if offer['type'] == 'sell' else 'طلب شراء'}:
"
    details += f"📌 المنتج: {offer['product']}
"
    if "octane" in offer:
        details += f"⛽ أوكتان: {offer['octane']}
"
    details += f"⚖️ الكمية: {offer['quantity']} {offer['unit']}
"
    details += f"💰 السعر: {offer['price']} {offer['currency']}
"
    details += f"☎️ الهاتف: {offer['phone']}
"
    details += f"🏭 التاجر/المعمل: {offer['trader']}
"
    details += f"🔥 سلفر: {offer['sulfur']}
"
    details += f"💧 طواف: {offer['density']}"

    if offer.get("photo"):
        await update.message.reply_photo(offer["photo"], caption=details)
    else:
        await update.message.reply_text(details)

    return await back_to_menu(update, context)

# عرض العروض حسب النوع
async def show_filtered_offers(update: Update, context: ContextTypes.DEFAULT_TYPE, offer_type=None):
    lang = context.user_data.get("lang", "ar")
    offers = load_offers()
    if offer_type:
        offers = [o for o in offers if o.get("type") == offer_type]
    if not offers:
        msg = "لا توجد عروض حالياً." if lang == "ar" else "هیچ پێشکەشێک نییە."
        await update.message.reply_text(msg)
        return MENU_SELECT
    for offer in offers:
        details = f"📦 {'عرض بيع' if offer['type'] == 'sell' else 'طلب شراء'}:
"
        details += f"📌 المنتج: {offer['product']}
"
        if "octane" in offer:
            details += f"⛽ أوكتان: {offer['octane']}
"
        details += f"⚖️ الكمية: {offer['quantity']} {offer['unit']}
"
        details += f"💰 السعر: {offer['price']} {offer['currency']}
"
        details += f"☎️ الهاتف: {offer['phone']}
"
        details += f"🏭 التاجر/المعمل: {offer['trader']}
"
        details += f"🔥 سلفر: {offer['sulfur']}
"
        details += f"💧 طواف: {offer['density']}"
        if offer.get("photo"):
            await update.message.reply_photo(offer["photo"], caption=details)
        else:
            await update.message.reply_text(details)
    return MENU_SELECT

# عرض العروض الخاصة بالمستخدم فقط
async def show_my_offers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = context.user_data.get("lang", "ar")
    offers = [o for o in load_offers() if o.get("user_id") == user_id]
    if not offers:
        msg = "لا توجد عروض مسجلة باسمك." if lang == "ar" else "هیچ پێشکەشی تایبەتی تۆ نییە."
        await update.message.reply_text(msg)
        return MENU_SELECT
    for offer in offers:
        details = f"📦 {'عرض بيع' if offer['type'] == 'sell' else 'طلب شراء'}:
"
        details += f"📌 المنتج: {offer['product']}
"
        if "octane" in offer:
            details += f"⛽ أوكتان: {offer['octane']}
"
        details += f"⚖️ الكمية: {offer['quantity']} {offer['unit']}
"
        details += f"💰 السعر: {offer['price']} {offer['currency']}
"
        details += f"☎️ الهاتف: {offer['phone']}
"
        details += f"🏭 التاجر/المعمل: {offer['trader']}
"
        details += f"🔥 سلفر: {offer['sulfur']}
"
        details += f"💧 طواف: {offer['density']}"
        if offer.get("photo"):
            await update.message.reply_photo(offer["photo"], caption=details)
        else:
            await update.message.reply_text(details)
    return MENU_SELECT


# دالة الإنهاء
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("تم الإلغاء.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANG_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_language)],
            MENU_SELECT: [
                MessageHandler(filters.Regex("^🛢️ بيع|🛢️ فرۆشتن$"), start_offer),
                MessageHandler(filters.Regex("^📝 طلب شراء|📝 داواکاری$"), start_offer),
                MessageHandler(filters.Regex("^📦 العروض|📦 پیشکەشەکان$"), lambda u, c: show_filtered_offers(u, c, None)),
                MessageHandler(filters.Regex("^📦 عروضي|📦 پێشکەشەکانی من$"), show_my_offers),
                MessageHandler(filters.Regex("^🔁 ابدأ من جديد|🔁 دەستپێکردنەوە$"), back_to_menu)
            ],
            PRODUCT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_product)],
            OCTANE_LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_octane)],
            QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_quantity)],
            UNIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unit)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_price)],
            CURRENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_currency)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone)],
            TRADER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_trader)],
            SULFUR: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sulfur)],
            DENSITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_density)],
            PHOTO: [
                MessageHandler(filters.PHOTO, handle_photo),
                CommandHandler("skip", skip_photo)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
