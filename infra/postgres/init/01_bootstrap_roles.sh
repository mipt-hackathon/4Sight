#!/bin/sh
set -eu

BI_READONLY_USER="${BI_READONLY_USER:-bi_readonly}"
BI_READONLY_PASSWORD="${BI_READONLY_PASSWORD:-bi_readonly}"
SUPERSET_METADATA_DB="${SUPERSET_METADATA_DB:-superset_metadata}"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<EOF
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '${BI_READONLY_USER}') THEN
        EXECUTE format('CREATE ROLE %I LOGIN PASSWORD %L', '${BI_READONLY_USER}', '${BI_READONLY_PASSWORD}');
    ELSE
        EXECUTE format('ALTER ROLE %I LOGIN PASSWORD %L', '${BI_READONLY_USER}', '${BI_READONLY_PASSWORD}');
    END IF;
END
\$\$;

GRANT CONNECT ON DATABASE ${POSTGRES_DB} TO ${BI_READONLY_USER};
EOF

if ! psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres -tAc \
    "SELECT 1 FROM pg_database WHERE datname = '${SUPERSET_METADATA_DB}'" | grep -q 1; then
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres \
        -c "CREATE DATABASE ${SUPERSET_METADATA_DB} OWNER ${POSTGRES_USER}"
fi
