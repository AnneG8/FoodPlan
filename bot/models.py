from django.db import models
from datetime import timedelta, date


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
        return f'{self.ingredient} - {self.convert_units()}'

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
    name = models.CharField('Название', max_length=80)
    image = models.ImageField('Изображение', null=True, blank=True)
    description = models.TextField('Описание', null=True, blank=True)
    type_of_meal = models.ForeignKey(
        MealType,
        verbose_name='Тип блюда',
        related_name='meals',
        on_delete=models.CASCADE
    )
    # ingredients_quant
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
                   for ingredient in self.ingredients_quant.all())
    get_caloric_value.short_description = 'Калории'


class Client(models.Model):
    id_telegram = models.CharField('Телеграм id', max_length=20)
    name = models.CharField('Имя', max_length=30)
    telegram_url = models.URLField(
        'Ссылка на телеграм',
        max_length=60,
        null=True,
        blank=True
    )
    renew_sub = models.BooleanField(
        'Продление подписки',
        default=False
    )
    is_paid_up = models.BooleanField(
        'Оплата подписки',
        default=False
    )
    payment_date = models.DateField(
        'День оплаты',
        null=True,
        blank=True
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

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'

    def __str__(self):
        return self.name


class Settings(models.Model):
    client = models.OneToOneField(
        Client,
        verbose_name='Клиент',
        related_name='settings',
        on_delete=models.CASCADE
    )
    type_of_meal = models.ManyToManyField(
        MealType,
        verbose_name='Запрещенные типы блюд',
        blank=True
    )
    excluded_ingrs = models.ManyToManyField(
        Ingredient,
        verbose_name='Исключить ингредиенты',
        related_name='excluded_ingrs',
        blank=True
    )
    chosen_ingrs = models.ManyToManyField(
        Ingredient,
        verbose_name='Обязательно наличие ингредиентов',
        related_name='chosen_ingrs',
        blank=True
    )
    min_сalories = models.IntegerField(
        'Минимум калорий', 
        null=True, 
        blank=True
    )
    max_сalories = models.IntegerField(
        'Максимум калорий',
        null=True, 
        blank=True
    )
    # db_index

    class Meta:
        verbose_name = 'Настройки'
        verbose_name_plural = 'Настройки'


class Revenue(models.Model):
    month = models.DateField(
        'Месяц',
        default=date.today().replace(day=1)
    )
    max_сalories = models.IntegerField('Максимум калорий', default=0)
    class Meta:
        verbose_name = 'Выручка за месяц'
        verbose_name_plural = 'Выручка'

