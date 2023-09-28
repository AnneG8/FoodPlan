from django.contrib import admin
from bot.models import Ingredient, MealType, Meal, Client

admin.site.register(Ingredient)
admin.site.register(MealType)
admin.site.register(Meal)
admin.site.register(Client)
