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
            reply_markup = InlineKeyboardMarkup(keyboard)
            cur_meal = Meal.objects.get(id=context.user_data["cur_dish_id"])
            text = ""
            text += f"{cur_meal.name}. Тип блюда - {cur_meal.type_of_meal.type_name}\n{cur_meal.description}\n"
            text += f"Калорийность - {cur_meal.get_caloric_value()} ккал\n\n"
            text += "Ингридиенты:\n"
            for ind, ingredient_quant in enumerate(cur_meal.ingredients_quant.all()):
                text += f"\t\t{ind+1}. {ingredient_quant.ingredient.name} {ingredient_quant.quantity}{ingredient_quant.ingredient.uom}\n"
            text += "\n\n"
            text += cur_meal.recipe

            update.effective_message.reply_photo(
                photo=cur_meal.image,
                caption=text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            return 'DISH_INFO'

        def next_dish(update, context):
            cur_client = Client.objects.get(id_telegram=context.user_data["user_id"])
            if cur_client.is_paid_up:
                if context.user_data["cur_dish_id"] < Meal.objects.all().count():
                    print(Meal.objects.get(id=context.user_data["cur_dish_id"]))
                    context.user_data["cur_dish_id"] += 1
                    print(Meal.objects.get(id=context.user_data["cur_dish_id"]))
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
            # token_pay = settings.token_pay # ЗАМЕНИЛ СТРОКУ
            token_pay = os.getenv("PAYMENT_TOKEN")
            print(token_pay)

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
            print(type(query))
            try:
                pass
            except:
                context.bot.answer_pre_checkout_query(
                    pre_checkout_query_id=query.id,
                    ok=False,
                    error_message="Что-то пошло не так...",
                )
            else:
                context.bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=True)

        def success_payment(update, context):
            '''Обработка успешной оплаты'''
            amount = update.message.successful_payment.total_amount / 100
            text = f'✅ Спасибо за оплату {amount} руб.!\n\n'
            keyboard = [
                [InlineKeyboardButton("На главную", callback_data="menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=telegram.ParseMode.HTML,
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
                    CallbackQueryHandler(calculate_cost, pattern='calculate_cost'),
                    CallbackQueryHandler(show_dishes, pattern='to_dishes'),
                ],
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

