from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler, CallbackQueryHandler, ContextTypes, filters

# Define states for ConversationHandler
LANG, PRICE, CURRENCY, PHONE, PHOTO = range(5)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Start the conversation and ask for language
    keyboard = [["العربية", "الكردية"]]
    await update.message.reply_text(
        "مرحبًا! الرجاء اختيار لغتك:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return LANG

async def language_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Store chosen language (for possible translation use)
    lang = update.message.text
    context.user_data['lang'] = lang
    # Ask for price after choosing language
    await update.message.reply_text("أدخل السعر:")
    return PRICE

async def price_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Store entered price
    price = update.message.text
    context.user_data['price'] = price
    # Ask for currency
    keyboard = [["دولار", "دينار"]]
    await update.message.reply_text(
        "اختر العملة:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CURRENCY

async def currency_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Store chosen currency
    currency = update.message.text
    context.user_data['currency'] = currency
    # Ask for phone number
    await update.message.reply_text("أدخل رقم الهاتف:")
    return PHONE

async def phone_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Store phone number
    phone = update.message.text
    context.user_data['phone'] = phone
    # Ask for optional photo or skip
    await update.message.reply_text("إرسال صورة (اختياري) أو اضغط /skip للتخطي.")
    return PHOTO

async def photo_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Handle received photo and finalize offer
    photo_file = await update.message.photo[-1].get_file()
    photo_id = photo_file.file_id
    # Save offer data to bot_data
    offer = {
        'price': context.user_data.get('price'),
        'currency': context.user_data.get('currency'),
        'phone': context.user_data.get('phone'),
        'photo': photo_id
    }
    if 'sales' not in context.bot_data:
        context.bot_data['sales'] = []
    context.bot_data['sales'].append(offer)
    # Confirm and show menu for viewing offers
    await update.message.reply_text("تم حفظ العرض بنجاح!")
    keyboard = [
        [InlineKeyboardButton("عروض البيع", callback_data='sales'),
         InlineKeyboardButton("طلبات الشراء", callback_data='buys')]
    ]
    await update.message.reply_text(
        "اختر ما تريد عرضه:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END

async def skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Handle skipping photo and finalize offer without photo
    offer = {
        'price': context.user_data.get('price'),
        'currency': context.user_data.get('currency'),
        'phone': context.user_data.get('phone')
    }
    if 'sales' not in context.bot_data:
        context.bot_data['sales'] = []
    context.bot_data['sales'].append(offer)
    await update.message.reply_text("تم حفظ العرض بنجاح!")
    keyboard = [
        [InlineKeyboardButton("عروض البيع", callback_data='sales'),
         InlineKeyboardButton("طلبات الشراء", callback_data='buys')]
    ]
    await update.message.reply_text(
        "اختر ما تريد عرضه:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END

async def show_sales(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Display all sale offers
    query = update.callback_query
    await query.answer()
    sales = context.bot_data.get('sales', [])
    if not sales:
        await query.message.reply_text("لا توجد عروض للبيع حاليًا.")
    else:
        for off in sales:
            text = f"السعر: {off.get('price')} {off.get('currency')}\nالهاتف: {off.get('phone')}"
            if 'photo' in off:
                # Send photo with caption if available
                await context.bot.send_photo(chat_id=query.message.chat.id, photo=off['photo'], caption=text)
            else:
                await query.message.reply_text(text)

async def show_buys(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Display all purchase requests
    query = update.callback_query
    await query.answer()
    buys = context.bot_data.get('buys', [])
    if not buys:
        await query.message.reply_text("لا توجد طلبات شراء حاليًا.")
    else:
        for off in buys:
            text = f"السعر: {off.get('price')} {off.get('currency')}\nالهاتف: {off.get('phone')}"
            if 'photo' in off:
                await context.bot.send_photo(chat_id=query.message.chat.id, photo=off['photo'], caption=text)
            else:
                await query.message.reply_text(text)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Handle cancellation
    await update.message.reply_text("تم إلغاء العملية.")
    return ConversationHandler.END

def main() -> None:
    TOKEN = "8190734067:AAFHgihi5tIdoCKiXBxntOgWNBzguCNVzsE"
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
                MessageHandler(filters.PHOTO & ~filters.COMMAND, receive_image)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(delete_offer, pattern='^delete_'))
    application.run_polling()

if __name__ == '__main__':
    main()
