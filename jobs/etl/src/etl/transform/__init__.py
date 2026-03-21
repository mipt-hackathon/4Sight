def run_transform(extracted_artifacts: list[str]) -> list[str]:
    """Return placeholder transformed artifact names."""

    # TODO: Add schema normalization, type coercion, deduplication, and enrichment steps.
    return [f"transformed:{artifact}" for artifact in extracted_artifacts]


__all__ = ["run_transform"]
