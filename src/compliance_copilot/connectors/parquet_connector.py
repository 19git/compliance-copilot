"""Parquet file connector."""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any

from .base import BaseConnector
from .exceptions import FileNotFoundError, DataLoadError, EmptyFileError


class ParquetConnector(BaseConnector):
    """Reads Parquet files into a pandas DataFrame.
    
    Parquet is a columnar storage format, great for large datasets.
    Requires pyarrow.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config or {})
        # No specific config needed for basic parquet reading
    
    def load(self, source: str, **kwargs) -> pd.DataFrame:
        path = Path(source)
        
        if not path.exists():
            raise FileNotFoundError(str(path))
        
        if path.stat().st_size == 0:
            raise EmptyFileError(str(path))
        
        try:
            df = pd.read_parquet(path)
            self._update_metadata(source, df)
            return df
        except Exception as e:
            raise DataLoadError(str(path), str(e))
    
    def validate(self, source: str) -> bool:
        path = Path(source)
        return path.exists() and path.suffix.lower() in ['.parquet', '.pq']
