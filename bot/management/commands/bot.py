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

            if not Client.objects.filter(id_telegram=user_id).exists():
                Client.objects.create(
                    id_telegram=user_id,
                    name=user_first_name,
                    is_paid_up=False
                )

            keyboard = [
                [
                    InlineKeyboardButton("Попробовать бесплатно", callback_data='to_menu'),
                    InlineKeyboardButton("Оплатить доступ", callback_data='to_payment'),
                ]

            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.effective_message.reply_photo(
                photo=open('C:/Users/Honor/Documents/GitHub/FoodPlan/media/greetings.jpg', 'rb'),
                caption=f"""<b>Шефом может стать каждый!\nПоможем быстро и легко приготовить блюдо дня!</b>""",
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
                ] if Client.objects.get(id_telegram=user_id).is_paid_up else
                [
                    InlineKeyboardButton("Выбрать блюдо", callback_data='to_dishes'),
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
                    InlineKeyboardButton("<<", callback_data='prev_dish'),
                    InlineKeyboardButton("Рецепт", callback_data='dish_info'),
                    InlineKeyboardButton(">>", callback_data='next_dish'),
                ],
                [
                    InlineKeyboardButton("В главное меню", callback_data='menu'),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            cur_meal = Meal.objects.get(id=context.user_data["cur_dish_id"])
            print(cur_meal.name)
            update.effective_message.reply_photo(
                photo=cur_meal.image,
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
                    InlineKeyboardButton("Рассчитать стоимость продуктов", callback_data='calculate_cost'),
                ],
                [
                    InlineKeyboardButton("К выбору блюд", callback_data='to_dishes'),
                ],
            ]
            if Client.objects.get(id_telegram=user_id).is_paid_up: keyboard.insert(
                0, [
                    InlineKeyboardButton("❤", callback_data='like_dish'),
                    InlineKeyboardButton("👎", callback_data='dislike_dish'),
                   ],
            )
            reply_markup = InlineKeyboardMarkup(keyboard)
            cur_meal = Meal.objects.get(id=context.user_data["cur_dish_id"])
            text = ""
            text += f"""<b>{cur_meal.name}</b>. 
<i>Тип блюда - {cur_meal.type_of_meal.type_name}</i>

{cur_meal.description}

Калорийность - {cur_meal.get_caloric_value()} ккал
Ингредиенты:

"""
            for ind, ingredient_quant in enumerate(cur_meal.ingredients_quant.all()):
                text += f"{ind+1}. {ingredient_quant.ingredient.name} {ingredient_quant.quantity}{ingredient_quant.ingredient.uom}\n"
            text += "\n"
            text += cur_meal.recipe

            update.effective_message.reply_text(
                #photo=cur_meal.image,
                text=text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            return 'DISH_INFO'

        def like_dish(update, context):
            cur_dish = Meal.objects.get(id=cur_dish_id)
            Client.objects.get(id_telegram=context.user_data["user_id"]).dislikes.remove(cur_dish)
            Client.objects.get(id_telegram=context.user_data["user_id"]).likes.add(cur_dish)
            update.effective_message.reply_text(
                text=f"""Блюдо "{cur_dish.name}"добавлено в ❤ Избранное""",
                parse_mode=ParseMode.HTML
            )
            return 'DISH_INFO'

        def dislike_dish(update, context):
            cur_dish = Meal.objects.get(id=cur_dish_id)
            Client.objects.get(id_telegram=context.user_data["user_id"]).likes.remove(cur_dish)
            Client.objects.get(id_telegram=context.user_data["user_id"]).dislikes.add(cur_dish)
            update.effective_message.reply_text(
                text=f"""Блюдо "{cur_dish.name}"добавлено в 👎 Черный список""",
                parse_mode=ParseMode.HTML
            )
            return 'DISH_INFO'

        def next_dish(update, context):
            cur_client = Client.objects.get(id_telegram=context.user_data["user_id"])
            if cur_client.is_paid_up:
                if context.user_data["cur_dish_id"] < Meal.objects.all().count():
                    print(Meal.objects.get(id=context.user_data["cur_dish_id"]))
                    context.user_data["cur_dish_id"] += 1
                    for id in Meal.objects.all():
                        print(id.name, id.id)
                    if context.user_data["cur_dish_id"] == 7:
                        context.user_data["cur_dish_id"] = 8
                    #print(Meal.objects.get(id=context.user_data["cur_dish_id"]))
                    return show_dishes(update, context)
            else:
                if context.user_data["cur_dish_id"] < 3:
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

        def send_invoice(update, context):
            keyboard = [
                [
                    InlineKeyboardButton("Подтвердить", callback_data='confirm'),
                    InlineKeyboardButton("Назад", callback_data='to_menu'),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.effective_message.reply_text(
                # photo=cur_meal.image,
                text="Оплатить подписку на 1 месяц 500,00 RUB",
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            return "SEND_INVOICE"
        
        def sucсess_pay(update, context):
            keyboard = [
                [
                    InlineKeyboardButton("В главное меню", callback_data='to_menu'),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            update.effective_message.reply_text(
                # photo=cur_meal.image,
                text="Подписка успшено оформлена✅",
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            return 'SUCCESS_PAYMENT'

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start_conversation)],
            states={
                'GREETINGS': [
                    CallbackQueryHandler(menu, pattern='to_menu'),
                    CallbackQueryHandler(send_invoice, pattern='to_payment'),
                ],
                'MAIN_MENU': [
                    CallbackQueryHandler(show_dishes, pattern='to_dishes'),
                    CallbackQueryHandler(show_filters, pattern='to_filters'),
                    CallbackQueryHandler(send_invoice, pattern='to_payment'),
                ],
                'CUR_DISH': [
                    CallbackQueryHandler(prev_dish, pattern='prev_dish'),
                    CallbackQueryHandler(next_dish, pattern='next_dish'),
                    CallbackQueryHandler(cur_dish_info, pattern='dish_info'),
                    CallbackQueryHandler(menu, pattern='menu'),
                ],
                'DISH_INFO': [
                    CallbackQueryHandler(like_dish, pattern='like_dish'),
                    CallbackQueryHandler(dislike_dish, pattern='dislike_dish'),
                    CallbackQueryHandler(calculate_cost, pattern='calculate_cost'),
                    CallbackQueryHandler(show_dishes, pattern='to_dishes'),
                ],
                'SEND_INVOICE': [
                    CallbackQueryHandler(sucсess_pay, pattern='confirm'),
                    CallbackQueryHandler(menu, pattern='to_menu'),
                    # CallbackQueryHandler(make_order, pattern='cancel'),
                ],
                'SUCCESS_PAYMENT': [
                    CallbackQueryHandler(menu, pattern='to_menu'),
                ],
                # 'PROCESS_PRE_CHECKOUT': [
                #     PreCheckoutQueryHandler(process_pre_checkout_query),
                #     CallbackQueryHandler(success_payment,
                #                          pattern='success_payment'),
                # ],
                # 'SUCCESS_PAYMENT': [
                #     CallbackQueryHandler(start_conversation,
                #                          pattern='to_start'),
                # ],
            },
            fallbacks=[CommandHandler('cancel', cancel)],
            per_chat=False
        )
        cur_dish_id = 1

        dispatcher.add_handler(conv_handler)
        dispatcher.bot_data["cur_dish_id"] = 1
        start_handler = CommandHandler('start', start_conversation)
        dispatcher.add_handler(start_handler)
        dispatcher.add_handler(CallbackQueryHandler(start_conversation, pattern='to_start'))
        updater.start_polling()
        updater.idle()

