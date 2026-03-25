import logging

from etl.contracts import build_load_plans
from etl.csv_parsers import detect_file_encoding, read_csv_header
from etl.models import CsvLoadPlan, CsvSourceFile

logger = logging.getLogger(__name__)


def run_transform(extracted_artifacts: list[CsvSourceFile]) -> list[CsvLoadPlan]:
    """
    Build direct-to-clean typed load plans from the raw CSV files.

    Current scope:
      - apply notebook-backed cleaning rules to data.csv
      - drop exact duplicate rows from data.csv before splitting
      - keep only the analyst-approved data.csv columns
      - split data.csv into users/orders/order_items
      - apply notebook-backed cleaning rules to events.csv
      - drop exact duplicate rows from events.csv before loading
      - fill missing events.user_id from ip_address when notebook logic allows it
      - fill missing events.city from ip_address when notebook logic allows it
      - load events.csv into clean.events without dropping event columns
    """

    plans: list[CsvLoadPlan] = []
    for source in extracted_artifacts:
        encoding = detect_file_encoding(source.path)
        header = read_csv_header(source.path, encoding)
        _validate_header(source.path, header)

        file_plans = build_load_plans(source, encoding, header)
        plans.extend(file_plans)

        logger.info(
            "Transform step prepared %s target table(s) from %s using encoding=%s",
            len(file_plans),
            source.filename,
            encoding,
        )

    return plans


def _validate_header(file_path, header: tuple[str, ...]) -> None:
    seen: set[str] = set()
    for column_name in header:
        if not column_name or not column_name.strip():
            raise ValueError(f"CSV header contains an empty column name in {file_path}")
        if column_name in seen:
            raise ValueError(
                f"CSV header contains duplicate column name {column_name!r} in {file_path}"
            )
        seen.add(column_name)
