"""Generic resources package."""

from .csv import CSVQueryProvider
from .rest import RESTQueryProvider
from .sql import SQLQueryProvider

__all__ = ["SQLQueryProvider", "RESTQueryProvider", "CSVQueryProvider"]
