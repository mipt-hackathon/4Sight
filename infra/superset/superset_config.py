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
ALLOWED_FRAME_ANCESTORS = [
    domain.strip()
    for domain in os.getenv(
        "SUPERSET_EMBED_ALLOWED_DOMAINS",
        "http://localhost:13000,http://127.0.0.1:13000",
    ).split(",")
    if domain.strip()
]

FEATURE_FLAGS = {
    "EMBEDDED_SUPERSET": True,
    "DISABLE_EMBEDDED_SUPERSET_LOGOUT": True,
}

GUEST_ROLE_NAME = os.getenv("SUPERSET_GUEST_ROLE_NAME", "Gamma")
GUEST_TOKEN_JWT_SECRET = os.getenv("SUPERSET_GUEST_TOKEN_JWT_SECRET", SECRET_KEY)
TALISMAN_ENABLED = False

# TODO: Register ANALYTICS_DATABASE_URI inside Superset.
# TODO: Keep dashboard datasets on mart/serving only.
