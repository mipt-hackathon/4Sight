import json
import pickle
import tempfile
from pathlib import Path

import pytest

from app.runtime.loaders import load_feature_columns, load_pickle_artifact


def test_load_pickle_artifact_success():
    obj = {"key": "value", "num": 42}
    with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
        pickle.dump(obj, f)
        path = Path(f.name)
    try:
        loaded = load_pickle_artifact(path)
        assert loaded == obj
    finally:
        path.unlink(missing_ok=True)


def test_load_pickle_artifact_missing_file():
    with pytest.raises(FileNotFoundError):
        load_pickle_artifact(Path("/nonexistent/model.pkl"))


def test_load_feature_columns_success():
    columns = ["col_a", "col_b", "col_c"]
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        json.dump(columns, f)
        path = Path(f.name)
    try:
        loaded = load_feature_columns(path)
        assert loaded == columns
    finally:
        path.unlink(missing_ok=True)


def test_load_feature_columns_missing_file():
    with pytest.raises(FileNotFoundError):
        load_feature_columns(Path("/nonexistent/feature_columns.json"))


def test_load_feature_columns_invalid_format():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        json.dump({"not": "a list"}, f)
        path = Path(f.name)
    try:
        with pytest.raises(ValueError, match="must be a list"):
            load_feature_columns(path)
    finally:
        path.unlink(missing_ok=True)


def test_load_feature_columns_non_string_elements():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        json.dump([1, 2, 3], f)
        path = Path(f.name)
    try:
        with pytest.raises(ValueError, match="must be a list"):
            load_feature_columns(path)
    finally:
        path.unlink(missing_ok=True)
