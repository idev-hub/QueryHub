"""CSV-backed provider for local datasets."""

from __future__ import annotations

import asyncio
import csv
from pathlib import Path
from typing import Any, Mapping

from ..config.models import CSVProviderConfig
from ..core.errors import ProviderExecutionError
from .base import QueryProvider, QueryResult


class CSVQueryProvider(QueryProvider):
    """Read tabular data from CSV sources."""

    def __init__(self, config: CSVProviderConfig) -> None:
        super().__init__(config)
        self._root_path = Path(config.root_path)

    @property
    def config(self) -> CSVProviderConfig:
        return super().config  # type: ignore[return-value]

    async def execute(self, query: Mapping[str, Any]) -> QueryResult:
        relative_path = query.get("path") or query.get("file")
        if not relative_path:
            raise ProviderExecutionError("CSV queries require a 'path' or 'file'")
        full_path = self._root_path / relative_path
        if not full_path.exists():
            raise ProviderExecutionError(f"CSV file not found: {full_path}")

        delimiter = query.get("delimiter") or self.config.delimiter
        encoding = query.get("encoding") or self.config.encoding

        rows = await asyncio.to_thread(self._read_csv, full_path, delimiter, encoding)
        filters = query.get("filters") or []
        filtered = self._apply_filters(rows, filters)
        return QueryResult(data=filtered, metadata={"rowcount": len(filtered)})

    def _read_csv(self, path: Path, delimiter: str, encoding: str) -> list[dict[str, Any]]:
        with path.open("r", encoding=encoding, newline="") as handle:
            reader = csv.DictReader(handle, delimiter=delimiter)
            return [dict(row) for row in reader]

    def _apply_filters(
        self,
        rows: list[dict[str, Any]],
        filters: list[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        if not filters:
            return rows

        def match(row: Mapping[str, Any]) -> bool:
            for flt in filters:
                column = flt.get("column")
                value = flt.get("value")
                op = flt.get("operator", "eq")
                if column is None or column not in row:
                    return False
                lhs = row[column]
                if op == "eq" and lhs != value:
                    return False
                if op == "ne" and lhs == value:
                    return False
                if op == "contains" and value is not None and value not in str(lhs):
                    return False
            return True

        return [row for row in rows if match(row)]
