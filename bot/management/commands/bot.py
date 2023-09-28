import datetime
import telegram
import os
#from bot.models import *
from telegram import Update
from django.core.management.base import BaseCommand
from django.db.models import Q, Count
from dotenv import load_dotenv
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
    ParseMode,
    LabeledPrice,
    InputMediaPhoto,
)
from telegram.ext import (
    Updater,
    Filters,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext,
    PreCheckoutQueryHandler,
    ConversationHandler
)


if __name__ == "__main__":
    load_dotenv()

    tg_token = os.getenv("TG_BOT_TOKEN")
    payment_token = os.getenv("PAYMENT_TOKEN")
    user_id = 6166975700
    bot = telegram.Bot(token=tg_token)

    # updates = bot.get_updates()
    # print(updates[0])
    # bot.send_message(text='Hi John!', chat_id=user_id)
    bot.send_invoice(
        chat_id=user_id,
        title="Оплата подписки",
        description="Оплата подписки пользователя на 12 месяцев",
        payload='payload',
        provider_token=payment_token,
        currency='RUB',
        # need_phone_number=False,
        # need_email=False,
        # is_flexible=False,
        prices=[LabeledPrice(label='Оплата подписки', amount=88000)],
        # reply_markup=reply_markup,
        start_parameter='test',
    )


    def process_pre_checkout_query(update, context):
        query = update.pre_checkout_query
        try:
            pass
        except:
            context.bot.answer_pre_checkout_query(
                pre_checkout_query_id=query.id,
                ok=False,
                error_message="Что-то пошло не так...",
            )
        else:
            context.bot.answer_pre_checkout_query(query.id, ok=True)


    def success_payment(update, context):
        '''Обработка успешной оплаты'''
        amount = update.message.successful_payment.total_amount / 100
        text = f'✅ Спасибо за оплату {amount} руб.!\n\n'
        keyboard = [
            [InlineKeyboardButton("На главную", callback_data="to_start")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=telegram.ParseMode.HTML,
        )

    # updater = Updater(token=tg_token, use_context=True)
    # dispatcher = updater.dispatcher


    # dispatcher.add_handler(conv_handler)
    # start_handler = CommandHandler('start', start_conversation)
    # dispatcher.add_handler(start_handler)
    # dispatcher.add_handler(CallbackQueryHandler(start_conversation, pattern='to_start'))
    # updater.start_polling()
    # updater.idle()