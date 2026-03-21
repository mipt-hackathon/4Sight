import logging

from common.config import get_settings
from common.logging import configure_logging

logger = logging.getLogger(__name__)


def main() -> None:
    settings = get_settings()
    configure_logging(settings.app_log_level)
    logger.info("Running training scaffold for service=%s", settings.app_name)
    logger.info(
        "Assumption: model features come from SQL-owned feature tables, not notebook state."
    )
    logger.info("Target: versioned artifacts written to /workspace/artifacts/models.")
    logger.info(
        "TODO: Train churn/recsys/forecast/segmentation models and write artifacts metadata."
    )


if __name__ == "__main__":
    main()
