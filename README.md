Отличный план! Вот обновленный README.md:

**README.md**
```markdown
# Backend для автоматизации закупок

Backend-приложение для автоматизации закупок в розничной сети на Django REST Framework.

## Функциональность

### Базовая часть
- REST API для сервиса заказа товаров
- Настраиваемые поля (характеристики) товаров
- Импорт товаров
- Отправка накладной на email администратора
- Отправка подтверждения заказа на email клиента
- Авторизация, регистрация, восстановление пароля через API
- Корзина с товарами от разных поставщиков
- Управление заказами

### Продвинутая часть
- Экспорт товаров
- Админка заказами
- Асинхронные задачи с Celery
- Docker-контейнеризация

## Технологии

- Python 3.10
- Django 5.2
- Django REST Framework
- PostgreSQL
- Redis
- Celery
- Docker
- Docker Compose

## 1. Локальная установка (без Docker)

### Требования
- Python 3.10+
- PostgreSQL 14+
- Redis

### Установка

1. Клонируйте репозиторий:
```bash
git clone git@github.com:tamoykinden/Final_project_auto_purch.git
cd final_work_auto_purch
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте базу данных PostgreSQL:
```sql
CREATE DATABASE <имя БД>;
CREATE USER <имя пользователя> WITH PASSWORD <пароль>;
GRANT ALL PRIVILEGES ON DATABASE <имя БД> TO <имя пользователя;
```

5. Создайте файл `.env` в корне проекта по примеру `.env.example`

6. Выполните миграции:
```bash
python3 manage.py makemigrations
python3 manage.py migrate
```

7. Запустите сервер разработки:
```bash
python3 manage.py runserver
```

1. В отдельном терминале запустите Celery:
```bash
celery -A final_work_auto_purch worker --loglevel=info
```

Приложение будет доступно по адресу: http://localhost:8000

## 2. Запуск с Docker

### Требования
- Docker
- Docker Compose

### Быстрый запуск

1. Клонируйте репозиторий:
```bash
git clone git@github.com:tamoykinden/Final_project_auto_purch.git
cd final_work_auto_purch
```

2. Создайте файл `.env` в корне проекта по примеру `.env.example`

3. Запустите проект:
```bash
docker-compose up --build
```

4. Приложение будет доступно по адресу: http://localhost:8000

### Структура контейнеров

- **backend** - Django приложение (порт 8000)
- **postgres** - База данных PostgreSQL (порт 5432)
- **redis** - Redis для Celery (порт 6379)
- **celery** - Celery worker для асинхронных задач

### Полезные команды

Просмотр логов:
```bash
docker-compose logs backend
docker-compose logs celery
```

Выполнение команд в контейнере:
```bash
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
```

Остановка контейнеров:
```bash
docker-compose down
```

## 3. Тестирование API с REST Client

В проекте есть два файла для тестирования API с помощью REST Client (VS Code extension):

- `test_api.buyer.http` - тесты для покупателя
- `test_api_supplier.http` - тесты для поставщика

### Настройка токенов

1. Установите расширение **REST Client** для VS Code
2. Запустите запросы регистрации и авторизации из файлов `.http`
3. Скопируйте полученные токены из ответов
4. В файлах `.http` замените `{{buyer_token}}` и `{{supplier_token}}` на реальные токены:

### Доступные тесты

**Для покупателя (`test_api.buyer.http`):**
- Регистрация и авторизация покупателя
- Просмотр магазинов, категорий, товаров
- Управление профилем и контактами
- Работа с корзиной
- Оформление и подтверждение заказов
- Отслеживание статуса задач

**Для поставщика (`test_api_supplier.http`):**
- Регистрация и авторизация поставщика
- Управление состоянием магазина
- Асинхронный импорт товаров
- Просмотр и обновление заказов
- Тестирование ошибок доступа

### Особенности тестирования

- Для админских функций (импорт через админку) требуется пользователь с `is_staff=True`
- Асинхронные задачи (импорт, отправка email) возвращают `task_id` для отслеживания статуса
- Все защищенные endpoints требуют заголовок `Authorization: Token ваш_токен`
- Тестируются различные сценарии ошибок (неверные токены, доступ к чужим данным)

## Администрирование

Админка Django доступна по адресу: http://localhost:8000/admin/

Создайте суперпользователя:
```bash
docker-compose exec backend python3 manage.py createsuperuser
```

## Разработка

### Добавление зависимостей
Добавляйте новые Python пакеты в `requirements.txt` и пересобирайте контейнеры:

```bash
docker-compose up --build
```

### Миграции базы данных
При изменении моделей создавайте миграции:

```bash
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate
```
```