from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CsvSourceFile:
    filename: str
    path: Path
    table_name: str


@dataclass(frozen=True)
class CsvImportPlan:
    source: CsvSourceFile
    encoding: str
    header: tuple[str, ...]
