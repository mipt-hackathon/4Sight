import os

ROW_LIMIT = 5000
SECRET_KEY = os.getenv("SUPERSET_SECRET_KEY", "replace-me")
SQLALCHEMY_DATABASE_URI = os.getenv(
    "SUPERSET_DATABASE_URI",
    "postgresql+psycopg2://retail:retail@postgres:5432/retail_analytics",
)

# TODO: Register PostgreSQL datasets, charts, and dashboards once marts/serving tables exist.
