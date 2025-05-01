from telegram import (
    Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler, CallbackQueryHandler
)
from datetime import datetime
import logging

# تفعيل تسجيل الأحداث
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# قوائم لتخزين العروض (بيع وشراء)
sell_offers = []
buy_requests = []
offer_id_counter = 0  # عداد لإنشاء معرف فريد لكل عرض

# تعريف مراحل المحادثة
LANGUAGE, MAIN_MENU = range(2)
SELL_PRODUCT, SELL_OCTANE, SELL_QTY, SELL_UNIT, SELL_PRICE, SELL_CURRENCY, SELL_PHONE, SELL_IMAGE = range(2, 10)
BUY_PRODUCT, BUY_OCTANE, BUY_QTY, BUY_UNIT, BUY_PRICE, BUY_CURRENCY, BUY_PHONE, BUY_IMAGE = range(10, 18)

# قائمة المنتجات (بنفس الأسماء بالعربية والكردية)
PRODUCTS = ["بنزين", "كاز فلاش", "كاز معمل", "نافتا", "دهن معمل", "فلاوين", "فلاوين مواصفات", "نفط خام"]

# قاموس ترجمة النصوص (العربية والكردية)
text = {
    "choose_language": {"ar": "اختر اللغة:\nزمانەکەت هەڵبژێرە:", "ku": "تکایه زمانەکەت هەڵبژێرە:"},
    "language_ar":    {"ar": "العربية", "ku": "عەرەبی"},
    "language_ku":    {"ar": "الكردية", "ku": "کوردی"},
    "sell":           {"ar": "بيع", "ku": "فرۆشتن"},
    "buy_request":    {"ar": "طلب شراء", "ku": "داواى کڕین"},
    "offers":         {"ar": "عروض", "ku": "پێشکەشەکان"},
    "my_offers":      {"ar": "عروضي", "ku": "پێشکەشەکانم"},
    "start_over":     {"ar": "ابدأ من جديد", "ku": "دووبارە دەست پێکردن"},
    "prompt_main_menu":{"ar": "اختر خيارًا:", "ku": "هەڵبژاردنێک هەڵبژێرە:"},
    "prompt_product": {"ar": "اختر المنتج:", "ku": "تکایه کاڵاک هەڵبژێرە:"},
    "prompt_octane":  {"ar": "أدخل نسبة الأوكتان:", "ku": "نرخەکەی ئۆکتانەکە بنووسە:"},
    "prompt_qty":     {"ar": "أدخل الكمية:", "ku": "بڕی کاڵاکە بنووسە:"},
    "prompt_unit":    {"ar": "أدخل الوحدة (مثال: لتر):", "ku": "یەکە بنووسە (بۆ نموونە: لیتر):"},
    "prompt_price":   {"ar": "أدخل السعر:", "ku": "نرخی کاڵاکە بنووسە:"},
    "prompt_currency":{"ar": "أدخل العملة:", "ku": "دراوەکە بنووسە:"},
    "prompt_phone":   {"ar": "أدخل رقم الهاتف:", "ku": "ژمارەی موبایل بنووسە:"},
    "prompt_image":   {"ar": "أرسل صورة (اختياري) أو اكتب \"لا صورة\":", "ku": "وێنە بنێرە (اختیار) یان بنووسە \"بێ وێنە\":"},
    "offer_recorded":{"ar": "تم تسجيل العرض بنجاح!", "ku": "پێشکەشەکە بەسەرکەوتوویی تۆمارکرا!"},
    "delete_sell":    {"ar": "حذف عرض البيع", "ku": "سڕینه‌وه‌ی پێشکەش فرۆشتن"},
    "delete_buy":     {"ar": "حذف طلب الشراء", "ku": "سڕینه‌وه‌ی داواکاریی کڕین"},
    "deleted_sell":   {"ar": "تم حذف عرض البيع.", "ku": "پێشکەشی فرۆشتن سڕایەوە."},
    "deleted_buy":    {"ar": "تم حذف طلب الشراء.", "ku": "داواکاریی کڕین سڕایەوە."},
    "no_sell_offers": {"ar": "لا توجد عروض بيع حالياً.", "ku": "هیچ پێشکەشێکی فرۆشتن نییە."},
    "no_buy_requests":{"ar": "لا توجد طلبات شراء حالياً.", "ku": "هیچ داواکارییەکانی کڕین نییە."},
    "no_offers":      {"ar": "ليس لديك أي عروض مسجلة.", "ku": "تۆ هیچ پێشکەشێکت نییە."}
}

def filter_expired_offers():
    """حذف العروض الأقدم من 24 ساعة."""
    global sell_offers, buy_requests
    now = datetime.now().timestamp()
    sell_offers = [off for off in sell_offers if now - off['timestamp'] < 86400]
    buy_requests = [off for off in buy_requests if now - off['timestamp'] < 86400]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بداية المحادثة: اختيار اللغة."""
    context.user_data.clear()
    keyboard = [[text['language_ar']['ar'], text['language_ku']['ar']]]
    await update.message.reply_text(text['choose_language']['ar'], reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
    return LANGUAGE

async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تعيين اللغة المختارة والانتقال للقائمة الرئيسية."""
    choice = update.message.text
    if choice == text['language_ar']['ar']:
        context.user_data['lang'] = 'ar'
    elif choice == text['language_ku']['ar']:
        context.user_data['lang'] = 'ku'
    else:
        context.user_data['lang'] = 'ar'
    lang = context.user_data['lang']
    options = [[text['sell'][lang], text['buy_request'][lang]],
               [text['offers'][lang], text['my_offers'][lang]],
               [text['start_over'][lang]]]
    await update.message.reply_text(text['prompt_main_menu'][lang], reply_markup=ReplyKeyboardMarkup(options, one_time_keyboard=True))
    return MAIN_MENU

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالجة اختيار المستخدم في القائمة الرئيسية."""
    choice = update.message.text
    lang = context.user_data.get('lang', 'ar')
    if choice == text['start_over'][lang]:
        return await start(update, context)
    # تنظيف العروض منتهية الصلاحية
    filter_expired_offers()
    if choice == text['sell'][lang]:
        context.user_data['flow'] = 'sell'
        await update.message.reply_text(text['prompt_product'][lang], reply_markup=ReplyKeyboardMarkup([[p] for p in PRODUCTS], one_time_keyboard=True))
        return SELL_PRODUCT
    if choice == text['buy_request'][lang]:
        context.user_data['flow'] = 'buy'
        await update.message.reply_text(text['prompt_product'][lang], reply_markup=ReplyKeyboardMarkup([[p] for p in PRODUCTS], one_time_keyboard=True))
        return BUY_PRODUCT
    if choice == text['offers'][lang]:
        await show_offers(update, context)
        return MAIN_MENU
    if choice == text['my_offers'][lang]:
        await show_my_offers(update, context)
        return MAIN_MENU
    await update.message.reply_text(
        "رجاء اختر خياراً صحيحاً." if lang == 'ar' else "تکایه هەڵبژاردنێکی دروست هەڵبژێرە."
    )
    return MAIN_MENU

# تدفق بيع
async def sell_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تخزين المنتج المطلوب للبيع."""
    product = update.message.text
    lang = context.user_data.get('lang', 'ar')
    context.user_data['product'] = product
    if product == "بنزين":
        await update.message.reply_text(text['prompt_octane'][lang])
        return SELL_OCTANE
    await update.message.reply_text(text['prompt_qty'][lang])
    return SELL_QTY

async def sell_octane(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تخزين نسبة الأوكتان ثم السؤال عن الكمية."""
    octane = update.message.text
    context.user_data['octane'] = octane
    lang = context.user_data.get('lang', 'ar')
    await update.message.reply_text(text['prompt_qty'][lang])
    return SELL_QTY

async def sell_qty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تخزين الكمية ثم السؤال عن الوحدة."""
    qty = update.message.text
    context.user_data['quantity'] = qty
    lang = context.user_data.get('lang', 'ar')
    await update.message.reply_text(text['prompt_unit'][lang])
    return SELL_UNIT

async def sell_unit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تخزين الوحدة ثم السؤال عن السعر."""
    unit = update.message.text
    context.user_data['unit'] = unit
    lang = context.user_data.get('lang', 'ar')
    await update.message.reply_text(text['prompt_price'][lang])
    return SELL_PRICE

async def sell_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تخزين السعر ثم السؤال عن العملة."""
    price = update.message.text
    context.user_data['price'] = price
    lang = context.user_data.get('lang', 'ar')
    await update.message.reply_text(text['prompt_currency'][lang])
    return SELL_CURRENCY

async def sell_currency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تخزين العملة ثم السؤال عن رقم الهاتف."""
    currency = update.message.text
    context.user_data['currency'] = currency
    lang = context.user_data.get('lang', 'ar')
    await update.message.reply_text(text['prompt_phone'][lang])
    return SELL_PHONE

async def sell_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تخزين رقم الهاتف ثم السؤال عن الصورة."""
    phone = update.message.text
    context.user_data['phone'] = phone
    lang = context.user_data.get('lang', 'ar')
    await update.message.reply_text(text['prompt_image'][lang])
    return SELL_IMAGE

async def sell_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالجة الصورة الاختيارية وتسجيل عرض البيع."""
    lang = context.user_data.get('lang', 'ar')
    image_file_id = None
    if update.message.photo:
        image_file_id = update.message.photo[-1].file_id
    else:
        text_msg = update.message.text or ""
        if "لا صورة" in text_msg or text_msg.lower() == "بێ وێنە":
            image_file_id = None
    global offer_id_counter
    offer_id_counter += 1
    offer = {
        'id': f"sell{offer_id_counter}",
        'user_id': update.message.from_user.id,
        'type': 'sell',
        'product': context.user_data.get('product'),
        'octane': context.user_data.get('octane', None),
        'quantity': context.user_data.get('quantity'),
        'unit': context.user_data.get('unit'),
        'price': context.user_data.get('price'),
        'currency': context.user_data.get('currency'),
        'phone': context.user_data.get('phone'),
        'image_file_id': image_file_id,
        'timestamp': datetime.now().timestamp()
    }
    sell_offers.append(offer)
    await update.message.reply_text(text['offer_recorded'][lang])
    # العودة إلى القائمة الرئيسية
    return await show_main_menu(update, context)

# تدفق شراء (طلب شراء)
async def buy_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تخزين المنتج المطلوب للشراء."""
    product = update.message.text
    lang = context.user_data.get('lang', 'ar')
    context.user_data['product'] = product
    if product == "بنزين":
        await update.message.reply_text(text['prompt_octane'][lang])
        return BUY_OCTANE
    await update.message.reply_text(text['prompt_qty'][lang])
    return BUY_QTY

async def buy_octane(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تخزين نسبة الأوكتان (للشراء) ثم السؤال عن الكمية."""
    octane = update.message.text
    context.user_data['octane'] = octane
    lang = context.user_data.get('lang', 'ar')
    await update.message.reply_text(text['prompt_qty'][lang])
    return BUY_QTY

async def buy_qty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تخزين الكمية (للشراء) ثم السؤال عن الوحدة."""
    qty = update.message.text
    context.user_data['quantity'] = qty
    lang = context.user_data.get('lang', 'ar')
    await update.message.reply_text(text['prompt_unit'][lang])
    return BUY_UNIT

async def buy_unit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تخزين الوحدة (للشراء) ثم السؤال عن السعر."""
    unit = update.message.text
    context.user_data['unit'] = unit
    lang = context.user_data.get('lang', 'ar')
    await update.message.reply_text(text['prompt_price'][lang])
    return BUY_PRICE

async def buy_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تخزين السعر (للشراء) ثم السؤال عن العملة."""
    price = update.message.text
    context.user_data['price'] = price
    lang = context.user_data.get('lang', 'ar')
    await update.message.reply_text(text['prompt_currency'][lang])
    return BUY_CURRENCY

async def buy_currency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تخزين العملة (للشراء) ثم السؤال عن رقم الهاتف."""
    currency = update.message.text
    context.user_data['currency'] = currency
    lang = context.user_data.get('lang', 'ar')
    await update.message.reply_text(text['prompt_phone'][lang])
    return BUY_PHONE

async def buy_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تخزين رقم الهاتف (للشراء) ثم السؤال عن الصورة."""
    phone = update.message.text
    context.user_data['phone'] = phone
    lang = context.user_data.get('lang', 'ar')
    await update.message.reply_text(text['prompt_image'][lang])
    return BUY_IMAGE

async def buy_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """معالجة الصورة الاختيارية وتسجيل طلب الشراء."""
    lang = context.user_data.get('lang', 'ar')
    image_file_id = None
    if update.message.photo:
        image_file_id = update.message.photo[-1].file_id
    else:
        text_msg = update.message.text or ""
        if "لا صورة" in text_msg or text_msg.lower() == "بێ وێنە":
            image_file_id = None
    global offer_id_counter
    offer_id_counter += 1
    offer = {
        'id': f"buy{offer_id_counter}",
        'user_id': update.message.from_user.id,
        'type': 'buy',
        'product': context.user_data.get('product'),
        'octane': context.user_data.get('octane', None),
        'quantity': context.user_data.get('quantity'),
        'unit': context.user_data.get('unit'),
        'price': context.user_data.get('price'),
        'currency': context.user_data.get('currency'),
        'phone': context.user_data.get('phone'),
        'image_file_id': image_file_id,
        'timestamp': datetime.now().timestamp()
    }
    buy_requests.append(offer)
    await update.message.reply_text(text['offer_recorded'][lang])
    # العودة إلى القائمة الرئيسية
    return await show_main_menu(update, context)

async def format_offer(offer, lang):
    """تنسيق عرض واحد كسطر نصي."""
    ts = datetime.fromtimestamp(offer['timestamp']).strftime('%Y-%m-%d %H:%M')
    product_line = offer['product']
    if offer.get('octane'):
        product_line += f" (أوكتان {offer['octane']})"
    return (f"{product_line} - {offer['quantity']} {offer['unit']} - "
            f"{offer['price']} {offer['currency']} - {offer['phone']} - {ts}")

async def show_offers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض جميع عروض البيع وطلبات الشراء."""
    lang = context.user_data.get('lang', 'ar')
    filter_expired_offers()
    messages = []
    if sell_offers:
        header = "عروض البيع:" if lang == 'ar' else "پێشکەشەکانی فرۆشتن:"
        lines = [await format_offer(off, lang) for off in sell_offers]
        messages.append(header + "\n" + "\n".join(lines))
    else:
        messages.append(text['no_sell_offers'][lang])
    if buy_requests:
        header = "طلبات الشراء:" if lang == 'ar' else "داواکاریەکانی کڕین:"
        lines = [await format_offer(off, lang) for off in buy_requests]
        messages.append(header + "\n" + "\n".join(lines))
    else:
        messages.append(text['no_buy_requests'][lang])
    await update.message.reply_text("\n\n".join(messages))

async def show_my_offers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض عروضي الخاصة بالمستخدم مع أزرار الحذف."""
    lang = context.user_data.get('lang', 'ar')
    filter_expired_offers()
    user_id = update.message.from_user.id
    user_sell = [off for off in sell_offers if off['user_id'] == user_id]
    user_buy = [off for off in buy_requests if off['user_id'] == user_id]
    if not user_sell and not user_buy:
        await update.message.reply_text(text['no_offers'][lang])
        return
    buttons = []
    message_lines = []
    idx = 0
    for off in user_sell:
        idx += 1
        message_lines.append(await format_offer(off, lang))
        buttons.append([InlineKeyboardButton(f"{text['delete_sell'][lang]} {idx}", callback_data=f"del_sell_{off['id']}")])
    for off in user_buy:
        idx += 1
        message_lines.append(await format_offer(off, lang))
        buttons.append([InlineKeyboardButton(f"{text['delete_buy'][lang]} {idx}", callback_data=f"del_buy_{off['id']}")])
    await update.message.reply_text("\n".join(message_lines), reply_markup=InlineKeyboardMarkup(buttons))

async def delete_offer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة حذف عرض عبر زر الحذف."""
    query = update.callback_query
    await query.answer()
    data = query.data
    lang = context.user_data.get('lang', 'ar')
    if data.startswith("del_sell_"):
        offer_id = data.split("_", 2)[2]
        global sell_offers
        sell_offers = [off for off in sell_offers if off['id'] != offer_id]
        await query.edit_message_text(text=text['deleted_sell'][lang])
    elif data.startswith("del_buy_"):
        offer_id = data.split("_", 2)[2]
        global buy_requests
        buy_requests = [off for off in buy_requests if off['id'] != offer_id]
        await query.edit_message_text(text=text['deleted_buy'][lang])

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """عرض القائمة الرئيسية مرة أخرى."""
    lang = context.user_data.get('lang', 'ar')
    options = [[text['sell'][lang], text['buy_request'][lang]],
               [text['offers'][lang], text['my_offers'][lang]],
               [text['start_over'][lang]]]
    await update.message.reply_text(text['prompt_main_menu'][lang], reply_markup=ReplyKeyboardMarkup(options, one_time_keyboard=True))
    return MAIN_MENU

def main():
    app = ApplicationBuilder().token("YOUR_TELEGRAM_BOT_TOKEN").build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_language)],
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu)],
            SELL_PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, sell_product)],
            SELL_OCTANE: [MessageHandler(filters.TEXT & ~filters.COMMAND, sell_octane)],
            SELL_QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, sell_qty)],
            SELL_UNIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, sell_unit)],
            SELL_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, sell_price)],
            SELL_CURRENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, sell_currency)],
            SELL_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, sell_phone)],
            SELL_IMAGE: [MessageHandler(filters.PHOTO | filters.TEXT & ~filters.COMMAND, sell_image)],
            BUY_PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, buy_product)],
            BUY_OCTANE: [MessageHandler(filters.TEXT & ~filters.COMMAND, buy_octane)],
            BUY_QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, buy_qty)],
            BUY_UNIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, buy_unit)],
            BUY_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, buy_price)],
            BUY_CURRENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, buy_currency)],
            BUY_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, buy_phone)],
            BUY_IMAGE: [MessageHandler(filters.PHOTO | filters.TEXT & ~filters.COMMAND, buy_image)],
        },
        fallbacks=[
            CommandHandler('start', start),
            MessageHandler(filters.Regex("^(ابدأ من جديد|دووبارە دەست پێکردن)$"), start)
        ]
    )
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(delete_offer_callback, pattern='^del_'))
    app.run_polling()

if __name__ == '__main__':
    main()
