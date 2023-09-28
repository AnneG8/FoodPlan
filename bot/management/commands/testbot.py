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

    bot = telegram.Bot(token='TG_BOT_TOKEN')

    updates = bot.get_updates()
    print(updates[0])

    # updater = Updater(token=tg_token, use_context=True)
    # dispatcher = updater.dispatcher


    # dispatcher.add_handler(conv_handler)
    # start_handler = CommandHandler('start', start_conversation)
    # dispatcher.add_handler(start_handler)
    # dispatcher.add_handler(CallbackQueryHandler(start_conversation, pattern='to_start'))
    # updater.start_polling()
    # updater.idle()
