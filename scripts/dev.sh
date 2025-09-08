#!/bin/bash

# BalanceCore Bot Development Script
# Скрипт для запуска в режиме разработки

set -e

echo "🔧 Запуск BalanceCore Bot в режиме разработки..."

# Активируем виртуальное окружение
if [ -d "venv" ]; then
    echo "📦 Активация виртуального окружения..."
    source venv/bin/activate
fi

# Проверяем наличие .env файла
if [ ! -f ".env" ]; then
    echo "❌ Файл .env не найден. Запустите сначала: make setup"
    exit 1
fi

# Загружаем переменные окружения
export $(cat .env | grep -v '^#' | xargs)

# Проверяем подключение к базе данных
echo "🔍 Проверка подключения к базе данных..."
if ! python -c "
import psycopg2
try:
    conn = psycopg2.connect('$DATABASE_URL')
    conn.close()
    print('✅ База данных доступна')
except Exception as e:
    print(f'❌ Ошибка подключения к базе данных: {e}')
    exit(1)
"; then
    echo "❌ Не удается подключиться к базе данных"
    echo "Убедитесь, что PostgreSQL запущен и настройки в .env корректны"
    exit 1
fi

# Запускаем миграции
echo "🔄 Запуск миграций базы данных..."
alembic upgrade head

# Запускаем API сервер в фоне
echo "🌐 Запуск API сервера..."
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

# Ждем запуска API
sleep 3

# Проверяем, что API запустился
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ API сервер не запустился"
    kill $API_PID 2>/dev/null || true
    exit 1
fi

echo "✅ API сервер запущен на http://localhost:8000"

# Запускаем бота
echo "🤖 Запуск Telegram бота..."
python bot/main.py &
BOT_PID=$!

# Функция для корректного завершения
cleanup() {
    echo ""
    echo "🛑 Завершение работы..."
    kill $API_PID 2>/dev/null || true
    kill $BOT_PID 2>/dev/null || true
    echo "✅ Все процессы остановлены"
    exit 0
}

# Обработка сигналов
trap cleanup SIGINT SIGTERM

echo ""
echo "✅ BalanceCore Bot запущен!"
echo ""
echo "🌐 API: http://localhost:8000"
echo "👨‍💼 Админ-панель: http://localhost:8000/admin"
echo "📚 API документация: http://localhost:8000/docs"
echo ""
echo "Нажмите Ctrl+C для остановки"

# Ждем завершения
wait
