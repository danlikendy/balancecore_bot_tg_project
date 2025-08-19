#!/usr/bin/env bash
set -euo pipefail
echo "[bootstrap] applying migrations..."
docker compose exec -T api alembic upgrade head
echo "[bootstrap] done."