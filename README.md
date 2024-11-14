# Foodgram
![](https://img.shields.io/badge/Python-3.9-lightblue)
![](https://img.shields.io/badge/Django-3.2-darkgreen)
![](https://img.shields.io/badge/Django_REST_framework-3.12-blue)
![](https://img.shields.io/badge/Djoser-2.2.1-orange)

*Веб-приложение, в котором Вы можете открыть для себя множество вкуснейших рецептов,
а также поделиться своими!*

Приложение доступно по адресу https://foodgram-app.sytes.net/.

### Возможности:
- Публикация собственных рецептов
- Подписка на других пользователей
- Список покупок, который можно скачать
- Избранные рецепты в один клик.

<details>
  <summary><b>Как запустить проект с помощью контейнеров</b></summary>

1. Форкнуть репозиторий и клонировать его на локальную машину
```
git clone git@github.com:ClosedEyeVisuals/foodgram.git
```
2. Создать в корневой директории файл .env и заполнить его по примеру

3. Запустить контейнеры:
```
sudo docker compose up --build
```
- Выполнить миграции
```
sudo docker compose exec backend python manage.py migrate
```
- Собрать статику и скопировать
```
sudo docker compose exec backend python manage.py collectstatic
sudo docker compose exec backend cp -r /app/collected_static/. /backend_static/static/
```
- Создать суперпользователя
```
sudo docker compose exec -it backend python manage.py createsuperuser
```
- При желании можно заполнить базу данных ингредиентами:
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py import_ingredients
```
4. После разработки остановить проект
```
sudo docker compose down
```
</details>

## API проекта
Документация с полным перечнем эндпоинтов доступна после запуска проекта по адресу:
>http://{*ваш_домен*}/**api/docs/**

#### [Автор](https://github.com/ClosedEyeVisuals)
