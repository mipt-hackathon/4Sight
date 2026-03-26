#!/bin/sh
set -e

superset db upgrade
superset fab create-admin \
  --username "${SUPERSET_ADMIN_USERNAME}" \
  --firstname "${SUPERSET_ADMIN_FIRSTNAME}" \
  --lastname "${SUPERSET_ADMIN_LASTNAME}" \
  --email "${SUPERSET_ADMIN_EMAIL}" \
  --password "${SUPERSET_ADMIN_PASSWORD}" || true
superset init
echo "Superset metadata DB is ready. Register ${SUPERSET_ANALYTICS_DATABASE_URI} as the BI read-only analytics connection for mart/serving."

exec superset run -h 0.0.0.0 -p 8088 --with-threads
