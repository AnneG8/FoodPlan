from django.shortcuts import render, get_object_or_404
from bot.models import Client


def is_sub_paid(id_telegram):
	user = get_object_or_404(Client, id_telegram=id_telegram)
	return user.is_paid_up




