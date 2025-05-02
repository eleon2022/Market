from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler,
                          CallbackQueryHandler, ConversationHandler, filters)
from uuid import uuid4
import logging

# Enable logging for debugging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token (use the provided token)
TOKEN = "8190734067:AAFHgihi5tIdoCKiXBxntOgWNBzguCNVzsE"

# Conversation states
(CHOOSING_LANGUAGE, MAIN_MENU, SELECT_PRODUCT, ENTER_OCTANE, ENTER_QUANTITY,
 SELECT_UNIT, ENTER_PRICE, SELECT_CURRENCY, ENTER_PHONE, ASK_IMAGE) = range(10)

# Texts dictionary for Arabic (ar) and Kurdish (ku) translations
TEXTS = {
    'ar': {
        'select_language': "🇸🇦 اختر لغتك:",
        'arabic': "🇸🇦 العربية",
        'kurdish': "🇰🇷 الكردية",
        'main_menu': "القائمة الرئيسية:",
        'sell': "🛢️ عرض للبيع",
        'buy': "🛒 طلب شراء",
        'my_offers': "🗂️ عروضي",
        'all_offers': "📁 الكل",
        'choose_product': "⚙️ اختر المنتج:",
        'enter_octane': "🛢️ أدخل نسبة الأوكتان للـ{}:",
        'enter_quantity': "📦 أدخل الكمية:",
        'choose_unit': "⚖️ اختر الوحدة:",
        'enter_price': "💰 أدخل السعر:",
        'choose_currency': "🪙 اختر العملة:",
        'enter_phone': "☎️ أدخل رقم الهاتف:",
        'ask_image': "📸 إرسال صورة (اختياري) أو اضغط /skip للتخطي.",
        'offer_registered': "✅ تم تسجيل العرض بنجاح!",
        'all_sell_offers': "🛒 جميع عروض البيع:",
        'all_buy_offers': "🛢️ جميع طلبات الشراء:",
        'no_offers': "لا توجد عروض حتى الآن.",
        'my_offers_header': "🗂️ عروضك:",
        'delete_button': "❌ حذف",
        'offer_deleted': "🗑️ تم حذف العرض.",
        'currency_dollar': 'دولار $',
        'currency_euro': 'يورو €',
        'currency_iqd': 'دينار عراقي',
        'unit_liter': 'لتر',
        'unit_barrel': 'برميل',
        'unit_ton': 'طن',
    },
    'ku': {
        'select_language': "🇰🇷 زمانەکەت هەڵبژێرە:",
        'arabic': "🇸🇦 عەرەبی",
        'kurdish': "🇰🇷 کوردی",
        'main_menu': "سەرەکی:",
        'sell': "🛢️ فڕۆشتن",
        'buy': "🛒 کڕین",
        'my_offers': "🗂️ پێشکەشەکانم",
        'all_offers': "📁 هەموو پێشکەشەکان",
        'choose_product': "⚙️ بەرهەمیەک هەڵبژێرە:",
        'enter_octane': "🛢️ ژمارەی ئۆکتانەکە بنووسە بۆ {}:",
        'enter_quantity': "📦 بڕەکە بنووسە:",
        'choose_unit': "⚖️ یەکەکە هەڵبژێرە:",
        'enter_price': "💰 نرخی بنووسە:",
        'choose_currency': "🪙 دراوە دیاربکە:",
        'enter_phone': "☎️ ژمارەی مۆبایل بنووسە:",
        'ask_image': "📸 وێنەیەک بنێرە (هەلبژێردراوە) یان /skip بۆ ڕابردن.",
        'offer_registered': "✅ پیشکەشەکەت تۆمارکرا!",
        'all_sell_offers': "🛒 هەموو پێشکەشەکانی فڕۆشتن:",
        'all_buy_offers': "🛢️ هەموو داواکاریەکانی کڕین:",
        'no_offers': "هیچ پێشکەشێک نییە تاکو ئێستا.",
        'my_offers_header': "🗂️ پێشکەشەکانت:",
        'delete_button': "❌ سڕینەوە",
        'offer_deleted': "🗑️ پێشکەشەکەت سڕایەوە.",
        'currency_dollar': 'دۆلار $',
        'currency_euro': 'یۆرۆ €',
        'currency_iqd': 'دینار عێراقی',
        'unit_liter': 'لیتر',
        'unit_barrel': 'بەرەیل',
        'unit_ton': 'تۆن',
    }
}

# List of products with names in both languages
PRODUCTS = [
    {'ar': 'بنزين', 'ku': 'بنزین'},
    {'ar': 'كاز فلاش', 'ku': 'گەزی فلاش'},
    {'ar': 'كاز معمل', 'ku': 'گەزی کارخانا'},
    {'ar': 'نافتا', 'ku': 'نافتە'},
    {'ar': 'دهن معمل', 'ku': 'دیزێلی کارخانا'},
    {'ar': 'فلاوين', 'ku': 'فلاوین'},
    {'ar': 'فلاوين مواصفات', 'ku': 'جۆری فلاوین'},
    {'ar': 'نفط خام', 'ku': 'نەوتی خاوه‌ندر'}
]

# Global list to store all offers
offers = []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Always restart and ask user to select language."""
    context.user_data.clear()  # يمسح بيانات المستخدم القديمة
    keyboard = [
        [InlineKeyboardButton("العربية", callback_data='lang_ar'),
         InlineKeyboardButton("الكردية", callback_data='lang_ku')]
    ]
    await update.message.reply_text(
        "اختر لغتك:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHOOSING_LANGUAGE

async def language_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle language selection and display main menu."""
    query = update.callback_query
    await query.answer()
    # Remove language selection buttons
    await query.message.edit_reply_markup(reply_markup=None)
    lang = query.data.split('_')[1]  # 'ar' or 'ku'
    context.user_data['lang'] = lang
    # Show main menu buttons
    text = TEXTS[lang]['main_menu']
    buttons = [
        [TEXTS[lang]['sell'], TEXTS[lang]['buy']],
        [TEXTS[lang]['my_offers'], TEXTS[lang]['all_offers']]
    ]
    await query.message.reply_text(text, reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
    return MAIN_MENU

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle user selection from the main menu."""
    user_choice = update.message.text
    lang = context.user_data.get('lang', 'ar')
    # Determine action
    if user_choice == TEXTS[lang]['sell']:
        context.user_data['offer_type'] = 'sell'
    elif user_choice == TEXTS[lang]['buy']:
        context.user_data['offer_type'] = 'buy'
    elif user_choice == TEXTS[lang]['my_offers']:
        return await show_my_offers(update, context)
    elif user_choice == TEXTS[lang]['all_offers']:
        return await show_all_offers(update, context)
    else:
        # If unknown input, remain in main menu
        return MAIN_MENU
    # Start adding a new offer
    context.user_data['new_offer'] = {'type': context.user_data['offer_type']}
    text = TEXTS[lang]['choose_product']
    # Create buttons for product list
    keyboard = []
    for i, product in enumerate(PRODUCTS):
        button = InlineKeyboardButton(product[lang], callback_data=f"product_{i}")
        keyboard.append([button])
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_PRODUCT

async def product_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save chosen product; if Benzene, ask for octane, else ask quantity."""
    query = update.callback_query
    await query.answer()
    # Remove product buttons
    await query.message.edit_reply_markup(reply_markup=None)
    lang = context.user_data['lang']
    product_id = int(query.data.split('_')[1])
    context.user_data['new_offer']['product_id'] = product_id
    product_name = PRODUCTS[product_id][lang]
    # If product is Benzene (index 0), ask octane percentage
    if product_id == 0:
        text = TEXTS[lang]['enter_octane'].format(product_name)
        await query.message.reply_text(text)
        return ENTER_OCTANE
    else:
        # Ask for quantity
        await query.message.reply_text(TEXTS[lang]['enter_quantity'])
        return ENTER_QUANTITY

async def enter_octane(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store octane and ask for quantity."""
    context.user_data['new_offer']['octane'] = update.message.text.strip()
    lang = context.user_data['lang']
    await update.message.reply_text(TEXTS[lang]['enter_quantity'])
    return ENTER_QUANTITY

async def enter_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store quantity and ask for unit (with buttons)."""
    context.user_data['new_offer']['quantity'] = update.message.text.strip()
    lang = context.user_data['lang']
    # Unit options: liter, barrel, ton
    buttons = [[TEXTS[lang]['unit_liter'], TEXTS[lang]['unit_barrel'], TEXTS[lang]['unit_ton']]]
    await update.message.reply_text(TEXTS[lang]['choose_unit'],
                                    reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
    return SELECT_UNIT

async def select_unit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store unit and ask for price."""
    context.user_data['new_offer']['unit'] = update.message.text.strip()
    lang = context.user_data['lang']
    await update.message.reply_text(TEXTS[lang]['enter_price'], reply_markup=ReplyKeyboardRemove())
    return ENTER_PRICE

async def enter_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store price and ask for currency (with buttons)."""
    context.user_data['new_offer']['price'] = update.message.text.strip()
    lang = context.user_data['lang']
    # Currency options: USD, EUR, IQD
    buttons = [[TEXTS[lang]['currency_dollar'], TEXTS[lang]['currency_euro'], TEXTS[lang]['currency_iqd']]]
    await update.message.reply_text(TEXTS[lang]['choose_currency'],
                                    reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
    return SELECT_CURRENCY

async def select_currency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store currency and ask for phone number."""
    context.user_data['new_offer']['currency'] = update.message.text.strip()
    lang = context.user_data['lang']
    await update.message.reply_text(TEXTS[lang]['enter_phone'], reply_markup=ReplyKeyboardRemove())
    return ENTER_PHONE

async def enter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store phone number and ask for an optional image."""
    context.user_data['new_offer']['phone'] = update.message.text.strip()
    lang = context.user_data['lang']
    await update.message.reply_text(TEXTS[lang]['ask_image'], reply_markup=ReplyKeyboardRemove())
    return ASK_IMAGE

async def skip_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User chose to skip sending an image."""
    context.user_data['new_offer']['image'] = None
    return await finalize_offer(update, context)

async def receive_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """User sent an image; store its file_id."""
    photo_file = await update.message.photo[-1].get_file()
    context.user_data['new_offer']['image'] = photo_file.file_id
    return await finalize_offer(update, context)

async def finalize_offer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save the new offer, schedule deletion, and return to main menu."""
    lang = context.user_data['lang']
    new_offer = context.user_data['new_offer']
    # Assign unique ID and user ID
    new_offer['id'] = str(uuid4())
    new_offer['user_id'] = update.effective_user.id
    # Ensure type and octane keys exist
    if 'type' not in new_offer:
        new_offer['type'] = context.user_data.get('offer_type', 'sell')
    if 'octane' not in new_offer:
        new_offer['octane'] = None
    # Add to global offers list
    offers.append(new_offer)
    # Schedule automatic deletion after 24 hours (86400 seconds)
    context.job_queue.run_once(delete_offer_job, 86400, data=new_offer['id'])
    # Confirm to user
    await update.message.reply_text(TEXTS[lang]['offer_registered'])
    # Show main menu again
    text = TEXTS[lang]['main_menu']
    buttons = [
        [TEXTS[lang]['sell'], TEXTS[lang]['buy']],
        [TEXTS[lang]['my_offers'], TEXTS[lang]['all_offers']]
    ]
    await update.message.reply_text(text, reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
    # Clean up temporary data
    context.user_data.pop('new_offer', None)
    return MAIN_MENU

async def show_all_offers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display all selling offers and all buying requests with optional image."""
    lang = context.user_data['lang']
    sell_offers = [o for o in offers if o['type'] == 'sell']
    buy_offers = [o for o in offers if o['type'] == 'buy']

    # عرض طلبات الشراء
    if buy_offers:
        await update.message.reply_text(TEXTS[lang]['all_buy_offers'])
        for offer in buy_offers:
            prod = PRODUCTS[offer['product_id']][lang]
            octane_str = f" ({'نسبة الأوكتان' if lang == 'ar' else 'ژمارەی ئۆکتان'}: {offer['octane']})" if offer.get('octane') else ""
            caption = (
                f"{prod}{octane_str}\n"
                f"📦 {offer['quantity']} {offer['unit']} | 💰 {offer['price']} {offer['currency']}\n"
                f"☎️ {offer['phone']}"
            )
            if offer.get('image'):
                await update.message.reply_photo(photo=offer['image'], caption=caption)
            else:
                await update.message.reply_text(caption)

    # عرض عروض البيع
    if sell_offers:
        await update.message.reply_text(TEXTS[lang]['all_sell_offers'])
        for offer in sell_offers:
            prod = PRODUCTS[offer['product_id']][lang]
            octane_str = f" ({'نسبة الأوكتان' if lang == 'ar' else 'ژمارەی ئۆکتان'}: {offer['octane']})" if offer.get('octane') else ""
            caption = (
                f"{prod}{octane_str}\n"
                f"📦 {offer['quantity']} {offer['unit']} | 💰 {offer['price']} {offer['currency']}\n"
                f"☎️ {offer['phone']}"
            )
            if offer.get('image'):
                await update.message.reply_photo(photo=offer['image'], caption=caption)
            else:
                await update.message.reply_text(caption)

    if not buy_offers and not sell_offers:
        await update.message.reply_text(TEXTS[lang]['no_offers'])

    return MAIN_MENU

async def show_all_offers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display all selling offers and all buying requests."""
    lang = context.user_data['lang']
    sell_offers = [o for o in offers if o['type'] == 'sell']
    buy_offers = [o for o in offers if o['type'] == 'buy']
    message = ""
    if sell_offers:
        message += TEXTS[lang]['all_sell_offers'] + "\n"
        for offer in sell_offers:
            prod = PRODUCTS[offer['product_id']][lang]
            octane_str = ""
            if offer.get('octane'):
                octane_str = f" ({'نسبة الأوكتان' if lang=='ar' else 'ژمارەی ئۆکتان'}: {offer['octane']})"
            message += (f"🛢️ {prod}{octane_str} | 📦 {offer['quantity']} {offer['unit']} | "
                        f"💰 {offer['price']} {offer['currency']} | ☎️ {offer['phone']}\n")
    if buy_offers:
        message += "\n" + TEXTS[lang]['all_buy_offers'] + "\n"
        for offer in buy_offers:
            prod = PRODUCTS[offer['product_id']][lang]
            octane_str = ""
            if offer.get('octane'):
                octane_str = f" ({'نسبة الأوكتان' if lang=='ar' else 'ژمارەی ئۆکتان'}: {offer['octane']})"
            message += (f"🛢️ {prod}{octane_str} | 📦 {offer['quantity']} {offer['unit']} | "
                        f"💰 {offer['price']} {offer['currency']} | ☎️ {offer['phone']}\n")
    if not message:
        message = TEXTS[lang]['no_offers']
    await update.message.reply_text(message)
    return MAIN_MENU

async def delete_offer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle deletion when the user clicks a delete button."""
    query = update.callback_query
    await query.answer()
    offer_id = query.data.split('_')[1]
    lang = context.user_data.get('lang', 'ar')
    # Find the offer and ensure it's owned by this user
    for i, offer in enumerate(offers):
        if offer['id'] == offer_id and offer['user_id'] == update.effective_user.id:
            offers.pop(i)
            await query.edit_message_text(TEXTS[lang]['offer_deleted'])
            return
    # If not found or not permitted
    await query.answer("⚠️ العرض غير موجود أو لا يمكن حذفه.", show_alert=True)

def delete_offer_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Job to automatically delete an offer after 24 hours."""
    job = context.job
    offer_id = job.data
    for i, offer in enumerate(offers):
        if offer['id'] == offer_id:
            offers.pop(i)
            break

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the current operation."""
    await update.message.reply_text("تم إلغاء العملية.")
    return ConversationHandler.END

def main() -> None:
    """Start the bot."""
    application = ApplicationBuilder().token(TOKEN).build()

    # Conversation handler for main flow
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING_LANGUAGE: [
                CallbackQueryHandler(language_chosen, pattern='^lang_')
            ],
            MAIN_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu)
            ],
            SELECT_PRODUCT: [
                CallbackQueryHandler(product_chosen, pattern='^product_')
            ],
            ENTER_OCTANE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_octane)
            ],
            ENTER_QUANTITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_quantity)
            ],
            SELECT_UNIT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, select_unit)
            ],
            ENTER_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_price)
            ],
            SELECT_CURRENCY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, select_currency)
            ],
            ENTER_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_phone)
            ],
            ASK_IMAGE: [
                CommandHandler('skip', skip_image),
                MessageHandler(filters.PHOTO, receive_image)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel), CommandHandler('start', start)]
    )
    application.add_handler(conv_handler)

    # Handler for delete offer buttons (callback queries)
    application.add_handler(CallbackQueryHandler(delete_offer, pattern='^delete_'))

    # Start the bot (using polling)
    application.run_polling()

if __name__ == '__main__':
    main()
