from sqlalchemy.orm import Session
from sqlalchemy import func, case, select
from core.models.user import User
from core.models.transaction import Transaction

def get_or_create_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user:
        return user
    user = User(id=user_id)  # PK=telegram id
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_balance(db: Session, user_id: int) -> float:
    total = db.query(
        func.coalesce(
            func.sum(
                case(
                    (Transaction.kind == "credit", Transaction.amount),
                    else_=-Transaction.amount
                )
            ),
            0
        )
    ).filter(Transaction.user_id == user_id).scalar()
    return float(total or 0.0)