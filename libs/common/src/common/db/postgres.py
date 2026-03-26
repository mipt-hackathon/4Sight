from common.config.settings import get_settings
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def create_db_engine() -> Engine:
    """Return a lazily used SQLAlchemy engine for future repository code."""

    settings = get_settings()
    return create_engine(settings.postgres_dsn, pool_pre_ping=True)
