import os

ROW_LIMIT = 5000
SECRET_KEY = os.getenv("SUPERSET_SECRET_KEY", "replace-me")
SQLALCHEMY_DATABASE_URI = os.getenv(
    "SUPERSET_DATABASE_URI",
    "postgresql+psycopg2://retail:retail@postgres:5432/superset_metadata",
)
ANALYTICS_DATABASE_URI = os.getenv(
    "SUPERSET_ANALYTICS_DATABASE_URI",
    "postgresql+psycopg2://bi_readonly:bi_readonly@postgres:5432/retail_analytics",
)

# TODO: Register ANALYTICS_DATABASE_URI inside Superset.
# TODO: Keep dashboard datasets on mart/serving only.
