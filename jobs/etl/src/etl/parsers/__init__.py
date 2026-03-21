import csv
import re
from pathlib import Path

from etl.models import CsvSourceFile

PREFERRED_TABLE_NAMES = {
    "data.csv": "transactions_wide_import",
    "events.csv": "events_import",
}
SUPPORTED_ENCODINGS = ("utf-8-sig", "utf-8", "cp1251", "latin-1")


def inspect_source_files(source_dir: str) -> list[str]:
    return [source.filename for source in discover_source_files(source_dir)]


def discover_source_files(source_dir: str) -> list[CsvSourceFile]:
    path = Path(source_dir)
    csv_files = sorted(item for item in path.rglob("*.csv") if item.is_file())
    return [
        CsvSourceFile(
            filename=item.name,
            path=item,
            table_name=_build_table_name(item.name),
        )
        for item in csv_files
    ]


def detect_file_encoding(file_path: Path) -> str:
    for encoding in SUPPORTED_ENCODINGS:
        try:
            with file_path.open("r", encoding=encoding, newline="") as handle:
                reader = csv.reader(handle)
                next(reader, None)
            return encoding
        except UnicodeDecodeError:
            continue

    raise UnicodeDecodeError(
        "csv",
        b"",
        0,
        1,
        f"Could not decode {file_path.name} with supported encodings {SUPPORTED_ENCODINGS}",
    )


def read_csv_header(file_path: Path, encoding: str) -> tuple[str, ...]:
    with file_path.open("r", encoding=encoding, newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)

    if not header:
        raise ValueError(f"CSV file is empty or missing a header row: {file_path}")

    return tuple(header)


def _build_table_name(filename: str) -> str:
    if filename in PREFERRED_TABLE_NAMES:
        return PREFERRED_TABLE_NAMES[filename]

    stem = Path(filename).stem.lower()
    slug = re.sub(r"[^a-z0-9]+", "_", stem).strip("_")
    return f"{slug or 'dataset'}_import"


__all__ = [
    "detect_file_encoding",
    "discover_source_files",
    "inspect_source_files",
    "read_csv_header",
]
