"""CSV file query provider.

This provider reads data from local CSV files.
"""

from __future__ import annotations

import asyncio
import csv
from pathlib import Path
from typing import Any, Mapping, Optional

from ....config.provider_models import ProviderConfig
from ....core.credentials import CredentialRegistry
from ....core.errors import ProviderExecutionError, ProviderInitializationError
from ...base_query_provider import BaseQueryProvider, QueryResult


class CSVQueryProvider(BaseQueryProvider):
    """Read tabular data from CSV files.

    This provider doesn't require credentials (reads from local filesystem).
    """

    def __init__(
        self,
        config: ProviderConfig,
        credential_registry: Optional[CredentialRegistry] = None,
    ) -> None:
        super().__init__(config, credential_registry)
        if config.type != "csv" or not config.resource.csv:
            raise ProviderInitializationError("CSVQueryProvider requires csv resource configuration")
        self._root_path = Path(config.resource.csv.root_path)

    @property
    def csv_config(self):
        """Get CSV-specific configuration from resource."""
        return self.config.resource.csv

    async def execute(self, query: Mapping[str, Any]) -> QueryResult:
        """Read data from a CSV file.

        Args:
            query: Query specification with keys:
                  - path or file: CSV file path relative to root_path (required)
                  - delimiter: Optional delimiter (overrides config)
                  - encoding: Optional encoding (overrides config)
                  - filters: Optional list of filters to apply
        """
        relative_path = query.get("path") or query.get("file")
        if not relative_path:
            raise ProviderExecutionError("CSV queries require a 'path' or 'file'")

        full_path = self._root_path / relative_path
        if not full_path.exists():
            raise ProviderExecutionError(f"CSV file not found: {full_path}")

        delimiter = query.get("delimiter") or self.csv_config.delimiter
        encoding = query.get("encoding") or self.csv_config.encoding

        rows = await asyncio.to_thread(self._read_csv, full_path, delimiter, encoding)

        filters = query.get("filters") or []
        filtered = self._apply_filters(rows, filters)

        return QueryResult(data=filtered, metadata={"rowcount": len(filtered)})

    def _read_csv(self, path: Path, delimiter: str, encoding: str) -> list[dict[str, Any]]:
        """Read CSV file synchronously."""
        with path.open("r", encoding=encoding, newline="") as handle:
            reader = csv.DictReader(handle, delimiter=delimiter)
            return [dict(row) for row in reader]

    def _apply_filters(
        self,
        rows: list[dict[str, Any]],
        filters: list[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        """Apply filters to CSV data."""
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
