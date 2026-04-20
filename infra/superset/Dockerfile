FROM apache/superset:4.1.1

USER root
RUN pip install --no-cache-dir psycopg2-binary

COPY infra/superset/superset_config.py /app/pythonpath/superset_config.py
COPY infra/superset/init.sh /app/docker/init.sh
COPY infra/superset/normalize_bar_chart_query_contexts.py /app/docker/normalize_bar_chart_query_contexts.py
COPY infra/superset/remove_deprecated_charts.py /app/docker/remove_deprecated_charts.py
COPY infra/superset/assets /app/docker/assets
RUN chmod +x /app/docker/init.sh

USER superset
