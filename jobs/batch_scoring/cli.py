import logging

from common.config.settings import get_settings
from common.logging.setup import configure_logging

logger = logging.getLogger(__name__)


def main() -> None:
    settings = get_settings()
    configure_logging(settings.app_log_level)
    logger.info("Running batch scoring scaffold for service=%s", settings.app_name)
    logger.info(
        "Assumption: trained artifacts and feature tables are available before scoring starts."
    )
    logger.info("Target: serving-layer tables consumed by backend APIs and Superset.")
    logger.info("TODO: Generate serving-layer outputs using trained model artifacts.")


if __name__ == "__main__":
    main()
