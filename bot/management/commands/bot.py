import datetime
import telegram
import os
from pathlib import Path
import sys
from bot.models import *
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


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        load_dotenv()

        tg_token = os.getenv("TG_BOT_TOKEN")
        updater = Updater(token=tg_token, use_context=True)
        dispatcher = updater.dispatcher

        def cancel(update, context): pass
        def paid(update, context): pass

        def start_conversation(update, context):
            query = update.callback_query
            user_first_name = update.effective_user.first_name
            user_id = update.effective_user.id
            context.user_data['user_first_name'] = user_first_name
            context.user_data['user_id'] = user_id

            keyboard = [
                [
                    InlineKeyboardButton("Попробовать бесплатно", callback_data='to_menu'),
                    InlineKeyboardButton("Оплатить доступ", callback_data='to_payment'),
                ]

            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.effective_message.reply_photo(
                photo=open('C:/Users/Honor/Documents/GitHub/FoodPlan/media/greetings.jpg', 'rb'),
                caption=f"""Шефом может стать каждый!
        Поможем быстро и легко приготовить блюдо дня!""",
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            for meal in Meal.objects.all():
                print(meal.id)
            return 'GREETINGS'

        def menu(update, context):
            query = update.callback_query
            user_first_name = update.effective_user.first_name
            user_id = update.effective_user.id
            context.user_data['user_first_name'] = user_first_name
            context.user_data['user_id'] = user_id
            context.user_data["cur_dish_id"] = 1

            keyboard = [
                [
                    InlineKeyboardButton("Выбрать блюдо", callback_data='to_dishes'),
                    InlineKeyboardButton("Настроить фильтр", callback_data='to_filters'),
                ],
                [
                    InlineKeyboardButton("Оплатить доступ", callback_data='to_payment')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.effective_message.reply_text(
                text=f"""Вы в основном меню""",
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            return 'MAIN_MENU'

        def show_dishes(update, context):
            query = update.callback_query
            user_first_name = update.effective_user.first_name
            user_id = update.effective_user.id
            context.user_data['user_first_name'] = user_first_name
            context.user_data['user_id'] = user_id

            keyboard = [
                [
                    InlineKeyboardButton("<", callback_data='prev_dish'),
                    InlineKeyboardButton("Подробнее", callback_data='dish_info'),
                    InlineKeyboardButton(">", callback_data='next_dish'),
                ],
                [
                    InlineKeyboardButton("В главное меню", callback_data='menu'),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            cur_meal = Meal.objects.get(id=context.user_data["cur_dish_id"])
            #print(Meal.objects.all())
            update.effective_message.reply_photo(
                photo=open('C:/Users/Honor/Documents/GitHub/FoodPlan/media/borsh-so-smetanoj.jpg', 'rb'),
                caption=f"""{cur_meal.name}. Тип блюда - {cur_meal.type_of_meal.type_name}""",
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            return 'CUR_DISH'

        def cur_dish_info(update, context):
            query = update.callback_query
            user_first_name = update.effective_user.first_name
            user_id = update.effective_user.id
            context.user_data['user_first_name'] = user_first_name
            context.user_data['user_id'] = user_id

            keyboard = [
                [
                    InlineKeyboardButton("<", callback_data='prev_dish'),
                    InlineKeyboardButton(">", callback_data='next_dish'),
                ],
                [
                    InlineKeyboardButton("Рассчитать стоимость продуктов", callback_data='calculate_cost'),
                ],
                [
                    InlineKeyboardButton("В главное меню", callback_data='menu'),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            cur_meal = Meal.objects.get(id=context.user_data["cur_dish_id"])
            text = ""
            text += f"{cur_meal.name}. Тип блюда - {cur_meal.type_of_meal.type_name}\n{cur_meal.description}\n\n"
            text += "Ингридиенты:\n"
            for ingredient_quant in cur_meal.ingredients_quant.all():
                text += f"\t{ingredient_quant.ingredient.name} {ingredient_quant.quantity}{ingredient_quant.ingredient.uom}\n"
            text += "\n\n"
            text += cur_meal.recipe

            update.effective_message.reply_photo(
                photo=open('C:/Users/Honor/Documents/GitHub/FoodPlan/media/borsh-so-smetanoj.jpg', 'rb'),#cur_meal.image
                caption=text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            return 'DISH_INFO'

        def next_dish(update, context):
            if context.user_data["cur_dish_id"] < Meal.objects.all().count():
                print(Meal.objects.get(id=context.user_data["cur_dish_id"]))
                context.user_data["cur_dish_id"] += 1
                print(Meal.objects.get(id=context.user_data["cur_dish_id"]))
                return show_dishes(update, context)

        def prev_dish(update, context):
            if context.user_data["cur_dish_id"] > 1:
                print(Meal.objects.get(id=context.user_data["cur_dish_id"]))
                context.user_data["cur_dish_id"] -= 1
                print(Meal.objects.get(id=context.user_data["cur_dish_id"]))
                return show_dishes(update, context)

        def show_filters(update, context): pass
        def calculate_cost(update, context): pass

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start_conversation)],
            states={
                'GREETINGS': [
                    CallbackQueryHandler(menu, pattern='to_menu'),
                    CallbackQueryHandler(paid, pattern='to_payment'),
                ],
                'MAIN_MENU': [
                    CallbackQueryHandler(show_dishes, pattern='to_dishes'),
                    CallbackQueryHandler(show_filters, pattern='to_filters'),
                    CallbackQueryHandler(paid, pattern='to_payment'),
                ],
                'CUR_DISH': [
                    CallbackQueryHandler(prev_dish, pattern='prev_dish'),
                    CallbackQueryHandler(next_dish, pattern='next_dish'),
                    CallbackQueryHandler(cur_dish_info, pattern='dish_info'),
                    CallbackQueryHandler(menu, pattern='menu'),
                ],
                'DISH_INFO': [
                    CallbackQueryHandler(prev_dish, pattern='prev_dish'),
                    CallbackQueryHandler(next_dish, pattern='next_dish'),
                    CallbackQueryHandler(calculate_cost, pattern='calculate_cost'),
                    CallbackQueryHandler(menu, pattern='menu'),
                ],
            },
            fallbacks=[CommandHandler('cancel', cancel)]
        )
        cur_dish_id = 1

        dispatcher.add_handler(conv_handler)
        dispatcher.bot_data["cur_dish_id"] = 1
        start_handler = CommandHandler('start', start_conversation)
        dispatcher.add_handler(start_handler)
        dispatcher.add_handler(CallbackQueryHandler(start_conversation, pattern='to_start'))
        updater.start_polling()
        updater.idle()

