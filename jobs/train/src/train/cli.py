import logging

from common.config import get_settings
from common.logging import configure_logging

logger = logging.getLogger(__name__)


def main() -> None:
    settings = get_settings()
    configure_logging(settings.app_log_level)
    logger.info("Running training scaffold.")
    logger.info(
        "TODO: Train churn/recsys/forecast/segmentation models and write artifacts metadata."
    )


if __name__ == "__main__":
    main()
