import argparse
import logging

from common.config.settings import get_settings
from common.logging.setup import configure_logging

from etl.csv_parsers import inspect_source_files
from etl.input_validation import validate_inputs
from etl.postgres_loader import run_load
from etl.source_extract import run_extract
from etl.transform_plans import run_transform

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Retail analytics ETL scaffold.")
    parser.add_argument(
        "--source-dir",
        default="/workspace/data/raw",
        help="Directory with mounted CSV files such as data.csv and events.csv.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    settings = get_settings()
    configure_logging(settings.app_log_level)

    logger.info("Running ETL scaffold for service=%s", settings.app_name)
    logger.info("Starting ETL scaffold for source_dir=%s", args.source_dir)
    logger.info(
        "Current scope: apply notebook-backed cleaning for data.csv and events.csv, then load "
        "typed clean tables."
    )
    logger.info(
        "Target tables: clean.users, clean.orders, clean.order_items, and clean.events."
    )
    source_files = inspect_source_files(args.source_dir)
    logger.info("Discovered source CSV files: %s", source_files or "none yet")
    validate_inputs(args.source_dir)
    extracted_artifacts = run_extract(args.source_dir)
    transformed_artifacts = run_transform(extracted_artifacts)
    run_load(transformed_artifacts)
    logger.info(
        "ETL clean load completed. Additional domain-specific cleaning and downstream modeling "
        "remain future work, but the current notebook-backed clean contract is fully applied."
    )


if __name__ == "__main__":
    main()
