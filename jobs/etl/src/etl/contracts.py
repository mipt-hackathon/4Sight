from pathlib import Path

from etl.models import CsvLoadPlan, CsvSourceFile, TableColumnSpec

REPO_ROOT = Path(__file__).resolve().parents[4]
CLEAN_SQL_DIR = REPO_ROOT / "sql" / "clean"

DATA_FILE_PLANS: tuple[tuple[str, tuple[TableColumnSpec, ...], str], ...] = (
    (
        "users",
        (
            TableColumnSpec("user_id", "user_id", "bigint", nullable=False, primary_key=True),
            TableColumnSpec("gender", "gender", "text"),
            TableColumnSpec("first_name", "first_name", "text"),
            TableColumnSpec("last_name", "last_name", "text"),
            TableColumnSpec("email", "email", "text"),
            TableColumnSpec("age", "age", "integer"),
            TableColumnSpec("state", "state", "text"),
            TableColumnSpec("street_address", "street_address", "text"),
            TableColumnSpec("postal_code", "postal_code", "text"),
            TableColumnSpec("city", "city", "text"),
            TableColumnSpec("country", "country", "text"),
            TableColumnSpec("traffic_source", "traffic_source", "text"),
            TableColumnSpec("is_loyal", "is_loyal", "boolean"),
        ),
        "user_id",
    ),
    (
        "orders",
        (
            TableColumnSpec("order_id", "order_id", "bigint", nullable=False, primary_key=True),
            TableColumnSpec("user_id", "user_id", "bigint", nullable=False),
            TableColumnSpec("status", "status", "text"),
            TableColumnSpec("created_at", "created_at", "timestamptz", nullable=False),
            TableColumnSpec("returned_at", "returned_at", "timestamptz"),
            TableColumnSpec("shipped_at", "shipped_at", "timestamptz"),
            TableColumnSpec("delivered_at", "delivered_at", "timestamptz"),
            TableColumnSpec("num_of_item", "num_of_item", "integer", nullable=False),
        ),
        "order_id",
    ),
    (
        "order_items",
        (
            TableColumnSpec(
                "order_item_id",
                "order_item_id",
                "bigint",
                nullable=False,
                primary_key=True,
            ),
            TableColumnSpec("order_id", "order_id", "bigint", nullable=False),
            TableColumnSpec("user_id", "user_id", "bigint", nullable=False),
            TableColumnSpec("product_id", "product_id", "bigint", nullable=False),
            TableColumnSpec("inventory_item_id", "inventory_item_id", "bigint", nullable=False),
            TableColumnSpec("sale_price", "sale_price", "numeric", nullable=False),
            TableColumnSpec("cost", "cost", "numeric", nullable=False),
            TableColumnSpec("category", "category", "text"),
            TableColumnSpec("brand", "brand", "text"),
            TableColumnSpec("department", "department", "text"),
            TableColumnSpec("sku", "sku", "text"),
            TableColumnSpec(
                "distribution_center_id",
                "distribution_center_id",
                "bigint",
                nullable=False,
            ),
            TableColumnSpec("delivery_longitude", "delivery_longitude", "float8"),
            TableColumnSpec("delivery_latitude", "delivery_latitude", "float8"),
            TableColumnSpec("warehouse_name", "warehouse_name", "text"),
            TableColumnSpec("warehouse_longitude", "warehouse_longitude", "float8"),
            TableColumnSpec("warehouse_latitude", "warehouse_latitude", "float8"),
            TableColumnSpec("product_name", "product_name", "text"),
            TableColumnSpec("customer_review", "customer_review", "text"),
        ),
        "order_item_id",
    ),
)

EVENTS_PLAN: tuple[TableColumnSpec, ...] = (
    TableColumnSpec("id", "source_event_id", "bigint", nullable=False),
    TableColumnSpec("user_id", "user_id", "bigint"),
    TableColumnSpec("sequence_number", "sequence_number", "integer", nullable=False),
    TableColumnSpec("session_id", "session_id", "uuid", nullable=False),
    TableColumnSpec("created_at", "created_at", "timestamptz", nullable=False),
    TableColumnSpec("ip_address", "ip_address", "text"),
    TableColumnSpec("city", "city", "text"),
    TableColumnSpec("state", "state", "text"),
    TableColumnSpec("postal_code", "postal_code", "text"),
    TableColumnSpec("browser", "browser", "text"),
    TableColumnSpec("traffic_source", "traffic_source", "text"),
    TableColumnSpec("uri", "uri", "text"),
    TableColumnSpec("event_type", "event_type", "text"),
)


def build_load_plans(
    source: CsvSourceFile,
    encoding: str,
    header: tuple[str, ...],
) -> list[CsvLoadPlan]:
    if source.filename == "data.csv":
        return [
            _build_plan(
                source=source,
                encoding=encoding,
                header=header,
                target_table=table_name,
                target_columns=target_columns,
                ddl_sql_path=_clean_sql_path(table_name),
                dedupe_key=dedupe_key,
                drop_source_duplicates=True,
            )
            for table_name, target_columns, dedupe_key in DATA_FILE_PLANS
        ]

    if source.filename == "events.csv":
        return [
            _build_plan(
                source=source,
                encoding=encoding,
                header=header,
                target_table="events",
                target_columns=EVENTS_PLAN,
                ddl_sql_path=_clean_sql_path("events"),
                surrogate_key="event_row_id",
            )
        ]

    raise ValueError(
        f"Unexpected CSV source {source.path}. This scaffold expects data.csv and events.csv only."
    )


def _build_plan(
    source: CsvSourceFile,
    encoding: str,
    header: tuple[str, ...],
    target_table: str,
    target_columns: tuple[TableColumnSpec, ...],
    ddl_sql_path: Path,
    dedupe_key: str | None = None,
    surrogate_key: str | None = None,
    drop_source_duplicates: bool = False,
) -> CsvLoadPlan:
    missing_columns = [
        column.source_name for column in target_columns if column.source_name not in header
    ]
    if missing_columns:
        raise ValueError(
            f"Source file {source.path} is missing columns required for clean.{target_table}: "
            f"{missing_columns}"
        )

    if not ddl_sql_path.exists():
        raise FileNotFoundError(
            f"Missing SQL DDL definition for clean.{target_table}: {ddl_sql_path}"
        )

    return CsvLoadPlan(
        source=source,
        encoding=encoding,
        source_header=header,
        target_table=target_table,
        target_columns=target_columns,
        ddl_sql_path=ddl_sql_path,
        dedupe_key=dedupe_key,
        surrogate_key=surrogate_key,
        drop_source_duplicates=drop_source_duplicates,
    )


def _clean_sql_path(target_table: str) -> Path:
    return CLEAN_SQL_DIR / f"clean_{target_table}.sql"


__all__ = ["build_load_plans"]
