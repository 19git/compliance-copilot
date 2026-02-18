"""Connector factory - creates the right connector for a file."""

from pathlib import Path
from typing import Dict, Type, Optional

from .base import BaseConnector
from .csv_connector import CSVConnector
from .excel_connector import ExcelConnector
from .pdf_connector import PDFConnector
from .json_connector import JSONConnector
from .parquet_connector import ParquetConnector
from .sql_connector import SQLConnector
from .exceptions import UnsupportedFormatError


class ConnectorFactory:
    _connectors: Dict[str, Type[BaseConnector]] = {
        '.csv': CSVConnector,
        '.tsv': CSVConnector,
        '.txt': CSVConnector,
        '.xlsx': ExcelConnector,
        '.xls': ExcelConnector,
        '.pdf': PDFConnector,
        '.json': JSONConnector,
        '.parquet': ParquetConnector,
        '.pq': ParquetConnector,
        # SQL is special: it doesn't use a file extension
    }
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
    
    def get_connector(self, source: str) -> BaseConnector:
        # Special case: if source looks like a SQL connection string?
        # For simplicity, we keep SQL as a separate method.
        # We'll handle SQL via a different config mechanism.
        ext = Path(source).suffix.lower()
        if ext not in self._connectors:
            raise UnsupportedFormatError(ext, list(self._connectors.keys()))
        
        connector_class = self._connectors[ext]
        connector_config = self.config.get(ext[1:], {})
        return connector_class(connector_config)
    
    def get_sql_connector(self, config: dict) -> SQLConnector:
        """Special method to get a SQL connector using config."""
        return SQLConnector(config)
    
    @classmethod
    def supported_formats(cls) -> list:
        return list(cls._connectors.keys())
