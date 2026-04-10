import json
import logging
import pickle
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def load_pickle_artifact(path: Path) -> Any:
    with open(path, "rb") as f:
        return pickle.load(f)


def load_feature_columns(path: Path) -> list[str]:
    with open(path, "r") as f:
        data = json.load(f)
    if not isinstance(data, list) or not all(isinstance(c, str) for c in data):
        raise ValueError(f"feature_columns.json must be a list[str]: {path}")
    return data
