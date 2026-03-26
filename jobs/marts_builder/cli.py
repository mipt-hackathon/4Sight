import logging

from common.config.settings import get_settings
from common.logging.setup import configure_logging

from marts_builder.sql_runner import run_mart_sql

logger = logging.getLogger(__name__)


def main() -> None:
    settings = get_settings()
    configure_logging(settings.app_log_level)
    logger.info("Running marts builder for service=%s", settings.app_name)
    logger.info("Assumption: clean-layer tables already exist in PostgreSQL.")
    logger.info("Target: reusable mart datasets in the mart schema for backend and BI consumers.")
    executed_files = run_mart_sql()
    logger.info("Mart refresh completed. Executed SQL files: %s", ", ".join(executed_files))


if __name__ == "__main__":
    main()
