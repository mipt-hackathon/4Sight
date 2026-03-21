from pathlib import Path


def run_extract(source_dir: str) -> list[str]:
    """Return placeholder extracted artifact names."""

    path = Path(source_dir)
    # TODO: Discover and parse data.csv/events.csv with encoding handling and validation hooks.
    return [f"extracted_from:{path.name or 'raw'}"]


__all__ = ["run_extract"]
