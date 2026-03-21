import argparse
import logging

from common.config import get_settings
from common.logging import configure_logging

from etl.extract import run_extract
from etl.load import run_load
from etl.parsers import inspect_source_files
from etl.transform import run_transform
from etl.validators import validate_inputs

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
        "Assumption: raw CSVs stay on disk and are never mirrored as raw PostgreSQL tables."
    )
    logger.info("Target: curated clean-layer tables in PostgreSQL after parsing and validation.")
    source_files = inspect_source_files(args.source_dir)
    logger.info("Discovered source CSV files: %s", source_files or "none yet")
    validate_inputs(args.source_dir)
    extracted_artifacts = run_extract(args.source_dir)
    transformed_artifacts = run_transform(extracted_artifacts)
    run_load(transformed_artifacts)
    logger.info("ETL scaffold completed. TODO: implement real ingestion pipeline.")


if __name__ == "__main__":
    main()
