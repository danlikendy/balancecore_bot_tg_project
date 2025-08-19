.PHONY: up down build logs api bot worker ps shell migrate revision test

up:
	docker compose up -d
down:
	docker compose down -v
build:
	docker compose up -d --build
logs:
	docker compose logs -f --tail=200
api:
	docker compose up -d --build api
bot:
	docker compose up -d --build bot
worker:
	docker compose up -d --build worker
ps:
	docker compose ps
shell:
	docker compose exec -it api bash
migrate:
	docker compose exec -T api alembic upgrade head
revision:
	docker compose exec -T api bash -lc 'alembic revision -m "$${MSG:-manual}" --autogenerate'
test:
	pytest -q
seed:
	docker compose exec -T api python infra/seed_tariffs.py