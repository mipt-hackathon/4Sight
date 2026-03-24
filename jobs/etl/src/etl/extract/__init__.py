import logging

from etl.models import CsvSourceFile
from etl.parsers import discover_source_files

logger = logging.getLogger(__name__)


def run_extract(source_dir: str) -> list[CsvSourceFile]:
    """Discover CSV files that should be loaded into PostgreSQL."""

    source_files = discover_source_files(source_dir)
    for source_file in source_files:
        logger.info("Extract step registered source file %s", source_file.path)
    return source_files


__all__ = ["run_extract"]
