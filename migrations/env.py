from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# --- добавим корень проекта в sys.path, чтобы импортировать core ---
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # .../app
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# --- проектные импорты ---
from core.config import settings
from core.models.base import Base
from core.models.user import User  # noqa: F401
from core.models.transaction import Transaction  # noqa: F401
from core.models.withdraw_request import WithdrawRequest  # noqa: F401

from core.models.tariff import Tariff

config = context.config

# если URL не задан в alembic.ini, берём из настроек проекта
if not config.get_main_option("sqlalchemy.url"):
    config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Логирование Alembic
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    section = config.get_section(config.config_ini_section) or {}
    connectable = engine_from_config(
        section, prefix="sqlalchemy.", poolclass=pool.NullPool
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()