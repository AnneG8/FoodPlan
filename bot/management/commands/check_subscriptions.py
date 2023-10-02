import schedule
import time
from django.core.management.base import BaseCommand
from django.shortcuts import get_object_or_404
from datetime import date
from bot.models import Client, Revenue
from bot.views import get_new_payment_date
from FoodPlan.settings import SUBS_PRICE


def get_curr_month_revenue(today: date = date.today()):
    curr_month_revenue = Revenue.objects.latest('month')
    last_month = curr_month_revenue.month
    if last_month != today.replace(day=1):
        curr_month_revenue = Revenue.objects.create()
    return curr_month_revenue


def check_subscriptions():
    today = date.today()
    curr_month_revenue = get_curr_month_revenue(today)

    clients = Client.objects.all()
    for client in clients():
        if client.payment_date != today:
            continue

        if client.renew_sub:
            curr_month_revenue.revenue_sum += SUBS_PRICE
            curr_month_revenue.save()
            client.payment_date = get_new_payment_date(client.payment_date)
        else:
            client.is_paid_up = False
            client.payment_date = None
        client.save()


class Command(BaseCommand):
    help = 'проверка наличия подписок'

    if not Revenue.objects.all():
        Revenue.objects.create()

    schedule.every().day.at('00:00', 'Europe/Moscow').do(check_subscriptions)
    while True:
        schedule.run_pending()
        time.sleep(1)
