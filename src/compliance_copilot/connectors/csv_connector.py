"""CSV file connector."""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any

from .base import BaseConnector
from .exceptions import FileNotFoundError, DataLoadError, EmptyFileError


class CSVConnector(BaseConnector):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config or {})
        self.delimiter = self.config.get("delimiter", "auto")
        self.encoding = self.config.get("encoding", "utf-8")
        self.header_row = self.config.get("header_row", 0)
    
    def load(self, source: str, **kwargs) -> pd.DataFrame:
        path = Path(source)
        
        if not path.exists():
            raise FileNotFoundError(str(path))
        
        if path.stat().st_size == 0:
            raise EmptyFileError(str(path))
        
        try:
            df = pd.read_csv(
                path,
                encoding=self.encoding,
                header=self.header_row
            )
            self._update_metadata(source, df)
            return df
        except pd.errors.EmptyDataError:
            raise EmptyFileError(str(path))
        except Exception as e:
            raise DataLoadError(str(path), str(e))
    
    def validate(self, source: str) -> bool:
        path = Path(source)
        return path.exists() and path.suffix.lower() in ['.csv', '.tsv', '.txt']
