import datetime
import telegram
from pathlib import Path
import sys
from bot.models import *
from FoodPlan.settings import TG_BOT_TOKEN
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

        tg_token = TG_BOT_TOKEN
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
                    InlineKeyboardButton("Оплатить подписку", callback_data='to_payment'),
                ] if not Client.objects.get(id_telegram=user_id).is_paid_up else
                [
                    InlineKeyboardButton("Попробовать бесплатно", callback_data='to_menu'),
                    InlineKeyboardButton("Отменить подписку", callback_data='cancel_sub')
                ],
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
            context.user_data["cur_dish_id"] = 0

            if Client.objects.get(id_telegram=user_id).is_paid_up:
                keyboard = [
                    [
                        InlineKeyboardButton("Выбрать блюдо", callback_data='to_dishes'),
                        InlineKeyboardButton("Настроить фильтр", callback_data='to_filters'),
                    ],
                    [
                        InlineKeyboardButton("Отменить подписку", callback_data='cancel_sub')
                    ]
                ]
            else:
                keyboard = [
                    [
                        InlineKeyboardButton("Выбрать блюдо", callback_data='to_dishes'),
                        InlineKeyboardButton("Оплатить подписку", callback_data='to_payment')
                    ],
                ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            update.effective_message.reply_photo(
                photo=open("C:/Users/Honor/Documents/GitHub/FoodPlan/media/img.png", "rb"),
                caption=f"""Основное меню""",
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
            cur_meal = Meal.objects.all()[context.user_data["cur_dish_id"]]
            print(cur_meal.name)
            update.effective_message.reply_photo(
                photo=cur_meal.image,
                caption=f"""<b>{cur_meal.name}</b>.
<i>Калорийность - {cur_meal.get_caloric_value()} ккал</i>

{cur_meal.description}""",
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
            cur_meal = Meal.objects.all()[context.user_data["cur_dish_id"]]
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
            cur_dish = Meal.objects.all()[context.user_data["cur_dish_id"]]
            Client.objects.get(id_telegram=context.user_data["user_id"]).dislikes.remove(cur_dish)
            Client.objects.get(id_telegram=context.user_data["user_id"]).likes.add(cur_dish)
            update.effective_message.reply_text(
                text=f"""Блюдо "{cur_dish.name}"добавлено в ❤ Избранное""",
                parse_mode=ParseMode.HTML
            )
            return 'DISH_INFO'

        def dislike_dish(update, context):
            cur_dish = Meal.objects.all()[context.user_data["cur_dish_id"]]
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
                if context.user_data["cur_dish_id"] < Meal.objects.all().count()-1:
                    context.user_data["cur_dish_id"] += 1
                    return show_dishes(update, context)
            else:
                if context.user_data["cur_dish_id"] < 3:
                    context.user_data["cur_dish_id"] += 1
                    return show_dishes(update, context)

        def prev_dish(update, context):
            if context.user_data["cur_dish_id"] >= 1:
                print(Meal.objects.all()[context.user_data["cur_dish_id"]])
                context.user_data["cur_dish_id"] -= 1
                print(Meal.objects.all()[context.user_data["cur_dish_id"]])
                return show_dishes(update, context)

        def show_filters(update, context): pass

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
        
        def success_pay(update, context):
            keyboard = [
                [
                    InlineKeyboardButton("В главное меню", callback_data='to_menu'),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            client = Client.objects.get(id_telegram=context.user_data["user_id"])
            client.is_paid_up = True
            client.save()
            update.effective_message.reply_text(
                # photo=cur_meal.image,
                text="Подписка успешно оформлена✅",
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            return 'SUCCESS_PAYMENT'

        def cancel_sub(update, context):
            keyboard = [
                [
                    InlineKeyboardButton("Подтвердить отмену", callback_data='confirm'),
                    InlineKeyboardButton("Назад", callback_data='to_menu'),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.effective_message.reply_text(
                # photo=cur_meal.image,
                text="Подтвердите отмену подписки",
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            return "CANCEL_SUB"

        def success_cancel_sub(update, context):
            keyboard = [
                [
                    InlineKeyboardButton("В главное меню", callback_data='to_menu'),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            client = Client.objects.get(id_telegram=context.user_data["user_id"])
            client.is_paid_up = False
            client.save()
            update.effective_message.reply_text(
                # photo=cur_meal.image,
                text="Подписка успешно отменена✅",
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            return 'SUCCESS_CANCEL_SUB'

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start_conversation)],
            states={
                'GREETINGS': [
                    CallbackQueryHandler(menu, pattern='to_menu'),
                    CallbackQueryHandler(send_invoice, pattern='to_payment'),
                    CallbackQueryHandler(cancel_sub, pattern='cancel_sub'),
                ],
                'MAIN_MENU': [
                    CallbackQueryHandler(show_dishes, pattern='to_dishes'),
                    CallbackQueryHandler(show_filters, pattern='to_filters'),
                    CallbackQueryHandler(send_invoice, pattern='to_payment'),
                    CallbackQueryHandler(cancel_sub, pattern='cancel_sub'),
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
                    CallbackQueryHandler(show_dishes, pattern='to_dishes'),
                ],
                'SEND_INVOICE': [
                    CallbackQueryHandler(success_pay, pattern='confirm'),
                    CallbackQueryHandler(menu, pattern='to_menu'),
                    # CallbackQueryHandler(make_order, pattern='cancel'),
                ],
                'SUCCESS_PAYMENT': [
                    CallbackQueryHandler(menu, pattern='to_menu'),
                ],
                'CANCEL_SUB': [
                    CallbackQueryHandler(success_cancel_sub, pattern='confirm'),
                    CallbackQueryHandler(menu, pattern='to_menu'),
                    # CallbackQueryHandler(make_order, pattern='cancel'),
                ],
                'SUCCESS_CANCEL_SUB': [
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

        dispatcher.add_handler(conv_handler)
        dispatcher.bot_data["cur_dish_id"] = 1
        start_handler = CommandHandler('start', start_conversation)
        dispatcher.add_handler(start_handler)
        dispatcher.add_handler(CallbackQueryHandler(start_conversation, pattern='to_start'))
        updater.start_polling()
        updater.idle()

