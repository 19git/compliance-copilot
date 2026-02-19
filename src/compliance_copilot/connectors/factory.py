"""Connector factory - creates the right connector for a data source."""

from pathlib import Path
from typing import Dict, Type, Optional

from .base import BaseConnector
from .csv_connector import CSVConnector
from .excel_connector import ExcelConnector
from .pdf_connector import PDFConnector
from .json_connector import JSONConnector
from .parquet_connector import ParquetConnector
from .sql_connector import SQLConnector
from .mongodb_connector import MongoDBConnector
from .postgresql_connector import PostgreSQLConnector
from .sqlite_connector import SQLiteConnector
from .bigquery_connector import BigQueryConnector
from .exceptions import UnsupportedFormatError


class ConnectorFactory:
    _connectors: Dict[str, Type[BaseConnector]] = {
        # File-based connectors
        '.csv': CSVConnector,
        '.tsv': CSVConnector,
        '.txt': CSVConnector,
        '.xlsx': ExcelConnector,
        '.xls': ExcelConnector,
        '.pdf': PDFConnector,
        '.json': JSONConnector,
        '.parquet': ParquetConnector,
        '.pq': ParquetConnector,
        '.db': SQLiteConnector,
        '.sqlite': SQLiteConnector,
        '.sqlite3': SQLiteConnector,
    }
    
    # Database connectors (no file extension)
    _database_connectors = {
        'mongodb': MongoDBConnector,
        'postgresql': PostgreSQLConnector,
        'bigquery': BigQueryConnector,
    }
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
    
    def get_connector(self, source: str) -> BaseConnector:
        """Get connector for file-based source."""
        ext = Path(source).suffix.lower()
        if ext not in self._connectors:
            raise UnsupportedFormatError(ext, list(self._connectors.keys()))
        
        connector_class = self._connectors[ext]
        connector_config = self.config.get(ext[1:], {})
        return connector_class(connector_config)
    
    def get_database_connector(self, db_type: str) -> BaseConnector:
        """Get connector for database source."""
        if db_type not in self._database_connectors:
            raise ValueError(f"Unsupported database type: {db_type}. "
                           f"Supported: {list(self._database_connectors.keys())}")
        
        connector_class = self._database_connectors[db_type]
        connector_config = self.config.get(db_type, {})
        return connector_class(connector_config)
    
    @classmethod
    def supported_formats(cls) -> list:
        """Get list of supported file extensions."""
        return list(cls._connectors.keys())
    
    @classmethod
    def supported_databases(cls) -> list:
        """Get list of supported database types."""
        return list(cls._database_connectors.keys())
