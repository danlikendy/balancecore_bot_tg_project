#!/bin/bash

# BalanceCore Bot Bootstrap Script
# Скрипт для первоначальной настройки проекта

set -e

echo "🚀 Запуск настройки BalanceCore Bot..."

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установите Python 3.9+ и повторите попытку."
    exit 1
fi

# Проверяем версию Python
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Требуется Python $REQUIRED_VERSION или выше. Текущая версия: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION найден"

# Создаем виртуальное окружение
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активируем виртуальное окружение
echo "🔧 Активация виртуального окружения..."
source venv/bin/activate

# Обновляем pip
echo "⬆️ Обновление pip..."
pip install --upgrade pip

# Устанавливаем зависимости
echo "📚 Установка зависимостей..."
pip install -r requirements.txt

# Копируем файл конфигурации
if [ ! -f ".env" ]; then
    echo "⚙️ Создание файла конфигурации..."
    cp env.example .env
    echo "📝 Отредактируйте файл .env с вашими настройками"
fi

# Проверяем наличие PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "⚠️ PostgreSQL не найден. Установите PostgreSQL для работы с базой данных."
    echo "   Или используйте Docker: docker-compose up -d postgres"
fi

# Проверяем наличие Redis
if ! command -v redis-cli &> /dev/null; then
    echo "⚠️ Redis не найден. Установите Redis для работы с FSM."
    echo "   Или используйте Docker: docker-compose up -d redis"
fi

echo ""
echo "✅ Настройка завершена!"
echo ""
echo "Следующие шаги:"
echo "1. Отредактируйте файл .env с вашими настройками"
echo "2. Настройте базу данных:"
echo "   - Создайте базу: createdb balancecore_bot"
echo "   - Запустите миграции: make migrate"
echo "3. Запустите проект:"
echo "   - Через Docker: make docker-up"
echo "   - Локально: make dev"
echo ""
echo "Админ-панель будет доступна по адресу: http://localhost:8000/admin"
