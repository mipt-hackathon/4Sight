import logging

from common.config.settings import get_settings
from common.logging.setup import configure_logging

logger = logging.getLogger(__name__)


def main() -> None:
    settings = get_settings()
    configure_logging(settings.app_log_level)
    logger.info("Running feature builder scaffold for service=%s", settings.app_name)
    logger.info(
        "Assumption: mart-layer inputs are available and stable enough for feature contracts."
    )
    logger.info("Target: explicit feature tables shared by training and inference workflows.")
    logger.info("TODO: Execute SQL from /workspace/sql/feature to create model-ready datasets.")


if __name__ == "__main__":
    main()
