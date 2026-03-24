import csv
import hashlib
import logging
import uuid
from datetime import datetime
from decimal import Decimal

from common.db import create_db_engine
from psycopg import sql
from sqlalchemy import text
from sqlalchemy.engine import Connection

from etl.models import CsvLoadPlan, TableColumnSpec

logger = logging.getLogger(__name__)
OBSOLETE_IMPORT_TABLES = (
    "transactions_wide_import",
    "users_import",
    "orders_import",
    "order_items_import",
    "events_import",
)


def run_load(transformed_artifacts: list[CsvLoadPlan]) -> None:
    """Load cleaned CSV rows directly into clean-schema tables defined in SQL files."""

    engine = create_db_engine()

    with engine.begin() as connection:
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS clean"))
        _drop_obsolete_import_tables(connection)

    for plan in transformed_artifacts:
        with engine.begin() as connection:
            _recreate_target_table(connection, plan)

        rows_loaded, source_duplicates_skipped, entity_duplicates_skipped = _copy_rows(engine, plan)

        logger.info(
            "Load step copied %s rows from %s into clean.%s using %s "
            "(source_duplicates_skipped=%s, entity_duplicates_skipped=%s)",
            rows_loaded,
            plan.source.filename,
            plan.target_table,
            plan.ddl_sql_path.name,
            source_duplicates_skipped,
            entity_duplicates_skipped,
        )

    logger.info(
        "TODO: extend events cleaning and downstream curated modeling on top of the current "
        "clean table contract."
    )


def _drop_obsolete_import_tables(connection: Connection) -> None:
    for table_name in OBSOLETE_IMPORT_TABLES:
        connection.execute(text(f'DROP TABLE IF EXISTS clean."{table_name}"'))


def _recreate_target_table(connection: Connection, plan: CsvLoadPlan) -> None:
    ddl_sql = plan.ddl_sql_path.read_text(encoding="utf-8").strip()
    if not ddl_sql:
        raise ValueError(
            f"SQL DDL file is empty for clean.{plan.target_table}: {plan.ddl_sql_path}"
        )

    connection.execute(text(f'DROP TABLE IF EXISTS clean."{plan.target_table}"'))
    connection.exec_driver_sql(ddl_sql)


def _copy_rows(engine, plan: CsvLoadPlan) -> tuple[int, int, int]:
    target_column_names = [column.target_name for column in plan.target_columns]
    copy_statement = sql.SQL("COPY {}.{} ({}) FROM STDIN").format(
        sql.Identifier("clean"),
        sql.Identifier(plan.target_table),
        sql.SQL(", ").join(sql.Identifier(column_name) for column_name in target_column_names),
    )

    seen_keys: set[str] = set()
    seen_source_rows: set[str] = set()
    skipped_source_duplicates = 0
    skipped_entity_duplicates = 0
    raw_connection = engine.raw_connection()
    try:
        with raw_connection.cursor() as cursor:
            with cursor.copy(copy_statement) as copy:
                with plan.source.path.open("r", encoding=plan.encoding, newline="") as handle:
                    reader = csv.DictReader(handle)
                    if tuple(reader.fieldnames or ()) != plan.source_header:
                        raise ValueError(f"CSV header changed while loading {plan.source.path}")

                    for row_number, row in enumerate(reader, start=1):
                        if None in row:
                            raise ValueError(
                                f"CSV row {row_number} in {plan.source.path} has extra unnamed "
                                "columns. TODO: handle malformed rows in a later cleaning step."
                            )

                        if plan.drop_source_duplicates:
                            row_signature = _source_row_signature(row, plan.source_header)
                            if row_signature in seen_source_rows:
                                skipped_source_duplicates += 1
                                continue
                            seen_source_rows.add(row_signature)

                        if plan.dedupe_key:
                            dedupe_value = row.get(plan.dedupe_key)
                            if dedupe_value in seen_keys:
                                skipped_entity_duplicates += 1
                                continue
                            seen_keys.add(dedupe_value)

                        converted_row = tuple(
                            _convert_value(row.get(column.source_name), column)
                            for column in plan.target_columns
                        )
                        copy.write_row(converted_row)
        raw_connection.commit()
    finally:
        raw_connection.close()

    return (
        _count_rows(engine, plan.target_table),
        skipped_source_duplicates,
        skipped_entity_duplicates,
    )


def _convert_value(value: str | None, column_spec: TableColumnSpec):
    if value is None or value == "":
        return None

    if column_spec.type_name == "text":
        return value
    if column_spec.type_name == "bigint":
        return int(value)
    if column_spec.type_name == "integer":
        return int(value)
    if column_spec.type_name == "numeric":
        return Decimal(value)
    if column_spec.type_name == "float8":
        return float(value)
    if column_spec.type_name == "boolean":
        return value == "True"
    if column_spec.type_name == "timestamptz":
        return datetime.fromisoformat(value)
    if column_spec.type_name == "uuid":
        return uuid.UUID(value)

    raise ValueError(f"Unsupported type_name={column_spec.type_name!r}")


def _count_rows(engine, table_name: str) -> int:
    with engine.connect() as connection:
        row_count = connection.execute(
            text(f'SELECT COUNT(*) FROM clean."{table_name}"')
        ).scalar_one()
    return int(row_count)

def _source_row_signature(row: dict[str, str | None], source_header: tuple[str, ...]) -> str:
    digest = hashlib.sha1()
    for column_name in source_header:
        digest.update((row.get(column_name) or "").encode("utf-8"))
        digest.update(b"\x1f")
    return digest.hexdigest()


__all__ = ["run_load"]
