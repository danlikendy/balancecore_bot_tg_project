# BalanceCore Bot

Telegram бот для управления балансом с возможностью пополнения и вывода средств с процентами.

## Быстрый старт

### 1. Автоматическая настройка
```bash
# Клонируйте и настройте проект
git clone https://github.com/danlikendy/balancecore_bot_tg_project
cd balancecore_bot_tg_project

# Автоматическая настройка
make setup
```

### 2. Настройка конфигурации
Отредактируйте файл `.env`:
```bash
# Обязательные настройки
BOT_TOKEN=8370158560:AAGvl9Z1930Ad7f2f42WfHmaB5ofFPToaKg
ADMIN_USER_ID=ваш_telegram_id
DATABASE_URL=postgresql://balancecore:balancecore_password@localhost:5432/balancecore_bot
SECRET_KEY=ваш-секретный-ключ

# Опциональные настройки
MIN_WITHDRAWAL_AMOUNT=100
ADMIN_PERCENTAGE=5
WITHDRAWAL_DELAY_DAYS=7
```

### 3. Запуск через Docker (рекомендуется)
```bash
# Запуск всех сервисов
make docker-up

# Просмотр логов
make docker-logs
```

### 4. Запуск локально
```bash
# Запуск в режиме разработки
make dev

# Или по отдельности
make docker-up postgres redis  # Только БД
make migrate                   # Миграции
uvicorn api.main:app --reload  # API
python bot/main.py             # Бот
```

## Функциональность

- **Пополнение баланса** - пользователи могут пополнять баланс
- **Просмотр баланса** - текущий баланс и история операций
- **Вывод средств** - заявки на вывод с процентами администратора
- **Задержка вывода** - настраиваемая задержка после пополнения
- **Админ-панель** - веб-интерфейс для управления заявками
- **Безопасность** - проверка прав и валидация данных

## Управление

### Основные команды Makefile
```bash
make help          # Справка по командам
make setup         # Первоначальная настройка
make dev           # Запуск в режиме разработки
make docker-up     # Запуск через Docker
make docker-down   # Остановка сервисов
make migrate       # Запуск миграций БД
make test          # Запуск тестов
make status        # Статус сервисов
```

### Telegram команды
- `/start` - Главное меню
- `/balance` - Мой баланс
- `/deposit` - Пополнить баланс
- `/withdraw` - Вывести средства
- `/history` - История операций
- `/help` - Справка

## Веб-интерфейс

- **API документация**: http://localhost:8000/docs
- **Админ-панель**: http://localhost:8000/admin
- **Статус API**: http://localhost:8000/health

## Конфигурация

### Переменные окружения (.env)
```bash
# Bot Configuration
BOT_TOKEN=ваш_токен_бота
ADMIN_USER_ID=ваш_telegram_id

# Database Configuration  
DATABASE_URL=postgresql://user:password@localhost:5432/balancecore_bot
REDIS_URL=redis://localhost:6379/0

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
SECRET_KEY=ваш-секретный-ключ

# Withdrawal Settings
MIN_WITHDRAWAL_AMOUNT=100      # Минимальная сумма вывода
ADMIN_PERCENTAGE=5             # Процент администратора
WITHDRAWAL_DELAY_DAYS=7        # Задержка вывода в днях
```

## Архитектура

```
balancecore_bot_tg_project/
├── bot/                    # Telegram бот
│   ├── handlers/           # Обработчики команд
│   ├── keyboards/          # Клавиатуры
│   ├── middlewares/        # Middleware
│   └── main.py             # Точка входа бота
├── api/                    # FastAPI приложение
│   ├── main.py             # Основное API
│   ├── admin_ui.py         # Админ-панель
│   ├── templates/          # HTML шаблоны
│   └── static/             # CSS/JS файлы
├── core/                   # Основная логика
│   ├── models/             # Модели базы данных
│   ├── schemas/            # Pydantic схемы
│   ├── repositories/       # Репозитории
│   ├── config.py           # Конфигурация
│   └── db.py               # Подключение к БД
├── migrations/             # Alembic миграции
├── scripts/                # Скрипты развертывания
├── tests/                  # Тесты
└── docker-compose.yml      # Docker конфигурация
```

## Разработка

### Установка зависимостей
```bash
pip install -r requirements.txt
```

### Запуск тестов
```bash
make test
```

### Создание миграций
```bash
make migrate-create
```

### Логирование
Логи сохраняются в директории `logs/`

## Развертывание

### Production
1. Настройте переменные окружения
2. Запустите через Docker: `docker-compose up -d`
3. Настройте reverse proxy (nginx)
4. Настройте SSL сертификаты

### Мониторинг
- API health check: `/health`
- Логи Docker: `docker-compose logs -f`
- Статус сервисов: `make status`

## Поддержка

При возникновении проблем:
1. Проверьте логи: `make docker-logs`
2. Проверьте статус: `make status`
3. Перезапустите сервисы: `make docker-down && make docker-up`

## Лицензия

MIT License
