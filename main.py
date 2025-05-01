import logging
from telegram import (
    Update, ReplyKeyboardMarkup, KeyboardButton, 
    InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ConversationHandler, CallbackQueryHandler, ContextTypes
)
import datetime

# تفعيل تسجيل الأحداث
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# رمز التوكن للبوت (يجب استبداله برمزك الخاص عند الحاجة)
TOKEN = "8190734067:AAFHgihi5tIdoCKiXBxntOgWNBzguCNVzsE"

# الحالات المختلفة في المحادثة
CHOOSING_PRODUCT, ASK_OCTANE, ASK_QUANTITY, ASK_UNIT, ASK_PRICE, ASK_CURRENCY, ASK_PHONE, ASK_IMAGE = range(8)

# قاعدة بيانات مؤقتة لحفظ العروض
offers = {
    'sell': [],
    'buy': []
}
offer_id_counter = 0

def new_offer_id():
    """إنشاء معرف فريد للعرض."""
    global offer_id_counter
    offer_id_counter += 1
    return offer_id_counter

def get_main_menu(lang):
    """إنشاء لوحة مفاتيح رئيسية حسب اللغة."""
    if lang == 'ar':
        return ReplyKeyboardMarkup([
            ["عرض بيع", "طلب شراء"],
            ["عرض جميع عروض البيع", "عرض جميع عروض الشراء"],
            ["عروضي"]
        ], resize_keyboard=True)
    else:
        return ReplyKeyboardMarkup([
            ["پێشکەشی فرۆشتن", "پێشکەشی کڕین"],
            ["هەموو پێشکەشەکانی فرۆشتن", "هەموو پێشکەشەکانی کڕین"],
            ["پێشکەشەکانم"]
        ], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء المحادثة واختيار اللغة."""
    keyboard = [
        [InlineKeyboardButton("العربية", callback_data='lang_ar'), 
         InlineKeyboardButton("کوردی", callback_data='lang_ku')]
    ]
    text = "اختر لغتك / زمانی خود را هەڵبژێرە:"
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def lang_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة اختيار اللغة وإرسال القائمة الرئيسية."""
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == 'lang_ar':
        context.user_data['lang'] = 'ar'
        text = "تم اختيار اللغة العربية. مرحبًا بك!"
    else:
        context.user_data['lang'] = 'ku'
        text = "زمانی کوردی هەڵبژێردرا. بەخێربێیت!"
    # تعديل رسالة اختيار اللغة وإرسال القائمة الرئيسية
    await query.edit_message_text(text=text, reply_markup=None)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=get_main_menu(context.user_data['lang'])
    )
    return

async def start_sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء عملية إنشاء عرض بيع."""
    lang = context.user_data.get('lang', 'ar')
    context.user_data['offer_type'] = 'sell'
    # اختيار المنتج
    if lang == 'ar':
        text = "اختر المنتج الذي تريد بيعه:"
        products = ["بنزين", "كاز فلاش", "كاز معمل", "نافتا",
                    "دهن معمل", "فلاوين", "فلاوين مواصفات", "نفط خام"]
    else:
        text = "بەرهەمەکەی کە دەتەوێت بفڕێیت هەڵبژێرە:"
        products = ["بنزین", "گاز فلاش", "گاز ماڵپەڕ", "نافێتا",
                    "دەهن ماڵپەڕ", "فلاوین", "فلاوین تایبەتمەند", "نەوتی خاوک"]
    keyboard = [[KeyboardButton(p)] for p in products]
    await update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CHOOSING_PRODUCT

async def start_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء عملية إنشاء طلب شراء."""
    lang = context.user_data.get('lang', 'ar')
    context.user_data['offer_type'] = 'buy'
    # اختيار المنتج
    if lang == 'ar':
        text = "اختر المنتج الذي تريد شراءه:"
        products = ["بنزين", "كاز فلاش", "كاز معمل", "نافتا",
                    "دهن معمل", "فلاوين", "فلاوين مواصفات", "نفط خام"]
    else:
        text = "بەرهەمەکەی کە دەتەوێت بکڕیت هەڵبژێرە:"
        products = ["بنزین", "گاز فلاش", "گاز ماڵپەڕ", "نافێتا",
                    "دەهن ماڵپەڕ", "فلاوین", "فلاوین تایبەتمەند", "نەوتی خاوک"]
    keyboard = [[KeyboardButton(p)] for p in products]
    await update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CHOOSING_PRODUCT

async def ask_octane(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """سؤال نسبة الأوكتان في حال كان المنتج بنزين."""
    text = update.message.text
    context.user_data['product'] = text
    lang = context.user_data.get('lang', 'ar')
    if text in ["بنزين", "بنزین"]:  # إذا كان البنزين
        if lang == 'ar':
            await update.message.reply_text("ما هو نسبة الأوكتان للوقود (بنزين)؟", reply_markup=ReplyKeyboardRemove())
        else:
            await update.message.reply_text("کەواتا ئاوکتان بۆ بنزین چەندە؟", reply_markup=ReplyKeyboardRemove())
        return ASK_OCTANE
    else:
        context.user_data['octane'] = None
        return await ask_quantity(update, context)

async def got_octane(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الحصول على نسبة الأوكتان."""
    context.user_data['octane'] = update.message.text
    return await ask_quantity(update, context)

async def ask_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """سؤال الكمية المطلوبة."""
    lang = context.user_data.get('lang', 'ar')
    if lang == 'ar':
        text = "ما هي الكمية؟"
    else:
        text = "چەند بەرە هەیە؟"
    await update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())
    return ASK_QUANTITY

async def got_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الحصول على الكمية."""
    context.user_data['quantity'] = update.message.text
    # السؤال عن الوحدة
    lang = context.user_data.get('lang', 'ar')
    if lang == 'ar':
        text = "ما هي الوحدة؟"
        units = ["ليتر", "طن", "برميل"]
    else:
        text = "یەکە چیه؟"
        units = ["لیتر", "تان", "بارەوێل"]
    keyboard = [[KeyboardButton(u)] for u in units]
    await update.message.reply_text(text, reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return ASK_UNIT

async def got_unit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الحصول على الوحدة."""
    context.user_data['unit'] = update.message.text
    # السؤال عن السعر
    lang = context.user_data.get('lang', 'ar')
    if lang == 'ar':
        text = "ما هو السعر؟"
    else:
        text = "نرخی چەنە؟"
    await update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())
    return ASK_PRICE

async def got_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الحصول على السعر."""
    context.user_data['price'] = update.message.text
    # السؤال عن العملة
    lang = context.user_data.get('lang', 'ar')
    if lang == 'ar':
        text = "ما هي العملة؟"
        currencies = ["دولار", "دينار"]
    else:
        text = "کەرەشنا چییە؟"
        currencies = ["دۆلار", "دینار"]
    keyboard = [[KeyboardButton(c)] for c in currencies]
    await update.message.reply_text(text, reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))
    return ASK_CURRENCY

async def got_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الحصول على العملة."""
    context.user_data['currency'] = update.message.text
    # السؤال عن رقم الهاتف
    lang = context.user_data.get('lang', 'ar')
    if lang == 'ar':
        text = "ما هو رقم الهاتف؟"
    else:
        text = "ژمارەی تەلەفونەکەت چەندە؟"
    await update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())
    return ASK_PHONE

async def got_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الحصول على رقم الهاتف."""
    context.user_data['phone'] = update.message.text
    # طلب إرسال صورة اختيارية
    lang = context.user_data.get('lang', 'ar')
    if lang == 'ar':
        text = "إرسال صورة للعرض (اختياري)، أو اكتب /skip للتخطي."
    else:
        text = "وێنەیەک بنێرە (بەختیاری)، یان /skip بنوسە بۆ دوورخستن."
    await update.message.reply_text(text)
    return ASK_IMAGE

async def skip_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تخطي إرسال الصورة."""
    context.user_data['image'] = None
    return await finalize_offer(update, context)

async def got_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الحصول على الصورة المرسلة."""
    photo_file = update.message.photo[-1]
    file_id = photo_file.file_id
    context.user_data['image'] = file_id
    return await finalize_offer(update, context)

async def finalize_offer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تسجيل العرض نهائيًا."""
    user = update.effective_user
    lang = context.user_data.get('lang', 'ar')
    offer_type = context.user_data.get('offer_type')
    # بناء بيانات العرض
    offer = {
        'id': new_offer_id(),
        'user_id': user.id,
        'user_name': user.username or user.first_name,
        'product': context.user_data.get('product'),
        'octane': context.user_data.get('octane'),
        'quantity': context.user_data.get('quantity'),
        'unit': context.user_data.get('unit'),
        'price': context.user_data.get('price'),
        'currency': context.user_data.get('currency'),
        'phone': context.user_data.get('phone'),
        'image': context.user_data.get('image'),
        'created_at': datetime.datetime.now()
    }
    offers[offer_type].append(offer)
    # جدولة حذف العرض بعد 24 ساعة
    context.job_queue.run_once(remove_offer, 86400, data={'offer_type': offer_type, 'id': offer['id']})
    # تأكيد التسجيل للمستخدم
    if lang == 'ar':
        text = f"تم تسجيل العرض رقم {offer['id']} بنجاح."
    else:
        text = f"بە سەرکەوتویی پێشکەش {offer['id']} تۆمار کرا."
    await update.message.reply_text(text, reply_markup=get_main_menu(lang))
    # إعادة تعيين بيانات المستخدم (إبقاء اللغة)
    context.user_data.clear()
    context.user_data['lang'] = lang
    return ConversationHandler.END

async def remove_offer(context: ContextTypes.DEFAULT_TYPE):
    """حذف العرض من القائمة بعد انتهاء مدته."""
    job = context.job
    data = job.data
    offer_type = data['offer_type']
    offer_id = data['id']
    offers_list = offers.get(offer_type, [])
    for offer in offers_list:
        if offer['id'] == offer_id:
            offers_list.remove(offer)
            logger.info(f"Removed {offer_type} offer {offer_id} due to timeout.")
            break

async def show_offers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض جميع العروض (بيع أو شراء)."""
    text = update.message.text
    lang = context.user_data.get('lang', 'ar')
    if text in ["عرض جميع عروض البيع", "هەموو پێشکەشەکانی فرۆشتن"]:
        offer_type = 'sell'
        title = "جميع عروض البيع:" if lang=='ar' else "هەموو پێشکەشەکانی فرۆشتن:"
    elif text in ["عرض جميع عروض الشراء", "هەموو پێشکەشەکانی کڕین"]:
        offer_type = 'buy'
        title = "جميع عروض الشراء:" if lang=='ar' else "هەموو پێشکەشەکانی کڕین:"
    else:
        return
    off_list = offers.get(offer_type, [])
    if not off_list:
        if lang == 'ar':
            await update.message.reply_text("لا توجد عروض حالياً.")
        else:
            await update.message.reply_text("هیچ پێشکەشێک نییە.")
        return
    response = title + "\n\n"
    for offer in off_list:
        user = offer.get('user_name', '')
        phone = offer.get('phone', '')
        prod = offer.get('product', '')
        quantity = offer.get('quantity', '')
        unit = offer.get('unit', '')
        price = offer.get('price', '')
        currency = offer.get('currency', '')
        octane = offer.get('octane', '')
        if offer_type == 'sell':
            if lang == 'ar':
                line = f"#{offer['id']} - المنتج: {prod}"
                if octane:
                    line += f" (أوكتان {octane})"
                line += f"\n  الكمية: {quantity} {unit}\n  السعر: {price} {currency}\n  بائع: {user} (الهاتف: {phone})\n\n"
            else:
                line = f"#{offer['id']} - بەرهەم: {prod}"
                if octane:
                    line += f" (ئاوکتان: {octane})"
                line += f"\n  بەرە: {quantity} {unit}\n  نرخی: {price} {currency}\n  فرۆشێ: {user} (تەلەفون: {phone})\n\n"
        else:  # buy
            if lang == 'ar':
                line = f"#{offer['id']} - المنتج: {prod}"
                if octane:
                    line += f" (أوكتان {octane})"
                line += f"\n  الكمية: {quantity} {unit}\n  السعر: {price} {currency}\n  مشتري: {user} (الهاتف: {phone})\n\n"
            else:
                line = f"#{offer['id']} - بەرهەم: {prod}"
                if octane:
                    line += f" (ئاوکتان: {octane})"
                line += f"\n  بەرە: {quantity} {unit}\n  نرخی: {price} {currency}\n  کڕێکار: {user} (تەلەفون: {phone})\n\n"
        response += line
    await update.message.reply_text(response, reply_markup=get_main_menu(lang))

async def my_offers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض عروض المستخدم الخاصة مع زر حذف لكل عرض."""
    lang = context.user_data.get('lang', 'ar')
    user = update.effective_user
    user_id = user.id
    user_offers = []
    for typ in ['sell', 'buy']:
        for offer in offers.get(typ, []):
            if offer['user_id'] == user_id:
                user_offers.append((typ, offer))
    if not user_offers:
        if lang == 'ar':
            await update.message.reply_text("ليس لديك أي عروض.", reply_markup=get_main_menu(lang))
        else:
            await update.message.reply_text("تۆ هیچ پێشکەشێکت نییە.", reply_markup=get_main_menu(lang))
        return
    # إرسال كل عرض مع زر الحذف
    for typ, offer in user_offers:
        prod = offer['product']
        quantity = offer['quantity']
        unit = offer['unit']
        price = offer['price']
        currency = offer['currency']
        octane = offer['octane']
        phone = offer['phone']
        if typ == 'sell':
            if lang == 'ar':
                text = f"عرض البيع #{offer['id']}:\nالمنتج: {prod}"
                if octane:
                    text += f" (أوكتان {octane})"
                text += f"\nالكمية: {quantity} {unit}\nالسعر: {price} {currency}\nالهاتف: {phone}"
            else:
                text = f"پێشکەشی فرۆشتن #{offer['id']}:\nبەرهەم: {prod}"
                if octane:
                    text += f" (ئاوکتان: {octane})"
                text += f"\nبەرە: {quantity} {unit}\nنرخی: {price} {currency}\nتەلەفون: {phone}"
        else:
            if lang == 'ar':
                text = f"طلب الشراء #{offer['id']}:\nالمنتج: {prod}"
                if octane:
                    text += f" (أوكتان {octane})"
                text += f"\nالكمية: {quantity} {unit}\nالسعر: {price} {currency}\nالهاتف: {phone}"
            else:
                text = f"پێشکەشی کڕین #{offer['id']}:\nبەرهەم: {prod}"
                if octane:
                    text += f" (ئاوکتان: {octane})"
                text += f"\nبەرە: {quantity} {unit}\nنرخی: {price} {currency}\nتەلەفون: {phone}"
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("حذف" if lang=='ar' else "لابردن", callback_data=f"del_{typ}_{offer['id']}")
        ]])
        await update.message.reply_text(text, reply_markup=keyboard)
    return

async def delete_offer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة حذف العرض عبر زر Inline."""
    query = update.callback_query
    await query.answer()
    data = query.data  # الشكل: del_{type}_{id}
    parts = data.split('_')
    if len(parts) != 3:
        return
    typ = parts[1]
    try:
        oid = int(parts[2])
    except:
        return
    # حذف العرض من القائمة
    for offer in offers.get(typ, []):
        if offer['id'] == oid:
            offers[typ].remove(offer)
            break
    # حذف رسالة العرض من الدردشة
    await query.message.delete()
    lang = context.user_data.get('lang', 'ar')
    if lang == 'ar':
        text = f"تم حذف العرض #{oid}."
    else:
        text = f"پێشکەش #{oid} لابرا."
    await query.message.reply_text(text, reply_markup=get_main_menu(lang))

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إلغاء المحادثة الجارية."""
    lang = context.user_data.get('lang', 'ar')
    if lang == 'ar':
        text = "تم إلغاء العملية."
    else:
        text = "پرۆسەکە باشترە کرا."
    await update.message.reply_text(text, reply_markup=get_main_menu(lang))
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    # إعداد معالج الحوار للمحادثات الخاصة بالبيع والشراء
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^(عرض بيع|پێشکەشی فرۆشتن)$"), start_sell),
            MessageHandler(filters.Regex("^(طلب شراء|پێشکەشی کڕین)$"), start_buy)
        ],
        states={
            CHOOSING_PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_octane)],
            ASK_OCTANE: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_octane)],
            ASK_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_quantity)],
            ASK_UNIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_unit)],
            ASK_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_price)],
            ASK_CURRENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_currency)],
            ASK_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, got_phone)],
            ASK_IMAGE: [
                MessageHandler(filters.PHOTO, got_image),
                MessageHandler(filters.Regex("^/skip$"), skip_image)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(lang_choice, pattern='^lang_'))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.Regex("^(عرض جميع عروض البيع|هەموو پێشکەشەکانی فرۆشتن)$"), show_offers))
    app.add_handler(MessageHandler(filters.Regex("^(عرض جميع عروض الشراء|هەموو پێشکەشەکانی کڕین)$"), show_offers))
    app.add_handler(MessageHandler(filters.Regex("^(عروضي|پێشکەشەکانم)$"), my_offers))
    app.add_handler(CallbackQueryHandler(delete_offer_callback, pattern='^del_'))
    app.add_handler(CommandHandler('cancel', cancel))
    
    app.run_polling()

if __name__ == '__main__':
    main()
