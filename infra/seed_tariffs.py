# infra/seed_tariffs.py
from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

# Добавляем корень проекта (/app в контейнере) в PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy.orm import Session  # noqa: E402
from core.db import SessionLocal  # noqa: E402
from core.models.tariff import Tariff  # noqa: E402

SEED: list[dict] = [
    {"code": "DAY", "name": "Дневной", "min_amount": 1000},
    {"code": "WEEK", "name": "Недельный", "min_amount": 5000},
    {"code": "MONTH", "name": "Месячный", "min_amount": 10000},
]


def upsert_tariffs(db: Session, items: Iterable[dict]) -> tuple[int, int]:
    """Идемпотентная загрузка тарифов. Возвращает (created, skipped)."""
    existed_codes = {t.code for t in db.query(Tariff).all()}
    created = 0
    skipped = 0
    for item in items:
        if item["code"] in existed_codes:
            skipped += 1
            continue
        db.add(Tariff(**item))
        created += 1
    db.commit()
    return created, skipped


def run() -> None:
    db: Session = SessionLocal()
    try:
        created, skipped = upsert_tariffs(db, SEED)
        print(
            f"[seed_tariffs] done: created={created}, skipped={skipped}, total={created+skipped}"
        )
    finally:
        db.close()


if __name__ == "__main__":
    run()