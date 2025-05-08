import os
import json
import logging
from uuid import uuid4
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler,
                          CallbackQueryHandler, ConversationHandler, filters)

# إعدادات تسجيل الأخطاء
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# تحميل التوكن من متغير بيئة
TOKEN = os.getenv("BOT_TOKEN")
OFFERS_FILE = "offers.json"

# حالات المحادثة
(CHOOSING_LANGUAGE, MAIN_MENU, SELECT_PRODUCT, ENTER_OCTANE, ENTER_QUANTITY,
 SELECT_UNIT, ENTER_PRICE, SELECT_CURRENCY, ENTER_PHONE, ENTER_SULFUR, ENTER_DENSITY, ASK_IMAGE) = range(12)

# تحميل العروض من ملف
if os.path.exists(OFFERS_FILE):
    with open(OFFERS_FILE, "r") as f:
        offers = json.load(f)
else:
    offers = []

def save_offers():
    with open(OFFERS_FILE, "w") as f:
        json.dump(offers, f)

# النصوص
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
        'currency_dollar': 'دولار $',
        'currency_euro': 'يورو €',
        'currency_iqd': 'دينار عراقي',
        'unit_liter': 'لتر',
        'unit_barrel': 'برميل',
        'unit_ton': 'طن',
    }
}

PRODUCTS = [
    {'ar': 'بنزين'}, {'ar': 'كاز فلاش'}, {'ar': 'كاز معمل'}, {'ar': 'نافتا'},
    {'ar': 'دهن معمل'}, {'ar': 'فلاوين'}, {'ar': 'فلاوين مواصفات'}, {'ar': 'نفط خام'}
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    keyboard = [
        [InlineKeyboardButton("العربية", callback_data='lang_ar')]
    ]
    await update.message.reply_text("اختر لغتك:", reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSING_LANGUAGE

async def language_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.message.edit_reply_markup(reply_markup=None)
    context.user_data['lang'] = query.data.split('_')[1]
    lang = context.user_data['lang']
    text = TEXTS[lang]['main_menu']
    buttons = [
        [TEXTS[lang]['sell'], TEXTS[lang]['buy']],
        [TEXTS[lang]['my_offers'], TEXTS[lang]['all_offers']]
    ]
    await query.message.reply_text(text, reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
    return MAIN_MENU

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_choice = update.message.text
    lang = context.user_data.get('lang', 'ar')
    if user_choice == TEXTS[lang]['sell']:
        context.user_data['offer_type'] = 'sell'
    elif user_choice == TEXTS[lang]['buy']:
        context.user_data['offer_type'] = 'buy'
    else:
        return MAIN_MENU
    context.user_data['new_offer'] = {'type': context.user_data['offer_type']}
    keyboard = [[InlineKeyboardButton(p['ar'], callback_data=f'product_{i}')] for i, p in enumerate(PRODUCTS)]
    await update.message.reply_text(TEXTS[lang]['choose_product'], reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_PRODUCT

async def product_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.message.edit_reply_markup(reply_markup=None)
    lang = context.user_data['lang']
    product_id = int(query.data.split('_')[1])
    context.user_data['new_offer']['product_id'] = product_id
    product_name = PRODUCTS[product_id]['ar']
    if product_id == 0:
        await query.message.reply_text(TEXTS[lang]['enter_octane'].format(product_name))
        return ENTER_OCTANE
    else:
        await query.message.reply_text(TEXTS[lang]['enter_quantity'])
        return ENTER_QUANTITY

async def enter_octane(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['new_offer']['octane'] = update.message.text.strip()
    lang = context.user_data['lang']
    await update.message.reply_text(TEXTS[lang]['enter_quantity'])
    return ENTER_QUANTITY

async def enter_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['new_offer']['quantity'] = update.message.text.strip()
    lang = context.user_data['lang']
    buttons = [[TEXTS[lang]['unit_liter'], TEXTS[lang]['unit_barrel'], TEXTS[lang]['unit_ton']]]
    await update.message.reply_text(TEXTS[lang]['choose_unit'], reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
    return SELECT_UNIT

async def select_unit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['new_offer']['unit'] = update.message.text.strip()
    lang = context.user_data['lang']
    await update.message.reply_text(TEXTS[lang]['enter_price'], reply_markup=ReplyKeyboardRemove())
    return ENTER_PRICE

async def enter_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['new_offer']['price'] = update.message.text.strip()
    lang = context.user_data['lang']
    buttons = [[TEXTS[lang]['currency_dollar'], TEXTS[lang]['currency_euro'], TEXTS[lang]['currency_iqd']]]
    await update.message.reply_text(TEXTS[lang]['choose_currency'], reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
    return SELECT_CURRENCY

async def select_currency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['new_offer']['currency'] = update.message.text.strip()
    await update.message.reply_text("🧪 أدخل نسبة الكبريت (سلفر):")
    return ENTER_SULFUR

async def enter_sulfur(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['new_offer']['sulfur'] = update.message.text.strip()
    await update.message.reply_text("⚖️ أدخل نسبة الكثافة (طواف):")
    return ENTER_DENSITY

async def enter_density(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['new_offer']['density'] = update.message.text.strip()
    lang = context.user_data['lang']
    await update.message.reply_text(TEXTS[lang]['enter_phone'], reply_markup=ReplyKeyboardRemove())
    return ENTER_PHONE

async def enter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['new_offer']['phone'] = update.message.text.strip()
    lang = context.user_data['lang']
    await update.message.reply_text(TEXTS[lang]['ask_image'])
    return ASK_IMAGE

async def skip_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['new_offer']['image'] = None
    return await finalize_offer(update, context)

async def receive_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    photo_file = await update.message.photo[-1].get_file()
    context.user_data['new_offer']['image'] = photo_file.file_id
    return await finalize_offer(update, context)

async def finalize_offer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data['lang']
    new_offer = context.user_data['new_offer']
    new_offer['id'] = str(uuid4())
    new_offer['user_id'] = update.effective_user.id
    new_offer.setdefault('octane', None)
    offers.append(new_offer)
    save_offers()
    context.job_queue.run_once(delete_offer_job, 86400, data=new_offer['id'])
    await update.message.reply_text(TEXTS[lang]['offer_registered'])
    buttons = [
        [TEXTS[lang]['sell'], TEXTS[lang]['buy']],
        [TEXTS[lang]['my_offers'], TEXTS[lang]['all_offers']]
    ]
    await update.message.reply_text(TEXTS[lang]['main_menu'], reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
    context.user_data.pop('new_offer', None)
    return MAIN_MENU

def delete_offer_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    offer_id = job.data
    for i, offer in enumerate(offers):
        if offer['id'] == offer_id:
            offers.pop(i)
            save_offers()
            break

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("تم إلغاء العملية.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING_LANGUAGE: [CallbackQueryHandler(language_chosen, pattern='^lang_')],
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu)],
            SELECT_PRODUCT: [CallbackQueryHandler(product_chosen, pattern='^product_')],
            ENTER_OCTANE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_octane)],
            ENTER_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_quantity)],
            SELECT_UNIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_unit)],
            ENTER_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_price)],
            SELECT_CURRENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_currency)],
            ENTER_SULFUR: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_sulfur)],
            ENTER_DENSITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_density)],
            ENTER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_phone)],
            ASK_IMAGE: [
                CommandHandler('skip', skip_image),
                MessageHandler(filters.PHOTO, receive_image)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel), CommandHandler('start', start)]
    )
    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == '__main__':
    main()
