from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CsvSourceFile:
    filename: str
    path: Path


@dataclass(frozen=True)
class TableColumnSpec:
    source_name: str
    target_name: str
    type_name: str
    nullable: bool = True
    primary_key: bool = False


@dataclass(frozen=True)
class CsvLoadPlan:
    source: CsvSourceFile
    encoding: str
    source_header: tuple[str, ...]
    target_table: str
    target_columns: tuple[TableColumnSpec, ...]
    dedupe_key: str | None = None
    surrogate_key: str | None = None
