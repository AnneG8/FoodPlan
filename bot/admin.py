from django.contrib import admin
from bot.models import (Ingredient, MealType, Meal, Client, 
                        IngredientQuantity, Revenue)


class IngredientQuantityInline(admin.TabularInline):
    model = IngredientQuantity
    fields = ['ingredient', 'quantity']


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    search_fields = ['name',]
    list_display = ['name', ]


@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    search_fields = ['name',] 
    list_display = ['name', 'type_of_meal', 'get_caloric_value', 'is_recommended',] # количество калорий 'сalories',
    list_editable = ['is_recommended',]
    list_filter = ['is_recommended', 'type_of_meal',]
    inlines = [IngredientQuantityInline,]


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    search_fields = ['name',]
    #readonly_fields нужно ли запретить менять is_paid_up, id_telegram и name?
    list_display = ['id_telegram', 'name', 'is_paid_up',]    #telegram_url
    list_filter = ['is_paid_up',]
    raw_id_fields = ('likes', 'dislikes', )


@admin.register(Revenue)
class RevenueAdmin(admin.ModelAdmin):
    ordering = ['-month',]
    readonly_fields = ['month', 'max_сalories',]


admin.site.register(MealType)
