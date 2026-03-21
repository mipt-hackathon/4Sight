import logging

from common.config import get_settings
from common.logging import configure_logging

logger = logging.getLogger(__name__)


def main() -> None:
    settings = get_settings()
    configure_logging(settings.app_log_level)
    logger.info("Running batch scoring scaffold.")
    logger.info("TODO: Generate serving-layer outputs using trained model artifacts.")


if __name__ == "__main__":
    main()
