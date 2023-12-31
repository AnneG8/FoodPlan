import telegram
import os
from datetime import date
from django.core.management.base import BaseCommand
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
from bot.views import get_new_payment_date, get_new_dish_id
from FoodPlan.settings import TG_BOT_TOKEN, STATIC_ROOT, SUBS_PRICE
from bot.models import *


class Command(BaseCommand):
    def handle(self, *args, **kwargs):

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
                    name=user_first_name
                )

            keyboard = [
                [
                    InlineKeyboardButton("Попробовать бесплатно", callback_data='to_menu'),
                    InlineKeyboardButton("Оплатить подписку", callback_data='to_payment'),
                ] if not Client.objects.get(id_telegram=user_id).renew_sub else
                [
                    InlineKeyboardButton("В главное меню", callback_data='to_menu'),
                    InlineKeyboardButton("Отменить подписку", callback_data='cancel_sub')
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            filepath = os.path.join(STATIC_ROOT, 'greetings.jpg')
            with open(filepath, 'rb') as file:
                update.effective_message.reply_photo(
                    photo=file,
                    caption=f"""<b>Шефом может стать каждый!\nПоможем быстро и легко приготовить блюдо дня!</b>""",
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
            return 'GREETINGS'

        def menu(update, context):
            query = update.callback_query
            user_first_name = update.effective_user.first_name
            user_id = update.effective_user.id
            context.user_data['user_first_name'] = user_first_name
            context.user_data['user_id'] = user_id
            context.user_data["cur_dish_id"] = 0

            context.user_data["is_showing_likes"] = False
            context.user_data["is_showing_dislikes"] = False

            client = Client.objects.get(id_telegram=user_id)
            settings = Settings.objects.get_or_create(client=client)[0]
            settings.save()

            if client.is_paid_up:
                keyboard = [
                    [
                        InlineKeyboardButton("Выбрать блюдо", callback_data='to_dishes'),
                    ],
                    [
                        InlineKeyboardButton("Избранное", callback_data='liked'),
                        InlineKeyboardButton("Черный список", callback_data='disliked')
                    ],
                    [
                        InlineKeyboardButton("Настроить фильтр", callback_data='to_filters'),
                        InlineKeyboardButton("Оплатить подписку", callback_data='to_payment')
                        if not Client.objects.get(id_telegram=user_id).renew_sub else
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
            filepath = os.path.join(STATIC_ROOT, 'img.png')
            with open(filepath, 'rb') as file:
                update.effective_message.reply_photo(
                    photo=file,
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
                    InlineKeyboardButton("В главное меню", callback_data='to_menu'),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            client = Client.objects.get(id_telegram=context.user_data["user_id"])

            if context.user_data["is_showing_likes"]:
                filtered_dishes = client.likes.all()
            elif context.user_data["is_showing_dislikes"]:
                filtered_dishes = client.dislikes.all()
            else:
                types_to_filter = list(client.settings.type_of_meal.all())
                if types_to_filter:
                    filtered_dishes = Meal.objects.filter(type_of_meal__in=types_to_filter)
                else:
                    filtered_dishes = Meal.objects.all()

                if client.settings.min_сalories:
                    for meal in filtered_dishes:
                        if meal.get_caloric_value() < client.settings.min_сalories:
                            filtered_dishes = filtered_dishes.exclude(id__in=[meal.id])
                if client.settings.max_сalories:
                    for meal in filtered_dishes:
                        if meal.get_caloric_value() > client.settings.max_сalories:
                            filtered_dishes = filtered_dishes.exclude(id__in=[meal.id])

                ingrs_to_filter = list(client.settings.chosen_ingrs.all())
                if ingrs_to_filter:
                    filtered_dishes = filtered_dishes.filter(ingredients_quant__ingredient__in=ingrs_to_filter)

                ingrs_to_filter = list(client.settings.excluded_ingrs.all())
                if ingrs_to_filter:
                    filtered_dishes = filtered_dishes.exclude(ingredients_quant__ingredient__in=ingrs_to_filter)

                dishes_ids = [i.id for i in client.dislikes.all()]
                filtered_dishes = filtered_dishes.exclude(id__in=dishes_ids)

            context.user_data["filtered_dishes"] = filtered_dishes
            if filtered_dishes.count() == 0:
                update.effective_message.reply_text(
                    text="Блюд по таким фильтрам не найдено",
                    parse_mode=ParseMode.HTML
                )
                return menu(update, context)

            cur_dish_id = context.user_data["cur_dish_id"]
            cur_meal = filtered_dishes[cur_dish_id]
            text = ""
            if cur_meal in list(client.likes.all()):
                text += "❤ "
            text += f"""<b>Блюдо №{cur_dish_id + 1}: {cur_meal.name}</b>.
<i>Калорийность - {cur_meal.get_caloric_value()} ккал</i>

{cur_meal.description}"""
            update.effective_message.reply_photo(
                photo=cur_meal.image,
                caption=text,
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
            cur_meal = context.user_data["filtered_dishes"][context.user_data["cur_dish_id"]]
            text = ""
            if context.user_data["is_showing_likes"]:
                text += "❤ "
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
                text=text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            return 'DISH_INFO'

        def show_likes(update, context):
            context.user_data["is_showing_likes"] = True
            return show_dishes(update, context)

        def show_dislikes(update, context):
            context.user_data["is_showing_dislikes"] = True
            return show_dishes(update, context)

        def like_dish(update, context):
            cur_dish = context.user_data["filtered_dishes"][context.user_data["cur_dish_id"]]
            Client.objects.get(id_telegram=context.user_data["user_id"]).dislikes.remove(cur_dish)
            Client.objects.get(id_telegram=context.user_data["user_id"]).likes.add(cur_dish)
            update.effective_message.reply_text(
                text=f"""Блюдо "{cur_dish.name}"добавлено в ❤ Избранное""",
                parse_mode=ParseMode.HTML
            )
            return cur_dish_info(update, context)

        def dislike_dish(update, context):
            cur_dish = context.user_data["filtered_dishes"][context.user_data["cur_dish_id"]]
            Client.objects.get(id_telegram=context.user_data["user_id"]).likes.remove(cur_dish)
            Client.objects.get(id_telegram=context.user_data["user_id"]).dislikes.add(cur_dish)
            update.effective_message.reply_text(
                text=f"""Блюдо "{cur_dish.name}"добавлено в 👎 Черный список""",
                parse_mode=ParseMode.HTML
            )
            return cur_dish_info(update, context)

        def next_dish(update, context):
            cur_client = Client.objects.get(id_telegram=context.user_data["user_id"])
            last_id = context.user_data["cur_dish_id"]
            if cur_client.is_paid_up:
                count_dishes = context.user_data["filtered_dishes"].count()
            else:
                count_dishes = 3
            context.user_data["cur_dish_id"] = get_new_dish_id(last_id, count_dishes - 1, 'next')
            return show_dishes(update, context)

        def prev_dish(update, context):
            cur_client = Client.objects.get(id_telegram=context.user_data["user_id"])
            last_id = context.user_data["cur_dish_id"]
            if cur_client.is_paid_up:
                count_dishes = context.user_data["filtered_dishes"].count()
            else:
                count_dishes = 3
            context.user_data["cur_dish_id"] = get_new_dish_id(last_id, count_dishes - 1, 'prev')
            return show_dishes(update, context)

        def show_filters(update, context):
            keyboard = [
                [
                    InlineKeyboardButton("По типу блюда", callback_data='filter_type'),
                ],
                [
                    InlineKeyboardButton("По минимальной калорийности", callback_data='filter_minkal'),
                ],
                [
                    InlineKeyboardButton("По максимальной калорийности", callback_data='filter_maxkal'),
                ],
                [
                    InlineKeyboardButton("По ингредиенту", callback_data='filter_ingr'),
                ],
                [
                    InlineKeyboardButton("Исключить ингредиент", callback_data='filter_rem_ingr'),
                ],
                [
                    InlineKeyboardButton("Сбросить фильтры", callback_data='filter_reset'),
                ],
                [
                    InlineKeyboardButton("Назад", callback_data='to_menu'),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            update.effective_message.reply_text(
                text="Настроить фильтр",
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            return "CHOOSE_FILTER"

        def filter_type(update, context):
            keyboard = []
            for i in range(MealType.objects.all().count()):
                keyboard.append([
                    InlineKeyboardButton(MealType.objects.all()[i].type_name, callback_data=f'filter_type_ch{i+1}'),
                ])
            reply_markup = InlineKeyboardMarkup(keyboard)

            update.effective_message.reply_text(
                text="Фильтр по типу блюда",
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            return "FILTER_TYPE"

        def filter_type_chd(update, context):
            update.effective_message.reply_text(
                text=f"""Блюда отфильтрованы по типу '{MealType.objects.all()[context.user_data["ch_type"]].type_name}'""",
                parse_mode=ParseMode.HTML
            )
            Client.objects.get(id_telegram=context.user_data["user_id"]).settings.type_of_meal.add(MealType.objects.all()[context.user_data["ch_type"]])
            Client.objects.get(id_telegram=context.user_data["user_id"]).settings.save()
            return show_filters(update, context)

        def filter_type_ch_1(update, context):
            context.user_data["ch_type"] = 0
            return filter_type_chd(update, context)

        def filter_type_ch_2(update, context):
            context.user_data["ch_type"] = 1
            return filter_type_chd(update, context)

        def filter_type_ch_3(update, context):
            context.user_data["ch_type"] = 2
            return filter_type_chd(update, context)

        def filter_type_ch_4(update, context):
            context.user_data["ch_type"] = 3
            return filter_type_chd(update, context)

        def filter_type_ch_5(update, context):
            context.user_data["ch_type"] = 4
            return filter_type_chd(update, context)

        def filter_type_ch_6(update, context):
            context.user_data["ch_type"] = 5
            return filter_type_chd(update, context)

        def filter_type_ch_7(update, context):
            context.user_data["ch_type"] = 6
            return filter_type_chd(update, context)

        def filter_type_ch_8(update, context):
            context.user_data["ch_type"] = 7
            return filter_type_chd(update, context)

        def filter_type_ch_9(update, context):
            context.user_data["ch_type"] = 8
            return filter_type_chd(update, context)

        def filter_type_ch_10(update, context):
            context.user_data["ch_type"] = 9
            return filter_type_chd(update, context)

        def filter_ingr(update, context):
            keyboard = [
                [
                    InlineKeyboardButton("Назад", callback_data='to_filters'),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.effective_message.reply_text(
                # photo=cur_meal.image,
                reply_markup=reply_markup,
                text="Введите ингредиент, который должен быть в блюде",
                parse_mode=ParseMode.HTML
            )
            return 'FILTER_INGR'

        def choose_ingr(update, context):
            keyboard = []
            find_ingrs = Ingredient.objects.filter(name__contains=update.message.text.lower())
            for i in range(find_ingrs.count()):
                keyboard.append([
                    InlineKeyboardButton(find_ingrs[i].name, callback_data=f'filter_ingr_ch{i+1}'),
                ])
            keyboard.append([InlineKeyboardButton("Уточнить поиск", callback_data='filter_ingr')])
            keyboard.append([InlineKeyboardButton("Назад", callback_data='to_filters')])
            if find_ingrs.count() == 0:
                keyboard = [
                    [InlineKeyboardButton("Уточнить поиск", callback_data='filter_ingr')],
                    [InlineKeyboardButton("Назад", callback_data='to_filters')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                update.effective_message.reply_text(
                    text="Таких ингредиентов не найдено. Уточните название",
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
                return "FILTER_INGR_CH"
            reply_markup = InlineKeyboardMarkup(keyboard)

            update.effective_message.reply_text(
                text="Фильтр по содержанию ингредиента",
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            context.user_data["finded_ingrs"] = find_ingrs
            return "FILTER_INGR_CH"

        def filter_ingr_chd(update, context):
            update.effective_message.reply_text(
                text=f"""Блюда отфильтрованы по ингредиенту '{context.user_data["finded_ingrs"][context.user_data["ch_ingr"]].name}'""",
                parse_mode=ParseMode.HTML
            )
            Client.objects.get(id_telegram=context.user_data["user_id"]).settings.chosen_ingrs.add(context.user_data["finded_ingrs"][context.user_data["ch_ingr"]])
            Client.objects.get(id_telegram=context.user_data["user_id"]).settings.save()
            return show_filters(update, context)

        def filter_ingr_ch_1(update, context):
            context.user_data["ch_ingr"] = 0
            return filter_ingr_chd(update, context)

        def filter_ingr_ch_2(update, context):
            context.user_data["ch_ingr"] = 1
            return filter_ingr_chd(update, context)

        def filter_ingr_ch_3(update, context):
            context.user_data["ch_ingr"] = 2
            return filter_ingr_chd(update, context)

        def filter_ingr_ch_4(update, context):
            context.user_data["ch_ingr"] = 3
            return filter_ingr_chd(update, context)

        def filter_ingr_ch_5(update, context):
            context.user_data["ch_ingr"] = 4
            return filter_ingr_chd(update, context)

        def filter_rem_ingr(update, context):
            keyboard = [
                [
                    InlineKeyboardButton("Назад", callback_data='to_filters'),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.effective_message.reply_text(
                # photo=cur_meal.image,
                reply_markup=reply_markup,
                text="Введите ингредиент, которого не должно быть в блюде",
                parse_mode=ParseMode.HTML
            )
            return 'FILTER_REM_INGR'

        def choose_rem_ingr(update, context):
            keyboard = []
            find_ingrs = Ingredient.objects.filter(name__contains=update.message.text.lower())
            for i in range(find_ingrs.count()):
                keyboard.append([
                    InlineKeyboardButton(find_ingrs[i].name, callback_data=f'filter_rem_ingr_ch{i+1}'),
                ])
            keyboard.append([InlineKeyboardButton("Уточнить поиск", callback_data='filter_rem_ingr')])
            keyboard.append([InlineKeyboardButton("Назад", callback_data='to_filters')])
            if find_ingrs.count() == 0:
                keyboard = [
                    [InlineKeyboardButton("Уточнить поиск", callback_data='filter_rem_ingr')],
                    [InlineKeyboardButton("Назад", callback_data='to_filters')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                update.effective_message.reply_text(
                    text="Таких ингредиентов не найдено. Уточните название",
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
                return "FILTER_REM_INGR_CH"
            reply_markup = InlineKeyboardMarkup(keyboard)

            update.effective_message.reply_text(
                text="Фильтр по содержанию ингредиенту",
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            context.user_data["finded_ingrs"] = find_ingrs
            return "FILTER_REM_INGR_CH"

        def filter_rem_ingr_chd(update, context):
            update.effective_message.reply_text(
                text=f"""Блюда с ингредиентом '{context.user_data["finded_ingrs"][context.user_data["ch_ingr"]].name}' успешно удалены""",
                parse_mode=ParseMode.HTML
            )
            Client.objects.get(id_telegram=context.user_data["user_id"]).settings.excluded_ingrs.add(context.user_data["finded_ingrs"][context.user_data["ch_ingr"]])
            Client.objects.get(id_telegram=context.user_data["user_id"]).settings.save()
            return show_filters(update, context)

        def filter_rem_ingr_ch_1(update, context):
            context.user_data["ch_ingr"] = 0
            return filter_rem_ingr_chd(update, context)

        def filter_rem_ingr_ch_2(update, context):
            context.user_data["ch_ingr"] = 1
            return filter_rem_ingr_chd(update, context)

        def filter_rem_ingr_ch_3(update, context):
            context.user_data["ch_ingr"] = 2
            return filter_rem_ingr_chd(update, context)

        def filter_rem_ingr_ch_4(update, context):
            context.user_data["ch_ingr"] = 3
            return filter_rem_ingr_chd(update, context)

        def filter_rem_ingr_ch_5(update, context):
            context.user_data["ch_ingr"] = 4
            return filter_rem_ingr_chd(update, context)

        def filter_minkal(update, context):
            keyboard = [
                [
                    InlineKeyboardButton("Назад", callback_data='to_filters'),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.effective_message.reply_text(
                # photo=cur_meal.image,
                reply_markup=reply_markup,
                text="Введите минимальное количество калорий",
                parse_mode=ParseMode.HTML
            )
            return 'FILTER_MINKAL'

        def choose_minkal(update, context):
            try:
                minkal = int(update.message.text)
            except ValueError:
                keyboard = [
                    [
                        InlineKeyboardButton("Назад", callback_data='to_filters'),
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                update.effective_message.reply_text(
                    reply_markup=reply_markup,
                    text="Введите целое число",
                    parse_mode=ParseMode.HTML
                )
                return 'FILTER_MINKAL'
            settings = Client.objects.get(id_telegram=context.user_data["user_id"]).settings
            settings.min_сalories = minkal
            settings.save()
            update.effective_message.reply_text(
                text="Фильтр применен",
                parse_mode=ParseMode.HTML
            )
            return show_filters(update, context)

        def filter_maxkal(update, context):
            keyboard = [
                [
                    InlineKeyboardButton("Назад", callback_data='to_filters'),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.effective_message.reply_text(
                # photo=cur_meal.image,
                reply_markup=reply_markup,
                text="Введите максимальное количество калорий",
                parse_mode=ParseMode.HTML
            )
            return 'FILTER_MAXKAL'

        def choose_maxkal(update, context):
            try:
                maxkal = int(update.message.text)
            except ValueError:
                keyboard = [
                    [
                        InlineKeyboardButton("Назад", callback_data='to_filters'),
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                update.effective_message.reply_text(
                    reply_markup=reply_markup,
                    text="Введите целое число",
                    parse_mode=ParseMode.HTML
                )
                return 'FILTER_MAXKAL'
            settings = Client.objects.get(id_telegram=context.user_data["user_id"]).settings
            settings.max_сalories = maxkal
            settings.save()
            update.effective_message.reply_text(
                text="Фильтр применен",
                parse_mode=ParseMode.HTML
            )
            return show_filters(update, context)

        def filter_reset(update, context):
            settings = Client.objects.get(id_telegram=context.user_data["user_id"]).settings
            settings.type_of_meal.clear()
            settings.min_сalories = None
            settings.max_сalories = None
            settings.chosen_ingrs.clear()
            settings.excluded_ingrs.clear()
            settings.save()
            update.effective_message.reply_text(
                text="Фильтры успешно сброшены✅",
                parse_mode=ParseMode.HTML
            )
            return show_filters(update, context)

        def send_invoice(update, context):
            keyboard = [
                [
                    InlineKeyboardButton("Подтвердить", callback_data='confirm'),
                    InlineKeyboardButton("Назад", callback_data='to_menu'),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            client = Client.objects.get(id_telegram=update.effective_user.id)
            if client.is_paid_up:
                text = "У вас уже олачена подписка на текущий месяц\nПродлить?"
            else:
                text = "Подписаться?\nСтоимость подписки 500,00 RUB в месяц"

            update.effective_message.reply_text(
                # photo=cur_meal.image,
                text=text,
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
            client.renew_sub = True
            if not client.is_paid_up:
                client.is_paid_up = True
                revenue = Revenue.objects.get_or_create()[0]
                revenue.revenue_sum += SUBS_PRICE
                revenue.save()
                client.payment_date = get_new_payment_date()
            client.save()
            settings = Settings.objects.get_or_create(client=client)[0]
            settings.save()
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
            client.renew_sub = False
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
                    CallbackQueryHandler(show_likes, pattern='liked'),
                    CallbackQueryHandler(show_dislikes, pattern='disliked'),
                    CallbackQueryHandler(send_invoice, pattern='to_payment'),
                    CallbackQueryHandler(cancel_sub, pattern='cancel_sub'),
                ],
                'CUR_DISH': [
                    CallbackQueryHandler(prev_dish, pattern='prev_dish'),
                    CallbackQueryHandler(next_dish, pattern='next_dish'),
                    CallbackQueryHandler(cur_dish_info, pattern='dish_info'),
                    CallbackQueryHandler(menu, pattern='to_menu'),
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
                'CHOOSE_FILTER': [
                    CallbackQueryHandler(filter_type, pattern='filter_type'),
                    CallbackQueryHandler(filter_minkal, pattern='filter_minkal'),
                    CallbackQueryHandler(filter_maxkal, pattern='filter_maxkal'),
                    CallbackQueryHandler(filter_ingr, pattern='filter_ingr'),
                    CallbackQueryHandler(filter_rem_ingr, pattern='filter_rem_ingr'),
                    CallbackQueryHandler(filter_reset, pattern='filter_reset'),
                    CallbackQueryHandler(menu, pattern='to_menu'),
                ],
                'FILTER_TYPE': [
                    CallbackQueryHandler(filter_type_ch_1, pattern='filter_type_ch1'),
                    CallbackQueryHandler(filter_type_ch_2, pattern='filter_type_ch2'),
                    CallbackQueryHandler(filter_type_ch_3, pattern='filter_type_ch3'),
                    CallbackQueryHandler(filter_type_ch_4, pattern='filter_type_ch4'),
                    CallbackQueryHandler(filter_type_ch_5, pattern='filter_type_ch5'),
                    CallbackQueryHandler(filter_type_ch_6, pattern='filter_type_ch6'),
                    CallbackQueryHandler(filter_type_ch_7, pattern='filter_type_ch7'),
                    CallbackQueryHandler(filter_type_ch_8, pattern='filter_type_ch8'),
                    CallbackQueryHandler(filter_type_ch_9, pattern='filter_type_ch9'),
                    CallbackQueryHandler(filter_type_ch_10, pattern='filter_type_ch10'),
                ],
                'FILTER_INGR': [
                    CallbackQueryHandler(show_filters, pattern='to_filters'),
                    MessageHandler(Filters.text & ~Filters.command, choose_ingr),
                ],
                'FILTER_INGR_CH': [
                    CallbackQueryHandler(filter_ingr_ch_1, pattern='filter_ingr_ch1'),
                    CallbackQueryHandler(filter_ingr_ch_2, pattern='filter_ingr_ch2'),
                    CallbackQueryHandler(filter_ingr_ch_3, pattern='filter_ingr_ch3'),
                    CallbackQueryHandler(filter_ingr_ch_4, pattern='filter_ingr_ch4'),
                    CallbackQueryHandler(filter_ingr_ch_5, pattern='filter_ingr_ch5'),
                    CallbackQueryHandler(filter_ingr, pattern='filter_ingr'),
                    CallbackQueryHandler(show_filters, pattern='to_filters'),
                ],
                'FILTER_REM_INGR': [
                    CallbackQueryHandler(show_filters, pattern='to_filters'),
                    MessageHandler(Filters.text & ~Filters.command, choose_rem_ingr),
                ],
                'FILTER_REM_INGR_CH': [
                    CallbackQueryHandler(filter_rem_ingr_ch_1, pattern='filter_rem_ingr_ch1'),
                    CallbackQueryHandler(filter_rem_ingr_ch_2, pattern='filter_rem_ingr_ch2'),
                    CallbackQueryHandler(filter_rem_ingr_ch_3, pattern='filter_rem_ingr_ch3'),
                    CallbackQueryHandler(filter_rem_ingr_ch_4, pattern='filter_rem_ingr_ch4'),
                    CallbackQueryHandler(filter_rem_ingr_ch_5, pattern='filter_rem_ingr_ch5'),
                    CallbackQueryHandler(filter_rem_ingr, pattern='filter_rem_ingr'),
                    CallbackQueryHandler(show_filters, pattern='to_filters'),
                ],
                'FILTER_MINKAL': [
                    CallbackQueryHandler(show_filters, pattern='to_filters'),
                    MessageHandler(Filters.text & ~Filters.command, choose_minkal),
                ],
                'FILTER_MAXKAL': [
                    CallbackQueryHandler(show_filters, pattern='to_filters'),
                    MessageHandler(Filters.text & ~Filters.command, choose_maxkal),
                ]
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

