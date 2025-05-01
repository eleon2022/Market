# -*- coding: utf-8 -*-
import logging
import json
import time

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes

# تهيئة السجلّات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8190734067:AAFHgihi5tIdoCKiXBxntOgWNBzguCNVzsE"
OFFERS_FILE = "offers.json"  # اسم ملف تخزين العروض

# قائمة المنتجات (اسم عربي ونظيره الكردي)
PRODUCTS = {
    "⚗️ نافتا": {"ku": "⚗️ نافتا"},
    "⛽ بنزين": {"ku": "⛽ بەنزین"},
    "🔥 كاز فلاش": {"ku": "🔥 گازۆیل فلاش"},
    "🧴 دهن معمل": {"ku": "🧴 ئۆیل کارگە"},
    "✅ فلاوين مواصفات": {"ku": "✅ فلاوین تایبەتمەند"},
    "🏋️ فلاوين قرص": {"ku": "🏋️ فلاوین قەڵەو"}
}

# الوحدات والعملات بالعربي والكردي
UNITS = {"طن": {"ku": "تەن"}, "لتر": {"ku": "لیتر"}}
CURRENCIES = {"دينار": {"ku": "دینار"}, "دولار": {"ku": "دۆلار"}}

# تعريف حالات المحادثة
LANG_SELECT, MENU_SELECT, SELL_PRODUCT, SELL_OCTANE, SELL_QUANTITY, SELL_UNIT, SELL_PRICE, SELL_CURRENCY, SELL_PHONE, SELL_PHOTO, BUY_SELECT = range(11)

def load_offers():
    """قراءة العروض من الملف أو إرجاع قائمة فارغة إذا لم يوجد الملف."""
    try:
        with open(OFFERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_offers(offers):
    """حفظ قائمة العروض في الملف بتنسيق JSON."""
    with open(OFFERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(offers, f, ensure_ascii=False, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء المحادثة مع اختيار اللغة."""
    context.user_data.clear()
    keyboard = [["العربية", "کوردی"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    text = "أهلاً وسهلاً بكم في بورصة نفط كردستان والعراق!\nيرجى اختيار اللغة:"
    await update.message.reply_text(text, reply_markup=reply_markup)
    return LANG_SELECT

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تعيين اللغة المختارة والمتابعة إلى القائمة الرئيسية."""
    lang = update.message.text
    if lang not in ["العربية", "کوردی"]:
        return LANG_SELECT
    context.user_data["lang"] = lang
    return await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض القائمة الرئيسية بناءً على اللغة."""
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
    """معالجة اختيار المستخدم في القائمة الرئيسية."""
    lang = context.user_data.get("lang", "العربية")
    text = update.message.text

    if text in ["🛒 بيع", "🛒 فرۆشتن"]:
        products = list(PRODUCTS.keys())
        if lang == "کوردی":
            products = [PRODUCTS[p]["ku"] for p in PRODUCTS]
        keyboard = [products[i:i+2] for i in range(0, len(products), 2)]
        msg = "اختر نوع المنتج:" if lang == "العربية" else "جۆری بەرهەم هەڵبژێرە:"
        await update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return SELL_PRODUCT

    if text in ["♻️ ابدأ من جديد", "♻️ دەستپێکردنەوە"]:
        return await start(update, context)

    if text in ["📝 طلب شراء", "📝 داواکردنی بەرهەم"]:
        return await buy_start(update, context)

    if text in ["📦 عروضي", "📦 پیشکەشەکانم"]:
        return await my_offers(update, context)

    return MENU_SELECT

async def sell_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تحديد المنتج في المسار الخاص بالبيع."""
    lang = context.user_data.get("lang", "العربية")
    product = update.message.text
    if lang == "کوردی":
        for ar, ku in PRODUCTS.items():
            if product == ku["ku"]:
                product = ar
                break
    context.user_data["product"] = product

    if "بنزين" in product or "بەنزین" in product:
        msg = "أدخل نسبة الأوكتان:" if lang == "العربية" else "رێژەی ئۆکتان بنووسە:"
        await update.message.reply_text(msg)
        return SELL_OCTANE
    else:
        msg = "أدخل الكمية:" if lang == "العربية" else "بڕی بەرهەم بنووسە:"
        await update.message.reply_text(msg)
        return SELL_QUANTITY

async def sell_octane(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة إدخال نسبة الأوكتان (للمنتجات البنزين)."""
    context.user_data["octane"] = update.message.text
    lang = context.user_data.get("lang", "العربية")
    msg = "أدخل الكمية:" if lang == "العربية" else "بڕی بەرهەم بنووسە:"
    await update.message.reply_text(msg)
    return SELL_QUANTITY

async def sell_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إدخال الكمية واختيار الوحدة."""
    context.user_data["quantity"] = update.message.text
    lang = context.user_data.get("lang", "العربية")
    keyboard = [["طن", "لتر"]] if lang == "العربية" else [["تەن", "لیتر"]]
    msg = "اختر الوحدة:" if lang == "العربية" else "یەکەی بەرهەم هەڵبژێرە:"
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return SELL_UNIT

async def sell_unit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اختيار الوحدة وإدخال السعر."""
    context.user_data["unit"] = update.message.text
    lang = context.user_data.get("lang", "العربية")
    msg = "أدخل السعر:" if lang == "العربية" else "نرخی بەرهەم بنووسە:"
    await update.message.reply_text(msg)
    return SELL_PRICE

async def sell_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إدخال السعر واختيار العملة."""
    context.user_data["price"] = update.message.text
    lang = context.user_data.get("lang", "العربية")
    keyboard = [["دينار", "دولار"]] if lang == "العربية" else [["دینار", "دۆلار"]]
    msg = "اختر العملة:" if lang == "العربية" else "جۆری دراو هەڵبژێرە:"
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return SELL_CURRENCY

async def sell_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إدخال العملة ورقم الهاتف."""
    context.user_data["currency"] = update.message.text
    lang = context.user_data.get("lang", "العربية")
    msg = "أدخل رقم الهاتف:" if lang == "العربية" else "ژمارەی تەلەفۆن بنووسە:"
    await update.message.reply_text(msg)
    return SELL_PHONE

async def sell_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إدخال رقم الهاتف وإرسال أو تخطي الصورة."""
    context.user_data["phone"] = update.message.text
    lang = context.user_data.get("lang", "العربية")
    msg = "أرسل صورة المنتج أو اضغط /skip للتخطي:" if lang == "العربية" else "وێنە بنێرە یان /skip بنووسە:"
    await update.message.reply_text(msg)
    return SELL_PHOTO

async def sell_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حفظ صورة المنتج (آخر صورة يتم إرسالها)."""
    context.user_data["photo"] = update.message.photo[-1].file_id
    return await finalize_offer(update, context)

async def skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تخطي رفع الصورة."""
    context.user_data["photo"] = None
    return await finalize_offer(update, context)

async def finalize_offer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حفظ العرض في الملف والإبلاغ عن النجاح."""
    user_id = update.message.from_user.id
    data = context.user_data
    offer = {
        "user_id": user_id,
        "lang": data.get("lang"),
        "product": data.get("product"),
        "octane": data.get("octane"),
        "quantity": data.get("quantity"),
        "unit": data.get("unit"),
        "price": data.get("price"),
        "currency": data.get("currency"),
        "phone": data.get("phone"),
        "photo": data.get("photo"),
        "timestamp": time.time()
    }
    offers = load_offers()
    offers.append(offer)
    save_offers(offers)
    lang = data.get("lang", "العربية")
    msg = "✅ تم حفظ العرض بنجاح!" if lang == "العربية" else "✅ پێشکەشەکە تۆمار کرا!"
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardRemove())
    return await show_main_menu(update, context)

async def buy_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء طلب شراء باختيار المنتج."""
    lang = context.user_data.get("lang", "العربية")
    products = list(PRODUCTS.keys())
    if lang == "کوردی":
        products = [PRODUCTS[p]["ku"] for p in PRODUCTS]
    keyboard = [products[i:i+2] for i in range(0, len(products), 2)]
    msg = "اختر المنتج لعرض العروض:" if lang == "العربية" else "جۆری بەرهەم هەڵبژێرە بۆ پیشکەشەکان:"
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return BUY_SELECT

async def buy_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض العروض المطابقة للمنتج المختار."""
    lang = context.user_data.get("lang", "العربية")
    selected = update.message.text
    if lang == "کوردی":
        for ar, ku in PRODUCTS.items():
            if selected == ku["ku"]:
                selected = ar
                break
    offers = load_offers()
    matched_offers = [o for o in offers if o["product"] == selected]
    if not matched_offers:
        msg = "لا توجد عروض حالياً." if lang == "العربية" else "هیچ پێشکەشێک نییە."
        await update.message.reply_text(msg, reply_markup=ReplyKeyboardRemove())
        return await show_main_menu(update, context)
    for offer in matched_offers:
        message = f"{offer['product']}"
        if offer.get("octane"):
            message += f"\n⛽ أوكتان: {offer['octane']}"
        message += f"\n📦 الكمية: {offer['quantity']} {offer['unit']}"
        message += f"\n💰 السعر: {offer['price']} {offer['currency']}"
        message += f"\n☎️ الهاتف: {offer['phone']}"
        if offer.get("photo"):
            await update.message.reply_photo(offer["photo"], caption=message)
        else:
            await update.message.reply_text(message)
    return await show_main_menu(update, context)

async def my_offers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض جميع العروض التي نشرها المستخدم الحالي."""
    user_id = update.message.from_user.id
    lang = context.user_data.get("lang", "العربية")
    offers = load_offers()
    user_offers = [o for o in offers if o["user_id"] == user_id]
    if not user_offers:
        msg = "لا تملك عروض حالياً." if lang == "العربية" else "هیچ پێشکەشێکت نییە."
        await update.message.reply_text(msg)
        return await show_main_menu(update, context)
    for idx, offer in enumerate(user_offers):
        message = f"🔢 رقم العرض: {idx + 1}\n🛢️ المنتج: {offer['product']}"
        if offer.get("octane"):
            message += f"\n⛽ أوكتان: {offer['octane']}"
        message += f"\n📦 الكمية: {offer['quantity']} {offer['unit']}"
        message += f"\n💰 السعر: {offer['price']} {offer['currency']}"
        message += f"\n☎️ الهاتف: {offer['phone']}"
        button = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ حذف هذا العرض", callback_data=f"delete_{idx}")]
        ])
        if offer.get("photo"):
            await update.message.reply_photo(offer["photo"], caption=message, reply_markup=button)
        else:
            await update.message.reply_text(message, reply_markup=button)
    return MENU_SELECT

async def handle_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف عرض حسب رقم العرض المختار."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    index = int(query.data.split("_")[1])
    offers = load_offers()
    user_offers = [o for o in offers if o["user_id"] == user_id]
    if index < 0 or index >= len(user_offers):
        await query.edit_message_text("العرض غير موجود.")
        return MENU_SELECT
    offer_to_delete = user_offers[index]
    offers.remove(offer_to_delete)
    save_offers(offers)
    await query.edit_message_text("✅ تم حذف العرض.")
    return MENU_SELECT

async def invalid_photo_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع إدخال غير صورة عند طلب الصورة."""
    lang = context.user_data.get("lang", "العربية")
    msg = "يرجى إرسال صورة أو /skip للتخطي." if lang == "العربية" else "تکایە وێنە بنێرە یان /skip بنووسە."
    await update.message.reply_text(msg)
    return SELL_PHOTO

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إلغاء المحادثة والعودة لنهاية الحالة."""
    lang = context.user_data.get("lang", "العربية")
    msg = "تم إلغاء العملية." if lang == "العربية" else "کارەکە وەستا."
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANG_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_language)],
            MENU_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu_select)],
            SELL_PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, sell_product)],
            SELL_OCTANE: [MessageHandler(filters.TEXT & ~filters.COMMAND, sell_octane)],
            SELL_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, sell_quantity)],
            SELL_UNIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, sell_unit)],
            SELL_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, sell_price)],
            SELL_CURRENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, sell_currency)],
            SELL_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, sell_phone)],
            SELL_PHOTO: [
                MessageHandler(filters.PHOTO, sell_photo),
                CommandHandler("skip", skip_photo),
                MessageHandler(filters.TEXT & ~filters.COMMAND, invalid_photo_input)
            ],
            BUY_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, buy_select)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
