FoodPlan Bot

---
Телеграм-бот с рецептами по подписке.

Проект состоит из 3 компонент:
1. Админка Django (для управления всем) + БД;
2. Телеграм-бот;
3. Ежедневная проверка актуальности подписок.

Функционал пользователя:
- оплата(имитация)/отмена подписки;
- просмотр книги рецептов;
- просмотр ингредиентов к рецептам;
- настройка параметров выдачи рецептов;
- добавление рецептов в избранное и черный список.

Функционал менеджера:
- добавление ингредиентов и рецептов;
- просмотр пользователей, активность их подписки;
- просмотр выручки в по месяцам; 

## Как установить

Python3 должен быть уже установлен. 
Затем используйте `pip` (или `pip3`, есть конфликт с Python2) для установки зависимостей:
```shell
pip install -r requirements.txt
```
Создайте файл **.env** в корне репозитория, добавьте в него обязательные параметы:
- TG_BOT_TOKEN — API-токен Telegram-бота, можно получить при [регистрации](https://way23.ru/%D1%80%D0%B5%D0%B3%D0%B8%D1%81%D1%82%D1%80%D0%B0%D1%86%D0%B8%D1%8F-%D0%B1%D0%BE%D1%82%D0%B0-%D0%B2-telegram.html).
- SUBS_PRICE — стоимость подписки в рублях.

Создайте базу данных:
```shell
python manage.py makemigrations
python manage.py migrate
```
Создайте суперпользователя:
```sh
python manage.py createsuperuser
```

### Как запустить

1. Запустить сервер:
```shell
python manage.py runserver
```
2. Запустить проверку подписок:
```shell
python manage.py check_subscriptions
```
3. Запустить телеграм-бота:
```shell
python manage.py bot
```
4. Войти в кабинет администратора:
Перейдите по [ссылке](http://127.0.0.1:8000/admin/)
