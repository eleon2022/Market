from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes

# States
SELECT_LANG, MAIN_MENU, PRODUCT, DENSITY, SULFUR, PRICE, CURRENCY, CONTACT, PHOTO = range(9)

# Data storage for listings
sale_offers = []
purchase_requests = []

# Keyboards
language_keyboard = ReplyKeyboardMarkup([["العربية", "الكردية"]], one_time_keyboard=True, resize_keyboard=True)
main_menu_keyboard = ReplyKeyboardMarkup([["🛢️ عرض بيع جديد", "🛒 طلب شراء جديد"], ["📜 عروض البيع", "📜 طلبات الشراء"]], resize_keyboard=True)
currency_keyboard = ReplyKeyboardMarkup([["دولار $", "دينار عراقي"], ["دينار كويتي", "يورو"]], one_time_keyboard=True, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("اختر اللغة:", reply_markup=language_keyboard)
    return SELECT_LANG

async def select_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = update.message.text
    context.user_data['lang'] = lang
    if lang == "العربية":
        text = "تم اختيار اللغة العربية."
    else:
        text = "زمانی کوردی هەڵبژێردرا."
    await update.message.reply_text(text)
    await update.message.reply_text("اختر من القائمة التالية:", reply_markup=main_menu_keyboard)
    return MAIN_MENU

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if text == "🛢️ عرض بيع جديد":
        context.user_data['listing_type'] = 'sell'
        context.user_data['listing'] = {}
        await update.message.reply_text("اختر المنتج:", reply_markup=ReplyKeyboardMarkup([["بنزين 80", "بنزين 91", "بنزين 95"], ["ديزل", "نفط خام", "نفط مُكرر"]], one_time_keyboard=True, resize_keyboard=True))
        return PRODUCT
    elif text == "🛒 طلب شراء جديد":
        context.user_data['listing_type'] = 'buy'
        context.user_data['listing'] = {}
        await update.message.reply_text("اختر المنتج:", reply_markup=ReplyKeyboardMarkup([["بنزين 80", "بنزين 91", "بنزين 95"], ["ديزل", "نفط خام", "نفط مُكرر"]], one_time_keyboard=True, resize_keyboard=True))
        return PRODUCT
    elif text == "📜 عروض البيع":
        if not sale_offers:
            await update.message.reply_text("لا توجد عروض بيع حالياً.")
        else:
            for off in sale_offers:
                msg = f"عرض بيع:\nالمنتج: {off['product']}\nنسبة الطواف: {off['density']}\nنسبة الكبريت: {off['sulfur']}\nالسعر: {off['price']} {off['currency']}\nرقم الهاتف: {off['contact']}"
                if off.get('photo'):
                    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=off['photo'], caption=msg)
                else:
                    await update.message.reply_text(msg)
        await update.message.reply_text("اختر من القائمة التالية:", reply_markup=main_menu_keyboard)
        return MAIN_MENU
    elif text == "📜 طلبات الشراء":
        if not purchase_requests:
            await update.message.reply_text("لا توجد طلبات شراء حالياً.")
        else:
            for req in purchase_requests:
                msg = f"طلب شراء:\nالمنتج: {req['product']}\nنسبة الطواف: {req['density']}\nنسبة الكبريت: {req['sulfur']}\nالسعر: {req['price']} {req['currency']}\nرقم الهاتف: {req['contact']}"
                if req.get('photo'):
                    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=req['photo'], caption=msg)
                else:
                    await update.message.reply_text(msg)
        await update.message.reply_text("اختر من القائمة التالية:", reply_markup=main_menu_keyboard)
        return MAIN_MENU
    else:
        await update.message.reply_text("يرجى اختيار خيار من القائمة.", reply_markup=main_menu_keyboard)
        return MAIN_MENU

async def product_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    product = update.message.text
    context.user_data['listing']['product'] = product
    await update.message.reply_text("أدخل نسبة الطواف:")
    return DENSITY

async def density_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    density = update.message.text
    context.user_data['listing']['density'] = density
    await update.message.reply_text("أدخل نسبة الكبريت:")
    return SULFUR

async def sulfur_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    sulfur = update.message.text
    context.user_data['listing']['sulfur'] = sulfur
    await update.message.reply_text("أدخل السعر:")
    return PRICE

async def price_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    price = update.message.text
    context.user_data['listing']['price'] = price
    await update.message.reply_text("اختر العملة:", reply_markup=currency_keyboard)
    return CURRENCY

async def currency_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    currency = update.message.text
    context.user_data['listing']['currency'] = currency
    await update.message.reply_text("أدخل رقم الهاتف:")
    return CONTACT

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    contact = update.message.text
    context.user_data['listing']['contact'] = contact
    await update.message.reply_text("أرسل صورة (اختياري) أو اكتب /skip للتخطي.")
    return PHOTO

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    photo_file = update.message.photo[-1].file_id
    context.user_data['listing']['photo'] = photo_file
    listing = context.user_data['listing']
    if context.user_data['listing_type'] == 'sell':
        sale_offers.append(listing)
    else:
        purchase_requests.append(listing)
    await update.message.reply_text("تم إضافة العرض بنجاح!", reply_markup=main_menu_keyboard)
    return MAIN_MENU

async def skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['listing']['photo'] = None
    listing = context.user_data['listing']
    if context.user_data['listing_type'] == 'sell':
        sale_offers.append(listing)
    else:
        purchase_requests.append(listing)
    await update.message.reply_text("تم إضافة العرض بنجاح!", reply_markup=main_menu_keyboard)
    return MAIN_MENU

def main():
    app = ApplicationBuilder().token("YOUR_BOT_TOKEN").build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECT_LANG: [MessageHandler(filters.Regex("^(العربية|الكردية)$"), select_language)],
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu)],
            PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_handler)],
            DENSITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, density_handler)],
            SULFUR: [MessageHandler(filters.TEXT & ~filters.COMMAND, sulfur_handler)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, price_handler)],
            CURRENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, currency_handler)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_handler)],
            PHOTO: [
                MessageHandler(filters.PHOTO, photo_handler),
                CommandHandler('skip', skip_photo)
            ],
        },
        fallbacks=[CommandHandler('start', start)]
    )
    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == '__main__':
    main()
