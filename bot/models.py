import sys

from django.db import models


class Ingredient(models.Model):
    name = models.CharField('Имя ингредиента', max_length=20)
    uom = models.CharField('Единицы измерения', max_length=20)
    сalories_in_uom = models.DecimalField(
        'Калорийность в ЕИ',
        max_digits=7, decimal_places=2,
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class IngredientQuantity(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ингредиент',
        on_delete=models.CASCADE
    )
    meal = models.ForeignKey(
        'Meal',
        verbose_name='Блюдо',
        related_name='ingredients_quant',
        on_delete=models.CASCADE
    )
    quantity = models.IntegerField('Количество')

    class Meta:
        verbose_name = 'Количество ингредиента'
        verbose_name_plural = 'Количество ингредиентов'

    def __str__(self):
        return f'{self.ingredient} - {convert_units()}'

    def convert_units(self):
        if self.ingredient.uom == 'г' and self.quantity >= 1000:
            return f'{self.quantity // 1000}кг {self.quantity % 1000}г'
        elif self.ingredient.uom == 'мл' and self.quantity >= 1000:
            return f'{self.quantity // 1000}л {self.quantity % 1000}мл'
        else:
            return f'{self.quantity}{self.ingredient.uom}'

    def get_caloric_value(self):
        return int(self.ingredient.сalories_in_uom * self.quantity)


class MealType(models.Model):
    type_name = models.CharField('Название', max_length=20)

    class Meta:
        verbose_name = 'Тип блюда'
        verbose_name_plural = 'Типы блюд'

    def __str__(self):
        return self.type_name


class Meal(models.Model):
    name = models.CharField('Название', max_length=40)
    description = models.TextField('Описание', null=True, blank=True)
    type_of_meal = models.ForeignKey(
        MealType,
        verbose_name='Тип блюда',
        related_name='meals',
        on_delete=models.CASCADE
    )
    # ingredients_quant
    image = models.ImageField('Изображение', null=True, blank=True)
    recipe = models.TextField('Рецепт')
    is_recommended = models.BooleanField('Рекомендуемое', default=False)
    # кол-во порций
    # время готовки

    class Meta:
        verbose_name = 'Блюдо'
        verbose_name_plural = 'Блюда'

    def __str__(self):
        return f'{self.type_of_meal} {self.name}'

    def get_caloric_value(self):
        return sum(ingredient.get_caloric_value()
                   for ingredient in self.ingredients_quant)


class Settings(models.Model):
    # виды - все
    # исключить ингридиенты
    # добавить ингридиенты
    # минимальная калорийность
    # максимальная калорийность

    class Meta:
        verbose_name = 'Настройки'
        verbose_name_plural = 'Настройки'


class Client(models.Model):
    id_telegram = models.CharField('Телеграм id', max_length=20)
    name = models.CharField('Имя', max_length=30)
    telegram_url = models.URLField(
        'Ссылка на телеграм',
        max_length=60,
        null=True,
        blank=True
    )
    is_paid_up = models.BooleanField(
        'Оплата подписки',
        default=False
    )
    likes = models.ManyToManyField(
        Meal,
        verbose_name='Избранное',
        related_name='liked_by',
        blank=True
    )
    dislikes = models.ManyToManyField(
        Meal,
        verbose_name='Чёрный список',
        related_name='disliked_by',
        blank=True
    )
    settings = models.OneToOneField(
        Settings,
        verbose_name='Настройки',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'

    def __str__(self):
        return self.name
