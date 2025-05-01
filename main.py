import logging
import json
import time
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token
BOT_TOKEN = "8190734067:AAFHgihi5tIdoCKiXBxntOgWNBzguCNVzsE"
# File to store offers
OFFERS_FILE = 'offers.json'

# Conversation states
(
    LANG_SELECT,
    MENU_SELECT,
    SELL_PRODUCT,
    SELL_OCTANE,
    SELL_QUANTITY,
    SELL_UNIT,
    SELL_PRICE,
    SELL_CURRENCY,
    SELL_PHONE,
    SELL_PHOTO,
    BUY_SELECT
) = range(11)

# Products with emojis and their Kurdish translations
PRODUCTS = {
    "⚗️ نافتا": {"ku": "⚗️ نافتا"},
    "⛽ بنزين": {"ku": "⛽ بەنزین"},
    "🔥 كاز فلاش": {"ku": "🔥 گازۆیل فلاش"},
    "🧴 دهن معمل": {"ku": "🧴 ئۆیل کارگە"},
    "✅ فلاوين مواصفات": {"ku": "✅ فلاوین تایبەتمەند"},
    "🏋️ فلاوين قرص": {"ku": "🏋️ فلاوین قەڵەو"}
}

# Units and currencies with Kurdish translations
UNITS = {"طن": "تەن", "لتر": "لیتر"}
CURRENCIES = {"دينار": "دینار", "دولار": "دۆلار"}

# Messages in Arabic and Kurdish
MESSAGES = {
    "start": {
        "ar": "أهلاً وسهلاً بكم في بورصة نفط كردستان والعراق!\nيرجى اختيار اللغة:",
        "ku": "بەخێربێن بۆ بازاڕی نەوتی کوردستان و عێراق!\nتكایە زمانیەکەت هەڵبژێرە:"
    },
    "menu_prompt": {
        "ar": "✨ اختر أحد الخيارات:",
        "ku": "✨ تکایە هەڵبژێرە:"
    },
    "choose_product": {
        "ar": "🛍️ اختر نوع المنتج:",
        "ku": "🛍️ جۆری بەرهەم هەڵبژێرە:"
    },
    "enter_octane": {
        "ar": "🔢 أدخل نسبة الأوكتان:",
        "ku": "🔢 رێژەی ئۆکتان بنووسە:"
    },
    "enter_quantity": {
        "ar": "📦 أدخل الكمية:",
        "ku": "📦 بڕی بەرهەم بنووسە:"
    },
    "choose_unit": {
        "ar": "📏 اختر الوحدة:",
        "ku": "📏 یەکەی بەرهەم هەڵبژێرە:"
    },
    "enter_price": {
        "ar": "💰 أدخل السعر:",
        "ku": "💰 نرخی بەرهەم بنووسە:"
    },
    "choose_currency": {
        "ar": "💱 اختر العملة:",
        "ku": "💱 جۆری دراو هەڵبژێرە:"
    },
    "enter_phone": {
        "ar": "📱 أدخل رقم الهاتف:",
        "ku": "📱 ژمارەی تەلەفۆن بنووسە:"
    },
    "send_photo": {
        "ar": "📸 أرسل صورة المنتج أو اضغط /skip للتخطي:",
        "ku": "📸 وێنە بنێرە یان وشەی /skip بنووسە:"
    },
    "offer_saved": {
        "ar": "✅ تم حفظ العرض بنجاح!",
        "ku": "✅ پێشکەشەکە تۆمار کرا!"
    },
    "no_offers": {
        "ar": "لا توجد عروض حالياً.",
        "ku": "هیچ پێشکەشێک نییە."
    },
    "no_my_offers": {
        "ar": "لا تملك عروض حالياً.",
        "ku": "هیچ پێشکەشێکت نییە."
    },
    "deleted": {
        "ar": "✅ تم حذف العرض.",
        "ku": "✅ پێشکەشەکە سڕایەوە."
    },
    "cancel": {
        "ar": "تم إلغاء العملية.",
        "ku": "کارەکە وەستا."
    },
    "invalid_photo": {
        "ar": "🚫 يرجى إرسال صورة أو اضغط /skip للتخطي.",
        "ku": "🚫 تکایە وێنەیەک بنێرە یان وشەی /skip بنووسە."
    },
    "choose_buy_product": {
        "ar": "🔍 اختر المنتج لعرض العروض:",
        "ku": "🔍 جۆری بەرهەم هەڵبژێرە بۆ پیشکەشەکان:"
    }
}

def load_offers():
    try:
        with open(OFFERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_offers(offers):
    with open(OFFERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(offers, f, ensure_ascii=False, indent=2)

# Start command handler: ask for language
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    reply_markup = ReplyKeyboardMarkup(
        [["العربية", "کوردی"]], one_time_keyboard=True, resize_keyboard=True
    )
    text = MESSAGES["start"]["ar"]
    await update.message.reply_text(text, reply_markup=reply_markup)
    return LANG_SELECT

# Set language based on user selection
async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    if choice not in ["العربية", "کوردی"]:
        return LANG_SELECT
    context.user_data["lang"] = "ku" if choice == "کوردی" else "ar"
    return await show_main_menu(update, context)

# Show main menu with options
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ar")
    if lang == "ku":
        keyboard = [
            ["🛒 فرۆشتن", "📝 داواکردنی بەرهەم"],
            ["📦 پیشکەشەکانم", "📢 پیشکەشەکان"],
            ["♻️ دەستپێکردنەوە"]
        ]
        msg = MESSAGES["menu_prompt"]["ku"]
    else:
        keyboard = [
            ["🛒 بيع", "📝 طلب شراء"],
            ["📦 عروضي", "📢 العروض"],
            ["♻️ ابدأ من جديد"]
        ]
        msg = MESSAGES["menu_prompt"]["ar"]
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return MENU_SELECT

# Handle menu selection
async def menu_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ar")
    text = update.message.text

    # Sell option
    if text in ["🛒 بيع", "🛒 فرۆشتن"]:
        if lang == "ku":
            products = [PRODUCTS[p]["ku"] for p in PRODUCTS]
        else:
            products = list(PRODUCTS.keys())
        keyboard = [products[i:i+2] for i in range(0, len(products), 2)]
        await update.message.reply_text(
            MESSAGES["choose_product"][lang],
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return SELL_PRODUCT

    # Start new (restart)
    if text in ["♻️ ابدأ من جديد", "♻️ دەستپێکردنەوە"]:
        return await start(update, context)

    # Buy option (list offers for a product)
    if text in ["📝 طلب شراء", "📝 داواکردنی بەرهەم"]:
        return await buy_start(update, context)

    # My offers
    if text in ["📦 عروضي", "📦 پیشکەشەکانم"]:
        return await my_offers(update, context)

    # All offers
    if text in ["📢 العروض", "📢 پیشکەشەکان"]:
        return await show_all_offers(update, context)

    return MENU_SELECT

# Sell flow: product selection
async def sell_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ar")
    product = update.message.text
    if lang == "ku":
        for ar, ku in PRODUCTS.items():
            if product == ku["ku"]:
                product = ar
                break
    context.user_data["product"] = product

    # If product is gasoline (has octane)
    if "بنزين" in product or "بەنزین" in product:
        await update.message.reply_text(MESSAGES["enter_octane"][lang])
        return SELL_OCTANE
    else:
        await update.message.reply_text(MESSAGES["enter_quantity"][lang])
        return SELL_QUANTITY

async def sell_octane(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["octane"] = update.message.text
    lang = context.user_data.get("lang", "ar")
    await update.message.reply_text(MESSAGES["enter_quantity"][lang])
    return SELL_QUANTITY

async def sell_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["quantity"] = update.message.text
    lang = context.user_data.get("lang", "ar")
    if lang == "ku":
        keyboard = [[UNITS["طن"], UNITS["لتر"]]]
    else:
        keyboard = [["طن", "لتر"]]
    await update.message.reply_text(MESSAGES["choose_unit"][lang],
                                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return SELL_UNIT

async def sell_unit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["unit"] = update.message.text
    lang = context.user_data.get("lang", "ar")
    await update.message.reply_text(MESSAGES["enter_price"][lang])
    return SELL_PRICE

async def sell_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["price"] = update.message.text
    lang = context.user_data.get("lang", "ar")
    if lang == "ku":
        keyboard = [[CURRENCIES["دينار"], CURRENCIES["دولار"]]]
    else:
        keyboard = [["دينار", "دولار"]]
    await update.message.reply_text(MESSAGES["choose_currency"][lang],
                                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return SELL_CURRENCY

async def sell_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["currency"] = update.message.text
    lang = context.user_data.get("lang", "ar")
    await update.message.reply_text(MESSAGES["enter_phone"][lang])
    return SELL_PHONE

async def sell_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text
    lang = context.user_data.get("lang", "ar")
    await update.message.reply_text(MESSAGES["send_photo"][lang])
    return SELL_PHOTO

async def sell_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = update.message.photo[-1].file_id
    context.user_data["photo"] = photo_file
    return await finalize_offer(update, context)

async def skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["photo"] = None
    return await finalize_offer(update, context)

async def invalid_photo_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ar")
    await update.message.reply_text(MESSAGES["invalid_photo"][lang])
    return SELL_PHOTO

# Finalize offer: save data and confirm
async def finalize_offer(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    lang = data.get("lang", "ar")
    await update.message.reply_text(MESSAGES["offer_saved"][lang], reply_markup=ReplyKeyboardRemove())
    return await show_main_menu(update, context)

# Buy flow: choose product to filter offers
async def buy_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ar")
    if lang == "ku":
        products = [PRODUCTS[p]["ku"] for p in PRODUCTS]
    else:
        products = list(PRODUCTS.keys())
    keyboard = [products[i:i+2] for i in range(0, len(products), 2)]
    await update.message.reply_text(MESSAGES["choose_buy_product"][lang],
                                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return BUY_SELECT

async def buy_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ar")
    selected = update.message.text
    if lang == "ku":
        for ar, ku in PRODUCTS.items():
            if selected == ku["ku"]:
                selected = ar
                break
    offers = load_offers()
    matched = [o for o in offers if o.get("product") == selected]
    if not matched:
        await update.message.reply_text(MESSAGES["no_offers"][lang], reply_markup=ReplyKeyboardRemove())
        return await show_main_menu(update, context)

    for offer in matched:
        msg = f"{offer['product']}"
        if offer.get("octane"):
            msg += f"\n⛽ أوكتان: {offer['octane']}"
        msg += f"\n📦 الكمية: {offer['quantity']} {offer['unit']}"
        msg += f"\n💰 السعر: {offer['price']} {offer['currency']}"
        msg += f"\n☎️ الهاتف: {offer['phone']}"
        if offer.get("photo"):
            await update.message.reply_photo(offer["photo"], caption=msg)
        else:
            await update.message.reply_text(msg)
    return await show_main_menu(update, context)

# Show all offers (from all users)
async def show_all_offers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ar")
    offers = load_offers()
    if not offers:
        await update.message.reply_text(MESSAGES["no_offers"][lang], reply_markup=ReplyKeyboardRemove())
        return await show_main_menu(update, context)

    for idx, offer in enumerate(offers, start=1):
        msg = f"🔢 رقم العرض: {idx}\n🛢️ المنتج: {offer['product']}"
        if offer.get("octane"):
            msg += f"\n⛽ أوكتان: {offer['octane']}"
        msg += f"\n📦 الكمية: {offer['quantity']} {offer['unit']}"
        msg += f"\n💰 السعر: {offer['price']} {offer['currency']}"
        msg += f"\n☎️ الهاتف: {offer['phone']}"
        if offer.get("photo"):
            await update.message.reply_photo(offer["photo"], caption=msg)
        else:
            await update.message.reply_text(msg)
    return await show_main_menu(update, context)

# Show offers created by this user
async def my_offers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    lang = context.user_data.get("lang", "ar")
    offers = load_offers()
    my_list = [o for o in offers if o.get("user_id") == user_id]
    if not my_list:
        await update.message.reply_text(MESSAGES["no_my_offers"][lang])
        return await show_main_menu(update, context)

    for idx, offer in enumerate(my_list, start=1):
        msg = f"🔢 رقم العرض: {idx}\n🛢️ المنتج: {offer['product']}"
        if offer.get("octane"):
            msg += f"\n⛽ أوكتان: {offer['octane']}"
        msg += f"\n📦 الكمية: {offer['quantity']} {offer['unit']}"
        msg += f"\n💰 السعر: {offer['price']} {offer['currency']}"
        msg += f"\n☎️ الهاتف: {offer['phone']}"
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ حذف هذا العرض", callback_data=f"delete_{idx-1}")
        ]])
        if offer.get("photo"):
            await update.message.reply_photo(offer["photo"], caption=msg, reply_markup=keyboard)
        else:
            await update.message.reply_text(msg, reply_markup=keyboard)
    return await show_main_menu(update, context)

# Callback handler for deleting an offer
async def handle_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "ar")
    user_id = query.from_user.id
    try:
        index = int(query.data.split("_")[1])
    except:
        await query.edit_message_text("🔴 خطأ في بيانات الزر.")
        return MENU_SELECT
    offers = load_offers()
    user_offers = [o for o in offers if o.get("user_id") == user_id]
    if index < 0 or index >= len(user_offers):
        await query.edit_message_text("❌ العرض غير موجود.")
        return MENU_SELECT
    offer_to_delete = user_offers[index]
    offers.remove(offer_to_delete)
    save_offers(offers)
    await query.edit_message_text(MESSAGES["deleted"][lang])
    return MENU_SELECT

# Fallback /cancel command
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ar")
    await update.message.reply_text(MESSAGES["cancel"][lang], reply_markup=ReplyKeyboardRemove())
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
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(handle_delete_callback, pattern=r"^delete_\d+"))
    app.run_polling()

if __name__ == "__main__":
    main()
