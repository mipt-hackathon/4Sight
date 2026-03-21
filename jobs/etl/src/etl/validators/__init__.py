from pathlib import Path

from etl.parsers import discover_source_files


def validate_inputs(source_dir: str) -> None:
    path = Path(source_dir)
    if not path.exists():
        raise FileNotFoundError(f"Input directory does not exist: {path}")

    csv_files = discover_source_files(source_dir)
    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files were found under {path}. Expected files such as data.csv and events.csv."
        )


__all__ = ["validate_inputs"]
