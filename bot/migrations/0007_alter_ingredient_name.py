# Generated by Django 4.2.5 on 2023-09-30 16:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0006_remove_revenue_max_сalories_revenue_revenue_sum'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingredient',
            name='name',
            field=models.CharField(max_length=20, unique=True, verbose_name='Имя ингредиента'),
        ),
    ]
