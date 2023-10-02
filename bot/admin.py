from django.contrib import admin
from bot.models import (Ingredient, MealType, Meal, Client, 
                        IngredientQuantity, Revenue)


class IngredientQuantityInline(admin.TabularInline):
    model = IngredientQuantity
    extra = 1
    fields = ['ingredient', 'quantity', ] #'ingredient__uom',


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    search_fields = ['name',]
    list_display = ['name', ]
    ordering = ['name',]


@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    search_fields = ['name',] 
    list_display = ['name', 'type_of_meal', 'get_caloric_value', 'is_recommended',]
    list_editable = ['is_recommended',]
    list_filter = ['is_recommended', 'type_of_meal',]
    inlines = [IngredientQuantityInline,]


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    search_fields = ['name',]
    #readonly_fields нужно ли запретить менять is_paid_up, id_telegram и name?
    list_display = ['name', 'id_telegram', 'is_paid_up', 'renew_sub', 'payment_date',]
    list_filter = ['is_paid_up', 'renew_sub',]
    raw_id_fields = ('likes', 'dislikes', )


@admin.register(Revenue)
class RevenueAdmin(admin.ModelAdmin):
    list_display = ['month', 'revenue_sum',]
    ordering = ['-month',]
    readonly_fields = ['month', 'revenue_sum',]


admin.site.register(MealType)
