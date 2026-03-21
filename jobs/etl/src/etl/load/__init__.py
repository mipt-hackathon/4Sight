import hashlib
import logging

from common.db import create_db_engine
from psycopg import sql
from sqlalchemy import BigInteger, Column, DateTime, Identity, MetaData, Table, Text, func, text
from sqlalchemy.engine import Connection

from etl.models import CsvImportPlan

logger = logging.getLogger(__name__)


def run_load(transformed_artifacts: list[CsvImportPlan]) -> None:
    """Load CSV rows into explicit clean-schema import tables."""

    engine = create_db_engine()

    for plan in transformed_artifacts:
        with engine.begin() as connection:
            connection.execute(text("CREATE SCHEMA IF NOT EXISTS clean"))
            _recreate_import_table(connection, plan)

        rows_loaded = _copy_csv_rows(engine, plan)

        with engine.begin() as connection:
            _record_source_file(connection, plan)

        logger.info(
            "Load step copied %s rows from %s into clean.%s",
            rows_loaded,
            plan.source.filename,
            plan.source.table_name,
        )

    logger.info(
        "TODO: replace import-table copying with real cleaning, deduplication, "
        "and typed curated models."
    )


def _recreate_import_table(connection: Connection, plan: CsvImportPlan) -> Table:
    metadata = MetaData(schema="clean")
    table = Table(
        plan.source.table_name,
        metadata,
        Column("etl_row_number", BigInteger, Identity(start=1), nullable=False),
        Column(
            "etl_source_file",
            Text,
            nullable=False,
            server_default=text(_quote_literal(plan.source.filename)),
        ),
        Column("etl_loaded_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
        *(Column(column_name, Text, nullable=True) for column_name in plan.header),
    )

    connection.execute(text(f'DROP TABLE IF EXISTS clean."{plan.source.table_name}"'))
    metadata.create_all(connection, tables=[table])
    return table


def _copy_csv_rows(engine, plan: CsvImportPlan) -> int:
    copy_statement = sql.SQL(
        "COPY {}.{} ({}) FROM STDIN WITH (FORMAT csv, HEADER true)"
    ).format(
        sql.Identifier("clean"),
        sql.Identifier(plan.source.table_name),
        sql.SQL(", ").join(sql.Identifier(column_name) for column_name in plan.header),
    )

    raw_connection = engine.raw_connection()
    try:
        with raw_connection.cursor() as cursor:
            with cursor.copy(copy_statement) as copy:
                with plan.source.path.open("r", encoding=plan.encoding, newline="") as handle:
                    while chunk := handle.read(1024 * 1024):
                        copy.write(chunk.encode("utf-8"))
        raw_connection.commit()
    finally:
        raw_connection.close()

    with engine.connect() as connection:
        row_count = connection.execute(
            text(f'SELECT COUNT(*) FROM clean."{plan.source.table_name}"')
        ).scalar_one()

    return int(row_count)


def _record_source_file(connection: Connection, plan: CsvImportPlan) -> None:
    connection.execute(
        text(
            """
            DELETE FROM public.source_files
            WHERE source_name = :source_name
              AND file_path <> :file_path
            """
        ),
        {
            "source_name": plan.source.filename,
            "file_path": str(plan.source.path),
        },
    )
    connection.execute(
        text(
            """
            INSERT INTO public.source_files (
                source_name,
                file_path,
                file_hash,
                detected_encoding,
                ingestion_status
            )
            VALUES (
                :source_name,
                :file_path,
                :file_hash,
                :detected_encoding,
                :ingestion_status
            )
            ON CONFLICT (file_path) DO UPDATE
            SET
                source_name = EXCLUDED.source_name,
                file_hash = EXCLUDED.file_hash,
                detected_encoding = EXCLUDED.detected_encoding,
                ingestion_status = EXCLUDED.ingestion_status
            """
        ),
        {
            "source_name": plan.source.filename,
            "file_path": str(plan.source.path),
            "file_hash": _hash_file(plan.source.path),
            "detected_encoding": plan.encoding,
            "ingestion_status": "loaded",
        },
    )


def _hash_file(file_path) -> str:
    digest = hashlib.sha256()
    with file_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _quote_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


__all__ = ["run_load"]
