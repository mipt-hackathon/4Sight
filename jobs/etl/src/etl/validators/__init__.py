from pathlib import Path


def validate_inputs(source_dir: str) -> None:
    path = Path(source_dir)
    # TODO: Add required-file checks, schema validation, encoding checks, and null-rate guards.
    if not path.exists():
        raise FileNotFoundError(f"Input directory does not exist: {path}")


__all__ = ["validate_inputs"]
