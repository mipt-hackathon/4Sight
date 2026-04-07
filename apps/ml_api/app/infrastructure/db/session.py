import logging

from common.db.postgres import create_db_engine
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


def make_engine() -> Engine:
    """Create the shared SQLAlchemy engine using the common factory."""
    engine = create_db_engine()
    logger.info("Database engine created")
    return engine
