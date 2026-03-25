import logging

from common.config.settings import get_settings
from common.logging.setup import configure_logging

logger = logging.getLogger(__name__)


def main() -> None:
    settings = get_settings()
    configure_logging(settings.app_log_level)
    logger.info("Running marts builder scaffold for service=%s", settings.app_name)
    logger.info("Assumption: clean-layer tables already exist in PostgreSQL.")
    logger.info("Target: reusable mart datasets in the mart schema for backend and BI consumers.")
    logger.info("TODO: Execute SQL from /workspace/sql/mart in a controlled refresh order.")


if __name__ == "__main__":
    main()
