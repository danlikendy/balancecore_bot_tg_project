# BalanceCore Bot

Telegram-бот (aiogram 3) + FastAPI backend + Celery + PostgreSQL + Redis.

## Быстрый старт
1) Скопируйте `.env.example` в `.env` и заполните токены;
2) `docker-compose up --build` — поднимет db, redis, api, bot, worker;
3) Проверьте API: `GET http://localhost:8000/health` -> `{"status":"ok"}`.