import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Keep backend ahead of ml_api because both services intentionally use an `app` package.
for relative_path in reversed(
    [
        "apps/backend",
        "apps/ml_api",
        "libs/common/src",
        "jobs/etl/src",
        "jobs/marts_builder/src",
        "jobs/feature_builder/src",
        "jobs/train/src",
        "jobs/batch_scoring/src",
    ]
):
    sys.path.insert(0, str(ROOT / relative_path))
