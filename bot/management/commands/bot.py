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


import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


def start_conversation():
    print("1")


def cancel(update, context): pass


def send_invoice(update, context):
    # token_pay = settings.token_pay # ЗАМЕНИЛ СТРОКУ
    token_pay = payment_token

    chat_id = update.effective_message.chat_id
    context.user_data['invoice_sent'] = True

    keyboard = [
        [InlineKeyboardButton('Оплатить', pay=True)],
        # [InlineKeyboardButton('На главную', callback_data='to_start')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_invoice(
        chat_id=chat_id,
        title="Оплата подписки",
        description="Оплата подписки пользователя на 12 месяцев",
        payload='payload',
        provider_token=token_pay,
        currency='RUB',
        # need_phone_number=False,
        # need_email=False,
        is_flexible=False,
        prices=[LabeledPrice(label='Оплата подписки', amount=20000)],
        reply_markup=reply_markup,
        start_parameter='test',
    )
    return 'SUCCESS_PAYMENT'


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

    return 'SUCCESS_PAYMENT'


if __name__ == "__main__":
    load_dotenv()

    tg_token = os.getenv("TG_BOT_TOKEN")
    payment_token = os.getenv("PAYMENT_TOKEN")
#    user_id = 6166975700 # это для теста


    updater = Updater(token=tg_token, use_context=True)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
                entry_points=[CommandHandler('start', send_invoice)],
                states={
                    'SEND_INVOICE': [
                        CallbackQueryHandler(send_invoice, pattern='pay'),
                        # CallbackQueryHandler(make_order, pattern='cancel'),

                    ],
                    'PROCESS_PRE_CHECKOUT': [
                        PreCheckoutQueryHandler(process_pre_checkout_query),
                        CallbackQueryHandler(success_payment,
                                             pattern='success_payment'),
                    ],
                    'SUCCESS_PAYMENT': [
                        CallbackQueryHandler(start_conversation,
                                             pattern='to_start'),
                    ],
                },
                fallbacks=[CommandHandler('cancel', cancel)],
                per_chat=False  # Добавили эту строку для решения проблем с оплатой
    )
    cur_dish_id = 0

    dispatcher.add_handler(conv_handler)
    start_handler = CommandHandler('start', send_invoice)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(CallbackQueryHandler(send_invoice, pattern='to_start'))
    updater.start_polling()
    updater.idle()


