# BalanceCore Bot

Telegram бот для управления депозитами с ежедневным начислением процентов. Пользователи могут создавать депозиты, получать проценты ежедневно и выводить средства в любое время.

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
BOT_TOKEN=ваш_токен_бота
ADMIN_USER_ID=ваш_telegram_id
DATABASE_URL=postgresql://balancecore:balancecore_password@localhost:5432/balancecore_bot
SECRET_KEY=ваш-секретный-ключ

# YooKassa настройки (для приема платежей)
YOOKASSA_SHOP_ID=ваш_shop_id
YOOKASSA_SECRET_KEY=ваш_secret_key
YOOKASSA_TEST_MODE=true

# PayMaster настройки (альтернативная платежная система)
PAYMASTER_MERCHANT_ID=ваш_merchant_id
PAYMASTER_SECRET_KEY=ваш_secret_key
PAYMASTER_API_URL=https://paymaster.ru
PAYMASTER_TEST_MODE=true

# Ozon Pay настройки (платежная система Ozon)
OZON_CLIENT_ID=ваш_client_id
OZON_CLIENT_SECRET=ваш_client_secret
OZON_API_URL=https://api.ozon.ru
OZON_TEST_MODE=true

# Настройки системы
MIN_WITHDRAWAL_AMOUNT=100
ADMIN_PERCENTAGE=5
WITHDRAWAL_DELAY_DAYS=0  # Без задержки для депозитов
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
python bot/main.py            # Бот
```

## Функциональность

### Для пользователей:
- **Создание депозитов** - пополнение с начислением процентов
- **Ежедневные проценты** - автоматическое начисление 1% в день
- **Просмотр баланса** - текущий баланс, депозиты и заработанные проценты
- **Вывод средств** - вывод в любое время с комиссией администратора
- **История операций** - полная история всех транзакций

### Для администратора:
- **Веб-панель** - управление заявками на вывод
- **Статистика** - общая статистика по депозитам и выводам
- **Автоматизация** - ежедневное начисление процентов по расписанию

### Безопасность:
- **Проверка прав** - разграничение доступа пользователей и админов
- **Валидация данных** - проверка всех входящих данных
- **Логирование** - полное логирование всех операций

## Стратегия процентов

### Как работают проценты:

1. **Создание депозита**: Пользователь пополняет баланс через ЮKassa
2. **Ежедневное начисление**: Каждый день автоматически начисляется 1% от текущей суммы депозита
3. **Сложные проценты**: Проценты начисляются на проценты (сложные проценты)
4. **Вывод в любое время**: Пользователь может вывести средства в любое время
5. **Автоматическое закрытие**: При выводе депозит автоматически закрывается с начислением всех процентов

### Пример расчета:
- Депозит: 10,000 руб.
- День 1: 10,000 + 1% = 10,100 руб.
- День 2: 10,100 + 1% = 10,201 руб.
- День 3: 10,201 + 1% = 10,303.01 руб.
- И так далее...

### Настройка ЮKassa:

1. **Регистрация**: Зарегистрируйтесь на https://yookassa.ru/
2. **Получение данных**: Получите Shop ID и Secret Key
3. **Настройка в .env**:
   ```bash
   YOOKASSA_SHOP_ID=ваш_shop_id
   YOOKASSA_SECRET_KEY=ваш_secret_key
   YOOKASSA_TEST_MODE=true  # false для продакшена
   ```

### Автоматическое начисление процентов:

Для ежедневного начисления процентов настройте cron:
```bash
# Каждый день в 00:01
1 0 * * * cd /path/to/project && python scripts/daily_interest.py
```

Или используйте Docker:
```bash
# Запуск начисления процентов
docker-compose exec bot python scripts/daily_interest.py
```

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
- `/balance` - Мой баланс и депозиты
- `/deposit` - Создать депозит с процентами
- `/withdraw` - Вывести средства
- `/history` - История операций
- `/help` - Справка

### Кнопки в боте:
- **Мой баланс** - показывает баланс, депозиты и заработанные проценты
- **Пополнить** - создание нового депозита с начислением процентов
- **Вывести средства** - вывод средств с депозитов и баланса
- **История операций** - все транзакции и начисления процентов

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

# YooKassa Configuration (для приема платежей)
YOOKASSA_SHOP_ID=ваш_shop_id
YOOKASSA_SECRET_KEY=ваш_secret_key
YOOKASSA_TEST_MODE=true

# System Settings
MIN_WITHDRAWAL_AMOUNT=100      # Минимальная сумма вывода
ADMIN_PERCENTAGE=5             # Процент администратора при выводе
WITHDRAWAL_DELAY_DAYS=0        # Задержка вывода (0 = без задержки)
```

## Архитектура

```
balancecore_bot_tg_project/
├── bot/                    # Telegram бот
│   ├── handlers/          # Обработчики команд
│   ├── keyboards/         # Клавиатуры
│   ├── middlewares/       # Middleware
│   └── main.py           # Точка входа бота
├── api/                   # FastAPI приложение
│   ├── main.py           # Основное API
│   ├── admin_ui.py       # Админ-панель
│   ├── templates/        # HTML шаблоны
│   └── static/           # CSS/JS файлы
├── core/                  # Основная логика
│   ├── models/           # Модели базы данных
│   │   ├── user.py       # Модель пользователя
│   │   ├── deposit.py    # Модель депозита с процентами
│   │   ├── transaction.py # Модель транзакций
│   │   └── payment.py    # Модель платежей ЮKassa
│   ├── services/         # Бизнес-логика
│   │   ├── interest.py   # Сервис начисления процентов
│   │   └── payment.py    # Сервис работы с ЮKassa
│   ├── repositories/     # Репозитории для работы с БД
│   ├── config.py         # Конфигурация
│   └── db.py            # Подключение к БД
├── migrations/            # Alembic миграции
├── scripts/              # Скрипты развертывания
│   └── daily_interest.py # Ежедневное начисление процентов
├── tests/                # Тесты
└── docker-compose.yml    # Docker конфигурация
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
- Логи начисления процентов: `logs/daily_interest.log`

### Ежедневные задачи
```bash
# Ручной запуск начисления процентов
python scripts/daily_interest.py

# Через Docker
docker-compose exec bot python scripts/daily_interest.py

# Настройка cron для автоматического начисления
# Добавьте в crontab:
# 1 0 * * * cd /path/to/project && python scripts/daily_interest.py
```

## Поддержка

При возникновении проблем:
1. Проверьте логи: `make docker-logs`
2. Проверьте статус: `make status`
3. Перезапустите сервисы: `make docker-down && make docker-up`

## Лицензия

MIT License


