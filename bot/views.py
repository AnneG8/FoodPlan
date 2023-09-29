import calendar
from datetime import timedelta, date
from django.shortcuts import render, get_object_or_404
from bot.models import Client


def is_sub_paid(id_telegram):
	user = get_object_or_404(Client, id_telegram=id_telegram)
	return user.is_paid_up


def get_new_payment_date(curr_date: date = date.today()) -> date:
	days_in_month = calendar.monthrange(curr_date.year, curr_date.month)[1]
	return curr_date + timedelta(days=days_in_month)


