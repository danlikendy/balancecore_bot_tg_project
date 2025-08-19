from core.db import SessionLocal
from core.repositories.balance import get_or_create_user, get_balance

def test_autocreate_user_and_zero_balance():
    db = SessionLocal()
    try:
        u = get_or_create_user(db, 999999)
        assert u.id == 999999
        assert get_balance(db, 999999) == 0.0
    finally:
        db.close()