FROM apache/superset:4.1.1

USER root
RUN pip install --no-cache-dir psycopg2-binary

COPY infra/superset/superset_config.py /app/pythonpath/superset_config.py
COPY infra/superset/init.sh /app/docker/init.sh
RUN chmod +x /app/docker/init.sh

USER superset
