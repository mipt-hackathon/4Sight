import csv
import logging
import uuid
from datetime import datetime
from decimal import Decimal

from common.db import create_db_engine
from psycopg import sql
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    Identity,
    Integer,
    MetaData,
    Numeric,
    Table,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
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
    """Load CSV rows directly into typed clean-schema tables."""

    engine = create_db_engine()

    with engine.begin() as connection:
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS clean"))
        _drop_obsolete_import_tables(connection)

    for plan in transformed_artifacts:
        with engine.begin() as connection:
            _recreate_target_table(connection, plan)

        rows_loaded = _copy_rows(engine, plan)

        logger.info(
            "Load step copied %s rows from %s into clean.%s",
            rows_loaded,
            plan.source.filename,
            plan.target_table,
        )

    logger.info(
        "TODO: add business cleaning, reconciliation, and stronger integrity rules "
        "on top of the typed clean tables."
    )


def _drop_obsolete_import_tables(connection: Connection) -> None:
    for table_name in OBSOLETE_IMPORT_TABLES:
        connection.execute(text(f'DROP TABLE IF EXISTS clean."{table_name}"'))


def _recreate_target_table(connection: Connection, plan: CsvLoadPlan) -> Table:
    metadata = MetaData(schema="clean")
    columns: list[Column] = []

    if plan.surrogate_key:
        columns.append(
            Column(
                plan.surrogate_key,
                BigInteger,
                Identity(start=1),
                primary_key=True,
                nullable=False,
            )
        )

    columns.extend(
        [
            Column(
                "etl_source_file",
                Text,
                nullable=False,
                server_default=text(_quote_literal(plan.source.filename)),
            ),
            Column(
                "etl_loaded_at",
                DateTime(timezone=True),
                nullable=False,
                server_default=func.now(),
            ),
        ]
    )

    for column_spec in plan.target_columns:
        columns.append(
            Column(
                column_spec.target_name,
                _sqlalchemy_type(column_spec.type_name),
                nullable=column_spec.nullable,
                primary_key=column_spec.primary_key,
            )
        )

    table = Table(plan.target_table, metadata, *columns)

    connection.execute(text(f'DROP TABLE IF EXISTS clean."{plan.target_table}"'))
    metadata.create_all(connection, tables=[table])
    return table


def _copy_rows(engine, plan: CsvLoadPlan) -> int:
    target_column_names = [column.target_name for column in plan.target_columns]
    copy_statement = sql.SQL("COPY {}.{} ({}) FROM STDIN").format(
        sql.Identifier("clean"),
        sql.Identifier(plan.target_table),
        sql.SQL(", ").join(sql.Identifier(column_name) for column_name in target_column_names),
    )

    seen_keys: set[str] = set()
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

                        if plan.dedupe_key:
                            dedupe_value = row.get(plan.dedupe_key)
                            if dedupe_value in seen_keys:
                                continue
                            seen_keys.add(dedupe_value)

                        converted_row = tuple(
                            _convert_value(row.get(column.source_name), column)
                            for column in plan.target_columns
                        )
                        copy.write_row(
                            converted_row
                        )
        raw_connection.commit()
    finally:
        raw_connection.close()

    return _count_rows(engine, plan.target_table)


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


def _sqlalchemy_type(type_name: str):
    if type_name == "text":
        return Text
    if type_name == "bigint":
        return BigInteger
    if type_name == "integer":
        return Integer
    if type_name == "numeric":
        return Numeric
    if type_name == "float8":
        return Float(precision=53)
    if type_name == "boolean":
        return Boolean
    if type_name == "timestamptz":
        return DateTime(timezone=True)
    if type_name == "uuid":
        return UUID(as_uuid=True)

    raise ValueError(f"Unsupported SQLAlchemy type_name={type_name!r}")


def _count_rows(engine, table_name: str) -> int:
    with engine.connect() as connection:
        row_count = connection.execute(
            text(f'SELECT COUNT(*) FROM clean."{table_name}"')
        ).scalar_one()
    return int(row_count)


def _quote_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


__all__ = ["run_load"]
