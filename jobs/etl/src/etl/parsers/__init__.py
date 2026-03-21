from pathlib import Path


def inspect_source_files(source_dir: str) -> list[str]:
    path = Path(source_dir)
    # TODO: Detect candidate CSVs, encodings, delimiters, and malformed lines.
    return sorted(item.name for item in path.glob("*.csv"))


__all__ = ["inspect_source_files"]
