import logging

from common.config import get_settings
from common.logging import configure_logging

logger = logging.getLogger(__name__)


def main() -> None:
    settings = get_settings()
    configure_logging(settings.app_log_level)
    logger.info("Running marts builder scaffold.")
    logger.info("TODO: Execute SQL from /workspace/sql/mart in a controlled refresh order.")


if __name__ == "__main__":
    main()
