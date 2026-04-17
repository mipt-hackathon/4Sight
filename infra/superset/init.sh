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
superset import-directory -o -f /app/docker/assets/retail_notebook_bi
python /app/docker/normalize_bar_chart_query_contexts.py
python - <<'PY'
from superset.app import create_app
app = create_app()
with app.app_context():
    from superset.extensions import db
    from superset.models.core import Database
    from superset.connectors.sqla.models import SqlaTable
    from superset.models.slice import Slice
    from superset.models.dashboard import Dashboard

    target_database = (
        db.session.query(Database)
        .filter(Database.database_name == "Retail Analytics")
        .one_or_none()
    )
    target_datasets = {
        (dataset.schema, dataset.table_name)
        for dataset in db.session.query(SqlaTable).all()
    }
    target_dashboards = {
        dashboard.slug
        for dashboard in db.session.query(Dashboard).all()
    }
    chart_count = db.session.query(Slice).count()
    bar_charts_without_query_context = [
        slice_.slice_name
        for slice_ in db.session.query(Slice)
        .filter(Slice.viz_type == "echarts_timeseries_bar")
        .all()
        if not slice_.query_context
    ]
    bar_charts_with_extra_controls = []
    for slice_ in db.session.query(Slice).filter(Slice.viz_type == "echarts_timeseries_bar"):
        params = slice_.params_dict or {}
        if params.get("show_extra_controls") is not False:
            bar_charts_with_extra_controls.append(slice_.slice_name)

    if target_database is None:
        raise SystemExit("Superset seed import incomplete: Retail Analytics database is missing")
    expected_datasets = {
        ("mart", "abc_xyz"),
        ("mart", "abc_xyz_cv_distribution"),
        ("mart", "abc_xyz_time_series_samples"),
        ("mart", "rfm"),
        ("mart", "rfm_churn_by_segment"),
        ("mart", "product_xyz"),
        ("mart", "region_abc"),
        ("mart", "logistics_metrics"),
        ("mart", "customer_abc_monthly"),
        ("mart", "customer_category_migration"),
        ("mart", "category_abc"),
        ("mart", "brand_abc"),
    }
    if expected_datasets - target_datasets:
        raise SystemExit(
            f"Superset seed import incomplete: expected mart datasets missing, got={sorted(target_datasets)}"
        )
    if chart_count < 33:
        raise SystemExit(f"Superset seed import incomplete: expected at least 33 charts, got={chart_count}")
    if {"retail-notebook-bi", "retail-notebook-bi-deep-dive"} - target_dashboards:
        raise SystemExit(
            f"Superset seed import incomplete: expected dashboards missing, got={sorted(target_dashboards)}"
        )
    if bar_charts_without_query_context:
        raise SystemExit(
            "Superset chart normalization incomplete: charts without query_context="
            f"{sorted(bar_charts_without_query_context)}"
        )
    if bar_charts_with_extra_controls:
        raise SystemExit(
            "Superset chart normalization incomplete: echarts_timeseries_bar charts must "
            "have show_extra_controls=false, got="
            f"{sorted(bar_charts_with_extra_controls)}"
        )
PY
echo "Superset metadata DB is ready. Imported BI assets for ${SUPERSET_ANALYTICS_DATABASE_URI}."

exec superset run -h 0.0.0.0 -p 8088 --with-threads
