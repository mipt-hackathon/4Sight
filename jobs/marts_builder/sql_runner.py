import logging
from pathlib import Path

from common.db.postgres import create_db_engine
from sqlalchemy import text

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
MART_SQL_DIR = REPO_ROOT / "sql" / "mart"
MART_REFRESH_ORDER = (
    "mart_sales_daily.sql",
    "mart_behavior_metrics.sql",
    "mart_customer_360.sql",
    "mart_abc_xyz.sql",
    "mart_abc_xyz_cv_distribution.sql",
    "mart_abc_xyz_time_series_samples.sql",
    "mart_rfm.sql",
    "mart_rfm_churn_by_segment.sql",
    "mart_logistics_metrics.sql",
    "mart_cohorts.sql",
    "mart_product_xyz.sql",
    "mart_region_abc.sql",
    "mart_customer_abc_monthly.sql",
    "mart_customer_category_migration.sql",
    "mart_category_abc.sql",
    "mart_brand_abc.sql",
)


def run_mart_sql() -> list[str]:
    available_sql_files = {path.name: path for path in MART_SQL_DIR.glob("*.sql")}
    missing_sql_files = [name for name in MART_REFRESH_ORDER if name not in available_sql_files]
    if missing_sql_files:
        raise FileNotFoundError(
            f"Missing mart SQL files required by marts_builder: {', '.join(missing_sql_files)}"
        )

    skipped_sql_files = sorted(set(available_sql_files) - set(MART_REFRESH_ORDER))
    if skipped_sql_files:
        logger.info(
            "Skipping mart SQL placeholders that are not implemented yet: %s",
            ", ".join(skipped_sql_files),
        )

    engine = create_db_engine()
    executed_files: list[str] = []
    with engine.begin() as connection:
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS mart"))
        for file_name in MART_REFRESH_ORDER:
            sql_path = available_sql_files[file_name]
            sql_text = sql_path.read_text(encoding="utf-8").strip()
            if not sql_text:
                raise ValueError(f"Mart SQL file is empty: {sql_path}")

            logger.info("Executing mart SQL file %s", sql_path.name)
            connection.exec_driver_sql(sql_text)
            executed_files.append(sql_path.name)

    return executed_files
