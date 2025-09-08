# BalanceCore Bot Makefile

.PHONY: help install dev test clean docker-build docker-up docker-down migrate

help: ## Показать справку
	@echo "BalanceCore Bot - Управление балансом в Telegram"
	@echo ""
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Установить зависимости
	pip install -r requirements.txt

dev: ## Запустить в режиме разработки
	@echo "Запуск в режиме разработки..."
	@echo "1. Запуск PostgreSQL и Redis через Docker..."
	docker-compose up -d postgres redis
	@echo "2. Ожидание готовности сервисов..."
	@sleep 10
	@echo "3. Запуск миграций..."
	alembic upgrade head
	@echo "4. Запуск API сервера..."
	uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload &
	@echo "5. Запуск бота..."
	python bot/main.py

test: ## Запустить тесты
	pytest tests/ -v

clean: ## Очистить временные файлы
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache/
	rm -rf logs/*.log

docker-build: ## Собрать Docker образ
	docker-compose build

docker-up: ## Запустить все сервисы через Docker
	docker-compose up -d

docker-down: ## Остановить все сервисы
	docker-compose down

docker-logs: ## Показать логи Docker сервисов
	docker-compose logs -f

migrate: ## Запустить миграции базы данных
	alembic upgrade head

migrate-create: ## Создать новую миграцию
	@read -p "Введите описание миграции: " desc; \
	alembic revision --autogenerate -m "$$desc"

init-db: ## Инициализировать базу данных
	@echo "Создание базы данных..."
	createdb balancecore_bot || true
	@echo "Запуск миграций..."
	alembic upgrade head
	@echo "База данных инициализирована!"

setup: ## Первоначальная настройка проекта
	@echo "Настройка BalanceCore Bot..."
	@echo "1. Копирование файла конфигурации..."
	cp env.example .env
	@echo "2. Установка зависимостей..."
	make install
	@echo "3. Инициализация базы данных..."
	make init-db
	@echo ""
	@echo "✅ Настройка завершена!"
	@echo ""
	@echo "Следующие шаги:"
	@echo "1. Отредактируйте файл .env с вашими настройками"
	@echo "2. Запустите проект: make dev"
	@echo "3. Откройте админ-панель: http://localhost:8000/admin"

status: ## Показать статус сервисов
	@echo "Статус сервисов:"
	@echo "PostgreSQL:"
	@pg_isready -h localhost -p 5432 -U balancecore || echo "  ❌ Недоступен"
	@echo "Redis:"
	@redis-cli ping || echo "  ❌ Недоступен"
	@echo "API:"
	@curl -s http://localhost:8000/health > /dev/null && echo "  ✅ Работает" || echo "  ❌ Недоступен"
