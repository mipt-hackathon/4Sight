import logging

from etl.models import CsvImportPlan, CsvSourceFile
from etl.parsers import detect_file_encoding, read_csv_header

logger = logging.getLogger(__name__)


def run_transform(extracted_artifacts: list[CsvSourceFile]) -> list[CsvImportPlan]:
    """
    Build explicit import plans without modifying source columns or values.

    TODO:
      - add actual cleaning and type coercion
      - resolve malformed headers and duplicate columns if they appear
    """

    plans: list[CsvImportPlan] = []
    for source in extracted_artifacts:
        encoding = detect_file_encoding(source.path)
        header = read_csv_header(source.path, encoding)
        _validate_header(source.path, header)

        plans.append(
            CsvImportPlan(
                source=source,
                encoding=encoding,
                header=header,
            )
        )
        logger.info(
            "Transform step prepared %s columns from %s using encoding=%s",
            len(header),
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


__all__ = ["run_transform"]
