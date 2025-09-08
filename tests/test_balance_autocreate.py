import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.db import Base
from core.repositories.balance import BalanceRepository
from core.models.transaction import TransactionType, TransactionStatus


@pytest.fixture
def db_session():
    """Создание тестовой сессии базы данных"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def balance_repo(db_session):
    """Создание репозитория для тестов"""
    return BalanceRepository(db_session)


def test_create_user(balance_repo):
    """Тест создания пользователя"""
    user = balance_repo.create_user(
        telegram_id=12345,
        username="testuser",
        first_name="Test",
        last_name="User"
    )
    
    assert user.telegram_id == 12345
    assert user.username == "testuser"
    assert user.first_name == "Test"
    assert user.last_name == "User"
    assert user.balance == 0.0
    assert user.is_active is True


def test_get_user_by_telegram_id(balance_repo):
    """Тест получения пользователя по Telegram ID"""
    # Создаем пользователя
    user = balance_repo.create_user(telegram_id=12345, username="testuser")
    
    # Получаем пользователя
    found_user = balance_repo.get_user_by_telegram_id(12345)
    
    assert found_user is not None
    assert found_user.telegram_id == 12345
    assert found_user.username == "testuser"


def test_update_user_balance(balance_repo):
    """Тест обновления баланса пользователя"""
    # Создаем пользователя
    user = balance_repo.create_user(telegram_id=12345)
    
    # Обновляем баланс
    success = balance_repo.update_user_balance(12345, 100.0)
    
    assert success is True
    
    # Проверяем, что баланс обновился
    updated_user = balance_repo.get_user_by_telegram_id(12345)
    assert updated_user.balance == 100.0


def test_create_transaction(balance_repo):
    """Тест создания транзакции"""
    # Создаем пользователя
    user = balance_repo.create_user(telegram_id=12345)
    
    # Создаем транзакцию
    transaction = balance_repo.create_transaction(
        user_id=12345,
        amount=100.0,
        transaction_type=TransactionType.DEPOSIT,
        description="Test deposit"
    )
    
    assert transaction.user_id == 12345
    assert transaction.amount == 100.0
    assert transaction.transaction_type == TransactionType.DEPOSIT
    assert transaction.description == "Test deposit"
    assert transaction.status == TransactionStatus.PENDING


def test_create_withdraw_request(balance_repo):
    """Тест создания заявки на вывод"""
    # Создаем пользователя
    user = balance_repo.create_user(telegram_id=12345)
    
    # Создаем заявку на вывод
    withdraw_request = balance_repo.create_withdraw_request(
        user_id=12345,
        amount=100.0,
        payment_method="Банковская карта",
        payment_details="1234 5678 9012 3456"
    )
    
    assert withdraw_request.user_id == 12345
    assert withdraw_request.amount == 100.0
    assert withdraw_request.payment_method == "Банковская карта"
    assert withdraw_request.payment_details == "1234 5678 9012 3456"
    assert withdraw_request.admin_fee > 0
    assert withdraw_request.final_amount < withdraw_request.amount


def test_can_user_withdraw(balance_repo):
    """Тест проверки возможности вывода средств"""
    # Создаем пользователя
    user = balance_repo.create_user(telegram_id=12345)
    
    # Пользователь без депозитов может выводить средства
    can_withdraw = balance_repo.can_user_withdraw(12345)
    assert can_withdraw is True
